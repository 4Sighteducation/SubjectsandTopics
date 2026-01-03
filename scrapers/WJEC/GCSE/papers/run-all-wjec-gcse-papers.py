"""
Run WJEC GCSE papers scraper for ALL WJEC GCSE subjects currently in staging.

Strategy:
  1) Query Supabase staging_aqa_subjects for (exam_board='WJEC', qualification_type='GCSE').
  2) Fetch https://www.wjec.co.uk/en/qualifications/ and extract GCSE qualification links.
     The page embeds a large JSON-ish dataset with objects like:
        {"name":"GCSE Business ","link":"/en/qualifications/business-gcse/", ...}
  3) Match staging subject_name to a qualification link (best-effort canonical match).
  4) For each match, run the universal scraper on <link>#tab_pastpapers and upload to staging.

Usage:
    PYTHONIOENCODING=utf-8 python scrapers/WJEC/GCSE/papers/run-all-wjec-gcse-papers.py

Optional:
    --limit N   (only process first N subjects)
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv
from supabase import create_client

# Ensure repo root is on sys.path so `import scrapers...` works when running as a script
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

# Local imports
from scrapers.WJEC.GCSE.papers.scrape_wjec_gcse_papers_universal import scrape_wjec_gcse_papers

import importlib.util

upload_helper_path = Path(
    r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\upload_papers_to_staging.py"
)
spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
upload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_module)
upload_papers_to_staging = upload_module.upload_papers_to_staging


@dataclass(frozen=True)
class QualLink:
    name: str
    link: str


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\(gcse\)", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _canonical_subject(name: str) -> str:
    n = _norm(name)
    n = re.sub(r"^gcse\s+", "", n)
    # Strip award qualifiers that don't appear in WJEC site names consistently
    n = re.sub(r"\b\(single award\)\b", "", n)
    n = re.sub(r"\b\(double award\)\b", "", n)
    n = re.sub(r"\b\(short course\)\b", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def fetch_wjec_gcse_links() -> list[QualLink]:
    url = "https://www.wjec.co.uk/en/qualifications/"
    html_text = requests.get(url, timeout=60).text
    decoded = html.unescape(html_text)

    # Extract GCSE objects from the embedded data:
    # ... "name":"GCSE Business ", ... "link":"/en/qualifications/business-gcse/", ...
    out: list[QualLink] = []
    for m in re.finditer(r'"name":"GCSE\s+([^"]+)"', decoded):
        chunk = decoded[m.start() : m.start() + 900]
        name_m = re.search(r'"name":"GCSE\s+([^"]+)"', chunk)
        link_m = re.search(r'"link":"(/en/qualifications/[^"]+/)"', chunk)
        if not name_m or not link_m:
            continue
        name = name_m.group(1).strip()
        link = link_m.group(1).strip()
        out.append(QualLink(name=name, link=link))

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

    # First try exact canonical match on candidate name
    canon_map = {_canonical_subject(c.name): c for c in candidates}
    if target in canon_map:
        return canon_map[target]

    best: tuple[int, QualLink] | None = None
    for c in candidates:
        cand = _canonical_subject(c.name)
        cand_tokens = set(cand.split())
        score = len(target_tokens & cand_tokens)
        # small boost if the slug contains all tokens (approx)
        slug = c.link.lower()
        if all(t in slug for t in target_tokens):
            score += 2
        if best is None or score > best[0]:
            best = (score, c)
    # Require at least 2 overlapping tokens to avoid bad matches like "science" -> "computer science"
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
        .eq("qualification_type", "GCSE")
        .order("subject_name")
        .execute()
        .data
        or []
    )

    print(f"[INFO] Staging WJEC GCSE subjects: {len(subs)}")

    candidates = fetch_wjec_gcse_links()
    print(f"[INFO] WJEC site GCSE qualification links: {len(candidates)}")

    todo = subs[: args.limit] if args.limit and args.limit > 0 else subs

    ok = 0
    skipped = 0
    failed = 0

    for idx, s in enumerate(todo, start=1):
        code = s["subject_code"]
        name = s["subject_name"]
        match = best_match(name, candidates)
        if not match:
            print(f"[SKIP] {idx}/{len(todo)} {code} :: {name} -> no GCSE link match")
            skipped += 1
            continue
        pastpapers_url = "https://www.wjec.co.uk" + match.link + "#tab_pastpapers"
        print(f"\n[RUN] {idx}/{len(todo)} {code} :: {name}")
        print(f"      URL: {pastpapers_url}")
        try:
            sets = scrape_wjec_gcse_papers(code, name, pastpapers_url, headless=True)
            uploaded = upload_papers_to_staging(code, "GCSE", sets, exam_board="WJEC")
            print(f"[OK] Uploaded {uploaded} sets for {code}")
            ok += 1
        except Exception as e:
            print(f"[FAIL] {code} :: {name} -> {e}")
            failed += 1

    print("\n" + "=" * 80)
    print("[DONE] WJEC GCSE papers batch")
    print(f"  ok:      {ok}")
    print(f"  skipped: {skipped}")
    print(f"  failed:  {failed}")


if __name__ == "__main__":
    main()


