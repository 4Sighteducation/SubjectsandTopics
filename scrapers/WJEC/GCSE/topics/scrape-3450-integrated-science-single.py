"""
WJEC GCSE Integrated Science (Single Award) (3450QS) - Topics Scraper

Spec (Teaching from 2025 / award from 2027):
  https://www.wjec.co.uk/media/zjtmica5/wjec-gcse-integrated-science-single-award-specification.pdf

Structure (per spec text extraction):
  - L0: Units 1-3
  - L1: Themes (e.g., 1.1 Maintaining a healthy body)
  - L2: Topics (e.g., 1.1.1 Diet and exercise)
  - L3: Subtopics (e.g., 1.1.1a Enzymes and digestion)
  - L4: Learners-should headings (know/understand/be able to/be aware of)
  - L5: Bullet statements and short prose points
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
    "name": "Integrated Science (Single Award)",
    "code": "WJEC-3450QS",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/zjtmica5/wjec-gcse-integrated-science-single-award-specification.pdf",
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
    if s.startswith("GCSE INTEGRATED SCIENCE"):
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


def parse_integrated_science_single(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    unit_re = re.compile(r"^Unit\s+(\d+)\s*[–-]\s*(.+)$", flags=re.IGNORECASE)
    areas_re = re.compile(r"^Areas of content$", flags=re.IGNORECASE)
    section_amp_re = re.compile(r"^Section Amplification$", flags=re.IGNORECASE)

    theme_re = re.compile(r"^(\d+\.\d)\s+(.+)$")  # 1.1 Maintaining a healthy body
    topic_re = re.compile(r"^(\d+\.\d+\.\d)\s+(.+)$")  # 1.1.1 Diet and exercise
    sub_inline_re = re.compile(r"^(\d+\.\d+\.\d[a-z])\s+(.+)$")  # 1.1.1a Enzymes and digestion
    sub_code_only_re = re.compile(r"^(\d+\.\d+\.\d[a-z])\s*$")  # 1.1.1a

    learners_head_re = re.compile(r"^(Learners should (?:know|understand|be able to|be aware of))\s*:?\s*$", flags=re.IGNORECASE)
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7]\s*(.+)$")

    # Find unit starts for Units 1-3 (we use these starts as hard boundaries to prevent
    # assessment/technical sections from leaking into Unit 2 parsing).
    starts: dict[int, tuple[int, str]] = {}
    for i, raw in enumerate(lines):
        s = _norm(raw)
        m = unit_re.match(s)
        if not m:
            continue
        unit_num = int(m.group(1))
        if unit_num not in (1, 2, 3):
            continue
        title = m.group(2)
        starts[unit_num] = (i, title)

    if not starts:
        raise RuntimeError("Could not locate Unit blocks for Integrated Science (Single).")

    unit_nums = sorted(starts)
    blocks: dict[int, tuple[int, int, str]] = {}
    for idx, u in enumerate(unit_nums):
        start = starts[u][0]
        title = starts[u][1]
        end = len(lines)
        if idx + 1 < len(unit_nums):
            end = starts[unit_nums[idx + 1]][0]
        blocks[u] = (start, end, title)

    nodes: list[Node] = []

    # maps for ensuring nodes exist
    theme_nodes: dict[str, str] = {}
    topic_nodes: dict[str, str] = {}

    for unit_num, (start, end, unit_title) in blocks.items():
        ucode = f"U{unit_num}"
        nodes.append(Node(code=ucode, title=f"Unit {unit_num}: {unit_title}".strip(), level=0, parent=None))

        block = lines[start:end]

        in_areas = False
        in_amp = False
        current_theme_code: Optional[str] = None  # e.g. 1.1
        current_topic_code: Optional[str] = None  # e.g. 1.1.1
        current_sub_code: Optional[str] = None  # e.g. 1.1.1a
        pending_sub: Optional[str] = None

        current_l4: Optional[str] = None
        l4_idx = 0
        l5_idx = 0

        def ensure_theme(code: str, title: str) -> str:
            if code in theme_nodes:
                return theme_nodes[code]
            node_code = f"{ucode}_{code.replace('.', '_')}"
            theme_nodes[code] = node_code
            nodes.append(Node(code=node_code, title=f"{code} {title}".strip(), level=1, parent=ucode))
            return node_code

        def ensure_topic(code: str, title: str) -> str:
            if code in topic_nodes:
                return topic_nodes[code]
            theme_code = ".".join(code.split(".")[:2])
            theme_node = theme_nodes.get(theme_code) or ensure_theme(theme_code, "Theme")
            node_code = f"{theme_node}_{code.replace('.', '_')}"
            topic_nodes[code] = node_code
            nodes.append(Node(code=node_code, title=f"{code} {title}".strip(), level=2, parent=theme_node))
            return node_code

        def start_sub(code: str, title: str) -> str:
            nonlocal current_sub_code, current_l4, l4_idx, l5_idx
            if not current_topic_code:
                # defensive
                ensure_topic("0.0.0", "Topic")
            topic_node = topic_nodes.get(current_topic_code) or ensure_topic(current_topic_code or "0.0.0", "Topic")
            sub_node = f"{topic_node}_{code.replace('.', '_')}"
            nodes.append(Node(code=sub_node, title=f"{code} {title}".strip(), level=3, parent=topic_node))
            current_sub_code = code
            current_l4 = None
            l4_idx = 0
            l5_idx = 0
            return sub_node

        def start_l4(title: str, parent_code: str) -> str:
            nonlocal current_l4, l4_idx, l5_idx
            l4_idx += 1
            current_l4 = f"{parent_code}_H{l4_idx:02d}"
            nodes.append(Node(code=current_l4, title=title, level=4, parent=parent_code))
            l5_idx = 0
            return current_l4

        def add_l5(text_line: str, parent_code: str) -> None:
            nonlocal l5_idx
            l5_idx += 1
            nodes.append(Node(code=f"{parent_code}_P{l5_idx:02d}", title=text_line, level=5, parent=parent_code))

        # Special-case Unit 3: Scientific Enquiry has no Section Amplification table; keep a curated shell.
        if unit_num == 3:
            tasks_parent = f"{ucode}_tasks"
            nodes.append(Node(code=tasks_parent, title="Tasks", level=1, parent=ucode))

            task_re = re.compile(r"^Task\s+([12])\s+\((\d+)\s+marks\)\s*:\s*$", flags=re.IGNORECASE)
            current_task: Optional[str] = None
            step_idx = 0
            for raw in block:
                s = _norm(raw)
                if not s or _looks_like_header_footer(s):
                    continue
                if s.upper().startswith("3 ASSESSMENT"):
                    break
                mtask = task_re.match(s)
                if mtask:
                    tnum = mtask.group(1)
                    marks = mtask.group(2)
                    current_task = f"{tasks_parent}_t{tnum}"
                    nodes.append(Node(code=current_task, title=f"Task {tnum} ({marks} marks)", level=2, parent=tasks_parent))
                    step_idx = 0
                    continue
                if current_task:
                    step_idx += 1
                    nodes.append(Node(code=f"{current_task}_p{step_idx:02d}", title=s, level=3, parent=current_task))
            continue

        for raw in block:
            s = _norm(raw)
            if not s or _looks_like_header_footer(s):
                continue
            # Stop before generic Assessment/appendix/technical sections if they appear inside the unit block.
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
                mth = theme_re.match(s)
                if mth:
                    current_theme_code = mth.group(1)
                    ensure_theme(mth.group(1), mth.group(2))
                    continue
                mt = topic_re.match(s)
                if mt:
                    current_topic_code = mt.group(1)
                    ensure_topic(mt.group(1), mt.group(2))
                    continue
                continue

            if in_amp:
                # topic header repeats
                mt = topic_re.match(s)
                if mt:
                    current_topic_code = mt.group(1)
                    ensure_topic(mt.group(1), mt.group(2))
                    pending_sub = None
                    current_sub_code = None
                    current_l4 = None
                    l4_idx = 0
                    l5_idx = 0
                    continue

                msi = sub_inline_re.match(s)
                if msi:
                    pending_sub = None
                    start_sub(msi.group(1), msi.group(2))
                    continue

                msc = sub_code_only_re.match(s)
                if msc:
                    pending_sub = msc.group(1)
                    continue

                # pending subtopic title can wrap
                if pending_sub:
                    title_parts = [s]
                    # if title is split across multiple lines, keep joining until a learner heading/bullet/subtopic marker/topic header
                    # (we don't have direct line index here, so just use this single line; wrapping is uncommon in this spec)
                    start_sub(pending_sub, _norm(" ".join(title_parts)))
                    pending_sub = None
                    continue

                # learner headings / bullets under current subtopic
                if current_topic_code and current_sub_code:
                    sub_parent = topic_nodes.get(current_topic_code)
                    sub_node_code = f"{sub_parent}_{current_sub_code.replace('.', '_')}" if sub_parent else None
                    if not sub_node_code:
                        continue

                    mh = learners_head_re.match(s)
                    if mh:
                        start_l4(f"{mh.group(1)}:", sub_node_code)
                        continue

                    bm = bullet_re.match(s)
                    if bm:
                        parent = current_l4 or start_l4("Content:", sub_node_code)
                        add_l5(_norm(bm.group(1)), parent)
                        continue

                    # prose line
                    parent = current_l4 or start_l4("Content:", sub_node_code)
                    add_l5(s, parent)
                    continue

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
    print("WJEC GCSE INTEGRATED SCIENCE (SINGLE AWARD) (3450QS) - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3450qs-integrated-science-single.txt")
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}\n")

    nodes = parse_integrated_science_single(text)

    counts: dict[int, int] = {}
    for n in nodes:
        counts[n.level] = counts.get(n.level, 0) + 1
    print("[INFO] Level breakdown:")
    for lvl in sorted(counts):
        print(f"  - L{lvl}: {counts[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("\n[OK] WJEC 3450QS Integrated Science (Single) topics scrape complete.")


if __name__ == "__main__":
    main()


