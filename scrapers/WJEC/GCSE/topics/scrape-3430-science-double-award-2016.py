"""
WJEC GCSE Science (Double Award) (3430QD) - Topics Scraper (Teaching from 2016 / award from 2018)

Spec:
  https://www.wjec.co.uk/media/lknfmp5c/wjec-gcse-science-double-award-spec-from-2016.pdf

PDF structure:
  - Units 1-6: Biology/Chemistry/Physics content with Topic headings (e.g. 1.1 ...), then
    lettered content statements (a)-(l), plus "SPECIFIED PRACTICAL WORK" bullets.
  - Unit 7: Practical Assessment (NEA) is largely administrative; we include a light shell only.

Hierarchy:
  - L0: Unit
  - L1: Topic (e.g. 1.1 Cells and movement across cell membranes)
  - L2: (a)/(b)/... statements (joined across wrapped lines)
  - L2: "Specified practical work" (if present)
  - L3: practical-work bullets
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
    "name": "Science (Double Award)",
    "code": "WJEC-3430QD",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/lknfmp5c/wjec-gcse-science-double-award-spec-from-2016.pdf",
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
    if s.startswith("GCSE SCIENCE (Double Award)"):
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


def parse_science_double_award(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    unit_start_re = re.compile(r"^2\.(\d)\s+Unit\s+([1-7])\b", flags=re.IGNORECASE)

    starts: dict[int, int] = {}
    unit_titles: dict[int, str] = {}
    for i, raw in enumerate(lines):
        s = _norm(raw)
        m = unit_start_re.match(s)
        if not m:
            continue
        u = int(m.group(2))
        # accept as real unit only if topic numbering appears soon
        window = "\n".join(_norm(x) for x in lines[i : i + 120]).lower()
        if "this unit includes the following topics" not in window:
            continue
        starts[u] = i
        # title is in the next couple of lines like "(Double Award) BIOLOGY 1"
        title = ""
        for j in range(i + 1, min(i + 10, len(lines))):
            t = _norm(lines[j])
            if not t or _looks_like_header_footer(t):
                continue
            if t.lower().startswith(("written examination", "15% of qualification", "this unit includes")):
                continue
            if t.startswith("(") and ")" in t:
                # e.g. "(Double Award) BIOLOGY 1" -> "Biology 1"
                after = t.split(")", 1)[-1].strip()
                title = after.title() if after else t
                break
            title = t.title()
            break
        unit_titles[u] = title or f"Unit {u}"

    if not starts:
        raise RuntimeError("Could not locate unit blocks (2.x Unit 1..7).")

    unit_nums = sorted(starts)
    blocks: dict[int, tuple[int, int]] = {}
    for idx, u in enumerate(unit_nums):
        start = starts[u]
        end = len(lines)
        if idx + 1 < len(unit_nums):
            end = starts[unit_nums[idx + 1]]
        blocks[u] = (start, end)

    # Topic headings inside units: "1.1 CELLS AND MOVEMENT ..."
    topic_hdr_re = re.compile(r"^(\d+\.\d)\s+([A-Z0-9][A-Z0-9 ,&'’/\\-]+)$")
    # Lettered content: (a) ...
    letter_re = re.compile(r"^\(([a-z])\)\s*(.+)$")
    practical_hdr_re = re.compile(r"^SPECIFIED PRACTICAL WORK$", flags=re.IGNORECASE)
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7]\s*(.+)$")

    def nice_title(s: str) -> str:
        # Avoid mangling acronyms too much; title-case only if it looks like full caps.
        if s.isupper():
            return s.title()
        return s

    nodes: list[Node] = []

    for u in unit_nums:
        start, end = blocks[u]
        ucode = f"U{u}"
        nodes.append(Node(code=ucode, title=f"Unit {u}: {unit_titles.get(u,'')}".strip(), level=0, parent=None))

        block = lines[start:end]

        if u == 7:
            # Unit 7 is Practical Assessment; keep a minimal shell (avoid huge admin text)
            sk = f"{ucode}_OVERVIEW"
            nodes.append(Node(code=sk, title="Practical Assessment overview", level=1, parent=ucode))
            nodes.append(Node(code=f"{sk}_1", title="Externally marked; carried out in centres; recommended final year", level=2, parent=sk))
            continue

        current_topic: Optional[str] = None
        current_practical: Optional[str] = None

        cur_letter: Optional[str] = None
        cur_parts: list[str] = []

        def flush_letter() -> None:
            nonlocal cur_letter, cur_parts
            if current_topic and cur_letter and cur_parts:
                txt = _norm(" ".join(cur_parts))
                nodes.append(Node(code=f"{current_topic}_{cur_letter}", title=txt, level=2, parent=current_topic))
            cur_letter = None
            cur_parts = []

        practical_b_idx = 0

        i = 0
        while i < len(block):
            s = _norm(block[i])
            if not s or _looks_like_header_footer(s):
                i += 1
                continue
            # skip the per-topic prefaces
            if s in {"Overview", "Working Scientifically", "Mathematical skills"}:
                # skip until blank line or until we hit the core "Learners should..." / (a)
                i += 1
                continue
            if s.lower().startswith("learners should be able to demonstrate and apply"):
                i += 1
                continue

            m_topic = topic_hdr_re.match(s)
            if m_topic:
                flush_letter()
                practical_b_idx = 0
                current_practical = None
                tcode = m_topic.group(1)
                ttitle = nice_title(m_topic.group(2))
                current_topic = f"{ucode}_{tcode.replace('.', '_')}"
                nodes.append(Node(code=current_topic, title=f"{tcode} {ttitle}".strip(), level=1, parent=ucode))
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

            m_letter = letter_re.match(s)
            if m_letter and current_topic:
                flush_letter()
                cur_letter = m_letter.group(1)
                cur_parts = [m_letter.group(2)]
                i += 1
                continue

            # wrapped line continuation for letter statements
            if cur_letter and current_topic:
                # stop if a new letter or new topic/practical begins
                if topic_hdr_re.match(s) or practical_hdr_re.match(s) or letter_re.match(s):
                    continue
                # ignore "SPECIFIED PRACTICAL WORK" etc handled above
                cur_parts.append(s)
                i += 1
                continue

            i += 1

        flush_letter()

    # De-dupe
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
    print("WJEC GCSE SCIENCE (DOUBLE AWARD) (3430QD) - TOPICS SCRAPER (2016 SPEC)")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3430qd-science-double-spec.txt")
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}\n")

    nodes = parse_science_double_award(text)

    counts: dict[int, int] = {}
    for n in nodes:
        counts[n.level] = counts.get(n.level, 0) + 1
    print("[INFO] Level breakdown:")
    for lvl in sorted(counts):
        print(f"  - L{lvl}: {counts[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("\n[OK] WJEC 3430QD Science (Double Award) topics scrape complete.")


if __name__ == "__main__":
    main()






