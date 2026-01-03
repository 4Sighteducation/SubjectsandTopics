"""
SQA National Qualifications - Papers Scraper (National 5 + Highest Level)
========================================================================

Goal
----
For as many SQA subjects as possible, scrape:
- National 5 (if available)
- Highest available of {Advanced Higher, Higher}

For each selected (subject, level) we extract:
- Course specification PDF link (from the "Course Specification" accordion)
- Past paper PDFs + marking instruction PDFs (from the "Past Papers and Marking Instructions" accordion)

Why Selenium?
------------
SQA level pages render only a partial set of links in the initial HTML.
The full "Past Papers and Marking Instructions" list is populated when the accordion is expanded.
So we use Selenium to expand accordions and then parse the post-interaction DOM.

Upload
------
Uploads into Supabase staging tables using the existing generic uploader:
- staging_aqa_subjects (exam_board='SQA', qualification_type in {'National 5','Higher','Advanced Higher'})
- staging_aqa_exam_papers via upload_papers_to_staging(subject_code, qualification_type, exam_board='SQA')
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scrapers.CCEA.ccea_common import load_supabase, slugify_code  # noqa: E402


SQA_BASE = "https://www.sqa.org.uk"
SQA_SUBJECT_INDEX = f"{SQA_BASE}/sqa/45625.html"
SQA_PASTPAPERS_FIND = f"{SQA_BASE}/pastpapers/findpapers.htm"

EXAM_BOARD = "SQA"

LEVEL_ORDER = ["National 5", "Higher", "Advanced Higher"]


@dataclass(frozen=True)
class SQASubject:
    name: str
    subject_url: str


def _norm_url(u: str, base: str) -> str:
    u = (u or "").strip()
    if not u:
        return u
    # SQA often uses root-relative-ish links without a leading slash, e.g. "files_ccc/..." or "pastpapers/...".
    # urljoin(level_url, "files_ccc/x.pdf") incorrectly yields ".../sqa/files_ccc/x.pdf", so we special-case.
    if re.match(r"^(files(_ccc)?/|pastpapers/)", u):
        return urljoin(SQA_BASE + "/", u)
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return urljoin(base, u)
    if u.startswith("http"):
        return u
    return urljoin(base, u)


def _requests_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    return s


def _get_with_retry(session: requests.Session, url: str, *, timeout: int = 30, retries: int = 5) -> requests.Response:
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_err = e
            time.sleep(min(2**attempt, 20))
    raise RuntimeError(f"GET failed after retries: {url} ({last_err})") from last_err


def load_subjects_from_index() -> List[SQASubject]:
    """
    Parse the SQA National Qualifications subjects page for subject links.
    """
    session = _requests_session()
    r = _get_with_retry(session, SQA_SUBJECT_INDEX, timeout=30, retries=5)
    soup = BeautifulSoup(r.text, "html.parser")

    # Reliable: numeric relative links like "45723.html" in the body correspond to subjects.
    main = soup.find("main") or soup
    out: List[SQASubject] = []
    seen: set[str] = set()

    for a in main.find_all("a", href=True):
        name = " ".join(a.get_text(" ", strip=True).split())
        href = (a.get("href") or "").strip()
        if not name:
            continue
        if not re.fullmatch(r"\d+\.html", href):
            continue
        if name.strip().lower() == "national qualifications":
            continue
        url = _norm_url(href, SQA_SUBJECT_INDEX)
        if url in seen:
            continue
        seen.add(url)
        out.append(SQASubject(name=name, subject_url=url))

    out.sort(key=lambda s: s.name.lower())
    return out


#
# NOTE: This scraper intentionally uses requests-only. SQA exposes the past papers list via
# /pastpapers/findpapers.htm and Selenium proved unreliable/hang-prone in automation.
#


def _extract_level_links(subject_html: str, subject_url: str) -> Dict[str, str]:
    """
    From a subject page (e.g. Biology), extract level tab links:
    National 3/4/5, Higher, Adv Higher.
    """
    soup = BeautifulSoup(subject_html, "html.parser")
    links: Dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text(" ", strip=True).split())
        if not text:
            continue
        if text not in {"National 3", "National 4", "National 5", "Higher", "Adv Higher", "Advanced Higher"}:
            continue
        href = _norm_url(a["href"], subject_url)
        label = "Advanced Higher" if text == "Adv Higher" else text
        links[label] = href
    return links


def choose_target_levels(level_links: Dict[str, str]) -> Dict[str, str]:
    """
    Return {level_name: level_url} for the requested scrape:
    - National 5 if present
    - Advanced Higher if present else Higher if present
    """
    out: Dict[str, str] = {}
    if "National 5" in level_links:
        out["National 5"] = level_links["National 5"]
    if "Advanced Higher" in level_links:
        out["Advanced Higher"] = level_links["Advanced Higher"]
    elif "Higher" in level_links:
        out["Higher"] = level_links["Higher"]
    return out


def _get_level_links_with_fallback(session: requests.Session, *, subject_url: str) -> Dict[str, str]:
    """
    Requests-only.
    Note: A small subset of subjects may redirect to hub pages (e.g. Modern Languages). If we
    need to handle those later, we'll add a dedicated requests-only hub parser.
    """
    r = _get_with_retry(session, subject_url, timeout=30, retries=5)
    return _extract_level_links(r.text, subject_url)


def _short_level(level_name: str) -> Optional[str]:
    if level_name == "National 5":
        return "N5"
    if level_name == "Higher":
        return "H"
    if level_name == "Advanced Higher":
        return "NAH"
    return None


def _parse_spec_pdf_from_level_page(html: str, base_url: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    # Prefer course spec PDFs
    candidates = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = " ".join(a.get_text(" ", strip=True).split()).lower()
        if ".pdf" not in href.lower():
            continue
        if "course specification" in text or "course-spec" in href.lower() or "course_spec" in href.lower():
            candidates.append(_norm_url(href, base_url))
    return candidates[0] if candidates else None


def _year_from_text_or_href(text: str, href: str) -> Optional[int]:
    for s in (text, href):
        m = re.search(r"\b(20\d{2})\b", s or "")
        if m:
            return int(m.group(1))
    # /2025/ segment
    m = re.search(r"/(20\d{2})/", href or "")
    if m:
        return int(m.group(1))
    return None


def _component_from_text_or_href(text: str, href: str) -> Tuple[int, Optional[str]]:
    t = (text or "").lower()
    h = (href or "").lower()
    # Section 1 / Section 2
    m = re.search(r"\bsection\s*(\d+)\b", t)
    if not m:
        m = re.search(r"_section(\d+)_", h)
    if m:
        n = int(m.group(1))
        return n, f"S{n}"
    # Paper 1 / Paper 2
    m = re.search(r"\bpaper\s*(\d+)\b", t)
    if not m:
        m = re.search(r"_paper(\d+)[^0-9]", h)
    if m:
        n = int(m.group(1))
        return n, f"P{n}"
    # Assignment
    if "assignment" in t or "_assignment_" in h:
        return 1, "ASSIGN"
    # Question paper (single)
    if "_qp_" in h or "question paper" in t:
        return 1, "QP"
    return 1, None


def _is_mark_scheme(text: str, href: str) -> bool:
    t = (text or "").lower()
    h = (href or "").lower()
    return (
        "marking instruction" in t
        or "marking instructions" in t
        or "/instructions/" in h
        or h.split("/")[-1].lower().startswith("mi_")
        or "_mi_" in h
    )


def _is_question_paper(text: str, href: str) -> bool:
    t = (text or "").lower()
    h = (href or "").lower()
    if "specimen" in t or "specimen" in h:
        return False
    return (
        "/papers/papers/" in h
        or "question" in t
        or "past paper" in t
        or ("paper" in t and "marking" not in t)
        or "_qp_" in h
        or "_section" in h
        or "_paper" in h
        or "_assignment_" in h
    )


def _collect_papers_from_level_page(html: str, base_url: str) -> List[Dict]:
    """
    Build grouped paper sets matching upload_papers_to_staging expected format.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Collect raw pdf-ish links.
    raw: List[Tuple[str, str]] = []
    for a in soup.find_all("a", href=True):
        href = _norm_url(a["href"], base_url)
        text = " ".join(a.get_text(" ", strip=True).split())
        if not href:
            continue
        if ".pdf" not in href.lower():
            continue
        raw.append((text, href))

    # Separate mark schemes and question papers
    mark_links = []
    qp_links = []
    for text, href in raw:
        if _is_mark_scheme(text, href):
            mark_links.append((text, href))
        elif _is_question_paper(text, href):
            qp_links.append((text, href))

    # Index mark schemes by year (and maybe component if detectable)
    marks_by_year: Dict[int, List[Tuple[str, str]]] = {}
    for text, href in mark_links:
        y = _year_from_text_or_href(text, href)
        if not y:
            continue
        marks_by_year.setdefault(y, []).append((text, href))

    grouped: Dict[Tuple[int, str, int, Optional[str], Optional[str]], Dict] = {}
    for text, href in qp_links:
        y = _year_from_text_or_href(text, href)
        if not y:
            continue
        paper_number, component_code = _component_from_text_or_href(text, href)
        series = "May"
        key = (y, series, paper_number, component_code, None)
        if key not in grouped:
            grouped[key] = {
                "year": y,
                "exam_series": series,
                "paper_number": paper_number,
                "component_code": component_code,
                "tier": None,
                "question_paper_url": None,
                "mark_scheme_url": None,
                "examiner_report_url": None,
            }
        grouped[key]["question_paper_url"] = href

        # Attach a marking instruction if available.
        if y in marks_by_year:
            # If there is exactly one MI for the year, attach it.
            if len(marks_by_year[y]) == 1:
                grouped[key]["mark_scheme_url"] = marks_by_year[y][0][1]
            else:
                # Try to choose the MI that best matches component tokens.
                best = None
                if component_code:
                    for mt, mh in marks_by_year[y]:
                        if component_code.lower() in (mt or "").lower() or component_code.lower() in (mh or "").lower():
                            best = mh
                            break
                grouped[key]["mark_scheme_url"] = best or marks_by_year[y][0][1]

    return list(grouped.values())


