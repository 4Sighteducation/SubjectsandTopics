"""
WJEC GCSE Cymraeg Language and Literature (3030) - Double Award (CD) Topics Scraper

Spec (Teaching from 2025 / award from 2027):
  https://www.wjec.co.uk/media/hysc5tin/wjec-gcse-iaith-a-llenyddiaeth-gymraeg-specification.pdf

Double Award requires Units: 1, 2, 3, 4b, 5, 6
"""

from __future__ import annotations

from pathlib import Path

from _wjec_gcse_cymraeg_3030_common import (
    Node,
    _force_utf8_stdio,
    download_pdf_text,
    parse_cymraeg_units,
    upload_to_staging,
)


SUBJECT = {
    "name": "Iaith a Llenyddiaeth Gymraeg (Double Award)",
    "code": "WJEC-3030CD",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/hysc5tin/wjec-gcse-iaith-a-llenyddiaeth-gymraeg-specification.pdf",
}


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC GCSE IAITH A LLENYDDIAETH GYMRAEG (3030CD) - TOPICS SCRAPER (DOUBLE)")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3030-cymraeg-spec.txt")
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}\n")

    nodes: list[Node] = parse_cymraeg_units(text, include_units={"U1", "U2", "U3", "U4b", "U5", "U6"})

    counts: dict[int, int] = {}
    for n in nodes:
        counts[n.level] = counts.get(n.level, 0) + 1
    print("[INFO] Level breakdown:")
    for lvl in sorted(counts):
        print(f"  - L{lvl}: {counts[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("\n[OK] WJEC 3030CD Cymraeg (Double) topics scrape complete.")


if __name__ == "__main__":
    main()


