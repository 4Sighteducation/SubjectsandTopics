"""
OCR Cambridge Technicals (Level 3) - Universal Unit Scraper
===========================================================

Scrapes examinable Unit PDFs listed in:
  scripts/Cambridge_Vocational_Quals.md

Data model:
- Staging Subject = Cambridge Technicals subject (e.g. Applied Science)
- Level 0 topics = Units (e.g. Unit 01 - Science Fundamentals)
- Level 1 topics = Learning outcomes (from table left column)
- Level 2 topics = Teaching content headings/items (e.g. 1.1)
- Level 3 topics = Bullet points under teaching content

We intentionally IGNORE:
- Exemplification column
- “Breadth and depth”
- Practical-only units (not in the markdown list)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Allow running as a standalone script
sys.path.append(str(Path(__file__).resolve().parent))

from ocr_vocational_common import (  # noqa: E402
    ParsedTopic,
    call_ai,
    download_pdf,
    extract_pdf_text,
    load_supabase,
    parse_numbered_hierarchy,
    replace_subject_topics,
    resolve_ai_provider,
    slice_relevant_text,
    slugify,
    upsert_staging_subject,
)


ROOT = Path(__file__).resolve().parents[4]
VOCATIONAL_MD = ROOT / "scripts" / "Cambridge_Vocational_Quals.md"

EXAM_BOARD = "OCR"
QUALIFICATION_TYPE = "CAMBRIDGE_TECHNICALS_L3"


def _parse_md_for_technicals(md_text: str) -> Dict[str, List[Tuple[str, str, str]]]:
    """
    Returns mapping:
      subject_name -> list of (unit_code, unit_title, pdf_url)
    Only reads Cambridge Technicals (Level 3) section.
    """
    lines = [ln.strip() for ln in md_text.splitlines()]
    in_technicals = False
    in_nationals = False
    current_subject: Optional[str] = None
    out: Dict[str, List[Tuple[str, str, str]]] = {}

    for ln in lines:
        if not ln:
            continue

        if ln.lower().startswith("cambridge technicals"):
            in_technicals = True
            in_nationals = False
            current_subject = None
            continue

        if ln.lower().startswith("cambridge nationals"):
            in_nationals = True
            in_technicals = False
            current_subject = None
            continue

        if not in_technicals or in_nationals:
            continue

        # Subject header lines like: "Applied Science Level 3"
        m_subj = re.match(r"^(?P<name>.+?)\s+Level\s*3\s*$", ln, flags=re.I)
        if m_subj:
            current_subject = m_subj.group("name").strip()
            out.setdefault(current_subject, [])
            continue

        # Unit lines supported:
        # - "Unit 01 - Science Fundamentals - https://...pdf"
        # - "Unit CC / Unit 25 - Cloud technology - https://...pdf"
        m_unit = re.match(
            r"^(?:Unit|UNit|UNIT)\s+(?P<code>[A-Z0-9]+)\s*(?:/\s*(?:Unit|UNit|UNIT)\s+(?P<alt>\d+)\s*)?-\s*(?P<title>.+?)\s*-\s*(?P<url>https?://\S+)$",
            ln,
            flags=re.I,
        )
        if m_unit and current_subject:
            raw_code = (m_unit.group("code") or "").strip().upper()
            alt_num = (m_unit.group("alt") or "").strip()

            # Normalize unit code:
            # - numeric -> U01, U02, ...
            # - alphanumeric (e.g. CC) -> CC
            if raw_code.isdigit():
                unit_code = f"U{int(raw_code):02d}"
            else:
                unit_code = raw_code

            unit_title = m_unit.group("title").strip()
            if alt_num:
                unit_title = f"{unit_title} (formerly Unit {alt_num})"

            url = m_unit.group("url").strip()
            out[current_subject].append((unit_code, unit_title, url))

    return out


def _build_prompt(*, subject_name: str, unit_code: str, unit_title: str, pdf_text: str) -> str:
    return f"""TASK: Extract curriculum hierarchy from an OCR Cambridge Technicals Unit specification.

CONTEXT:
- Subject: {subject_name}
- Unit: {unit_code} - {unit_title}

DOCUMENT STRUCTURE:
The relevant content is presented in LANDSCAPE TABLES with columns:
1) Learning outcomes (left)
2) Teaching content (middle)
3) Exemplification (right)

WHAT TO EXTRACT:
- Extract ONLY learning outcomes + teaching content.
- IGNORE the Exemplification column completely.
- IGNORE “Breadth and depth” and any assessment/intro pages.

