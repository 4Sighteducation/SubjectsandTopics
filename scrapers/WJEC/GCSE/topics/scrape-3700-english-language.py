"""
WJEC GCSE English Language (3700) - Curated Topics Scraper (Exam units focus)

Spec (teaching from 2015 / award from 2017):
  https://www.wjec.co.uk/media/krviytuc/wjec-gcse-english-language-specification-2015-24-10-14-branded.pdf

Note:
The spec does not define a granular, teachable content list like many other WJEC GCSEs.
To make this subject useful in the app (even if lightly used), we upload a curated,
exam-structure-based hierarchy for Units 2 and 3 (the two external exam units).

Hierarchy:
  - L0: Unit 2 (Exam)
    - L1: Section A Reading
    - L1: Section B Writing
  - L0: Unit 3 (Exam)
    - L1: Section A Reading
    - L1: Section B Writing
Under each Section we add practical “revision hooks” such as text types, question types,
and common writing forms.
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
    "name": "English Language",
    "code": "WJEC-3700",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/krviytuc/wjec-gcse-english-language-specification-2015-24-10-14-branded.pdf",
}


def _force_utf8_stdio() -> None:
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def build_nodes() -> list[Node]:
    nodes: list[Node] = []

    def add(code: str, title: str, level: int, parent: Optional[str]) -> None:
        nodes.append(Node(code=code, title=title, level=level, parent=parent))

    # L0s
    u2 = "U2"
    u3 = "U3"
    add(u2, "Unit 2 (Exam): Reading and Writing — Description, Narration and Exposition", 0, None)
    add(u3, "Unit 3 (Exam): Reading and Writing — Argumentation, Persuasion and Instructional", 0, None)

    # Unit 2 sections
    u2a = f"{u2}_A"
    u2b = f"{u2}_B"
    add(u2a, "Section A: Reading (20%)", 1, u2)
    add(u2b, "Section B: Writing (20%)", 1, u2)

    add(f"{u2a}_t", "Text types assessed (thematic link)", 2, u2a)
    add(f"{u2a}_t_desc", "Description text", 3, f"{u2a}_t")
    add(f"{u2a}_t_narr", "Narration text", 3, f"{u2a}_t")
    add(f"{u2a}_t_expo", "Exposition text", 3, f"{u2a}_t")
    add(f"{u2a}_t_cont", "Continuous texts (e.g. autobiography, biography, diaries, speeches, reportage, travel writing, reviews, fiction extracts)", 3, f"{u2a}_t")
    add(f"{u2a}_t_non", "Non-continuous texts (e.g. advertisements, diagrams, lists, graphs, schedules, tables)", 3, f"{u2a}_t")

    add(f"{u2a}_q", "Question types", 2, u2a)
    add(f"{u2a}_q_short", "Short responses (e.g. multiple choice, short constructed response, cloze, sequencing)", 3, f"{u2a}_q")
    add(f"{u2a}_q_long", "Extended responses (e.g. paraphrasing, comprehension in context, analysis/deduction/inference)", 3, f"{u2a}_q")
    add(f"{u2a}_edit", "Editing task (2.5%): word, sentence and text level", 2, u2a)

    add(f"{u2b}_task", "Extended writing task (choice of 2)", 2, u2b)
    add(f"{u2b}_forms", "Possible writing forms", 2, u2b)
    add(f"{u2b}_forms_bio", "Biography / memoir", 3, f"{u2b}_forms")
    add(f"{u2b}_forms_travel", "Travel writing / food writing", 3, f"{u2b}_forms")
    add(f"{u2b}_forms_diary", "Diary / story / personal essay", 3, f"{u2b}_forms")
    add(f"{u2b}_proof", "Proofreading task (2.5%)", 2, u2b)
    add(f"{u2b}_mark", "Marking focus (50/50)", 2, u2b)
    add(f"{u2b}_mark_comm", "Communication & organisation (meaning, purpose, readers, structure)", 3, f"{u2b}_mark")
    add(f"{u2b}_mark_acc", "Accuracy (language, grammar, punctuation, spelling)", 3, f"{u2b}_mark")

    # Unit 3 sections
    u3a = f"{u3}_A"
    u3b = f"{u3}_B"
    add(u3a, "Section A: Reading (20%)", 1, u3)
    add(u3b, "Section B: Writing (20%)", 1, u3)

    add(f"{u3a}_t", "Text types assessed (thematic link)", 2, u3a)
    add(f"{u3a}_t_arg", "Argumentation text", 3, f"{u3a}_t")
    add(f"{u3a}_t_pers", "Persuasion text", 3, f"{u3a}_t")
    add(f"{u3a}_t_instr", "Instructional text (required for Reading only)", 3, f"{u3a}_t")
    add(
        f"{u3a}_t_formats",
        "Possible formats (continuous, non-continuous, digital/multi-modal)",
        2,
        u3a,
    )
    add(f"{u3a}_t_formats_eg", "Letters, emails, factsheets, leaflets, articles, reports, blogs, notices, guides, manuals", 3, f"{u3a}_t_formats")
    add(f"{u3a}_q", "Question types", 2, u3a)
    add(f"{u3a}_q_short", "Short responses (e.g. multiple choice, short constructed response, cloze, sequencing)", 3, f"{u3a}_q")
    add(f"{u3a}_q_long", "Extended responses (e.g. paraphrasing, comprehension in context, analysis/deduction/inference)", 3, f"{u3a}_q")

    add(f"{u3b}_tasks", "Writing tasks (both compulsory)", 2, u3b)
    add(f"{u3b}_tasks_arg", "Argumentation writing task", 3, f"{u3b}_tasks")
    add(f"{u3b}_tasks_pers", "Persuasion writing task", 3, f"{u3b}_tasks")
    add(f"{u3b}_forms", "Common real-life forms", 2, u3b)
    add(f"{u3b}_forms_let", "Letters / emails", 3, f"{u3b}_forms")
    add(f"{u3b}_forms_art", "Articles / reviews", 3, f"{u3b}_forms")
    add(f"{u3b}_forms_sp", "Speeches / campaign writing", 3, f"{u3b}_forms")
    add(f"{u3b}_mark", "Marking focus (50/50)", 2, u3b)
    add(f"{u3b}_mark_comm", "Communication & organisation (meaning, purpose, readers, structure)", 3, f"{u3b}_mark")
    add(f"{u3b}_mark_acc", "Accuracy (language, grammar, punctuation, spelling)", 3, f"{u3b}_mark")

    # General exam notes (as a small add-on under Unit 2)
    add(f"{u2}_notes", "General exam notes", 1, u2)
    add(f"{u2}_notes_untiered", "Untiered — full grade range available in external units", 2, f"{u2}_notes")
    add(f"{u2}_notes_dict", "Dictionaries are not permitted in the assessments", 2, f"{u2}_notes")

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

    to_insert = [
        {
            "subject_id": subject_id,
            "topic_code": n.code,
            "topic_name": n.title,
            "topic_level": n.level,
            "exam_board": SUBJECT["exam_board"],
        }
        for n in nodes
    ]
    inserted = supabase.table("staging_aqa_topics").insert(to_insert).execute()
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
    print("WJEC GCSE ENGLISH LANGUAGE (3700) - CURATED TOPICS SCRAPER")
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
    print("\n[OK] WJEC 3700 English Language topics upload complete.")


if __name__ == "__main__":
    main()






