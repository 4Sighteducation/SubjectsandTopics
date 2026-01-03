"""
WJEC GCE AS/A Level Mathematics (2017 spec) - Topics Scraper

Spec:
  https://www.wjec.co.uk/media/lm3fegtu/wjec-gce-maths-spec-from-2017-e.pdf

Entry-code mapping in spec:
  - AS cash-in: 2300QS/2300CS
  - A level cash-in: 1300QS/1300CS

We model the full A level content under the A level cash-in: WJEC-1300CS.

Hierarchy:
  - L0: Units 1..4
  - L1: Areas of content (2.1.1, 2.2.3, 2.3.7, 2.4.5 etc.)

This keeps a clean structure without trying to parse deep prose/exemplification (which
can be noisy in extracted text).
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
    "name": "Mathematics",
    "code": "WJEC-1300CS",
    "qualification": "A-Level",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/lm3fegtu/wjec-gce-maths-spec-from-2017-e.pdf",
}


UNIT_TITLES = {
    1: "AS Unit 1: Pure Mathematics A",
    2: "AS Unit 2: Applied Mathematics A",
    3: "A2 Unit 3: Pure Mathematics B",
    4: "A2 Unit 4: Applied Mathematics B",
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
    if s.startswith("GCE AS and A Level Mathematics"):
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


def parse_maths(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    unit_hdr_re = re.compile(r"^2\.(\d)\s+(AS|A2)\s+UNIT\s+\1\b(?!\s+\d)", flags=re.IGNORECASE)
    unit_starts: dict[int, int] = {}
    for i, raw in enumerate(lines):
        s = _norm(raw)
        m = unit_hdr_re.match(s)
        if m:
            unit_starts[int(m.group(1))] = i

    if not unit_starts:
        raise RuntimeError("Could not locate unit starts for Mathematics.")

    unit_nums = sorted(unit_starts)
    blocks: dict[int, tuple[int, int]] = {}
    for idx, u in enumerate(unit_nums):
        start = unit_starts[u]
        end = len(lines)
        if idx + 1 < len(unit_nums):
            end = unit_starts[unit_nums[idx + 1]]
        blocks[u] = (start, end)

    area_re = re.compile(r"^(\d+\.\d+\.\d+)\s+(.+)$")

    nodes: list[Node] = []
    seen: set[str] = set()

    def add(code: str, title: str, level: int, parent: Optional[str]) -> None:
        if code in seen:
            return
        nodes.append(Node(code=code, title=title, level=level, parent=parent))
        seen.add(code)

    for u in unit_nums:
        ucode = f"U{u}"
        add(ucode, UNIT_TITLES.get(u, f"Unit {u}"), 0, None)

        start, end = blocks[u]
        block = lines[start:end]
        for raw in block:
            s = _norm(raw)
            if not s or _looks_like_header_footer(s):
                continue
            if s.upper().startswith(("3 ASSESSMENT", "3. ASSESSMENT", "4 TECHNICAL INFORMATION")):
                break
            m = area_re.match(s)
            if not m:
                continue
            code = m.group(1)
            title = m.group(2)
            add(f"{ucode}_{code.replace('.', '_')}", f"{code} {title}".strip(), 1, ucode)

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC A-LEVEL MATHEMATICS (1300CS) - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}")

    text = download_pdf_text(SUBJECT["pdf_url"])
    nodes = parse_maths(text)

    by_level: dict[int, int] = {}
    for n in nodes:
        by_level[n.level] = by_level.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(by_level):
        print(f"  - L{lvl}: {by_level[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("[OK] Mathematics scrape complete.")


if __name__ == "__main__":
    main()






