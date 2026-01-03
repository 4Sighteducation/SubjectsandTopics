"""
Generate expanded CCEA A-Level markdown + JSON from `CCEA - GCE (ALevels).md`.

Outputs:
- scrapers/OCR/GCSE/topics/CCEA - GCE (ALevels) - expanded.md
- scrapers/CCEA/A_Level/ccea-alevel-subjects.json
"""

from __future__ import annotations

import json
from pathlib import Path

from scrapers.CCEA.A_Level.ccea_alevel_subjects import load_subjects_from_repo


SCRAPERS_DIR = Path(__file__).resolve().parents[2]
EXPANDED_MD = SCRAPERS_DIR / "OCR" / "GCSE" / "topics" / "CCEA - GCE (ALevels) - expanded.md"
OUT_JSON = Path(__file__).resolve().parent / "ccea-alevel-subjects.json"


def main() -> int:
    subjects = load_subjects_from_repo()

    OUT_JSON.write_text(
        json.dumps(
            [
                {
                    "name": s.name,
                    "first_teaching_year": s.first_teaching_year,
                    "subject_page_url": s.subject_page_url,
                    "specification_url": s.specification_url,
                    "past_papers_url": s.past_papers_url,
                }
                for s in subjects
            ],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    lines = ["CCEA - GCE (ALevels) (expanded)", ""]
    for s in subjects:
        lines.append(s.name)
        lines.append(f"First teaching from September {s.first_teaching_year}")
        lines.append(f"Subject Page - {s.subject_page_url}")
        lines.append(f"Specification - {s.specification_url}")
        lines.append(f"Past Papers - {s.past_papers_url}")
        lines.append("")
    EXPANDED_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {EXPANDED_MD}")
    print(f"Subjects: {len(subjects)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())






