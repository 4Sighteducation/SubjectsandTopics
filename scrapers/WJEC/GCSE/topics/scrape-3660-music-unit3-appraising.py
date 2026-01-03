"""
WJEC GCSE Music (3660) - Topics Scraper (Unit 3 Appraising only)

Spec:
  https://www.wjec.co.uk/media/mrvjqftj/wjec-gcse-music-spec-from-2016-e-290125.pdf

User requirement:
  - Only Unit 3: Appraising
  - Areas of study 1-4

Hierarchy:
  - L0: Unit 3: Appraising
  - L1: General musical elements/contexts/language (from the Unit 3 intro) + Areas of Study 1-4
  - L2: Content buckets (implicit "Content" per section, plus "Prepared extract" when present)
  - L3: Bullet points and short statements
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
    "name": "Music",
    "code": "WJEC-3660",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/mrvjqftj/wjec-gcse-music-spec-from-2016-e-290125.pdf",
}

UNIT3_TITLE = "Unit 3: Appraising"


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
    if s.startswith("GCSE MUSIC"):
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


def parse_music_unit3(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Locate Unit 3 start (avoid TOC by requiring AoS listing nearby)
    unit3_re = re.compile(r"^2\.3\s+Unit\s+3\b", flags=re.IGNORECASE)
    unit4_re = re.compile(r"^2\.4\s+Unit\s+4\b", flags=re.IGNORECASE)

    start = None
    for i, raw in enumerate(lines):
        s = _norm(raw)
        if not unit3_re.match(s):
            continue
        window = "\n".join(_norm(x) for x in lines[i : i + 120]).lower()
        if "unit 3" in window and "appraising" in window and "area of study 1" in window:
            start = i
            break
    if start is None:
        # fallback: search the first "Unit 3" heading block
        for i, raw in enumerate(lines):
            s = _norm(raw)
            if s.lower() == "unit 3:" or s.lower().startswith("unit 3"):
                window = "\n".join(_norm(x) for x in lines[i : i + 120]).lower()
                if "area of study 1" in window and "musical forms and devices" in window:
                    start = i
                    break
    if start is None:
        raise RuntimeError("Could not locate Unit 3: Appraising block.")

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if unit4_re.match(_norm(lines[j])):
            end = j
            break

    block = lines[start:end]

    aos_re = re.compile(r"^Area of study\s+([1-4]):\s+(.+)$", flags=re.IGNORECASE)
    elements_hdr = re.compile(r"^Musical Elements$", flags=re.IGNORECASE)
    contexts_hdr = re.compile(r"^Musical Contexts$", flags=re.IGNORECASE)
    language_hdr = re.compile(r"^Musical Language$", flags=re.IGNORECASE)
    assessment_stop = re.compile(r"^Assessment of Unit 3\b", flags=re.IGNORECASE)
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7]\s*(.+)$")

    nodes: list[Node] = []
    nodes.append(Node(code="U3", title=UNIT3_TITLE, level=0, parent=None))

    # General section bucket
    general_code = "U3_general"
    nodes.append(Node(code=general_code, title="Musical elements, contexts and language", level=1, parent="U3"))

    current_l1: Optional[str] = None
    current_l2: Optional[str] = None
    l3_idx = 0

    def start_l2(parent: str, code: str, title: str) -> str:
        nonlocal current_l2, l3_idx
        current_l2 = f"{parent}_{code}"
        nodes.append(Node(code=current_l2, title=title, level=2, parent=parent))
        l3_idx = 0
        return current_l2

    def add_l3(parent: str, text_line: str) -> None:
        nonlocal l3_idx
        l3_idx += 1
        nodes.append(Node(code=f"{parent}_p{l3_idx:03d}", title=text_line, level=3, parent=parent))

    # Track which general subsection we're in
    general_mode: Optional[str] = None
    # Area of study structures
    aos_parent: Optional[str] = None
    aos_num: Optional[str] = None
    aos_content_l2: Optional[str] = None

    i = 0
    while i < len(block):
        s = _norm(block[i])
        if not s or _looks_like_header_footer(s):
            i += 1
            continue
        if assessment_stop.match(s):
            break

        m_aos = aos_re.match(s)
        if m_aos:
            aos_num = m_aos.group(1)
            aos_title = m_aos.group(2).rstrip(".")
            aos_parent = f"U3_AOS{aos_num}"
            nodes.append(Node(code=aos_parent, title=f"Area of study {aos_num}: {aos_title}".strip(), level=1, parent="U3"))
            aos_content_l2 = start_l2(aos_parent, "content", "Content")
            general_mode = None
            i += 1
            continue

        # General headings
        if elements_hdr.match(s):
            general_mode = "elements"
            start_l2(general_code, "elements", "Musical elements")
            i += 1
            continue
        if contexts_hdr.match(s):
            general_mode = "contexts"
            start_l2(general_code, "contexts", "Musical contexts")
            i += 1
            continue
        if language_hdr.match(s):
            general_mode = "language"
            start_l2(general_code, "language", "Musical language")
            i += 1
            continue

        bm = bullet_re.match(s)
        if bm:
            item = _norm(bm.group(1))
            if current_l2:
                add_l3(current_l2, item)
            i += 1
            continue

        # Non-bullet prose: attach to the current content L2 for AoS, otherwise to the current general sub-bucket
        if aos_content_l2:
            add_l3(aos_content_l2, s)
        elif current_l2:
            add_l3(current_l2, s)

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
        raise RuntimeError("No topics parsed.")
    return uniq


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC GCSE MUSIC (3660) - TOPICS SCRAPER (UNIT 3 ONLY)")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3660-music-spec.txt")
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}\n")

    nodes = parse_music_unit3(text)

    counts: dict[int, int] = {}
    for n in nodes:
        counts[n.level] = counts.get(n.level, 0) + 1
    print("[INFO] Level breakdown:")
    for lvl in sorted(counts):
        print(f"  - L{lvl}: {counts[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("\n[OK] WJEC 3660 Music Unit 3 topics scrape complete.")


if __name__ == "__main__":
    main()






