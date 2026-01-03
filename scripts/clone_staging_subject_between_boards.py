"""
Clone a staging subject + its full topic tree from one exam board to another.

Use case:
- WJEC and EDUQAS specs are identical but must exist as separate entities in staging.

This script:
- Finds the source subject (by id or by board/qual/name substring)
- Creates/updates the destination subject row (new subject_code / exam_board)
- Copies all topics, preserving topic_code/topic_level/topic_name and parent relationships

Usage (PowerShell):
  py scripts/clone_staging_subject_between_boards.py ^
    --from-board WJEC --to-board EDUQAS ^
    --qualification "A-Level" ^
    --name-contains "Music" ^
    --to-subject-code "EDUQAS-M"

Notes:
- Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in .env at repo root.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


@dataclass(frozen=True)
class Subject:
    id: str
    subject_code: str
    subject_name: str
    qualification_type: str
    exam_board: str
    specification_url: str | None


def load_supabase():
    load_dotenv(ENV_PATH)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_KEY not found in .env")
    return create_client(url, key)


def fetch_subject_by_id(sb, subject_id: str) -> Subject:
    rows = (
        sb.table("staging_aqa_subjects")
        .select("id,subject_code,subject_name,qualification_type,exam_board,specification_url")
        .eq("id", subject_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        raise RuntimeError(f"Subject not found: {subject_id}")
    r = rows[0]
    return Subject(
        id=r["id"],
        subject_code=r["subject_code"],
        subject_name=r["subject_name"],
        qualification_type=r["qualification_type"],
        exam_board=r["exam_board"],
        specification_url=r.get("specification_url"),
    )


def find_subject(sb, *, board: str, qualification: str, name_contains: str) -> Subject:
    rows = (
        sb.table("staging_aqa_subjects")
        .select("id,subject_code,subject_name,qualification_type,exam_board,specification_url")
        .eq("exam_board", board)
        .eq("qualification_type", qualification)
        .ilike("subject_name", f"%{name_contains}%")
        .execute()
        .data
        or []
    )
    if not rows:
        raise RuntimeError(f"No subject found for {board=} {qualification=} {name_contains=}")
    if len(rows) > 1:
        msg = "\n".join([f"- id={r['id']} code={r['subject_code']} name={r['subject_name']}" for r in rows])
        raise RuntimeError(f"Multiple matches; pass --from-subject-id instead:\n{msg}")
    r = rows[0]
    return Subject(
        id=r["id"],
        subject_code=r["subject_code"],
        subject_name=r["subject_name"],
        qualification_type=r["qualification_type"],
        exam_board=r["exam_board"],
        specification_url=r.get("specification_url"),
    )


def count_topics(sb, *, subject_id: str, board: str) -> int:
    return (
        sb.table("staging_aqa_topics")
        .select("id", count="exact")
        .eq("subject_id", subject_id)
        .eq("exam_board", board)
        .execute()
        .count
        or 0
    )


def clone_topics(sb, *, from_subject_id: str, from_board: str, to_subject_id: str, to_board: str) -> int:
    # Fetch source topics
    src = (
        sb.table("staging_aqa_topics")
        .select("id,topic_code,topic_name,topic_level,parent_topic_id")
        .eq("subject_id", from_subject_id)
        .eq("exam_board", from_board)
        .execute()
        .data
        or []
    )
    if not src:
        raise RuntimeError("Source subject has 0 topics; refusing to clone.")

    id_to_code = {r["id"]: r["topic_code"] for r in src}
    rows_to_insert = []
    for r in src:
        parent_code = id_to_code.get(r["parent_topic_id"]) if r.get("parent_topic_id") else None
        rows_to_insert.append(
            {
                "topic_code": r["topic_code"],
                "topic_name": r["topic_name"],
                "topic_level": r["topic_level"],
                "subject_id": to_subject_id,
                "exam_board": to_board,
                "_parent_code": parent_code,  # temp field for linking after insert
            }
        )

    # Clear destination topics (if any), deepest-first, batched
    deleted_total = 0
    BATCH = 200
    for lvl in range(7, -1, -1):
        while True:
            rows = (
                sb.table("staging_aqa_topics")
                .select("id")
                .eq("subject_id", to_subject_id)
                .eq("exam_board", to_board)
                .eq("topic_level", lvl)
                .limit(BATCH)
                .execute()
                .data
                or []
            )
            if not rows:
                break
            ids = [x["id"] for x in rows]
            res = sb.table("staging_aqa_topics").delete().in_("id", ids).execute()
            deleted_total += len(res.data or [])

    # Insert topics without parent links
    insert_payload = []
    for r in rows_to_insert:
        insert_payload.append(
            {
                "subject_id": r["subject_id"],
                "topic_code": r["topic_code"],
                "topic_name": r["topic_name"],
                "topic_level": r["topic_level"],
                "exam_board": r["exam_board"],
            }
        )

    inserted = sb.table("staging_aqa_topics").insert(insert_payload).execute().data or []
    if len(inserted) != len(insert_payload):
        raise RuntimeError(f"Insert mismatch: inserted={len(inserted)} expected={len(insert_payload)}")

    code_to_new_id = {r["topic_code"]: r["id"] for r in inserted}

    # Link parents
    linked = 0
    for r in rows_to_insert:
        parent_code = r["_parent_code"]
        if not parent_code:
            continue
        child_id = code_to_new_id.get(r["topic_code"])
        parent_id = code_to_new_id.get(parent_code)
        if child_id and parent_id:
            sb.table("staging_aqa_topics").update({"parent_topic_id": parent_id}).eq("id", child_id).execute()
            linked += 1

    print(f"[OK] Destination cleared: {deleted_total} old topics deleted")
    print(f"[OK] Inserted: {len(inserted)} topics")
    print(f"[OK] Linked:   {linked} parent relationships")
    return len(inserted)


def upsert_dest_subject(
    sb,
    *,
    src: Subject,
    to_board: str,
    to_subject_code: str,
    override_subject_name: str | None,
) -> Subject:
    payload = {
        "subject_name": override_subject_name or src.subject_name,
        "subject_code": to_subject_code,
        "qualification_type": src.qualification_type,
        "specification_url": src.specification_url,
        "exam_board": to_board,
    }
    res = (
        sb.table("staging_aqa_subjects")
        .upsert(payload, on_conflict="subject_code,qualification_type,exam_board")
        .execute()
    )
    r = (res.data or [None])[0]
    if not r:
        # Some supabase configs return no rows; refetch
        r = (
            sb.table("staging_aqa_subjects")
            .select("id,subject_code,subject_name,qualification_type,exam_board,specification_url")
            .eq("subject_code", to_subject_code)
            .eq("qualification_type", src.qualification_type)
            .eq("exam_board", to_board)
            .limit(1)
            .execute()
            .data
            or [None]
        )[0]
    if not r:
        raise RuntimeError("Failed to upsert destination subject.")
    return Subject(
        id=r["id"],
        subject_code=r["subject_code"],
        subject_name=r["subject_name"],
        qualification_type=r["qualification_type"],
        exam_board=r["exam_board"],
        specification_url=r.get("specification_url"),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-board", required=True)
    ap.add_argument("--to-board", required=True)
    ap.add_argument("--qualification", required=True)
    ap.add_argument("--name-contains", default=None)
    ap.add_argument("--from-subject-id", default=None)
    ap.add_argument("--to-subject-code", required=True)
    ap.add_argument("--override-subject-name", default=None)
    args = ap.parse_args()

    sb = load_supabase()

    if args.from_subject_id:
        src = fetch_subject_by_id(sb, args.from_subject_id)
    else:
        if not args.name_contains:
            raise RuntimeError("Pass either --from-subject-id or --name-contains")
        src = find_subject(sb, board=args.from_board, qualification=args.qualification, name_contains=args.name_contains)

    if src.exam_board != args.from_board or src.qualification_type != args.qualification:
        raise RuntimeError(f"Source subject mismatch: got {src.exam_board=} {src.qualification_type=}")

    print(f"[INFO] Source: {src.subject_name} id={src.id} code={src.subject_code} board={src.exam_board} qual={src.qualification_type}")
    print(f"[INFO] Source topic count: {count_topics(sb, subject_id=src.id, board=args.from_board)}")

    dest = upsert_dest_subject(
        sb,
        src=src,
        to_board=args.to_board,
        to_subject_code=args.to_subject_code,
        override_subject_name=args.override_subject_name,
    )
    print(f"[INFO] Dest:   {dest.subject_name} id={dest.id} code={dest.subject_code} board={dest.exam_board} qual={dest.qualification_type}")
    print(f"[INFO] Dest current topic count: {count_topics(sb, subject_id=dest.id, board=args.to_board)}")

    clone_topics(
        sb,
        from_subject_id=src.id,
        from_board=args.from_board,
        to_subject_id=dest.id,
        to_board=args.to_board,
    )

    print("[OK] Clone complete.")


if __name__ == "__main__":
    main()






