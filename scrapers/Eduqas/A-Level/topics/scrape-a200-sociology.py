"""
Eduqas/WJEC A Level Sociology (spec from 2015) - Topics Scraper (table bullets, max depth L3)

Spec:
  https://www.eduqas.co.uk/media/heonctwb/eduqas-a-level-sociology-spec-from-2015-e-290119.pdf

Entry code in spec: A200QS

Structure (deterministic, aligned to spec tables):
  - L0: Component 1 / Component 2 / Component 3
  - L1: Section (A/B/C) or major content areas
  - L2: Content headings (from left table column) or Option name
  - L3: Amplification bullets (from right table column)
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
    "name": "Sociology",
    "qualification": "A-Level",
    "pdf_url": "https://www.eduqas.co.uk/media/heonctwb/eduqas-a-level-sociology-spec-from-2015-e-290119.pdf",
}

SUBJECTS = [
    {**BASE_SUBJECT, "code": "EDUQAS-A200QS", "exam_board": "EDUQAS"},
    {**BASE_SUBJECT, "code": "WJEC-A200QS", "exam_board": "WJEC"},
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
    if s.startswith("A LEVEL SOCIOLOGY"):
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
    lines = [ln.rstrip("\n") for ln in (pdf_text or "").splitlines()]

    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7\uF0B7\u2023\u2022\u2023\u25E6\u25AA\u25A0\u00B7\u2024\u2043\u2219\u25CB\u25CF\u25A1\u25C6\u25C7\u25C8\u25C9\uF0B7]\s*(.+)$")
    dot_bullet_re = re.compile(r"^[\u2022\uF0B7\u00B7]\s*(.+)$")

    def is_bullet(s: str) -> Optional[str]:
        m = bullet_re.match(s)
        if m:
            return _norm(m.group(1))
        m2 = dot_bullet_re.match(s)
        if m2:
            return _norm(m2.group(1))
        return None

    def skip_line(s: str) -> bool:
        low = s.lower()
        if not s or _looks_like_header_footer(s):
            return True
        if low in {"content amplification", "option amplification", "compulsory", "option", "section a", "section b", "section c"}:
            return True
        if low.startswith("written examination"):
            return True
        if low.startswith("below are the assessment objectives") or low.startswith("ao1") or low.startswith("this is a linear qualification"):
            return True
        return False

    nodes: list[Node] = []

    # L0 components
    c1 = "C1"
    c2 = "C2"
    c3 = "C3"
    nodes.append(Node(code=c1, title="Component 1: Socialisation, identity and culture", level=0, parent=None))
    nodes.append(Node(code=c2, title="Component 2: Methods of sociological enquiry", level=0, parent=None))
    nodes.append(Node(code=c3, title="Component 3: Social differentiation, power and stratification", level=0, parent=None))

    # Find anchors
    idx_c1 = None
    idx_c2 = None
    idx_c3 = None
    idx_end = None
    for i, ln in enumerate(lines):
        s = _norm(ln)
        if not s:
            continue
        if idx_c1 is None and s == "Section A":
            # Component 1 Section A has the Content/Amplification table header shortly after.
            look = " ".join(_norm(x) for x in lines[i : min(len(lines), i + 12)])
            if "Content Amplification" in look:
                idx_c1 = i
        if idx_c2 is None and s.startswith("Written examination: 1 hour 45 minutes"):
            idx_c2 = i
        if idx_c3 is None and s.startswith("Written examination: 2 hours 30 minutes") and "social differentiation" in _norm(" ".join(lines[i : i + 5])).lower():
            idx_c3 = i
        if idx_end is None and s.lower().startswith("below are the assessment objectives"):
            idx_end = i
    if idx_c1 is None:
        raise RuntimeError("Could not locate Component 1 content (Section A table).")
    if idx_c2 is None:
        raise RuntimeError("Could not locate Component 2 (methods) start.")
    if idx_c3 is None:
        raise RuntimeError("Could not locate Component 3 start.")
    if idx_end is None:
        idx_end = len(lines)

    # Component 1: parse sections A, B, C
    c1_lines = lines[idx_c1:idx_c2]
    sec_code = { "A": f"{c1}_SA", "B": f"{c1}_SB", "C": f"{c1}_SC" }
    nodes.append(Node(code=sec_code["A"], title="Section A (Compulsory)", level=1, parent=c1))
    nodes.append(Node(code=sec_code["B"], title="Section B (Option)", level=1, parent=c1))
    nodes.append(Node(code=sec_code["C"], title="Section C (Option)", level=1, parent=c1))

    def parse_table_rows(block_lines: list[str], parent_code: str, code_prefix: str) -> None:
        """Parse 'Content / Amplification' style blocks: heading (left column) then bullet items (right column)."""
        cur_heading_parts: list[str] = []
        cur_heading_code: Optional[str] = None
        h_idx = 0
        b_idx = 0
        cur_bullet_parts: list[str] = []

        def ensure_heading() -> None:
            nonlocal cur_heading_code, h_idx, b_idx, cur_heading_parts
            if cur_heading_code:
                return
            if not cur_heading_parts:
                return
            h_idx += 1
            cur_heading_code = f"{code_prefix}_H{h_idx:02d}"
            heading_title = _norm(" ".join(cur_heading_parts))
            # Sometimes the PDF extraction leaks a bullet glyph into the heading row.
            heading_title = heading_title.split("", 1)[0].split("•", 1)[0].strip()
            nodes.append(Node(code=cur_heading_code, title=heading_title, level=2, parent=parent_code))
            cur_heading_parts = []
            b_idx = 0

        def flush_bullet() -> None:
            nonlocal cur_bullet_parts, b_idx
            if cur_heading_code and cur_bullet_parts:
                b_idx += 1
                nodes.append(Node(code=f"{cur_heading_code}_B{b_idx:03d}", title=_norm(" ".join(cur_bullet_parts)), level=3, parent=cur_heading_code))
            cur_bullet_parts = []

        def reset_heading() -> None:
            nonlocal cur_heading_parts, cur_heading_code, b_idx, cur_bullet_parts
            flush_bullet()
            cur_heading_parts = []
            cur_heading_code = None
            b_idx = 0
            cur_bullet_parts = []

        for raw in block_lines:
            s = _norm(raw)
            if skip_line(s):
                continue

            b = is_bullet(s)
            if b:
                ensure_heading()
                flush_bullet()
                cur_bullet_parts = [b]
                continue

            # Non-bullet line: either heading text (before first bullet) or bullet continuation.
            if cur_bullet_parts:
                # bullet continuation (wrapped line) unless it clearly looks like the next heading
                if s and s[0].isupper():
                    flush_bullet()
                    # start a new heading row
                    cur_heading_code = None
                    cur_heading_parts = [s]
                else:
                    cur_bullet_parts.append(s)
                continue

            if cur_heading_code:
                # start of a NEW heading row
                reset_heading()

            cur_heading_parts.append(s)

        flush_bullet()

    # Slice sections within component 1
    def find_idx(block: list[str], needle: str) -> int:
        for i, ln in enumerate(block):
            if _norm(ln) == needle:
                return i
        return -1

    i_sa = find_idx(c1_lines, "Section A")
    i_sb = find_idx(c1_lines, "Section B")
    i_sc = find_idx(c1_lines, "Section C")
    if i_sa == -1 or i_sb == -1 or i_sc == -1:
        raise RuntimeError("Could not locate Section A/B/C within Component 1.")

    # Section A table rows are between 'Content Amplification' and 'Section B'
    parse_table_rows(c1_lines[i_sa:i_sb], sec_code["A"], f"{sec_code['A']}")

    # Section B options: 'Families and households' and 'Youth cultures'
    def parse_options(block_lines: list[str], parent_code: str, code_prefix: str) -> None:
        opt = None
        opt_code = None
        o_idx = 0
        b_idx = 0
        for raw in block_lines:
            s = _norm(raw)
            if skip_line(s):
                continue
            b = is_bullet(s)
            if b:
                if opt_code:
                    b_idx += 1
                    nodes.append(Node(code=f"{opt_code}_B{b_idx:03d}", title=b, level=3, parent=opt_code))
                continue
            # option name
            low = s.lower()
            if low in {"families and households", "youth cultures", "education", "media", "religion", "crime and deviance", "health and disability", "politics", "world sociology"}:
                o_idx += 1
                opt_code = f"{code_prefix}_O{o_idx:02d}"
                nodes.append(Node(code=opt_code, title=s, level=2, parent=parent_code))
                b_idx = 0
                opt = s
                continue
            # ignore other non-bullet narrative

    parse_options(c1_lines[i_sb:i_sc], sec_code["B"], f"{sec_code['B']}")
    parse_options(c1_lines[i_sc:], sec_code["C"], f"{sec_code['C']}")

    # Component 2: methods
    c2_lines = lines[idx_c2:idx_c3]
    # Start from the first table header to avoid pulling in the preamble as a 'heading'.
    start_tbl = 0
    for i, ln in enumerate(c2_lines):
        if _norm(ln) == "Content Amplification":
            start_tbl = i
            break
    parse_table_rows(c2_lines[start_tbl:], c2, f"{c2}")

    # Component 3: parse Section A bullets + Section B options (Crime/Health/Politics/World)
    c3_lines = lines[idx_c3:idx_end]
    # Section A bullets (immediately after 'Section A')
    c3_sa = f"{c3}_SA"
    nodes.append(Node(code=c3_sa, title="Section A (Compulsory)", level=1, parent=c3))
    c3_sb = f"{c3}_SB"
    nodes.append(Node(code=c3_sb, title="Section B (Option)", level=1, parent=c3))

    # split at Section B
    i_a = None
    i_b = None
    for i, ln in enumerate(c3_lines):
        if _norm(ln) == "Section A":
            i_a = i
        if _norm(ln) == "Section B":
            i_b = i
            break
    if i_a is None:
        raise RuntimeError("Could not locate Component 3 Section A.")
    if i_b is None:
        i_b = len(c3_lines)

    # bullets for section A
    b_idx = 0
    for raw in c3_lines[i_a:i_b]:
        s = _norm(raw)
        if skip_line(s):
            continue
        b = is_bullet(s)
        if b:
            b_idx += 1
            nodes.append(Node(code=f"{c3_sa}_B{b_idx:03d}", title=b, level=2, parent=c3_sa))

    # options for section B (Option Amplification tables)
    parse_options(c3_lines[i_b:], c3_sb, c3_sb)

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("EDUQAS/WJEC A LEVEL SOCIOLOGY - TOPICS SCRAPER (L0-L3)")
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

    print("[OK] Sociology (A-Level) scrape complete (uploaded to EDUQAS + WJEC).")


if __name__ == "__main__":
    main()


