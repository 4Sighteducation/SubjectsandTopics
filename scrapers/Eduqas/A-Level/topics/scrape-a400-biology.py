"""
Eduqas/WJEC A Level Biology (spec from 2015) - Topics Scraper (component topics + (a)/(b) statements, max depth L3)

Spec:
  https://www.eduqas.co.uk/media/2ltc54x1/eduqas-a-level-biology-spec-from-2015-e-1410.pdf

Entry code in spec: A400QS

Structure (deterministic):
  - L0: Component 1/2/3 (Energy for Life / Continuity of Life / Requirements for Life)
  - L1: Topic within component (e.g., "1. Importance of ATP")
  - L2: Learners-should statements (a),(b),(c)...
  - L2: "Specified practical work" (shell)
  - L3: Practical bullets

Ignored:
  - Overview / Working scientifically / Mathematical Skills / How Science Works
  - Appendices / Assessment objectives / admin pages
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
    "name": "Biology",
    "qualification": "A-Level",
    "pdf_url": "https://www.eduqas.co.uk/media/2ltc54x1/eduqas-a-level-biology-spec-from-2015-e-1410.pdf",
}

SUBJECTS = [
    {**BASE_SUBJECT, "code": "EDUQAS-A400QS", "exam_board": "EDUQAS"},
    {**BASE_SUBJECT, "code": "WJEC-A400QS", "exam_board": "WJEC"},
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
    if s.startswith("A LEVEL BIOLOGY"):
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
    lines = [_norm(ln) for ln in (pdf_text or "").splitlines()]
    lines = [ln for ln in lines if ln and not _looks_like_header_footer(ln)]

    # Component anchors (caps in extraction)
    comp_markers = [
        ("C1", "Component 1: Energy for Life", "ENERGY FOR LIFE"),
        ("C2", "Component 2: Continuity of Life", "CONTINUITY OF LIFE"),
        ("C3", "Component 3: Requirements for Life", "REQUIREMENTS FOR LIFE"),
    ]

    # Find component block ranges
    comp_idxs: list[tuple[str, str, int]] = []
    for code, title, marker in comp_markers:
        for i, ln in enumerate(lines):
            if ln == marker:
                comp_idxs.append((code, title, i))
                break
    if len(comp_idxs) != 3:
        raise RuntimeError("Could not locate all Biology component headings (ENERGY/CONTINUITY/REQUIREMENTS).")
    comp_idxs.sort(key=lambda x: x[2])

    blocks: list[tuple[str, str, int, int]] = []
    for idx, (code, title, start) in enumerate(comp_idxs):
        end = comp_idxs[idx + 1][2] if idx + 1 < len(comp_idxs) else len(lines)
        blocks.append((code, title, start, end))

    nodes: list[Node] = []
    for code, title, _, _ in blocks:
        nodes.append(Node(code=code, title=title, level=0, parent=None))

    topic_hdr_re = re.compile(r"^(\d)\.\s+(.+)$")  # 1. Importance of ATP
    letter_re = re.compile(r"^\(([a-z])\)\s+(.+)$")
    spw_re = re.compile(r"^SPECIFIED PRACTICAL WORK$", re.IGNORECASE)
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7\uF0B7\u2023]\s*(.+)$")

    ignore_section_prefixes = (
        "Overview",
        "Working scientifically",
        "Mathematical Skills",
        "How Science Works",
        "Learners will be",
        "The assessment will",
        "This component includes",
        "Written examination",
        "33",
    )

    def is_ignored_line(s: str) -> bool:
        if not s:
            return True
        if any(s.startswith(p) for p in ignore_section_prefixes):
            return True
        return False

    for comp_code, comp_title, start, end in blocks:
        block = lines[start:end]
        comp_topic_context = comp_title.split(": ", 1)[1] if ": " in comp_title else comp_title
        current_topic_code: Optional[str] = None
        current_topic_num: Optional[int] = None
        current_stmt_code: Optional[str] = None
        stmt_parts: list[str] = []
        letter_counts: dict[str, int] = {}

        topic_counter = 0
        spw_counter = 0
        spw_mode = False
        spw_parent_code: Optional[str] = None
        spw_bullet_idx = 0

        def flush_stmt() -> None:
            nonlocal current_stmt_code, stmt_parts
            if current_stmt_code and stmt_parts:
                nodes.append(Node(code=current_stmt_code, title=_norm(" ".join(stmt_parts)), level=2, parent=current_topic_code))
            current_stmt_code = None
            stmt_parts = []

        for i, ln in enumerate(block):
            if is_ignored_line(ln):
                continue

            # new topic heading: appears as "Energy for Life" then "1. ..." etc.
            m_topic = topic_hdr_re.match(ln)
            if m_topic and current_topic_code is None and int(m_topic.group(1)) >= 1:
                # first topic in component might appear after title line; allow
                pass

            if m_topic and int(m_topic.group(1)) >= 1:
                # Require the within-component topic context marker (e.g., "Energy for Life") to appear just before
                # the topic header. This filters out the component summary topic list.
                prev_window = [x for x in block[max(0, i - 6) : i] if x]
                if comp_topic_context not in prev_window:
                    continue
                # Skip the early component topic-list page ("This component includes the following topics: ...")
                # by requiring that an actual topic heading is followed by "Overview" shortly after.
                lookahead = [x for x in block[i : min(i + 6, len(block))] if x]
                if not any(x == "Overview" for x in lookahead):
                    continue
                # ensure this is a topic header in this component (topic numbers are 1..6 etc)
                # Flush any pending statement
                flush_stmt()
                spw_mode = False
                spw_parent_code = None
                spw_bullet_idx = 0

                topic_counter += 1
                topic_title = f"{m_topic.group(1)}. {m_topic.group(2)}"
                current_topic_code = f"{comp_code}_T{topic_counter:02d}"
                letter_counts = {}
                nodes.append(Node(code=current_topic_code, title=topic_title, level=1, parent=comp_code))
                continue

            if not current_topic_code:
                continue

            # Start of learners-should statements (followed by (a),(b)...)
            if ln.lower().startswith("learners should be able to demonstrate and apply their knowledge and understanding of"):
                flush_stmt()
                continue

            # Specified practical work block
            if spw_re.match(ln):
                flush_stmt()
                spw_mode = True
                spw_counter += 1
                spw_parent_code = f"{current_topic_code}_SPW"
                nodes.append(Node(code=spw_parent_code, title="Specified practical work", level=2, parent=current_topic_code))
                spw_bullet_idx = 0
                continue

            # (a) / (b) statements
            m_letter = letter_re.match(ln)
            if m_letter:
                flush_stmt()
                letter = m_letter.group(1)
                letter_counts[letter] = letter_counts.get(letter, 0) + 1
                suffix = "" if letter_counts[letter] == 1 else f"_D{letter_counts[letter]:02d}"
                current_stmt_code = f"{current_topic_code}_{letter}{suffix}"
                stmt_parts = [m_letter.group(2)]
                continue

            # bullets under SPW
            if spw_mode and spw_parent_code:
                bm = bullet_re.match(ln)
                if bm:
                    spw_bullet_idx += 1
                    nodes.append(Node(code=f"{spw_parent_code}_B{spw_bullet_idx:03d}", title=_norm(bm.group(1)), level=3, parent=spw_parent_code))
                continue

            # continuation lines for current statement (wrapped)
            if current_stmt_code:
                # stop if we hit a new section header
                if ln in {"Overview", "Working scientifically", "Mathematical Skills", "How Science Works"}:
                    flush_stmt()
                    continue
                # avoid pulling in other admin headings
                if ln.upper() in {"ENERGY FOR LIFE", "CONTINUITY OF LIFE", "REQUIREMENTS FOR LIFE"}:
                    flush_stmt()
                    current_topic_code = None
                    continue
                # append continuation
                stmt_parts.append(ln)

        flush_stmt()

    if not nodes:
        raise RuntimeError("No Biology topics parsed.")

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("EDUQAS/WJEC A LEVEL BIOLOGY - TOPICS SCRAPER (L0-L3)")
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

    print("[OK] Biology (A-Level) scrape complete (uploaded to EDUQAS + WJEC).")


if __name__ == "__main__":
    main()


