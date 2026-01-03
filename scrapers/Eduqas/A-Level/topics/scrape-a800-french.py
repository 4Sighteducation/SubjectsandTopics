"""
Eduqas A Level French (spec from 2016) - Topics Scraper (max depth L2)

Spec:
  https://www.eduqas.co.uk/media/pb5dz24v/eduqas-a-level-french-spec-from-2016-r.pdf

Entry code in spec: A800QS

This scraper focuses on the *curriculum structure* that supports flashcard generation:
- Themes and sub-themes (explicit in the spec)
- Prescribed works (explicit list of 6 literary works + 6 films)
- Assessment components (high-level shells only; avoid assessment metadata)

Hierarchy (L0-L2):
  - L0: Themes and sub-themes
    - L1: Theme
      - L2: Sub-theme
  - L0: Prescribed works for Component 3
    - L1: Literary works / Films
      - L2: Work title (with author/director where given)
  - L0: Components (1..3)
    - L1: Task shells
      - L2: Key requirements (brief)
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
    "name": "French",
    "qualification": "A-Level",
    "pdf_url": "https://www.eduqas.co.uk/media/pb5dz24v/eduqas-a-level-french-spec-from-2016-r.pdf",
}

SUBJECTS = [
    {**SUBJECT, "code": "EDUQAS-A800QS", "exam_board": "EDUQAS"},
    {**SUBJECT, "code": "WJEC-A800QS", "exam_board": "WJEC"},
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

    # L0: Themes and sub-themes (explicit list in the spec)
    l0_themes = "THEMES"
    nodes.append(Node(code=l0_themes, title="Themes and sub-themes", level=0, parent=None))

    themes = [
        (
            "T1",
            "Being a young person in French-speaking society",
            [
                "Families and citizenship",
                "Youth trends and personal identity",
                "Education and employment opportunities",
            ],
        ),
        (
            "T2",
            "Understanding the French-speaking world",
            [
                "Regional culture and heritage in France, French-speaking countries and communities",
                "Media, art, film and music in the French-speaking world",
            ],
        ),
        (
            "T3",
            "Diversity and difference",
            [
                "Migration and integration",
                "Cultural identity and marginalisation",
                "Cultural enrichment and celebrating difference",
                "Discrimination and diversity",
            ],
        ),
        (
            "T4",
            "France 1940–1950: The Occupation and post-war years",
            [
                "June 1940–May 1945",
                "The cultural dimension in occupied France",
                "1945–1950",
            ],
        ),
    ]

    for tcode, title, subs in themes:
        l1 = f"{l0_themes}_{tcode}"
        nodes.append(Node(code=l1, title=title, level=1, parent=l0_themes))
        for i, s in enumerate(subs, 1):
            nodes.append(Node(code=f"{l1}_{i:02d}", title=s, level=2, parent=l1))

    # L0: Prescribed works
    l0_works = "WORKS"
    nodes.append(Node(code=l0_works, title="Prescribed works for Component 3", level=0, parent=None))
    l1_lit = f"{l0_works}_LIT"
    l1_films = f"{l0_works}_FILM"
    nodes.append(Node(code=l1_lit, title="Literary works", level=1, parent=l0_works))
    nodes.append(Node(code=l1_films, title="Films", level=1, parent=l0_works))

    literary = [
        "Delphine de Vigan: No et Moi (novel, 2007)",
        "Fouad Laroui: Une année chez les Français (novel, 2010)",
        "Jean Anouilh: Antigone (play, 1944)",
        "Albert Camus: L’Étranger (novel, 1942)",
        "Vercors: Le silence de la mer (novel, 1942)",
        "Guy de Maupassant: Boule de Suif et autres contes de guerre (novel, 1880)",
    ]
    films = [
        "Éric Toledano, Olivier Nakache: Intouchables (feature film, 2011)",
        "Christophe Barratier: Les Choristes (feature film, 2004)",
        "Ismaël Ferroukhi: Le Grand Voyage (feature film, 2004)",
        "Mathieu Kassovitz: La Haine (feature film, 1995)",
        "Louis Malle: Au Revoir les Enfants (feature film, 1987)",
        "Gérard Jugnot: Monsieur Batignole (feature film, 2002)",
    ]
    for i, w in enumerate(literary, 1):
        nodes.append(Node(code=f"{l1_lit}_{i:02d}", title=w, level=2, parent=l1_lit))
    for i, w in enumerate(films, 1):
        nodes.append(Node(code=f"{l1_films}_{i:02d}", title=w, level=2, parent=l1_films))

    # L0: Components (lightweight shells)
    components = [
        ("C1", "Component 1: Speaking", [
            ("TASKS", "Tasks", [
                "Task 1: Independent Research Project (presentation + discussion)",
                "Task 2: Discussion based on a stimulus card relating to one theme studied",
            ]),
            ("NOTES", "Key notes", [
                "Non-exam assessment (speaking test)",
                "Independent Research Project is required",
            ]),
        ]),
        ("C2", "Component 2: Listening, Reading and Translation", [
            ("PAP", "Paper structure", [
                "Listening",
                "Reading",
                "Translation into English",
                "Translation into French",
            ]),
            ("NOTES", "Key notes", [
                "Assesses themes and language skills",
            ]),
        ]),
        ("C3", "Component 3: Critical and analytical response in writing (closed-book)", [
            ("WORKS", "Works", [
                "Two essays: one must be based on a literary work",
                "Second essay: another literary work or a film (from prescribed list)",
            ]),
            ("NOTES", "Key notes", [
                "Closed-book assessment",
                "Focus on critical/analytical response to works",
            ]),
        ]),
    ]

    for ccode, ctitle, sections in components:
        nodes.append(Node(code=ccode, title=ctitle, level=0, parent=None))
        for scode, stitle, bullets in sections:
            l1 = f"{ccode}_{scode}"
            nodes.append(Node(code=l1, title=stitle, level=1, parent=ccode))
            for i, b in enumerate(bullets, 1):
                nodes.append(Node(code=f"{l1}_{i:02d}", title=b, level=2, parent=l1))

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("EDUQAS A LEVEL FRENCH - TOPICS SCRAPER (L0-L2)")
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
    print("[OK] French (A-Level) scrape complete (uploaded to EDUQAS + WJEC).")


if __name__ == "__main__":
    main()


