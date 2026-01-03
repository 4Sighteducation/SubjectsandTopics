"""
Eduqas/WJEC A Level Physics (spec from 2015) - Topics Scraper (topic headings + (a)/(b) statements, max depth L3)

Spec:
  https://www.eduqas.co.uk/media/1gjjlldz/eduqas-a-level-physics-spec-from-2015-e-2310.pdf

Entry code in spec: A420QS

Requested structure:
  - Use the real topic headings in the text (e.g., "1. BASIC PHYSICS", "2. KINEMATICS", ...)
  - ONLY scrape the content under the sections:
      "Learners should be able to demonstrate and apply their knowledge and understanding of:"
    (do not scrape that header text itself)
  - Also include "SPECIFIED PRACTICAL WORK" bullets under each topic.

Implementation:
  - L0: Component blocks detected by ALL-CAPS component headings with a following "Written examination" line.
        (If not detected, everything goes under a single L0 "Physics".)
  - L1: Topic headings like "1. BASIC PHYSICS"
  - L2: (a)/(b)/(c)... statements (joined across wrapped lines)
  - L2: "Specified practical work" + L3 bullets
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


BASE_SUBJECT = {
    "name": "Physics",
    "qualification": "A-Level",
    "pdf_url": "https://www.eduqas.co.uk/media/1gjjlldz/eduqas-a-level-physics-spec-from-2015-e-2310.pdf",
}

SUBJECTS = [
    {**BASE_SUBJECT, "code": "EDUQAS-A420QS", "exam_board": "EDUQAS"},
    {**BASE_SUBJECT, "code": "WJEC-A420QS", "exam_board": "WJEC"},
]


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
    if "© WJEC" in s or "WJEC CBAC" in s:
        return True
    if s.startswith("A LEVEL PHYSICS"):
        return True
    if re.fullmatch(r"\d{1,3}", s):
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

    deleted_total = 0
    BATCH = 200
    for lvl in range(7, -1, -1):
        while True:
            rows = (
                supabase.table("staging_aqa_topics")
                .select("id")
                .eq("subject_id", subject_id)
                .eq("exam_board", subject["exam_board"])
                .eq("topic_level", lvl)
                .limit(BATCH)
                .execute()
                .data
                or []
            )
            if not rows:
                break
            ids = [r["id"] for r in rows]
            res = supabase.table("staging_aqa_topics").delete().in_("id", ids).execute()
            deleted_total += len(res.data or [])
    print(f"[OK] Cleared old topics ({deleted_total} rows)")

    inserted = (
        supabase.table("staging_aqa_topics")
        .insert(
            [
                {
                    "subject_id": subject_id,
                    "topic_code": n.code,
                    "topic_name": n.title,
                    "topic_level": n.level,
                    "exam_board": subject["exam_board"],
                }
                for n in nodes
            ]
        )
        .execute()
    )
    print(f"[OK] Uploaded {len(inserted.data)} topics")

    code_to_id = {row["topic_code"]: row["id"] for row in inserted.data}
    linked = 0
    for n in nodes:
        if not n.parent:
            continue
        child_id = code_to_id.get(n.code)
        parent_id = code_to_id.get(n.parent)
        if child_id and parent_id:
            supabase.table("staging_aqa_topics").update({"parent_topic_id": parent_id}).eq("id", child_id).execute()
            linked += 1
    print(f"[OK] Linked {linked} relationships")


def build_nodes(pdf_text: str) -> list[Node]:
    raw_lines = [ln.rstrip("\n") for ln in (pdf_text or "").splitlines()]
    lines = [_norm(ln) for ln in raw_lines]
    lines = [ln for ln in lines if ln and not _looks_like_header_footer(ln)]

    # Detect component headings in caps followed by "Written examination"
    comp_title_re = re.compile(r"^[A-Z][A-Z\s&]+$")
    written_re = re.compile(r"^Written examination:", re.I)
    comp_blocks: list[tuple[str, int]] = []
    for i in range(len(lines) - 1):
        if comp_title_re.match(lines[i]) and written_re.match(lines[i + 1]):
            comp_blocks.append((lines[i], i))

    # De-dupe consecutive duplicates
    dedup: list[tuple[str, int]] = []
    seen_titles = set()
    for title, idx in comp_blocks:
        if title not in seen_titles:
            dedup.append((title, idx))
            seen_titles.add(title)
    comp_blocks = sorted(dedup, key=lambda x: x[1])

    nodes: list[Node] = []

    if not comp_blocks:
        nodes.append(Node(code="C0", title="Physics", level=0, parent=None))
        comp_blocks = [("Physics", 0)]

    # Topic headings like: "1.  BASIC PHYSICS" or "2. KINEMATICS"
    topic_re = re.compile(r"^(\d+)\.\s+([A-Z].+)$")
    letter_re = re.compile(r"^\(([a-z])\)\s+(.+)$")
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7\uF0B7\u2023]\s*(.+)$")

    learners_head_re = re.compile(r"^Learners should be able to demonstrate and apply their knowledge and$", re.I)
    learners_head2_re = re.compile(r"^Learners should be able to demonstrate and apply their knowledge and", re.I)
    learners_understanding_re = re.compile(r"^understanding of:", re.I)

    spw_re = re.compile(r"^SPECIFIED PRACTICAL WORK$", re.I)

    # Build component node list with ranges
    comp_ranges: list[tuple[str, str, int, int]] = []
    for ci, (title, start) in enumerate(comp_blocks):
        code = f"C{ci+1}"
        nodes.append(Node(code=code, title=_norm(title.title()), level=0, parent=None))
        end = comp_blocks[ci + 1][1] if ci + 1 < len(comp_blocks) else len(lines)
        comp_ranges.append((code, title, start, end))

    for comp_code, _, start, end in comp_ranges:
        block = lines[start:end]

        current_topic_code: Optional[str] = None
        topic_idx = 0

        in_learners = False
        current_stmt_code: Optional[str] = None
        stmt_parts: list[str] = []
        letter_counts: dict[str, int] = {}

        spw_parent: Optional[str] = None
        spw_bi = 0

        def flush_stmt() -> None:
            nonlocal current_stmt_code, stmt_parts
            if current_topic_code and current_stmt_code and stmt_parts:
                nodes.append(Node(code=current_stmt_code, title=_norm(" ".join(stmt_parts)), level=2, parent=current_topic_code))
            current_stmt_code = None
            stmt_parts = []

        for i, ln in enumerate(block):
            # topic header
            tm = topic_re.match(ln)
            if tm and ln.upper() == ln:
                flush_stmt()
                in_learners = False
                spw_parent = None
                spw_bi = 0
                letter_counts = {}
                topic_idx += 1
                title = _norm(f"{tm.group(1)}. {tm.group(2).title()}")
                current_topic_code = f"{comp_code}_T{topic_idx:02d}"
                nodes.append(Node(code=current_topic_code, title=title, level=1, parent=comp_code))
                continue

            if not current_topic_code:
                continue

            # learners header lines (skip)
            if learners_head_re.match(ln) or learners_head2_re.match(ln):
                flush_stmt()
                in_learners = True
                continue
            if in_learners and learners_understanding_re.match(ln):
                continue

            # specified practical work
            if spw_re.match(ln):
                flush_stmt()
                spw_parent = f"{current_topic_code}_SPW"
                nodes.append(Node(code=spw_parent, title="Specified practical work", level=2, parent=current_topic_code))
                spw_bi = 0
                in_learners = False
                continue

            if spw_parent:
                bm = bullet_re.match(ln)
                if bm:
                    spw_bi += 1
                    nodes.append(Node(code=f"{spw_parent}_B{spw_bi:03d}", title=_norm(bm.group(1)), level=3, parent=spw_parent))
                continue

            if not in_learners:
                continue

            # (a) statements
            lm = letter_re.match(ln)
            if lm:
                flush_stmt()
                letter = lm.group(1)
                letter_counts[letter] = letter_counts.get(letter, 0) + 1
                suffix = "" if letter_counts[letter] == 1 else f"_D{letter_counts[letter]:02d}"
                current_stmt_code = f"{current_topic_code}_{letter}{suffix}"
                stmt_parts = [lm.group(2)]
                continue

            # wrapped continuation for current statement
            if current_stmt_code:
                # stop if we hit another heading
                if ln.upper() == "OVERVIEW" or ln.upper() == "WORKING SCIENTIFICALLY":
                    flush_stmt()
                    in_learners = False
                    continue
                stmt_parts.append(ln)

        flush_stmt()

    if len(nodes) <= 1:
        raise RuntimeError("No Physics topics parsed.")

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("EDUQAS/WJEC A LEVEL PHYSICS - TOPICS SCRAPER (L0-L3)")
    print("=" * 80)
    print(f"Spec: {BASE_SUBJECT['pdf_url']}")

    pdf_text = download_pdf_text(BASE_SUBJECT["pdf_url"])
    nodes = build_nodes(pdf_text)

    by_level: dict[int, int] = {}
    for n in nodes:
        by_level[n.level] = by_level.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(by_level):
        print(f"  - L{lvl}: {by_level[lvl]}")

    for subj in SUBJECTS:
        print(f"\n[INFO] Uploading for exam_board={subj['exam_board']} code={subj['code']} ...")
        upload_to_staging(subject=subj, nodes=nodes)

    print("[OK] Physics (A-Level) scrape complete (uploaded to EDUQAS + WJEC).")


if __name__ == "__main__":
    main()






