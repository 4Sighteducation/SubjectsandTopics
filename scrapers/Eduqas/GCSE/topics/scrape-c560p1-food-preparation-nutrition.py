"""
Eduqas GCSE Food Preparation and Nutrition (Component 1 only) - Topics Scraper

Spec:
  https://www.eduqas.co.uk/media/4zjdq104/eduqas-gcse-food-preparation-nutrition-spec-from-2016.pdf

Entry codes referenced in spec include: C560P1 / C560P2.
We scrape ONLY Component 1: Principles of Food Preparation and Nutrition.

User requirements:
- Upload to BOTH EDUQAS and WJEC (same content, separate subjects).
- L0: Component 1: Principles of Food Preparation and Nutrition
- L1: The six Areas of Content:
    1. Food commodities  (special case: not a 2-col table; create 3 L2s)
    2. Principles of nutrition
    3. Diet and good health
    4. The science of food
    5. Where food comes from
    6. Cooking and food preparation
- For (1) Food commodities create L2s:
    a) What are the Food Groups?
    b) Understand the Food Group
    c) Applying the Food Groups
- For (2) Principles of nutrition: split Macronutrients vs Micronutrients as separate L2s (ignore the left label)
- For other areas: treat the left-column headings (e.g., "Energy requirements of individuals") as L2s.
  Keep text together; avoid splitting large statements into many tiny topics.
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


PDF_URL = "https://www.eduqas.co.uk/media/4zjdq104/eduqas-gcse-food-preparation-nutrition-spec-from-2016.pdf"

SUBJECTS = [
    {
        "exam_board": "EDUQAS",
        "code": "EDUQAS-C560P1",
        "name": "Food Preparation and Nutrition",
        "qualification": "GCSE",
        "pdf_url": PDF_URL,
    },
    {
        "exam_board": "WJEC",
        "code": "WJEC-C560P1",
        "name": "Food and Nutrition",
        "qualification": "GCSE",
        "pdf_url": PDF_URL,
    },
]


def _force_utf8_stdio() -> None:
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def download_pdf_text(url: str) -> list[str]:
    print("[INFO] Downloading PDF...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    reader = PdfReader(BytesIO(resp.content))
    print(f"[OK] Downloaded {len(reader.pages)} pages")
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    return [ln.rstrip() for ln in text.split("\n")]


SECTION_TITLES = [
    (1, "Food commodities"),
    (2, "Principles of nutrition"),
    (3, "Diet and good health"),
    (4, "The science of food"),
    (5, "Where food comes from"),
    (6, "Cooking and food preparation"),
]


def build_nodes(lines: list[str]) -> list[Node]:
    nodes: list[Node] = []
    seen: set[str] = set()

    def add(code: str, title: str, level: int, parent: Optional[str]) -> None:
        if code in seen:
            return
        nodes.append(Node(code=code, title=title, level=level, parent=parent))
        seen.add(code)

    # Find the *real* section starts (ignore earlier contents list by taking the last occurrence before/within content)
    def find_section_starts() -> dict[int, int]:
        starts: dict[int, int] = {}
        for n, title in SECTION_TITLES:
            # Some headings omit the dot (e.g. "5 Where food comes from")
            pat = re.compile(rf"^\s*{n}\.?\s+{re.escape(title)}\s*$", flags=re.I)
            idxs = [i for i, ln in enumerate(lines) if pat.match(_norm(ln))]
            if not idxs:
                continue
            # choose the last occurrence (the earlier ones are the Areas of Content list)
            starts[n] = idxs[-1]
        return starts

    starts = find_section_starts()
    if 1 not in starts or 2 not in starts:
        raise RuntimeError("Could not locate content section starts for Food spec.")

    # Determine end of section 6 (stop at Appendices / Assessment / end)
    end_all = len(lines)
    for i in range(starts.get(6, starts[2]) + 1, len(lines)):
        s = _norm(lines[i])
        if s.lower().startswith("appendix") or s.lower().startswith("assessment") or s.startswith("3 Assessment"):
            end_all = i
            break

    # L0 component shell
    l0 = "C1"
    add(l0, "Component 1: Principles of Food Preparation and Nutrition", 0, None)

    def slice_for(n: int) -> list[str]:
        if n not in starts:
            return []
        start = starts[n]
        # end at next section start or end_all
        next_start = end_all
        for m, _t in SECTION_TITLES:
            if m > n and m in starts:
                next_start = min(next_start, starts[m])
        return lines[start:next_start]

    # Helpers for bullets/roman
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7]\s*(.+)$")
    roman_re = re.compile(r"^\(?([ivx]+)\)?\s*(.+)$", flags=re.I)  # (i) ...

    def emit_bullets(parent_code: str, text_lines: list[str], base_code: str) -> None:
        idx = 0
        cur_parts: list[str] = []

        def flush() -> None:
            nonlocal idx, cur_parts
            if cur_parts:
                idx += 1
                add(f"{base_code}_{idx:02d}", _norm(" ".join(cur_parts)), 3, parent_code)
                cur_parts = []

        for raw in text_lines:
            s = raw.strip()
            if not s:
                flush()
                continue
            bm = bullet_re.match(s)
            if bm:
                flush()
                idx += 1
                add(f"{base_code}_B{idx:02d}", _norm(bm.group(1)), 3, parent_code)
                continue
            # treat roman lines as distinct items
            if s.startswith("(") and ")" in s[:6]:
                flush()
                idx += 1
                add(f"{base_code}_R{idx:02d}", _norm(s), 3, parent_code)
                continue
            cur_parts.append(s)
        flush()

    # Section 1: Food commodities (manual L2s)
    sec1 = slice_for(1)
    s1_code = "S1"
    add(s1_code, "1. Food commodities", 1, l0)

    # Partition section 1 into three logical blocks
    # a) food groups bullets after intro paragraph until "For each food commodity learners need to know and understand:"
    i_know = next((i for i, ln in enumerate(sec1) if "need to know and understand" in _norm(ln).lower()), None)
    i_able = next((i for i, ln in enumerate(sec1) if "need to be able to" in _norm(ln).lower()), None)
    if i_know is None or i_able is None:
        i_know = len(sec1)
        i_able = len(sec1)

    # Extract food groups bullets (between first bullet and i_know)
    group_lines: list[str] = []
    for ln in sec1:
        if bullet_re.match(ln.strip()):
            group_lines.append(ln)
        elif group_lines and _norm(ln).lower().startswith("for each food commodity learners need to know"):
            break

    l2a = f"{s1_code}_A"
    add(l2a, "a) What are the Food Groups?", 2, s1_code)
    emit_bullets(l2a, group_lines, f"{l2a}_L3")

    # b) know and understand bullets
    know_lines = [ln for ln in sec1[i_know:i_able] if bullet_re.match(ln.strip())]
    l2b = f"{s1_code}_B"
    add(l2b, "b) Understand the Food Group", 2, s1_code)
    emit_bullets(l2b, know_lines, f"{l2b}_L3")

    # c) be able to bullets (from i_able onwards)
    able_lines = [ln for ln in sec1[i_able:] if bullet_re.match(ln.strip())]
    l2c = f"{s1_code}_C"
    add(l2c, "c) Applying the Food Groups", 2, s1_code)
    emit_bullets(l2c, able_lines, f"{l2c}_L3")

    # Section 2: Principles of nutrition (Macronutrients vs Micronutrients)
    sec2 = slice_for(2)
    s2_code = "S2"
    add(s2_code, "2. Principles of nutrition", 1, l0)

    # Split into macro/micro blocks
    macro_start = next((i for i, ln in enumerate(sec2) if _norm(ln).startswith("Macronutrients are defined")), None)
    micro_start = next((i for i, ln in enumerate(sec2) if _norm(ln).startswith("Micronutrients are required")), None)
    if macro_start is None:
        macro_start = 0
    if micro_start is None:
        micro_start = len(sec2)

    # L2: Macronutrients / Micronutrients
    l2_macro = f"{s2_code}_MACRO"
    add(l2_macro, "Macronutrients", 2, s2_code)
    macro_lines = sec2[macro_start:micro_start]
    emit_bullets(l2_macro, macro_lines, f"{l2_macro}_L3")

    l2_micro = f"{s2_code}_MICRO"
    add(l2_micro, "Micronutrients", 2, s2_code)
    micro_lines = sec2[micro_start:]
    emit_bullets(l2_micro, micro_lines, f"{l2_micro}_L3")

    # Generic parser for sections 3-6 using subheading blocks before "Learners must..."
    trigger_re = re.compile(r"^Learners\s+(must\s+know\s+and\s+understand|should\s+be\s+able)", flags=re.I)
    section_hdr_re = re.compile(r"^\s*([3-6])\.\s+(.+)$")

    def parse_section_generic(n: int, sec_lines: list[str]) -> None:
        s_code = f"S{n}"
        add(s_code, f"{n}. {dict(SECTION_TITLES).get(n, '')}".strip(), 1, l0)

        # Start after heading line
        start_idx = 0
        for i, ln in enumerate(sec_lines):
            if section_hdr_re.match(_norm(ln)):
                start_idx = i + 1
                break

        heading_buf: list[str] = []
        current_l2: Optional[str] = None
        l2_idx = 0
        content_buf: list[str] = []

        def flush_content() -> None:
            nonlocal content_buf
            if current_l2 and content_buf:
                emit_bullets(current_l2, content_buf, f"{current_l2}_L3")
            content_buf = []

        for ln in sec_lines[start_idx:]:
            s = ln.strip()
            if not s:
                continue
            # stop if next section begins
            if re.match(r"^\s*[4-7]\.\s+", _norm(s)) and n != 6:
                break

            if trigger_re.match(_norm(s)):
                # finalize heading as L2
                if heading_buf:
                    flush_content()
                    l2_idx += 1
                    title = _norm(" ".join(heading_buf))
                    current_l2 = f"{s_code}_H{l2_idx:02d}"
                    add(current_l2, title, 2, s_code)
                    heading_buf = []
                # include the trigger line as content (often useful)
                content_buf.append(s)
                continue

            # If we don't have an L2 yet, we're still collecting heading lines
            if current_l2 is None and not bullet_re.match(s) and not s.startswith("("):
                heading_buf.append(s)
                continue

            # Otherwise, treat as content line under current L2
            if current_l2:
                content_buf.append(s)

        flush_content()

    for n in (3, 4, 5, 6):
        sec = slice_for(n)
        if sec:
            parse_section_generic(n, sec)

    return nodes


def upload_to_staging(*, subject: dict, nodes: list[Node]) -> None:
    env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
    load_dotenv(env_path)
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    subject_result = supabase.table("staging_aqa_subjects").upsert(
        {
            "subject_name": subject["name"],
            "subject_code": subject["code"],
            "qualification_type": subject["qualification"],
            "specification_url": subject["pdf_url"],
            "exam_board": subject["exam_board"],
        },
        on_conflict="subject_code,qualification_type,exam_board",
    ).execute()
    subject_id = subject_result.data[0]["id"]
    print(f"[OK] Subject ID: {subject_id} ({subject['exam_board']})")

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

    payload = [
        {
            "subject_id": subject_id,
            "topic_code": n.code,
            "topic_name": n.title,
            "topic_level": n.level,
            "exam_board": subject["exam_board"],
        }
        for n in nodes
    ]
    inserted_rows: list[dict] = []
    INS_BATCH = 500
    for i in range(0, len(payload), INS_BATCH):
        res = supabase.table("staging_aqa_topics").insert(payload[i : i + INS_BATCH]).execute()
        inserted_rows.extend(res.data or [])
    print(f"[OK] Uploaded {len(inserted_rows)} topics")

    code_to_id = {row["topic_code"]: row["id"] for row in inserted_rows}
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


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("EDUQAS/WJEC GCSE FOOD PREPARATION & NUTRITION (C560P1) - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {PDF_URL}")

    lines = download_pdf_text(PDF_URL)
    nodes = build_nodes(lines)

    by_level: dict[int, int] = {}
    for n in nodes:
        by_level[n.level] = by_level.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(by_level):
        print(f"  - L{lvl}: {by_level[lvl]}")

    for subj in SUBJECTS:
        print(f"\n[INFO] Uploading for exam_board={subj['exam_board']} code={subj['code']} ...")
        upload_to_staging(subject=subj, nodes=nodes)

    print("[OK] Food Prep & Nutrition scrape complete (uploaded to EDUQAS + WJEC).")


if __name__ == "__main__":
    main()


