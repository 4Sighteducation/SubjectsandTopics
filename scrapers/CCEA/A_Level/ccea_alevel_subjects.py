"""
CCEA A-Level (GCE) subject list + URL extrapolation
===================================================

Parses `scrapers/OCR/GCSE/topics/CCEA - GCE (ALevels).md` and produces fully-populated URLs for:
- Subject page
- Specification PDF
- Past papers page
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote


SCRAPERS_DIR = Path(__file__).resolve().parents[2]
SOURCE_MD = SCRAPERS_DIR / "OCR" / "GCSE" / "topics" / "CCEA - GCE (ALevels).md"

CCEA_BASE = "https://ccea.org.uk"


@dataclass(frozen=True)
class CCEAAlevelSubject:
    name: str
    first_teaching_year: int
    subject_page_url: str
    specification_url: str
    past_papers_url: str


def _clean_name(name: str) -> str:
    return (name or "").strip().rstrip(".").strip()


def _slugify(name: str) -> str:
    s = _clean_name(name).lower()
    s = s.replace("&", " and ")
    # CCEA GCE Irish uses Gaeilge slug
    if s == "irish":
        s = "gaeilge"
    # Remove punctuation but keep word breaks
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"\bthe\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace(" ", "-")
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def build_subject_page_url(name: str, year: int) -> str:
    slug = _slugify(name)
    return f"{CCEA_BASE}/post-16/gce/subjects/gce-{slug}-{year}"


def build_spec_url(name: str, year: int) -> str:
    subj = _clean_name(name)
    # Some CCEA pages use older folder years and suffixed filenames (e.g. _0.pdf, _1.pdf).
    # We'll default to the common pattern and allow per-subject overrides below.
    folder = f"GCE {subj} ({year})"
    filename = f"GCE {subj} ({year})-specification-Standard.pdf"
    return f"{CCEA_BASE}/downloads/docs/Specifications/GCE/{quote(folder)}/{quote(filename)}"


def build_past_papers_url(subject_page_url: str) -> str:
    return subject_page_url.rstrip("/") + "/past-papers-mark-schemes"


def parse_alevel_md(md_text: str) -> List[CCEAAlevelSubject]:
    lines = [ln.strip() for ln in md_text.splitlines()]
    subjects: List[CCEAAlevelSubject] = []

    current_name: Optional[str] = None
    current_year: Optional[int] = None
    subject_page: Optional[str] = None
    spec_url: Optional[str] = None
    papers_url: Optional[str] = None

    def flush():
        nonlocal current_name, current_year, subject_page, spec_url, papers_url
        if not current_name:
            return
        year = current_year or 2016
        subj = _clean_name(current_name)
        sp = subject_page or build_subject_page_url(subj, year)
        su = spec_url or build_spec_url(subj, year)
        pu = papers_url or build_past_papers_url(sp)
        subjects.append(
            CCEAAlevelSubject(
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
        if ln.lower().startswith("ccea"):
            continue
        if re.fullmatch(r"[A-Z]", ln):
            continue

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

        m_year = re.search(r"\b(20\d{2})\b", ln)
        if ln.lower().startswith("first teaching") and m_year:
            current_year = int(m_year.group(1))
            continue

        # new subject line
        if current_name and (not ln.lower().startswith("first teaching")) and ("http" not in ln.lower()):
            flush()
        if current_name is None and ("http" not in ln.lower()) and (not ln.lower().startswith("first teaching")):
            current_name = ln
            continue

    flush()
    return subjects


def load_subjects_from_repo() -> List[CCEAAlevelSubject]:
    if not SOURCE_MD.exists():
        raise RuntimeError(f"Missing file: {SOURCE_MD}")
    subjects = parse_alevel_md(SOURCE_MD.read_text(encoding="utf-8"))
    # Known exceptions discovered via Selenium (Cloudflare-protected subject pages):
    # - "Professional Business Services" (First teaching 2023) points to a spec hosted under (2017) with Standard_1.pdf.
    fixed = []
    for s in subjects:
        if s.name.lower() == "professional business services":
            fixed.append(
                CCEAAlevelSubject(
                    name=s.name,
                    first_teaching_year=s.first_teaching_year,
                    subject_page_url=s.subject_page_url,
                    specification_url="https://ccea.org.uk/downloads/docs/Specifications/GCE/GCE%20Professional%20Business%20Services%20%282017%29/GCE%20Professional%20Business%20Services%20%282017%29-specification-Standard_1.pdf",
                    past_papers_url=s.past_papers_url,
                )
            )
        else:
            fixed.append(s)
    return fixed


