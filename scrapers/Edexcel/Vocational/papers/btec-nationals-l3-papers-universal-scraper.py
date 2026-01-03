"""
Edexcel (Pearson) BTEC Nationals Level 3 - External Assessment Papers Scraper
=============================================================================

Goal:
- For each BTEC Nationals L3 subject already scraped into staging (topics),
  scrape Pearson "Course materials" -> "External assessments" resources.
- Extract ONLY:
  - Question papers
  - Mark schemes
  - Examiner reports
- Ignore:
  - Set tasks / externally set task
  - Admin/support guides
  - Secure tests / locked resources (typically not public PDF URLs)

Uploads to staging:
- staging_aqa_exam_papers via upload_papers_to_staging()
- exam_board='EDEXCEL'
- qualification_type='BTEC_NATIONALS_L3'

Notes:
- Pearson course materials pages are JS-rendered, so we use Selenium.
- We resolve course materials URL by guessing slug+year from subject_name + spec_url hints.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[4]
ENV_PATH = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")

QUAL_BASE_BTEC_NATIONALS = "https://qualifications.pearson.com/en/qualifications/btec-nationals"
QUAL_BASE_BTEC_AAQS = "https://qualifications.pearson.com/en/qualifications/btec-aaqs"
EXAM_BOARD = "EDEXCEL"
QUAL_TYPE = "BTEC_NATIONALS_L3"


def _slugify_hyphen(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[’']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def _extract_year_hints(spec_url: str) -> List[int]:
    if not spec_url:
        return []
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", spec_url)]
    # de-dupe preserving order
    out: List[int] = []
    seen = set()
    for y in years:
        if y not in seen:
            out.append(y)
            seen.add(y)
    return out


def resolve_course_materials_url(subject_name: str, spec_url: str) -> Optional[str]:
    """
    Guess course materials URL:
      https://qualifications.pearson.com/en/qualifications/btec-nationals/<slug>-<year>.coursematerials.html
    We try a set of year candidates and pick first that returns HTTP 200.
    """
    # If we already have a Pearson qualification page URL, derive directly.
    if spec_url and "qualifications.pearson.com/en/qualifications/" in spec_url:
        if spec_url.endswith(".coursematerials.html"):
            return spec_url.split("#", 1)[0]
        if spec_url.endswith(".html"):
            return spec_url.split("#", 1)[0].replace(".html", ".coursematerials.html")

    # Base path depends on qualification family (Medical Science in your list is BTEC AAQs)
    base = QUAL_BASE_BTEC_NATIONALS
    if spec_url and "btec-aaqs" in spec_url.lower():
        base = QUAL_BASE_BTEC_AAQS

    slug = _slugify_hyphen(subject_name)
    year_candidates: List[int] = []
    year_candidates.extend(_extract_year_hints(spec_url))
    # common cohorts (and older ones) – we brute-force years for reliability
    year_candidates.extend(list(range(2010, 2026)))
    # de-dupe
    uniq_years: List[int] = []
    seen = set()
    for y in year_candidates:
        if y not in seen:
            uniq_years.append(y)
            seen.add(y)

    for y in uniq_years:
        url = f"{base}/{slug}-{y}.coursematerials.html"
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                continue
            # basic sanity: must look like a course materials page
            if "Page not found" in r.text or "page not found" in r.text.lower():
                continue
            if "Course materials" not in r.text and "course materials" not in r.text.lower():
                continue
            return url
        except Exception:
            continue

    # Some qualifications use non-year slugs (e.g. applied-human-biology.coursematerials.html)
    try:
        url = f"{base}/{slug}.coursematerials.html"
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and ("page not found" not in r.text.lower()) and ("course materials" in r.text.lower()):
            return url
    except Exception:
        pass
    return None


def _algolia_query(app_id: str, api_key: str, index: str, *, query: str = "", filters: str = "", facets: Optional[List[str]] = None, page: int = 0, hits_per_page: int = 1000) -> Dict:
    url = f"https://{app_id}-dsn.algolia.net/1/indexes/{index}/query"
    headers = {
        "X-Algolia-API-Key": api_key,
        "X-Algolia-Application-Id": app_id,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    body: Dict = {
        "query": query,
        "filters": filters,
        "page": page,
        "hitsPerPage": hits_per_page,
    }
    if facets:
        body["facets"] = facets
    r = requests.post(url, json=body, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()


def _extract_algolia_config(soup: BeautifulSoup) -> Tuple[str, str, str]:
    api_key = soup.select_one(".algoliaAPIKey")
    app_id = soup.select_one(".algoliaAppId")
    index = soup.select_one(".algoliaIndexName")
    if not api_key or not app_id or not index:
        raise RuntimeError("Algolia config not found in course materials page")
    return (app_id.get("value") or "", api_key.get("value") or "", index.get("value") or "")


def _build_base_filters_from_page(soup: BeautifulSoup) -> str:
    vals: List[str] = []
    for inp in soup.find_all("input", attrs={"name": "filterQuery"}):
        v = (inp.get("value") or "").strip()
        if not v:
            continue
        if v.lower().startswith("category:"):
            v = v.split(":", 1)[1]
        # IMPORTANT:
        # Many External-assessments assets are not consistently tagged with Specification-Code facets.
        # Using spec-code filters can accidentally exclude legitimate papers (seen on Agriculture).
        # We scope primarily by family + subject, then post-filter by folder in the URL.
        if "Qualification-Family/" not in v and "Qualification-Subject/" not in v:
            continue
        vals.append(v)
    uniq = sorted(set(vals))
    return " AND ".join([f'category:\"{v}\"' for v in uniq])


def _discover_external_assessments_facet(app_id: str, api_key: str, index: str, *, base_filters: str) -> Optional[str]:
    # Ask for category facets in the current qualification scope, then pick the one for external assessments
    data = _algolia_query(app_id, api_key, index, filters=base_filters, facets=["category"], hits_per_page=0, page=0)
    cat = (data.get("facets") or {}).get("category") or {}
    # Prefer exact match if present
    for k in cat.keys():
        if k.lower() == "pearson-uk:category/external-assessments":
            return k
    # Otherwise fuzzy match
    for k in cat.keys():
        low = k.lower()
        if "pearson-uk:category/" in low and "external" in low and "assess" in low:
            return k
    return None


def _pick_subject_folder_hint(spec_url: str, subject_name: str) -> Optional[str]:
    """
    Prefer folder name from spec_url: /content/dam/pdf/BTEC-Nationals/<Folder>/
    """
    m = re.search(r"/BTEC-Nationals/([^/]+)/", spec_url or "", flags=re.I)
    if m:
        return m.group(1)
    # fallback: slug-ish tokens
    return _slugify_hyphen(subject_name).replace("-", " ")


def _category_value(hit: Dict, prefix: str) -> Optional[str]:
    cats = hit.get("category") or []
    for c in cats:
        if isinstance(c, str) and c.startswith(prefix):
            return c
    return None


def scrape_external_assessments_via_algolia(
    *,
    course_materials_url: str,
    subject_folder_hint: Optional[str],
    min_year: int,
) -> List[Dict]:
    """
    Returns list of grouped paper sets:
      {year, exam_series, paper_number, component_code, question_paper_url, mark_scheme_url, examiner_report_url}
    """
    html = requests.get(course_materials_url, timeout=60, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "html.parser")
    app_id, api_key, index = _extract_algolia_config(soup)
    base_filters = _build_base_filters_from_page(soup)
    ext_facet = _discover_external_assessments_facet(app_id, api_key, index, base_filters=base_filters)
    if not ext_facet:
        return []
    filters = f'{base_filters} AND category:\"{ext_facet}\"'

    # paginate
    page = 0
    hits: List[Dict] = []
    while True:
        data = _algolia_query(app_id, api_key, index, filters=filters, page=page, hits_per_page=1000)
        hits.extend(data.get("hits") or [])
        nb_pages = int(data.get("nbPages") or 0)
        page += 1
        if page >= nb_pages:
            break

    grouped: Dict[Tuple[int, str, int], Dict] = {}

    folder_token = (subject_folder_hint or "").lower().strip()

    for hit in hits:
        url = hit.get("url") or ""
        title = hit.get("title") or ""
        doc_type = _category_value(hit, "Pearson-UK:Document-Type/")
        unit_tag = _category_value(hit, "Pearson-UK:Unit/")
        series_tag = _category_value(hit, "Pearson-UK:Exam-Series/")

        if not url or "/content/dam/" not in url.lower() or "/pdf/" not in url.lower():
            continue

        abs_url = url if url.startswith("http") else "https://qualifications.pearson.com" + url

        # Filter to this subject's folder when possible (prevents cross-tagging bleed)
        if folder_token:
            if folder_token.startswith("/"):
                if folder_token not in abs_url.lower():
                    continue
            else:
                # folder names from /BTEC-Nationals/<Folder>/ are case-sensitive-ish, but we compare lowercased
                if f"/btec-nationals/{folder_token.lower()}/" not in abs_url.lower():
                    # If we only have a weak word-hint fallback, don't over-filter.
                    pass

        if not doc_type:
            continue
        dt = doc_type.split("/", 1)[1].lower()
        # Ignore set tasks / admin/support / modified
        if "set-task" in dt or "set task" in dt or "administrative" in dt or "support" in dt or "modified" in dt:
            continue
        if ("question" in dt and "paper" in dt) or dt in {"que", "qp", "question-paper"}:
            kind = "question_paper"
        elif ("mark" in dt and "scheme" in dt) or dt in {"rms", "mark-scheme"}:
            kind = "mark_scheme"
        elif ("examiner" in dt and "report" in dt) or dt in {"pef", "examiner-report"}:
            kind = "examiner_report"
        else:
            continue

        if not unit_tag:
            # fallback from title
            m = re.search(r"\bUnit\s+(\d{1,2})\b", title, flags=re.I)
            unit_num = int(m.group(1)) if m else None
        else:
            m = re.search(r"Unit-(\d{1,2})", unit_tag)
            unit_num = int(m.group(1)) if m else None
        if unit_num is None:
            continue

        if not series_tag:
            # fallback from title like "June 2023"
            m = re.search(r"\b(January|June|November|October|May)\s+(20\d{2})\b", title, flags=re.I)
            if not m:
                continue
            series = m.group(1).title()
            year = int(m.group(2))
        else:
            # Exam-Series/January-2022
            tail = series_tag.split("/", 1)[1]
            m = re.match(r"([A-Za-z]+)-(\d{4})", tail)
            if not m:
                continue
            series = m.group(1).title()
            year = int(m.group(2))

        if year < min_year:
            continue

        key = (year, series, unit_num)
        if key not in grouped:
            grouped[key] = {
                "year": year,
                "exam_series": series,
                "paper_number": unit_num,
                "component_code": f"U{unit_num:02d}",
                "tier": None,
                "question_paper_url": None,
                "mark_scheme_url": None,
                "examiner_report_url": None,
            }

        if kind == "question_paper":
            grouped[key]["question_paper_url"] = abs_url
        elif kind == "mark_scheme":
            grouped[key]["mark_scheme_url"] = abs_url
        elif kind == "examiner_report":
            grouped[key]["examiner_report_url"] = abs_url

    return [v for v in grouped.values() if v.get("question_paper_url")]


def main() -> int:
    parser = argparse.ArgumentParser(description="BTEC Nationals L3 External Assessment Papers Scraper (Pearson)")
    parser.add_argument("--min-year", type=int, default=2023)
    parser.add_argument("--subject", help="Filter subject by name (partial match)")
    parser.add_argument("--limit-subjects", type=int)
    args = parser.parse_args()

    load_dotenv(ENV_PATH)
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_key:
        print("[ERROR] Missing SUPABASE_URL / SUPABASE_SERVICE_KEY")
        return 1

    # Import uploader
    sys.path.insert(0, str(ROOT))
    import importlib.util

    upload_path = ROOT / "upload_papers_to_staging.py"
    spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    upload_papers_to_staging = mod.upload_papers_to_staging

    from supabase import create_client

    sb = create_client(supabase_url, supabase_key)

    q = (
        sb.table("staging_aqa_subjects")
        .select("subject_code,subject_name,specification_url")
        .eq("exam_board", EXAM_BOARD)
        .eq("qualification_type", QUAL_TYPE)
    )
    subjects = q.execute().data or []
    subjects.sort(key=lambda r: r["subject_name"].lower())
    if args.subject:
        subjects = [s for s in subjects if args.subject.lower() in s["subject_name"].lower()]
    if args.limit_subjects:
        subjects = subjects[: args.limit_subjects]

    if not subjects:
        print("[WARN] No BTEC subjects found in staging to scrape papers for.")
        return 0

    ok = 0
    skipped = 0
    failed = 0

    for i, s in enumerate(subjects, 1):
        subj_name = (s["subject_name"] or "").replace("BTEC Nationals -", "").strip()
        spec_url = s.get("specification_url") or ""
        cm_url = resolve_course_materials_url(subj_name, spec_url)
        if not cm_url:
            print(f"[SKIP] ({i}/{len(subjects)}) {subj_name}: could not resolve course materials URL")
            skipped += 1
            continue

        try:
            folder_hint = _pick_subject_folder_hint(spec_url, subj_name)
            sets = scrape_external_assessments_via_algolia(
                course_materials_url=cm_url,
                subject_folder_hint=folder_hint,
                min_year=args.min_year,
            )
            if not sets:
                print(f"[WARN] ({i}/{len(subjects)}) {subj_name}: 0 sets found")
                ok += 1
                continue
            uploaded = upload_papers_to_staging(
                subject_code=s["subject_code"],
                qualification_type=QUAL_TYPE,
                papers_data=sets,
                exam_board=EXAM_BOARD,
            )
            print(f"[OK] ({i}/{len(subjects)}) {subj_name}: uploaded {uploaded} paper sets")
            ok += 1
            time.sleep(0.6)
        except Exception as e:
            print(f"[ERROR] ({i}/{len(subjects)}) {subj_name} failed: {e}")
            failed += 1

    print(f"[DONE] ok={ok} skipped={skipped} failed={failed} total={len(subjects)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())


