"""
Reconcile staging subjects with "official" subject lists (WJEC + Eduqas markdown).

Goal:
- Make staging subject rows match what the exam board websites list.
- Keep WJEC and EDUQAS as separate entities (even if specs are identical).

Inputs (repo files):
- scrapers/OCR/GCSE/topics/WJEC - ALL.md
- scrapers/Eduqas/A-Level/topics/Eduqas Qualifications - All.md

What this script does:
- Parses BOTH files into expected subject sets per (exam_board, qualification_type).
- Fetches staging_aqa_subjects for the same (board, qual).
- Normalizes subject names to compare reliably (case/spacing/(A-Level) suffix, trailing hyphens).
- Prints:
  - extras in staging (recommend DELETE)
  - missing in staging (recommend SCRAPE/CREATE)
  - SQL to delete extras (topics first, then subjects)

Usage:
  PYTHONIOENCODING=utf-8 python scripts/reconcile_staging_subjects_with_official_lists.py
"""

from __future__ import annotations

import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from supabase import create_client


ROOT = Path(__file__).resolve().parents[1]
WJEC_LIST = ROOT / "scrapers" / "OCR" / "GCSE" / "topics" / "WJEC - ALL.md"
EDUQAS_LIST = ROOT / "scrapers" / "Eduqas" / "A-Level" / "topics" / "Eduqas Qualifications - All.md"

ENV_PATH = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")


@dataclass(frozen=True)
class StagingSubject:
    id: str
    subject_code: str
    subject_name: str
    qualification_type: str
    exam_board: str
    topic_count: int


def norm_name(name: str) -> str:
    s = (name or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*\(A-Level\)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s*\(GCSE\)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s*\(Level 3 Extended Project\)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s*-\s*$", "", s).strip()
    return s.lower()


def load_supabase():
    load_dotenv(ENV_PATH)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_KEY not found in .env")
    return create_client(url, key)


def parse_official_list(path: Path) -> dict[tuple[str, str], set[str]]:
    """
    Return mapping: (board, qualification_type) -> set of normalized subject names
    qualification_type is one of: 'GCSE', 'A-Level'

    The markdown formats are inconsistent; we support the patterns used in both files.
    """
    txt = path.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]

    # Determine board from title lines
    board = "WJEC" if "WJEC" in lines[0].upper() else "EDUQAS"

    current_qual: str | None = None
    out: dict[tuple[str, str], set[str]] = defaultdict(set)

    def set_qual_from_line(line: str) -> str | None:
        up = line.upper()
        if "GCSE" in up and "QUALIFICATIONS" in up:
            return "GCSE"
        if ("ALEVEL" in up or "ALEVEL" in up or "A-LEVEL" in up) and "QUALIFICATIONS" in up:
            return "A-Level"
        if "ALEVEL" == up.strip():
            return "A-Level"
        return None

    # subject line formats (in these files vary a lot):
    #   "Art and Design - GCSE / A"
    #   "Music -GCSE / A"                 (no space)
    #   "Business GCSE / A"               (no dash)
    #   "Drama (and Theatre) = GCSE / A"
    #   "Economics - A"
    #   "Extended Project - Level 3 Extended Project"
    #   "Science" then sub-items etc.
    for ln in lines:
        q = set_qual_from_line(ln)
        if q:
            current_qual = q
            continue
        if ln.startswith("#"):
            continue
        if current_qual is None:
            continue

        # skip section headers like "Science"
        if ln.lower() in {"science"}:
            continue

        # split subject vs qualifier
        subj: str
        qual_part: str

        # 1) Handle explicit separators (allow no-space variants)
        m_sep = re.match(r"^(.*?)\s*(?:=|-)\s*(.+)$", ln)
        if m_sep:
            subj = m_sep.group(1).strip()
            qual_part = m_sep.group(2).strip()
        else:
            # 2) Handle no-dash format like "Business GCSE / A"
            m_tail = re.match(
                r"^(?P<subj>.+?)\s+(?P<qual>GCSE\s*/\s*A|GCSE|A|Level\s+3\s+Extended\s+Project.*|Welsh\s+Baccalaureate.*)$",
                ln,
                flags=re.I,
            )
            if m_tail:
                subj = m_tail.group("subj").strip()
                qual_part = m_tail.group("qual").strip()
            else:
                # raw line with no recognizable qualifier; treat as subject in current section
                subj = ln.strip()
                qual_part = ""

        subj_norm = norm_name(subj)
        qual_part_up = (qual_part or "").upper()

        # Determine whether this subject exists at GCSE and/or A-Level according to the line.
        # NOTE: if we're in the A-Level section, that means "offered at A-Level" even if the line says GCSE / A.
        has_gcse = ("GCSE" in qual_part_up) or current_qual == "GCSE"
        has_alevel = (
            qual_part_up.strip() == "A"
            or "GCSE / A" in qual_part_up
            or "/ A" in qual_part_up
            or current_qual == "A-Level"
        )

        # Handle 'Extended Project' (this is NOT an A-Level; it’s a Level 3 qualification).
        # IMPORTANT: match staging `qualification_type` used by the EPQ scraper.
        if "EXTENDED PROJECT" in qual_part_up or "LEVEL 3 EXTENDED PROJECT" in qual_part_up:
            out[(board, "Level 3 Extended Project")].add(subj_norm)
            continue

        if has_gcse:
            out[(board, "GCSE")].add(subj_norm)
        if has_alevel:
            out[(board, "A-Level")].add(subj_norm)

    return out


