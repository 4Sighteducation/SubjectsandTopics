"""
Eduqas/WJEC A Level Economics (spec from 2015) - Topics Scraper (table-based, reliable)

Spec:
  https://www.eduqas.co.uk/media/odmjnwaa/eduqas-a-economics-spec-from-2015.pdf

Entry code in spec: A520QS

Required structure (as requested):
  - L0: Microeconomics / Macroeconomics / Trade and development  (in this order)
  - L1: "Content" column items (left column)
  - L2: "Amplification" column paragraphs/lines (middle column), split by directive/bullets and
        joined across wrapped lines.

IMPORTANT:
- DO NOT SCRAPE "Additional guidance notes" (third column). We explicitly ignore it.
- Uses `pdfplumber` table extraction to avoid PDF text flow creating fake/truncated topics.
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
    "name": "Economics",
    "qualification": "A-Level",
    "pdf_url": "https://www.eduqas.co.uk/media/odmjnwaa/eduqas-a-economics-spec-from-2015.pdf",
}

SUBJECTS = [
    {**BASE_SUBJECT, "code": "EDUQAS-A520QS", "exam_board": "EDUQAS"},
    {**BASE_SUBJECT, "code": "WJEC-A520QS", "exam_board": "WJEC"},
]

# Force ordering via codes (UI typically sorts by topic_code)
AREAS = [
    ("01_MICRO", "Microeconomics"),
    ("02_MACRO", "Macroeconomics"),
    ("03_TRADE", "Trade and development"),
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

    # Batched delete (deepest-first) to avoid statement timeouts on large trees.
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


_AREA_HEADING_RE = re.compile(
    r"(^|\n)\s*[•\u2022\u25cf\u00b7\uF0B7\u2023\u2022\u25AA\u25A0\u25E6\u25CB\u25CF\u25AA\u25A1\u25C6\u25C7\u25C8\u25C9\u25B6\u25B7\u25B8\u25B9\u25BA\u25BB\u25BC\u25BD\u25BE\u25BF\u25C0\u25C1\u25C2\u25C3\u25C4\u25C5\u25C6\u25C7\u25C8\u25C9\u25CA\u25CB\u25CC\u25CD\u25CE\u25CF\u25D0\u25D1\u25D2\u25D3\u25D4\u25D5\u25D6\u25D7\u25D8\u25D9\u25DA\u25DB\u25DC\u25DD\u25DE\u25DF\u25E0\u25E1\u25E2\u25E3\u25E4\u25E5\u25E6\u25E7\u25E8\u25E9\u25EA\u25EB\u25EC\u25ED\u25EE\u25EF\u25F0\u25F1\u25F2\u25F3\u25F4\u25F5\u25F6\u25F7\u25F8\u25F9\u25FA\u25FB\u25FC\u25FD\u25FE\u25FF\uF0B7]?\s*(Microeconomics|Macroeconomics|Trade and development)\b",
    flags=re.IGNORECASE | re.MULTILINE,
)

_TABLE_HDR_OK = re.compile(r"^\s*content\s*$", flags=re.IGNORECASE)
_DIRECTIVE_START = re.compile(
    r"^(Define|Explain|Use|Understand|Identify|Illustrate|Evaluate|Analyse|Analyze|Calculate|Describe|Compare|Discuss|Assess|Apply|Examine|Relate)\b",
    flags=re.IGNORECASE,
)


def _clean_cell(cell: Optional[str]) -> str:
    s = (cell or "").replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = "\n".join(line.strip() for line in s.splitlines())
    return s.strip()


def _split_amplification(cell_text: str) -> list[str]:
    """
    Turn the Amplification cell into a list of L2 statements.
    In the spec, each new line is typically a new statement.
    We also split when a new line begins with a directive verb.
    """
    lines = [ln.strip() for ln in (cell_text or "").splitlines() if ln.strip()]
    out: list[str] = []
    cur: list[str] = []

    def flush() -> None:
        nonlocal cur
        txt = _norm(" ".join(cur))
        if txt:
            out.append(txt)
        cur = []

    for ln in lines:
        ln2 = re.sub(r"^[•\u2022\u25cf\u00b7\uF0B7\u2023]\s*", "", ln).strip()
        if cur and _DIRECTIVE_START.match(ln2):
            flush()
        cur.append(ln2)
    flush()
    return out


def _classify_area_from_content_title(title: str) -> Optional[str]:
    """
    Assign each Content-row to Micro/Macro/Trade based on keywords in the Content title.
    This is needed because the PDF tables don't always include the section heading on every page.
    """
    t = (title or "").lower()
    trade_keys = (
        "trade",
        "development",
        "global",
        "exchange rate",
        "balance of payments",
        "tariff",
        "quota",
        "protection",
        "wto",
        "imf",
        "world bank",
        "aid",
        "fdi",
        "multinational",
        "terms of trade",
        "comparative advantage",
        "free trade",
    )
    macro_keys = (
        "aggregate",
        "circular flow",
        "national income",
        "gdp",
        "inflation",
        "deflation",
        "unemployment",
        "economic growth",
        "recession",
        "fiscal",
        "monetary",
        "interest rate",
        "central bank",
        "bank of england",
        "phillips",
        "multiplier",
        "budget",
        "public debt",
        "government policy objectives",
    )
    if any(k in t for k in trade_keys):
        return "03_TRADE"
    if any(k in t for k in macro_keys):
        return "02_MACRO"
    return None


def _parse_tables(pdf_bytes: bytes) -> list[Node]:
    nodes: list[Node] = []
    for code, title in AREAS:
        nodes.append(Node(code=code, title=title, level=0, parent=None))

    counters = {code: 0 for code, _ in AREAS}
    current_area: Optional[str] = None
    global_mid1: Optional[float] = None
    global_mid2: Optional[float] = None

    # We'll use table geometry (rows/bbox) from find_tables(), but extract text by bucketing words
    # into 3 columns using header word x-positions. This avoids pdfplumber's cell text extraction
    # returning blanks for the middle/right columns.
    def words_in_bbox(words: list[dict], bbox: tuple[float, float, float, float]) -> list[dict]:
        x0, top, x1, bottom = bbox
        return [w for w in words if w["x0"] >= x0 and w["x1"] <= x1 and w["top"] >= top and w["bottom"] <= bottom]

    def lines_from_words(words: list[dict], *, xmin: float, xmax: float, y_tol: float = 2.5) -> list[str]:
        ws = [w for w in words if xmin <= w["x0"] < xmax]
        ws.sort(key=lambda w: (w["top"], w["x0"]))
        lines: list[list[str]] = []
        last_top: Optional[float] = None
        for w in ws:
            top = w["top"]
            if last_top is None or abs(top - last_top) > y_tol:
                lines.append([w["text"]])
                last_top = top
            else:
                lines[-1].append(w["text"])
        return [" ".join(parts).strip() for parts in lines if parts]

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        print(f"[OK] PDF pages: {len(pdf.pages)}")
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            m = _AREA_HEADING_RE.search(page_text)
            if m:
                heading = m.group(2).lower()
                if heading.startswith("micro"):
                    current_area = "01_MICRO"
                elif heading.startswith("macro"):
                    current_area = "02_MACRO"
                else:
                    current_area = "03_TRADE"

            # default area once we encounter the first content table
            if current_area is None:
                current_area = "01_MICRO"

            words = page.extract_words() or []
            tables = page.find_tables() or []
            if not tables:
                continue

            for t in tables:
                if not t.rows or len(t.rows) < 2:
                    continue
                # Try to derive column splits from header row words, else fall back to global splits.
                hdr_row = t.rows[0]
                hdr_words = words_in_bbox(words, hdr_row.bbox)
                texts = {w["text"].lower() for w in hdr_words}

                mid1 = None
                mid2 = None
                has_header = False
                if "content" in texts and "amplification" in texts and "additional" in texts:
                    content_w = [w for w in hdr_words if w["text"].lower() == "content"]
                    amp_w = [w for w in hdr_words if w["text"].lower() == "amplification"]
                    add_w = [w for w in hdr_words if w["text"].lower() == "additional"]
                    if content_w and amp_w and add_w:
                        max_content_x1 = max(w["x1"] for w in content_w)
                        min_amp_x0 = min(w["x0"] for w in amp_w)
                        max_amp_x1 = max(w["x1"] for w in amp_w)
                        min_add_x0 = min(w["x0"] for w in add_w)
                        mid1 = (max_content_x1 + min_amp_x0) / 2.0
                        mid2 = (max_amp_x1 + min_add_x0) / 2.0
                        if global_mid1 is None or global_mid2 is None:
                            global_mid1, global_mid2 = mid1, mid2
                        has_header = True

                if mid1 is None or mid2 is None:
                    if global_mid1 is None or global_mid2 is None:
                        # can't reliably split columns on this table
                        continue
                    mid1, mid2 = global_mid1, global_mid2

                left, top, right, bottom = t.bbox

                table_words = words_in_bbox(words, (left, top, right, bottom))

                def emit_row(row_bbox: tuple[float, float, float, float]) -> None:
                    row_words = words_in_bbox(table_words, row_bbox)
                    c_lines = lines_from_words(row_words, xmin=left, xmax=mid1, y_tol=2.5)
                    content = _norm(" ".join(c_lines))
                    if not content or content.lower() == "content":
                        return
                    low = content.lower()
                    # Skip non-curriculum admin/assessment tables that can be detected as tables too.
                    if low.startswith("component") or "overall weighting" in low or "%" in content:
                        return
                    if low.startswith("version") or low.startswith("description") or low.startswith("page number"):
                        return
                    a_lines = lines_from_words(row_words, xmin=mid1, xmax=mid2, y_tol=2.5)
                    amp_text = "\n".join(a_lines).strip()
                    if not amp_text or amp_text.lower() == "amplification":
                        return
                    area_for_row = _classify_area_from_content_title(content) or current_area
                    counters[area_for_row] += 1
                    l1_code = f"{area_for_row}_C{counters[area_for_row]:03d}"
                    nodes.append(Node(code=l1_code, title=content, level=1, parent=area_for_row))
                    for pi, p in enumerate(_split_amplification(amp_text), 1):
                        nodes.append(Node(code=f"{l1_code}_A{pi:02d}", title=p, level=2, parent=l1_code))

                if has_header and len(t.rows) >= 3:
                    # Use table-provided row geometry when available; it's the cleanest separation.
                    for r in t.rows[1:]:
                        emit_row(r.bbox)
                else:
                    # Fallback: derive row bands from Content-column text blocks.
                    header_bottom = t.rows[0].bbox[3] if t.rows else top
                    content_words = [w for w in table_words if w["x0"] < mid1 and w["top"] > header_bottom + 1]
                    if not content_words:
                        continue
                    cw_sorted = sorted(content_words, key=lambda w: (w["top"], w["x0"]))
                    line_tops: list[float] = []
                    last_top: Optional[float] = None
                    for w in cw_sorted:
                        if last_top is None or abs(w["top"] - last_top) > 2.5:
                            line_tops.append(w["top"])
                            last_top = w["top"]

                    band_starts: list[float] = []
                    for ttop in line_tops:
                        if not band_starts or (ttop - band_starts[-1]) > 45:
                            band_starts.append(ttop)

                    for bi, band_top in enumerate(band_starts):
                        band_bottom = (band_starts[bi + 1] - 1) if bi + 1 < len(band_starts) else bottom
                        row_bbox = (left, max(header_bottom + 1, band_top - 1), right, band_bottom)
                        emit_row(row_bbox)

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("EDUQAS/WJEC A LEVEL ECONOMICS - TOPICS SCRAPER (L0-L2, TABLE-BASED)")
    print("=" * 80)
    print(f"Spec: {BASE_SUBJECT['pdf_url']}")

    pdf_bytes = download_pdf(BASE_SUBJECT["pdf_url"])
    nodes = _parse_tables(pdf_bytes)

    by_level: dict[int, int] = {}
    for n in nodes:
        by_level[n.level] = by_level.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(by_level):
        print(f"  - L{lvl}: {by_level[lvl]}")

    for subj in SUBJECTS:
        print(f"\n[INFO] Uploading for exam_board={subj['exam_board']} code={subj['code']} ...")
        upload_to_staging(subject=subj, nodes=nodes)

    print("[OK] Economics (A-Level) scrape complete (uploaded to EDUQAS + WJEC).")


if __name__ == "__main__":
    main()


