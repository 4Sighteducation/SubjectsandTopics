"""
WJEC GCE AS/A Level Welsh Second Language (2016 spec) - Topics Scraper

Spec:
  https://www.wjec.co.uk/media/4ohbsvel/wjec-gce-welsh-second-language-spec-from-2016-e-1.pdf

Entry-code mapping in spec:
  - AS cash-in: 2020QS
  - A level cash-in: 1020QS

We model the full A level content under: WJEC-1020QS.

This is assessment-driven; we publish a clean curriculum shell:
  - L0: Units 1-4 (core assessed units)
  - L1: Key components as listed in the spec
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
    "code": "WJEC-1020QS",
    "qualification": "A-Level",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/4ohbsvel/wjec-gce-welsh-second-language-spec-from-2016-e-1.pdf",
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
    units = {
        1: "AS Unit 1: Film and Oracy",
        2: "AS Unit 2: Non-examination Assessment",
        3: "AS Unit 3: The use of Language and Poetry",
        4: "A2 Unit 4: Drama and Oracy",
    }

    nodes: list[Node] = []
    for u in range(1, 5):
        ucode = f"U{u}"
        nodes.append(Node(code=ucode, title=units[u], level=0, parent=None))

    nodes.extend(
        [
            Node(code="U1_A", title="Section A: Film", level=1, parent="U1"),
            Node(code="U1_B", title="Section B: Oracy", level=1, parent="U1"),
            Node(code="U2_overview", title="Coursework: portfolio tasks (set by WJEC)", level=1, parent="U2"),
            Node(code="U3_A", title="Section A: Language", level=1, parent="U3"),
            Node(code="U3_B", title="Section B: Poetry", level=1, parent="U3"),
            Node(code="U4_A", title="Section A: Drama", level=1, parent="U4"),
            Node(code="U4_B", title="Section B: Oracy", level=1, parent="U4"),
        ]
    )

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC A-LEVEL WELSH SECOND LANGUAGE (1020QS) - TOPICS SCRAPER")
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
    print("[OK] Welsh Second Language scrape complete.")


if __name__ == "__main__":
    main()






