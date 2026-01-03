"""
Common parser/uploader for WJEC GCSE Cymraeg Language and Literature (3030) Single/Double Award.

Spec:
  https://www.wjec.co.uk/media/hysc5tin/wjec-gcse-iaith-a-llenyddiaeth-gymraeg-specification.pdf

Expected structure in extracted text:
  - Unit blocks: "Unit 1", "Unit 2", ... and "Unit 4a"/"Unit 4b"
  - Each unit contains a "Content  Further Information" table.

Hierarchy:
  - L0: Unit
  - L1: Unit topic (e.g., 1.1 Narrative) where present; otherwise a generic topic for the unit
  - L2: Content rows (e.g., 1.1.1 ...)
  - L3: Headings inside further info (often "Learners should be able to:" etc.)
  - L4: Bullet statements / short prose points
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
    if s.startswith("GCSE CYMRAEG LANGUAGE AND LITERATURE"):
        return True
    if re.fullmatch(r"\d{1,3}", s):  # page number
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
            "subject_name": f"{subject['name']} (GCSE)",
            "subject_code": subject["code"],
            "qualification_type": "GCSE",
            "specification_url": subject["pdf_url"],
            "exam_board": subject["exam_board"],
        },
        on_conflict="subject_code,qualification_type,exam_board",
    ).execute()
    subject_id = subject_result.data[0]["id"]
    print(f"[OK] Subject ID: {subject_id}")

    max_level = max((n.level for n in nodes), default=0)
    deleted_total = 0
    for lvl in range(max_level, -1, -1):
        res = supabase.table("staging_aqa_topics").delete().eq("subject_id", subject_id).eq("topic_level", lvl).execute()
        deleted_total += len(res.data or [])
    print(f"[OK] Cleared old topics ({deleted_total} rows)")

    to_insert = [
        {
            "subject_id": subject_id,
            "topic_code": n.code,
            "topic_name": n.title,
            "topic_level": n.level,
            "exam_board": subject["exam_board"],
        }
        for n in nodes
    ]
    inserted = supabase.table("staging_aqa_topics").insert(to_insert).execute()
    print(f"[OK] Uploaded {len(inserted.data)} topics")

    code_to_id = {t["topic_code"]: t["id"] for t in inserted.data}
    linked = 0
    for n in nodes:
        if not n.parent:
            continue
        parent_id = code_to_id.get(n.parent)
        child_id = code_to_id.get(n.code)
        if parent_id and child_id:
            supabase.table("staging_aqa_topics").update({"parent_topic_id": parent_id}).eq("id", child_id).execute()
            linked += 1
    print(f"[OK] Linked {linked} relationships")


def parse_cymraeg_units(text: str, *, include_units: set[str]) -> list[Node]:
    """
    include_units: e.g. {"U1","U2","U3","U4a"} or {"U1","U2","U3","U4b","U5","U6"}
    """
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Find unit blocks (avoid TOC by requiring "Areas of content" + "Content  Further information" in the window)
    unit_re = re.compile(r"^Unit\s+(\d+)([ab])?\b", flags=re.IGNORECASE)

    # Collect starts for ALL units found, then later filter by include_units.
    starts: dict[str, int] = {}
    for i, raw in enumerate(lines):
        s = _norm(raw)
        m = unit_re.match(s)
        if not m:
            continue
        unit_num = m.group(1)
        unit_suf = m.group(2) or ""
        unit_key = f"U{unit_num}{unit_suf}"
        window = "\n".join(_norm(x) for x in lines[i : i + 140])
        wlow = window.lower()
        if ("areas of content" in wlow) and ("content" in wlow) and ("further information" in wlow):
            starts[unit_key] = i

    if not starts:
        raise RuntimeError("Could not locate any unit blocks for Cymraeg 3030 (check extraction).")

    # Determine end indices
    unit_order = sorted(starts.items(), key=lambda kv: kv[1])
    blocks: dict[str, tuple[int, int]] = {}
    for idx, (ukey, start) in enumerate(unit_order):
        end = len(lines)
        if idx + 1 < len(unit_order):
            end = unit_order[idx + 1][1]
        blocks[ukey] = (start, end)

    # Patterns inside units
    areas_re = re.compile(r"^Areas of content$", flags=re.IGNORECASE)
    table_re = re.compile(r"^Content\s+Further\s+Information$", flags=re.IGNORECASE)
    l1_re = re.compile(r"^(\d+\.\d)\s+(.+)$")  # e.g. 1.1 Narrative
    l2_re = re.compile(r"^(\d+\.\d+\.\d+)\s+(.+)$")  # e.g. 1.1.1 ...
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7]\s*(.+)$")

    nodes: list[Node] = []

    for ukey, (start, end) in blocks.items():
        if ukey not in include_units:
            continue
        block = lines[start:end]

        # Grab unit title from next non-header line(s) after "Unit X"
        u_title_parts: list[str] = []
        j = 1
        while start + j < len(lines) and len(u_title_parts) < 3:
            t = _norm(lines[start + j])
            if not t or _looks_like_header_footer(t):
                j += 1
                continue
            # Stop if we hit "Areas of content" quickly
            if areas_re.match(t):
                break
            if t.lower().startswith(("written examination", "non-examination", "overview of unit")):
                j += 1
                continue
            u_title_parts.append(t)
            j += 1
        unit_title = _norm(" ".join(u_title_parts)) or ukey

        nodes.append(Node(code=ukey, title=f"{ukey.replace('U', 'Unit ')}: {unit_title}".strip(), level=0, parent=None))

        # Parse Areas of content to find L1 topics
        current_l1: Optional[str] = None
        seen_table = False
        in_areas = False
        in_table = False

        # fallback L1 (only used if no explicit L1 topic rows are detected)
        default_l1_code = f"{ukey}_T"

        # Map numeric L1 code to node code so L2 rows attach correctly
        l1_map: dict[str, str] = {}

        # state for L2/L3/L4
        current_l2: Optional[str] = None
        current_l3: Optional[str] = None
        l3_idx = 0
        l4_idx = 0

        def ensure_l1(l1_code: str, l1_title: str) -> str:
            if l1_code in l1_map:
                return l1_map[l1_code]
            node_code = f"{ukey}_{l1_code.replace('.', '_')}"
            nodes.append(Node(code=node_code, title=f"{l1_code} {l1_title}".strip(), level=1, parent=ukey))
            l1_map[l1_code] = node_code
            return node_code

        def start_l2(l1_code: str, l2_code: str, l2_title: str) -> None:
            nonlocal current_l1, current_l2, current_l3, l3_idx, l4_idx
            current_l1 = l1_map.get(l1_code) or ensure_l1(l1_code, "Content")
            current_l2 = f"{current_l1}_{l2_code.replace('.', '_')}"
            nodes.append(Node(code=current_l2, title=f"{l2_code} {l2_title}".strip(), level=2, parent=current_l1))
            current_l3 = None
            l3_idx = 0
            l4_idx = 0

        def start_l3(title: str) -> None:
            nonlocal current_l3, l3_idx, l4_idx
            if not current_l2:
                return
            l3_idx += 1
            current_l3 = f"{current_l2}_H{l3_idx:02d}"
            nodes.append(Node(code=current_l3, title=title, level=3, parent=current_l2))
            l4_idx = 0

        def add_l4(text_line: str) -> None:
            nonlocal l4_idx
            parent = current_l3 or current_l2
            if not parent:
                return
            l4_idx += 1
            nodes.append(Node(code=f"{parent}_P{l4_idx:02d}", title=text_line, level=4, parent=parent))

        def _looks_like_exam_admin(s: str) -> bool:
            slow = s.lower()
            if "assessment objectives" in slow:
                return True
            if slow.startswith(("for this assessment", "task setting", "learners are allowed to take", "if necessary, the teacher should")):
                return True
            if "authentication" in slow or "moderated" in slow or "centre" in slow and "moderated" in slow:
                return True
            if slow.startswith(("entries and awards", "technical information", "malpractice")):
                return True
            return False

        # Walk block
        for raw in block:
            s = _norm(raw)
            if not s or _looks_like_header_footer(s):
                continue
            if _looks_like_exam_admin(s):
                continue

            if table_re.match(s):
                in_table = True
                in_areas = False
                seen_table = True
                continue

            if areas_re.match(s):
                in_areas = True
                in_table = False
                continue

            if in_areas and not seen_table:
                m1 = l1_re.match(s)
                if m1:
                    ensure_l1(m1.group(1), m1.group(2))
                continue

            if in_table:
                m2 = l2_re.match(s)
                if m2:
                    l2_code = m2.group(1)
                    l2_title = m2.group(2)
                    # infer L1 code prefix
                    l1_code = ".".join(l2_code.split(".")[:2])
                    start_l2(l1_code, l2_code, l2_title)
                    continue

                # headings inside further info often end with ":" or start with "Learners ..."
                if s.endswith(":") or s.lower().startswith("learners "):
                    start_l3(s)
                    continue

                bm = bullet_re.match(s)
                if bm:
                    add_l4(_norm(bm.group(1)))
                    continue

                # prose
                add_l4(s)

        # If we never detected any explicit L1 topic rows, add the fallback L1 (rare in this spec).
        if not l1_map:
            nodes.append(Node(code=default_l1_code, title="Content", level=1, parent=ukey))

    # de-dupe by code
    uniq: list[Node] = []
    seen = set()
    for n in nodes:
        if n.code in seen:
            continue
        seen.add(n.code)
        uniq.append(n)
    if not uniq:
        raise RuntimeError("No topics parsed for Cymraeg 3030.")
    return uniq


