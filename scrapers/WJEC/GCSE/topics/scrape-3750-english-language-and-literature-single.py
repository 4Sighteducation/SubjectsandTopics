"""
WJEC GCSE English Language and Literature (Single Award) (3750QS) - Curated Topics

Spec (Teaching from 2025 / award from 2027):
  https://www.wjec.co.uk/media/w2mlpil0/wjec-gcse-english-language-and-literature-single-and-double-award-specification-2.pdf

This spec covers BOTH Single + Double Award. We upload Single Award only here.

Rationale:
The PDF describes unit structure and assessment, and clearly lists Unit 4a set-text options.
Other required/prescribed materials are referenced (WJEC Anthology, prescribed stimuli/texts)
but are published/updated separately; we represent these as explicit placeholders so the app
structure is correct and can be filled later.
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
    "name": "English Language and Literature (Single Award)",
    "code": "WJEC-3750QS",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/w2mlpil0/wjec-gcse-english-language-and-literature-single-and-double-award-specification-2.pdf",
}


def _force_utf8_stdio() -> None:
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def build_nodes() -> list[Node]:
    nodes: list[Node] = []

    def add(code: str, title: str, level: int, parent: Optional[str]) -> None:
        nodes.append(Node(code=code, title=title, level=level, parent=parent))

    # Single Award units: 1,2,3,4a
    u1, u2, u3, u4a = "U1", "U2", "U3", "U4A"

    add(u1, "Unit 1 (Exam): Context and Meaning", 0, None)
    add(u2, "Unit 2 (NEA): Belonging", 0, None)
    add(u3, "Unit 3 (NEA): Influence and Power", 0, None)
    add(u4a, "Unit 4a (Exam, Single only): Motivations", 0, None)

    # Unit 1 structure
    add(f"{u1}_A", "Section A: Poetry (WJEC Anthology poem + unseen poem)", 1, u1)
    add(f"{u1}_A_req", "Required texts", 2, f"{u1}_A")
    add(f"{u1}_A_req_anthem", "WJEC Poetry Anthology — Unit 1 poems (by theme)", 3, f"{u1}_A_req")
    add(f"{u1}_A_req_anthem_rel", "Unit 1: Relationships", 4, f"{u1}_A_req_anthem")
    add(f"{u1}_A_req_anthem_rel_1", "Valentine — Carol Ann Duffy", 5, f"{u1}_A_req_anthem_rel")
    add(f"{u1}_A_req_anthem_rel_2", "Modern Love — Douglas Dunn", 5, f"{u1}_A_req_anthem_rel")
    add(f"{u1}_A_req_anthem_id", "Unit 1: Identity", 4, f"{u1}_A_req_anthem")
    add(f"{u1}_A_req_anthem_id_1", "I Come From — Dean Atta", 5, f"{u1}_A_req_anthem_id")
    add(f"{u1}_A_req_anthem_id_2", "Miz Rosa Rides the Bus — Angela Jackson", 5, f"{u1}_A_req_anthem_id")
    add(f"{u1}_A_req_anthem_conf", "Unit 1: Conflict", 4, f"{u1}_A_req_anthem")
    add(f"{u1}_A_req_anthem_conf_1", "The End and the Beginning — Wislawa Szymborska", 5, f"{u1}_A_req_anthem_conf")
    add(f"{u1}_A_req_anthem_conf_2", "A Century Later — Imtiaz Dharker", 5, f"{u1}_A_req_anthem_conf")
    add(f"{u1}_A_req_anthem_nat", "Unit 1: The Natural World", 4, f"{u1}_A_req_anthem")
    add(f"{u1}_A_req_anthem_nat_1", "Ark — Simon Armitage", 5, f"{u1}_A_req_anthem_nat")
    add(f"{u1}_A_req_anthem_nat_2", "Like an Heiress — Grace Nichols", 5, f"{u1}_A_req_anthem_nat")
    add(f"{u1}_A_req_anthem_cp", "Unit 1: Children and Parents", 4, f"{u1}_A_req_anthem")
    add(f"{u1}_A_req_anthem_cp_1", "Catrin — Gillian Clarke", 5, f"{u1}_A_req_anthem_cp")
    add(f"{u1}_A_req_anthem_cp_2", "Coming Home — Owen Sheers", 5, f"{u1}_A_req_anthem_cp")
    add(f"{u1}_A_req_unseen", "Unseen poem", 3, f"{u1}_A_req")
    add(f"{u1}_A_tasks", "Exam tasks", 2, f"{u1}_A")
    add(f"{u1}_A_tasks_obj", "Objective / short / restricted responses", 3, f"{u1}_A_tasks")
    add(f"{u1}_A_tasks_essay", "Analytical comparative essay (anthology poem vs unseen poem)", 3, f"{u1}_A_tasks")

    add(f"{u1}_B", "Section B: Writing", 1, u1)
    add(f"{u1}_B_task", "Extended response (1 from a choice of 2)", 2, f"{u1}_B")
    add(f"{u1}_B_types", "Writing types", 2, f"{u1}_B")
    add(f"{u1}_B_types_creative", "Creative literary writing", 3, f"{u1}_B_types")
    add(f"{u1}_B_types_nonfic", "Non-fiction writing", 3, f"{u1}_B_types")

    # Unit 2 structure (NEA)
    add(f"{u2}_A", "Task A: Written essay on a prose text (from WJEC longlist)", 1, u2)
    add(f"{u2}_A_req", "Required text", 2, f"{u2}_A")
    add(f"{u2}_A_req_prose", "One prose text selected from WJEC suggested longlist (not enumerated here)", 3, f"{u2}_A_req")
    add(f"{u2}_A_focus", "Focus", 2, f"{u2}_A")
    add(f"{u2}_A_focus_theme", "Belonging explored through character(s) and setting", 3, f"{u2}_A_focus")

    add(f"{u2}_B", "Task B: Individually researched oral presentation", 1, u2)
    add(f"{u2}_B_focus", "Focus", 2, f"{u2}_B")
    add(f"{u2}_B_focus_link", "Linked to the studied prose text (theme/issue/representation/relationship)", 3, f"{u2}_B_focus")

    # Unit 3 structure (NEA)
    add(f"{u3}_A", "Task A: Group discussion (6–10 minutes) on non-fiction anthology theme", 1, u3)
    add(f"{u3}_A_req", "Required texts", 2, f"{u3}_A")
    add(f"{u3}_A_req_anth", "WJEC non-fiction anthology (Unit 3 & Unit 6) — theme shells", 3, f"{u3}_A_req")
    add(f"{u3}_A_req_anth_div", "Diversity", 4, f"{u3}_A_req_anth")
    add(f"{u3}_A_req_anth_hr", "Human Rights", 4, f"{u3}_A_req_anth")
    add(f"{u3}_A_req_anth_rel", "Relationships", 4, f"{u3}_A_req_anth")
    add(f"{u3}_A_req_anth_wales", "Wales and Global Contexts", 4, f"{u3}_A_req_anth")
    add(f"{u3}_A_req_anth_work", "Work and sustainability", 4, f"{u3}_A_req_anth")
    add(f"{u3}_A_req_pres", "One WJEC prescribed text (per theme) — published separately", 3, f"{u3}_A_req")
    add(f"{u3}_A_stim", "Stimuli/themes", 2, f"{u3}_A")
    add(f"{u3}_A_stim_note", "Two theme options published by WJEC (stimuli + prescribed text per theme)", 3, f"{u3}_A_stim")

    add(f"{u3}_B", "Task B: Creative non-fiction writing", 1, u3)
    add(f"{u3}_B_focus", "Informed by reading/discussion from Task A", 2, f"{u3}_B")

    # Unit 4a set text choices (Single)
    add(f"{u4a}_set", "Set text options (choose one)", 1, u4a)
    add(f"{u4a}_set_AIC", "An Inspector Calls — 3750UA", 2, f"{u4a}_set")
    add(f"{u4a}_set_EARN", "The Importance of Being Earnest — 3750UB", 2, f"{u4a}_set")
    add(f"{u4a}_set_RB", "Refugee Boy: playscript — 3750UC", 2, f"{u4a}_set")
    add(f"{u4a}_set_PYG", "Pygmalion — 3750UD", 2, f"{u4a}_set")
    add(f"{u4a}_set_MND", "A Midsummer Night’s Dream — 3750UE", 2, f"{u4a}_set")

    add(f"{u4a}_A", "Section A: Responses + analytical essay on the set text", 1, u4a)
    add(f"{u4a}_B", "Section B: Creative literary writing (1 from a choice of 2)", 1, u4a)

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
    print("WJEC GCSE ENGLISH LANGUAGE & LITERATURE (3750QS) - SINGLE AWARD (CURATED)")
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
    print("\n[OK] WJEC 3750QS Single Award topics upload complete.")


if __name__ == "__main__":
    main()


