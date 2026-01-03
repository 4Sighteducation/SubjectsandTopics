"""
CLI wrapper for the WJEC GCSE universal papers scraper.

Implementation lives in:
  scrapers/WJEC/GCSE/papers/scrape_wjec_gcse_papers_universal.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

from scrapers.WJEC.GCSE.papers.scrape_wjec_gcse_papers_universal import scrape_wjec_gcse_papers

# Import upload helper (kept consistent with existing scrapers)
import importlib.util

upload_helper_path = Path(
    r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\upload_papers_to_staging.py"
)
spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
upload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_module)
upload_papers_to_staging = upload_module.upload_papers_to_staging

def main() -> None:
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    subject_code = sys.argv[1]
    subject_name = sys.argv[2]
    pastpapers_url = sys.argv[3]

    paper_sets = scrape_wjec_gcse_papers(subject_code, subject_name, pastpapers_url, headless=True)
    uploaded = upload_papers_to_staging(subject_code, "GCSE", paper_sets, exam_board="WJEC")
    print(f"\n✅ Uploaded {uploaded} paper sets to staging for {subject_code} (WJEC GCSE)")


if __name__ == "__main__":
    main()


