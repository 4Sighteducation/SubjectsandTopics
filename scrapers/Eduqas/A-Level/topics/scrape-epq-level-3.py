"""
WJEC/Eduqas Level 3 Extended Project Qualification (EPQ) - Topics Scraper (basic, max depth L2)

Spec (found via Eduqas PDF URL scraper):
  https://www.eduqas.co.uk/media/mqjlqngj/wjec-level-3-extended-project-spec-e-26-04-23-1.pdf

Notes:
- This is an assessment/skills-based qualification; scraping at deep granularity creates noise.
- We therefore upload a concise L0-L2 structure: overview, process, assessment objectives, and outputs.
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
    "name": "Extended Project",
    "qualification": "Level 3 Extended Project",
    "pdf_url": "https://www.eduqas.co.uk/media/mqjlqngj/wjec-level-3-extended-project-spec-e-26-04-23-1.pdf",
}

SUBJECTS = [
    {**SUBJECT, "code": "EDUQAS-EPQ-L3", "exam_board": "EDUQAS"},
    {**SUBJECT, "code": "WJEC-EPQ-L3", "exam_board": "WJEC"},
]


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
            "subject_name": f"{subject['name']} ({subject['qualification']})",
            "subject_code": subject["code"],
            "qualification_type": subject["qualification"],
            "specification_url": subject["pdf_url"],
            "exam_board": subject["exam_board"],
        },
        on_conflict="subject_code,qualification_type,exam_board",
    ).execute()
    subject_id = subject_result.data[0]["id"]
    print(f"[OK] Subject ID: {subject_id}")

    deleted_total = 0
    BATCH = 200
    for lvl in range(7, -1, -1):
        while True:
            rows = (
                supabase.table("staging_aqa_topics")
                .select("id")
                .eq("subject_id", subject_id)
                .eq("exam_board", subject["exam_board"])
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

    inserted = (
        supabase.table("staging_aqa_topics")
        .insert(
            [
                {
                    "subject_id": subject_id,
                    "topic_code": n.code,
                    "topic_name": n.title,
                    "topic_level": n.level,
                    "exam_board": subject["exam_board"],
                }
                for n in nodes
            ]
        )
        .execute()
    )
    print(f"[OK] Uploaded {len(inserted.data)} topics")

    code_to_id = {row["topic_code"]: row["id"] for row in inserted.data}
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
    nodes: list[Node] = []

    # L0: Overview
    o = "OV"
    nodes.append(Node(code=o, title="Overview", level=0, parent=None))
    nodes.append(Node(code=f"{o}_01", title="What the Extended Project is", level=1, parent=o))
    for i, p in enumerate(
        [
            "Standalone Level 3 qualification taken alongside other studies",
            "Develops independent research and project management skills",
            "Centres supervise; learners plan, research, produce and review an outcome",
        ],
        1,
    ):
        nodes.append(Node(code=f"{o}_01_{i:02d}", title=p, level=2, parent=f"{o}_01"))

    nodes.append(Node(code=f"{o}_02", title="Project outputs (types)", level=1, parent=o))
    for i, p in enumerate(
        [
            "Dissertation / extended written report",
            "Artefact / product with accompanying report",
            "Performance / event with accompanying report",
        ],
        1,
    ):
        nodes.append(Node(code=f"{o}_02_{i:02d}", title=p, level=2, parent=f"{o}_02"))

    # L0: Process
    pr = "PROC"
    nodes.append(Node(code=pr, title="Project process", level=0, parent=None))
    steps = [
        "Choose an area and define a focused title / question",
        "Plan the project (aims, methods, timeline, resources)",
        "Research and develop the project (sources, data, analysis)",
        "Produce the final outcome",
        "Review the process and the outcome (evaluation and reflection)",
        "Present to a non-specialist audience (communication skills)",
    ]
    nodes.append(Node(code=f"{pr}_01", title="Stages", level=1, parent=pr))
    for i, s in enumerate(steps, 1):
        nodes.append(Node(code=f"{pr}_01_{i:02d}", title=s, level=2, parent=f"{pr}_01"))

    # L0: Assessment objectives
    ao = "AO"
    nodes.append(Node(code=ao, title="Assessment objectives (AO)", level=0, parent=None))
    aos = [
        ("AO1", "Manage: identify, design, plan and carry out the project"),
        ("AO2", "Use resources: research, select and use information effectively"),
        ("AO3", "Develop and realise: apply skills/knowledge to produce the outcome"),
        ("AO4", "Review: evaluate process and outcome; communicate effectively"),
    ]
    for code, title in aos:
        nodes.append(Node(code=f"{ao}_{code}", title=f"{code}: {title}", level=1, parent=ao))
        nodes.append(Node(code=f"{ao}_{code}_01", title="Evidence typically includes planning, research log, product/report, and evaluation", level=2, parent=f"{ao}_{code}"))

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("EDUQAS LEVEL 3 EXTENDED PROJECT (EPQ) - TOPICS SCRAPER (L0-L2)")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}")

    nodes = build_nodes()
    by_level: dict[int, int] = {}
    for n in nodes:
        by_level[n.level] = by_level.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(by_level):
        print(f"  - L{lvl}: {by_level[lvl]}")

    for subj in SUBJECTS:
        print(f"\n[INFO] Uploading for exam_board={subj['exam_board']} code={subj['code']} ...")
        upload_to_staging(subject=subj, nodes=nodes)
    print("[OK] EPQ scrape complete (uploaded to EDUQAS + WJEC).")


if __name__ == "__main__":
    main()


