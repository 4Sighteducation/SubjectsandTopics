"""
WJEC GCSE Social Studies (3170) - Topics Scraper (Units 1-4)

Spec (Teaching from 2026 / award from 2028):
  https://www.wjec.co.uk/media/vl4jx4am/wjec-gcse-social-studies-specification-e.pdf

Structure in spec:
  - L0: Unit 1..4
  - L1: Topic (e.g., 1.1 Understanding society)
  - L2: Subtopic (e.g., 1.1.1 Understanding societies)
  - L3: Headings inside amplification (Learners should know/understand/be able to/be aware of, etc.)
  - L4: Bullet points / short prose points
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
    "name": "Social Studies",
    "code": "WJEC-3170",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/vl4jx4am/wjec-gcse-social-studies-specification-e.pdf",
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
    if s.startswith("GCSE SOCIAL STUDIES"):
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


def parse_social_studies(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Find unit blocks (avoid TOC by requiring Areas of content and Section Amplification nearby)
    unit_heading_re = re.compile(r"^Unit\s+([1-4])\s*$", flags=re.IGNORECASE)
    starts: dict[int, int] = {}
    titles: dict[int, str] = {}
    for i, raw in enumerate(lines):
        s = _norm(raw)
        m = unit_heading_re.match(s)
        if not m:
            continue
        u = int(m.group(1))
        window = "\n".join(_norm(x) for x in lines[i : i + 120]).lower()
        if "areas of content" not in window or "section amplification" not in window:
            continue
        starts[u] = i
        # title is next meaningful line
        title = ""
        for j in range(i + 1, min(i + 15, len(lines))):
            t = _norm(lines[j])
            if not t or _looks_like_header_footer(t):
                continue
            if t.lower().startswith(("written examination", "non-examination", "overview of unit")):
                continue
            title = t
            break
        titles[u] = title or f"Unit {u}"

    if not starts:
        raise RuntimeError("Could not locate unit blocks for Social Studies (3170).")

    unit_nums = sorted(starts)
    blocks: dict[int, tuple[int, int]] = {}
    for idx, u in enumerate(unit_nums):
        start = starts[u]
        end = len(lines)
        if idx + 1 < len(unit_nums):
            end = starts[unit_nums[idx + 1]]
        blocks[u] = (start, end)

    areas_re = re.compile(r"^Areas of content$", flags=re.IGNORECASE)
    amp_re = re.compile(r"^Section Amplification$", flags=re.IGNORECASE)
    l1_re = re.compile(r"^(\d+\.\d)\s+(.+)$")
    l2_code_only_re = re.compile(r"^(\d+\.\d+\.\d)\s*$")
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7]\s*(.+)$")
    learners_like_re = re.compile(r"^(Learners should|They should)\b", flags=re.IGNORECASE)

    nodes: list[Node] = []

    for u in unit_nums:
        start, end = blocks[u]
        ucode = f"U{u}"
        nodes.append(Node(code=ucode, title=f"Unit {u}: {titles.get(u,'')}".strip(), level=0, parent=None))

        block = lines[start:end]
        in_areas = False
        in_amp = False

        current_l1: Optional[str] = None
        current_l2: Optional[str] = None
        pending_l2: Optional[str] = None

        current_l3: Optional[str] = None
        l3_idx = 0
        l4_idx = 0

        def ensure_l1(code: str, title: str) -> str:
            nonlocal current_l1
            current_l1 = f"{ucode}_{code.replace('.', '_')}"
            nodes.append(Node(code=current_l1, title=f"{code} {title}".strip(), level=1, parent=ucode))
            return current_l1

        def start_l2(code: str, title: str) -> str:
            nonlocal current_l2, current_l3, l3_idx, l4_idx
            if not current_l1:
                ensure_l1(f"{u}.0", "Content")
            current_l2 = f"{current_l1}_{code.replace('.', '_')}"
            nodes.append(Node(code=current_l2, title=f"{code} {title}".strip(), level=2, parent=current_l1))
            current_l3 = None
            l3_idx = 0
            l4_idx = 0
            return current_l2

        def start_l3(title: str) -> str:
            nonlocal current_l3, l3_idx, l4_idx
            if not current_l2:
                return ""
            l3_idx += 1
            current_l3 = f"{current_l2}_H{l3_idx:02d}"
            nodes.append(Node(code=current_l3, title=title, level=3, parent=current_l2))
            l4_idx = 0
            return current_l3

        def add_l4(text_line: str) -> None:
            nonlocal l4_idx
            parent = current_l3 or current_l2
            if not parent:
                return
            l4_idx += 1
            nodes.append(Node(code=f"{parent}_P{l4_idx:02d}", title=text_line, level=4, parent=parent))

        i = 0
        while i < len(block):
            s = _norm(block[i])
            if not s or _looks_like_header_footer(s):
                i += 1
                continue

            if s.upper().startswith(("3 ASSESSMENT", "4 MALPRACTICE", "5 TECHNICAL INFORMATION", "OPPORTUNITIES FOR INTEGRATION")):
                break

            if areas_re.match(s):
                in_areas = True
                in_amp = False
                i += 1
                continue
            if amp_re.match(s):
                in_amp = True
                in_areas = False
                i += 1
                continue

            if in_areas:
                m1 = l1_re.match(s)
                if m1:
                    code = m1.group(1)
                    title_parts = [m1.group(2)]
                    # collect wrapped L1 title lines until we hit "In this topic..." or another heading
                    j = i + 1
                    while j < len(block):
                        t = _norm(block[j])
                        if not t or _looks_like_header_footer(t):
                            j += 1
                            continue
                        if t.startswith("In this topic learners will"):
                            break
                        if l1_re.match(t) or amp_re.match(t) or areas_re.match(t):
                            break
                        if re.match(r"^\d+\.\d+\.\d", t):
                            break
                        title_parts.append(t)
                        j += 1
                    ensure_l1(code, _norm(" ".join(title_parts)))
                    i = j
                    continue
                i += 1
                continue

            if in_amp:
                # L2 markers
                mco = l2_code_only_re.match(s)
                if mco:
                    pending_l2 = mco.group(1)
                    i += 1
                    continue

                m_inline = re.match(r"^(\d+\.\d+\.\d)\s+(.+)$", s)
                if m_inline:
                    pending_l2 = None
                    start_l2(m_inline.group(1), m_inline.group(2))
                    i += 1
                    continue

                if pending_l2 and not learners_like_re.match(s) and not bullet_re.match(s):
                    # title for pending l2 (may wrap)
                    title_parts = [s]
                    j = i + 1
                    while j < len(block):
                        t = _norm(block[j])
                        if not t or _looks_like_header_footer(t):
                            j += 1
                            continue
                        if learners_like_re.match(t) or bullet_re.match(t) or l2_code_only_re.match(t) or re.match(r"^\d+\.\d+\.\d\s+", t):
                            break
                        title_parts.append(t)
                        j += 1
                    start_l2(pending_l2, _norm(" ".join(title_parts)))
                    pending_l2 = None
                    i = j
                    continue

                # Headings / bullets / prose
                if learners_like_re.match(s) or s.endswith(":"):
                    start_l3(s)
                    i += 1
                    continue

                bm = bullet_re.match(s)
                if bm:
                    if current_l2 and not current_l3:
                        start_l3("Content:")
                    add_l4(_norm(bm.group(1)))
                    i += 1
                    continue

                if current_l2:
                    if not current_l3:
                        start_l3("Content:")
                    add_l4(s)
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
        raise RuntimeError("No topics parsed (Social Studies).")
    return uniq


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("WJEC GCSE SOCIAL STUDIES (3170) - TOPICS SCRAPER (U1-U4)")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3170-social-studies-spec.txt")
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}\n")

    nodes = parse_social_studies(text)

    counts: dict[int, int] = {}
    for n in nodes:
        counts[n.level] = counts.get(n.level, 0) + 1
    print("[INFO] Level breakdown:")
    for lvl in sorted(counts):
        print(f"  - L{lvl}: {counts[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("\n[OK] WJEC 3170 Social Studies topics scrape complete.")


if __name__ == "__main__":
    main()






