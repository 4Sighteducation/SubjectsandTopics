"""
Module form of the WJEC GCSE universal papers scraper.

Keep this file importable (underscores) so batch runners can `import ...`.

CLI wrapper lives in:
  scrapers/WJEC/GCSE/papers/scrape-wjec-gcse-papers-universal.py
"""

from __future__ import annotations

import re
import sys
import time
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Try to use webdriver-manager if available
try:
    from webdriver_manager.chrome import ChromeDriverManager

    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

# Load environment (mainly for upload helper)
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)


def init_driver(headless: bool = True) -> webdriver.Chrome:
    print("🌐 Initializing Chrome WebDriver...")
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    if WEBDRIVER_MANAGER_AVAILABLE:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)

    driver.implicitly_wait(10)
    print("✓ WebDriver initialized")
    return driver


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _classify_doc_type(title: str) -> str | None:
    t = (title or "").lower()
    if "mark scheme" in t:
        return "mark_scheme"
    if "examiner report" in t or "examiner's report" in t or "examiners report" in t:
        return "examiner_report"
    if "past paper" in t or "question paper" in t:
        return "question_paper"
    # Resource material sometimes appears (esp Business); treat as question paper adjunct for now
    if "resource" in t:
        return "question_paper"
    return None


def _parse_series_from_url(url: str) -> tuple[int | None, str | None]:
    clean = (url or "").split("#")[0].split("?")[0]
    series_map = {
        "S": "Summer",
        "W": "Winter",
        "N": "November",
        "J": "January",
    }

    m = re.search(r"/([A-Za-z])(\d{2})/", clean)
    if m:
        code = m.group(1).upper()
        yy = int(m.group(2))
        year = 2000 + yy
        return year, series_map.get(code, code)

    filename = clean.split("/")[-1]
    m2 = re.match(r"^([A-Za-z])(\d{2})-", filename)
    if m2:
        code = m2.group(1).upper()
        yy = int(m2.group(2))
        year = 2000 + yy
        return year, series_map.get(code, code)

    return None, None


def _parse_component_from_url(url: str) -> tuple[int | None, str | None]:
    clean = (url or "").split("#")[0].split("?")[0]
    filename = clean.split("/")[-1]
    if " " in filename:
        filename = filename.split(" ")[0] + ".pdf"

    m = re.search(r"^[A-Za-z]\d{2}-([A-Za-z0-9-]+)\.pdf$", filename)
    if not m:
        return None, None
    doc = m.group(1)
    doc = re.sub(r"-\d{6,8}$", "", doc)
    doc = re.sub(r"-(ms|mark-scheme|rms|er|examiner-report|report)(?:[-_].*)?$", "", doc, flags=re.IGNORECASE)
    doc = doc.upper()

    um = re.search(r"U(\d)", doc)
    paper_number = int(um.group(1)) if um else None
    return paper_number, doc


def _expand_all(driver: webdriver.Chrome) -> None:
    try:
        buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Collapse / Expand all')]")
        if buttons:
            driver.execute_script("arguments[0].click();", buttons[0])
            time.sleep(2)
    except Exception:
        pass

    selectors = [
        "button[aria-expanded='false']",
        ".accordion button",
        ".accordion__header",
        ".accordion-header",
        "[data-toggle='collapse']",
        "summary",
    ]
    expanded = 0
    for selector in selectors:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, selector)
        except Exception:
            continue
        for el in elems[:200]:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(0.05)
                if el.get_attribute("aria-expanded") == "false":
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(0.1)
                    expanded += 1
            except Exception:
                pass
    if expanded:
        print(f"   ✓ Expanded {expanded} sections")

    try:
        year_candidates = driver.find_elements(
            By.XPATH,
            "//*[self::button or self::div or self::a or self::h2 or self::h3 or self::h4][string-length(normalize-space(.))<=6]",
        )
        year_clicked = 0
        for el in year_candidates:
            try:
                txt = _norm(el.text)
                if not re.fullmatch(r"20\d{2}", txt):
                    continue
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(0.05)
                driver.execute_script("arguments[0].click();", el)
                time.sleep(0.1)
                year_clicked += 1
            except Exception:
                pass
        if year_clicked:
            print(f"   ✓ Clicked {year_clicked} year headings")
    except Exception:
        pass


def scrape_wjec_gcse_papers(
    subject_code: str, subject_name: str, pastpapers_url: str, headless: bool = True
) -> list[dict]:
    print("=" * 80)
    print("WJEC GCSE - PAPERS SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {subject_name}")
    print(f"Code: {subject_code}")
    print(f"URL: {pastpapers_url}\n")

    driver = None
    raw_docs: list[dict] = []

    try:
        driver = init_driver(headless=headless)
        print("📂 Navigating...")
        driver.get(pastpapers_url)
        time.sleep(5)

        print("📂 Expanding accordions...")
        _expand_all(driver)

        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(20):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.find_all("a", href=True)
        for a in links:
            href = a.get("href", "").strip()
            text = _norm(a.get_text())
            if not href:
                continue
            if href.startswith("//"):
                href = "https:" + href
            if not re.search(r"\.pdf($|\?)", href, flags=re.IGNORECASE):
                continue
            if "pastpapers.download.wjec.co.uk" not in href and "wjec.co.uk" not in href:
                continue

            doc_type = _classify_doc_type(text) or _classify_doc_type(href)
            year, series = _parse_series_from_url(href)
            paper_number, component_code = _parse_component_from_url(href)
            raw_docs.append(
                {
                    "title": text,
                    "url": href,
                    "doc_type": doc_type,
                    "year": year,
                    "exam_series": series,
                    "paper_number": paper_number,
                    "component_code": component_code,
                }
            )

        print(f"\n✓ Found {len(raw_docs)} PDF links (raw)")
        dts = Counter(d["doc_type"] for d in raw_docs)
        print("   Breakdown (doc_type):", dict(dts))
        years = Counter((d["year"], d["exam_series"]) for d in raw_docs if d.get("year") and d.get("exam_series"))
        if years:
            print("   Breakdown (year/series):", dict(years))

    finally:
        if driver:
            driver.quit()

    paper_sets: dict[str, dict] = {}
    for d in raw_docs:
        if not d.get("year") or not d.get("exam_series") or not d.get("component_code"):
            continue
        key = f"{d['year']}-{d['exam_series']}-{d['component_code']}"
        if key not in paper_sets:
            paper_sets[key] = {
                "year": d["year"],
                "exam_series": d["exam_series"],
                "paper_number": d.get("paper_number") or 1,
                "component_code": d.get("component_code"),
                "tier": None,
                "question_paper_url": None,
                "mark_scheme_url": None,
                "examiner_report_url": None,
            }
        if d["doc_type"] == "mark_scheme":
            paper_sets[key]["mark_scheme_url"] = d["url"]
        elif d["doc_type"] == "examiner_report":
            paper_sets[key]["examiner_report_url"] = d["url"]
        else:
            paper_sets[key]["question_paper_url"] = d["url"]

    sets = list(paper_sets.values())
    print(f"✓ Grouped into {len(sets)} paper sets")
    return sets


def main() -> None:
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    # This module doesn't upload directly (wrapper script does).
    # Keeping main only for compatibility if needed later.
    raise SystemExit("Use scrape-wjec-gcse-papers-universal.py for CLI execution.")






