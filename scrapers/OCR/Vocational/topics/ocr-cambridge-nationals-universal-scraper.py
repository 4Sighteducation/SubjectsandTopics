"""
OCR Cambridge Nationals (Level 2) - Universal Exam Unit Scraper
===============================================================

Scrapes ONLY the externally assessed unit per subject, as listed in:
  scripts/Cambridge_Vocational_Quals.md

Data model:
- Staging Subject = Cambridge Nationals subject (e.g. Sport Studies)
- Level 0 topics = Examined Unit (e.g. Unit R184: Contemporary issues in sport)
- Level 1 topics = Topic areas
- Level 2 topics = Teaching content headings (often bold in the table)
- Level 3 topics = Bullet points / sub-points under teaching content

We intentionally IGNORE:
- Any “Breadth and depth” columns/sections
- Any exemplification/expansion columns
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

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
QUALIFICATION_TYPE = "CAMBRIDGE_NATIONALS_L2"


def _parse_md_for_nationals(md_text: str) -> Dict[str, Tuple[str, str, str]]:
    """
    Returns mapping:
      subject_name -> (unit_code, unit_title, pdf_url)
    Only reads Cambridge Nationals (Level 2) section, and only the externally assessed unit.
    """
    lines = [ln.strip() for ln in md_text.splitlines()]
    in_nationals = False
    current_subject: Optional[str] = None
    out: Dict[str, Tuple[str, str, str]] = {}

    for ln in lines:
        if not ln:
            continue

        if ln.lower().startswith("cambridge nationals"):
            in_nationals = True
            current_subject = None
            continue

        if ln.lower().startswith("cambridge technicals"):
            in_nationals = False
            current_subject = None
            continue

        if not in_nationals:
            continue

        # Subject header lines like: "Sport Studies Level 1/2"
        m_subj = re.match(r"^(?P<name>.+?)\s+Level\s*1/2\s*$", ln, flags=re.I)
        if m_subj:
            current_subject = m_subj.group("name").strip()
            continue

        # Externally assessed unit lines like:
        # "Externally Asssesed - Unit R184: Contemporary issues in sport - https://...pdf"
        m_unit = re.match(
            r"^(?:Externally\s+Ass+es+ed|Externally\s+Assessed)\s*-\s*Unit\s+(?P<code>R\d+)\s*:\s*(?P<title>.+?)\s*-\s*(?P<url>https?://\S+)$",
            ln,
            flags=re.I,
        )
        if m_unit and current_subject:
            unit_code = m_unit.group("code").strip().upper()
            unit_title = m_unit.group("title").strip()
            url = m_unit.group("url").strip()
            out[current_subject] = (unit_code, unit_title, url)

    return out


def _build_prompt(*, subject_name: str, unit_code: str, unit_title: str, pdf_text: str) -> str:
    return f"""TASK: Extract curriculum hierarchy from an OCR Cambridge Nationals examined unit specification.

CONTEXT:
- Subject: {subject_name}
- Examined unit: {unit_code}: {unit_title}

DOCUMENT STRUCTURE:
The relevant content is in TABLES under "Teaching content" (often alongside other columns like
exemplification and/or breadth and depth).

WHAT TO EXTRACT:
- Extract ONLY the curriculum topics for the examined unit.
- Ignore any column/section named “Breadth and depth”.
- Ignore exemplification/expansion columns.

OUTPUT HIERARCHY:
- Output ONLY a numbered hierarchy. Nothing else.
- Start numbering at 1 (these will become Level 1 under the Unit).
- Max depth = 3 levels in output:
  - Output Level 0: Topic areas (main headings)
  - Output Level 1: Teaching content headings (often bold in the table; treat them as headings)
  - Output Level 2: Bullet points / sub-points under teaching content

BULLET POINTS (CRITICAL):
- Teaching content rows often contain bullet lists.
- In the extracted PDF text, bullets may appear as the glyph "\\uf0b7" (or other bullet-like characters).
- You MUST turn each bullet into its own child line under the relevant teaching content heading.
- Number bullet children as: 1.1.1, 1.1.2, 1.1.3, etc (relative to their parent).
- If a bullet wraps onto the next line, keep it as ONE bullet item.

IMPORTANT:
- Do not include assessment objectives or exam guidance sections.
- Do not invent content; use only what’s explicitly present.

PDF TEXT (best-effort extraction; may be messy due to tables):
{pdf_text}
"""


def scrape_subject(
    *,
    sb,
    provider: str,
    ai_client,
    subject_name: str,
    unit: Tuple[str, str, str],
) -> int:
    unit_code, unit_title, url = unit

    subject_code = f"OCR-CNAT-{slugify(subject_name).upper()}"
    subject_id = upsert_staging_subject(
        sb,
        exam_board=EXAM_BOARD,
        qualification_type=QUALIFICATION_TYPE,
        subject_name=f"Cambridge Nationals - {subject_name}",
        subject_code=subject_code,
        specification_url="",
    )

    topics: List[ParsedTopic] = []

    # Level 0 is the examined unit
    unit_topic_code = f"{subject_code}-{unit_code}"
    topics.append(ParsedTopic(code=unit_topic_code, title=f"{unit_code}: {unit_title}", level=0, parent_code=None))

    pdf_bytes = download_pdf(url)
    full_text = extract_pdf_text(pdf_bytes)
    chunk = slice_relevant_text(
        full_text,
        keywords=["teaching content", "topic area", "learning outcomes", "breadth", "depth"],
        max_chars=220_000,
    )

    prompt = _build_prompt(subject_name=subject_name, unit_code=unit_code, unit_title=unit_title, pdf_text=chunk)
    hierarchy = call_ai(provider, ai_client, prompt=prompt, max_tokens=16000)

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
    parser = argparse.ArgumentParser(description="OCR Cambridge Nationals Universal Scraper (Examined Unit Only)")
    parser.add_argument("--subject", help="Filter subjects by name (partial match)")
    parser.add_argument("--limit-subjects", type=int, help="Limit number of subjects processed")
    args = parser.parse_args()

    if not VOCATIONAL_MD.exists():
        raise RuntimeError(f"Missing file: {VOCATIONAL_MD}")

    md_text = VOCATIONAL_MD.read_text(encoding="utf-8")
    mapping = _parse_md_for_nationals(md_text)

    subjects = sorted(mapping.items(), key=lambda kv: kv[0].lower())
    if args.subject:
        subjects = [(k, v) for (k, v) in subjects if args.subject.lower() in k.lower()]
    if args.limit_subjects:
        subjects = subjects[: args.limit_subjects]

    sb = load_supabase()
    provider, ai_client = resolve_ai_provider()

    total_topics = 0
    for subject_name, unit in subjects:
        inserted = scrape_subject(sb=sb, provider=provider, ai_client=ai_client, subject_name=subject_name, unit=unit)
        total_topics += inserted
        print(f"[OK] {subject_name}: inserted {inserted} topics")

    print(f"[DONE] Total inserted topics: {total_topics}")


if __name__ == "__main__":
    main()