OUTPUT HIERARCHY RULES:
- Output ONLY a numbered hierarchy. Nothing else.
- Start numbering at 1 (these will become Level 1 under the Unit).
- Max depth = 3 levels in output:
  - Output Level 0: Learning outcomes (e.g. "1 Understand ...")
  - Output Level 1: Teaching content headings/items (e.g. "1.1 The atom is ...")
  - Output Level 2: Bullet points / sub-points that appear under teaching content items

BULLET POINTS (CRITICAL):
- Teaching content rows often contain bullet lists.
- In the extracted PDF text, bullets may appear as the glyph "\\uf0b7" (or other bullet-like characters).
- You MUST turn each bullet into its own child line under the relevant teaching content item.
- Number bullet children as: 1.1.1, 1.1.2, 1.1.3, etc.
- If a bullet wraps onto the next line, keep it as ONE bullet item (don’t split mid-sentence).

IMPORTANT:
- Do not include anything from exemplification.
- Keep titles concise but faithful (don’t invent content).

PDF TEXT (best-effort extraction; may be messy due to tables):
{pdf_text}
"""


def scrape_subject(
    *,
    sb,
    provider: str,
    ai_client,
    subject_name: str,
    units: List[Tuple[str, str, str]],
    unit_filter: Optional[str] = None,
    limit_units: Optional[int] = None,
) -> int:
    # Create a stable subject_code
    subject_code = f"OCR-CTEC-{slugify(subject_name).upper()}"

    subject_id = upsert_staging_subject(
        sb,
        exam_board=EXAM_BOARD,
        qualification_type=QUALIFICATION_TYPE,
        subject_name=f"Cambridge Technicals - {subject_name}",
        subject_code=subject_code,
        specification_url="",
    )

    topics: List[ParsedTopic] = []

    selected_units = units
    if unit_filter:
        selected_units = [u for u in selected_units if unit_filter.lower() in (u[0] + " " + u[1]).lower()]
    if limit_units:
        selected_units = selected_units[:limit_units]

    for unit_code, unit_title, url in selected_units:
        unit_topic_code = f"{subject_code}-{unit_code}"
        topics.append(
            ParsedTopic(code=unit_topic_code, title=f"{unit_code} - {unit_title}", level=0, parent_code=None)
        )

        pdf_bytes = download_pdf(url)
        full_text = extract_pdf_text(pdf_bytes)
        chunk = slice_relevant_text(
            full_text,
            keywords=["teaching content", "learning outcomes", "exemplification"],
            max_chars=220_000,
        )

        prompt = _build_prompt(subject_name=subject_name, unit_code=unit_code, unit_title=unit_title, pdf_text=chunk)
        hierarchy = call_ai(provider, ai_client, prompt=prompt, max_tokens=16000)

        # Parse AI hierarchy; treat AI level 0 as Level 1 under Unit.
        unit_prefix = f"{subject_code}-{unit_code}"
        parsed = parse_numbered_hierarchy(
            hierarchy,
            code_prefix=unit_prefix,
            base_parent_code=unit_topic_code,
            level_offset=1,
            level_cap=3,
        )
        topics.extend(parsed)

    inserted_count = replace_subject_topics(sb, subject_id=subject_id, exam_board=EXAM_BOARD, topics=topics)
    return inserted_count


def main():
    parser = argparse.ArgumentParser(description="OCR Cambridge Technicals Universal Scraper (Examinable Units)")
    parser.add_argument("--subject", help="Filter subjects by name (partial match)")
    parser.add_argument("--unit", help="Filter units within a subject (partial match)")
    parser.add_argument("--limit-subjects", type=int, help="Limit number of subjects processed")
    parser.add_argument("--limit-units", type=int, help="Limit number of units per subject processed")
    args = parser.parse_args()

    if not VOCATIONAL_MD.exists():
        raise RuntimeError(f"Missing file: {VOCATIONAL_MD}")

    md_text = VOCATIONAL_MD.read_text(encoding="utf-8")
    mapping = _parse_md_for_technicals(md_text)

    subjects = sorted(mapping.items(), key=lambda kv: kv[0].lower())
    if args.subject:
        subjects = [(k, v) for (k, v) in subjects if args.subject.lower() in k.lower()]
    if args.limit_subjects:
        subjects = subjects[: args.limit_subjects]

    sb = load_supabase()
    provider, ai_client = resolve_ai_provider()

    total_topics = 0
    for subject_name, units in subjects:
        inserted = scrape_subject(
            sb=sb,
            provider=provider,
            ai_client=ai_client,
            subject_name=subject_name,
            units=units,
            unit_filter=args.unit,
            limit_units=args.limit_units,
        )
        total_topics += inserted
        print(f"[OK] {subject_name}: inserted {inserted} topics")

    print(f"[DONE] Total inserted topics: {total_topics}")


if __name__ == "__main__":
    main()


