"""
CCEA GCSE - Universal Past Papers Scraper
=========================================

Important:
- CCEA subject + past paper pages are protected by Cloudflare and block simple HTTP requests.
- Selenium (NON-HEADLESS) reliably passes the JS challenge automatically on Windows.
  Headless tends to get stuck on the "Just a moment..." page.

Strategy:
- Use Selenium non-headless to open each subject page, then navigate to the subject's
  "Past papers & mark schemes" page.
- Extract only: Question Papers, Mark Schemes, Examiner Reports (if present).

Upload:
- staging_aqa_exam_papers via upload_papers_to_staging(subject_code, qualification_type='GCSE', exam_board='CCEA')
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scrapers.CCEA.ccea_common import (  # noqa: E402
    download_pdf_with_driver_session,
    ensure_storage_bucket,
    load_supabase,
    slugify_code,
    upload_pdf_bytes_to_storage,
)
from scrapers.CCEA.GCSE.ccea_gcse_subjects import load_subjects_from_repo  # noqa: E402


EXAM_BOARD = "CCEA"
QUAL_TYPE = "GCSE"

STORAGE_BUCKET_PDFS = "exam-pdfs"

def _dismiss_cookie_banner(driver: webdriver.Chrome) -> bool:
    """
    CCEA pages sometimes show a cookie/consent banner (OneTrust/Cookiebot/etc) that blocks clicks.
    Best-effort: try common accept/close selectors. Safe to call repeatedly.
    """
    candidates = [
        "#onetrust-accept-btn-handler",
        "button#onetrust-accept-btn-handler",
        "button[aria-label='Accept cookies']",
        "button[title='Accept cookies']",
        "button[title='Accept all cookies']",
        "button[aria-label='Accept all cookies']",
        "button.cookie-accept",
        "button#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
        "button#CybotCookiebotDialogBodyButtonAccept",
        ".onetrust-close-btn-handler",
        "#onetrust-close-btn-container button",
        "button[aria-label='Close']",
        "button[title='Close']",
        "button[aria-label='Dismiss']",
    ]

    for css in candidates:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, css)
            if not els:
                continue
            el = els[0]
            if not el.is_displayed():
                continue
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.1)
            driver.execute_script("arguments[0].click();", el)
            time.sleep(0.4)
            return True
        except Exception:
            continue
    try:
        driver.execute_script("document.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape'}));")
    except Exception:
        pass
    return False


def _should_cache_pdf(url: str | None) -> bool:
    if not url:
        return False
    u = (url or "").lower()
    # Only cache CCEA-hosted PDFs. If already a Supabase storage URL, skip.
    if "supabase.co/storage" in u:
        return False
    return "ccea.org.uk" in u and u.endswith(".pdf")


def _pdf_storage_path(*, subject_code: str, paper: dict, kind: str) -> str:
    year = paper.get("year")
    series = (paper.get("exam_series") or "June").replace("/", "-")
    pn = paper.get("paper_number") or 1
    comp = paper.get("component_code") or f"P{pn}"
    tier = paper.get("tier") or "Any"
    return f"papers/CCEA/{QUAL_TYPE}/{subject_code}/{year}/{series}/{comp}/{tier}/{kind}.pdf"


def cache_ccae_pdfs_in_sets(sb, driver, *, subject_code: str, past_papers_url: str, sets: list[dict]) -> list[dict]:
    """
    Key fix: CCEA PDFs are Cloudflare protected. Railway cannot download them reliably (403).
    When we scrape with Selenium (non-headless) we *can* download them using the cleared session cookies.

    This caches PDFs into Supabase Storage and replaces staging URLs with stable storage URLs.
    """
    import os
    from dotenv import load_dotenv

    # Ensure storage bucket exists (best-effort)
    load_dotenv()
    supabase_url = os.getenv("SUPABASE_URL") or ""
    service_key = os.getenv("SUPABASE_SERVICE_KEY") or ""
    if supabase_url and service_key:
        ensure_storage_bucket(supabase_url=supabase_url, service_key=service_key, bucket=STORAGE_BUCKET_PDFS, public=True)

    out: list[dict] = []
    for p in sets:
        p2 = dict(p)
        # Cache question paper (required for extraction); mark scheme/report best-effort.
        for field, kind, required in [
            ("question_paper_url", "question", True),
            ("mark_scheme_url", "mark_scheme", False),
            ("examiner_report_url", "examiner_report", False),
        ]:
            url = p2.get(field)
            if not _should_cache_pdf(url):
                continue
            try:
                pdf_bytes = download_pdf_with_driver_session(driver, url, referer=past_papers_url, timeout=90, retries=4)
                path = _pdf_storage_path(subject_code=subject_code, paper=p2, kind=kind)
                cached_url = upload_pdf_bytes_to_storage(sb, bucket=STORAGE_BUCKET_PDFS, path=path, pdf_bytes=pdf_bytes)
                p2[field] = cached_url
            except Exception as e:
                if required:
                    raise RuntimeError(f"[CCEA] Failed to cache required PDF ({field}) for {subject_code}: {e}") from e
                print(f"[WARN] [CCEA] Failed to cache optional PDF ({field}) for {subject_code}: {e}")
        out.append(p2)
    return out


def init_driver() -> webdriver.Chrome:
    chrome_options = Options()
    # Intentionally NOT headless (Cloudflare)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1400,900")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver


def _wait_cloudflare_clear(driver: webdriver.Chrome, *, timeout_s: int = 35) -> bool:
    for _ in range(timeout_s):
        if "Just a moment" not in (driver.title or ""):
            _dismiss_cookie_banner(driver)
            return True
        time.sleep(1)
    return False


def _find_past_papers_url(driver: webdriver.Chrome, subject_page_url: str) -> str:
    driver.get(subject_page_url)
    if not _wait_cloudflare_clear(driver):
        raise RuntimeError("Cloudflare challenge did not clear for subject page")
    _dismiss_cookie_banner(driver)

    # Prefer an explicit link on the page
    soup = BeautifulSoup(driver.page_source, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a.get("href") or ""
        if "past-papers-mark-schemes" in href:
            return urljoin(subject_page_url, href)

    # Fallback: append expected path
    return subject_page_url.rstrip("/") + "/past-papers-mark-schemes"


def _tier_from_text(text: str) -> Optional[str]:
    t = (text or "").lower()
    if "foundation" in t:
        return "Foundation"
    if "higher" in t:
        return "Higher"
    return None


def _doc_type(text: str, href: str) -> Optional[str]:
    """
    CCEA past paper links often don't say 'Question Paper' / 'Mark Scheme' in the anchor text.
    Instead the filename includes:
    - '-Paper.pdf' or '-Paper_0.pdf' for question papers
    - '-MS.pdf' for mark schemes
    """
    t = (text or "").lower()
    h = (href or "").lower()

    if "set task" in t or "controlled assessment" in t or "specimen" in t or "sample" in t:
        return None
    # Ignore modified versions (MV18/MV24) for now - keep the standard series materials
    if "/modified/" in h or "mv18" in h or "mv24" in h:
        return None

    if h.endswith("-ms.pdf") or "-ms.pdf" in h:
        return "mark_scheme"
    if "-paper" in h and h.endswith(".pdf"):
        return "question_paper"
    if "examiner" in t or "report" in t or "-report" in h or "-er" in h:
        return "examiner_report"

    # Fallback to text signals (some pages do label them)
    if "mark scheme" in t or ("mark" in t and "scheme" in t):
        return "mark_scheme"
    if "question paper" in t:
        return "question_paper"
    return None


def _series_from_text(text: str) -> str:
    t = (text or "").lower()
    if "summer" in t or "june" in t:
        return "June"
    if "winter" in t or "january" in t:
        return "January"
    if "november" in t:
        return "November"
    return "June"


def _extract_year(text: str) -> Optional[int]:
    m = re.search(r"\b(20\d{2})\b", text or "")
    return int(m.group(1)) if m else None


def _extract_component(text: str, href: str) -> Tuple[int, Optional[str]]:
    t = (text or "")
    h = href or ""
    # Unit / Component / Paper identifiers
    m = re.search(r"\bUnit\s*(\d+)\b", t, flags=re.I)
    if not m:
        m = re.search(r"\bComponent\s*(\d+)\b", t, flags=re.I)
    if not m:
        m = re.search(r"\bUnit\s*(\d+)\b", h, flags=re.I)
    unit = int(m.group(1)) if m else 1

    # Booklet A/B for practical skills etc.
    booklet = None
    mb = re.search(r"\bBooklet\s*([A-Z])\b", t, flags=re.I)
    if mb:
        booklet = mb.group(1).upper()

    # If it was a Component, use C prefix (more accurate for arts subjects)
    if re.search(r"\bComponent\s*%d\b" % unit, t, flags=re.I):
        code = f"C{unit}{booklet or ''}"
    else:
        code = f"U{unit}{booklet or ''}"
    return unit, code


def scrape_past_papers_page(driver: webdriver.Chrome, past_papers_url: str) -> List[Dict]:
    """
    CCEA pages expose filters as Drupal views selects (Year / Series / Type).
    We iterate years to capture more papers than the default list.
    """

    def _apply_filters(*, year_value: str, series_value: str, type_value: str) -> None:
        _dismiss_cookie_banner(driver)
        # Selects are typically:
        # - field_year_target_id_selective--*
        # - field_series_target_id_selective--*
        # - field_past_paper_type_target_id_selective--*
        # Retry to avoid transient stale elements during Drupal view refresh
        for attempt in range(4):
            try:
                year_el = driver.find_element(By.CSS_SELECTOR, "select[name^='field_year_target_id_selective']")
                series_el = driver.find_element(By.CSS_SELECTOR, "select[name^='field_series_target_id_selective']")
                type_el = driver.find_element(By.CSS_SELECTOR, "select[name^='field_past_paper_type_target_id_selective']")
                year_sel = Select(year_el)
                series_sel = Select(series_el)
                type_sel = Select(type_el)

                # Some selects can be "not interactable" unless scrolled into view.
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", year_el)
                time.sleep(0.1)
                year_sel.select_by_value(year_value)
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", series_el)
                time.sleep(0.1)
                series_sel.select_by_value(series_value)
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", type_el)
                time.sleep(0.1)
                type_sel.select_by_value(type_value)
                break
            except StaleElementReferenceException:
                time.sleep(0.6)
                if attempt == 3:
                    raise
            except Exception:
                _dismiss_cookie_banner(driver)
                time.sleep(0.6)
                if attempt == 3:
                    raise

        # Apply/submit (varies across pages)
        btn = None
        for css in ["input#edit-submit", "button#edit-submit", "input.form-submit", "button.form-submit"]:
            found = driver.find_elements(By.CSS_SELECTOR, css)
            if found:
                btn = found[0]
                break
        if btn:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.1)
            driver.execute_script("arguments[0].click();", btn)
            # Give time for Drupal view AJAX + DOM refresh
            time.sleep(2.2)
        else:
            # fallback: changing selects may auto-submit
            time.sleep(2.2)

        # Re-scroll to top after apply (helps avoid overlapping sticky headers)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.2)

    def _collect_page_sets() -> List[Dict]:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a.get("href") or ""
            if ".pdf" not in href.lower():
                continue
            text = " ".join(a.get_text(" ", strip=True).split())
            dtype = _doc_type(text, href)
            if not dtype:
                continue
            abs_url = urljoin(past_papers_url, href)
            tier = _tier_from_text(text)
            links.append((text, abs_url, dtype, tier, a))

        grouped: Dict[Tuple[int, str, int, Optional[str], Optional[str]], Dict] = {}
        for text, url, dtype, tier, a in links:
            year = _extract_year(text)
            series = _series_from_text(text)
            if not year:
                prev = a.find_previous(["h1", "h2", "h3", "h4", "strong"])
                if prev:
                    ctx = prev.get_text(" ", strip=True)
                    year = _extract_year(ctx) or year
                    series = _series_from_text(ctx) or series
            if not year:
                year = _extract_year(url) or 0
            if not year:
                continue

            paper_number, component_code = _extract_component(text, url)
            key = (year, series, paper_number, component_code, tier)
            if key not in grouped:
                grouped[key] = {
                    "year": year,
                    "exam_series": series,
                    "paper_number": paper_number,
                    "component_code": component_code,
                    "tier": tier,
                    "question_paper_url": None,
                    "mark_scheme_url": None,
                    "examiner_report_url": None,
                }
            if dtype == "question_paper":
                grouped[key]["question_paper_url"] = url
            elif dtype == "mark_scheme":
                grouped[key]["mark_scheme_url"] = url
            elif dtype == "examiner_report":
                grouped[key]["examiner_report_url"] = url

        return [
            v
            for v in grouped.values()
            if (v.get("question_paper_url") or v.get("mark_scheme_url") or v.get("examiner_report_url"))
        ]

    def _click_next_if_present() -> bool:
        # Drupal pager next
        for css in ["li.pager__item--next a", "a[rel='next']", "a[title*='Go to next page']"]:
            nxt = driver.find_elements(By.CSS_SELECTOR, css)
            if nxt:
                nxt[0].click()
                time.sleep(1.8)
                return True
        return False

    driver.get(past_papers_url)
    if not _wait_cloudflare_clear(driver):
        raise RuntimeError("Cloudflare challenge did not clear for past papers page")
    _dismiss_cookie_banner(driver)

    # Read available year options
    def _read_option_values(selector: str) -> List[tuple]:
        sel = Select(driver.find_element(By.CSS_SELECTOR, selector))
        return [((o.text or "").strip(), (o.get_attribute("value") or "")) for o in sel.options]

    year_opts = _read_option_values("select[name^='field_year_target_id_selective']")
    series_opts = _read_option_values("select[name^='field_series_target_id_selective']")
    type_opts = _read_option_values("select[name^='field_past_paper_type_target_id_selective']")

    # Prefer Standard papers; keep Series Any (some pages only have Summer) and Year iterate.
    # Grab values safely (some selects use empty value for - Any -)
    any_series_val = series_opts[0][1] if series_opts else ""
    # prefer Standard if available, else Any
    standard_val = None
    for txt, val in type_opts:
        if txt.strip().lower() == "standard":
            standard_val = val
            break
    if standard_val is None:
        standard_val = type_opts[0][1] if type_opts else ""

    years = []
    for txt, val in year_opts:
        txt = (txt or "").strip()
        if txt.isdigit():
            years.append((int(txt), val))
    years.sort(reverse=True)

    all_sets: Dict[Tuple[int, str, int, Optional[str], Optional[str]], Dict] = {}

    # If no year facet, just scrape current page.
    if not years:
        for s in _collect_page_sets():
            all_sets[(s["year"], s["exam_series"], s["paper_number"], s.get("component_code"), s.get("tier"))] = s
        return list(all_sets.values())

    for _, year_val in years:
        _apply_filters(year_value=year_val, series_value=any_series_val, type_value=standard_val)

        # paginate for this year
        while True:
            for s in _collect_page_sets():
                all_sets[(s["year"], s["exam_series"], s["paper_number"], s.get("component_code"), s.get("tier"))] = s
            if not _click_next_if_present():
                break

        # Reset back to the base URL for the next year to avoid stale pager state.
        driver.get(past_papers_url)
        if not _wait_cloudflare_clear(driver):
            break
        time.sleep(1.0)

    return list(all_sets.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", help="Filter subject by name (partial match)")
    parser.add_argument("--limit-subjects", type=int)
    args = parser.parse_args()

    # dynamic import (project-root file)
    import importlib.util

    upload_path = ROOT / "upload_papers_to_staging.py"
    spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    upload_papers_to_staging = mod.upload_papers_to_staging

    subjects = load_subjects_from_repo()
    if args.subject:
        subjects = [s for s in subjects if args.subject.lower() in s.name.lower()]
    if args.limit_subjects:
        subjects = subjects[: args.limit_subjects]

    if not subjects:
        print("[WARN] No subjects matched.")
        return 0

    # Ensure subjects exist in staging
    sb = load_supabase()

    driver = None
    ok = 0
    skipped = 0
    failed = 0
    try:
        driver = init_driver()
        for s in subjects:
            subject_code = f"CCEA-GCSE-{slugify_code(s.name)}"
            # Ensure subject row exists (papers uploader looks it up by subject_code/exam_board/qual)
            sb.table("staging_aqa_subjects").upsert(
                {
                    "exam_board": EXAM_BOARD,
                    "qualification_type": QUAL_TYPE,
                    "subject_name": s.name,
                    "subject_code": subject_code,
                    "specification_url": s.specification_url,
                },
                on_conflict="subject_code,qualification_type,exam_board",
            ).execute()

            try:
                # Use the subject-specific past papers URL from the markdown-derived list.
                # The subject page often links to a generic finder page which requires interactive filtering.
                sets = scrape_past_papers_page(driver, s.past_papers_url)
                if not sets:
                    print(f"[WARN] {s.name}: 0 paper sets found")
                    skipped += 1
                    continue
                # Critical: cache CCEA PDFs into Supabase Storage so Railway extraction won't 403
                sets = cache_ccae_pdfs_in_sets(
                    sb,
                    driver,
                    subject_code=subject_code,
                    past_papers_url=s.past_papers_url,
                    sets=sets,
                )
                uploaded = upload_papers_to_staging(
                    subject_code=subject_code,
                    qualification_type=QUAL_TYPE,
                    papers_data=sets,
                    exam_board=EXAM_BOARD,
                )
                print(f"[OK] {s.name}: uploaded {uploaded} paper sets")
                ok += 1
                time.sleep(0.8)
            except Exception as e:
                print(f"[ERROR] {s.name}: {e}")
                failed += 1
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    print(f"[DONE] ok={ok} skipped={skipped} failed={failed} total={len(subjects)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())


