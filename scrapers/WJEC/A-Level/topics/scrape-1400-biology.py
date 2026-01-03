"""
WJEC GCE AS/A Level Biology (2015 spec) - Topics Scraper

Spec:
  https://www.wjec.co.uk/media/mxbh1zaf/wjec-gce-biology-spec-from-2015-e-101025.pdf

Entry-code mapping in spec:
  - AS Units 1-2: 2400U1/2400U2, AS cash-in: 2400QS/2400CS
  - A2 Units 3-5: 1400U3/1400U4/1400U5, A level cash-in: 1400QS/1400CS

We model the full A level content under one subject code (A level cash-in): WJEC-1400CS.

Hierarchy:
  - L0: Unit 1..5
  - L1: Topic within unit (numbered 1..n)
  - L2: lettered statements (a), (b), ... (wrapped lines joined)
  - L2: Specified practical work (shell)
  - L3: practical-work bullets

Unit 5 is a practical exam with admin-style prose; we upload a concise shell only.
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
    "name": "Biology",
    "code": "WJEC-1400CS",
    "qualification": "A-Level",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/mxbh1zaf/wjec-gce-biology-spec-from-2015-e-101025.pdf",
}


UNIT_TITLES = {
    1: "AS Unit 1: Basic Biochemistry and Cell Organisation",
    2: "AS Unit 2: Biodiversity and Physiology of Body Systems",
    3: "A2 Unit 3: Energy, Homeostasis and the Environment",
    4: "A2 Unit 4: Variation, Inheritance and Options",
    5: "A2 Unit 5: Practical examination",
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
    if s.startswith("GCE AS and A Level Biology"):
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


def parse_biology(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Unit boundaries
    unit_hdr_re = re.compile(r"^(AS|A2)\s+UNIT\s+([1-5])\b", flags=re.IGNORECASE)
    unit_starts: dict[int, int] = {}
    for i, raw in enumerate(lines):
        s = _norm(raw)
        m = unit_hdr_re.match(s)
        if not m:
            continue
        u = int(m.group(2))
        # accept if "This unit includes the following topics" appears nearby
        window = "\n".join(_norm(x) for x in lines[i : i + 60]).lower()
        if "this unit includes the following topics" in window:
            unit_starts[u] = i

    if not unit_starts:
        raise RuntimeError("Could not locate Biology unit starts.")

    unit_nums = sorted(unit_starts)
    blocks: dict[int, tuple[int, int]] = {}
    for idx, u in enumerate(unit_nums):
        start = unit_starts[u]
        end = len(lines)
        if idx + 1 < len(unit_nums):
            end = unit_starts[unit_nums[idx + 1]]
        blocks[u] = (start, end)

    # Topic headers are like: "1. Chemical elements are joined together ..."
    topic_re = re.compile(r"^(\d+)\.\s+(.+)$")
    letter_re = re.compile(r"^\(([a-z])\)\s*(.+)$", flags=re.IGNORECASE)
    practical_hdr_re = re.compile(r"^SPECIFIED PRACTICAL WORK$", flags=re.IGNORECASE)
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7]\s*(.+)$")

    nodes: list[Node] = []

    for u in unit_nums:
        ucode = f"U{u}"
        nodes.append(Node(code=ucode, title=UNIT_TITLES.get(u, f"Unit {u}"), level=0, parent=None))

        start, end = blocks[u]
        block = lines[start:end]

        if u == 5:
            # Practical exam: keep small shell
            sk = f"{ucode}_overview"
            nodes.append(Node(code=sk, title="Practical examination overview", level=1, parent=ucode))
            nodes.append(Node(code=f"{sk}_1", title="Two tasks: Experimental Task (20 marks) and Practical Analysis Task (30 marks)", level=2, parent=sk))
            nodes.append(Node(code=f"{sk}_2", title="Main topic areas for assessment released each spring term", level=2, parent=sk))
            continue

        current_topic: Optional[str] = None
        current_practical: Optional[str] = None
        practical_b_idx = 0

        cur_letter: Optional[str] = None
        cur_parts: list[str] = []

        def flush_letter() -> None:
            nonlocal cur_letter, cur_parts
            if current_topic and cur_letter and cur_parts:
                txt = _norm(" ".join(cur_parts))
                nodes.append(Node(code=f"{current_topic}_{cur_letter}", title=txt, level=2, parent=current_topic))
            cur_letter = None
            cur_parts = []

        i = 0
        while i < len(block):
            s = _norm(block[i])
            if not s or _looks_like_header_footer(s):
                i += 1
                continue

            # stop at assessment section
            if s.upper().startswith(("3. ASSESSMENT", "3 ASSESSMENT", "4 TECHNICAL INFORMATION")):
                break

            # skip non-content headings
            if s in {"Overview", "Working scientifically", "Mathematical Skills", "How Science Works"}:
                i += 1
                continue
            if s.lower().startswith("learners should be able to demonstrate and apply"):
                i += 1
                continue

            mt = topic_re.match(s)
            if mt:
                # avoid TOC lines ("1. Introduction 5")
                if "introduction" in mt.group(2).lower() and mt.group(1) == "1":
                    i += 1
                    continue
                # if we are inside content block and hit a topic title, accept
                # (these headers appear twice: in unit topic list and at start of topic section; de-dupe by code later)
                flush_letter()
                practical_b_idx = 0
                current_practical = None
                tnum = mt.group(1)
                ttitle = mt.group(2)
                # ignore "1. Introduction", etc outside content
                if ttitle.lower().startswith(("introduction", "aims and objectives", "prior learning", "equality and fair access", "welsh baccalaureate", "welsh perspective")):
                    i += 1
                    continue
                current_topic = f"{ucode}_T{int(tnum):02d}"
                nodes.append(Node(code=current_topic, title=f"{tnum}. {ttitle}".strip(), level=1, parent=ucode))
                i += 1
                continue

            if practical_hdr_re.match(s):
                flush_letter()
                if current_topic:
                    current_practical = f"{current_topic}_practical"
                    nodes.append(Node(code=current_practical, title="Specified practical work", level=2, parent=current_topic))
                    practical_b_idx = 0
                i += 1
                continue

            bm = bullet_re.match(s)
            if bm and current_practical:
                practical_b_idx += 1
                nodes.append(Node(code=f"{current_practical}_b{practical_b_idx:02d}", title=_norm(bm.group(1)), level=3, parent=current_practical))
                i += 1
                continue

            ml = letter_re.match(s)
            if ml and current_topic:
                flush_letter()
                cur_letter = ml.group(1).lower()
                cur_parts = [ml.group(2)]
                i += 1
                continue

            if cur_letter and current_topic:
                # stop if next marker begins
                if topic_re.match(s) or practical_hdr_re.match(s) or letter_re.match(s):
                    i += 1
                    continue
                cur_parts.append(s)
                i += 1
                continue

            i += 1

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


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC GCE AS/A LEVEL BIOLOGY - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/A-Level/topics/debug-wjec-1400-biology-spec.txt")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}\n")

    nodes = parse_biology(text)

    counts: dict[int, int] = {}
    for n in nodes:
        counts[n.level] = counts.get(n.level, 0) + 1
    print("[INFO] Level breakdown:")
    for lvl in sorted(counts):
        print(f"  - L{lvl}: {counts[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("\n[OK] WJEC Biology (A-Level) topics scrape complete.")


if __name__ == "__main__":
    main()






