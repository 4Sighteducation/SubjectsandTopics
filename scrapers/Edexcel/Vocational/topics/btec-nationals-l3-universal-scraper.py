"""
Edexcel (Pearson) BTEC Nationals - Level 3 (Vocational) Universal Topics Scraper
===============================================================================

Input list (source of truth):
  BTEC Nationals - Level 3.md

For each subject, we scrape ONLY the units listed on the subject line(s) and upload to staging:
- exam_board = 'EDEXCEL'
- qualification_type = 'BTEC_NATIONALS_L3'

Hierarchy (matches the user's example):
- Level 0: Unit (e.g., Unit 02 - Behaviour and Discipline...)
- Level 1: H1-style headings within the unit (e.g., A Factors affecting behaviour)
- Level 2: H2-style headings (e.g., A1 Principal psychological perspectives...)
- Level 3: bullet headings (e.g., Behaviourist:)
- Level 4: sub-bullets (e.g., emphasis on the role of environmental factors...)

Note:
- Specs are usually PDFs (pearson content/dam). Some links in the list are Pearson pages; we resolve to a PDF.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Allow running as a standalone script
sys.path.append(str(Path(__file__).resolve().parent))

from btec_vocational_common import (  # noqa: E402
    ParsedTopic,
    call_ai,
    download_pdf,
    extract_pdf_text,
    load_supabase,
    parse_numbered_hierarchy,
    resolve_ai_provider,
    slugify,
    upsert_staging_subject,
    replace_subject_topics,
)


ROOT = Path(__file__).resolve().parents[4]
BTEC_MD = ROOT / "BTEC Nationals - Level 3.md"

EXAM_BOARD = "EDEXCEL"
QUALIFICATION_TYPE = "BTEC_NATIONALS_L3"

PEARSON_BASE = "https://qualifications.pearson.com"


@dataclass(frozen=True)
class BtecSubjectSpec:
    subject_name: str
    units: List[Tuple[str, str]]  # [(unit_num_2d, unit_title), ...]
    source_url: str


def _parse_unit_segments(blob: str) -> List[Tuple[str, str]]:
    """
    Parse unit numbers + titles from a blob like:
      "Units 01 Professional Working Responsibilities / Unit 02 - Plant and Soil Science / Unit 03 - Contemporary Issues ..."
    Returns: [("01","Professional Working Responsibilities"), ("02","Plant and Soil Science"), ...]
    """
    if not blob:
        return []

    # Remove URL so it doesn't pollute titles
    s = re.sub(r"https?://\S+", "", blob).strip()

    # Find every "Unit NN" occurrence and slice titles between them.
    hits = list(re.finditer(r"\bUnits?\s*0?(\d{1,2})\b", s, flags=re.I))
    if not hits:
        return []

    out: List[Tuple[str, str]] = []
    for idx, h in enumerate(hits):
        try:
            num = f"{int(h.group(1)):02d}"
        except Exception:
            continue
        start = h.end()
        end = hits[idx + 1].start() if idx + 1 < len(hits) else len(s)
        title = s[start:end].strip()
        # Remove common separators between unit code and title
        title = re.sub(r"^[\s\-–—:,/]+", "", title).strip()
        # Collapse whitespace
        title = " ".join(title.split())
        # Remove trailing separators
        title = title.strip(" -–—:,\t/")
        out.append((num, title))

    # de-dupe by unit number, preserving first title we saw
    seen = set()
    uniq: List[Tuple[str, str]] = []
    for num, title in out:
        if num in seen:
            continue
        seen.add(num)
        uniq.append((num, title))
    return uniq


def parse_btec_md(md_text: str) -> List[BtecSubjectSpec]:
    """
    Parses `BTEC Nationals - Level 3.md` which is loosely structured:
      Subject Name
      Unit 01 ... / Unit 02 ... - https://...pdf
    Some subjects have the URL on the same line, some with weird spacing.
    """
    lines = [ln.strip() for ln in md_text.splitlines()]
    out: List[BtecSubjectSpec] = []

    current_subject: Optional[str] = None
    buffer: List[str] = []

    def flush():
        nonlocal current_subject, buffer
        if not current_subject:
            buffer = []
            return
        blob = " ".join([b for b in buffer if b]).strip()
        if not blob:
            buffer = []
            return

        # Find URL (first http... token)
        m_url = re.search(r"(https?://\S+)", blob)
        if not m_url:
            buffer = []
            return
        url = m_url.group(1).strip()
        units = _parse_unit_segments(blob)
        if not units:
            # some lines might be "Unit 01 -" missing, but generally this should exist
            buffer = []
            return

        out.append(BtecSubjectSpec(subject_name=current_subject, units=units, source_url=url))
        buffer = []

    for ln in lines:
        if not ln:
            continue
        # Skip header
        if ln.lower().startswith("btec nationals"):
            continue

        # Some subjects appear as a clean header line, others appear inline with units + URL (e.g. Agriculture).
        # Subject header line is typically no URL and no "Unit"
        is_subject_header = ("http" not in ln.lower()) and ("unit" not in ln.lower()) and (len(ln) < 80)
        if is_subject_header:
            flush()
            current_subject = ln.strip()
            continue

        # Inline subject + units + URL on one line (Agriculture case)
        if ("http" in ln.lower()) and (current_subject is None):
            # infer subject name from start of line up to the first dash or 'Unit(s)'
            inferred = ln
            if " - " in inferred:
                inferred = inferred.split(" - ", 1)[0]
            inferred = re.split(r"\bUnits?\b", inferred, flags=re.I)[0].strip(" -:\t")
            if inferred:
                current_subject = inferred.strip()
                buffer.append(ln)
                flush()
                current_subject = None
                continue

        # Otherwise treat as part of subject block
        if current_subject:
            buffer.append(ln)
            # If URL present, likely end of block; flush now.
            if "http" in ln.lower():
                flush()

    flush()
    return out


def resolve_spec_pdf_url(source_url: str) -> str:
    """
    If source_url is already a .pdf, return it.
    If it's a Pearson qualification page, attempt to find a PDF spec link.
    """
    if not source_url:
        raise ValueError("Empty source_url")
    if ".pdf" in source_url.lower():
        return source_url

    # Fetch page and look for PDFs that look like "specification" or "spec"
    html = requests.get(source_url, timeout=60, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "html.parser")
    pdfs = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" not in href.lower():
            continue
        abs_url = href
        if href.startswith("/"):
            abs_url = urljoin(PEARSON_BASE, href)
        elif href.startswith("//"):
            abs_url = "https:" + href
        text = " ".join(a.get_text(" ", strip=True).split()).lower()
        pdfs.append((text, abs_url))

    # Prefer ones that look like spec
    for key in ["specification", "specification and sample", "spec", "sample assessment material"]:
        for t, u in pdfs:
            if key in t or key in u.lower():
                return u

    # fallback: first pdf
    if pdfs:
        return pdfs[0][1]

    raise RuntimeError(f"Could not resolve a specification PDF from page: {source_url}")


def _find_best_unit_header_start(full_text: str, unit_n: int) -> Optional[int]:
    """
    Many BTEC specs contain multiple occurrences of "Unit N:" (TOC, headers, body).
    We try to pick the *body* occurrence by scoring proximity to "Essential content" / "Learning aims".
    """
    if not full_text:
        return None
    # NOTE: PDF text extraction is inconsistent about line breaks, so we cannot rely on ^-anchored headers.
    matches = list(re.finditer(rf"\bUnit\s+0?{unit_n}\s*:", full_text, flags=re.I))
    if not matches:
        return None

    best = None
    best_score = -1
    for m in matches:
        start = m.start()
        window = full_text[m.end() : m.end() + 60_000].lower()
        score = 0
        if "essential content" in window:
            score += 10
        if "learning aims" in window:
            score += 5
        if start > 10_000:
            score += 1
        # Prefer later occurrences when scores tie (body tends to be later than TOC)
        if score > best_score or (score == best_score and best is not None and start > best):
            best = start
            best_score = score

    # If nothing scored, use the last occurrence (least likely to be the early TOC)
    if best is None:
        return matches[-1].start()
    return best


def _find_unit_body_span_via_essential_content(full_text: str, unit_n: int) -> Tuple[Optional[int], Optional[int]]:
    """
    Prefer to locate the unit body by finding an "Essential content" heading and mapping it back
    to the nearest preceding "Unit X:" mention. This avoids picking TOC occurrences.
    Returns (start_idx, end_idx). start_idx is at the Essential content heading.
    """
    if not full_text:
        return (None, None)

    essentials = list(re.finditer(r"essential\s+content", full_text, flags=re.I))
    if not essentials:
        return (None, None)

    def nearest_unit_before(idx: int) -> Tuple[Optional[int], Optional[int]]:
        # Look back a bounded window; enough to capture the unit heading preceding "Essential content"
        lo = max(0, idx - 12_000)
        back = full_text[lo:idx]
        hits = list(re.finditer(r"\bUnit\s+(\d{1,2})\s*:", back, flags=re.I))
        if not hits:
            return (None, None)
        last = hits[-1]
        try:
            n = int(last.group(1))
        except Exception:
            return (None, None)
        return (lo + last.start(), n)

    chosen_start = None
    chosen_unit_header = None
    chosen_essential = None

    for e in essentials:
        unit_header_idx, n = nearest_unit_before(e.start())
        if n == unit_n and unit_header_idx is not None:
            chosen_start = e.start()
            chosen_unit_header = unit_header_idx
            chosen_essential = e.start()
            break

    if chosen_start is None or chosen_unit_header is None or chosen_essential is None:
        return (None, None)

    # Find the next Essential content that belongs to a different unit, and end at its unit header.
    end = None
    for e2 in essentials:
        if e2.start() <= chosen_essential:
            continue
        unit_header_idx2, n2 = nearest_unit_before(e2.start())
        if unit_header_idx2 is None:
            continue
        if n2 != unit_n and unit_header_idx2 > chosen_unit_header:
            end = unit_header_idx2
            break

    return (chosen_start, end)


def extract_unit_window(full_text: str, unit_num: str, *, max_chars: int = 220_000) -> str:
    """
    Extract a window of text around the unit section.
    Looks for "Unit 02" / "Unit 2" and returns the following chunk.
    """
    if not full_text:
        return ""
    unit_n = int(unit_num)

    # Primary strategy: anchor on "Essential content" and map back to Unit N
    start, end = _find_unit_body_span_via_essential_content(full_text, unit_n)
    if start is None:
        # Fallback: heuristic start near a Unit N mention
        start = _find_best_unit_header_start(full_text, unit_n) or 0
        end = None

    if end is None:
        chunk = full_text[start : start + max_chars]
    else:
        chunk = full_text[start:end]
        if len(chunk) > max_chars:
            chunk = chunk[:max_chars]
    return chunk


def extract_unit_title(full_text: str, unit_num: str) -> Optional[str]:
    """
    Best-effort extraction of the unit title from the spec text, e.g.
      "Unit 1: Animal Breeding and Genetics"
    """
    if not full_text:
        return None
    unit_n = int(unit_num)
    # Prefer the unit heading that precedes the unit's Essential content.
    start, _ = _find_unit_body_span_via_essential_content(full_text[:900_000], unit_n)
    if start is not None:
        # Look back from Essential content to find the closest Unit N:
        lo = max(0, start - 12_000)
        back = full_text[lo:start]
        hits = list(re.finditer(rf"\bUnit\s+0?{unit_n}\s*:\s*", back, flags=re.I))
        if hits:
            h = hits[-1]
            header_idx = lo + h.start()
            hay = full_text[header_idx : header_idx + 800]
        else:
            hay = full_text[:2000]
    else:
        # Fallback: heuristic
        header_idx = _find_best_unit_header_start(full_text[:900_000], unit_n)
        if header_idx is None:
            return None
        hay = full_text[header_idx : header_idx + 800]

    m = re.search(rf"\bUnit\s+0?{unit_n}\s*:\s*", hay, flags=re.I)
    if not m:
        return f"Unit {unit_n}"

    after = hay[m.end() : m.end() + 240]
    after_norm = " ".join(after.replace("\r", "\n").split())

    # Cut if another unit title leaks in
    cut = re.search(r"\bUnit\s+\d{1,2}\s*:", after_norm, flags=re.I)
    if cut:
        after_norm = after_norm[: cut.start()].strip()

    for marker in [
        "Essential content",
        "Learning aims",
        "Assessment criteria",
        "Summary of assessment",
        "Unit introduction",
        "The supervised assessment",
        "A task set",
    ]:
        idx = after_norm.lower().find(marker.lower())
        if idx > 0:
            after_norm = after_norm[:idx].strip()
            break

    title = re.sub(r"\bPage\s+\d+\b", "", after_norm, flags=re.I).strip(" -:\t")
    title = re.sub(r"\s{2,}", " ", title).strip()
    if not title:
        return f"Unit {unit_n}"
    if len(title) > 140:
        title = title[:140].rsplit(" ", 1)[0].strip()
    return f"Unit {unit_n}: {title}"


def build_prompt(*, subject_name: str, unit_num: str, pdf_text: str) -> str:
    return f"""TASK: Extract curriculum hierarchy from an Edexcel (Pearson) BTEC Nationals Level 3 specification, for ONE unit.

