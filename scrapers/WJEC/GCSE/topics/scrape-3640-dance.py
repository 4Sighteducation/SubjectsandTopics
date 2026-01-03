"""
WJEC GCSE Dance (3640) - Topics Scraper (Unit 3 only)

Spec (Teaching from 2026 / award from 2028):
  https://www.wjec.co.uk/media/kthlbju4/wjec-gcse-dance-specification-e.pdf

User requirements:
  - Only Unit 3: Dance Appreciation is required.
  - Add set works under a separate L0 (Unit 3 set works).
  - For the Unit 3 content table, split L2 vs L3 based on the "Further information" column:
      - L1: 3.1.1 / 3.1.2 / 3.1.3
      - L2: "Learners should understand/know/be able..." subheads in further information
      - L3: bullet points under that subhead
      - L4: nested bullets when a bullet introduces "for example:"
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
    if "WJEC CBAC" in s or "© WJEC" in s:
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

    # Slice to Unit 3 (avoid contents page entry like "Unit 3 .... 15")
    unit3_header_re = re.compile(r"^Unit\s+3\b(?!\s+\.{2,}|\s+\d)", flags=re.IGNORECASE)
    stop_re = re.compile(r"^Opportunities for integration of learning experiences\b", flags=re.IGNORECASE)

    start = None
    for i, raw in enumerate(lines):
        s = _norm(raw)
        if not unit3_header_re.match(s):
            continue
        window = "\n".join(_norm(x) for x in lines[i : i + 80])
        if "Dance Appreciation" in window and "Areas of content" in window:
            start = i
            break
    if start is None:
        raise RuntimeError("Could not locate Unit 3 section.")

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if stop_re.match(_norm(lines[j])):
            end = j
            break

    block = lines[start:end]

    # Key markers inside Unit 3
    setworks_start_re = re.compile(r"^Learners will study three set works for Unit 3\b", flags=re.IGNORECASE)
    areas_of_content_re = re.compile(r"^Areas of content\b", flags=re.IGNORECASE)

    # L1 topics in Unit 3
    l1_re = re.compile(r"^3\.1\.(\d)\s+(.+)$")
    l1_code_only_re = re.compile(r"^3\.1\.(\d)$")

    # Further info subheads (become L2)
    l2_re = re.compile(r"^Learners should\s+(understand|know|be able to)\s+(.+)$", flags=re.IGNORECASE)

    # Bullets
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7�]\s*(.+)$")

    nodes: list[Node] = []

    # L0s
    unit_l0_code = "U3"
    setworks_l0_code = "U3_SETWORKS"
    nodes.append(Node(code=unit_l0_code, title="Unit 3: Dance Appreciation", level=0, parent=None))
    nodes.append(Node(code=setworks_l0_code, title="Unit 3: Set works", level=0, parent=None))

    # 1) Parse set works block
    def parse_setworks() -> None:
        # Find set works section
        sw_start = None
        sw_end = None
        for i, raw in enumerate(block):
            if setworks_start_re.match(_norm(raw)):
                sw_start = i
                break
        if sw_start is None:
            return
        for j in range(sw_start + 1, len(block)):
            if areas_of_content_re.match(_norm(block[j])):
                sw_end = j
                break
        if sw_end is None:
            sw_end = len(block)

        sw = [_norm(x) for x in block[sw_start:sw_end] if _norm(x)]

        # Create column nodes
        col_nodes = [
            ("C1", "Column 1 – Compulsory"),
            ("C2", "Column 2 – Longer works"),
            ("C3", "Column 3 – Shorter works"),
        ]
        for code, title in col_nodes:
            nodes.append(Node(code=f"{setworks_l0_code}_{code}", title=title, level=1, parent=setworks_l0_code))

        # Parse the lists. The extraction is linear, so use robust pattern matching.
        joined = "\n".join(sw)

        # Column 1 (single compulsory work)
        # Keep the full line(s) as one title if possible.
        # Example extracted:
        #   All learners must study
        #   “Rygbi: Annwyl (Dear)”
        #   by Fearghus Ó
        #   Conchúir and performers
        #   of National Dance
        #   Company Wales
        c1_title = None
        m = re.search(r"All learners must study\s+“([^”]+)”\s+by\s+(.+?)(?=Centres must select one of|$)", joined, flags=re.IGNORECASE | re.DOTALL)
        if m:
            work = _norm(m.group(1))
            by = _norm(m.group(2))
            c1_title = f"{work} — {by}"
        if c1_title:
            nodes.append(Node(code=f"{setworks_l0_code}_C1_1", title=c1_title, level=2, parent=f"{setworks_l0_code}_C1"))

        # Column 2 options (1..3)
        m2 = re.search(r"Column 2.*?Centres must select one of the following:(.+?)Centres must select one of the following:", joined, flags=re.IGNORECASE | re.DOTALL)
        if m2:
            chunk = m2.group(1)
            for num, title in re.findall(r"\b(\d)\.\s*([^\n]+(?:\n(?!\d\.).+)*)", chunk, flags=re.DOTALL):
                nodes.append(Node(code=f"{setworks_l0_code}_C2_{num}", title=_norm(title), level=2, parent=f"{setworks_l0_code}_C2"))

        # Column 3 options (1..3) – after the second "Centres must select..."
        m3 = re.search(r"Column 3.*?Centres must select one of the following:(.+?)(?=GCSE DANCE|\Z)", joined, flags=re.IGNORECASE | re.DOTALL)
        if m3:
            chunk = m3.group(1)
            for num, title in re.findall(r"\b(\d)\.\s*([^\n]+(?:\n(?!\d\.).+)*)", chunk, flags=re.DOTALL):
                nodes.append(Node(code=f"{setworks_l0_code}_C3_{num}", title=_norm(title), level=2, parent=f"{setworks_l0_code}_C3"))

    parse_setworks()

    # 2) Parse the Unit 3 content table (3.1.1-3.1.3)
    # Find the "Areas of content" section.
    content_start = None
    for i, raw in enumerate(block):
        if areas_of_content_re.match(_norm(raw)):
            content_start = i
            break
    if content_start is None:
        raise RuntimeError("Could not locate Areas of content in Unit 3.")

    content_lines = block[content_start:]

    # First, create the three L1 nodes from the list under "3.1 Dance Appreciation"
    # (these titles can wrap across lines).
    l1_map: dict[str, str] = {}
    list_start = None
    for i, raw in enumerate(content_lines):
        if _norm(raw).startswith("3.1 Dance Appreciation"):
            list_start = i
            break
    if list_start is None:
        raise RuntimeError("Could not locate '3.1 Dance Appreciation' heading.")

    # The list ends at the table header "Content  Further information"
    table_header_idx = None
    for j in range(list_start, len(content_lines)):
        if _norm(content_lines[j]).lower() == "content further information":
            table_header_idx = j
            break
    if table_header_idx is None:
        raise RuntimeError("Could not locate the 'Content  Further information' table header.")

    i = list_start
    while i < table_header_idx:
        s = _norm(content_lines[i])
        m = l1_re.match(s)
        if not m:
            i += 1
            continue
        n = m.group(1)
        title_parts = [m.group(2)]
        k = i + 1
        while k < table_header_idx:
            nxt = _norm(content_lines[k])
            if not nxt or _looks_like_header_footer(nxt):
                k += 1
                continue
            if l1_re.match(nxt) or nxt.lower() == "content further information":
                break
            # wrapped continuation of the L1 title
            title_parts.append(nxt)
            k += 1
        full_title = _norm(" ".join(title_parts))
        l1_code = f"{unit_l0_code}_3_1_{n}"
        nodes.append(Node(code=l1_code, title=f"3.1.{n} {full_title}".strip(), level=1, parent=unit_l0_code))
        l1_map[n] = l1_code
        i = k

    # Now parse the table starting at the header
    content_lines = content_lines[table_header_idx + 1 :]

    # State
    current_l1_code: Optional[str] = None
    current_l2_code: Optional[str] = None

    # bullet nesting state (for "for example:" groups)
    current_example_group_code: Optional[str] = None
    example_group_idx = 0
    bullet_idx = 0

    def flush_example_group() -> None:
        nonlocal current_example_group_code
        current_example_group_code = None

    def start_l2(raw_line: str) -> None:
        nonlocal current_l2_code, current_example_group_code, example_group_idx, bullet_idx
        if not current_l1_code:
            return
        current_example_group_code = None
        example_group_idx = 0
        bullet_idx = 0
        # build a compact title by removing the leading "Learners should"
        t = _norm(raw_line)
        t = re.sub(r"^Learners should\s+", "", t, flags=re.IGNORECASE).strip()
        # remove trailing full stop if it's a sentence (keeps colons)
        if t.endswith(".") and not t.endswith("..."):
            t = t[:-1].strip()
        # code: increment based on count
        existing = sum(1 for n in nodes if n.parent == current_l1_code and n.level == 2)
        current_l2_code = f"{current_l1_code}_s{existing+1:02d}"
        nodes.append(Node(code=current_l2_code, title=t, level=2, parent=current_l1_code))

    def add_l3_bullet(text_: str) -> None:
        nonlocal bullet_idx
        if not current_l2_code:
            return
        bullet_idx += 1
        nodes.append(Node(code=f"{current_l2_code}_b{bullet_idx:02d}", title=_norm(text_), level=3, parent=current_l2_code))

    def start_example_group(text_: str) -> None:
        nonlocal current_example_group_code, example_group_idx
        if not current_l2_code:
            return
        example_group_idx += 1
        # strip trailing colon for readability
        t = _norm(text_)
        if t.endswith(":"):
            t = t[:-1].strip()
        current_example_group_code = f"{current_l2_code}_eg{example_group_idx:02d}"
        nodes.append(Node(code=current_example_group_code, title=t, level=3, parent=current_l2_code))

    def add_l4_under_example(text_: str) -> None:
        if not current_example_group_code:
            return
        # count existing l4 children
        existing = sum(1 for n in nodes if n.parent == current_example_group_code and n.level == 4)
        nodes.append(Node(code=f"{current_example_group_code}_b{existing+1:02d}", title=_norm(text_), level=4, parent=current_example_group_code))

    i = 0
    while i < len(content_lines):
        raw = content_lines[i]
        s = _norm(raw)
        if not s or _looks_like_header_footer(s):
            i += 1
            continue

        # Skip the "Content  Further information" header
        if s.lower() in {"content further information", "content", "further information"}:
            i += 1
            continue

        # Table section selector: "3.1.1" / "3.1.2" / "3.1.3" (code only).
        mcode = l1_code_only_re.match(s)
        if mcode:
            n = mcode.group(1)
            current_l1_code = l1_map.get(n)
            current_l2_code = None
            flush_example_group()
            bullet_idx = 0
            example_group_idx = 0
            i += 1
            continue

        # Ignore left-column row title repeats until we hit Learners should... / bullets
        if current_l1_code and not s.lower().startswith("learners should") and not bullet_re.match(s) and not s.startswith("N.B"):
            # Many of these are the content-column titles ("The constituent features of dance")
            i += 1
            continue

        # L2 headings (Learners should ...) — titles can wrap across lines.
        m2 = l2_re.match(s)
        if m2 and current_l1_code:
            # A common pattern is a redundant first sentence "Learners should be able to identify..."
            # followed immediately by "Learners should understand ... including:" — skip the redundant one.
            if "identify and describe" in s.lower():
                # lookahead for an "understand ... including" soon
                look = "\n".join(_norm(x) for x in content_lines[i + 1 : i + 8])
                if "Learners should understand" in look:
                    i += 1
                    continue
            # collect wrapped continuation lines for the L2 title
            title_parts = [s]
            k = i + 1
            while k < len(content_lines):
                nxt = _norm(content_lines[k])
                if not nxt or _looks_like_header_footer(nxt):
                    k += 1
                    continue
                if l1_code_only_re.match(nxt) or l2_re.match(nxt) or nxt.startswith("N.B") or bullet_re.match(nxt):
                    break
                # append wrapped part (common for long lines in 3.1.2 / 3.1.3)
                title_parts.append(nxt)
                k += 1
            start_l2(_norm(" ".join(title_parts)))
            i = k
            continue

        # Note lines
        if s.startswith("N.B"):
            i += 1
            continue

        # Bullets (L3/L4)
        bm = bullet_re.match(s)
        if bm and current_l2_code:
            # collect wrapped bullet continuations
            bt_parts = [_norm(bm.group(1))]
            k = i + 1
            while k < len(content_lines):
                nxt = _norm(content_lines[k])
                if not nxt or _looks_like_header_footer(nxt):
                    k += 1
                    continue
                if bullet_re.match(nxt) or l2_re.match(nxt) or l1_code_only_re.match(nxt) or nxt.startswith("N.B"):
                    break
                bt_parts.append(nxt)
                k += 1
            bt = _norm(" ".join(bt_parts))
            # Start example groups on bullets containing "for example:"
            if "for example:" in bt.lower() or bt.lower().endswith("for example:"):
                start_example_group(bt)
                i = k
                continue

            # If we're inside an example group, keep simple bullet items nested under it
            if current_example_group_code:
                # Heuristic: end nesting when bullet is a new "how ..." sentence or ends with ":" or contains "for example:"
                if bt.lower().startswith(("how ", "the way ")) or bt.endswith(":") or "for example:" in bt.lower():
                    flush_example_group()
                    # process this bullet again as a top-level L3
                    continue
                add_l4_under_example(bt)
                i = k
                continue

            add_l3_bullet(bt)
            i = k
            continue

        # Wrapped bullet continuations are uncommon here; keep it simple: ignore other lines.
        i += 1

    # De-dupe by code
    uniq: list[Node] = []
    seen = set()
    for n in nodes:
        if n.code in seen:
            continue
        seen.add(n.code)
        uniq.append(n)
    if not uniq:
        raise RuntimeError("No topics parsed.")
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
    print("\n[OK] WJEC 3640 Dance Unit 3 topics scrape complete.")


if __name__ == "__main__":
    main()


