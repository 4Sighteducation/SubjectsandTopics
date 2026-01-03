"""
WJEC GCSE The Sciences (Double Award) (3450QD) - Topics Scraper

Spec (Teaching from 2025 / award from 2026/2027):
  https://www.wjec.co.uk/media/1iyjmnoo/wjec-gcse-the-sciences-double-award-specification-e.pdf

Structure (per spec text extraction):
  - L0: Units 1-6
  - L1: Topic areas (e.g., 1.1 Cell structure and function...)
  - L2: Subtopics (e.g., 1.1.1 Structure of animal and plant cells)
  - L3: Learners-should headings (know/understand/be able to/be aware of)
  - L4: Bullet statements and short prose points
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
    "name": "The Sciences (Double Award)",
    "code": "WJEC-3450QD",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/1iyjmnoo/wjec-gcse-the-sciences-double-award-specification-e.pdf",
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
    if s.startswith("GCSE THE SCIENCES"):
        return True
    if re.fullmatch(r"\d{1,3}", s):  # page number
        return True
    return False


def download_pdf_text(url: str) -> str:
    print("[INFO] Downloading PDF...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    reader = PdfReader(BytesIO(resp.content))
    print(f"[OK] Downloaded {len(reader.pages)} pages")
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def upload_to_staging(*, subject: dict, nodes: list[Node]) -> None:
    env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
    load_dotenv(env_path)
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    subject_result = supabase.table("staging_aqa_subjects").upsert(
        {
            "subject_name": f"{subject['name']} (GCSE)",
            "subject_code": subject["code"],
            "qualification_type": "GCSE",
            "specification_url": subject["pdf_url"],
            "exam_board": subject["exam_board"],
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
            "exam_board": subject["exam_board"],
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


def parse_sciences_double(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    unit_heading_re = re.compile(r"^Unit\s+([1-6])\s*$", flags=re.IGNORECASE)
    areas_re = re.compile(r"^Areas of content$", flags=re.IGNORECASE)
    section_amp_re = re.compile(r"^Section Amplification$", flags=re.IGNORECASE)

    l1_re = re.compile(r"^(\d+\.\d)\s+(.+)$")  # 1.1 Cell structure and function...
    l2_code_only_re = re.compile(r"^(\d+\.\d+\.\d)\s*$")  # 1.1.1
    l2_inline_re = re.compile(r"^(\d+\.\d+\.\d)\s+(.+)$")  # 1.1.1 Structure of...

    learners_head_re = re.compile(r"^(Learners should (?:know|understand|be able to|be aware of))\s*:?\s*$", flags=re.IGNORECASE)
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7]\s*(.+)$")

    # Collect real unit starts (avoid TOC by requiring Areas of content nearby)
    starts: dict[int, int] = {}
    titles: dict[int, str] = {}
    for i, raw in enumerate(lines):
        s = _norm(raw)
        mh = unit_heading_re.match(s)
        if not mh:
            continue
        u = int(mh.group(1))
        window = "\n".join(_norm(x) for x in lines[i : i + 90]).lower()
        if "areas of content" not in window or "section amplification" not in window:
            continue
        starts[u] = i
        # title is usually on next non-empty non-header line
        title = ""
        for j in range(i + 1, min(i + 12, len(lines))):
            t = _norm(lines[j])
            if not t or _looks_like_header_footer(t):
                continue
            if t.lower().startswith(("written examination", "overview of unit")):
                continue
            title = t
            break
        titles[u] = title or f"Unit {u}"

    if not starts:
        raise RuntimeError("Could not locate Unit blocks for The Sciences (Double Award).")

    unit_nums = sorted(starts)
    blocks: dict[int, tuple[int, int]] = {}
    for idx, u in enumerate(unit_nums):
        start = starts[u]
        end = len(lines)
        if idx + 1 < len(unit_nums):
            end = starts[unit_nums[idx + 1]]
        blocks[u] = (start, end)

    nodes: list[Node] = []

    for u in unit_nums:
        start, end = blocks[u]
        ucode = f"U{u}"
        utitle = titles.get(u) or f"Unit {u}"
        nodes.append(Node(code=ucode, title=f"Unit {u}: {utitle}".strip(), level=0, parent=None))

        block = lines[start:end]

        in_areas = False
        in_amp = False
        current_l1: Optional[str] = None
        current_l2: Optional[str] = None
        pending_l2: Optional[str] = None

        current_l3: Optional[str] = None
        l3_idx = 0
        l4_idx = 0

        def ensure_l1(code: str, title: str) -> str:
            nonlocal current_l1
            current_l1 = f"{ucode}_{code.replace('.', '_')}"
            nodes.append(Node(code=current_l1, title=f"{code} {title}".strip(), level=1, parent=ucode))
            return current_l1

        def start_l2(code: str, title: str) -> str:
            nonlocal current_l2, current_l3, l3_idx, l4_idx
            if not current_l1:
                ensure_l1(f"{u}.0", "Content")
            current_l2 = f"{current_l1}_{code.replace('.', '_')}"
            nodes.append(Node(code=current_l2, title=f"{code} {title}".strip(), level=2, parent=current_l1))
            current_l3 = None
            l3_idx = 0
            l4_idx = 0
            return current_l2

        def start_l3(title: str) -> str:
            nonlocal current_l3, l3_idx, l4_idx
            if not current_l2:
                return ""
            l3_idx += 1
            current_l3 = f"{current_l2}_H{l3_idx:02d}"
            nodes.append(Node(code=current_l3, title=title, level=3, parent=current_l2))
            l4_idx = 0
            return current_l3

        def add_l4(text_line: str) -> None:
            nonlocal l4_idx
            parent = current_l3 or current_l2
            if not parent:
                return
            l4_idx += 1
            nodes.append(Node(code=f"{parent}_P{l4_idx:02d}", title=text_line, level=4, parent=parent))

        for raw in block:
            s = _norm(raw)
            if not s or _looks_like_header_footer(s):
                continue
            # stop at assessment/technical sections if they appear
            if s.upper().startswith(("3 ASSESSMENT", "4 MALPRACTICE", "5 TECHNICAL INFORMATION")):
                break

            if areas_re.match(s):
                in_areas = True
                in_amp = False
                continue
            if section_amp_re.match(s):
                in_amp = True
                in_areas = False
                continue

            if in_areas:
                m1 = l1_re.match(s)
                if m1:
                    ensure_l1(m1.group(1), m1.group(2))
                continue

            if in_amp:
                mi = l2_inline_re.match(s)
                if mi:
                    pending_l2 = None
                    start_l2(mi.group(1), mi.group(2))
                    continue
                mc = l2_code_only_re.match(s)
                if mc:
                    pending_l2 = mc.group(1)
                    continue
                if pending_l2 and not learners_head_re.match(s) and not bullet_re.match(s):
                    # title for pending l2 (may wrap, but usually 1 line here)
                    start_l2(pending_l2, s)
                    pending_l2 = None
                    continue

                mh = learners_head_re.match(s)
                if mh:
                    start_l3(f"{mh.group(1)}:")
                    continue

                bm = bullet_re.match(s)
                if bm:
                    if not current_l3 and current_l2:
                        start_l3("Content:")
                    add_l4(_norm(bm.group(1)))
                    continue

                if current_l2:
                    if not current_l3:
                        start_l3("Content:")
                    add_l4(s)

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


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC GCSE THE SCIENCES (DOUBLE AWARD) (3450QD) - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3450qd-the-sciences-double.txt")
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}\n")

    nodes = parse_sciences_double(text)

    counts: dict[int, int] = {}
    for n in nodes:
        counts[n.level] = counts.get(n.level, 0) + 1
    print("[INFO] Level breakdown:")
    for lvl in sorted(counts):
        print(f"  - L{lvl}: {counts[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("\n[OK] WJEC 3450QD The Sciences (Double Award) topics scrape complete.")


if __name__ == "__main__":
    main()


