"""
WJEC GCSE Physics (3420) - Topics Scraper
Spec:
  https://www.wjec.co.uk/media/0drne4lc/wjec-gcse-physics-spec-from-2016.pdf
"""

from __future__ import annotations

from pathlib import Path

from _wjec_gcse_separate_science_common import (
    _force_utf8_stdio,
    download_pdf_text,
    parse_separate_science,
    upload_to_staging,
)


SUBJECT = {
    "name": "Physics",
    "code": "WJEC-3420",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/0drne4lc/wjec-gcse-physics-spec-from-2016.pdf",
}


UNIT_TITLES = {
    1: "Unit 1: Conceptual Physics",
    2: "Unit 2: Physics in Action",
}


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC GCSE PHYSICS (3420) - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3420-spec.txt")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}")

    nodes = parse_separate_science(text=text, unit_titles=UNIT_TITLES, unit_nums=(1, 2))
    levels = {}
    for n in nodes:
        levels[n.level] = levels.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("\n[OK] WJEC 3420 Physics topics scrape complete.")


if __name__ == "__main__":
    main()


