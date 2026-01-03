"""
CLI wrapper for the WJEC A-Level universal papers scraper.

Usage:
    PYTHONIOENCODING=utf-8 python scrapers/WJEC/A-Level/papers/scrape-wjec-alevel-papers-universal.py <subject_code> "<subject_name>" "<pastpapers_tab_url>"
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

# Load the implementation module by file path (A-Level has a hyphen in the folder name)
import importlib.util  # noqa: E402

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

impl_path = Path(__file__).with_name("scrape_wjec_alevel_papers_universal.py")
spec_impl = importlib.util.spec_from_file_location("scrape_wjec_alevel_papers_universal", impl_path)
impl_mod = importlib.util.module_from_spec(spec_impl)
spec_impl.loader.exec_module(impl_mod)
scrape_wjec_alevel_papers = impl_mod.scrape_wjec_alevel_papers

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
        raise SystemExit(1)

    subject_code = sys.argv[1]
    subject_name = sys.argv[2]
    pastpapers_url = sys.argv[3]

    paper_sets = scrape_wjec_alevel_papers(subject_code, subject_name, pastpapers_url, headless=True)
    uploaded = upload_papers_to_staging(subject_code, "A-Level", paper_sets, exam_board="WJEC")
    print(f"\n✅ Uploaded {uploaded} paper sets to staging for {subject_code} (WJEC A-Level)")


if __name__ == "__main__":
    main()


