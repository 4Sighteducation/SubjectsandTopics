"""
WJEC GCSE German (3820) - Topics Scraper (Units 2, 3, 4 only)

Spec:
  https://www.wjec.co.uk/media/eniouj5u/wjec-gcse-german-spec-from-2016-e-19-11-21.pdf

User requirement:
  - Only Units 2/3/4 are needed (Listening, Reading, Writing). Unit 1 is spoken NEA.

Because the spec is largely assessment-structure + themes/sub-themes (rather than a long,
bullet-by-bullet syllabus), we upload a clean, revision-friendly hierarchy:

  - L0: Unit 2: Listening
  - L0: Unit 3: Reading
  - L0: Unit 4: Writing
    Under each:
      - L1: 3 broad themes
      - L2: sub-themes
      - L3: bullet sub-points

This matches the spec's "context for learning the language" structure.
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
    "name": "German",
    "code": "WJEC-3820",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/eniouj5u/wjec-gcse-german-spec-from-2016-e-19-11-21.pdf",
}


def _force_utf8_stdio() -> None:
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


THEMES = [
    (
        "Identity and culture",
        [
            ("Youth Culture", ["Self and relationships", "Technology and social media"]),
            ("Lifestyle", ["Health and fitness", "Entertainment and leisure"]),
            ("Customs and Traditions", ["Food and drink", "Festivals and celebrations"]),
        ],
    ),
    (
        "Wales and the World – areas of interest",
        [
            ("Home and Locality", ["Local areas of interest", "Travel and Transport"]),
            (
                "The Wider World",
                [
                    "Local and regional features and characteristics of Germany and German-speaking countries",
                    "Holidays and tourism",
                ],
            ),
            ("Global Sustainability", ["Environment", "Social issues"]),
        ],
    ),
    (
        "Current and future study and employment",
        [
            ("Current Study", ["School/college life", "School/college studies"]),
            ("Enterprise, Employability and Future Plans", ["Skills and personal qualities", "Post-16 study", "Career plans", "Employment"]),
        ],
    ),
]


def build_nodes() -> list[Node]:
    nodes: list[Node] = []

    def add(code: str, title: str, level: int, parent: Optional[str]) -> None:
        nodes.append(Node(code=code, title=title, level=level, parent=parent))

    units = [
        ("U2", "Unit 2: Listening"),
        ("U3", "Unit 3: Reading"),
        ("U4", "Unit 4: Writing"),
    ]

    for ucode, utitle in units:
        add(ucode, utitle, 0, None)
        for t_idx, (theme_title, subthemes) in enumerate(THEMES, start=1):
            t_code = f"{ucode}_T{t_idx}"
            add(t_code, theme_title, 1, ucode)
            for s_idx, (sub_title, bullets) in enumerate(subthemes, start=1):
                s_code = f"{t_code}_S{s_idx}"
                add(s_code, sub_title, 2, t_code)
                for b_idx, b in enumerate(bullets, start=1):
                    add(f"{s_code}_b{b_idx:02d}", b, 3, s_code)

        # Quick unit-level skills shell (useful but minimal)
        sk = f"{ucode}_SKILLS"
        add(sk, "Assessment focus (skills)", 1, ucode)
        if ucode == "U2":
            add(f"{sk}_1", "Understand and respond to spoken language", 2, sk)
        elif ucode == "U3":
            add(f"{sk}_1", "Understand and respond to written language", 2, sk)
        else:
            add(f"{sk}_1", "Communicate in writing (incl. translation task)", 2, sk)

    # De-dupe by code
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
    print("WJEC GCSE GERMAN (3820) - TOPICS SCRAPER (U2/U3/U4)")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    nodes = build_nodes()
    levels = {}
    for n in nodes:
        levels[n.level] = levels.get(n.level, 0) + 1
    print("[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(nodes)
    print("\n[OK] WJEC 3820 German topics upload complete.")


if __name__ == "__main__":
    main()






