"""
WJEC GCSE Applied Science (Single Award) (Teaching from 2016) - Topics Scraper

Spec PDF:
  https://www.wjec.co.uk/media/a4ebfry4/wjec-gcse-applied-science-single-spec-from-2016.pdf

Target hierarchy (per user spec):
  - L0: Units (Unit 1..2 only for learning content)
  - L1: Topics (e.g. 1.1 Modern living and energy)
  - L2: Subtopics (e.g. 1.1.1 Underpinning energy concepts)
  - L3: (a)/(b)/(c)... content statements under "Learners should be able to demonstrate..."

Ignore:
  - Overview
  - Working Scientifically
  - Mathematical skills
  - Unit 3/4 (Task Based / Practical Assessment) and other admin/assessment text
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
    "name": "Applied Science (Single Award)",
    "code": "WJEC-3440",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/a4ebfry4/wjec-gcse-applied-science-single-spec-from-2016.pdf",
}


UNIT_TITLES = {
    1: "Unit 1 (Single Award): Science in the Modern World",
    2: "Unit 2 (Single Award): Science to Support Our Lifestyles",
}


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
    if re.fullmatch(r"\d{1,3}", s):
        return True
    if s.startswith("GCSE APPLIED SCIENCE"):
        return True
    return False


def _append_wrapped(parts: list[str], s: str) -> None:
    s = _norm(s)
    if not s:
        return
    if not parts:
        parts.append(s)
        return
    if s[0].islower() or parts[-1].endswith("-") or s.startswith(("and ", "or ", "including ", "to ", "with ", "for ")):
        parts[-1] = _norm(f"{parts[-1]} {s}")
    else:
        parts.append(s)


def download_pdf_text(url: str) -> str:
    print("[INFO] Downloading PDF...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    reader = PdfReader(BytesIO(resp.content))
    print(f"[OK] Downloaded {len(reader.pages)} pages")
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def _find_unit_blocks(lines: list[str]) -> dict[int, tuple[int, int]]:
    # Subject content section uses 2.1 Unit 1, 2.2 Unit 2, 2.3 Unit 3...
    unit_start_re = re.compile(r"^2\.\d+\s+Unit\s+([1-4])\b", flags=re.IGNORECASE)
    starts: dict[int, int] = {}

    for i, raw in enumerate(lines):
        s = _norm(raw)
        m = unit_start_re.match(s)
        if not m:
            continue
        unit_num = int(m.group(1))
        if unit_num not in (1, 2):
            continue
        window = "\n".join(lines[i : i + 140])
        if re.search(rf"\b{unit_num}\.1\b", window) and "This unit includes the following topics" in window:
            starts[unit_num] = i

    blocks: dict[int, tuple[int, int]] = {}
    for unit_num in sorted(starts):
        start = starts[unit_num]
        end = len(lines)
        for other in sorted(starts):
            if other <= unit_num:
                continue
            end = starts[other]
            break
        # stop at Unit 3 if it appears (we only want Units 1/2)
        for j in range(start, len(lines)):
            sj = _norm(lines[j])
            if re.match(r"^2\.\d+\s+Unit\s+3\b", sj, flags=re.IGNORECASE) or sj.startswith("3 Assessment"):
                end = j
                break
        blocks[unit_num] = (start, end)
    return blocks


def parse_applied_science_single(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]
    lines = [ln.rstrip() for ln in text.split("\n")]
    blocks = _find_unit_blocks(lines)

    # patterns
    # L1 headings sometimes appear as "1.1.  MODERN LIVING AND ENERGY" (extra dot after minor).
    l1_re = re.compile(r"^([1-2])\.(\d)\.?\s+(.+)$")
    l2_re = re.compile(r"^([1-2])\.(\d)\.(\d)\s+(.+)$")
    letter_re = re.compile(r"^\(([a-z])\)\s*(.+)$", flags=re.IGNORECASE)
    stop_content_re = re.compile(r"^(SPECIFIED PRACTICAL WORK|Table\s+\d+(\.\d+)?\b)", flags=re.IGNORECASE)

    start_content_prefix_re = re.compile(
        r"^Learners should be able to demonstrate and apply their knowledge and\b",
        re.IGNORECASE,
    )
    understanding_of_re = re.compile(r"^understanding of:?\s*$", re.IGNORECASE)
    skip_section_titles = {"Overview", "Working Scientifically", "Mathematical skills"}

    def _is_caps_heading_text(t: str) -> bool:
        letters = [ch for ch in t if ch.isalpha()]
        if not letters:
            return False
        upper = sum(1 for ch in letters if ch.isupper())
        return (upper / len(letters)) >= 0.7

    nodes: list[Node] = []

    for unit_num in (1, 2):
        if unit_num not in blocks:
            continue
        start, end = blocks[unit_num]
        block_lines = lines[start:end]

        unit_code = f"U{unit_num}"
        nodes.append(Node(code=unit_code, title=UNIT_TITLES[unit_num], level=0, parent=None))

        current_l1_code: Optional[str] = None
        current_l2_code: Optional[str] = None
        in_content = False

        current_l3_code: Optional[str] = None
        current_l3_parts: list[str] = []

        def flush_l3() -> None:
            nonlocal current_l3_code, current_l3_parts
            if current_l2_code and current_l3_code and current_l3_parts:
                title = _norm(" ".join(current_l3_parts))
                if title:
                    nodes.append(Node(code=current_l3_code, title=title, level=3, parent=current_l2_code))
            current_l3_code = None
            current_l3_parts = []

        def ensure_l2_for_topic_level_content() -> Optional[str]:
            """
            Some WJEC topics (e.g. 1.4 Protecting our environment) have no numbered subtopics
            (1.4.1 etc) and jump straight from the L1 topic into lettered (a)/(b)/(c) statements.

            In that case we create a single implicit L2 ("Content") under the current L1 so those
            lettered statements have a stable parent.
            """
            nonlocal current_l2_code
            if current_l2_code:
                return current_l2_code
            if not current_l1_code:
                return None
            current_l2_code = f"{current_l1_code}__content"
            nodes.append(Node(code=current_l2_code, title="Content", level=2, parent=current_l1_code))
            return current_l2_code

        # Start at first ALL CAPS L1 header to avoid the topic list preamble.
        content_start = 0
        for j, raw in enumerate(block_lines):
            sj = _norm(raw)
            m1 = l1_re.match(sj)
            if m1 and int(m1.group(1)) == unit_num:
                if _is_caps_heading_text(m1.group(3)):
                    content_start = j
                    break

        i = content_start
        while i < len(block_lines):
            s = _norm(block_lines[i])
            if not s or _looks_like_header_footer(s):
                i += 1
                continue

            # L2 headings first
            m2 = l2_re.match(s)
            if m2 and int(m2.group(1)) == unit_num:
                flush_l3()
                in_content = False
                major, minor, sub, title = m2.group(1), m2.group(2), m2.group(3), m2.group(4)
                title_parts = [title]
                j = i + 1
                while j < len(block_lines):
                    nxt = _norm(block_lines[j])
                    if not nxt or _looks_like_header_footer(nxt):
                        j += 1
                        continue
                    if l2_re.match(nxt) or l1_re.match(nxt) or start_content_prefix_re.match(nxt) or understanding_of_re.match(nxt) or nxt in skip_section_titles:
                        break
                    if len(nxt) <= 120 and not nxt.endswith("."):
                        title_parts.append(nxt)
                        j += 1
                        continue
                    break
                full_title = _norm(" ".join(title_parts))
                current_l2_code = f"{unit_code}_{major}_{minor}_{sub}"
                parent = current_l1_code or unit_code
                nodes.append(Node(code=current_l2_code, title=f"{major}.{minor}.{sub} {full_title}".strip(), level=2, parent=parent))
                i = j
                continue

            # L1 headings
            m1 = l1_re.match(s)
            if m1 and int(m1.group(1)) == unit_num and not re.match(r"^\d+\.\d+\.\d+", s):
                flush_l3()
                in_content = False
                major, minor, title = m1.group(1), m1.group(2), m1.group(3)
                title_parts = [title]
                j = i + 1
                while j < len(block_lines):
                    nxt = _norm(block_lines[j])
                    if not nxt or _looks_like_header_footer(nxt):
                        j += 1
                        continue
                    if l2_re.match(nxt) or l1_re.match(nxt) or nxt in skip_section_titles or start_content_prefix_re.match(nxt) or understanding_of_re.match(nxt):
                        break
                    if len(nxt) <= 120 and not nxt.endswith("."):
                        title_parts.append(nxt)
                        j += 1
                        continue
                    break
                full_title = _norm(" ".join(title_parts))
                current_l1_code = f"{unit_code}_{major}_{minor}"
                current_l2_code = None
                nodes.append(Node(code=current_l1_code, title=f"{major}.{minor} {full_title}".strip(), level=1, parent=unit_code))
                i = j
                continue

            if s in skip_section_titles:
                in_content = False
                flush_l3()
                i += 1
                continue

            if start_content_prefix_re.match(s):
                in_content = True
                flush_l3()
                i += 1
                continue
            if understanding_of_re.match(s) and i > 0 and start_content_prefix_re.match(_norm(block_lines[i - 1])):
                in_content = True
                flush_l3()
                i += 1
                continue

            if in_content:
                # Defensive: stop content before specified practical work / tables.
                if stop_content_re.match(s):
                    flush_l3()
                    in_content = False
                    i += 1
                    continue

                parent_l2 = ensure_l2_for_topic_level_content()
                if not parent_l2:
                    i += 1
                    continue

                lm = letter_re.match(s)
                if lm:
                    flush_l3()
                    letter = lm.group(1).lower()
                    content = lm.group(2).strip()
                    current_l3_code = f"{parent_l2}_{letter}"
                    current_l3_parts = [content] if content else []
                    i += 1
                    continue
                if current_l3_code and current_l3_parts:
                    if l2_re.match(s) or l1_re.match(s):
                        flush_l3()
                        in_content = False
                        continue
                    _append_wrapped(current_l3_parts, s)
                    i += 1
                    continue

            i += 1

        flush_l3()

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
    env_path = Path(r"C:\\Users\\tonyd\\OneDrive - 4Sight Education Ltd\\Apps\\flash-curriculum-pipeline\\.env")
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
        res = (
            supabase.table("staging_aqa_topics")
            .delete()
            .eq("subject_id", subject_id)
            .eq("topic_level", lvl)
            .execute()
        )
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
    print("WJEC GCSE APPLIED SCIENCE (SINGLE AWARD) (3440) - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3440-spec.txt")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}")

    nodes = parse_applied_science_single(text)
    levels = {}
    for n in nodes:
        levels[n.level] = levels.get(n.level, 0) + 1
    print("\\n[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(nodes)
    print("\\n[OK] WJEC 3440 topics scrape complete.")


if __name__ == "__main__":
    main()


