"""
WJEC GCSE English Language and Literature (Double Award) (3750QD) - Curated Topics

Spec (Teaching from 2025 / award from 2027):
  https://www.wjec.co.uk/media/w2mlpil0/wjec-gcse-english-language-and-literature-single-and-double-award-specification-2.pdf

This spec covers BOTH Single + Double Award. We upload Double Award only here.

Double Award units: 1,2,3,4b,5,6
Key 'hard lists' we can accurately include from the PDF:
  - Unit 4b set-text options (with entry codes)
Other prescribed materials are referenced but not enumerated here (anthology lists, WJEC-set
stimuli/texts/poems) and are represented as placeholders.
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
    "name": "English Language and Literature (Double Award)",
    "code": "WJEC-3750QD",
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

    u1, u2, u3, u4b, u5, u6 = "U1", "U2", "U3", "U4B", "U5", "U6"

    add(u1, "Unit 1 (Exam): Context and Meaning", 0, None)
    add(u2, "Unit 2 (NEA): Belonging", 0, None)
    add(u3, "Unit 3 (NEA): Influence and Power", 0, None)
    add(u4b, "Unit 4b (Exam, Double only): Motivations", 0, None)
    add(u5, "Unit 5 (NEA, Double only): Continuity and Change", 0, None)
    add(u6, "Unit 6 (Exam, Double only): Connections", 0, None)

    # Unit 1 (same structure as common unit)
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
    add(f"{u1}_B", "Section B: Writing (creative literary OR non-fiction; 1 from a choice of 2)", 1, u1)

    # Unit 2 (NEA)
    add(f"{u2}_A", "Task A: Written essay on a prose text (from WJEC longlist)", 1, u2)
    add(f"{u2}_A_req", "Required text", 2, f"{u2}_A")
    add(f"{u2}_A_req_prose", "One prose text selected from WJEC suggested longlist (not enumerated here)", 3, f"{u2}_A_req")
    add(f"{u2}_B", "Task B: Individually researched oral presentation (linked to the prose text)", 1, u2)

    # Unit 3 (NEA)
    add(f"{u3}_A", "Task A: Group discussion (6–10 minutes) on non-fiction anthology theme", 1, u3)
    add(f"{u3}_A_req", "Required texts", 2, f"{u3}_A")
    add(f"{u3}_A_req_anth", "WJEC non-fiction anthology (Unit 3 & Unit 6) — theme shells", 3, f"{u3}_A_req")
    add(f"{u3}_A_req_anth_div", "Diversity", 4, f"{u3}_A_req_anth")
    add(f"{u3}_A_req_anth_hr", "Human Rights", 4, f"{u3}_A_req_anth")
    add(f"{u3}_A_req_anth_rel", "Relationships", 4, f"{u3}_A_req_anth")
    add(f"{u3}_A_req_anth_wales", "Wales and Global Contexts", 4, f"{u3}_A_req_anth")
    add(f"{u3}_A_req_anth_work", "Work and sustainability", 4, f"{u3}_A_req_anth")
    add(f"{u3}_A_req_pres", "One WJEC prescribed text (per theme) — published separately", 3, f"{u3}_A_req")
    add(f"{u3}_B", "Task B: Creative non-fiction writing (informed by Task A)", 1, u3)

    # Unit 4b set text choices (Double)
    add(f"{u4b}_set", "Set text options (choose one)", 1, u4b)
    add(f"{u4b}_set_AIC", "An Inspector Calls — 3750UF", 2, f"{u4b}_set")
    add(f"{u4b}_set_AF", "Animal Farm — 3750UG", 2, f"{u4b}_set")
    add(f"{u4b}_set_PIG", "Pigeon — 3750UH", 2, f"{u4b}_set")
    add(f"{u4b}_set_MNIL", "My Name Is Leon — 3750UJ", 2, f"{u4b}_set")
    add(f"{u4b}_set_LT", "Leave Taking — 3750UK", 2, f"{u4b}_set")
    add(f"{u4b}_set_DNA", "DNA — 3750UL", 2, f"{u4b}_set")
    add(f"{u4b}_A", "Section A: Responses + analytical essay on the set text", 1, u4b)
    add(f"{u4b}_B", "Section B: Creative literary writing (1 from a choice of 2)", 1, u4b)

    # Unit 5 (NEA, Double only)
    add(f"{u5}_A", "Task A: Extended response on a whole Shakespeare play", 1, u5)
    add(f"{u5}_A_req", "Required text", 2, f"{u5}_A")
    add(f"{u5}_A_req_sh", "One whole Shakespeare play (centre-selected) — not enumerated here", 3, f"{u5}_A_req")
    add(f"{u5}_B", "Task B: Paired discussion on poetry", 1, u5)
    add(f"{u5}_B_req", "Required poems", 2, f"{u5}_B")
    add(f"{u5}_B_req_pres", "WJEC Poetry Anthology — Unit 5 prescribed poems (by theme)", 3, f"{u5}_B_req")
    add(f"{u5}_B_req_pres_rel", "Unit 5: Relationships", 4, f"{u5}_B_req_pres")
    add(f"{u5}_B_req_pres_rel_1", "La Belle Dame sans Merci — John Keats", 5, f"{u5}_B_req_pres_rel")
    add(f"{u5}_B_req_pres_id", "Unit 5: Identity", 4, f"{u5}_B_req_pres")
    add(f"{u5}_B_req_pres_id_1", "I Am! — John Clare", 5, f"{u5}_B_req_pres_id")
    add(f"{u5}_B_req_pres_conf", "Unit 5: Conflict", 4, f"{u5}_B_req_pres")
    add(f"{u5}_B_req_pres_conf_1", "The Charge of the Light Brigade — Alfred, Lord Tennyson", 5, f"{u5}_B_req_pres_conf")
    add(f"{u5}_B_req_pres_nat", "Unit 5: The Natural World", 4, f"{u5}_B_req_pres")
    add(f"{u5}_B_req_pres_nat_1", "God's Grandeur — Gerard Manley Hopkins", 5, f"{u5}_B_req_pres_nat")
    add(f"{u5}_B_req_pres_cp", "Unit 5: Children and Parents", 4, f"{u5}_B_req_pres")
    add(f"{u5}_B_req_pres_cp_1", "On my First Son — Ben Jonson", 5, f"{u5}_B_req_pres_cp")
    add(f"{u5}_B_req_choice", "One further poem chosen by learner (anthology or self-selected)", 3, f"{u5}_B_req")

    # Unit 6 (Exam, Double only)
    add(f"{u6}_A", "Section A: Mixed short + longer analytical/comparative/evaluative responses", 1, u6)
    add(f"{u6}_A_req", "Required texts", 2, f"{u6}_A")
    add(f"{u6}_A_req_anth", "WJEC non-fiction anthology (Unit 3 & Unit 6) — theme shells", 3, f"{u6}_A_req")
    add(f"{u6}_A_req_anth_div", "Diversity", 4, f"{u6}_A_req_anth")
    add(f"{u6}_A_req_anth_hr", "Human Rights", 4, f"{u6}_A_req_anth")
    add(f"{u6}_A_req_anth_rel", "Relationships", 4, f"{u6}_A_req_anth")
    add(f"{u6}_A_req_anth_wales", "Wales and Global Contexts", 4, f"{u6}_A_req_anth")
    add(f"{u6}_A_req_anth_work", "Work and sustainability", 4, f"{u6}_A_req_anth")
    add(f"{u6}_B", "Section B: Writing / producing a linked response (per exam paper)", 1, u6)

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
    print("WJEC GCSE ENGLISH LANGUAGE & LITERATURE (3750QD) - DOUBLE AWARD (CURATED)")
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
    print("\n[OK] WJEC 3750QD Double Award topics upload complete.")


if __name__ == "__main__":
    main()


