"""
Run WJEC AS/A Level papers scraper for ALL WJEC A-Level subjects currently in staging.

It maps staging subject_name -> WJEC AS/A Level qualification links by scraping:
  https://www.wjec.co.uk/en/qualifications/

Usage:
    PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 python -u scrapers/WJEC/A-Level/papers/run-all-wjec-alevel-papers.py

Optional:
    --limit N
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv
from supabase import create_client


@dataclass(frozen=True)
class QualLink:
    name: str
    link: str


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _canonical_subject(name: str) -> str:
    n = _norm(name)
    n = re.sub(r"^\s*as/a\s*level\s+", "", n)
    n = re.sub(r"^\s*as/a level\s+", "", n)
    n = re.sub(r"^\s*as level\s+", "", n)
    n = re.sub(r"^\s*a level\s+", "", n)
    n = re.sub(r"\(a-level\)", "", n)
    n = re.sub(r"\s*\(a level\)\s*", " ", n)
    n = re.sub(r"\s+", " ", n).strip()

    # Known naming alignment tweaks (staging vs WJEC site)
    if n == "drama":
        n = "drama and theatre"
    if n == "english language and literature":
        n = "english language and literature"
    return n


def fetch_wjec_asa_level_links() -> list[QualLink]:
    url = "https://www.wjec.co.uk/en/qualifications/"
    decoded = html.unescape(requests.get(url, timeout=60).text)

    out: list[QualLink] = []
    # Objects look like:
    # {"name":"AS/A Level Government and Politics", ... "link":"/en/qualifications/government-and-politics-asa-level/", ...}
    for m in re.finditer(r'"name":"AS/A Level\s+([^"]+)"', decoded):
        chunk = decoded[m.start() : m.start() + 900]
        name_m = re.search(r'"name":"AS/A Level\s+([^"]+)"', chunk)
        link_m = re.search(r'"link":"(/en/qualifications/[^"]*asa-level/)"', chunk)
        if not name_m or not link_m:
            continue
        out.append(QualLink(name=name_m.group(1).strip(), link=link_m.group(1).strip()))

    # De-dupe by link
    seen = set()
    deduped: list[QualLink] = []
    for q in out:
        if q.link in seen:
            continue
        seen.add(q.link)
        deduped.append(q)
    return sorted(deduped, key=lambda x: x.link)


def best_match(staging_name: str, candidates: list[QualLink]) -> QualLink | None:
    target = _canonical_subject(staging_name)
    target_tokens = set(target.split())
    if not target_tokens:
        return None

    canon_map = {_canonical_subject(c.name): c for c in candidates}
    if target in canon_map:
        return canon_map[target]

    best: tuple[int, QualLink] | None = None
    for c in candidates:
        cand = _canonical_subject(c.name)
        cand_tokens = set(cand.split())
        score = len(target_tokens & cand_tokens)
        slug = c.link.lower()
        if all(t in slug for t in target_tokens):
            score += 2
        if best is None or score > best[0]:
            best = (score, c)

    # Require >=2 overlap tokens to avoid bad matches
    if not best or best[0] < 2:
        return None
    return best[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
    load_dotenv(env_path)
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    subs = (
        supabase.table("staging_aqa_subjects")
        .select("subject_code,subject_name")
        .eq("exam_board", "WJEC")
        .eq("qualification_type", "A-Level")
        .order("subject_name")
        .execute()
        .data
        or []
    )
    print(f"[INFO] Staging WJEC A-Level subjects: {len(subs)}")

    candidates = fetch_wjec_asa_level_links()
    print(f"[INFO] WJEC site AS/A Level qualification links: {len(candidates)}")

    # Load scraper implementation by file path (A-Level folder uses a hyphen)
    impl_path = Path(__file__).with_name("scrape_wjec_alevel_papers_universal.py")
    spec_impl = importlib.util.spec_from_file_location("scrape_wjec_alevel_papers_universal", impl_path)
    impl_mod = importlib.util.module_from_spec(spec_impl)
    spec_impl.loader.exec_module(impl_mod)
    scrape_wjec_alevel_papers = impl_mod.scrape_wjec_alevel_papers

    # Load uploader helper
    upload_helper_path = Path(
        r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\upload_papers_to_staging.py"
    )
    spec_u = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
    upload_mod = importlib.util.module_from_spec(spec_u)
    spec_u.loader.exec_module(upload_mod)
    upload_papers_to_staging = upload_mod.upload_papers_to_staging

    todo = subs[: args.limit] if args.limit and args.limit > 0 else subs

    ok = 0
    skipped = 0
    failed = 0

    for idx, s in enumerate(todo, start=1):
        code = s["subject_code"]
        name = s["subject_name"]
        match = best_match(name, candidates)
        if not match:
            print(f"[SKIP] {idx}/{len(todo)} {code} :: {name} -> no AS/A Level link match")
            skipped += 1
            continue
        pastpapers_url = "https://www.wjec.co.uk" + match.link + "#tab_pastpapers"
        print(f"\n[RUN] {idx}/{len(todo)} {code} :: {name}")
        print(f"      URL: {pastpapers_url}")
        try:
            sets = scrape_wjec_alevel_papers(code, name, pastpapers_url, headless=True)
            uploaded = upload_papers_to_staging(code, "A-Level", sets, exam_board="WJEC")
            print(f"[OK] Uploaded {uploaded} sets for {code}")
            ok += 1
        except Exception as e:
            print(f"[FAIL] {code} :: {name} -> {e}")
            failed += 1

    print("\n" + "=" * 80)
    print("[DONE] WJEC A-Level papers batch")
    print(f"  ok:      {ok}")
    print(f"  skipped: {skipped}")
    print(f"  failed:  {failed}")


if __name__ == "__main__":
    main()






