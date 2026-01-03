"""
WJEC GCE AS/A Level Government and Politics (2017 spec) - Topics Scraper

Spec:
  https://www.wjec.co.uk/media/kzca3xqp/wjec-gce-gov-and-politics-spec-from-2017-e-15-11-2022-1.pdf

Entry-code mapping in spec:
  - AS cash-in: 2160QS/2160CS
  - A level cash-in: 1160QS/1160CS

We model the full A level content under the A level cash-in: WJEC-1160CS.

PDF structure (clean tables):
  - Unit headings contain section headings like "1.1 Sovereignty, power and accountability"
  - Under each section, tables with columns:
      - "Key Concepts"
      - "Content and amplification" (bulleted)

Hierarchy (matches the PDF):
  - L0: Unit 1..4
  - L1: Section heading (e.g., 1.1 Sovereignty, power and accountability)
  - L2: Key concept row (e.g., 1.1.1 The British Constitution.)
  - L3: Bullets under Content and amplification
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
    "name": "Government and Politics",
    "code": "WJEC-1160CS",
    "qualification": "A-Level",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/kzca3xqp/wjec-gce-gov-and-politics-spec-from-2017-e-15-11-2022-1.pdf",
}


UNIT_TITLES = {
    1: "AS Unit 1: Government in Wales and the United Kingdom",
    2: "AS Unit 2: Living and participating in a democracy",
    3: "A2 Unit 3: Political concepts and theories",
    4: "A2 Unit 4: Government and politics of the USA",
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
    if s.startswith("GCE AS and A LEVEL GOVERNMENT AND POLITICS"):
        return True
    if re.fullmatch(r"\d{1,3}", s):
        return True
    return False


def download_pdf_text(url: str) -> str:
    raise RuntimeError("This scraper uses pdfplumber table parsing; call download_pdf_bytes() instead.")


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

    # Delete existing topics, batched, deepest-first
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
    batch_size = 500
    for lvl in range(max_level, -1, -1):
        while True:
            rows = (
                supabase.table("staging_aqa_topics")
                .select("id")
                .eq("subject_id", subject_id)
                .eq("topic_level", lvl)
                .limit(batch_size)
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

    # Insert batched
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
    expected_links = sum(1 for n in nodes if n.parent)
    for n in nodes:
        if not n.parent:
            continue
        child_id = code_to_id.get(n.code)
        parent_id = code_to_id.get(n.parent)
        if child_id and parent_id:
            supabase.table("staging_aqa_topics").update({"parent_topic_id": parent_id}).eq("id", child_id).execute()
            linked += 1
    if linked != expected_links:
        print(f"[WARN] Linked {linked}/{expected_links} relationships (some parents missing?)")
    else:
        print(f"[OK] Linked {linked} relationships")


def _merge_wrapped_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for s in [x.strip() for x in lines if (x or "").strip()]:
        if not merged:
            merged.append(s)
            continue
        prev = merged[-1]
        # If previous line doesn't look "finished", treat this as a wrap continuation.
        if not prev.endswith((".", "?", "!", ";")):
            merged[-1] = f"{prev} {s}"
        else:
            merged.append(s)
    return merged


def _parse_content_cell(text: str) -> list[str]:
    """
    Returns content items (mostly bullets) from the 'Content and amplification' cell.
    Preserves bullet items and joins wrapped lines.
    """
    if not text:
        return []
    raw_lines = [ln.rstrip() for ln in (text or "").splitlines()]
    raw_lines = [ln.strip() for ln in raw_lines if ln.strip()]
    if not raw_lines:
        return []

    bullet_prefix_re = re.compile(r"^[•\u2022\u25cf\u00b7]\s*")
    has_bullets = any(bullet_prefix_re.search(ln) for ln in raw_lines)

    if has_bullets:
        items: list[str] = []
        cur: list[str] = []
        for ln in raw_lines:
            if bullet_prefix_re.match(ln):
                if cur:
                    items.append(_norm(" ".join(cur)))
                cur = [bullet_prefix_re.sub("", ln).strip()]
            else:
                if not cur:
                    cur = [ln]
                else:
                    cur.append(ln)
        if cur:
            items.append(_norm(" ".join(cur)))
        return items

    # No bullets: keep per-line items but join obvious wraps.
    return [_norm(s) for s in _merge_wrapped_lines(raw_lines)]


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


def parse_govpol(pdf_bytes: bytes) -> list[Node]:
    nodes: list[Node] = []
    seen: set[str] = set()

    def add(code: str, title: str, level: int, parent: Optional[str]) -> None:
        if code in seen:
            return
        nodes.append(Node(code=code, title=title, level=level, parent=parent))
        seen.add(code)

    # Emit units always
    for u in (1, 2, 3, 4):
        add(f"U{u}", UNIT_TITLES.get(u, f"Unit {u}"), 0, None)

    # Section headings like: "1.1 Sovereignty, power and accountability"
    section_re = re.compile(r"^(\d+\.\d)(?!\.)\s+(.+)$")

    # Key concept row like: "1.1.1 The British Constitution."
    key_concept_re = re.compile(r"^(\d+\.\d+\.\d+)\s+(.+)$")

    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "edge_min_length": 20,
        "intersection_tolerance": 5,
        "text_tolerance": 3,
    }

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            # Precompute visible text lines with y-positions for this page so we can
            # recover the bold section headings (1.1 / 1.2 / 3.3 / etc) above each table.
            page_lines: list[dict] = []
            words = page.extract_words() or []
            for top, bottom, line in _group_words_to_lines(words):
                if not line or _looks_like_header_footer(line):
                    continue
                # Hard stop once we hit assessment/technical sections
                if line.upper().startswith(("3 ASSESSMENT", "3. ASSESSMENT", "4 TECHNICAL INFORMATION")):
                    page_lines = []
                    break
                # Ignore contents/TOC-like lines that end with a page number (e.g. "... 6")
                if re.search(r"\s\d{1,3}$", line):
                    continue
                page_lines.append({"top": top, "bottom": bottom, "text": line})

            for t in page.find_tables(table_settings) or []:
                data = t.extract()
                if not data or len(data) < 2 or not data[0] or len(data[0]) < 2:
                    continue
                hdr0 = _norm((data[0][0] or "")).lower()
                hdr1 = _norm((data[0][1] or "")).lower()
                if "key concepts" not in hdr0:
                    continue
                if "content" not in hdr1 or "amplification" not in hdr1:
                    continue

                # Attach each row to its OWN parent section derived from the key concept code.
                # This prevents a whole table from being parented under the wrong section heading.
                table_top = t.bbox[1]

                for row in data[1:]:
                    if not row or len(row) < 2:
                        continue
                    left = _norm(row[0] or "")
                    right = row[1] or ""
                    if not left:
                        continue
                    km = key_concept_re.match(left)
                    if not km:
                        continue

                    kc_code = km.group(1)  # e.g. 1.2.1
                    kc_title = _norm(km.group(2))
                    sec = ".".join(kc_code.split(".")[:2])  # e.g. 1.2
                    try:
                        unit = int(sec.split(".")[0])
                    except Exception:
                        continue
                    if unit not in {1, 2, 3, 4}:
                        continue

                    # Best-effort: find the section heading line (e.g. "1.2 The Government of the UK")
                    # above the table. Fallback to plain section number.
                    sec_title = ""
                    sec_line_re = re.compile(rf"^{re.escape(sec)}(?!\.)\s+(.+)$")
                    candidates = [
                        ln
                        for ln in page_lines
                        if ln["bottom"] <= table_top + 2 and sec_line_re.match(ln["text"])
                    ]
                    if candidates:
                        best = max(candidates, key=lambda ln: ln["bottom"])
                        m = sec_line_re.match(best["text"])
                        sec_title = _norm(m.group(1)) if m else ""

                    sec_code = f"U{unit}_{sec.replace('.', '_')}"
                    add(sec_code, f"{sec} {sec_title}".strip() if sec_title else sec, 1, f"U{unit}")

                    l2_code = f"{sec_code}_{kc_code.replace('.', '_')}"
                    add(l2_code, f"{kc_code} {kc_title}".strip(), 2, sec_code)

                    items = _parse_content_cell(right)
                    for bi, it in enumerate(items, start=1):
                        add(f"{l2_code}_b{bi:02d}", it, 3, l2_code)

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC A-LEVEL GOVERNMENT AND POLITICS (1160CS) - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}")

    pdf_bytes = download_pdf_bytes(SUBJECT["pdf_url"])
    nodes = parse_govpol(pdf_bytes)

    by_level: dict[int, int] = {}
    for n in nodes:
        by_level[n.level] = by_level.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(by_level):
        print(f"  - L{lvl}: {by_level[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("[OK] Government and Politics scrape complete.")


if __name__ == "__main__":
    main()


