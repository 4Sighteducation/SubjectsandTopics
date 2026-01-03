"""
OCR Vocational (Cambridge Technicals / Cambridge Nationals) - Assessment Page Papers Scraper
==========================================================================================

Scrapes PDFs from OCR qualification "Assessment" pages that contain:
- Tabs for Level 2 / Level 3
- Accordions per exam series/year listing PDFs:
  - Question paper
  - Mark scheme
  - Examiners' report

Examples:
- Technicals (Engineering, Level 3 tab):
  https://www.ocr.org.uk/qualifications/cambridge-technicals/engineering/assessment/#level-3
- Nationals (Engineering Design, Level 2):
  https://www.ocr.org.uk/qualifications/cambridge-nationals/engineering-design-level-1-2-j822/assessment/

Uploads grouped paper sets into:
  staging_aqa_exam_papers
using upload_papers_to_staging.py

Usage:
  python scrape-ocr-vocational-assessment-papers.py \\
    --subject-code OCR-CTEC-ENGINEERING \\
    --qualification-type CAMBRIDGE_TECHNICALS_L3 \\
    --assessment-url "https://www.ocr.org.uk/qualifications/cambridge-technicals/engineering/assessment/#level-3" \\
    --level level-3

  python scrape-ocr-vocational-assessment-papers.py \\
    --subject-code OCR-CNAT-ENGINEERING_DESIGN \\
    --qualification-type CAMBRIDGE_NATIONALS_L2 \\
    --assessment-url "https://www.ocr.org.uk/qualifications/cambridge-nationals/engineering-design-level-1-2-j822/assessment/" \\
    --level level-2
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# Setup paths to allow importing upload helper
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

import importlib.util

upload_helper_path = PROJECT_ROOT / "upload_papers_to_staging.py"
spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
upload_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(upload_module)
upload_papers_to_staging = upload_module.upload_papers_to_staging


OCR_BASE = "https://www.ocr.org.uk"
SERIES_RE = re.compile(r"\b(June|January|November|May|October)\b", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(20\d{2})\b")


def _abs_url(href: str) -> str:
    href = (href or "").strip()
    if not href:
        return ""
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return urljoin(OCR_BASE, href)
    return href


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _parse_year_series(text: str) -> Tuple[Optional[int], Optional[str]]:
    t = _norm(text)
    ym = YEAR_RE.search(t)
    sm = SERIES_RE.search(t)
    year = int(ym.group(1)) if ym else None
    series = sm.group(1).capitalize() if sm else None
    return year, series


def _classify_doc_type(title: str) -> Optional[str]:
    t = (title or "").lower()
    if "question paper" in t or t.startswith("question paper"):
        return "Question Paper"
    if "mark scheme" in t or t.startswith("mark scheme"):
        return "Mark Scheme"
    if "examiner" in t or "examiners" in t:
        return "Examiner Report"
    return None


def _extract_unit_code(text: str) -> Optional[str]:
    """
    Returns a stable unit identifier from surrounding text.
    Supported:
    - Unit 01 / Unit 23 etc
    - R038 style (Nationals)
    """
    t = _norm(text)
    m = re.search(r"\bUnit\s+([A-Z]{1,3}|\d{1,3})\b", t, flags=re.IGNORECASE)
    if m:
        code = m.group(1).upper()
        if code.isdigit():
            return f"Unit {int(code):02d}"
        return f"Unit {code}"

    m2 = re.search(r"\b(R\d{3})\b", t, flags=re.IGNORECASE)
    if m2:
        return m2.group(1).upper()

    return None


def _paper_number_from_unit(unit_code: str) -> int:
    """
    Convert a unit code to numeric paper_number used by staging.
    - Unit 01 -> 1
    - Unit 23 -> 23
    - R038 -> 38
    Fallback -> 1
    """
    if not unit_code:
        return 1
    m = re.search(r"\bUnit\s+(\d{1,3})\b", unit_code, flags=re.IGNORECASE)
    if m:
        return int(m.group(1))
    m2 = re.search(r"\bR(\d{3})\b", unit_code, flags=re.IGNORECASE)
    if m2:
        return int(m2.group(1))
    return 1


def _find_level_container(soup: BeautifulSoup, level: str) -> BeautifulSoup:
    """
    Best-effort selection of the tab content for a level (level-2 / level-3).
    OCR pages generally include an element with id 'level-2' or 'level-3'.
    """
    level = (level or "").strip().lower()
    if not level:
        return soup
    # Some OCR pages have anchors / tab buttons with id=level-3 that are NOT the content.
    # Only accept an id match if it actually contains PDF links.
    el = soup.find(id=level)
    if el and el.find("a", href=re.compile(r"\.pdf($|\?)", re.IGNORECASE)):
        return el
    el = soup.find(id=level.replace("-", ""))
    if el and el.find("a", href=re.compile(r"\.pdf($|\?)", re.IGNORECASE)):
        return el
    # fallback: if the URL hash is present in-page as anchor
    anchor = soup.find("a", href=re.compile(rf"#{re.escape(level)}$", re.I))
    if anchor:
        container = anchor.find_parent()
        if container:
            return container
    return soup


def scrape_assessment_page(*, assessment_url: str, level: str) -> List[dict]:
    """
    Returns list of grouped paper sets compatible with upload_papers_to_staging():
      {year, exam_series, paper_number, component_code, tier, question_paper_url, mark_scheme_url, examiner_report_url}
    """
    r = requests.get(assessment_url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    container = _find_level_container(soup, level)

    # We group by (year, series, component_code)
    grouped: Dict[Tuple[int, str, str], dict] = {}

    # Iterate all PDF links; associate each with nearest preceding year heading (h4.level-2.heading).
    pdf_links = container.find_all("a", href=True)
    for a in pdf_links:
        href = _abs_url(a.get("href", ""))
        if not href.lower().endswith(".pdf"):
            continue

        title = _norm(a.get_text(" ", strip=True))
        doc_type = _classify_doc_type(title) or _classify_doc_type(href)
        if not doc_type:
            # Skip “Formula booklet”, “Modified papers ZIP”, and other misc PDFs for now
            continue

        # Find nearest previous year heading.
        # Technicals pages: <h4 class="level-2 heading" data-tab="level-3"><span>2024 - June series</span></h4>
        # Nationals pages: headings can be plain h3/h4 without data-tab.
        h = a.find_previous(
            "h4",
            class_=lambda c: c and ("level-2" in str(c)) and ("heading" in str(c)),
        )
        year = series = None
        if h:
            year, series = _parse_year_series(h.get_text(" ", strip=True))
            # Enforce tab (level-2 vs level-3) by heading attribute when present
            desired_tab = (level or "").strip().lower()
            heading_tab = (h.get("data-tab") or "").strip().lower()
            if desired_tab and heading_tab and desired_tab != heading_tab:
                year = series = None  # force fallback

        if not year or not series:
            # Fallback: walk back through generic headings until we find a year+series
            h2 = a.find_previous(["h2", "h3", "h4"])
            while h2:
                year, series = _parse_year_series(h2.get_text(" ", strip=True))
                if year and series:
                    break
                h2 = h2.find_previous(["h2", "h3", "h4"])
            if not year or not series:
                continue

        # Try to capture unit code from the entire list item text (it often contains “Unit 01”)
        li = a.find_parent("li") or a.parent
        context_text = li.get_text(" ", strip=True) if li else title
        unit_code = _extract_unit_code(context_text) or _extract_unit_code(title)
        if not unit_code:
            # As a last resort, key by title (still stable per series heading)
            unit_code = "PAPER"

        component_code = unit_code  # keep human-readable in DB
        paper_number = _paper_number_from_unit(unit_code)

        key = (year, series, component_code)
        if key not in grouped:
            grouped[key] = {
                "year": year,
                "exam_series": series,
                "paper_number": paper_number,
                "component_code": component_code,
                "tier": None,
                "question_paper_url": None,
                "mark_scheme_url": None,
                "examiner_report_url": None,
            }

        if doc_type == "Question Paper":
            grouped[key]["question_paper_url"] = href
        elif doc_type == "Mark Scheme":
            grouped[key]["mark_scheme_url"] = href
        elif doc_type == "Examiner Report":
            grouped[key]["examiner_report_url"] = href

    return list(grouped.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR Vocational assessment-page paper scraper (Technicals/Nationals)")
    parser.add_argument("--subject-code", required=True, help="staging_aqa_subjects.subject_code (e.g. OCR-CTEC-ENGINEERING)")
    parser.add_argument(
        "--qualification-type",
        required=True,
        choices=["CAMBRIDGE_TECHNICALS_L3", "CAMBRIDGE_NATIONALS_L2"],
        help="Must match staging_aqa_subjects.qualification_type",
    )
    parser.add_argument("--assessment-url", required=True, help="OCR qualification assessment page URL")
    parser.add_argument("--level", required=True, choices=["level-2", "level-3"], help="Which tab/level to parse")
    parser.add_argument("--min-year", type=int, default=2019, help="Filter out papers older than this year")
    args = parser.parse_args()

    sets = scrape_assessment_page(assessment_url=args.assessment_url, level=args.level)
    sets = [s for s in sets if s.get("year") and s["year"] >= args.min_year]

    print(f"[OK] Scraped {len(sets)} paper sets from assessment page")
    # Basic breakdown
    by_year: Dict[int, int] = {}
    for s in sets:
        by_year[s["year"]] = by_year.get(s["year"], 0) + 1
    for y in sorted(by_year.keys(), reverse=True):
        print(f"  {y}: {by_year[y]} sets")

    if not sets:
        print("[WARN] No paper sets found; not uploading (and not deleting existing staging papers).")
        return

    uploaded = upload_papers_to_staging(
        subject_code=args.subject_code,
        qualification_type=args.qualification_type,
        papers_data=sets,
        exam_board="OCR",
    )
    print(f"[OK] Uploaded {uploaded} paper sets to staging for {args.subject_code} ({args.qualification_type})")


if __name__ == "__main__":
    main()


