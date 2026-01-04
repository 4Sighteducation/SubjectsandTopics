"""
Promote ONE subject from staging -> production, then (optionally) regenerate embeddings in topic_ai_metadata.

Why:
- Students report missing/weird topics for one subject
- You fix/scrape into staging, validate, then promote just that subject
- Regenerate just that subject's embeddings (no giant full rebuild)

Requirements:
- Python 3.10+
- pip install -r requirements.txt

Env vars:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- OPENAI_API_KEY (required only if --generate-embeddings is enabled; summaries optional)

Notes:
- This assumes staging tables exist in the SAME Supabase project:
  - staging_aqa_subjects
  - staging_aqa_topics
  (Yes, naming is legacy; they store multi-board data and include an exam_board field.)

Usage examples:
  python scripts/promote_subject_and_embeddings.py --exam-board Edexcel --qualification A_LEVEL --subject-code 9PE0 --generate-embeddings
  python scripts/promote_subject_and_embeddings.py --exam-board Edexcel --qualification A_LEVEL --subject-name "Physical Education" --generate-embeddings --generate-summaries
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from supabase import create_client
from dotenv import load_dotenv

# Load local .env (keeps CLI usage simple)
_env_path = Path(__file__).resolve().parents[1] / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


def die(msg: str) -> None:
    print(f"[FATAL] {msg}", file=sys.stderr)
    raise SystemExit(2)


def getenv_required(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        die(f"Missing env var {name}")
    return v


def pgvector_literal(vec: List[float]) -> str:
    # pgvector input format: [0.1,0.2,...]
    # Keep it compact; PostgREST will cast text -> vector.
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def openai_embed(texts: List[str]) -> List[List[float]]:
    """
    Uses OpenAI embeddings (text-embedding-3-small) and returns vectors.
    """
    from openai import OpenAI  # type: ignore

    api_key = getenv_required("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    # Batch call
    res = client.embeddings.create(model="text-embedding-3-small", input=texts)
    # Preserve ordering
    return [d.embedding for d in res.data]


def openai_summary(topic_name: str, full_path: List[str]) -> str:
    """
    Optional small plain-English summary for search results.
    """
    from openai import OpenAI  # type: ignore

    api_key = getenv_required("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    path = " > ".join([p for p in full_path if p])
    prompt = (
        "Write a short plain-English summary (1 sentence, max 20 words) of the curriculum topic.\n"
        f"Topic path: {path}\n"
        f"Topic name: {topic_name}\n"
        "Return only the sentence."
    )

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You write crisp educational summaries."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=80,
    )
    return (res.choices[0].message.content or "").strip() or topic_name


def fetch_single(
    sb, table: str, filters: List[Tuple[str, str, Any]], select: str
) -> Optional[Dict[str, Any]]:
    q = sb.table(table).select(select)
    for col, op, val in filters:
        if op == "eq":
            q = q.eq(col, val)
        elif op == "ilike":
            q = q.ilike(col, val)
        else:
            die(f"Unsupported op: {op}")
    res = q.maybe_single().execute()
    return res.data


def main() -> None:
    # Force UTF-8 output (Windows consoles may default to cp1252; avoid crashes on unicode like ✓)
    try:
        if (getattr(sys.stdout, "encoding", "") or "").lower() != "utf-8":
            import io

            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--exam-board", required=True, help="e.g. Edexcel, AQA, OCR")
    ap.add_argument("--qualification", required=True, help="e.g. A_LEVEL, GCSE, INTERNATIONAL_GCSE")
    ap.add_argument("--subject-code", default="", help="preferred selector (exact match)")
    ap.add_argument("--subject-name", default="", help="fallback selector (ilike)")
    ap.add_argument("--generate-embeddings", action="store_true")
    ap.add_argument("--generate-summaries", action="store_true", help="extra cost; optional")
    ap.add_argument("--batch-size", type=int, default=25)
    args = ap.parse_args()

    if not args.subject_code and not args.subject_name:
        die("Provide --subject-code or --subject-name")

    supabase_url = getenv_required("SUPABASE_URL")
    # Backward compatible: older scripts/use-cases store the service role key as SUPABASE_SERVICE_KEY.
    service_key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or "").strip()
    if not service_key:
        die("Missing env var SUPABASE_SERVICE_ROLE_KEY (or legacy SUPABASE_SERVICE_KEY)")
    sb = create_client(supabase_url, service_key)

    exam_board = args.exam_board.strip()
    qualification = args.qualification.strip()

    # 1) Ensure exam board exists (upsert)
    print(f"[1/5] Ensuring exam board exists: {exam_board}")
    sb.table("exam_boards").upsert(
        # NOTE: exam_boards.country is NOT NULL in production; default to UK for now.
        # If/when we add non-UK boards, extend this mapping.
        {"code": exam_board, "full_name": exam_board, "active": True, "country": "UK"},
        on_conflict="code",
    ).execute()

    eb = fetch_single(sb, "exam_boards", [("code", "eq", exam_board)], "id,code")
    if not eb:
        die("Failed to resolve exam_boards.id")

    qt = fetch_single(sb, "qualification_types", [("code", "eq", qualification)], "id,code")
    if not qt:
        die(f"qualification_types missing code={qualification}. Create it first.")

    # 2) Resolve staging subject row
    print("[2/5] Resolving staging subject row...")
    filters: List[Tuple[str, str, Any]] = [("exam_board", "eq", exam_board)]
    if args.subject_code:
        filters.append(("subject_code", "eq", args.subject_code.strip()))
    else:
        # staging uses various labels; ilike for robustness
        filters.append(("subject_name", "ilike", f"%{args.subject_name.strip()}%"))

    stg = fetch_single(
        sb,
        "staging_aqa_subjects",
        filters,
        "id,subject_code,subject_name,exam_board,qualification_type",
    )
    if not stg:
        die("No staging subject matched. Check staging_aqa_subjects filters.")

    subject_code = stg["subject_code"]
    subject_name = stg["subject_name"]
    print(f"  - staging subject: {subject_code} — {subject_name}")

    # 3) Upsert production subject row
    print("[3/5] Upserting production exam_board_subjects row...")
    sb.table("exam_board_subjects").upsert(
        {
            "subject_code": subject_code,
            "subject_name": subject_name,
            "exam_board_id": eb["id"],
            "qualification_type_id": qt["id"],
            "is_current": True,
        },
        on_conflict="subject_code,exam_board_id,qualification_type_id",
    ).execute()

    prod_subj = fetch_single(
        sb,
        "exam_board_subjects",
        [
            ("subject_code", "eq", subject_code),
            ("exam_board_id", "eq", eb["id"]),
            ("qualification_type_id", "eq", qt["id"]),
        ],
        "id,subject_code,subject_name",
    )
    if not prod_subj:
        die("Failed to resolve production exam_board_subjects row after upsert.")

    prod_subject_id = prod_subj["id"]
    print(f"  - production subject id: {prod_subject_id}")

    # 4) Replace curriculum_topics for this subject
    print("[4/5] Updating curriculum_topics for this subject (preserve IDs where possible)...")
    # NOTE: staging_aqa_topics does NOT always include sort_order. We compute a deterministic order client-side.
    topics_res = (
        sb.table("staging_aqa_topics")
        .select("id,topic_code,topic_name,topic_level,parent_topic_id,subject_id")
        .eq("subject_id", stg["id"])
        .order("topic_level")
        .order("topic_code")
        .execute()
    )
    stg_topics = topics_res.data or []
    if not stg_topics:
        die("No staging topics found for that staging subject id.")
    print(f"  - staging topics: {len(stg_topics)}")

    # Staging can contain accidental duplicates (especially from AI outputs), commonly at bullet level.
    # Production enforces uniqueness on (exam_board_subject_id, parent_topic_id, topic_level, topic_name),
    # so we must de-duplicate BEFORE promoting.
    def _norm_topic_name(x: Any) -> str:
        s = str(x or "")
        s = s.replace("\ufffd", "•").replace("●", "•")
        s = " ".join(s.split()).strip()
        return s

    # Merge duplicates by rewiring children to a canonical node, then dropping duplicates.
    stg_by_id: Dict[str, Dict[str, Any]] = {str(t["id"]): t for t in stg_topics if t.get("id")}
    children_by_parent: Dict[str, List[str]] = {}
    for t in stg_topics:
        pid = t.get("parent_topic_id")
        if pid:
            children_by_parent.setdefault(str(pid), []).append(str(t.get("id")))

    canonical_by_key: Dict[tuple, str] = {}
    dup_ids: List[str] = []
    # Deterministic canonical pick: lowest topic_code, then lowest UUID string.
    for t in sorted(
        (t for t in stg_topics if t.get("id")),
        key=lambda x: (str(x.get("topic_code") or ""), str(x.get("id") or "")),
    ):
        tid = str(t["id"])
        key = (
            str(t.get("parent_topic_id") or ""),
            int(t.get("topic_level") or 0),
            _norm_topic_name(t.get("topic_name")),
        )
        if key not in canonical_by_key:
            canonical_by_key[key] = tid
        else:
            dup_ids.append(tid)

    if dup_ids:
        # Rewire children of dup nodes -> canonical node
        for dup_id in dup_ids:
            dup = stg_by_id.get(dup_id)
            if not dup:
                continue
            key = (
                str(dup.get("parent_topic_id") or ""),
                int(dup.get("topic_level") or 0),
                _norm_topic_name(dup.get("topic_name")),
            )
            canon_id = canonical_by_key.get(key)
            if not canon_id or canon_id == dup_id:
                continue
            for child_id in children_by_parent.get(dup_id, []):
                child = stg_by_id.get(child_id)
                if child:
                    child["parent_topic_id"] = canon_id
        # Drop duplicate nodes from the list
        before = len(stg_topics)
        stg_topics = [t for t in stg_topics if str(t.get("id")) not in set(dup_ids)]
        print(f"  - staging duplicates removed: {before - len(stg_topics)} (rewired children where needed)")

    # Compute deterministic sort_order for production inserts/updates.
    # This avoids relying on a staging sort_order column and keeps ordering stable across runs.
    stg_topics_sorted = sorted(
        stg_topics,
        key=lambda t: (
            int(t.get("topic_level") or 0),
            str(t.get("topic_code") or ""),
            str(t.get("id") or ""),
        ),
    )
    stg_sort_order_by_id: Dict[str, int] = {
        str(t.get("id")): i for i, t in enumerate(stg_topics_sorted) if t.get("id")
    }

    # SAFETY:
    # Do NOT delete all production topics for a subject once users can have flashcards referencing topic_id.
    # Instead:
    # - Reuse existing production topic IDs where topic_code matches
    # - Insert only new topic_codes
    # - Optionally delete removed topic_codes (default: DO NOT delete; it can break existing flashcards)

    # Fetch existing production topics for this subject (id + topic_code).
    # We intentionally treat topic_code as the stable identity key for a node.
    # Matching by (level,name) can incorrectly collapse legitimately distinct nodes that share names.
    prod_rows = (
        sb.table("curriculum_topics")
        .select("id,topic_code")
        .eq("exam_board_subject_id", prod_subject_id)
        .execute()
        .data
        or []
    )
    prod_id_by_code = {
        r.get("topic_code"): r.get("id") for r in prod_rows if r.get("topic_code") and r.get("id")
    }

    # Upsert topics (pass 1): set parent_topic_id NULL until we patch relations.
    # Strategy:
    # - If production already has this topic_code, update that existing row (preserve id).
    # - Otherwise insert a new row using the staging UUID as the id (deterministic + helps parent mapping).
    upserts: List[Dict[str, Any]] = []
    for t in stg_topics:
        code = t.get("topic_code")
        stg_id = t.get("id")
        if not code or not stg_id:
            continue
        existing_id = prod_id_by_code.get(code)
        row = {
            "id": existing_id or stg_id,
            "exam_board_subject_id": prod_subject_id,
            "topic_code": code,
            "topic_name": t.get("topic_name"),
            "topic_level": t.get("topic_level"),
            "parent_topic_id": None,
            "sort_order": stg_sort_order_by_id.get(str(stg_id), 0),
        }
        upserts.append(row)

    # De-duplicate any accidental repeated ids (defensive)
    uniq_by_id: Dict[str, Dict[str, Any]] = {}
    for r in upserts:
        rid = str(r.get("id"))
        if not rid:
            continue
        uniq_by_id[rid] = r
    upserts = list(uniq_by_id.values())

    for i in range(0, len(upserts), 1000):
        sb.table("curriculum_topics").upsert(upserts[i : i + 1000], on_conflict="id").execute()

    # Refresh production lookup (need IDs for newly-inserted codes)
    prod_rows2 = (
        sb.table("curriculum_topics")
        .select("id,topic_code")
        .eq("exam_board_subject_id", prod_subject_id)
        .execute()
        .data
        or []
    )
    prod_id_by_code2 = {r.get("topic_code"): r.get("id") for r in prod_rows2 if r.get("topic_code") and r.get("id")}

    # Patch parent_topic_id using mapped IDs.
    stg_code_by_id = {
        str(x.get("id")): x.get("topic_code")
        for x in stg_topics
        if x.get("id") and x.get("topic_code")
    }
    parent_updates = 0
    for t in stg_topics:
        code = t.get("topic_code")
        if not code:
            continue
        parent_stg_id = t.get("parent_topic_id")
        if not parent_stg_id:
            continue
        parent_code = stg_code_by_id.get(str(parent_stg_id))
        if not parent_code:
            continue
        child_prod_id = prod_id_by_code2.get(code)
        parent_prod_id = prod_id_by_code2.get(parent_code)
        if not child_prod_id or not parent_prod_id:
            continue
        sb.table("curriculum_topics").update({"parent_topic_id": parent_prod_id}).eq("id", child_prod_id).execute()
        parent_updates += 1

    print(f"  - parent links updated: {parent_updates}")

    # OPTIONAL SAFE CLEANUP:
    # Remove production topics that are no longer present in staging ONLY if they are not referenced by any flashcards.
    # This avoids leaving stale "old bullet code" nodes visible in the app, while preventing user data breakage.
    stg_codes = {t.get("topic_code") for t in stg_topics if t.get("topic_code")}
    prod_codes = {r.get("topic_code") for r in prod_rows2 if r.get("topic_code")}
    removed_codes = sorted([c for c in prod_codes if c not in stg_codes])
    if removed_codes:
        deleted = 0
        kept = 0
        for code in removed_codes:
            tid = prod_id_by_code2.get(code)
            if not tid:
                continue
            try:
                # If any flashcards reference this topic_id, keep it.
                # NOTE: production schema uses `flashcards.topic_id` (UUID FK) in FLASH.
                fc = sb.table("flashcards").select("id", count="exact").eq("topic_id", tid).execute()
                if int(fc.count or 0) > 0:
                    kept += 1
                    continue
            except Exception:
                # If we cannot verify, be conservative and keep.
                kept += 1
                continue
            sb.table("curriculum_topics").delete().eq("id", tid).execute()
            deleted += 1
        if deleted or kept:
            print(f"  - removed stale prod topics (unreferenced): deleted={deleted} kept(referenced/unknown)={kept}")

    # 5) Generate topic_ai_metadata embeddings for this subject (optional)
    if not args.generate_embeddings:
        print("[5/5] Skipping embeddings (pass --generate-embeddings to enable). Done.")
        return

    print("[5/5] Generating embeddings for this subject...")

    # Query topics_with_context for this subject (filters match the view fields)
    ctx_res = (
        sb.table("topics_with_context")
        .select("topic_id,topic_name,topic_code,topic_level,sort_order,subject_name,exam_board,qualification_level,full_path")
        .eq("exam_board", exam_board)
        .eq("qualification_level", qualification)
        .eq("subject_code", subject_code)
        .order("topic_level")
        .order("sort_order")
        .execute()
    )
    ctx_rows = ctx_res.data or []
    if not ctx_rows:
        die("topics_with_context returned 0 rows for this subject. Is production is_current=true and topics inserted?")

    # Batch embed
    batch_size = max(1, int(args.batch_size))
    total = len(ctx_rows)
    created = 0

    def upsert_topic_ai_metadata_chunk(rows_chunk: List[Dict[str, Any]], chunk_size: int = 25) -> None:
        """
        Supabase/PostgREST can intermittently fail on large payloads (especially embeddings).
        Upsert in small chunks with retries to handle transient network/TLS issues.
        """
        for j in range(0, len(rows_chunk), chunk_size):
            batch = rows_chunk[j : j + chunk_size]
            last_err: Exception | None = None
            for attempt in range(5):
                try:
                    sb.table("topic_ai_metadata").upsert(batch, on_conflict="topic_id").execute()
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    time.sleep(min(8.0, 0.8 * (2**attempt)))
            if last_err:
                raise last_err

    # Pre-clear existing metadata for topics in this subject (defensive)
    # If IDs changed, this ensures no stale rows remain. If IDs are stable, delete is a no-op because topics were deleted.
    topic_ids = [r["topic_id"] for r in ctx_rows]
    for i in range(0, len(topic_ids), 500):
        sb.table("topic_ai_metadata").delete().in_("topic_id", topic_ids[i : i + 500]).execute()

    for i in range(0, total, batch_size):
        chunk = ctx_rows[i : i + batch_size]
        texts = []
        for r in chunk:
            path = " > ".join([p for p in (r.get("full_path") or []) if p])
            # Add code + path context to improve semantic search
            text = f"{r.get('topic_name','')}\nPath: {path}\nCode: {r.get('topic_code','')}"
            texts.append(text)

        vectors = openai_embed(texts)
        upserts = []
        for r, vec in zip(chunk, vectors):
            full_path = r.get("full_path") or []
            summary = r.get("topic_name") or ""
            if args.generate_summaries:
                # slow + cost; do it per topic
                summary = openai_summary(r.get("topic_name") or "", full_path)

            upserts.append(
                {
                    "topic_id": r["topic_id"],
                    "embedding": pgvector_literal(vec),
                    "plain_english_summary": summary,
                    "difficulty_band": "core",
                    "exam_importance": 0.5,
                    "subject_name": r.get("subject_name") or subject_name,
                    "exam_board": r.get("exam_board") or exam_board,
                    "qualification_level": r.get("qualification_level") or qualification,
                    "topic_level": r.get("topic_level"),
                    "full_path": full_path,
                    "is_active": True,
                    "spec_version": "v1",
                }
            )

        # Upsert embeddings in smaller batches to avoid large payload/network issues
        upsert_topic_ai_metadata_chunk(
            upserts,
            chunk_size=min(25, max(5, batch_size // 4)),
        )
        created += len(upserts)
        print(f"  - upserted embeddings: {created}/{total}")
        time.sleep(0.2)

    print("Done")


if __name__ == "__main__":
    main()

