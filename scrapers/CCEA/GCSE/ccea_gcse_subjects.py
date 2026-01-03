"""
CCEA GCSE subject list + URL extrapolation
=========================================

Parses `scrapers/OCR/GCSE/topics/CCEA - GCSEs.md` (source of truth) and produces
fully-populated URLs for:
- Subject page
- Specification PDF
- Past papers page

We intentionally avoid making HTTP requests to CCEA in this module because CCEA
uses Cloudflare which blocks simple requests; Selenium is used in the papers scraper.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote


SCRAPERS_DIR = Path(__file__).resolve().parents[2]
SOURCE_MD = SCRAPERS_DIR / "OCR" / "GCSE" / "topics" / "CCEA - GCSEs.md"


CCEA_BASE = "https://ccea.org.uk"


@dataclass(frozen=True)
class CCEAGCSESubject:
    name: str
    first_teaching_year: int
    subject_page_url: str
    specification_url: str
    past_papers_url: str


def _clean_name(name: str) -> str:
    n = (name or "").strip()
    # Drop trailing periods (e.g. "Agriculture and Land Use.")
    n = re.sub(r"\.+$", "", n).strip()
    return n


def _slugify(name: str) -> str:
    """
    Create slug for CCEA subject pages.
    Examples from file:
      Agriculture and Land Use -> agriculture-and-land-use
      Art and Design -> art-and-design
    """
    s = _clean_name(name).lower()
    s = s.replace("&", " and ")
    # Normalise special cases seen on CCEA (from existing patterns)
    if s == "learning for life and work":
        s = "learning life and work"
    if s == "irish":
        s = "gaeilge"
    # Remove punctuation but keep word breaks
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"\bthe\b", " ", s)  # CCEA often omits "the" in slugs
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace(" ", "-")
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def build_subject_page_url(name: str, year: int) -> str:
    slug = _slugify(name)
    # Construction is a known CCEA pattern: drop "the" but also drop "and-the" -> "and"
    if slug == "construction-and-the-built-environment":
        slug = "construction-and-built-environment"
    return f"{CCEA_BASE}/key-stage-4/gcse/subjects/gcse-{slug}-{year}"


def build_spec_url(name: str, year: int) -> str:
    # Matches the pattern in the markdown examples.
    subj = _clean_name(name)
    folder = f"GCSE {subj} ({year})"
    filename = f"GCSE {subj} ({year})-specification-Standard.pdf"
    return f"{CCEA_BASE}/downloads/docs/Specifications/GCSE/{quote(folder)}/{quote(filename)}"


def build_past_papers_url(subject_page_url: str) -> str:
    return subject_page_url.rstrip("/") + "/past-papers-mark-schemes"


def parse_gcse_md(md_text: str) -> List[CCEAGCSESubject]:
    lines = [ln.strip() for ln in md_text.splitlines()]
    subjects: List[CCEAGCSESubject] = []

    current_name: Optional[str] = None
    current_year: Optional[int] = None
    subject_page: Optional[str] = None
    spec_url: Optional[str] = None
    papers_url: Optional[str] = None

    def flush():
        nonlocal current_name, current_year, subject_page, spec_url, papers_url
        if not current_name:
            return
        year = current_year or 2017
        subj = _clean_name(current_name)
        sp = subject_page or build_subject_page_url(subj, year)
        su = spec_url or build_spec_url(subj, year)
        pu = papers_url or build_past_papers_url(sp)
        subjects.append(
            CCEAGCSESubject(
                name=subj,
                first_teaching_year=year,
                subject_page_url=sp,
                specification_url=su,
                past_papers_url=pu,
            )
        )
        current_name = None
        current_year = None
        subject_page = None
        spec_url = None
        papers_url = None

    for ln in lines:
        if not ln:
            continue
        # Letter headings
        if re.fullmatch(r"[A-Z]", ln):
            continue
        if ln.lower().startswith("ccea"):
            continue

        # URLs
        if ln.lower().startswith("subject page"):
            m = re.search(r"(https?://\S+)", ln)
            if m:
                subject_page = m.group(1)
            continue
        if ln.lower().startswith("specification"):
            m = re.search(r"(https?://\S+)", ln)
            if m:
                spec_url = m.group(1)
            continue
        if ln.lower().startswith("past papers"):
            m = re.search(r"(https?://\S+)", ln)
            if m:
                papers_url = m.group(1)
            continue

        # Year
        m_year = re.search(r"\b(20\d{2})\b", ln)
        if ln.lower().startswith("first teaching") and m_year:
            current_year = int(m_year.group(1))
            continue

        # New subject name line
        # If we hit a subject name while one is in progress, flush the previous.
        if current_name and (not ln.lower().startswith("first teaching")) and ("http" not in ln.lower()):
            # Some subjects have duplicate "First teaching..." lines; ignore that case above.
            # Treat this as start of next subject.
            flush()

        if current_name is None and ("http" not in ln.lower()) and (not ln.lower().startswith("first teaching")):
            current_name = ln
            continue

    flush()
    return subjects


def load_subjects_from_repo() -> List[CCEAGCSESubject]:
    if not SOURCE_MD.exists():
        raise RuntimeError(f"Missing file: {SOURCE_MD}")
    return parse_gcse_md(SOURCE_MD.read_text(encoding="utf-8"))


