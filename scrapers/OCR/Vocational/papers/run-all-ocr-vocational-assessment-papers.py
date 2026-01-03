"""
Run OCR Vocational past-paper scraping for ALL Cambridge Technicals + Cambridge Nationals in staging.
===================================================================================================

This script:
1) Reads OCR vocational subjects from staging_aqa_subjects:
   - qualification_type in {CAMBRIDGE_TECHNICALS_L3, CAMBRIDGE_NATIONALS_L2}
2) Discovers each subject's qualification page slug from OCR landing pages:
   - https://www.ocr.org.uk/qualifications/cambridge-technicals/
   - https://www.ocr.org.uk/qualifications/cambridge-nationals/
3) Builds assessment URLs:
   - Technicals:  https://www.ocr.org.uk/qualifications/cambridge-technicals/<slug>/assessment/#level-3
   - Nationals:   https://www.ocr.org.uk/qualifications/cambridge-nationals/<slug>/assessment/
4) Scrapes and uploads paper sets into staging_aqa_exam_papers.

Usage:
  python run-all-ocr-vocational-assessment-papers.py --min-year 2019
  python run-all-ocr-vocational-assessment-papers.py --only CAMBRIDGE_NATIONALS_L2
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client


ROOT = Path(__file__).resolve().parents[4]
ENV_PATH = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")

OCR_BASE = "https://www.ocr.org.uk"
TECH_LANDING = "https://www.ocr.org.uk/qualifications/cambridge-technicals/"
NAT_LANDING = "https://www.ocr.org.uk/qualifications/cambridge-nationals/"


def _norm_key(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\blevel\s*\d.*$", "", s, flags=re.I).strip()
    s = re.sub(r"\b-\s*j\\d+\\b", "", s, flags=re.I).strip()
    return re.sub(r"[^a-z0-9]+", "", s)


def _short_subject_name(staging_subject_name: str) -> str:
    """
    "Cambridge Technicals - Applied Science" -> "Applied Science"
    "Cambridge Nationals - Engineering Design" -> "Engineering Design"
    Be robust to unicode dashes and weird spacing by splitting on the first dash-like separator.
    """
    s = (staging_subject_name or "").strip()
    low = s.lower()
    if low.startswith("cambridge technicals") or low.startswith("cambridge nationals"):
        # split on first dash-like separator
        parts = re.split(r"\s*[-–—]\s*", s, maxsplit=1)
        if len(parts) == 2:
            return parts[1].strip()
        # fallback: remove the prefix words
        s = re.sub(r"^cambridge\\s+(technicals|nationals)\\s*", "", s, flags=re.I).strip()
    return s.strip()


def _fetch_links(url: str, prefix: str) -> Dict[str, str]:
    """
    Returns mapping: norm_key(display_text) -> absolute qualification page URL (endswith /)
    """
    html = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "html.parser")
    out: Dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href.startswith(prefix):
            continue
        text = " ".join(a.get_text(" ", strip=True).split())
        if not text:
            continue
        # ignore misc nav entries
        if "convert raw marks" in text.lower():
            continue
        out[_norm_key(text)] = urljoin(OCR_BASE, href if href.endswith("/") else href + "/")
    return out


def _load_scrape_module():
    # The scraper file name includes hyphens, so import by file path
    target = ROOT / "scrapers" / "OCR" / "Vocational" / "papers" / "scrape-ocr-vocational-assessment-papers.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("ocr_vocational_papers", target)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _load_uploader():
    sys.path.insert(0, str(ROOT))
    import importlib.util

    target = ROOT / "upload_papers_to_staging.py"
    spec = importlib.util.spec_from_file_location("upload_papers_to_staging", target)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.upload_papers_to_staging


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OCR vocational assessment paper scraping for ALL staging subjects")
    parser.add_argument("--min-year", type=int, default=2019)
    parser.add_argument("--only", choices=["CAMBRIDGE_TECHNICALS_L3", "CAMBRIDGE_NATIONALS_L2"])
    parser.add_argument("--limit", type=int, help="Limit number of subjects processed (for testing)")
    args = parser.parse_args()

    load_dotenv(ENV_PATH)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        print("[ERROR] Missing SUPABASE_URL / SUPABASE_SERVICE_KEY")
        return 1
    sb = create_client(url, key)

    # Fetch staging subjects
    q = (
        sb.table("staging_aqa_subjects")
        .select("id,subject_name,subject_code,qualification_type")
        .eq("exam_board", "OCR")
        .in_("qualification_type", ["CAMBRIDGE_TECHNICALS_L3", "CAMBRIDGE_NATIONALS_L2"])
    )
    if args.only:
        q = q.eq("qualification_type", args.only)
    subjects = q.execute().data or []
    subjects.sort(key=lambda s: (s["qualification_type"], s["subject_name"]))
    if args.limit:
        subjects = subjects[: args.limit]

    if not subjects:
        print("[WARN] No OCR vocational subjects found in staging.")
        return 0

    # Build link maps (single fetch each)
    tech_links = _fetch_links(TECH_LANDING, "/qualifications/cambridge-technicals/")
    nat_links = _fetch_links(NAT_LANDING, "/qualifications/cambridge-nationals/")

    scrape_mod = _load_scrape_module()
    upload = _load_uploader()

    ok = 0
    skipped = 0
    failed = 0

    for i, subj in enumerate(subjects, 1):
        qual = subj["qualification_type"]
        short = _short_subject_name(subj["subject_name"])
        keyname = _norm_key(short)

        if qual == "CAMBRIDGE_TECHNICALS_L3":
            base = tech_links.get(keyname)
            if not base:
                print(f"[SKIP] ({i}/{len(subjects)}) No Technicals link match for '{short}'")
                skipped += 1
                continue
            assessment_url = urljoin(base, "assessment/") + "#level-3"
            level = "level-3"
        else:
            base = nat_links.get(keyname)
            if not base:
                print(f"[SKIP] ({i}/{len(subjects)}) No Nationals link match for '{short}'")
                skipped += 1
                continue
            assessment_url = urljoin(base, "assessment/")
            level = "level-2"

        try:
            sets = scrape_mod.scrape_assessment_page(assessment_url=assessment_url, level=level)
            sets = [s for s in sets if s.get("year") and s["year"] >= args.min_year]

            if not sets:
                print(f"[WARN] ({i}/{len(subjects)}) {short} -> 0 sets (leaving existing staging papers untouched)")
                ok += 1
                continue

            uploaded = upload(
                subject_code=subj["subject_code"],
                qualification_type=qual,
                papers_data=sets,
                exam_board="OCR",
            )
            print(f"[OK] ({i}/{len(subjects)}) {short} ({qual}) -> uploaded {uploaded} sets")
            ok += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"[ERROR] ({i}/{len(subjects)}) {short} ({qual}) failed: {e}")
            failed += 1

    print("\n" + "=" * 80)
    print(f"[DONE] subjects={len(subjects)} ok={ok} skipped={skipped} failed={failed}")
    print("=" * 80)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())


