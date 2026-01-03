"""
WJEC GCSE Health and Social Care, and Childcare (3910) - Topics Scraper (Unit 1 only)

Spec (Teaching from 2025 / award from 2027):
  https://www.wjec.co.uk/media/1vwfivwb/wjec-gcse-health-and-social-care-and-childcare-specification-e.pdf

User requirement:
  - Only Unit 1 (exam): Health and Social Care, and Childcare in Wales in the 21st Century
  - Structure:
      L0: Unit 1
      L1: 1.1 / 1.2 / 1.3 topics
      L2: 1.x.y subtopics (from Section Amplification)
      L3: "Learners should know/understand/be able to/..." heading lines (when present)
      L4: bullet statements and short prose points
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
    "name": "Health and Social Care, and Childcare",
    "code": "WJEC-3910",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/1vwfivwb/wjec-gcse-health-and-social-care-and-childcare-specification-e.pdf",
}

UNIT_1_TITLE = "Unit 1: Health and Social Care, and Childcare in Wales in the 21st Century"


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
    if s.startswith("GCSE HEALTH AND SOCIAL CARE"):
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


def parse_unit1(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Locate Unit 1 start (avoid TOC "Unit 1 .... 10")
    unit1_heading_re = re.compile(r"^Unit\s+1\s*$", flags=re.IGNORECASE)
    unit2_heading_re = re.compile(r"^Unit\s+2\s*$", flags=re.IGNORECASE)

    start = None
    for i, raw in enumerate(lines):
        s = _norm(raw)
        if not unit1_heading_re.match(s):
            continue
        window = "\n".join(_norm(x) for x in lines[i : i + 80])
        if "Areas of content" in window and "1.1 Growth and Development" in window and "Section Amplification" in window:
            start = i
            break
    if start is None:
        raise RuntimeError("Could not locate Unit 1 block (Unit 1 heading).")

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if unit2_heading_re.match(_norm(lines[j])):
            end = j
            break

    block = lines[start:end]

    # Patterns
    areas_re = re.compile(r"^Areas of content$", flags=re.IGNORECASE)
    section_amp_re = re.compile(r"^Section Amplification$", flags=re.IGNORECASE)
    l1_re = re.compile(r"^(1\.\d)\s+(.+)$")  # 1.1 Growth and Development
    l2_code_only_re = re.compile(r"^(1\.\d\.\d)\s*$")  # 1.1.1
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7]\s*(.+)$")
    learners_re = re.compile(r"^Learners should\b", flags=re.IGNORECASE)

    nodes: list[Node] = []
    nodes.append(Node(code="U1", title=UNIT_1_TITLE, level=0, parent=None))

    current_l1: Optional[str] = None
    current_l2: Optional[str] = None
    current_l3: Optional[str] = None
    current_l3_idx = 0
    current_l4_idx = 0

    in_section_amp = False
    pending_l2_code: Optional[str] = None

    def ensure_l1(code: str, title: str) -> None:
        nonlocal current_l1
        current_l1 = f"U1_{code.replace('.', '_')}"
        nodes.append(Node(code=current_l1, title=f"{code} {title}".strip(), level=1, parent="U1"))

    def start_l2(code: str, title: str) -> None:
        nonlocal current_l2, current_l3, current_l3_idx, current_l4_idx
        if not current_l1:
            # defensive: create a placeholder
            ensure_l1("1.0", "Unit content")
        current_l2 = f"{current_l1}_{code.replace('.', '_')}"
        nodes.append(Node(code=current_l2, title=f"{code} {title}".strip(), level=2, parent=current_l1))
        current_l3 = None
        current_l3_idx = 0
        current_l4_idx = 0

    def start_l3(title: str) -> None:
        nonlocal current_l3, current_l3_idx, current_l4_idx
        if not current_l2:
            return
        current_l3_idx += 1
        current_l3 = f"{current_l2}_H{current_l3_idx:02d}"
        nodes.append(Node(code=current_l3, title=title, level=3, parent=current_l2))
        current_l4_idx = 0

    def add_l4(text_line: str) -> None:
        nonlocal current_l4_idx
        parent = current_l3 or current_l2
        if not parent:
            return
        current_l4_idx += 1
        nodes.append(Node(code=f"{parent}_P{current_l4_idx:02d}", title=text_line, level=4, parent=parent))

    i = 0
    while i < len(block):
        raw = block[i]
        s = _norm(raw)

        if not s or _looks_like_header_footer(s):
            i += 1
            continue

        if areas_re.match(s):
            in_section_amp = False
            i += 1
            continue

        if section_amp_re.match(s):
            in_section_amp = True
            i += 1
            continue

        # L1 topics (from Areas of content)
        m1 = l1_re.match(s)
        if m1:
            ensure_l1(m1.group(1), m1.group(2))
            pending_l2_code = None
            i += 1
            continue

        if in_section_amp:
            # L2 code-only marker
            m2 = l2_code_only_re.match(s)
            if m2:
                pending_l2_code = m2.group(1)
                i += 1
                continue

            # Title lines for a pending L2 (can wrap across multiple lines)
            if pending_l2_code and not learners_re.match(s) and not bullet_re.match(s):
                title_parts = [s]
                j = i + 1
                while j < len(block):
                    t = _norm(block[j])
                    if not t or _looks_like_header_footer(t):
                        j += 1
                        continue
                    if learners_re.match(t) or bullet_re.match(t) or l2_code_only_re.match(t) or l1_re.match(t) or section_amp_re.match(t):
                        break
                    title_parts.append(t)
                    j += 1
                start_l2(pending_l2_code, _norm(" ".join(title_parts)))
                pending_l2_code = None
                i = j
                continue

            # Headings and content under current L2
            if learners_re.match(s):
                # Keep the full heading line; content lists beneath are bullets/prose
                start_l3(s)
                i += 1
                continue

            bm = bullet_re.match(s)
            if bm:
                add_l4(_norm(bm.group(1)))
                i += 1
                continue

            # prose line; attach as L4 point
            add_l4(s)
            i += 1
            continue

        i += 1

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


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC GCSE HEALTH AND SOCIAL CARE, AND CHILDCARE (3910) - TOPICS SCRAPER (UNIT 1)")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3910-hscc-spec.txt")
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}\n")

    nodes = parse_unit1(text)

    # breakdown
    counts: dict[int, int] = {}
    for n in nodes:
        counts[n.level] = counts.get(n.level, 0) + 1
    print("[INFO] Level breakdown:")
    for lvl in sorted(counts):
        print(f"  - L{lvl}: {counts[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("\n[OK] WJEC 3910 HSCC Unit 1 scrape complete.")


if __name__ == "__main__":
    main()






