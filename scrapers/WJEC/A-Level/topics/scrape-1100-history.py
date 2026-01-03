"""
WJEC GCE AS/A Level History (2015 spec) - Topics Scraper

Spec:
  https://www.wjec.co.uk/media/uwlondvv/wjec-gce-history-spec-from-2015-e.pdf

Entry-code mapping in spec:
  - AS cash-in: 2100QS/2100CS
  - A level cash-in: 1100QS/1100CS

We model the full A level content under the A level cash-in: WJEC-1100CS.

PDF structure:
  - Units 1..4
  - Each option has a clearly marked table with two columns:
      - "Concepts and perspectives" (left)
      - "Key issues and content" (right)
    The table contains multiple rows; each row has a concept heading + related key-issue lines.

Hierarchy:
  - L0: Unit 1..4
  - L1: Option / Part (already created by the skeleton parser)
  - L2: Concepts and perspectives rows (joined multi-line cell text)
  - L3: Key issues and content (each line item, with wrapped lines joined)
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


SUBJECT = {
    "name": "History",
    "code": "WJEC-1100CS",
    "qualification": "A-Level",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/uwlondvv/wjec-gce-history-spec-from-2015-e.pdf",
}


UNIT_TITLES = {
    1: "AS Unit 1: Period Study",
    2: "AS Unit 2: Depth Study Part 1",
    3: "A2 Unit 3: Breadth Study",
    4: "A2 Unit 4: Depth Study Part 2",
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
    if s.startswith("GCE AS and A Level History"):
        return True
    if re.fullmatch(r"\d{1,3}", s):
        return True
    return False


def download_pdf_text(url: str) -> str:
    raise RuntimeError("This scraper uses pdfplumber; call download_pdf_bytes() instead.")


def download_pdf_bytes(url: str) -> bytes:
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

    existing_max = 0
    try:
        res = (
            supabase.table("staging_aqa_topics")
            .select("topic_level")
            .eq("subject_id", subject_id)
            .order("topic_level", desc=True)
            .limit(1)
            .execute()
        )
        if res.data:
            existing_max = int(res.data[0]["topic_level"] or 0)
    except Exception:
        existing_max = 0

    max_level = max(existing_max, max((n.level for n in nodes), default=0))
    deleted_total = 0
    BATCH = 500
    for lvl in range(max_level, -1, -1):
        while True:
            rows = (
                supabase.table("staging_aqa_topics")
                .select("id")
                .eq("subject_id", subject_id)
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
    for i in range(0, len(payload), 500):
        res = supabase.table("staging_aqa_topics").insert(payload[i : i + 500]).execute()
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


def _group_words_to_lines(words: list[dict], y_tol: float = 2.5) -> list[tuple[float, float, str]]:
    """
    Group words to visual lines by 'top' coordinate.
    Returns (top, bottom, text).
    """
    lines: list[dict] = []
    for w in sorted(words, key=lambda x: (x["top"], x["x0"])):
        if not lines or abs(w["top"] - lines[-1]["top"]) > y_tol:
            lines.append({"top": w["top"], "bottom": w["bottom"], "words": [w]})
        else:
            lines[-1]["words"].append(w)
            lines[-1]["bottom"] = max(lines[-1]["bottom"], w["bottom"])

    out: list[tuple[float, float, str]] = []
    for ln in lines:
        text = " ".join(w["text"] for w in sorted(ln["words"], key=lambda x: x["x0"]))
        out.append((ln["top"], ln["bottom"], _norm(text)))
    return out


def _merge_wrapped_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for s in [x.strip() for x in lines if (x or "").strip()]:
        if not merged:
            merged.append(s)
            continue
        prev = merged[-1]
        # Join if the previous line clearly wraps into the next
        if (not prev.endswith((".", "?", "!", ";", ":"))) and (s[:1].islower()):
            merged[-1] = f"{prev} {s}"
        else:
            merged.append(s)
    return merged


def _split_semicolon_items(text: str) -> list[str]:
    """
    Breadth/depth theme tables use semicolon-separated prose in the right column.
    We join wrapped lines and then split on ';' to get clean atomic items.
    """
    if not text:
        return []
    raw = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if not raw:
        return []
    joined = _merge_wrapped_lines(raw)
    out: list[str] = []
    for ln in joined:
        parts = [p.strip() for p in ln.split(";") if p.strip()]
        out.extend(parts if parts else [ln.strip()])
    return [_norm(x) for x in out if _norm(x)]


def _iter_history_tables(pdf_bytes: bytes):
    """
    Yields tuples:
      (page_number, parent_key, kind, table_bbox, left_col_bbox, right_col_bbox, hdr0, hdr1)
    parent_key tracks the current option/part so we can attach children correctly.
    """
    settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "edge_min_length": 20,
        "intersection_tolerance": 5,
        "text_tolerance": 3,
    }

    unit_opt_re = re.compile(r"\bUNIT\s+([1-4])\s*-\s*OPTION\s+(\d+)\b", flags=re.IGNORECASE)
    depth_pair_re = re.compile(r"\bUnit\s+([24])\s+\((AS|A2)\):\s+Part\s+([12]):", flags=re.IGNORECASE)

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        current_parent: Optional[str] = None
        for pi, page in enumerate(pdf.pages, start=1):
            txt = page.extract_text() or ""

            om = unit_opt_re.search(txt)
            if om:
                u = int(om.group(1))
                n = int(om.group(2))
                current_parent = f"U{u}_opt{n:02d}"

            dm = depth_pair_re.search(txt)
            if dm:
                u = int(dm.group(1))
                part = dm.group(3)
                current_parent = f"U{u}_part{part}"

            if not current_parent:
                continue

            for t in page.find_tables(settings) or []:
                table_data = t.extract()
                if not table_data or not table_data[0] or len(table_data[0]) < 2:
                    continue
                hdr0 = _norm(table_data[0][0] or "")
                hdr1 = _norm(table_data[0][1] or "")

                # Type A: Concepts/Key issues option tables
                if ("concepts" in hdr0.lower() and "perspectives" in hdr0.lower()) and (
                    "key issues" in hdr1.lower() or "key issues and content" in hdr1.lower()
                ):
                    left_col = t.columns[0].bbox
                    right_col = t.columns[1].bbox
                    yield (pi, current_parent, "concepts", t.bbox, left_col, right_col, hdr0, hdr1)
                    continue

                # Type B: Breadth/Depth study theme tables (Theme 1/2/3...) – usually header text is in col 0
                if re.match(r"^Theme\s+\d+", hdr0, flags=re.IGNORECASE):
                    left_col = t.columns[0].bbox
                    right_col = t.columns[1].bbox
                    yield (pi, current_parent, "theme", t.bbox, left_col, right_col, hdr0, hdr1)
                    continue


def parse_history(pdf_bytes: bytes) -> list[Node]:
    """
    Build the skeleton (units/options) from text, then enrich each option/part by parsing
    its 2-column table(s) into L2/L3.
    """
    nodes: list[Node] = []
    seen: set[str] = set()

    def add(code: str, title: str, level: int, parent: Optional[str]) -> None:
        if code in seen:
            return
        nodes.append(Node(code=code, title=title, level=level, parent=parent))
        seen.add(code)

    # Always emit units
    for u in (1, 2, 3, 4):
        add(f"U{u}", UNIT_TITLES[u], 0, None)

    # Skeleton: parse headings from plain text (quick + reliable)
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    lines = [ln.rstrip() for ln in text.split("\n")]

    unit_opt_re = re.compile(r"^UNIT\s+([1-4])\s*-\s*OPTION\s+(\d+)$", flags=re.IGNORECASE)
    depth_pair_re = re.compile(
        r"^Unit\s+([24])\s+\((AS|A2)\):\s+Part\s+([12]):\s+(.+)$", flags=re.IGNORECASE
    )

    i = 0
    while i < len(lines):
        s = _norm(lines[i])
        if not s or _looks_like_header_footer(s):
            i += 1
            continue

        dm = depth_pair_re.match(s)
        if dm:
            unit_num = int(dm.group(1))
            part = dm.group(3)
            title = _norm(dm.group(4))
            ucode = f"U{unit_num}"
            opt_code = f"{ucode}_part{part}"
            add(opt_code, f"Part {part}: {title}", 1, ucode)
            i += 1
            continue

        om = unit_opt_re.match(s)
        if om:
            unit_num = int(om.group(1))
            opt_num = int(om.group(2))
            ucode = f"U{unit_num}"
            title = ""
            j = i + 1
            while j < len(lines):
                t = _norm(lines[j])
                if t and not _looks_like_header_footer(t):
                    title = t
                    break
                j += 1
            code = f"{ucode}_opt{opt_num:02d}"
            add(code, f"Option {opt_num}: {title}".strip(), 1, ucode)
            i = j + 1
            continue

        i += 1

    # Enrich: parse tables into L2/L3/L4 under each L1 parent
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "edge_min_length": 20,
        "intersection_tolerance": 5,
        "text_tolerance": 3,
    }

    for (_page_num, parent_code, kind, table_bbox, left_bbox, right_bbox, hdr0, hdr1) in _iter_history_tables(
        pdf_bytes
    ):
        if parent_code not in seen:
            # In case a table appears before the skeleton heading (rare), create a shell parent
            u = int(parent_code[1])
            add(parent_code, parent_code, 1, f"U{u}")

        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            page = pdf.pages[_page_num - 1]
            if kind == "concepts":
                tbl_words = page.within_bbox(table_bbox).extract_words() or []
                header_words = [
                    w
                    for w in tbl_words
                    if _norm(w["text"]).lower() in {"concepts", "perspectives", "key", "issues", "content"}
                ]
                header_bottom = max((w["bottom"] for w in header_words), default=table_bbox[1])
                y_start = header_bottom + 2

                left_words = (
                    page.within_bbox((left_bbox[0], y_start, left_bbox[2], left_bbox[3])).extract_words() or []
                )
                left_lines = _group_words_to_lines(left_words)
                if not left_lines:
                    continue

                # Build concept blocks by vertical gaps between consecutive lines
                blocks: list[list[tuple[float, float, str]]] = []
                cur_block: list[tuple[float, float, str]] = [left_lines[0]]
                for prev, nxt in zip(left_lines, left_lines[1:]):
                    gap = nxt[0] - prev[1]
                    if gap > 10:
                        blocks.append(cur_block)
                        cur_block = [nxt]
                    else:
                        cur_block.append(nxt)
                blocks.append(cur_block)

                for ci, block in enumerate(blocks, start=1):
                    concept_title = _norm(" ".join(x[2] for x in block))
                    if not concept_title:
                        continue
                    concept_code = f"{parent_code}_c{ci:02d}"
                    add(concept_code, concept_title, 2, parent_code)

                    y0 = block[0][0] - 1
                    y1 = (blocks[ci][0][0] - 1) if ci < len(blocks) else right_bbox[3]
                    r_words = page.within_bbox((right_bbox[0], y0, right_bbox[2], y1)).extract_words() or []
                    r_lines = [ln[2] for ln in _group_words_to_lines(r_words)]
                    items = _merge_wrapped_lines(r_lines)
                    items = [
                        it
                        for it in items
                        if it.lower() not in {"key issues and content", "concepts and perspectives"} and len(it) >= 4
                    ]
                    for ki, it in enumerate(items, start=1):
                        add(f"{concept_code}_k{ki:02d}", it, 3, concept_code)

            elif kind == "theme":
                # L2: Theme header under the option
                theme_title = _norm(hdr0)
                theme_idx = (
                    len(
                        [
                            n
                            for n in nodes
                            if n.parent == parent_code
                            and n.level == 2
                            and n.code.startswith(f"{parent_code}_t")
                        ]
                    )
                    + 1
                )
                theme_code = f"{parent_code}_t{theme_idx:02d}"
                add(theme_code, theme_title, 2, parent_code)

                # Find the exact table on this page and parse rows (L3 headings + L4 items)
                match = None
                for t in page.find_tables(table_settings) or []:
                    if tuple(round(x, 2) for x in t.bbox) == tuple(round(x, 2) for x in table_bbox):
                        match = t
                        break
                if not match:
                    continue
                data = match.extract() or []
                if len(data) < 2:
                    continue
                for r in data[1:]:
                    if not r or len(r) < 2:
                        continue
                    left_txt = _norm(r[0] or "")
                    right_txt = r[1] or ""
                    if not left_txt:
                        continue
                    row_idx = len([n for n in nodes if n.parent == theme_code and n.level == 3]) + 1
                    row_code = f"{theme_code}_r{row_idx:02d}"
                    add(row_code, left_txt, 3, theme_code)
                    items = _split_semicolon_items(right_txt)
                    for ii, it in enumerate(items, start=1):
                        add(f"{row_code}_i{ii:02d}", it, 4, row_code)

    if not nodes:
        raise RuntimeError("No topics parsed for History.")
    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC A-LEVEL HISTORY (1100CS) - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}")

    pdf_bytes = download_pdf_bytes(SUBJECT["pdf_url"])
    nodes = parse_history(pdf_bytes)

    by_level: dict[int, int] = {}
    for n in nodes:
        by_level[n.level] = by_level.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(by_level):
        print(f"  - L{lvl}: {by_level[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("[OK] History scrape complete.")


if __name__ == "__main__":
    main()


