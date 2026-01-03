"""
WJEC GCSE Welsh Language (3000) - Topics Scraper (curated exam structure)

Spec:
  https://www.wjec.co.uk/media/mvkeqncx/wjec-gcse-welsh-language-spec-from-2015-e-20-03-23.pdf

This spec is best represented as an exam/skill structure (rather than a long content syllabus).
We upload a clean hierarchy:

  - L0: Unit 1: Oracy (NEA)
  - L0: Unit 2: Reading & Writing — Description, Narration and Exposition (Exam)
  - L0: Unit 3: Reading & Writing — Argumentation, Persuasion and Instructional (Exam)

  Under each:
    - L1: Sections/tasks
    - L2/L3: concise bullet points describing requirements and focus areas
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
    "name": "Welsh Language",
    "code": "WJEC-3000",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/mvkeqncx/wjec-gcse-welsh-language-spec-from-2015-e-20-03-23.pdf",
}


def _force_utf8_stdio() -> None:
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def build_nodes() -> list[Node]:
    nodes: list[Node] = []

    def add(code: str, title: str, level: int, parent: Optional[str]) -> None:
        nodes.append(Node(code=code, title=title, level=level, parent=parent))

    # Unit 1: Oracy (NEA)
    add("U1", "Unit 1: Oracy (Non-examination assessment)", 0, None)
    add("U1_T1", "Task 1: Individual Researched Presentation (15%)", 1, "U1")
    add("U1_T1_1", "Based on WJEC set themes (choose one): Wales; Leisure; World of Work; World of Science/Technology; Citizenship", 2, "U1_T1")
    add("U1_T1_2", "Focus: convey information and demonstrate verbal reasoning", 2, "U1_T1")
    add("U1_T2", "Task 2: Responding and Interacting (15%)", 1, "U1")
    add("U1_T2_1", "Group discussion to WJEC written/visual stimulus", 2, "U1_T2")
    add("U1_T2_2", "Focus: express and corroborate opinion; convey experiences and/or persuade", 2, "U1_T2")
    add("U1_MARK", "Marking focus", 1, "U1")
    add("U1_MARK_1", "AO1 credit split: 50% register/accuracy/range; 50% content/organisation", 2, "U1_MARK")
    add("U1_ADMIN", "Evidence/admin", 1, "U1")
    add("U1_ADMIN_1", "Audio or audio-visual recording required for all candidates", 2, "U1_ADMIN")

    # Unit 2: Reading & Writing — D/N/E
    add("U2", "Unit 2 (Exam): Reading and Writing — Description, Narration and Exposition", 0, None)
    add("U2_A", "Section A: Reading (15%)", 1, "U2")
    add("U2_A_1", "At least one description, one narration and one exposition text with a thematic link", 2, "U2_A")
    add("U2_A_2", "Continuous + non-continuous texts (e.g., adverts/diagrams/graphs/tables)", 2, "U2_A")
    add("U2_A_3", "Question styles: short + extended responses (incl. inference/deduction)", 2, "U2_A")
    add("U2_A_4", "Includes editing task (2.5% of qualification total)", 2, "U2_A")
    add("U2_B", "Section B: Writing (20%)", 1, "U2")
    add("U2_B_1", "One extended writing task from a choice of two (description/narration/exposition)", 2, "U2_B")
    add("U2_B_2", "May draw on reading materials from Section A where appropriate", 2, "U2_B")
    add("U2_B_3", "Includes proofreading task (2.5% of qualification total)", 2, "U2_B")
    add("U2_B_4", "Marks split: 50% communication/organisation; 50% accuracy (grammar/punct/spelling)", 2, "U2_B")

    # Unit 3: Reading & Writing — A/P/I
    add("U3", "Unit 3 (Exam): Reading and Writing — Argumentation, Persuasion and Instructional", 0, None)
    add("U3_A", "Section A: Reading (15%)", 1, "U3")
    add("U3_A_1", "At least one argumentation, one persuasion and one instructional text with a thematic link", 2, "U3_A")
    add("U3_A_2", "Continuous + non-continuous texts; range of question styles", 2, "U3_A")
    add("U3_B", "Section B: Writing (20%)", 1, "U3")
    add("U3_B_1", "One compulsory argumentation writing task + one compulsory persuasion writing task", 2, "U3_B")
    add("U3_B_2", "Awareness of audience/purpose; adapt style/form to real-life contexts", 2, "U3_B")
    add("U3_B_3", "Marks split: 50% communication/organisation; 50% accuracy (grammar/punct/spelling)", 2, "U3_B")

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
    print("WJEC GCSE WELSH LANGUAGE (3000) - TOPICS UPLOAD (CURATED)")
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
    print("\n[OK] WJEC 3000 Welsh Language topics upload complete.")


if __name__ == "__main__":
    main()






