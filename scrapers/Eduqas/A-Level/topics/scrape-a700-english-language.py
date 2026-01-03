"""
Eduqas A Level English Language (spec from 2015) - Topics Scraper (curated, max depth L2)

Spec:
  https://www.eduqas.co.uk/media/fxefxsd5/wjec-eduqas-a-level-english-language-specification-from-2015.pdf

Entry code in spec: A700QS

Rationale:
- This is not a "knowledge list" spec; the most useful curriculum structure for flashcards is
  a curated hierarchy capturing:
  - component names
  - what learners do in each section
  - the major focus areas / study themes for the NEA

Hierarchy (L0-L2):
  - L0: Component (title)
  - L1: Section / focus
  - L2: Key requirements / tasks / content focus
"""

from __future__ import annotations

import io
import os
import re
import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from pypdf import PdfReader
from supabase import create_client


@dataclass(frozen=True)
class Node:
    code: str
    title: str
    level: int
    parent: Optional[str]


SUBJECT = {
    "name": "English Language",
    "qualification": "A-Level",
    "pdf_url": "https://www.eduqas.co.uk/media/fxefxsd5/wjec-eduqas-a-level-english-language-specification-from-2015.pdf",
}

SUBJECTS = [
    {**SUBJECT, "code": "EDUQAS-A700QS", "exam_board": "EDUQAS"},
    {**SUBJECT, "code": "WJEC-A700QS", "exam_board": "WJEC"},
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

    comps = [
        ("C1", "Component 1: Language Concepts and Issues", [
            ("S_A", "Section A: Analysis of Spoken Language", [
                "Analyse spoken language using linguistic concepts and methods",
                "Consider contextual factors and how meaning is created for audiences",
            ]),
            ("S_B", "Section B: Language Issues", [
                "Choose one question from a set of language issues questions",
                "Evaluate viewpoints and evidence; construct a reasoned argument",
            ]),
            ("GEN", "Exam essentials", [
                "Written examination: 2 hours",
                "Compulsory question in Section A; choice in Section B",
            ]),
        ]),
        ("C2", "Component 2: Language Change Over Time", [
            ("HIST", "Historical change", [
                "How English changes across time; causes of change",
                "Use evidence from texts / data to support analysis",
            ]),
            ("CHANGE", "Mechanisms and patterns of change", [
                "Lexis, grammar, semantics and discourse across periods",
                "Language attitudes and standardisation",
            ]),
            ("GEN", "Exam essentials", [
                "Written examination (per spec)",
                "Focus on analysing and evaluating language change",
            ]),
        ]),
        ("C3", "Component 3: Creative and Critical Use of Language", [
            ("READ", "Critical reading / analysis", [
                "Analyse and evaluate how texts achieve purposes for audiences",
                "Apply linguistic concepts to written texts",
            ]),
            ("WRITE", "Creative writing + commentary", [
                "Produce original writing for a specified purpose/audience",
                "Write an analytical commentary on language choices made",
            ]),
            ("GEN", "Exam essentials", [
                "Written examination (per spec)",
                "Assesses creative control and analytical explanation",
            ]),
        ]),
        ("C4", "Component 4: Language and Identity (NEA)", [
            ("INV", "Language investigation", [
                "Independent language investigation: data collection, methods, interpretation",
                "Folder length (per spec): 2500–3500 words",
            ]),
            ("AREAS", "Investigation areas (choose one area)", [
                "Language and gender",
                "Language and power",
                "Language and technology",
                "Language and occupation",
            ]),
            ("GEN", "NEA essentials", [
                "Non-exam assessment; submit a research-based investigation",
                "Develop a hypothesis/theory linked to language and identity",
            ]),
        ]),
    ]

    for comp_code, comp_title, sections in comps:
        nodes.append(Node(code=comp_code, title=comp_title, level=0, parent=None))
        for sec_code, sec_title, bullets in sections:
            l1 = f"{comp_code}_{sec_code}"
            nodes.append(Node(code=l1, title=sec_title, level=1, parent=comp_code))
            for i, b in enumerate(bullets, 1):
                nodes.append(Node(code=f"{l1}_{i:02d}", title=b, level=2, parent=l1))

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("EDUQAS A LEVEL ENGLISH LANGUAGE - TOPICS SCRAPER (L0-L2)")
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
    print("[OK] English Language (A-Level) scrape complete (uploaded to EDUQAS + WJEC).")


if __name__ == "__main__":
    main()


