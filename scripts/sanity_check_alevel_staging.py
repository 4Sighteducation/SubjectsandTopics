"""
Sanity check: EDUQAS + WJEC A-Level staging integrity

Checks:
1) Within each exam_board (EDUQAS, WJEC), there should be NO duplicate subject rows for the same
   logical subject name (normalized subject_name).
2) Each A-Level subject should have >0 topics.
3) Parent linkage integrity: no orphaned parent_topic_id rows for these subjects.
4) Cross-board duplication: for paired entry codes A###QS, ensure EDUQAS-A###QS and WJEC-A###QS exist
   and have the same topic counts (optionally allow differences via threshold).

Usage:
  cd <repo>
  PYTHONIOENCODING=utf-8 python scripts/sanity_check_alevel_staging.py
"""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


ENV_PATH = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")

BOARDS = ["EDUQAS", "WJEC"]
QUAL = "A-Level"

# If you want to allow minor diffs between boards (e.g., small legacy variation), raise this.
ALLOWED_CROSS_BOARD_TOPIC_DIFF = 0


@dataclass(frozen=True)
class Subject:
    id: str
    subject_code: str
    subject_name: str
    exam_board: str


def norm_subject_name(name: str) -> str:
    s = (name or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*\(A-Level\)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s*-\s*$", "", s).strip()
    return s.lower()


def load_supabase():
    load_dotenv(ENV_PATH)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_KEY not found in .env")
    return create_client(url, key)


def fetch_subjects(sb, board: str) -> list[Subject]:
    rows = (
        sb.table("staging_aqa_subjects")
        .select("id,subject_code,subject_name,exam_board")
        .eq("qualification_type", QUAL)
        .eq("exam_board", board)
        .execute()
        .data
        or []
    )
    return [Subject(**r) for r in rows]


def topic_count(sb, *, subject_id: str, board: str) -> int:
    res = sb.table("staging_aqa_topics").select("id", count="exact").eq("subject_id", subject_id).eq("exam_board", board).execute()
    return int(res.count or 0)


def orphan_parent_count(sb, *, subject_id: str, board: str) -> int:
    """
    Fetch topic ids and parent ids for the subject; compute orphans client-side.
    IMPORTANT: Supabase/PostgREST will paginate; do NOT assume a single request returns all rows.
    """
    page_size = 1000
    offset = 0
    ids: set[str] = set()
    parent_rows: list[dict] = []

    while True:
        res = (
            sb.table("staging_aqa_topics")
            .select("id,parent_topic_id")
            .eq("subject_id", subject_id)
            .eq("exam_board", board)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break
        for r in batch:
            ids.add(r["id"])
            if r.get("parent_topic_id"):
                parent_rows.append(r)
        if len(batch) < page_size:
            break
        offset += page_size

    orphans = 0
    for r in parent_rows:
        pid = r.get("parent_topic_id")
        if pid and pid not in ids:
            orphans += 1
    return orphans


def main() -> None:
    sb = load_supabase()

    print("=" * 90)
    print("SANITY CHECK: EDUQAS + WJEC A-LEVEL STAGING")
    print("=" * 90)

    subjects_by_board: dict[str, list[Subject]] = {b: fetch_subjects(sb, b) for b in BOARDS}

    # 1) Within-board duplicate normalized names
    print("\n## Within-board duplicates")
    dup_fail = False
    for board, subs in subjects_by_board.items():
        groups: dict[str, list[Subject]] = defaultdict(list)
        for s in subs:
            groups[norm_subject_name(s.subject_name)].append(s)
        dups = {k: v for k, v in groups.items() if len(v) > 1}
        print(f"- {board}: {len(dups)} duplicate groups")
        for k, items in sorted(dups.items(), key=lambda kv: kv[0]):
            dup_fail = True
            print(f"  - {k}:")
            for it in items:
                print(f"    - {it.subject_name} ({it.subject_code}) id={it.id}")

    # 2) Topic counts + 3) orphan parents
    print("\n## Topic counts + parent integrity")
    zero_fail = False
    orphan_fail = False
    counts_by_code: dict[tuple[str, str], int] = {}

    for board, subs in subjects_by_board.items():
        zeros = 0
        orphans_total = 0
        for s in subs:
            cnt = topic_count(sb, subject_id=s.id, board=board)
            counts_by_code[(board, s.subject_code)] = cnt
            if cnt == 0:
                zeros += 1
            orph = orphan_parent_count(sb, subject_id=s.id, board=board)
            orphans_total += orph
        print(f"- {board}: subjects={len(subs)} zero-topic={zeros} orphan-parent-refs={orphans_total}")
        if zeros:
            zero_fail = True
            for s in sorted(subs, key=lambda x: x.subject_name):
                if counts_by_code[(board, s.subject_code)] == 0:
                    print(f"  - ZERO topics: {s.subject_name} ({s.subject_code}) id={s.id}")
        if orphans_total:
            orphan_fail = True

    # 4) Cross-board A###QS pairing
    print("\n## Cross-board A###QS pairs (EDUQAS vs WJEC)")
    pair_fail = False
    eduqas_codes = {s.subject_code for s in subjects_by_board["EDUQAS"]}
    wjec_codes = {s.subject_code for s in subjects_by_board["WJEC"]}

    eduqas_a = sorted([c for c in eduqas_codes if re.fullmatch(r"EDUQAS-A\d{3}QS", c, flags=re.I)])
    for ec in eduqas_a:
        suffix = ec.split("-", 1)[1]  # A###QS
        wc = f"WJEC-{suffix}"
        e_cnt = counts_by_code.get(("EDUQAS", ec), 0)
        w_cnt = counts_by_code.get(("WJEC", wc), 0)
        exists = wc in wjec_codes
        if not exists:
            pair_fail = True
            print(f"- MISSING WJEC pair for {ec} (expected {wc})")
            continue
        diff = abs(e_cnt - w_cnt)
        if diff > ALLOWED_CROSS_BOARD_TOPIC_DIFF:
            pair_fail = True
            print(f"- COUNT MISMATCH {suffix}: EDUQAS={e_cnt} vs WJEC={w_cnt} (diff {diff})")

    # Summary
    print("\n## Result")
    failures = []
    if dup_fail:
        failures.append("within-board duplicates")
    if zero_fail:
        failures.append("zero-topic subjects")
    if orphan_fail:
        failures.append("orphan parent refs")
    if pair_fail:
        failures.append("cross-board mismatches")

    if failures:
        print("FAIL:", ", ".join(failures))
        raise SystemExit(1)
    print("PASS: no duplicates, no zero-topic subjects, parent links OK, and EDUQAS/WJEC pairs match.")


if __name__ == "__main__":
    main()