def _fetch_pastpapers_html(session: requests.Session, *, subject_name: str, level_name: str) -> str:
    """
    The SQA course pages load the past papers list via AJAX:
      /pastpapers/findpapers.htm?subject=<SUBJECT>&level=<N5|H|NAH>
    This is far more reliable than Selenium accordion clicking.
    """
    short = _short_level(level_name)
    if not short:
        return ""
    subj = quote((subject_name or "").replace(":", "").strip())
    url = f"{SQA_PASTPAPERS_FIND}?subject={subj}&level={short}"
    r = _get_with_retry(session, url, timeout=40, retries=5)
    return r.text or ""


def scrape_level(session: requests.Session, level_url: str, *, subject_name: str, level_name: str) -> Tuple[Optional[str], List[Dict]]:
    # Spec link comes from the level page itself.
    level_html = _get_with_retry(session, level_url, timeout=40, retries=5).text
    spec_url = _parse_spec_pdf_from_level_page(level_html, level_url)

    # Paper sets come from the dedicated pastpapers endpoint (what the accordion loads).
    past_html = _fetch_pastpapers_html(session, subject_name=subject_name, level_name=level_name)
    paper_sets = _collect_papers_from_level_page(past_html, SQA_BASE)
    return spec_url, paper_sets


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", help="Filter subject by name (partial match)")
    parser.add_argument("--limit-subjects", type=int)
    parser.add_argument("--headless", action="store_true", help="Run Chrome headless (default)")
    parser.add_argument("--no-headless", action="store_true", help="Run Chrome visible")
    parser.add_argument("--dry-run", action="store_true", help="Do not upload to staging; just print counts")
    parser.add_argument("--debug", action="store_true", help="Verbose debug output (prints link classification counts)")
    parser.add_argument(
        "--resume-missing",
        action="store_true",
        help="Only process subject/level pairs missing paper sets in staging (paper_sets=0).",
    )
    args = parser.parse_args()

    print(
        f"[START] sqa papers | subject={args.subject!r} limit_subjects={args.limit_subjects} "
        f"dry_run={bool(args.dry_run)} resume_missing={bool(args.resume_missing)}",
        flush=True,
    )

    headless = True
    if args.no_headless:
        headless = False

    upload_path = ROOT / "upload_papers_to_staging.py"
    spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    upload_papers_to_staging = mod.upload_papers_to_staging

    subjects = load_subjects_from_index()
    if args.subject:
        subjects = [s for s in subjects if args.subject.lower() in s.name.lower()]
    if args.limit_subjects:
        subjects = subjects[: args.limit_subjects]

    if not subjects:
        print("[WARN] No subjects matched.")
        return 0

    sb = load_supabase()
    session = _requests_session()

    ok = 0
    skipped = 0
    failed = 0

    try:
        for subj in subjects:
            try:
                level_links = _get_level_links_with_fallback(session, subject_url=subj.subject_url)
                targets = choose_target_levels(level_links)
                if not targets:
                    print(f"[SKIP] {subj.name}: no National 5 / Higher / Advanced Higher tabs found")
                    skipped += 1
                    continue

                for level_name in LEVEL_ORDER:
                    if level_name not in targets:
                        continue
                    level_url = targets[level_name]
                    subject_code = f"SQA-{slugify_code(level_name)}-{slugify_code(subj.name)}"

                    if args.resume_missing and not args.dry_run:
                        try:
                            existing = (
                                sb.table("staging_aqa_subjects")
                                .select("id")
                                .eq("exam_board", EXAM_BOARD)
                                .eq("qualification_type", level_name)
                                .eq("subject_code", subject_code)
                                .maybe_single()
                                .execute()
                                .data
                            )
                            if existing and existing.get("id"):
                                cnt = (
                                    sb.table("staging_aqa_exam_papers")
                                    .select("id", count="exact")
                                    .eq("subject_id", existing["id"])
                                    .execute()
                                    .count
                                    or 0
                                )
                                if cnt > 0:
                                    continue
                        except Exception:
                            # If the resume check fails, proceed to scrape.
                            pass

                    spec_url, sets = scrape_level(session, level_url, subject_name=subj.name, level_name=level_name)
                    if not spec_url:
                        # Still insert subject row, but warn
                        spec_url = level_url
                        print(f"[WARN] {subj.name} ({level_name}): spec PDF not found; using level URL as placeholder")

                    if args.debug:
                        # Print a compact diagnostic summary (from the pastpapers endpoint content).
                        soup = BeautifulSoup(_fetch_pastpapers_html(session, subject_name=subj.name, level_name=level_name), "html.parser")
                        pdf_hrefs = []
                        for a in soup.find_all("a", href=True):
                            href = _norm_url(a["href"], SQA_BASE)
                            if ".pdf" in (href or "").lower():
                                pdf_hrefs.append(href)
                        qps = sum(1 for href in pdf_hrefs if _is_question_paper("", href))
                        mis = sum(1 for href in pdf_hrefs if _is_mark_scheme("", href))
                        print(
                            f"[DEBUG] {subj.name} ({level_name}): pdf_links={len(pdf_hrefs)} qp_like={qps} mi_like={mis} sets={len(sets)}"
                        )
                        if not sets and pdf_hrefs:
                            print("[DEBUG] sample pdf hrefs:")
                            for h in pdf_hrefs[:12]:
                                print("  -", h)

                    if not args.dry_run:
                        sb.table("staging_aqa_subjects").upsert(
                            {
                                "exam_board": EXAM_BOARD,
                                "qualification_type": level_name,
                                "subject_name": subj.name,
                                "subject_code": subject_code,
                                "specification_url": spec_url,
                            },
                            on_conflict="subject_code,qualification_type,exam_board",
                        ).execute()

                    if not sets:
                        print(f"[WARN] {subj.name} ({level_name}): 0 paper sets found")
                        continue

                    if args.dry_run:
                        print(f"[DRY] {subj.name} ({level_name}): paper_sets={len(sets)} spec={'yes' if spec_url else 'no'}")
                    else:
                        uploaded = upload_papers_to_staging(
                            subject_code=subject_code,
                            qualification_type=level_name,
                            papers_data=sets,
                            exam_board=EXAM_BOARD,
                        )
                        print(f"[OK] {subj.name} ({level_name}): uploaded {uploaded} paper sets")
                        time.sleep(0.4)

                ok += 1
            except Exception as e:
                print(f"[ERROR] {subj.name}: {e}")
                failed += 1
    finally:
        pass

    print(f"[DONE] ok={ok} skipped={skipped} failed={failed} total={len(subjects)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())


