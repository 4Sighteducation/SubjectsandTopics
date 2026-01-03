"""
WJEC GCSE Welsh Second Language (3020) - Topics Scraper (revision-friendly themes)

Spec:
  https://www.wjec.co.uk/media/h03dhvqm/wjec-gcse-welsh-second-lang-spec-2017-e-15-11-2021.pdf

The spec is mostly assessment structure + broad themes (EMPLOYMENT / WALES AND THE WORLD / YOUTH).
We upload a clean hierarchy:

  - L0: Unit 1: Oracy response to visual stimulus
  - L0: Unit 2: Communicating with other people
  - L0: Unit 3: Narrative, specific and instructional
  - L0: Unit 4: Descriptive, creative and imaginative
    Under each:
      - L1: Broad themes
      - L2: Minimal assessment focus shells
"""

from __future__ import annotations

import io
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client


@dataclass(frozen=True)
class Node:
    code: str
    title: str
    level: int
    parent: Optional[str]


SUBJECT = {
    "name": "Welsh Second Language",
    "code": "WJEC-3020",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/h03dhvqm/wjec-gcse-welsh-second-lang-spec-2017-e-15-11-2021.pdf",
}


def _force_utf8_stdio() -> None:
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


THEMES = ["EMPLOYMENT", "WALES AND THE WORLD", "YOUTH"]


def build_nodes() -> list[Node]:
    nodes: list[Node] = []

    def add(code: str, title: str, level: int, parent: Optional[str]) -> None:
        nodes.append(Node(code=code, title=title, level=level, parent=parent))

    units = [
        ("U1", "Unit 1: Oracy response to visual stimulus"),
        ("U2", "Unit 2: Communicating with other people"),
        ("U3", "Unit 3: Narrative, specific and instructional"),
        ("U4", "Unit 4: Descriptive, creative and imaginative"),
    ]

    for ucode, utitle in units:
        add(ucode, utitle, 0, None)

        # Themes
        t_parent = f"{ucode}_THEMES"
        add(t_parent, "Broad themes (context for learning)", 1, ucode)
        for i, t in enumerate(THEMES, start=1):
            add(f"{t_parent}_{i}", t, 2, t_parent)

        # Minimal skills focus
        sk = f"{ucode}_SKILLS"
        add(sk, "Assessment focus (skills)", 1, ucode)
        if ucode in ("U1", "U2"):
            add(f"{sk}_1", "Speaking + Listening (Oracy assessment)", 2, sk)
        else:
            add(f"{sk}_1", "Reading + Writing (examination)", 2, sk)

    # De-dupe
    uniq: list[Node] = []
    seen = set()
    for n in nodes:
        if n.code in seen:
            continue
        seen.add(n.code)
        uniq.append(n)
    return uniq


def upload_to_staging(nodes: list[Node]) -> None:
    env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
    load_dotenv(env_path)
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    subject_result = supabase.table("staging_aqa_subjects").upsert(
        {
            "subject_name": f"{SUBJECT['name']} (GCSE)",
            "subject_code": SUBJECT["code"],
            "qualification_type": "GCSE",
            "specification_url": SUBJECT["pdf_url"],
            "exam_board": SUBJECT["exam_board"],
        },
        on_conflict="subject_code,qualification_type,exam_board",
    ).execute()
    subject_id = subject_result.data[0]["id"]
    print(f"[OK] Subject ID: {subject_id}")

    max_level = max((n.level for n in nodes), default=0)
    deleted_total = 0
    for lvl in range(max_level, -1, -1):
        res = supabase.table("staging_aqa_topics").delete().eq("subject_id", subject_id).eq("topic_level", lvl).execute()
        deleted_total += len(res.data or [])
    print(f"[OK] Cleared old topics ({deleted_total} rows)")

    inserted = supabase.table("staging_aqa_topics").insert(
        [
            {
                "subject_id": subject_id,
                "topic_code": n.code,
                "topic_name": n.title,
                "topic_level": n.level,
                "exam_board": SUBJECT["exam_board"],
            }
            for n in nodes
        ]
    ).execute()
    print(f"[OK] Uploaded {len(inserted.data)} topics")

    code_to_id = {t["topic_code"]: t["id"] for t in inserted.data}
    linked = 0
    for n in nodes:
        if not n.parent:
            continue
        parent_id = code_to_id.get(n.parent)
        child_id = code_to_id.get(n.code)
        if parent_id and child_id:
            supabase.table("staging_aqa_topics").update({"parent_topic_id": parent_id}).eq("id", child_id).execute()
            linked += 1
    print(f"[OK] Linked {linked} relationships")


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC GCSE WELSH SECOND LANGUAGE (3020) - TOPICS UPLOAD (CURATED)")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    nodes = build_nodes()
    levels: dict[int, int] = {}
    for n in nodes:
        levels[n.level] = levels.get(n.level, 0) + 1
    print("[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(nodes)
    print("\n[OK] WJEC 3020 Welsh Second Language topics upload complete.")


if __name__ == "__main__":
    main()






