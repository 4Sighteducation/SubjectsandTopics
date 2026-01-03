"""
WJEC GCSE Built Environment (3509) - Topics Scraper (Unit 1 only)

Spec (Version 2 Oct 2021):
  https://www.wjec.co.uk/media/cjlos3v5/wjec-gcse-built-environment-specification-e-20-10-2021.pdf

User requirement:
  - Only Unit 1 is needed (Unit 1 is the on-screen exam).
  - Unit 1 has 8 areas (2.1.1 .. 2.1.8) which are table-structured ("Content Amplification").

Hierarchy we create:
  - L0: Unit 1: Introduction to the built environment
  - L1: 2.1.1 .. 2.1.8 topics
  - L2: Table row headings (a), (b), (c) ...
  - L3: Bullet statements under each row

We intentionally skip the short pre-table bullet list under each topic to avoid duplication with the table.
"""

from __future__ import annotations

import io
import os
import re
import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from pypdf import PdfReader
from supabase import create_client


@dataclass(frozen=True)
class Node:
    code: str
    title: str
    level: int
    parent: Optional[str]


SUBJECT = {
    "name": "Built Environment",
    "code": "WJEC-3509",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/cjlos3v5/wjec-gcse-built-environment-specification-e-20-10-2021.pdf",
}


UNIT_1_TITLE = "Unit 1: Introduction to the built environment"


def _force_utf8_stdio() -> None:
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _looks_like_header_footer(line: str) -> bool:
    s = (line or "").strip()
    if not s:
        return True
    if "WJEC CBAC" in s or "© WJEC" in s:
        return True
    if re.fullmatch(r"\d{1,3}", s):  # page number
        return True
    if s.startswith("GCSE BUILT ENVIRONMENT"):
        return True
    return False