CONTEXT:
- Qualification: BTEC Nationals Level 3
- Subject: {subject_name}
- Target unit: Unit {unit_num}

IMPORTANT SCOPE RULES:
- Extract ONLY content belonging to Unit {unit_num}.
- Ignore assessment guidance, administrative info, grading criteria, and any other units.
- The unit content is typically under headings like "Essential content" and organised as headings + bullets.

OUTPUT FORMAT (CRITICAL):
- Output ONLY a numbered hierarchy. Nothing else.
- Start numbering at 1.
- Max depth = 4.

DO NOT OUTPUT THE UNIT TITLE:
- The unit title itself will be handled separately as Level 0 in our database.
- Your output must start at the FIRST level UNDER the unit (content areas / headings like A, B, C).

HIERARCHY MAPPING (IMPORTANT):
- Level 0 (1, 2, 3, ...): content areas / major headings, usually lettered in the spec like:
  - "A Examine ..." / "B Investigate ..." / "C Examine ..."
- Level 1 (1.1, 1.2, ...): subheadings like A1, A2, A3... (treat these as ONE level, not bullets)
- Level 2 (1.1.1, 1.1.2, ...): detailed curriculum points under the A1/A2 subheading.
  - If the document uses bullets, use each bullet as one Level 2 item.
  - If the document is a paragraph/list without bullet markers, split it into short, atomic curriculum statements WITHOUT inventing anything.
