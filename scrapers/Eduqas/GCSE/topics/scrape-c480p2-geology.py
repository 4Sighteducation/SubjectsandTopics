"""
Eduqas GCSE Geology - Topics Scraper

Spec:
  https://www.wjec.co.uk/media/5bcdmd54/eduqas-gcse-geology-spec-from-2017-e.pdf

Entry code in spec: C480P2 (non-#### format).

User requirement:
  - Structure is based around Key Ideas (L0).
  - The spec uses tables with two columns:
      - Knowledge and understanding
      - Geological techniques and skills
    We MUST NOT scrape the techniques/skills column.

Implementation approach:
  - L0: Key Idea N
  - L1: Sub-sections (e.g. 3.1 Planetary Geology)
  - L2: Knowledge/understanding statements (a., b., c. ...)
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
    "name": "Geology",
    "code": "EDUQAS-C480P2",
    "qualification": "GCSE",
    "exam_board": "EDUQAS",
    "pdf_url": "https://www.wjec.co.uk/media/5bcdmd54/eduqas-gcse-geology-spec-from-2017-e.pdf",
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
    if "© WJEC" in s or "© Eduqas" in s or "WJEC CBAC" in s:
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


def parse_geology(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    key_idea_re = re.compile(r"^Key Idea\s+(\d+):\s+(.+)$", flags=re.IGNORECASE)
    section_re = re.compile(r"^(\d+)\.(\d+)\s+(.+)$")  # e.g. 3.1 Planetary Geology
    ku_header_re = re.compile(r"^Knowledge and understanding\b", flags=re.IGNORECASE)
    letter_re = re.compile(r"^([a-e])\.\s*(.+)$", flags=re.IGNORECASE)

    nodes: list[Node] = []

    current_l0: Optional[str] = None
    current_l1: Optional[str] = None
    current_letter: Optional[str] = None
    current_parts: list[str] = []
    in_ku = False

    def flush_letter() -> None:
        nonlocal current_letter, current_parts
        if current_l1 and current_letter and current_parts:
            txt = _norm(" ".join(current_parts))
            if txt:
                nodes.append(Node(code=f"{current_l1}_{current_letter.lower()}", title=f"{current_letter.lower()}. {txt}", level=2, parent=current_l1))
        current_letter = None
        current_parts = []

    for raw in lines:
        s = _norm(raw)
        if not s or _looks_like_header_footer(s):
            continue

        km = key_idea_re.match(s)
        if km:
            flush_letter()
            in_ku = False
            ki_num = km.group(1)
            ki_title = km.group(2)
            current_l0 = f"KI{ki_num}"
            current_l1 = None
            nodes.append(Node(code=current_l0, title=f"Key Idea {ki_num}: {ki_title}", level=0, parent=None))
            continue

        sm = section_re.match(s)
        if sm and current_l0:
            # Stop parsing once we hit the assessment section (3.1 Assessment objectives...)
            if s.lower().startswith("3.1 assessment objectives"):
                break
            flush_letter()
            in_ku = False
            sec_major, sec_minor, sec_title = sm.group(1), sm.group(2), sm.group(3)
            current_l1 = f"{current_l0}_{sec_major}_{sec_minor}"
            nodes.append(Node(code=current_l1, title=f"{sec_major}.{sec_minor} {sec_title}", level=1, parent=current_l0))
            continue

        if ku_header_re.match(s):
            flush_letter()
            in_ku = True
            continue

        if not in_ku or not current_l1:
            continue

        lm = letter_re.match(s)
        if lm:
            flush_letter()
            current_letter = lm.group(1).lower()
            current_parts = [lm.group(2)]
            continue

        # Continuation lines for the current knowledge statement:
        # Keep everything until the next letter/section/key idea, even if it begins with e.g.
        if current_letter:
            # defensive stops (skills column is ignored implicitly because it doesn't start with a./b./c.)
            # but do stop if a new header is encountered
            if s.lower().startswith("geological techniques and skills"):
                continue
            current_parts.append(s)

    flush_letter()

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

    inserted = supabase.table("staging_aqa_topics").insert(
        [
            {
                "subject_id": subject_id,
                "topic_code": n.code,
                "topic_name": n.title,
                "topic_level": n.level,
                "exam_board": SUBJECT["exam_board"],
            }
            for n in nodes
        ]
    ).execute()
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
    print("EDUQAS GCSE GEOLOGY (C480P2) - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/Eduqas/GCSE/topics/debug-eduqas-c480p2-geology-spec.txt")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}")

    nodes = parse_geology(text)
    levels = {}
    for n in nodes:
        levels[n.level] = levels.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(nodes)
    print("\n[OK] EDUQAS C480P2 Geology topics scrape complete.")


if __name__ == "__main__":
    main()






