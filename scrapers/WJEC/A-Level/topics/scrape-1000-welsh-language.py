"""
WJEC GCE AS/A Level Welsh First Language (2015 spec) - Topics Scraper

Spec:
  https://www.wjec.co.uk/media/jbhnh54j/wjec-gce-welsh-first-language-spec-from-2015-e-09-2022.pdf

Entry-code mapping in spec (Welsh-medium codes shown as N*):
  - AS Units 1-3: 2000N1/2000N2/2000N3, AS cash-in: 2000CS (English-medium may vary)
  - A2 Units 4-6: 1000N4/1000N5/1000N6, A level cash-in: 1000CS

We model the full A level content under: WJEC-1000CS.

This is primarily an assessment-driven subject; we publish a clean curriculum shell:
  - L0: Units 1-4 (core assessed units). Units 5-6 are admin/variation heavy; add as shells.
  - L1: Key components (texts/tasks) as listed in the spec

This is intentionally conservative to avoid scraping huge assessment admin prose.
"""

from __future__ import annotations

import io
import os
import re
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
    "code": "WJEC-1000CS",
    "qualification": "A-Level",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/jbhnh54j/wjec-gce-welsh-first-language-spec-from-2015-e-09-2022.pdf",
}


def _force_utf8_stdio() -> None:
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def upload_to_staging(*, subject: dict, nodes: list[Node]) -> None:
    env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
    load_dotenv(env_path)
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    subject_result = supabase.table("staging_aqa_subjects").upsert(
        {
            "subject_name": f"{subject['name']} (A-Level)",
            "subject_code": subject["code"],
            "qualification_type": "A-Level",
            "specification_url": subject["pdf_url"],
            "exam_board": subject["exam_board"],
        },
        on_conflict="subject_code,qualification_type,exam_board",
    ).execute()
    subject_id = subject_result.data[0]["id"]
    print(f"[OK] Subject ID: {subject_id}")

    existing_max = 0
    try:
        res = (
            supabase.table("staging_aqa_topics")
            .select("topic_level")
            .eq("subject_id", subject_id)
            .order("topic_level", desc=True)
            .limit(1)
            .execute()
        )
        if res.data:
            existing_max = int(res.data[0]["topic_level"] or 0)
    except Exception:
        existing_max = 0

    max_level = max(existing_max, max((n.level for n in nodes), default=0))
    deleted_total = 0
    BATCH = 500
    for lvl in range(max_level, -1, -1):
        while True:
            rows = (
                supabase.table("staging_aqa_topics")
                .select("id")
                .eq("subject_id", subject_id)
                .eq("topic_level", lvl)
                .limit(BATCH)
                .execute()
                .data
                or []
            )
            if not rows:
                break
            ids = [r["id"] for r in rows]
            res = supabase.table("staging_aqa_topics").delete().in_("id", ids).execute()
            deleted_total += len(res.data or [])
    print(f"[OK] Cleared old topics ({deleted_total} rows)")

    payload = [
        {
            "subject_id": subject_id,
            "topic_code": n.code,
            "topic_name": n.title,
            "topic_level": n.level,
            "exam_board": subject["exam_board"],
        }
        for n in nodes
    ]
    inserted_rows: list[dict] = []
    for i in range(0, len(payload), 500):
        res = supabase.table("staging_aqa_topics").insert(payload[i : i + 500]).execute()
        inserted_rows.extend(res.data or [])
    print(f"[OK] Uploaded {len(inserted_rows)} topics")

    code_to_id = {row["topic_code"]: row["id"] for row in inserted_rows}
    linked = 0
    for n in nodes:
        if not n.parent:
            continue
        child_id = code_to_id.get(n.code)
        parent_id = code_to_id.get(n.parent)
        if child_id and parent_id:
            supabase.table("staging_aqa_topics").update({"parent_topic_id": parent_id}).eq("id", child_id).execute()
            linked += 1
    print(f"[OK] Linked {linked} relationships")


def build_nodes() -> list[Node]:
    # Titles from the spec summary (extracted reliably earlier)
    units = {
        1: "AS Unit 1: The Film, the Play and Oracy",
        2: "AS Unit 2: Non-examination Assessment",
        3: "AS Unit 3: The Use of Language, and Poetry",
        4: "A2 Unit 4: The Novel and Oracy",
        5: "A2 Unit 5: Non-examination Assessment",
        6: "A2 Unit 6: The Use of Language, and Prose",
    }

    nodes: list[Node] = []
    for u in range(1, 7):
        ucode = f"U{u}"
        nodes.append(Node(code=ucode, title=units[u], level=0, parent=None))

    # Minimal curated structure per unit (enough for navigation + flashcard generation)
    nodes.extend(
        [
            Node(code="U1_A", title="Section A: Film", level=1, parent="U1"),
            Node(code="U1_B", title="Section B: Play", level=1, parent="U1"),
            Node(code="U1_C", title="Section C: Oracy", level=1, parent="U1"),
            Node(code="U2_overview", title="Coursework: two written pieces (set by WJEC)", level=1, parent="U2"),
            Node(code="U3_A", title="Section A: Language", level=1, parent="U3"),
            Node(code="U3_B", title="Section B: Poetry", level=1, parent="U3"),
            Node(code="U3_C", title="Section C: Oracy", level=1, parent="U3"),
            Node(code="U4_A", title="Section A: Novel", level=1, parent="U4"),
            Node(code="U4_B", title="Section B: Oracy", level=1, parent="U4"),
            Node(code="U5_overview", title="Coursework: extended study + evaluation tasks", level=1, parent="U5"),
            Node(code="U6_overview", title="Advanced language and prose study (assessment-led)", level=1, parent="U6"),
        ]
    )

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC A-LEVEL WELSH LANGUAGE (1000CS) - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}")

    nodes = build_nodes()
    by_level: dict[int, int] = {}
    for n in nodes:
        by_level[n.level] = by_level.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(by_level):
        print(f"  - L{lvl}: {by_level[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("[OK] Welsh Language scrape complete.")


if __name__ == "__main__":
    main()






