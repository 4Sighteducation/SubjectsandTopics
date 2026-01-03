"""
Eduqas/WJEC A Level Physical Education (spec from 2016) - Topics Scraper (table-based, max depth L3)

Spec:
  https://www.eduqas.co.uk/media/avjhdg4g/eduqas-a-level-physical-education-spec-from-2016-e-07-08-2020.pdf

Entry code in spec: A550QS

Requested structure:
  - L0: Areas of study (1..5)
  - L2: Bold heading of each table row cell (we approximate as the first line of the Content cell)
  - L3: Each separate paragraph under that heading (Content paragraphs + Amplification paragraphs)

Notes:
  - We use pdfplumber + word-bucketing because table extraction often returns blank cells.
  - We only scrape the two-column Subject Content tables (Content / Amplification), and ignore
    assessment/appendix/activity-list tables.
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

import pdfplumber
import requests
from dotenv import load_dotenv
from supabase import create_client


@dataclass(frozen=True)
class Node:
    code: str
    title: str
    level: int
    parent: Optional[str]


BASE_SUBJECT = {
    "name": "Physical Education",
    "qualification": "A-Level",
    "pdf_url": "https://www.eduqas.co.uk/media/avjhdg4g/eduqas-a-level-physical-education-spec-from-2016-e-07-08-2020.pdf",
}

SUBJECTS = [
    {**BASE_SUBJECT, "code": "EDUQAS-A550QS", "exam_board": "EDUQAS"},
    {**BASE_SUBJECT, "code": "WJEC-A550QS", "exam_board": "WJEC"},
]

AREA_TITLES = [
    "1. Exercise physiology, training and performance",
    "2. Movement analysis, technology and biomechanics",
    "3. Sport psychology",
    "4. Skill acquisition",
    "5. Sport and society",
]


def _force_utf8_stdio() -> None:
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def download_pdf(url: str) -> bytes:
    print("[INFO] Downloading PDF...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.content


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


def build_nodes(pdf_bytes: bytes) -> list[Node]:
    nodes: list[Node] = []
    area_codes = []
    for i, title in enumerate(AREA_TITLES, 1):
        code = f"A{i}"
        area_codes.append(code)
        nodes.append(Node(code=code, title=title, level=0, parent=None))

    def words_in_bbox(words: list[dict], bbox: tuple[float, float, float, float]) -> list[dict]:
        x0, top, x1, bottom = bbox
        return [w for w in words if w["x0"] >= x0 and w["x1"] <= x1 and w["top"] >= top and w["bottom"] <= bottom]

    def lines_with_tops(words: list[dict], *, xmin: float, xmax: float, y_tol: float = 2.5) -> list[tuple[float, str]]:
        ws = [w for w in words if xmin <= w["x0"] < xmax]
        ws.sort(key=lambda w: (w["top"], w["x0"]))
        out: list[tuple[float, str]] = []
        cur_top: Optional[float] = None
        cur_parts: list[str] = []
        for w in ws:
            top = w["top"]
            if cur_top is None or abs(top - cur_top) > y_tol:
                if cur_parts:
                    out.append((cur_top if cur_top is not None else top, " ".join(cur_parts).strip()))
                cur_top = top
                cur_parts = [w["text"]]
            else:
                cur_parts.append(w["text"])
        if cur_parts:
            out.append((cur_top if cur_top is not None else 0.0, " ".join(cur_parts).strip()))
        return [(t, _norm(s)) for t, s in out if _norm(s)]

    def paragraphs_from_lines(lines: list[tuple[float, str]], gap: float = 14.0) -> list[str]:
        if not lines:
            return []
        paras: list[list[str]] = [[lines[0][1]]]
        last_top = lines[0][0]
        for top, txt in lines[1:]:
            if (top - last_top) > gap:
                paras.append([txt])
            else:
                paras[-1].append(txt)
            last_top = top
        return [_norm(" ".join(p)) for p in paras if _norm(" ".join(p))]

    # Track current area based on page text headings.
    current_area = "A1"
    # Stable counters per area so topic_codes are unique across tables/pages.
    area_row_idx: dict[str, int] = {f"A{i}": 0 for i in range(1, 6)}

    area_heading_re = re.compile(r"^([1-5])\.\s+(.+)$")

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        print(f"[OK] PDF pages: {len(pdf.pages)}")
        for page in pdf.pages:
            text = page.extract_text() or ""
            # update area if present on this page
            for ln in (text.splitlines() if text else []):
                m = area_heading_re.match(_norm(ln))
                if m:
                    n = int(m.group(1))
                    if 1 <= n <= 5:
                        current_area = f"A{n}"

            words = page.extract_words() or []
            tables = page.find_tables() or []
            if not tables:
                continue

            for t in tables:
                if not t.rows or len(t.rows) < 2:
                    continue
                hdr_words = words_in_bbox(words, t.rows[0].bbox)
                hdr_texts = {w["text"].lower() for w in hdr_words}
                if "content" not in hdr_texts or "amplification" not in hdr_texts:
                    continue

                content_words = [w for w in hdr_words if w["text"].lower() == "content"]
                amp_words = [w for w in hdr_words if w["text"].lower() == "amplification"]
                if not content_words or not amp_words:
                    continue

                # derive split between columns from header positions
                max_content_x1 = max(w["x1"] for w in content_words)
                min_amp_x0 = min(w["x0"] for w in amp_words)
                mid = (max_content_x1 + min_amp_x0) / 2.0
                left, top, right, bottom = t.bbox

                # Parse each row: L2 heading from first line of content col, L3 paragraphs from both cols.
                for r in t.rows[1:]:
                    row_words = words_in_bbox(words, r.bbox)
                    if not row_words:
                        continue
                    c_lines = lines_with_tops(row_words, xmin=left, xmax=mid)
                    a_lines = lines_with_tops(row_words, xmin=mid, xmax=right)
                    if not c_lines:
                        continue
                    # Build content paragraphs; first paragraph acts as the (possibly multi-line) heading.
                    paras_c_all = paragraphs_from_lines(c_lines)
                    if not paras_c_all:
                        continue
                    heading = paras_c_all[0]
                    # ignore header rows that sometimes repeat
                    if heading.lower() in {"content", "amplification"}:
                        continue

                    paras_c = paras_c_all[1:]
                    paras_a = paragraphs_from_lines(a_lines)

                    # Sometimes the first content line is not actually the bold heading; if it's too short, merge.
                    if len(heading) < 6 and paras_c:
                        heading = _norm(f"{heading} {paras_c[0]}")
                        paras_c = paras_c[1:]

                    area_row_idx[current_area] += 1
                    l2 = f"{current_area}_H{area_row_idx[current_area]:03d}"
                    nodes.append(Node(code=l2, title=heading, level=2, parent=current_area))

                    p_idx = 0
                    for p in paras_c:
                        if not p:
                            continue
                        p_idx += 1
                        nodes.append(Node(code=f"{l2}_P{p_idx:03d}", title=p, level=3, parent=l2))
                    for p in paras_a:
                        if not p:
                            continue
                        p_idx += 1
                        nodes.append(Node(code=f"{l2}_P{p_idx:03d}", title=f"(Amplification) {p}", level=3, parent=l2))

    if len(nodes) <= 5:
        raise RuntimeError("No PE content tables parsed (only area shells).")

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("EDUQAS/WJEC A LEVEL PHYSICAL EDUCATION - TOPICS SCRAPER (L0/L2/L3)")
    print("=" * 80)
    print(f"Spec: {BASE_SUBJECT['pdf_url']}")

    pdf_bytes = download_pdf(BASE_SUBJECT["pdf_url"])
    nodes = build_nodes(pdf_bytes)

    by_level: dict[int, int] = {}
    for n in nodes:
        by_level[n.level] = by_level.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(by_level):
        print(f"  - L{lvl}: {by_level[lvl]}")

    for subj in SUBJECTS:
        print(f"\n[INFO] Uploading for exam_board={subj['exam_board']} code={subj['code']} ...")
        upload_to_staging(subject=subj, nodes=nodes)

    print("[OK] Physical Education (A-Level) scrape complete (uploaded to EDUQAS + WJEC).")


if __name__ == "__main__":
    main()