def canonical_subject_name(name: str) -> str:
    """
    Canonicalise subject names for comparison, to avoid false "extras" where our DB
    intentionally contains award-variants (single/double) but the official list doesn't.
    """
    n = norm_name(name)

    # Strip common qualifiers that appear in staging but not always in official lists.
    # NOTE: don't use \b around parentheses; it won't match because '(' isn't a "word" char.
    n = re.sub(r"\(\s*single\s+award\s*\)", "", n, flags=re.I).strip()
    n = re.sub(r"\(\s*double\s+award\s*\)", "", n, flags=re.I).strip()
    n = re.sub(r"\(\s*foundation\s*\)", "", n, flags=re.I).strip()
    n = re.sub(r"\(\s*higher\s*\)", "", n, flags=re.I).strip()

    # Collapse common WJEC naming differences
    alias = {
        "the sciences": "integrated science",
        # leave 'science (double award)' as-is; distinct from integrated science in WJEC naming
        "drama": "drama (and theatre)",
        "drama and theatre": "drama (and theatre)",
    }
    if n in alias:
        n = alias[n]

    # Eduqas GCSE Geography naming: official list uses "A Geography"/"B Geography",
    # but we prefer "Geography A"/"Geography B" in staging/UI.
    if n in {"a geography", "geography a"}:
        n = "geography a"
    if n in {"b geography", "geography b"}:
        n = "geography b"

    # Strip trailing duplicated whitespace
    n = re.sub(r"\s+", " ", n).strip()
    return n


def merge_expected(*maps: dict[tuple[str, str], set[str]]) -> dict[tuple[str, str], set[str]]:
    out: dict[tuple[str, str], set[str]] = defaultdict(set)
    for m in maps:
        for k, v in m.items():
            out[k].update(v)
    return out


def fetch_staging_subjects(sb, *, board: str, qual: str) -> list[StagingSubject]:
    subs = (
        sb.table("staging_aqa_subjects")
        .select("id,subject_code,subject_name,qualification_type,exam_board")
        .eq("exam_board", board)
        .eq("qualification_type", qual)
        .execute()
        .data
        or []
    )
    out: list[StagingSubject] = []
    for s in subs:
        cnt = (
            sb.table("staging_aqa_topics")
            .select("id", count="exact")
            .eq("subject_id", s["id"])
            .eq("exam_board", board)
            .execute()
            .count
            or 0
        )
        out.append(
            StagingSubject(
                id=s["id"],
                subject_code=s["subject_code"],
                subject_name=s["subject_name"],
                qualification_type=s["qualification_type"],
                exam_board=s["exam_board"],
                topic_count=int(cnt),
            )
        )
    return out


def main() -> None:
    if not WJEC_LIST.exists():
        raise RuntimeError(f"Missing file: {WJEC_LIST}")
    if not EDUQAS_LIST.exists():
        raise RuntimeError(f"Missing file: {EDUQAS_LIST}")

    expected = merge_expected(parse_official_list(WJEC_LIST), parse_official_list(EDUQAS_LIST))

    sb = load_supabase()

    # We reconcile only boards covered by the lists.
    targets = sorted(expected.keys())

    to_delete_subjects: list[StagingSubject] = []

    print("=" * 90)
    print("RECONCILE STAGING SUBJECTS WITH OFFICIAL LISTS")
    print("=" * 90)
    print(f"WJEC list:   {WJEC_LIST}")
    print(f"Eduqas list: {EDUQAS_LIST}")

    for (board, qual) in targets:
        exp = expected[(board, qual)]
        staging = fetch_staging_subjects(sb, board=board, qual=qual)
        # Compare using canonicalised names (collapses award-variants + known naming deltas)
        exp_canon = {canonical_subject_name(x) for x in exp}

        st_canon: dict[str, list[StagingSubject]] = defaultdict(list)
        for s in staging:
            st_canon[canonical_subject_name(s.subject_name)].append(s)
        st_names = set(st_canon.keys())

        extras = sorted(st_names - exp_canon)
        missing = sorted(exp_canon - st_names)

        print(f"\n## {board} {qual}")
        print(f"- expected subjects: {len(exp)}")
        print(f"- staging subjects:  {len(staging)}")
        print(f"- extras in staging: {len(extras)}")
        print(f"- missing in staging:{len(missing)}")

        if extras:
            print("\n### Extras (recommended DELETE)")
            for n in extras:
                # potentially multiple subjects collapse to the same canonical name; list them all
                for s in sorted(st_canon[n], key=lambda x: (x.subject_name, x.subject_code)):
                    print(f"- {s.subject_name} ({s.subject_code}) topics={s.topic_count} id={s.id}")
                    to_delete_subjects.append(s)

        if missing:
            print("\n### Missing (needs scrape/create)")
            for n in missing:
                print(f"- {n}")

    # De-dupe delete list by subject_id
    uniq: dict[str, StagingSubject] = {s.id: s for s in to_delete_subjects}
    deletions = list(uniq.values())

    print("\n" + "=" * 90)
    print(f"TOTAL SUBJECTS TO DELETE: {len(deletions)}")
    print("=" * 90)

    if deletions:
        ids = [d.id for d in deletions]
        print("\n--- SQL (delete topics first, then subjects) ---\n")
        chunk = 50
        for i in range(0, len(ids), chunk):
            part = ids[i : i + chunk]
            in_list = ", ".join([f"'{x}'" for x in part])
            print(f"delete from staging_aqa_topics where subject_id in ({in_list});")
        print()
        for i in range(0, len(ids), chunk):
            part = ids[i : i + chunk]
            in_list = ", ".join([f"'{x}'" for x in part])
            print(f"delete from staging_aqa_subjects where id in ({in_list});")
    else:
        print("No deletions recommended.")


if __name__ == "__main__":
    main()


