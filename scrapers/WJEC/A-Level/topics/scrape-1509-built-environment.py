"""
WJEC GCE AS/A Level Built Environment (2021 spec) - Topics Scraper

Spec:
  https://www.wjec.co.uk/media/x02b00xo/wjec-gce-built-environment-specification-e-23-08-2021.pdf

Entry-code mapping in spec:
  - AS Units 1-2: 2509U1/2509U2, AS cash-in: 2509QS/2509CS
  - A2 Units 3-4: 1509U3/1509U4, A level cash-in: 1509QS/1509CS

We model the full A level content under one subject code (A level cash-in): WJEC-1509CS.

PDF structure within each unit:
  - Unit heading (2.1 AS Unit 1, 2.2 AS Unit 2, 2.3 A Level Unit 3, 2.4 A Level Unit 4)
  - Areas of content list (2.1.1 ... etc)
  - For each area, a "Content  Amplification" table with (a)/(b)/(c) rows:
      - Row title in the "Content" column
      - Row amplification prose + "Learners should ..." headings + bullet lists

Hierarchy:
  - L0: Unit 1..4
  - L1: Area of content (e.g., 2.1.1 ...)
  - L2: Content row (a/b/c...) with row title
  - L3: "Learners should ..." headings (and other colon headings)
  - L4: bullets / short prose points
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
    "code": "WJEC-1509CS",
    "qualification": "A-Level",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/x02b00xo/wjec-gce-built-environment-specification-e-23-08-2021.pdf",
}


UNIT_TITLES = {
    1: "AS Unit 1: Our built environment",
    2: "AS Unit 2: Design and planning practices",
    3: "A2 Unit 3: Materials, technologies and techniques",
    4: "A2 Unit 4: Construction practices",
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
    if s.startswith("GCE AS AND A LEVEL BUILT ENVIRONMENT"):
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
            "subject_name": f"{subject['name']} (A-Level)",
            "subject_code": subject["code"],
            "qualification_type": "A-Level",
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


def parse_built_environment(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Find unit starts by the "2.x AS Unit N"/"2.x A Level Unit N" heading lines
    unit_hdr_re = re.compile(r"^2\.(\d)\s+(AS|A\s*Level)\s+Unit\s+([1-4])\b", flags=re.IGNORECASE)
    starts: dict[int, int] = {}
    for i, raw in enumerate(lines):
        s = _norm(raw)
        m = unit_hdr_re.match(s)
        if not m:
            continue
        u = int(m.group(3))
        window = "\n".join(_norm(x) for x in lines[i : i + 80]).lower()
        if "areas of content" in window and "content" in window and "amplification" in window:
            starts[u] = i

    if not starts:
        raise RuntimeError("Could not locate unit blocks for Built Environment.")

    unit_nums = sorted(starts)
    blocks: dict[int, tuple[int, int]] = {}
    for idx, u in enumerate(unit_nums):
        start = starts[u]
        end = len(lines)
        if idx + 1 < len(unit_nums):
            end = starts[unit_nums[idx + 1]]
        blocks[u] = (start, end)

    area_re = re.compile(r"^(2\.[1-4]\.\d+(?:\.\d+)?[a-z]?)\s+(.+)$", flags=re.IGNORECASE)
    content_amp_re = re.compile(r"^Content\s+Amplification$", flags=re.IGNORECASE)
    row_re = re.compile(r"^\(([a-z])\)\s*(.*)$", flags=re.IGNORECASE)
    learners_re = re.compile(r"^(Learners should|They should)\b", flags=re.IGNORECASE)
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7]\s*(.+)$")

    nodes: list[Node] = []

    for u in unit_nums:
        ucode = f"U{u}"
        nodes.append(Node(code=ucode, title=UNIT_TITLES.get(u, f"Unit {u}"), level=0, parent=None))

        start, end = blocks[u]
        block = lines[start:end]

        current_area: Optional[str] = None
        current_row: Optional[str] = None
        current_head: Optional[str] = None
        head_idx = 0
        point_idx = 0
        in_table = False

        pending_row_letter: Optional[str] = None
        pending_row_title_parts: list[str] = []

        def start_area(code: str, title: str) -> None:
            nonlocal current_area, current_row, current_head, head_idx, point_idx, in_table
            current_area = f"{ucode}_{code.replace('.', '_')}"
            nodes.append(Node(code=current_area, title=f"{code} {title}".strip(), level=1, parent=ucode))
            current_row = None
            current_head = None
            head_idx = 0
            point_idx = 0
            in_table = False

        def start_row(letter: str, title: str) -> None:
            nonlocal current_row, current_head, head_idx, point_idx
            if not current_area:
                return
            current_row = f"{current_area}_{letter.lower()}"
            nodes.append(Node(code=current_row, title=f"({letter.lower()}) {title}".strip(), level=2, parent=current_area))
            current_head = None
            head_idx = 0
            point_idx = 0

        def start_heading(title: str) -> None:
            nonlocal current_head, head_idx, point_idx
            if not current_row:
                return
            head_idx += 1
            current_head = f"{current_row}_H{head_idx:02d}"
            nodes.append(Node(code=current_head, title=title, level=3, parent=current_row))
            point_idx = 0

        def add_point(text_line: str) -> None:
            nonlocal point_idx
            parent = current_head or current_row
            if not parent:
                return
            point_idx += 1
            lvl = 4 if current_head else 3
            nodes.append(Node(code=f"{parent}_P{point_idx:02d}", title=text_line, level=lvl, parent=parent))

        i = 0
        while i < len(block):
            s = _norm(block[i])
            if not s or _looks_like_header_footer(s):
                i += 1
                continue

            if s.upper().startswith(("3 ASSESSMENT", "4 MALPRACTICE", "5 TECHNICAL INFORMATION", "APPENDIX")):
                break

            m_area = area_re.match(s)
            if m_area and not s.lower().startswith(("content", "amplification")):
                # area heading
                start_area(m_area.group(1), m_area.group(2))
                i += 1
                continue

            if content_amp_re.match(s):
                in_table = True
                i += 1
                continue

            if in_table:
                mrow = row_re.match(s)
                if mrow:
                    # flush any pending row title
                    if pending_row_letter and pending_row_title_parts:
                        start_row(pending_row_letter, _norm(" ".join(pending_row_title_parts)))
                        pending_row_letter = None
                        pending_row_title_parts = []

                    letter = mrow.group(1)
                    rest = _norm(mrow.group(2) or "")
                    if rest:
                        start_row(letter, rest)
                    else:
                        pending_row_letter = letter
                        pending_row_title_parts = []
                    i += 1
                    continue

                if pending_row_letter:
                    # collect row title lines until we hit a sentence (.) or a learner heading/bullet/next row/next area
                    if learners_re.match(s) or bullet_re.match(s) or row_re.match(s) or area_re.match(s) or content_amp_re.match(s):
                        # no title found; fallback
                        start_row(pending_row_letter, "Content")
                        pending_row_letter = None
                        pending_row_title_parts = []
                        continue
                    # stop title when we hit an obvious sentence
                    if "." in s:
                        # end title; start row with collected title (or fallback), then treat this as content line
                        title = _norm(" ".join(pending_row_title_parts)) or "Content"
                        start_row(pending_row_letter, title)
                        pending_row_letter = None
                        pending_row_title_parts = []
                        # fallthrough to treat current line as content
                    else:
                        pending_row_title_parts.append(s)
                        i += 1
                        continue

                if learners_re.match(s) or s.endswith(":"):
                    start_heading(s)
                    i += 1
                    continue

                bm = bullet_re.match(s)
                if bm:
                    add_point(_norm(bm.group(1)))
                    i += 1
                    continue

                # prose line
                add_point(s)
                i += 1
                continue

            i += 1

        # flush pending row at end
        if pending_row_letter:
            start_row(pending_row_letter, _norm(" ".join(pending_row_title_parts)) or "Content")

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
    print("WJEC GCE AS/A LEVEL BUILT ENVIRONMENT - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/A-Level/topics/debug-wjec-1509-built-environment-spec.txt")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}\n")

    nodes = parse_built_environment(text)

    counts: dict[int, int] = {}
    for n in nodes:
        counts[n.level] = counts.get(n.level, 0) + 1
    print("[INFO] Level breakdown:")
    for lvl in sorted(counts):
        print(f"  - L{lvl}: {counts[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("\n[OK] WJEC Built Environment (A-Level) topics scrape complete.")


if __name__ == "__main__":
    main()






