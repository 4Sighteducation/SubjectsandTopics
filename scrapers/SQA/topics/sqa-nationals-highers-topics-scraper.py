"""
SQA National Qualifications - Topics Scraper (National 5 + Highest Level)
========================================================================

Goal
----
For as many SQA subjects as possible, scrape curriculum TOPICS from the course specification PDFs:
- National 5 (if available)
- Highest available of {Advanced Higher, Higher}

Uploads into staging:
- staging_aqa_subjects (exam_board='SQA', qualification_type in {'National 5','Higher','Advanced Higher'})
- staging_aqa_topics (topic_code/topic_name/topic_level,parent_topic_id, exam_board='SQA')

Approach
--------
1) Discover subjects from: https://www.sqa.org.uk/sqa/45625.html
2) For each subject, determine the N5 + highest level tabs
3) Visit each level page and expand the "Course Specification" accordion to obtain the spec PDF link
4) Download PDF, extract text (pdfplumber), send to AI to produce numbered hierarchy, parse + upload
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


ROOT = __import__("pathlib").Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scrapers.CCEA.ccea_common import (  # noqa: E402
    call_ai,
    download_pdf,
    extract_pdf_text,
    load_supabase,
    parse_numbered_hierarchy,
    replace_subject_topics,
    resolve_ai_provider,
    slice_relevant_text,
    slugify_code,
    upsert_staging_subject,
)


SQA_BASE = "https://www.sqa.org.uk"
SQA_SUBJECT_INDEX = f"{SQA_BASE}/sqa/45625.html"

EXAM_BOARD = "SQA"
LEVEL_ORDER = ["National 5", "Higher", "Advanced Higher"]


@dataclass(frozen=True)
class SQASubject:
    name: str
    subject_url: str


def _norm_url(u: str, base: str) -> str:
    u = (u or "").strip()
    if not u:
        return u
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return urljoin(base, u)
    if u.startswith("http"):
        return u
    return urljoin(base, u)


def load_subjects_from_index() -> List[SQASubject]:
    r = requests.get(SQA_SUBJECT_INDEX, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    main = soup.find("main") or soup

    out: List[SQASubject] = []
    seen: set[str] = set()
    for a in main.find_all("a", href=True):
        name = " ".join(a.get_text(" ", strip=True).split())
        href = (a.get("href") or "").strip()
        if not name or not href:
            continue
        if not (
            re.fullmatch(r"\d+\.html", href)
            or re.search(r"/sqa/\d+\.html", href)
            or re.search(r"/\d+\.html", href)
        ):
            continue
        url = _norm_url(href, SQA_SUBJECT_INDEX)  # relative links are relative to /sqa/
        if url in seen:
            continue
        seen.add(url)
        out.append(SQASubject(name=name, subject_url=url))

    # Optional: restrict to the giant "Select subject" dropdown, if present.
    for sel in soup.find_all("select"):
        options = {" ".join(o.get_text(" ", strip=True).split()) for o in sel.find_all("option")}
        options = {o for o in options if o and o.lower() not in {"select subject", "select your subject"}}
        if len(options) >= 30 and ("Accounting" in options or "Biology" in options):
            out = [s for s in out if s.name in options]
            break

    out.sort(key=lambda s: s.name.lower())
    return out


def init_driver(*, headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,900")
    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(10)
    return driver


def _extract_level_links(subject_html: str, subject_url: str) -> Dict[str, str]:
    soup = BeautifulSoup(subject_html, "html.parser")
    links: Dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text(" ", strip=True).split())
        if not text:
            continue
        if text not in {"National 3", "National 4", "National 5", "Higher", "Adv Higher", "Advanced Higher"}:
            continue
        href = _norm_url(a["href"], subject_url)
        label = "Advanced Higher" if text == "Adv Higher" else text
        links[label] = href
    return links


def choose_target_levels(level_links: Dict[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if "National 5" in level_links:
        out["National 5"] = level_links["National 5"]
    if "Advanced Higher" in level_links:
        out["Advanced Higher"] = level_links["Advanced Higher"]
    elif "Higher" in level_links:
        out["Higher"] = level_links["Higher"]
    return out


def _click_expand_accordion(driver: webdriver.Chrome, title_text: str) -> None:
    xpaths = [
        f"//*[self::button or self::a or self::div][contains(normalize-space(.), '{title_text}')]",
    ]
    for xp in xpaths:
        els = driver.find_elements(By.XPATH, xp)
        if not els:
            continue
        el = els[0]
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", el)
            time.sleep(1.2)
            return
        except Exception:
            continue


def _parse_spec_pdf_from_level_page(html: str, base_url: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = " ".join(a.get_text(" ", strip=True).split()).lower()
        if ".pdf" not in href.lower():
            continue
        if "course specification" in text or "course-spec" in href.lower() or "course_spec" in href.lower():
            candidates.append(_norm_url(href, base_url))
    return candidates[0] if candidates else None


def scrape_spec_pdf_url(driver: webdriver.Chrome, level_url: str) -> Optional[str]:
    driver.get(level_url)
    time.sleep(0.8)
    _click_expand_accordion(driver, "Course Specification")
    time.sleep(0.8)
    html = driver.page_source
    return _parse_spec_pdf_from_level_page(html, level_url)


def _build_prompt(*, subject_name: str, level_name: str, text: str) -> str:
    return f"""
