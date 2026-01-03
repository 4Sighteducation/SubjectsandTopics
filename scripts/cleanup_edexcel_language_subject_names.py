#!/usr/bin/env python
"""
Normalize Edexcel A-Level language subject names in staging so they display cleanly in the viewer/app.

Example fix:
  "French (listening,reading and writing) (A-Level)" -> "French (A-Level)"

This script updates ONLY staging_aqa_subjects.subject_name for the language subjects found in:
  scrapers/Edexcel/A-Level/edexcel-alevel-subjects.json

Usage:
  python scripts/cleanup_edexcel_language_subject_names.py --dry-run
  python scripts/cleanup_edexcel_language_subject_names.py --apply
"""

from __future__ import annotations

import argparse
import os
import sys
import io
import json
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


LANGUAGE_NAMES = {
    "Arabic",
    "Chinese",
    "French",
    "German",
    "Greek",
    "Gujarati",
    "Italian",
    "Japanese",
    "Persian",
    "Portuguese",
    "Russian",
    "Spanish",
    "Turkish",
    "Urdu",
}


def main() -> int:
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", default=False)
    ap.add_argument("--apply", action="store_true", default=False)
    args = ap.parse_args()

    if args.apply and args.dry_run:
        print("[ERROR] Use only one of --dry-run or --apply")
        return 2
    if not args.apply and not args.dry_run:
        args.dry_run = True

    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("[ERROR] Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in env")
        return 1

    sb = create_client(url, key)

    cfg_path = repo_root / "scrapers" / "Edexcel" / "A-Level" / "edexcel-alevel-subjects.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    code_to_name = {row["code"]: row["name"] for row in cfg if row.get("name") in LANGUAGE_NAMES}

    print(f"[INFO] Found {len(code_to_name)} language subjects in config")

    changes = []
    for code, base_name in sorted(code_to_name.items()):
        desired = f"{base_name} (A-Level)"

        rows = (
            sb.table("staging_aqa_subjects")
            .select("id, subject_code, subject_name, exam_board, qualification_type")
            .eq("subject_code", code)
            .eq("qualification_type", "A-Level")
            .in_("exam_board", ["EDEXCEL", "Edexcel"])
            .execute()
            .data
            or []
        )
        for r in rows:
            current = (r.get("subject_name") or "").strip()
            if current != desired:
                changes.append((r["id"], code, r.get("exam_board"), current, desired))

    if not changes:
        print("[OK] No subject_name changes needed.")
        return 0

    print(f"[INFO] Planned changes: {len(changes)}")
    for _id, code, board, cur, new in changes[:40]:
        print(f"- {code} [{board}]: {cur} -> {new}")
    if len(changes) > 40:
        print(f"... plus {len(changes)-40} more")

    if args.dry_run:
        print("\n[DRY RUN] No updates applied. Re-run with --apply to make changes.")
        return 0

    # Apply updates
    updated = 0
    for _id, code, board, cur, new in changes:
        sb.table("staging_aqa_subjects").update({"subject_name": new}).eq("id", _id).execute()
        updated += 1

    print(f"\n[OK] Updated {updated} staging_aqa_subjects rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())