def download_pdf_text(url: str) -> str:
    print("[INFO] Downloading PDF...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    reader = PdfReader(BytesIO(resp.content))
    print(f"[OK] Downloaded {len(reader.pages)} pages")
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def parse_built_environment_unit1(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Locate Unit 1 block: from "2.1 Unit 1" to "2.2 Unit 2"
    # Note: the table of contents includes lines like "2.1 Unit 1 7" (page number).
    # We only want the real section headers (no trailing page number).
    unit1_start_re = re.compile(r"^2\.1\s+Unit\s+1\b(?!\s+\d)", flags=re.IGNORECASE)
    unit2_start_re = re.compile(r"^2\.2\s+Unit\s+2\b(?!\s+\d)", flags=re.IGNORECASE)

    start = None
    end = len(lines)
    # Choose the Unit 1 occurrence inside the actual subject content section.
    for i, raw in enumerate(lines):
        if not unit1_start_re.match(_norm(raw)):
            continue
        window = "\n".join(_norm(x) for x in lines[i : i + 140])
        if "Overview of unit" in window and "Areas of content" in window and "2.1.1" in window:
            start = i
            break
    if start is None:
        raise RuntimeError("Could not locate Unit 1 start (2.1 Unit 1).")
    for j in range(start + 1, len(lines)):
        if unit2_start_re.match(_norm(lines[j])):
            end = j
            break

    block = lines[start:end]

    # Patterns inside Unit 1
    topic_re = re.compile(r"^2\.1\.(\d)\s+(.+)$", flags=re.IGNORECASE)
    content_header_re = re.compile(r"^Content\s+Amplification\s*$", flags=re.IGNORECASE)
    row_re = re.compile(r"^\(([a-z])\)\s*(.+)?$", flags=re.IGNORECASE)
    learners_re = re.compile(r"^Learners should\b", flags=re.IGNORECASE)
    bullet_re = re.compile(r"^[•\u2022]\s*(.+)$")  # bullet char often extracts as \u2022 or similar

    # Stop/escape hatches
    stop_topic_re = re.compile(r"^2\.1\.(\d)\s+", flags=re.IGNORECASE)
    stop_unit_re = unit2_start_re

    nodes: list[Node] = []

    unit_code = "U1"
    nodes.append(Node(code=unit_code, title=UNIT_1_TITLE, level=0, parent=None))

    current_l1_code: Optional[str] = None
    current_l2_code: Optional[str] = None

    in_table = False

    # L2 title assembly (because row labels can wrap across lines)
    pending_row_letter: Optional[str] = None
    pending_row_title_parts: list[str] = []

    # L3 bullet assembly (wrapped lines)
    current_l3_code: Optional[str] = None
    current_l3_parts: list[str] = []
    bullet_idx = 0

    def flush_l3() -> None:
        nonlocal current_l3_code, current_l3_parts
        if current_l2_code and current_l3_code and current_l3_parts:
            title = _norm(" ".join(current_l3_parts))
            if title:
                nodes.append(Node(code=current_l3_code, title=title, level=3, parent=current_l2_code))
        current_l3_code = None
        current_l3_parts = []

    def flush_pending_row_title_if_needed() -> None:
        """If we have a pending (a) title being built, finalize the L2 node now."""
        nonlocal pending_row_letter, pending_row_title_parts, current_l2_code, bullet_idx
        if not current_l1_code or not pending_row_letter:
            return
        title = _norm(" ".join(pending_row_title_parts)) or f"({pending_row_letter})"
        current_l2_code = f"{current_l1_code}_{pending_row_letter.lower()}"
        nodes.append(Node(code=current_l2_code, title=f"({pending_row_letter.lower()}) {title}".strip(), level=2, parent=current_l1_code))
        pending_row_letter = None
        pending_row_title_parts = []
        bullet_idx = 0

    def start_new_row(letter: str, initial: str) -> None:
        nonlocal pending_row_letter, pending_row_title_parts, current_l2_code
        flush_l3()
        # finalize previous pending title (if any) before starting new one
        if pending_row_letter:
            flush_pending_row_title_if_needed()
        current_l2_code = None
        pending_row_letter = letter
        pending_row_title_parts = [initial] if initial else []

    def start_new_topic(topic_num: str, title: str) -> None:
        nonlocal current_l1_code, current_l2_code, in_table, pending_row_letter, pending_row_title_parts, bullet_idx
        flush_l3()
        if pending_row_letter:
            flush_pending_row_title_if_needed()
        in_table = False
        pending_row_letter = None
        pending_row_title_parts = []
        current_l2_code = None
        bullet_idx = 0
        current_l1_code = f"{unit_code}_2_1_{topic_num}"
        nodes.append(Node(code=current_l1_code, title=f"2.1.{topic_num} {title}".strip(), level=1, parent=unit_code))

    i = 0
    while i < len(block):
        s = _norm(block[i])
        if not s or _looks_like_header_footer(s):
            i += 1
            continue

        if stop_unit_re.match(s):
            break

        tm = topic_re.match(s)
        if tm:
            # Topic headings appear twice: once in the "Areas of content" list and once as the real section header.
            # We treat the second appearance as the real header if it is followed soon by content header.
            topic_num, ttitle = tm.group(1), tm.group(2)
            # If we don't yet have this topic, create it; if we do and we're already inside it, ignore duplicates.
            if current_l1_code != f"{unit_code}_2_1_{topic_num}":
                start_new_topic(topic_num, ttitle)
            i += 1
            continue

        if content_header_re.match(s):
            in_table = True
            i += 1
            continue

        # Only parse table rows after the "Content Amplification" header.
        if not in_table:
            i += 1
            continue

        # New row (a), (b), (c) ...
        rm = row_re.match(s)
        if rm:
            letter = rm.group(1)
            rest = _norm(rm.group(2) or "")
            # Sometimes the row header is "(b) Manufacturing Learners should be ..."
            # Split off any trailing "Learners should ..." into content stream by finalizing L2 early.
            if rest and learners_re.search(rest):
                before, after = re.split(r"(?i)\\b(Learners should\\b)", rest, maxsplit=1)
                before = _norm(before)
                start_new_row(letter, before)
                flush_pending_row_title_if_needed()
                # push the "Learners should..." fragment back through the loop as normal content
                block.insert(i + 1, after.strip())
                i += 1
                continue

            start_new_row(letter, rest)
            i += 1
            continue

        # If we're still building the L2 title, keep appending short lines until we hit content.
        if pending_row_letter and not current_l2_code:
            # stop title build on bullets, "Learners should", next row, or next topic
            if bullet_re.match(s) or learners_re.match(s) or row_re.match(s) or stop_topic_re.match(s):
                flush_pending_row_title_if_needed()
                continue
            # otherwise treat this as wrapped title text (often 1-3 words like "structures")
            if len(s) <= 80:
                pending_row_title_parts.append(s)
                i += 1
                continue
            # long line => it's content; finalize title and continue processing as content
            flush_pending_row_title_if_needed()
            continue

        # Ignore the "Learners should know/ be aware..." marker lines
        if learners_re.match(s):
            i += 1
            continue

        # Bullet content => L3
        bm = bullet_re.match(s)
        if bm and current_l2_code:
            flush_l3()
            bullet_idx += 1
            current_l3_code = f"{current_l2_code}_b{bullet_idx:02d}"
            current_l3_parts = [_norm(bm.group(1))] if bm.group(1) else []
            i += 1
            continue

        # Wrapped bullet continuation
        if current_l3_code and current_l3_parts and current_l2_code:
            # stop if we hit a new row/topic
            if row_re.match(s) or topic_re.match(s):
                flush_l3()
                continue
            # join continuation
            current_l3_parts.append(s)
            i += 1
            continue

        i += 1

    flush_l3()
    if pending_row_letter:
        flush_pending_row_title_if_needed()

    # de-dupe by code
    uniq: list[Node] = []
    seen = set()
    for n in nodes:
        if n.code in seen:
            continue
        seen.add(n.code)
        uniq.append(n)

    if not uniq:
        raise RuntimeError("No topics parsed (check PDF extraction / unit detection).")
    return uniq


def upload_to_staging(nodes: list[Node]) -> None:
    env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
    load_dotenv(env_path)
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    subject_result = supabase.table("staging_aqa_subjects").upsert(
        {
            "subject_name": f"{SUBJECT['name']} (GCSE)",
            "subject_code": SUBJECT["code"],
            "qualification_type": "GCSE",
            "specification_url": SUBJECT["pdf_url"],
            "exam_board": SUBJECT["exam_board"],
        },
        on_conflict="subject_code,qualification_type,exam_board",
    ).execute()
    subject_id = subject_result.data[0]["id"]
    print(f"[OK] Subject ID: {subject_id}")

    max_level = max((n.level for n in nodes), default=0)
    deleted_total = 0
    for lvl in range(max_level, -1, -1):
        res = supabase.table("staging_aqa_topics").delete().eq("subject_id", subject_id).eq("topic_level", lvl).execute()
        deleted_total += len(res.data or [])
    print(f"[OK] Cleared old topics ({deleted_total} rows)")

    to_insert = [
        {
            "subject_id": subject_id,
            "topic_code": n.code,
            "topic_name": n.title,
            "topic_level": n.level,
            "exam_board": SUBJECT["exam_board"],
        }
        for n in nodes
    ]
    inserted = supabase.table("staging_aqa_topics").insert(to_insert).execute()
    print(f"[OK] Uploaded {len(inserted.data)} topics")

    code_to_id = {t["topic_code"]: t["id"] for t in inserted.data}
    linked = 0
    for n in nodes:
        if not n.parent:
            continue
        parent_id = code_to_id.get(n.parent)
        child_id = code_to_id.get(n.code)
        if parent_id and child_id:
            supabase.table("staging_aqa_topics").update({"parent_topic_id": parent_id}).eq("id", child_id).execute()
            linked += 1
    print(f"[OK] Linked {linked} relationships")


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC GCSE BUILT ENVIRONMENT (3509) - UNIT 1 TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3509-built-environment-spec.txt")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}")

    nodes = parse_built_environment_unit1(text)
    levels = {}
    for n in nodes:
        levels[n.level] = levels.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(nodes)
    print("\n[OK] WJEC 3509 Built Environment (Unit 1) topics scrape complete.")


if __name__ == "__main__":
    main()


