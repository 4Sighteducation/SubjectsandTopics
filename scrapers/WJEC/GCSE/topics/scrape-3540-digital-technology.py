"""
WJEC GCSE Digital Technology (3540) - Topics Scraper (Unit 1 only)

Spec (For teaching from 2021 / award from 2023):
  https://www.wjec.co.uk/media/y14f1jvq/wjec-gcse-digital-technology-specification-e-20-08-2020.pdf

User requirement:
  - Only Unit 1 (exam): The digital world
  - L1: 2.1.1 .. 2.1.6
  - Include the short "In this section learners will gain knowledge..." bullets (as L2)
  - Parse the Content/Amplification table:
      - L2: (a)/(b)/(c)... row titles from the Content column
      - L3: "Learners should ..." headings within the Amplification column
      - L4+: bullet statements, with simple nesting when a bullet introduces a list (ends with ':')
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
    "name": "Digital Technology",
    "code": "WJEC-3540",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/y14f1jvq/wjec-gcse-digital-technology-specification-e-20-08-2020.pdf",
}


UNIT_1_TITLE = "Unit 1: The digital world"


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
    if s.startswith("GCSE DIGITAL TECHNOLOGY"):
        return True
    return False


def download_pdf_text(url: str) -> str:
    print("[INFO] Downloading PDF...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    reader = PdfReader(BytesIO(resp.content))
    print(f"[OK] Downloaded {len(reader.pages)} pages")
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def parse_digital_technology_unit1(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Locate Unit 1 block inside subject content (avoid TOC line "2.1 Unit 1 6")
    unit1_re = re.compile(r"^2\.1\s+Unit\s+1\b(?!\s+\d)", flags=re.IGNORECASE)
    unit2_re = re.compile(r"^2\.2\s+Unit\s+2\b(?!\s+\d)", flags=re.IGNORECASE)

    start = None
    for i, raw in enumerate(lines):
        s = _norm(raw)
        if not unit1_re.match(s):
            continue
        window = "\n".join(_norm(x) for x in lines[i : i + 160])
        if "Areas of content" in window and "2.1.1 Data" in window and "Content Amplification" in window:
            start = i
            break
    if start is None:
        raise RuntimeError("Could not locate Unit 1 start (2.1 Unit 1).")

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if unit2_re.match(_norm(lines[j])):
            end = j
            break

    block = lines[start:end]

    # Patterns
    l1_re = re.compile(r"^2\.1\.(\d)\s+(.+)$", flags=re.IGNORECASE)
    content_amp_re = re.compile(r"^Content\s+Amplification\s*$", flags=re.IGNORECASE)
    row_re = re.compile(r"^\(([a-z])\)\s*(.+)?$", flags=re.IGNORECASE)
    learners_re = re.compile(r"^Learners should\b", flags=re.IGNORECASE)
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7�]\s*(.+)$")

    nodes: list[Node] = []
    unit_code = "U1"
    nodes.append(Node(code=unit_code, title=UNIT_1_TITLE, level=0, parent=None))

    current_l1_code: Optional[str] = None
    current_row_code: Optional[str] = None  # L2 row (a)/(b)...
    current_l3_code: Optional[str] = None  # "Learners should ..." heading

    # overview bullet capture (L2 under L1)
    in_overview = False
    ov_idx = 0

    # row title assembly
    pending_row_letter: Optional[str] = None
    pending_row_title_parts: list[str] = []

    # bullet nesting under L3
    l4_heading_code: Optional[str] = None
    l3_idx = 0
    l4_idx = 0
    l5_idx = 0

    def reset_heading_state() -> None:
        nonlocal current_l3_code, l4_heading_code, l3_idx, l4_idx, l5_idx
        current_l3_code = None
        l4_heading_code = None
        l3_idx = 0
        l4_idx = 0
        l5_idx = 0

    def flush_pending_row_title() -> None:
        nonlocal pending_row_letter, pending_row_title_parts, current_row_code
        if not current_l1_code or not pending_row_letter:
            return
        title = _norm(" ".join(pending_row_title_parts)) or f"({pending_row_letter})"
        current_row_code = f"{current_l1_code}_{pending_row_letter.lower()}"
        nodes.append(Node(code=current_row_code, title=f"({pending_row_letter.lower()}) {title}".strip(), level=2, parent=current_l1_code))
        pending_row_letter = None
        pending_row_title_parts = []

    def start_new_l1(n: str, title: str) -> None:
        nonlocal current_l1_code, current_row_code, in_overview, ov_idx
        flush_pending_row_title()
        reset_heading_state()
        in_overview = True
        ov_idx = 0
        current_row_code = None
        current_l1_code = f"{unit_code}_2_1_{n}"
        nodes.append(Node(code=current_l1_code, title=f"2.1.{n} {title}".strip(), level=1, parent=unit_code))

    def add_overview_bullet(text_: str) -> None:
        nonlocal ov_idx
        if not current_l1_code:
            return
        ov_idx += 1
        nodes.append(Node(code=f"{current_l1_code}__ov{ov_idx:02d}", title=_norm(text_), level=2, parent=current_l1_code))

    def start_row(letter: str, initial: str) -> None:
        nonlocal pending_row_letter, pending_row_title_parts, current_row_code, in_overview
        reset_heading_state()
        flush_pending_row_title()
        in_overview = False
        current_row_code = None
        pending_row_letter = letter
        pending_row_title_parts = [initial] if initial else []

    def start_l3_heading(text_: str) -> None:
        nonlocal l3_idx, current_l3_code, l4_heading_code, l4_idx, l5_idx
        if not current_row_code:
            return
        l3_idx += 1
        l4_heading_code = None
        l4_idx = 0
        l5_idx = 0
        t = _norm(text_)
        # keep as-is but strip trailing ':' for node title clarity
        if t.endswith(":"):
            t = t[:-1].strip()
        current_l3_code = f"{current_row_code}_s{l3_idx:02d}"
        nodes.append(Node(code=current_l3_code, title=t, level=3, parent=current_row_code))

    def start_l4_heading(text_: str) -> None:
        nonlocal l4_heading_code, l4_idx, l5_idx
        if not current_l3_code:
            return
        l4_idx += 1
        l5_idx = 0
        t = _norm(text_)
        if t.endswith(":"):
            t = t[:-1].strip()
        l4_heading_code = f"{current_l3_code}_h{l4_idx:02d}"
        nodes.append(Node(code=l4_heading_code, title=t, level=4, parent=current_l3_code))

    def add_bullet(text_: str) -> None:
        nonlocal l4_idx, l5_idx
        if not current_l3_code:
            return
        t = _norm(text_)
        # If we have an open heading, bullets go one level deeper.
        if l4_heading_code:
            l5_idx += 1
            nodes.append(Node(code=f"{l4_heading_code}_b{l5_idx:02d}", title=t, level=5, parent=l4_heading_code))
        else:
            l4_idx += 1
            nodes.append(Node(code=f"{current_l3_code}_b{l4_idx:02d}", title=t, level=4, parent=current_l3_code))

    i = 0
    while i < len(block):
        s = _norm(block[i])
        if not s or _looks_like_header_footer(s):
            i += 1
            continue

        # L1 topics
        m1 = l1_re.match(s)
        if m1:
            start_new_l1(m1.group(1), m1.group(2))
            i += 1
            continue

        # Stop capturing overview when we reach the table
        if content_amp_re.match(s):
            in_overview = False
            flush_pending_row_title()
            reset_heading_state()
            i += 1
            continue

        # Overview bullets (L2 under L1)
        bm = bullet_re.match(s)
        if bm and in_overview and current_l1_code:
            add_overview_bullet(bm.group(1))
            i += 1
            continue

        # Start of a table row (a)/(b)...
        rm = row_re.match(s)
        if rm and current_l1_code:
            letter = rm.group(1).lower()
            rest = _norm(rm.group(2) or "")
            # Some lines are like "(d) Data backup Learners should: ..." -> split
            if rest and "Learners should" in rest:
                # Use a non-capturing split to avoid 3-part results from capturing groups.
                parts = re.split(r"(?i)\\bLearners should\\b", rest, maxsplit=1)
                before = _norm(parts[0])
                after_tail = parts[1] if len(parts) > 1 else ""
                start_row(letter, before)
                flush_pending_row_title()
                # push the remaining learners statement back into the stream
                block.insert(i + 1, _norm(f"Learners should {after_tail}"))
                i += 1
                continue
            start_row(letter, rest)
            i += 1
            continue

        # If we're still building the row title, append until we hit Learners should
        if pending_row_letter and not current_row_code:
            if learners_re.match(s):
                flush_pending_row_title()
                continue
            # include content-column bullet fragments in the row title
            if bm:
                pending_row_title_parts.append(_norm(bm.group(1)))
                i += 1
                continue
            # short wrapped continuation
            if len(s) <= 80:
                pending_row_title_parts.append(s)
                i += 1
                continue
            # long line likely means we missed a learners marker; finalize and continue
            flush_pending_row_title()
            continue

        # "Learners should ..." headings become L3 nodes
        if learners_re.match(s) and current_row_code:
            start_l3_heading(s)
            i += 1
            continue

        # Amplification bullets (L4/L5 under current L3)
        if bm and current_l3_code:
            bt = _norm(bm.group(1))
            # If a bullet introduces a list, treat it as a heading and nest subsequent bullets.
            if bt.endswith(":") or bt.lower().endswith("the following:") or bt.lower().endswith("including:"):
                start_l4_heading(bt)
            else:
                add_bullet(bt)
            i += 1
            continue

        # Blank line resets nesting under current L3 (common between bullet groups)
        if current_l3_code and not s:
            l4_heading_code = None
            i += 1
            continue

        i += 1

    flush_pending_row_title()

    # de-dupe by code
    uniq: list[Node] = []
    seen = set()
    for n in nodes:
        if n.code in seen:
            continue
        seen.add(n.code)
        uniq.append(n)

    if not uniq:
        raise RuntimeError("No topics parsed.")
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
    print("WJEC GCSE DIGITAL TECHNOLOGY (3540) - UNIT 1 TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3540-digital-technology-spec.txt")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}")

    nodes = parse_digital_technology_unit1(text)
    levels = {}
    for n in nodes:
        levels[n.level] = levels.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(nodes)
    print("\n[OK] WJEC 3540 Digital Technology (Unit 1) topics scrape complete.")


if __name__ == "__main__":
    main()


