"""
Eduqas GCSE Geography A (C111QS) - Topics Scraper

Spec:
  https://www.eduqas.co.uk/media/j0zo4wbh/eduqas-gcse-geography-a-spec-from-2016-e-24-01-20.pdf

User requirement:
  - EDUQAS only
  - Hierarchy:
      L0: Core Themes and Option Themes (Theme headings)
      L1: Key Ideas
      L2: Key questions
    Depth of study should be ignored.

Implementation:
  - Parse Component 1 and Component 2 blocks (Component 3 is fieldwork and ignored).
  - Extract Theme -> Key Idea -> Key questions (question codes like 1.1.1 ...).
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
    "name": "Geography A",
    "code": "EDUQAS-C111QS",
    "qualification": "GCSE",
    "exam_board": "EDUQAS",
    "pdf_url": "https://www.eduqas.co.uk/media/j0zo4wbh/eduqas-gcse-geography-a-spec-from-2016-e-24-01-20.pdf",
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
    if "WJEC CBAC" in s or "© WJEC" in s or "© WJEC CBAC" in s or "eduqas" == s.lower():
        return True
    if s.startswith("GCSE GEOGRAPHY"):
        return True
    if re.fullmatch(r"\d{1,3}", s):
        return True
    return False


def download_pdf_text(url: str) -> str:
    raise RuntimeError("This scraper uses table parsing; call download_pdf_bytes() instead.")


def download_pdf_bytes(url: str) -> bytes:
    print("[INFO] Downloading PDF...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.content


def parse_geography_a(pdf_bytes: bytes) -> list[Node]:
    """
    Use pdfplumber table extraction to avoid the 2-column Key questions/Depth of study
    table being merged into a single huge line (which created giant nodes).
    We ignore Depth of study entirely.
    """
    theme_re = re.compile(r"^(Core Theme\s+\d+|Theme\s+\d+):\s+(.+)$", flags=re.IGNORECASE)
    key_idea_re = re.compile(r"^Key Idea\s+(\d+\.\d+):\s+(.+)$", flags=re.IGNORECASE)
    comp_re = re.compile(r"^2\.(\d)\s+Component\s+\1\b", flags=re.IGNORECASE)
    code_re = re.compile(r"\b(\d+\.\d+\.\d+)\b")

    nodes: list[Node] = []
    seen_codes: set[str] = set()

    def add_node(code: str, title: str, level: int, parent: Optional[str]) -> None:
        if code in seen_codes:
            return
        nodes.append(Node(code=code, title=title, level=level, parent=parent))
        seen_codes.add(code)

    def split_by_code(s: str) -> dict[str, str]:
        out: dict[str, str] = {}
        if not s:
            return out
        s = re.sub(r"\s+", " ", s).strip()
        hits = list(code_re.finditer(s))
        for idx, m in enumerate(hits):
            code = m.group(1)
            start = m.end()
            end = hits[idx + 1].start() if idx + 1 < len(hits) else len(s)
            seg = s[start:end].strip(" -:;")
            if seg:
                out[code] = seg
        return out

    settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "edge_min_length": 20,
        "intersection_tolerance": 5,
        "text_tolerance": 3,
    }

    current_comp = "C1"
    current_theme_code: Optional[str] = None
    current_key_idea_code: Optional[str] = None

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            for raw_ln in txt.split("\n"):
                s = _norm(raw_ln)
                cm = comp_re.match(s)
                if cm:
                    current_comp = f"C{cm.group(1)}"
                tm = theme_re.match(s)
                if tm:
                    label = _norm(tm.group(1)).title().replace("Theme", "Theme").replace("Core Theme", "Core Theme")
                    title = _norm(tm.group(2))
                    num = re.search(r"(\d+)", label)
                    tnum = num.group(1) if num else "X"
                    current_theme_code = f"{current_comp}_TH{tnum}"
                    add_node(current_theme_code, f"{label}: {title}", 0, None)
                    current_key_idea_code = None
                km = key_idea_re.match(s)
                if km and current_theme_code:
                    ki_num = km.group(1)
                    ki_title = _norm(km.group(2))
                    current_key_idea_code = f"{current_theme_code}_KI{ki_num.replace('.', '_')}"
                    add_node(current_key_idea_code, f"Key Idea {ki_num}: {ki_title}", 1, current_theme_code)

            tables = page.extract_tables(settings) or []
            for t in tables:
                if not t or len(t) < 2 or not t[0] or len(t[0]) < 2:
                    continue
                hdr0 = _norm((t[0][0] or ""))
                hdr1 = _norm((t[0][1] or ""))
                if "Key questions" not in hdr0 or "Depth of study" not in hdr1:
                    continue
                if not current_key_idea_code:
                    continue
                for row in t[1:]:
                    if not row or len(row) < 1:
                        continue
                    q_map = split_by_code(row[0] or "")
                    for code, q_text in q_map.items():
                        q_node_code = f"{current_key_idea_code}_{code.replace('.', '_')}"
                        add_node(q_node_code, f"{code} {q_text}".strip(), 2, current_key_idea_code)

    if not nodes:
        raise RuntimeError("No topics parsed for Geography A.")
    return nodes


def upload_to_staging(*, nodes: list[Node]) -> None:
    env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
    load_dotenv(env_path)
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    subject_result = supabase.table("staging_aqa_subjects").upsert(
        {
            "subject_name": SUBJECT["name"],
            "subject_code": SUBJECT["code"],
            "qualification_type": SUBJECT["qualification"],
            "specification_url": SUBJECT["pdf_url"],
            "exam_board": SUBJECT["exam_board"],
        },
        on_conflict="subject_code,qualification_type,exam_board",
    ).execute()
    subject_id = subject_result.data[0]["id"]
    print(f"[OK] Subject ID: {subject_id}")

    # Clear old topics
    deleted_total = 0
    BATCH = 200
    for lvl in range(7, -1, -1):
        while True:
            rows = (
                supabase.table("staging_aqa_topics")
                .select("id")
                .eq("subject_id", subject_id)
                .eq("exam_board", SUBJECT["exam_board"])
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
            "exam_board": SUBJECT["exam_board"],
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
    print("EDUQAS GCSE GEOGRAPHY A (C111QS) - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}")

    pdf_bytes = download_pdf_bytes(SUBJECT["pdf_url"])
    nodes = parse_geography_a(pdf_bytes)

    by_level: dict[int, int] = {}
    for n in nodes:
        by_level[n.level] = by_level.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(by_level):
        print(f"  - L{lvl}: {by_level[lvl]}")

    upload_to_staging(nodes=nodes)
    print("[OK] Geography A scrape complete.")


if __name__ == "__main__":
    main()