- Level 3 (1.1.1.1, 1.1.1.2, ...): sub-bullets / subpoints (if present).

BULLETS:
- In extracted text, bullets may appear as "•", "o", "-", or weird glyphs.
- Preserve bullet nesting: bullets under a bullet-heading become children; sub-bullets become grandchildren.
- If a bullet wraps across lines, keep it as one item.

PDF TEXT (messy extraction, but contains the content):
{pdf_text}
"""


def scrape_subject(
    *,
    sb,
    provider: str,
    ai_client,
    spec: BtecSubjectSpec,
    unit_filter: Optional[str] = None,
    max_units: Optional[int] = None,
) -> int:
    subject_code = f"EDEXCEL-BTEC-{slugify(spec.subject_name).upper()}"
    pdf_url = resolve_spec_pdf_url(spec.source_url)

    subject_id = upsert_staging_subject(
        sb,
        exam_board=EXAM_BOARD,
        qualification_type=QUALIFICATION_TYPE,
        subject_name=f"BTEC Nationals - {spec.subject_name}",
        subject_code=subject_code,
        specification_url=pdf_url,
    )

    pdf_bytes = download_pdf(pdf_url)
    full_text = extract_pdf_text(pdf_bytes)

    topics: List[ParsedTopic] = []

    units = spec.units
    if unit_filter:
        units = [(n, t) for (n, t) in units if unit_filter.strip() in n]
    if max_units:
        units = units[:max_units]

    for unit_num, unit_title_from_md in units:
        unit_code = f"U{unit_num}"
        unit_topic_code = f"{subject_code}-{unit_code}"
        # L0 title MUST be stable and clean. Prefer the markdown unit title (source of truth).
        md_title = (unit_title_from_md or "").strip()
        if md_title:
            l0_title = f"Unit {int(unit_num)}: {md_title}"
        else:
            l0_title = extract_unit_title(full_text, unit_num) or f"Unit {int(unit_num)}"
        topics.append(ParsedTopic(code=unit_topic_code, title=l0_title, level=0, parent_code=None))

        chunk = extract_unit_window(full_text, unit_num, max_chars=220_000)
        prompt = build_prompt(subject_name=spec.subject_name, unit_num=unit_num, pdf_text=chunk)
        hierarchy = call_ai(provider, ai_client, prompt=prompt, max_tokens=16000)

        parsed = parse_numbered_hierarchy(
            hierarchy,
            code_prefix=f"{subject_code}-{unit_code}",
            base_parent_code=unit_topic_code,
            level_offset=1,
            level_cap=4,
        )
        topics.extend(parsed)

    # Deduplicate by topic_code (AI output can occasionally repeat numbering lines)
    uniq: List[ParsedTopic] = []
    seen = set()
    for t in topics:
        if t.code in seen:
            continue
        uniq.append(t)
        seen.add(t.code)

    inserted = replace_subject_topics(sb, subject_id=subject_id, exam_board=EXAM_BOARD, topics=uniq)
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser(description="Edexcel BTEC Nationals (L3) Universal Topic Scraper (exam units only)")
    parser.add_argument("--subject", help="Filter subject by name (partial match)")
    parser.add_argument("--unit", help="Filter units by 2-digit number (e.g. 02)")
    parser.add_argument("--limit-subjects", type=int, help="Limit number of subjects processed")
    parser.add_argument("--max-units", type=int, help="Max units per subject")
    args = parser.parse_args()

    if not BTEC_MD.exists():
        raise RuntimeError(f"Missing file: {BTEC_MD}")

    specs = parse_btec_md(BTEC_MD.read_text(encoding="utf-8"))
    if args.subject:
        specs = [s for s in specs if args.subject.lower() in s.subject_name.lower()]
    if args.limit_subjects:
        specs = specs[: args.limit_subjects]

    if not specs:
        print("[WARN] No subjects found to scrape.")
        return 0

    sb = load_supabase()
    provider, ai_client = resolve_ai_provider()

    total = 0
    for spec in specs:
        try:
            inserted = scrape_subject(
                sb=sb,
                provider=provider,
                ai_client=ai_client,
                spec=spec,
                unit_filter=args.unit,
                max_units=args.max_units,
            )
            total += inserted
            print(f"[OK] {spec.subject_name}: inserted {inserted} topics")
        except Exception as e:
            print(f"[ERROR] {spec.subject_name} failed: {e}")

    print(f"[DONE] Total inserted topics: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


