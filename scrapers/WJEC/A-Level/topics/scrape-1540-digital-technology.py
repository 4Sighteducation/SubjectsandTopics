"""
WJEC GCE AS/A Level Digital Technology (2022 spec) - Topics Scraper

Spec:
  https://www.wjec.co.uk/media/0guiggrp/wjec-gce-digital-technology-specification-e-29-06-2022.pdf

Entry-code mapping in spec:
  - AS Units 1-2: 2540U1/2540U2, AS cash-in: 2540QS/2540CS
  - A2 Units 3-4: 1540U3/1540U4, A level cash-in: 1540QS/1540CS

We model the full A level content under one subject code (A level cash-in): WJEC-1540CS.

PDF structure within each unit:
  - Unit heading (2.1 AS Unit 1, 2.2 AS Unit 2, 2.3 A Level Unit 3, 2.4 A Level Unit 4)
  - Areas of content list (2.1.1 ... etc)
  - For each area, a "Content  Amplification" table with (a)/(b)/(c) rows:
      - Row title in the "Content" column
      - Row amplification prose + "Learners should ..." headings + bullet lists

Hierarchy:
  - L0: Unit 1..4
  - L1: Area of content (e.g., 2.1.1 ...)
  - L2: Content row (a/b/c...) with row title
  - L3: "Learners should ..." headings (and other colon headings)
  - L4: bullets / short prose points
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
    "name": "Digital Technology",
    "code": "WJEC-1540CS",
    "qualification": "A-Level",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/0guiggrp/wjec-gce-digital-technology-specification-e-29-06-2022.pdf",
}


UNIT_TITLES = {
    1: "AS Unit 1: Innovation in Digital Technology",
    2: "AS Unit 2: Creative Digital Practices",
    3: "A2 Unit 3: Connected Systems",
    4: "A2 Unit 4: Digital Solutions",
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
    if s.startswith("GCE AS AND A LEVEL DIGITAL TECHNOLOGY"):
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

    # IMPORTANT: delete from the existing max level in DB (previous runs may have deeper levels)
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

    # Delete in batches (Supabase/PostgREST statement timeout can be aggressive on large deletes)
    deleted_total = 0
    batch_size = 500
    for lvl in range(max_level, -1, -1):
        while True:
            # fetch a small batch of ids at this level
            fetch = (
                supabase.table("staging_aqa_topics")
                .select("id")
                .eq("subject_id", subject_id)
                .eq("topic_level", lvl)
                .limit(batch_size)
                .execute()
            )
            ids = [r["id"] for r in (fetch.data or [])]
            if not ids:
                break
            del_res = supabase.table("staging_aqa_topics").delete().in_("id", ids).execute()
            deleted_total += len(del_res.data or ids)
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


def parse_digital_technology(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    unit_hdr_re = re.compile(r"^2\.(\d)\s+(AS|A\s*Level)\s+Unit\s+([1-4])\b", flags=re.IGNORECASE)
    starts: dict[int, int] = {}
    for i, raw in enumerate(lines):
        s = _norm(raw)
        m = unit_hdr_re.match(s)
        if not m:
            continue
        u = int(m.group(3))
        # Unit 2/4 have longer NEA intro blocks; use a larger window.
        window = "\n".join(_norm(x) for x in lines[i : i + 520]).lower()
        # Accept if we can see area numbering for this unit + content amplification tables.
        # (Prevents TOC matches while being robust to long NEA intros.)
        if (f"2.{u}." in window) and ("content amplification" in window):
            starts[u] = i

    if not starts:
        raise RuntimeError("Could not locate unit blocks for Digital Technology.")

    unit_nums = sorted(starts)
    blocks: dict[int, tuple[int, int]] = {}
    for idx, u in enumerate(unit_nums):
        start = starts[u]
        end = len(lines)
        if idx + 1 < len(unit_nums):
            end = starts[unit_nums[idx + 1]]
        blocks[u] = (start, end)

    area_re = re.compile(r"^(2\.[1-4]\.\d+(?:\.\d+)?[a-z]?)\s+(.+)$", flags=re.IGNORECASE)
    content_amp_re = re.compile(r"^Content\s+Amplification$", flags=re.IGNORECASE)
    row_re = re.compile(r"^\(([a-z])\)\s*(.*)$", flags=re.IGNORECASE)
    learners_re = re.compile(r"^(Learners should|They should)\b", flags=re.IGNORECASE)
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7]\s*(.+)$")

    nodes: list[Node] = []

    def _split_title_and_content(rest: str) -> tuple[str, str]:
        """
        Some row titles leak the first words of amplification onto the same line, e.g.:
          '(d) Impacts of the IoT Learners should understand ...'
        We split at the first 'Learners should' / 'They should' if present.
        Returns (title, trailing_content)
        """
        if not rest:
            return "", ""
        m = re.search(r"\b(Learners should|They should)\b", rest, flags=re.IGNORECASE)
        if not m:
            return rest, ""
        return _norm(rest[: m.start()]), _norm(rest[m.start() :])

    for u in unit_nums:
        ucode = f"U{u}"
        nodes.append(Node(code=ucode, title=UNIT_TITLES.get(u, f"Unit {u}"), level=0, parent=None))

        start, end = blocks[u]
        block = lines[start:end]

        current_area: Optional[str] = None
        current_row: Optional[str] = None
        in_table = False

        pending_row_letter: Optional[str] = None
        pending_row_title_parts: list[str] = []

        def start_area(code: str, title: str) -> None:
            nonlocal current_area, current_row, in_table
            current_area = f"{ucode}_{code.replace('.', '_')}"
            nodes.append(Node(code=current_area, title=f"{code} {title}".strip(), level=1, parent=ucode))
            current_row = None
            in_table = False

        def start_row(letter: str, title: str) -> None:
            nonlocal current_row
            if not current_area:
                return
            current_row = f"{current_area}_{letter.lower()}"
            nodes.append(Node(code=current_row, title=f"({letter.lower()}) {title}".strip(), level=2, parent=current_area))

        i = 0
        while i < len(block):
            s = _norm(block[i])
            if not s or _looks_like_header_footer(s):
                i += 1
                continue

            if s.upper().startswith(("3 ASSESSMENT", "4 MALPRACTICE", "5 TECHNICAL INFORMATION", "APPENDIX")):
                break

            m_area = area_re.match(s)
            if m_area and not s.lower().startswith(("content", "amplification")):
                start_area(m_area.group(1), m_area.group(2))
                i += 1
                continue

            if content_amp_re.match(s):
                in_table = True
                i += 1
                continue

            if in_table:
                mrow = row_re.match(s)
                if mrow:
                    if pending_row_letter and pending_row_title_parts:
                        start_row(pending_row_letter, _norm(" ".join(pending_row_title_parts)))
                        pending_row_letter = None
                        pending_row_title_parts = []

                    letter = mrow.group(1)
                    rest = _norm(mrow.group(2) or "")
                    title, trailing = _split_title_and_content(rest)
                    if title:
                        # Row titles often wrap across lines (e.g. "The Internet of" + "Things (IoT)")
                        title_parts = [title]
                        j = i + 1
                        while j < len(block):
                            nxt = _norm(block[j])
                            if not nxt or _looks_like_header_footer(nxt):
                                j += 1
                                continue
                            if learners_re.match(nxt) or bullet_re.match(nxt) or row_re.match(nxt) or area_re.match(nxt) or content_amp_re.match(nxt):
                                break
                            # Only treat as title continuation if it looks like a short fragment (not a sentence)
                            if "." in nxt:
                                break
                            if len(nxt) > 70:
                                break
                            title_parts.append(nxt)
                            # stop after a couple of fragments
                            if len(title_parts) >= 3:
                                break
                            j += 1
                        start_row(letter, _norm(" ".join(title_parts)))
                        i = max(i + 1, j)
                        continue
                    else:
                        pending_row_letter = letter
                        pending_row_title_parts = []
                    i += 1
                    continue

                if pending_row_letter:
                    if learners_re.match(s) or bullet_re.match(s) or row_re.match(s) or area_re.match(s) or content_amp_re.match(s):
                        start_row(pending_row_letter, "Content")
                        pending_row_letter = None
                        pending_row_title_parts = []
                        continue
                    if "." in s:
                        title = _norm(" ".join(pending_row_title_parts)) or "Content"
                        start_row(pending_row_letter, title)
                        pending_row_letter = None
                        pending_row_title_parts = []
                        # fallthrough
                    else:
                        pending_row_title_parts.append(s)
                        i += 1
                        continue

                # Max depth = L2: ignore amplification content.
                i += 1
                continue

            i += 1

        if pending_row_letter:
            start_row(pending_row_letter, _norm(" ".join(pending_row_title_parts)) or "Content")

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
    print("WJEC GCE AS/A LEVEL DIGITAL TECHNOLOGY - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/A-Level/topics/debug-wjec-1540-digital-technology-spec.txt")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}\n")

    nodes = parse_digital_technology(text)

    counts: dict[int, int] = {}
    for n in nodes:
        counts[n.level] = counts.get(n.level, 0) + 1
    print("[INFO] Level breakdown:")
    for lvl in sorted(counts):
        print(f"  - L{lvl}: {counts[lvl]}")

    upload_to_staging(subject=SUBJECT, nodes=nodes)
    print("\n[OK] WJEC Digital Technology (A-Level) topics scrape complete.")


if __name__ == "__main__":
    main()


