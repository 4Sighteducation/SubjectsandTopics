"""
WJEC/Eduqas A Level Geology (teaching from 2017) - Topics Scraper (table-based).

Spec:
  https://www.wjec.co.uk/media/xfrhmzui/eduqas-a-level-geology-2017-e.pdf

Required structure (user-specified):
  L0: FUNDAMENTALS OF GEOLOGY
    L1: F1 Elements, minerals and rocks
    L1: F2 Surface and internal processes of the rock cycle
    L1: F3 Time and change
    L1: F4 Earth structure and global tectonics

  L0: INTERPRETING THE GEOLOGICAL RECORD
    L1: G1 Rock forming processes
    L1: G2 Rock deformation
    L1: G3 Past life and past climates
    L1: G4 Earth materials and natural resources

  L0: GEOLOGICAL THEMES
    L1: T1 Geohazards
    L1: T2 Geological map applications
    L1: T3 Quaternary geology
    L1: T4 Geological evolution of Britain
    L1: T5 Geology of the lithosphere

Then within each topic:
  L2: Key Ideas (table header "Key Idea N: ...")
  L3: lettered points a., b., c. ... (keep text together; don't over-split)
  L4: bullet points under the lettered points (• ...)

IMPORTANT:
- Ignore the "Geological techniques and skills" column entirely.
- Keep wrapped lines together as a single node title (avoid fake splits).
- Dual upload: create separate subjects for EDUQAS and WJEC.
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
    "name": "Geology",
    "qualification": "A-Level",
    "pdf_url": "https://www.wjec.co.uk/media/xfrhmzui/eduqas-a-level-geology-2017-e.pdf",
}

# No explicit A###QS code is visible in the PDF text; use stable internal codes.
SUBJECTS = [
    {**BASE_SUBJECT, "code": "EDUQAS-GEOL-A", "exam_board": "EDUQAS"},
    {**BASE_SUBJECT, "code": "WJEC-GEOL-A", "exam_board": "WJEC"},
]


L0S = [
    ("01_FUND", "FUNDAMENTALS OF GEOLOGY"),
    ("02_RECORD", "INTERPRETING THE GEOLOGICAL RECORD"),
    ("03_THEMES", "GEOLOGICAL THEMES"),
]

TOPICS = [
    ("01_FUND", "F1", "Elements, minerals and rocks"),
    ("01_FUND", "F2", "Surface and internal processes of the rock cycle"),
    ("01_FUND", "F3", "Time and change"),
    ("01_FUND", "F4", "Earth structure and global tectonics"),
    ("02_RECORD", "G1", "Rock forming processes"),
    ("02_RECORD", "G2", "Rock deformation"),
    ("02_RECORD", "G3", "Past life and past climates"),
    ("02_RECORD", "G4", "Earth materials and natural resources"),
    ("03_THEMES", "T1", "Geohazards"),
    ("03_THEMES", "T2", "Geological map applications"),
    ("03_THEMES", "T3", "Quaternary geology"),
    ("03_THEMES", "T4", "Geological evolution of Britain"),
    ("03_THEMES", "T5", "Geology of the lithosphere"),
]

TOPIC_TO_L0 = {tid: l0 for (l0, tid, _t) in TOPICS}


def _force_utf8_stdio() -> None:
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def download_pdf(url: str) -> bytes:
    print("[INFO] Downloading PDF...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.content


def _table_settings() -> dict:
    return {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "edge_min_length": 20,
        "intersection_tolerance": 5,
        "text_tolerance": 3,
    }


def _join_cells(cells: list[str | None]) -> str:
    # Preserve internal newlines (they are important for bullets), but remove trailing spaces.
    parts: list[str] = []
    for c in cells:
        if not c:
            continue
        t = c.strip("\n")
        if t.strip():
            parts.append(t)
    # Join with newline so that splitlines() keeps structure.
    return "\n".join(parts).strip()


TOPIC_HDR_RE = re.compile(r"^\s*Topic\s+([FGT]\d)\s*:\s*(.+)\s*$", flags=re.I)
KEY_IDEA_RE = re.compile(r"^\s*Key\s+Idea\s+(\d+)\s*:\s*(.+)\s*$", flags=re.I)
LETTER_RE = re.compile(r"^\s*([a-z])\.\s*(.+)\s*$", flags=re.I)
BULLET_RE = re.compile(r"^\s*[•\u2022\u25cf\u00b7\uF0B7\u2023]\s*(.+)\s*$")


def build_base_nodes() -> list[Node]:
    nodes: list[Node] = []
    for l0_code, l0_title in L0S:
        nodes.append(Node(code=l0_code, title=l0_title, level=0, parent=None))
    for l0_code, tid, title in TOPICS:
        nodes.append(Node(code=tid, title=f"{tid} {title}", level=1, parent=l0_code))
    return nodes


def parse_tables(pdf_bytes: bytes) -> list[Node]:
    nodes = build_base_nodes()
    seen_codes: set[str] = {n.code for n in nodes}
    next_bullet_idx_by_l3: dict[str, int] = {}

    # State
    current_topic: Optional[str] = None
    topic_hdr_parts: list[str] = []
    in_topic_hdr = False

    current_ki_code: Optional[str] = None
    current_ki_num: Optional[int] = None
    ki_hdr_parts: list[str] = []
    in_ki_hdr = False

    current_l3_code: Optional[str] = None
    l3_letter: Optional[str] = None
    l3_para_idx = 0
    l4_bullet_idx = 0

    def add_node(code: str, title: str, level: int, parent: Optional[str]) -> bool:
        if code in seen_codes:
            return False
        nodes.append(Node(code=code, title=title, level=level, parent=parent))
        seen_codes.add(code)
        return True

    def row_has_letter(text: str) -> bool:
        return any(LETTER_RE.match(ln.strip()) for ln in (text or "").splitlines() if ln.strip())

    def flush_topic_hdr() -> None:
        nonlocal in_topic_hdr, topic_hdr_parts, current_topic
        if not in_topic_hdr or not topic_hdr_parts:
            in_topic_hdr = False
            topic_hdr_parts = []
            return
        hdr = _norm_space(" ".join(topic_hdr_parts))
        m = TOPIC_HDR_RE.match(hdr)
        if m:
            current_topic = m.group(1).upper()
        in_topic_hdr = False
        topic_hdr_parts = []

    def flush_ki_hdr() -> None:
        nonlocal in_ki_hdr, ki_hdr_parts, current_ki_code, current_ki_num
        nonlocal current_l3_code, l3_letter, l3_para_idx, l4_bullet_idx
        if not in_ki_hdr or not ki_hdr_parts or not current_topic:
            in_ki_hdr = False
            ki_hdr_parts = []
            return
        hdr = _norm_space(" ".join(ki_hdr_parts))
        m = KEY_IDEA_RE.match(hdr)
        if m:
            ki_num = int(m.group(1))
            ki_title = _norm_space(m.group(2))
            current_ki_num = ki_num
            current_ki_code = f"{current_topic}_KI{ki_num:02d}"
            # Key idea headers can repeat across page breaks; only create once.
            add_node(
                code=current_ki_code,
                title=f"Key Idea {ki_num}: {ki_title}",
                level=2,
                parent=current_topic,
            )
            # reset L3/L4 state per Key Idea
            current_l3_code = None
            l3_letter = None
            l3_para_idx = 0
            l4_bullet_idx = 0
        in_ki_hdr = False
        ki_hdr_parts = []

    def start_new_l3(letter: Optional[str], title_text: str) -> None:
        nonlocal current_l3_code, l3_letter, l3_para_idx, l4_bullet_idx
        if not current_ki_code:
            return
        l4_bullet_idx = 0
        if letter:
            current_l3_code = f"{current_ki_code}_{letter.lower()}"
            l3_letter = letter.lower()
            if not add_node(
                code=current_l3_code,
                title=f"{letter.lower()}. {title_text}",
                level=3,
                parent=current_ki_code,
            ):
                # Existing letter node (likely repeated on next page) -> treat as continuation
                append_to_current_l3(title_text)
            next_bullet_idx_by_l3.setdefault(current_l3_code, 0)
        else:
            l3_para_idx += 1
            current_l3_code = f"{current_ki_code}_P{l3_para_idx:02d}"
            l3_letter = None
            if add_node(code=current_l3_code, title=title_text, level=3, parent=current_ki_code):
                next_bullet_idx_by_l3.setdefault(current_l3_code, 0)

    def add_l4_bullet(text: str) -> None:
        nonlocal l4_bullet_idx
        if not current_l3_code:
            # If bullet appears without a letter/para, create a paragraph shell
            start_new_l3(None, "Content")
        # Maintain bullet numbering per L3, even if we revisit an existing L3 across page breaks
        nxt = next_bullet_idx_by_l3.get(current_l3_code, 0) + 1
        next_bullet_idx_by_l3[current_l3_code] = nxt
        l4_bullet_idx = nxt
        add_node(
            code=f"{current_l3_code}_B{l4_bullet_idx:03d}",
            title=text,
            level=4,
            parent=current_l3_code,
        )

    def append_to_current_l3(extra: str) -> None:
        # Keep text together: mutate last node title by replacing it (safe because nodes are immutable dataclass)
        if not current_l3_code:
            start_new_l3(None, extra)
            return
        # Find last node with this code
        for i in range(len(nodes) - 1, -1, -1):
            if nodes[i].code == current_l3_code:
                merged = _norm_space(nodes[i].title + " " + extra)
                nodes[i] = Node(code=nodes[i].code, title=merged, level=nodes[i].level, parent=nodes[i].parent)  # type: ignore[misc]
                return

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        settings = _table_settings()
        # Subject content tables start around page 14 (1-indexed). Limit to reduce false matches.
        for page in pdf.pages[10:55]:
            tables = page.extract_tables(settings) or []
            for t in tables:
                # Quick filter: only tables that contain "Topic " or "Key Idea"
                flat = "\n".join([" | ".join([(c or "").strip() for c in row]) for row in t if row])
                if "Topic " not in flat and "Key Idea" not in flat and not LETTER_RE.search(flat):
                    continue

                for row in t:
                    if not row:
                        continue
                    left = _join_cells([row[0] if len(row) > 0 else None, row[1] if len(row) > 1 else None])
                    if not left:
                        continue

                    # Topic header handling (may span multiple rows)
                    if left.lower().startswith("topic "):
                        flush_ki_hdr()
                        in_topic_hdr = True
                        topic_hdr_parts = [left]
                        continue
                    if in_topic_hdr and not left.lower().startswith("key idea") and not row_has_letter(left) and left.strip().lower() != "knowledge and understanding":
                        topic_hdr_parts.append(left)
                        continue
                    if in_topic_hdr and (left.lower().startswith("key idea") or left.strip().lower() == "knowledge and understanding" or row_has_letter(left)):
                        flush_topic_hdr()
                        # fall through to process current row

                    # Key idea header handling (may span multiple rows)
                    if left.lower().startswith("key idea"):
                        flush_topic_hdr()
                        in_ki_hdr = True
                        ki_hdr_parts = [left]
                        continue
                    if in_ki_hdr and not row_has_letter(left) and not left.lower().startswith("topic ") and left.strip().lower() != "knowledge and understanding":
                        ki_hdr_parts.append(left)
                        continue
                    if in_ki_hdr and (row_has_letter(left) or left.strip().lower() == "knowledge and understanding" or left.lower().startswith("topic ")):
                        flush_ki_hdr()
                        # fall through to process current row

                    # If we see a letter but we haven't flushed Key Idea yet, do so
                    if in_ki_hdr and row_has_letter(left):
                        flush_ki_hdr()

                    # Skip header row (after we had a chance to flush topic/key-idea headers)
                    if left.strip().lower() == "knowledge and understanding":
                        continue

                    # Ignore until we know topic + key idea
                    if not current_topic or current_topic not in TOPIC_TO_L0:
                        continue
                    if not current_ki_code:
                        continue

                    # Process content lines (can include multiple lines)
                    lines = [ln.strip() for ln in left.splitlines() if ln.strip()]
                    for ln in lines:
                        m_letter = LETTER_RE.match(ln)
                        if m_letter:
                            letter = m_letter.group(1)
                            txt = _norm_space(m_letter.group(2))
                            # Some tables repeat the same lettered point across page breaks; treat repeats as continuation.
                            target_code = f"{current_ki_code}_{letter.lower()}" if current_ki_code else None
                            if target_code and target_code in seen_codes:
                                current_l3_code = target_code
                                l3_letter = letter.lower()
                                next_bullet_idx_by_l3.setdefault(current_l3_code, next_bullet_idx_by_l3.get(current_l3_code, 0))
                                append_to_current_l3(txt)
                            else:
                                start_new_l3(letter, txt)
                            continue

                        m_b = BULLET_RE.match(ln)
                        if m_b:
                            add_l4_bullet(_norm_space(m_b.group(1)))
                            continue

                        # Continuation text: if we have a current letter/para, append; else create a para
                        append_to_current_l3(_norm_space(ln))

    # flush any headers at end
    flush_topic_hdr()
    flush_ki_hdr()

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

    # Clear old topics (deepest-first), batched
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

    # Insert topics in batches to avoid payload limits
    inserted_rows: list[dict] = []
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
    INS_BATCH = 500
    for i in range(0, len(payload), INS_BATCH):
        part = payload[i : i + INS_BATCH]
        res = supabase.table("staging_aqa_topics").insert(part).execute()
        inserted_rows.extend(res.data or [])
    print(f"[OK] Uploaded {len(inserted_rows)} topics")

    code_to_id = {row["topic_code"]: row["id"] for row in inserted_rows}

    # Link parents. PostgREST doesn't support a true "bulk update with distinct values",
    # and upsert requires NOT NULL columns. Keep it simple and reliable.
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
    print("EDUQAS/WJEC A-LEVEL GEOLOGY (2017) - TOPICS SCRAPER (TABLE PARSER)")
    print("=" * 80)
    print(f"Spec: {BASE_SUBJECT['pdf_url']}")

    pdf_bytes = download_pdf(BASE_SUBJECT["pdf_url"])
    nodes = parse_tables(pdf_bytes)
    # Guard against duplicate topic_codes (would violate staging unique constraint)
    seen: set[str] = set()
    dups: list[str] = []
    for n in nodes:
        if n.code in seen:
            dups.append(n.code)
        seen.add(n.code)
    if dups:
        raise RuntimeError(f"Duplicate topic_code(s) generated: {sorted(set(dups))[:20]}")

    by_level: dict[int, int] = {}
    for n in nodes:
        by_level[n.level] = by_level.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(by_level):
        print(f"  - L{lvl}: {by_level[lvl]}")

    if not any(n.level >= 2 for n in nodes):
        raise RuntimeError("No Key Ideas parsed (L2+). Check table parsing.")

    for subj in SUBJECTS:
        print(f"\n[INFO] Uploading for exam_board={subj['exam_board']} code={subj['code']} ...")
        upload_to_staging(subject=subj, nodes=nodes)

    print("[OK] Geology scrape complete (uploaded to EDUQAS + WJEC).")


if __name__ == "__main__":
    main()


