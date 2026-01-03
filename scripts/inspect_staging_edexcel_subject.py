#!/usr/bin/env python
"""
Inspect staging data for a single subject (focus: Edexcel A-Level topic hierarchy).

This is a lightweight "SQL-like" audit you can run locally without opening the Supabase SQL editor.

Usage:
  python scripts/inspect_staging_edexcel_subject.py 9PS0
  python scripts/inspect_staging_edexcel_subject.py 9PS0 --board Edexcel --qual "A-Level"
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import io
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from supabase import create_client


CODE_2_RE = re.compile(r"^\d+\.\d+$")
CODE_3_RE = re.compile(r"^\d+\.\d+\.\d+$")
ANY_3PART_IN_TEXT_RE = re.compile(r"\b\d+\.\d+\.\d+\b")


@dataclass(frozen=True)
class SubjectKey:
    subject_code: str
    qualification_type: str
    exam_board: str


def _load_env() -> None:
    """
    Load .env in a forgiving way:
    - Try CWD
    - Try repo root (one level up from this file's parent)
    """
    load_dotenv()
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env", override=False)


def _get_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment. "
            "Add them to flash-curriculum-pipeline/.env or your shell env."
        )
    return create_client(url, key)


def _find_subject(sb, subject_code: str, qualification_type: str, exam_board: str) -> Dict[str, Any]:
    # Board casing varies in your staging history; accept both.
    boards = list({exam_board, exam_board.upper(), exam_board.title()})
    resp = (
        sb.table("staging_aqa_subjects")
        # Keep this select intentionally conservative: some staging schemas don't include timestamps.
        .select("id, subject_code, subject_name, qualification_type, exam_board, specification_url")
        .eq("subject_code", subject_code)
        .eq("qualification_type", qualification_type)
        .in_("exam_board", boards)
        .execute()
    )
    data = resp.data or []
    if not data:
        raise SystemExit(
            f"Subject not found in staging_aqa_subjects: code={subject_code} qual={qualification_type} board in {boards}"
        )
    if len(data) > 1:
        # Prefer exact match on board first, else latest updated
        exact = [s for s in data if s.get("exam_board") == exam_board]
        if exact:
            data = exact
        data.sort(key=lambda s: (s.get("updated_at") or ""), reverse=True)
    return data[0]


def _fetch_topics(sb, subject_id: str) -> List[Dict[str, Any]]:
    # Pull only what we need for analysis.
    resp = (
        sb.table("staging_aqa_topics")
        # Keep this select conservative: created_at/updated_at may not exist in staging.
        .select("id, topic_code, topic_name, topic_level, parent_topic_id")
        .eq("subject_id", subject_id)
        .order("topic_level")
        .order("topic_code")
        .execute()
    )
    return resp.data or []


def _summarize(subject: Dict[str, Any], topics: List[Dict[str, Any]]) -> None:
    print("=" * 90)
    print("STAGING SUBJECT INSPECTOR")
    print("=" * 90)
    print(f"Subject: {subject.get('subject_name')}")
    print(f"Code:    {subject.get('subject_code')}")
    print(f"Board:   {subject.get('exam_board')}")
    print(f"Qual:    {subject.get('qualification_type')}")
    print(f"Topics:  {len(topics)}")
    print(f"Spec:    {subject.get('specification_url')}")
    print("-" * 90)

    by_level = Counter(t.get("topic_level") for t in topics)
    print("Counts by topic_level:")
    for level in sorted(by_level.keys()):
        print(f"  - L{level}: {by_level[level]}")

    codes_2 = [t for t in topics if CODE_2_RE.match((t.get("topic_code") or "").strip())]
    codes_3 = [t for t in topics if CODE_3_RE.match((t.get("topic_code") or "").strip())]
    print("\nCode-shape counts:")
    print(f"  - two-part numeric codes (e.g., 1.1):     {len(codes_2)}")
    print(f"  - three-part numeric codes (e.g., 1.1.1): {len(codes_3)}")

    parent_ids = {t.get("id") for t in topics}
    orphans = [
        t for t in topics
        if t.get("parent_topic_id") is not None and t.get("parent_topic_id") not in parent_ids
    ]
    has_parent = [t for t in topics if t.get("parent_topic_id") is not None]
    print("\nHierarchy integrity:")
    print(f"  - topics with parent_topic_id: {len(has_parent)}")
    print(f"  - orphaned parent_topic_id refs: {len(orphans)}")

    contaminated = [
        t for t in topics
        if ANY_3PART_IN_TEXT_RE.search((t.get("topic_name") or "") or "")
        and not CODE_3_RE.match((t.get("topic_code") or "").strip())
    ]
    print("\nLikely 'swallowed subtopics' rows (topic_name contains 1.1.1 etc but row itself is not 1.1.1):")
    print(f"  - count: {len(contaminated)}")
    if contaminated:
        print("  - examples:")
        for t in contaminated[:12]:
            code = t.get("topic_code")
            lvl = t.get("topic_level")
            name = (t.get("topic_name") or "").replace("\n", " ").strip()
            name_short = name[:160] + ("..." if len(name) > 160 else "")
            print(f"    • L{lvl} {code}: {name_short}")

    print("\nSample topics (first 25 by level/code):")
    for t in topics[:25]:
        code = t.get("topic_code")
        lvl = t.get("topic_level")
        parent = t.get("parent_topic_id")
        name = (t.get("topic_name") or "").replace("\n", " ").strip()
        name_short = name[:120] + ("..." if len(name) > 120 else "")
        print(f"  - L{lvl} {code} (parent={'Y' if parent else 'N'}): {name_short}")

    # Paper distribution (how many Level 1 topics sit under each Paper)
    code_to_id = {t.get("topic_code"): t.get("id") for t in topics}
    id_to_topic = {t.get("id"): t for t in topics}
    paper_ids = {p: code_to_id.get(p) for p in ["Paper1", "Paper2", "Paper3"]}
    print("\nPaper distribution (Level 1 Topic* rows directly under each Paper):")
    for paper_code, paper_id in paper_ids.items():
        if not paper_id:
            print(f"  - {paper_code}: (missing Paper row)")
            continue
        direct_children = [t for t in topics if t.get("parent_topic_id") == paper_id and (t.get("topic_code") or "").startswith("Topic")]
        print(f"  - {paper_code}: {len(direct_children)} Topic* children")
        for t in direct_children[:12]:
            print(f"    • {t.get('topic_code')}: {(t.get('topic_name') or '')[:80].strip()}")

    # Spot-check: show children under any "Issues and debates" L2 rows (these should be split bullets)
    issues_rows = [
        t for t in topics
        if (t.get("topic_level") == 2 or str(t.get("topic_level")) == "2")
        and "issues and debates" in ((t.get("topic_name") or "").lower())
    ]
    if issues_rows:
        print("\nIssues/debates split check (direct children of L2 rows containing 'Issues and debates'):")
        for row in issues_rows[:6]:
            row_id = row.get("id")
            kids = [t for t in topics if t.get("parent_topic_id") == row_id]
            print(f"  - {row.get('topic_code')} children: {len(kids)}")
            for k in kids[:10]:
                print(f"    • {k.get('topic_code')}: {(k.get('topic_name') or '')[:90].strip()}")


def main() -> int:
    # Force UTF-8 output (Windows consoles often default to cp1252, which breaks on bullets, etc.)
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser()
    parser.add_argument("subject_code", nargs="?", default="9PS0")
    parser.add_argument("--board", default="Edexcel")
    parser.add_argument("--qual", default="A-Level", dest="qualification_type")
    args = parser.parse_args()

    _load_env()
    sb = _get_client()

    subject_code = str(args.subject_code).strip().upper()
    qual = str(args.qualification_type).strip()
    board = str(args.board).strip()

    subject = _find_subject(sb, subject_code, qual, board)
    topics = _fetch_topics(sb, subject["id"])
    _summarize(subject, topics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


