"""
WJEC GCSE Welsh Literature (3010) - Topics Scraper (curated set texts + tasks)

Spec:
  https://www.wjec.co.uk/media/nawo2ern/wjec-gcse-welsh-literature-spec-from-2015-e-10-05-2023.pdf

We model this as a clean revision/teaching hierarchy:
  - L0: Unit 1 Poetry (exam)
  - L0: Unit 2 Novel (exam)
  - L0: Unit 3 Visual Literature (oral exam)
  - L0: Unit 4 Written Tasks (NEA)

Include set poems / set novels / set visual literature texts exactly as listed in the spec.
Unit 4 themes for short stories are WJEC-set and change; we keep them as shells.
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
    "name": "Welsh Literature",
    "code": "WJEC-3010",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/nawo2ern/wjec-gcse-welsh-literature-spec-from-2015-e-10-05-2023.pdf",
}


def _force_utf8_stdio() -> None:
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


SET_POEMS_FOUNDATION = [
    ("Rhaid peidio dawnsio...", "Emyr Lewis"),
    ("Y Ferch wrth y Bar yng Nghlwb Ifor", "Rhys Iorwerth"),
    ("Gweld y Gorwel", "Aneirin Karadog"),
    ("Y Sbectol Hud", "Mererid Hopwood"),
    ("Tai Unnos", "Iwan Llwyd"),
    ("Walker's Wood", "Myrddin ap Dafydd"),
]

SET_POEMS_HIGHER_ONLY = [
    ("Ofn", "Hywel Griffiths"),
    ("Eifionydd", "R. Williams Parry"),
    ("Y Coed", "Gwenallt"),
    ("Etifeddiaeth", "Gerallt Lloyd Owen"),
]

SET_NOVELS_FOUNDATION = [
    ("Llinyn Trôns", "Bethan Gwanas"),
    ("Bachgen yn y Môr", "Morris Gleitzman (adaptation by Elin Meek)"),
    ("Diffodd y Sêr", "Haf Llewelyn"),
]

SET_NOVELS_HIGHER = [
    ("Dim", "Dafydd Chilton"),
    ("Yn y Gwaed", "Geraint Vaughan Jones"),
    ("O Ran", "Mererid Hopwood"),
]

SET_NOVELS_ALL_ABILITIES = [
    ("Ac Yna Clywodd Sŵn y Môr", "Alun Jones"),
    ("I Ble’r Aeth Haul y Bore?", "Eirug Wyn"),
    ("Llyfr Glas Nebo", "Manon Steffan Ros"),
]

VISUAL_LITERATURE_SET_TEXTS_2024 = [
    ("Y Gwyll (film MMXV) — S4C", "Short story: ‘Tân’ (Darnau Dylan Iorwerth)"),
    ("Y Weithred — S4C", "Short story: ‘Epynt’ (Tudur Dylan Jones)"),
]


def build_nodes() -> list[Node]:
    nodes: list[Node] = []

    def add(code: str, title: str, level: int, parent: Optional[str]) -> None:
        nodes.append(Node(code=code, title=title, level=level, parent=parent))

    # Unit 1: Poetry
    add("U1", "Unit 1: Poetry (Exam)", 0, None)
    add("U1_SET", "Set poems (from Fesul Gair anthology)", 1, "U1")
    add("U1_SET_F", "Foundation Tier", 2, "U1_SET")
    for i, (t, a) in enumerate(SET_POEMS_FOUNDATION, start=1):
        add(f"U1_SET_F_{i:02d}", f"{t} — {a}", 3, "U1_SET_F")
    add("U1_SET_H_EXTRA", "Higher Tier: additional set poems", 2, "U1_SET")
    for i, (t, a) in enumerate(SET_POEMS_HIGHER_ONLY, start=1):
        add(f"U1_SET_H_EXTRA_{i:02d}", f"{t} — {a}", 3, "U1_SET_H_EXTRA")
    add("U1_EXAM", "Exam focus", 1, "U1")
    add("U1_EXAM_1", "Compare one set poem with an unseen poem", 2, "U1_EXAM")
    add("U1_EXAM_2", "Respond to content/message/theme; style/metre; personal response", 2, "U1_EXAM")

    # Unit 2: Novel
    add("U2", "Unit 2: Novel (Exam)", 0, None)
    add("U2_SET", "Set novels (for assessment from 2021)", 1, "U2")
    add("U2_SET_F", "Foundation Tier options", 2, "U2_SET")
    for i, (t, a) in enumerate(SET_NOVELS_FOUNDATION, start=1):
        add(f"U2_SET_F_{i:02d}", f"{t} — {a}", 3, "U2_SET_F")
    add("U2_SET_H", "Higher Tier options", 2, "U2_SET")
    for i, (t, a) in enumerate(SET_NOVELS_HIGHER, start=1):
        add(f"U2_SET_H_{i:02d}", f"{t} — {a}", 3, "U2_SET_H")
    add("U2_SET_ALL", "Suitable to the entire range of abilities", 2, "U2_SET")
    for i, (t, a) in enumerate(SET_NOVELS_ALL_ABILITIES, start=1):
        add(f"U2_SET_ALL_{i:02d}", f"{t} — {a}", 3, "U2_SET_ALL")
    add("U2_EXAM", "Exam focus", 1, "U2")
    add("U2_EXAM_1", "Respond to content/themes/plot/character; author’s style; personal/creative response", 2, "U2_EXAM")

    # Unit 3: Visual literature (oral)
    add("U3", "Unit 3: Visual Literature (Oral examination)", 0, None)
    add("U3_SET", "Set texts (for assessment from 2024)", 1, "U3")
    for i, (film, story) in enumerate(VISUAL_LITERATURE_SET_TEXTS_2024, start=1):
        add(f"U3_SET_{i:02d}", film, 2, "U3_SET")
        add(f"U3_SET_{i:02d}_S", story, 3, f"U3_SET_{i:02d}")
    add("U3_FOCUS", "Discussion focus (examples)", 1, "U3")
    add("U3_FOCUS_1", "Plot/structure; characters; themes; background; style/technique; compare film to printed text", 2, "U3_FOCUS")

    # Unit 4: NEA written tasks
    add("U4", "Unit 4: Written Tasks (Non-examination assessment)", 0, None)
    add("U4_T1", "Task 1: Short Stories (theme set by WJEC; changes every two years)", 1, "U4")
    add("U4_T1_1", "Study 2 short stories on a specific theme from 20 Stori Fer Cyfrol 1/2 (ed. Emyr Llywelyn)", 2, "U4_T1")
    add("U4_T2", "Task 2: Drama/Film (written task)", 1, "U4")
    add("U4_T2_1", "Written response to a set drama/film task (details vary by WJEC materials)", 2, "U4_T2")

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
    print("WJEC GCSE WELSH LITERATURE (3010) - TOPICS UPLOAD (CURATED)")
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
    print("\n[OK] WJEC 3010 Welsh Literature topics upload complete.")


if __name__ == "__main__":
    main()






