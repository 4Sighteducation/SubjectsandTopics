"""
CCEA A-Level (GCE) - Universal Topics Scraper (PDF specs)
=========================================================

Source list:
- `scrapers/OCR/GCSE/topics/CCEA - GCE (ALevels).md` (and extrapolated URLs)

Scrapes:
- CCEA GCE specification PDFs (direct PDF links; not Cloudflare-protected)

Uploads into staging:
- staging_aqa_subjects (exam_board='CCEA', qualification_type='A-Level')
- staging_aqa_topics (topic_code/topic_name/topic_level,parent_topic_id, exam_board='CCEA')

Extraction strategy:
- pdfplumber to extract text
- AI model converts to numbered hierarchy with depth; explicitly pull learning outcomes bullets
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scrapers.CCEA.A_Level.ccea_alevel_subjects import load_subjects_from_repo  # noqa: E402
from scrapers.CCEA.ccea_common import (  # noqa: E402
    call_ai,
    download_pdf,
    extract_pdf_text,
    load_supabase,
    parse_numbered_hierarchy,
    replace_subject_topics,
    resolve_ai_provider,
    slice_relevant_text,
    slugify_code,
    upsert_staging_subject,
)


EXAM_BOARD = "CCEA"
QUAL_TYPE = "A-Level"


def _build_prompt(subject_name: str, *, text: str) -> str:
    return f"""
You are extracting curriculum topics for the CCEA GCE A-Level specification: "{subject_name}".

Return ONLY a numbered hierarchy (no preamble, no markdown).

Rules:
- Use strict numbering with dots:
  1. <Level 0 title>
  1.1 <Level 1 title>
  1.1.1 <Level 2 title>
  1.1.1.1 <Level 3 title>
  1.1.1.1.1 <Level 4 title>  (only if needed)
- Keep titles short and curriculum-focused (no page numbers).
- Use the main units/modules (AS1/AS2/A2 etc) as Level 0 where present.
- IMPORTANT (depth):
  - The spec uses tables with a "Learning Outcomes" column. Capture the *bullet points* under outcomes as Level 3/4.
  - If an outcome statement is long, do NOT copy it verbatim; create a short Level 2 label and put bullets beneath.
- IGNORE:
  - assessment objectives / grade descriptors / administration
  - appendices, glossaries, exemplars

Input text (extracted from PDF):
---
{text}
---
""".strip()


def scrape_one(subject, *, provider: str, client) -> int:
    subject_name = subject.name
    subject_code = f"CCEA-ALEVEL-{slugify_code(subject_name)}"

    sb = load_supabase()
    subject_id = upsert_staging_subject(
        sb,
        exam_board=EXAM_BOARD,
        qualification_type=QUAL_TYPE,
        subject_name=subject_name,
        subject_code=subject_code,
        specification_url=subject.specification_url,
    )

    pdf = download_pdf(subject.specification_url)
    full_text = extract_pdf_text(pdf)
    full_text = (
        full_text.replace("\uf0b7", "• ")
        .replace("●", "• ")
        .replace("•", "\n- ")
    )
    window = slice_relevant_text(
        full_text,
        keywords=[
            "learning outcomes",
            "students should be able to",
            "subject content",
            "content",
            "unit",
            "as 1",
            "as1",
            "as 2",
            "a2",
        ],
        max_chars=260_000,
    )

    hierarchy = call_ai(provider, client, prompt=_build_prompt(subject_name, text=window), max_tokens=14000)
    parsed = parse_numbered_hierarchy(hierarchy, code_prefix=subject_code, base_parent_code=None, level_offset=0, level_cap=4)
    count = replace_subject_topics(sb, subject_id=subject_id, exam_board=EXAM_BOARD, topics=parsed, batch_size=500)
    print(f"[OK] {subject_name}: topics={count}")
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", help="Filter subject by name (partial match)")
    parser.add_argument("--limit-subjects", type=int)
    args = parser.parse_args()

    provider, client = resolve_ai_provider()
    subjects = load_subjects_from_repo()
    if args.subject:
        subjects = [s for s in subjects if args.subject.lower() in s.name.lower()]
    if args.limit_subjects:
        subjects = subjects[: args.limit_subjects]

    if not subjects:
        print("[WARN] No subjects matched.")
        return 0

    ok = 0
    failed = 0
    for s in subjects:
        try:
            scrape_one(s, provider=provider, client=client)
            ok += 1
        except Exception as e:
            failed += 1
            print(f"[ERROR] {s.name}: {e}")

    print(f"[DONE] ok={ok} failed={failed} total={len(subjects)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())






