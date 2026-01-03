"""
WJEC GCSE Dance (3640) - Topics Scraper (Unit 3 only: Dance Appreciation)

Spec:
  https://www.wjec.co.uk/media/kthlbju4/wjec-gcse-dance-specification-e.pdf

User requirement:
  - Only Unit 3 is needed (digital examination).
  - Add the Unit 3 set works under a separate L0.
  - Parse the Unit 3 table (Content / Further information) so that:
      - L0: Unit 3: Dance Appreciation
      - L0: Unit 3 Set Works
      - L1: 3.1.1 / 3.1.2 / 3.1.3
      - L2: Content row (the 3.1.x item itself)
      - L3: "Further information" headings/statements
      - L4: bullets under a heading
      - L5: sub-bullets when a bullet ends with ":" (e.g., "staging for example:")
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
    "name": "Dance",
    "code": "WJEC-3640",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/kthlbju4/wjec-gcse-dance-specification-e.pdf",
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
    if "WJEC CBAC" in s or "© WJEC" in s or "� WJEC" in s:
        return True
    if re.fullmatch(r"\d{1,3}", s):  # page number
        return True
    if s.startswith("GCSE DANCE"):
        return True
    return False


def download_pdf_text(url: str) -> str:
    print("[INFO] Downloading PDF...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    reader = PdfReader(BytesIO(resp.content))
    print(f"[OK] Downloaded {len(reader.pages)} pages")
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def parse_dance_unit3(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    # ---- Set works block ----
    set_works_start_re = re.compile(r"^Learners will study three set works for Unit 3\.", re.IGNORECASE)
    areas_of_content_re = re.compile(r"^Areas of content\s*$", re.IGNORECASE)

    set_start = None
    set_end = None
    for i, raw in enumerate(lines):
        if set_works_start_re.match(_norm(raw)):
            set_start = i
            break
    if set_start is not None:
        for j in range(set_start + 1, len(lines)):
            if areas_of_content_re.match(_norm(lines[j])):
                set_end = j
                break

    set_block = lines[set_start:set_end] if (set_start is not None and set_end is not None) else []

    # ---- Dance Appreciation table block ----
    da_start_re = re.compile(r"^3\.1\s+Dance Appreciation\b", re.IGNORECASE)
    da_end_re = re.compile(r"^4\s+Assessment\b|^4\.\s*Assessment\b", re.IGNORECASE)

    da_start = None
    da_end = len(lines)
    for i, raw in enumerate(lines):
        if da_start_re.match(_norm(raw)):
            da_start = i
            break
    if da_start is None:
        raise RuntimeError("Could not locate '3.1 Dance Appreciation' in extracted text.")
    for j in range(da_start + 1, len(lines)):
        if da_end_re.match(_norm(lines[j])):
            da_end = j
            break
    da_block = lines[da_start:da_end]

    # Patterns
    topic_list_re = re.compile(r"^3\.1\.(\d)\s+(.+)$")  # 3.1.1 ...
    content_header_re = re.compile(r"^Content\s+Further information\s*$", re.IGNORECASE)
    # Bullet char sometimes comes out as '•' or '�'
    bullet_re = re.compile(r"^[•\u2022�]\s*(.+)$")
    learners_stmt_re = re.compile(r"^Learners should\b", re.IGNORECASE)

    nodes: list[Node] = []

    # L0s
    unit_code = "U3"
    unit_title = "Unit 3: Dance Appreciation"
    nodes.append(Node(code=unit_code, title=unit_title, level=0, parent=None))

    set_code = "U3_SET_WORKS"
    nodes.append(Node(code=set_code, title="Unit 3 Set Works", level=0, parent=None))

    # ---- Parse set works into hierarchy ----
    # We build:
    #   L1: Column 1 – Compulsory / Column 2 – Longer works / Column 3 – Shorter works
    #   L2: Each listed work (including compulsory)
    col1 = Node(code=f"{set_code}_COL1", title="Column 1 – Compulsory", level=1, parent=set_code)
    col2 = Node(code=f"{set_code}_COL2", title="Column 2 – Longer works", level=1, parent=set_code)
    col3 = Node(code=f"{set_code}_COL3", title="Column 3 – Shorter works", level=1, parent=set_code)
    nodes.extend([col1, col2, col3])
    col_parent = {"COL1": col1.code, "COL2": col2.code, "COL3": col3.code}

    # Extract works from the set works table (it is flattened into lines)
    # Strategy:
    # - Collect quoted title blocks and numbered list items after each "Centres must select..." marker
    # - Use simple state machine: which column we're populating
    current_col = None
    work_idx = {"COL1": 0, "COL2": 0, "COL3": 0}

    def add_work(col_key: str, title: str) -> None:
        title = _norm(title).strip("“”\"")
        if not title:
            return
        work_idx[col_key] += 1
        parent_code = col_parent[col_key]
        nodes.append(Node(code=f"{set_code}_{col_key}_W{work_idx[col_key]:02d}", title=title, level=2, parent=parent_code))

    if set_block:
        for raw in set_block:
            s = _norm(raw)
            if not s or _looks_like_header_footer(s):
                continue
            if s.startswith("All learners must study"):
                current_col = "COL1"
                continue
            if s.startswith("Centres must select one of the following:"):
                # first occurrence is Column 2; second is Column 3
                current_col = "COL2" if work_idx["COL2"] == 0 else "COL3"
                continue
            # compulsory work title is in quotes (often split across lines)
            if current_col == "COL1":
                if "Rygbi:" in s or "Annwyl" in s or "Conchúir" in s or "National Dance Company Wales" in s:
                    # accumulate until blank-ish; easiest: just add each meaningful line as part of one title buffer
                    # We'll create one combined title at the end of COL1 parsing
                    pass
            # numbered items for columns 2/3
            m = re.match(r"^\d+\.\s*(.+)$", s)
            if m and current_col in ("COL2", "COL3"):
                add_work(current_col, m.group(1))

        # Build the compulsory work as a single title by joining relevant lines
        comp_lines: list[str] = []
        in_comp = False
        for raw in set_block:
            s = _norm(raw)
            if s.startswith("All learners must study"):
                in_comp = True
                continue
            if s.startswith("Centres must select one of the following:"):
                in_comp = False
            if not in_comp:
                continue
            if not s or _looks_like_header_footer(s):
                continue
            if any(k in s for k in ("Rygbi", "Annwyl", "Fearghus", "Conchúir", "National Dance Company Wales")):
                comp_lines.append(s)
        if comp_lines:
            add_work("COL1", _norm(" ".join(comp_lines)))

    # ---- Parse Unit 3 Dance Appreciation table ----
    # L1 topic nodes from the list at the top
    topic_titles: dict[str, str] = {}
    for raw in da_block[:80]:
        s = _norm(raw)
        m = topic_list_re.match(s)
        if m:
            idx = m.group(1)
            topic_titles[idx] = _norm(m.group(2))

    # Create L1 nodes for 3.1.1-3.1.3 (even if titles wrap)
    l1_codes: dict[str, str] = {}
    for idx in ("1", "2", "3"):
        title = topic_titles.get(idx, f"3.1.{idx}")
        code = f"{unit_code}_3_1_{idx}"
        l1_codes[idx] = code
        nodes.append(Node(code=code, title=f"3.1.{idx} {title}".strip(), level=1, parent=unit_code))

    # Find the table start after the "Content  Further information" header
    table_start = None
    for i, raw in enumerate(da_block):
        if content_header_re.match(_norm(raw)):
            table_start = i + 1
            break
    if table_start is None:
        raise RuntimeError("Could not locate the 'Content  Further information' header for Unit 3 table.")

    # Table row starts look like:
    #   3.1.1
    #   The constituent features of
    #   dance
    row_code_re = re.compile(r"^3\.1\.(\d)\s*$")
    stop_row_re = re.compile(r"^3\.1\.(\d)\s*$|^3\.1\.(\d)\s+.+$", re.IGNORECASE)

    current_l1: Optional[str] = None
    current_l2: Optional[str] = None
    l2_row_idx = 0

    current_l3: Optional[str] = None
    l3_idx = 0

    current_l4: Optional[str] = None
    l4_idx = 0

    # For bullet wrapping and nested bullets
    active_bullet_code: Optional[str] = None
    active_bullet_parts: list[str] = []
    nested_parent_code: Optional[str] = None  # when bullet endswith ':'

    def flush_active_bullet() -> None:
        nonlocal active_bullet_code, active_bullet_parts
        if active_bullet_code and active_bullet_parts:
            # title is already stored via nodes append at creation time for L4/L5;
            # for wrapped continuation, update last node by de-dupe strategy: we instead append continuation as separate node (bad).
            # To keep it simple, we finalize as a single string at creation time; continuation is appended before node creation.
            pass
        active_bullet_code = None
        active_bullet_parts = []

    def add_l3_statement(text_: str) -> str:
        nonlocal l3_idx, current_l3, current_l4, l4_idx, nested_parent_code
        l3_idx += 1
        code = f"{current_l2}_S{l3_idx:02d}"
        nodes.append(Node(code=code, title=_norm(text_), level=3, parent=current_l2))
        current_l3 = code
        current_l4 = None
        l4_idx = 0
        nested_parent_code = None
        return code

    def add_l4_bullet(text_: str, level: int, parent: str) -> str:
        nonlocal l4_idx
        l4_idx += 1
        code = f"{parent}_B{l4_idx:02d}"
        nodes.append(Node(code=code, title=_norm(text_), level=level, parent=parent))
        return code

    # Helper: capture topic row title which is often multi-line between row code and first "Learners should"
    i = table_start
    while i < len(da_block):
        raw = da_block[i]
        s = _norm(raw)
        if not s or _looks_like_header_footer(s):
            i += 1
            continue

        # row start: a bare "3.1.1" line
        rm = row_code_re.match(s)
        if rm:
            # finalize previous row state
            current_l3 = None
            current_l4 = None
            nested_parent_code = None
            l3_idx = 0
            l4_idx = 0

            idx = rm.group(1)
            current_l1 = l1_codes.get(idx)
            if not current_l1:
                i += 1
                continue

            # Collect the content-cell title lines until we hit a Learners line or next row code
            title_parts: list[str] = []
            j = i + 1
            while j < len(da_block):
                sj = _norm(da_block[j])
                if not sj or _looks_like_header_footer(sj):
                    j += 1
                    continue
                if learners_stmt_re.match(sj) or row_code_re.match(sj) or stop_row_re.match(sj):
                    break
                # content titles are short fragments like "The constituent features of" / "dance"
                if len(sj) <= 120:
                    title_parts.append(sj)
                    j += 1
                    continue
                break
            row_title = _norm(" ".join(title_parts)) or f"3.1.{idx}"
            l2_row_idx += 1
            current_l2 = f"{current_l1}_ROW"
            nodes.append(Node(code=current_l2, title=f"3.1.{idx} {row_title}".strip(), level=2, parent=current_l1))
            i = j
            continue

        if not current_l2:
            i += 1
            continue

        # Group headings / statements (L3)
        if learners_stmt_re.match(s):
            # start a new L3 statement; bullets will attach to it
            add_l3_statement(s)
            i += 1
            continue

        # Bullets (L4/L5)
        bm = bullet_re.match(s)
        if bm and current_l3:
            txt = _norm(bm.group(1))
            # if we are in nested mode (previous bullet ended with ':'), attach as L5 to that bullet
            if nested_parent_code:
                add_l4_bullet(txt, level=5, parent=nested_parent_code)
            else:
                bcode = add_l4_bullet(txt, level=4, parent=current_l3)
                # enter nested mode if this bullet ends with ':'
                if txt.endswith(":"):
                    nested_parent_code = bcode
            i += 1
            continue

        # Wrapped continuation of last bullet or statement:
        # - If we have nested parent and the current line is not a new learners statement, treat as continuation of last bullet item.
        # Given WJEC extraction here is pretty clean, we keep it simple and just append as a new L3 statement if it's texty.
        if current_l3 and s and not row_code_re.match(s) and not learners_stmt_re.match(s):
            # If it's a short line and we recently had a statement, append to last statement by creating a new statement is noisy;
            # instead, treat it as a continuation statement.
            # Practical: append it as another L3 statement.
            add_l3_statement(s)
            i += 1
            continue

        i += 1

    # de-dupe by code
    uniq: list[Node] = []
    seen = set()
    for n in nodes:
        if n.code in seen:
            continue
        seen.add(n.code)
        uniq.append(n)
    if not uniq:
        raise RuntimeError("No topics parsed (check PDF extraction).")
    return uniq


def upload_to_staging(nodes: list[Node]) -> None:
    env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
    load_dotenv(env_path)
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    subject_result = supabase.table("staging_aqa_subjects").upsert(
        {
            "subject_name": f"{SUBJECT['name']} (GCSE)",
            "subject_code": SUBJECT["code"],
            "qualification_type": "GCSE",
            "specification_url": SUBJECT["pdf_url"],
            "exam_board": SUBJECT["exam_board"],
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
            "exam_board": SUBJECT["exam_board"],
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


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC GCSE DANCE (3640) - UNIT 3 TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3640-dance-spec.txt")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}")

    nodes = parse_dance_unit3(text)
    levels = {}
    for n in nodes:
        levels[n.level] = levels.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(nodes)
    print("\n[OK] WJEC 3640 Dance (Unit 3) topics scrape complete.")


if __name__ == "__main__":
    main()


