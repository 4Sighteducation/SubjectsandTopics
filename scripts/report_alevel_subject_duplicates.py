"""
Report (and generate SQL for) duplicate / placeholder A-Level subjects in staging.

Goal:
- Within each exam board (EDUQAS, WJEC), keep ONE subject row per real subject.
- Allow EDUQAS and WJEC to have separate subject rows for the *same* subject (that is desired).
- Remove legacy placeholder rows (e.g. EDUQAS-P, EDUQAS-PE, EDUQAS-F) and any 0-topic shells.

This script DOES NOT delete anything. It prints:
- Detected duplicate groups within each board (by normalized subject_name)
- Recommended keep/delete
- SQL you can run in Supabase SQL editor to delete topics first, then subjects

Usage:
  PYTHONIOENCODING=utf-8 python scripts/report_alevel_subject_duplicates.py
"""

from __future__ import annotations

import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


@dataclass(frozen=True)
class SubjectRow:
    id: str
    subject_code: str
    subject_name: str
    exam_board: str
    topic_count: int
    norm_name: str


def norm_name(name: str) -> str:
    s = (name or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*\(A-Level\)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s*-\s*$", "", s).strip()
    return s.lower()


def load_supabase():
    env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
    load_dotenv(env_path)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_KEY not found in .env")
    return create_client(url, key)


def fetch_alevel_subjects(supabase, *, board: str) -> list[SubjectRow]:
    subs = (
        supabase.table("staging_aqa_subjects")
        .select("id,subject_code,subject_name,exam_board")
        .eq("qualification_type", "A-Level")
        .eq("exam_board", board)
        .execute()
        .data
        or []
    )

    rows: list[SubjectRow] = []
    for s in subs:
        sid = s["id"]
        cnt = (
            supabase.table("staging_aqa_topics")
            .select("id", count="exact")
            .eq("subject_id", sid)
            .eq("exam_board", board)
            .execute()
            .count
            or 0
        )
        rows.append(
            SubjectRow(
                id=sid,
                subject_code=s["subject_code"],
                subject_name=s["subject_name"],
                exam_board=board,
                topic_count=cnt,
                norm_name=norm_name(s["subject_name"]),
            )
        )
    return rows


def pick_keeper(board: str, items: list[SubjectRow]) -> SubjectRow:
    """
    Prefer the 'real' A-level code row (BOARD-A###QS) when present.
    Otherwise keep the row with the highest topic_count.
    """
    alevel_code_re = re.compile(rf"^{re.escape(board)}-A\d{{3}}QS$", re.I)
    preferred = [s for s in items if alevel_code_re.match(s.subject_code)]
    if preferred:
        # if multiple, keep the one with most topics
        return sorted(preferred, key=lambda r: (-r.topic_count, r.subject_code))[0]
    return sorted(items, key=lambda r: (-r.topic_count, r.subject_code))[0]


def main() -> None:
    supabase = load_supabase()
    boards = ["EDUQAS", "WJEC"]

    to_delete: list[SubjectRow] = []

    for board in boards:
        rows = fetch_alevel_subjects(supabase, board=board)
        groups: dict[str, list[SubjectRow]] = defaultdict(list)
        for r in rows:
            groups[r.norm_name].append(r)

        dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
        print(f"\n=== {board} A-Level duplicate groups within board: {len(dup_groups)} ===")
        for k, items in sorted(dup_groups.items(), key=lambda kv: kv[0]):
            keeper = pick_keeper(board, items)
            print(f"\n-- {k}")
            for it in sorted(items, key=lambda r: (-r.topic_count, r.subject_code)):
                tag = "KEEP" if it.id == keeper.id else "DEL "
                print(f"  [{tag}] {it.subject_name:<35} {it.subject_code:<14} topics={it.topic_count:<4} id={it.id}")
                if tag == "DEL ":
                    to_delete.append(it)

        # also delete 0-topic shells that are not BOARD-A###QS
        alevel_code_re = re.compile(rf"^{re.escape(board)}-A\d{{3}}QS$", re.I)
        zeros = [r for r in rows if r.topic_count == 0 and not alevel_code_re.match(r.subject_code)]
        if zeros:
            print(f"\n=== {board} additional 0-topic shells (non {board}-A###QS): {len(zeros)} ===")
            for it in sorted(zeros, key=lambda r: (r.subject_name, r.subject_code)):
                print(f"  [DEL ] {it.subject_name:<35} {it.subject_code:<14} topics=0    id={it.id}")
                to_delete.append(it)

    # de-dupe delete list by id
    uniq: dict[str, SubjectRow] = {s.id: s for s in to_delete}
    deletions = list(uniq.values())

    print(f"\n=== TOTAL SUBJECTS RECOMMENDED FOR DELETION: {len(deletions)} ===")
    if not deletions:
        return

    # Print SQL
    ids = [d.id for d in deletions]
    print("\n--- SQL (delete topics first, then subjects) ---\n")
    # Chunk IDs to keep IN lists manageable
    chunk = 50
    for i in range(0, len(ids), chunk):
        part = ids[i : i + chunk]
        in_list = ", ".join([f"'{x}'" for x in part])
        print(f"delete from staging_aqa_topics where subject_id in ({in_list});")
    print()
    for i in range(0, len(ids), chunk):
        part = ids[i : i + chunk]
        in_list = ", ".join([f"'{x}'" for x in part])
        print(f"delete from staging_aqa_subjects where id in ({in_list});")


if __name__ == "__main__":
    main()