You are extracting curriculum topics for the SQA {level_name} course specification: "{subject_name}".

Return ONLY a numbered hierarchy (no preamble, no markdown).

Rules:
- Use strict numbering with dots:
  1. <Level 0 title>
  1.1 <Level 1 title>
  1.1.1 <Level 2 title>
  1.1.1.1 <Level 3 title>
  1.1.1.1.1 <Level 4 title>  (only if needed)
- Prefer the spec's own structure (Units / Topics / Key Areas / Mandatory course content).
- Capture learning outcome bullets / "skills, knowledge and understanding" bullets as Level 3/4.
- Keep titles short and curriculum-focused (no page numbers, no admin).
- IGNORE assessment admin, coursework admin, grade boundaries, general course assessment tables, appendices.

Input text (extracted from PDF):
---
{text}
---
""".strip()


def scrape_one(subject: SQASubject, *, level_name: str, level_url: str, driver, provider: str, client) -> int:
    sb = load_supabase()
    subject_code = f"SQA-{slugify_code(level_name)}-{slugify_code(subject.name)}"

    spec_url = scrape_spec_pdf_url(driver, level_url)
    if not spec_url:
        raise RuntimeError(f"Spec PDF not found on level page: {level_url}")

    subject_id = upsert_staging_subject(
        sb,
        exam_board=EXAM_BOARD,
        qualification_type=level_name,
        subject_name=subject.name,
        subject_code=subject_code,
        specification_url=spec_url,
    )

    pdf = download_pdf(spec_url)
    full_text = extract_pdf_text(pdf)
    full_text = (
        (full_text or "")
        .replace("\uf0b7", "• ")
        .replace("●", "• ")
        .replace("•", "\n- ")
    )
    window = slice_relevant_text(
        full_text,
        keywords=[
            "course content",
            "mandatory course",
            "course outline",
            "key areas",
            "skills, knowledge",
            "knowledge and understanding",
            "unit",
            "topic",
        ],
        max_chars=240_000,
    )
    hierarchy = call_ai(provider, client, prompt=_build_prompt(subject_name=subject.name, level_name=level_name, text=window), max_tokens=14000)
    parsed = parse_numbered_hierarchy(hierarchy, code_prefix=subject_code, base_parent_code=None, level_offset=0, level_cap=4)
    count = replace_subject_topics(sb, subject_id=subject_id, exam_board=EXAM_BOARD, topics=parsed, batch_size=500)
    print(f"[OK] {subject.name} ({level_name}): topics={count}")
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", help="Filter subject by name (partial match)")
    parser.add_argument("--limit-subjects", type=int)
    parser.add_argument("--dry-run", action="store_true", help="Do not write to staging (just validate PDF discovery)")
    parser.add_argument("--headless", action="store_true", help="Run Chrome headless (default)")
    parser.add_argument("--no-headless", action="store_true", help="Run Chrome visible")
    args = parser.parse_args()

    headless = True
    if args.no_headless:
        headless = False

    subjects = load_subjects_from_index()
    if args.subject:
        subjects = [s for s in subjects if args.subject.lower() in s.name.lower()]
    if args.limit_subjects:
        subjects = subjects[: args.limit_subjects]
    if not subjects:
        print("[WARN] No subjects matched.")
        return 0

    provider, client = resolve_ai_provider()
    driver = init_driver(headless=headless)

    ok = 0
    skipped = 0
    failed = 0
    try:
        for subj in subjects:
            try:
                r = requests.get(subj.subject_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
                r.raise_for_status()
                level_links = _extract_level_links(r.text, subj.subject_url)
                targets = choose_target_levels(level_links)
                if not targets:
                    print(f"[SKIP] {subj.name}: no National 5 / Higher / Advanced Higher tabs found")
                    skipped += 1
                    continue

                for level in LEVEL_ORDER:
                    if level not in targets:
                        continue
                    level_url = targets[level]
                    if args.dry_run:
                        spec_url = scrape_spec_pdf_url(driver, level_url)
                        print(f"[DRY] {subj.name} ({level}): spec={'yes' if spec_url else 'no'}")
                        continue
                    scrape_one(subj, level_name=level, level_url=level_url, driver=driver, provider=provider, client=client)
                    time.sleep(0.5)

                ok += 1
            except Exception as e:
                failed += 1
                print(f"[ERROR] {subj.name}: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    print(f"[DONE] ok={ok} skipped={skipped} failed={failed} total={len(subjects)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())


