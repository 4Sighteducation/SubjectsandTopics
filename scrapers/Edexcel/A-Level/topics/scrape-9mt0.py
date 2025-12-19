"""
Edexcel A-Level Music Technology (9MT0) - Topics Scraper (ALL COMPONENTS)

Scrapes specification content for all four components:
  - Component 1: Recording (NEA)
  - Component 2: Technology-based Composition (NEA)
  - Component 3: Listening and analysing (exam)
  - Component 4: Producing and analysing (practical exam)

Hierarchy:
  - L0: Component 1..4
  - L1: Content overview / Assessment overview (and other detected headings)
  - L2: Bullet items / prose statements
  - L3: Sub-bullets (e.g. "o ..." nested under a main bullet)
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
    "name": "Music Technology",
    "code": "9MT0",
    "qualification": "A-Level",
    "exam_board": "EDEXCEL",
    "pdf_url": "https://qualifications.pearson.com/content/dam/pdf/A%20Level/Music-Technology/2017/specification-and-sample-assessments/Pearson_Edexcel_Level_3_Advanced_GCE_in_Music_Technology_Specification_issue3.pdf",
}


def _force_utf8_stdio() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _slug(s: str) -> str:
    s = _norm(s).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "x"


def _looks_like_header_footer(line: str) -> bool:
    s = (line or "").strip()
    if not s:
        return True
    if "Pearson Edexcel Level 3 Advanced GCE in Music Technology" in s:
        return True
    if s.startswith("Specification") and "© Pearson Education Limited" in s:
        return True
    if s.startswith("Issue ") and "© Pearson Education Limited" in s:
        return True
    if re.fullmatch(r"\d{1,3}", s):
        return True
    return False


def _append_wrapped(items: list[str], s: str) -> None:
    s = _norm(s)
    if not s:
        return
    if not items:
        items.append(s)
        return
    if s[0].islower() or s.startswith(("and ", "or ", "including ", "to ", "with ", "for ")):
        items[-1] = _norm(f"{items[-1]} {s}")
    else:
        items.append(s)


def download_pdf_text(url: str) -> str:
    print("[INFO] Downloading PDF...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    reader = PdfReader(BytesIO(resp.content))
    print(f"[OK] Downloaded {len(reader.pages)} pages")
    return "\n".join((p.extract_text() or "") for p in reader.pages)


COMPONENTS = {
    1: "Component 1: Recording",
    2: "Component 2: Technology-based Composition",
    3: "Component 3: Listening and analysing",
    4: "Component 4: Producing and analysing",
}


def _find_component_blocks(lines: list[str]) -> dict[int, tuple[int, int]]:
    """
    Find the best content blocks for each component by choosing the occurrence whose
    nearby window contains 'Content overview'.
    """
    blocks: dict[int, tuple[int, int]] = {}
    # collect candidate starts
    candidates: dict[int, list[int]] = {k: [] for k in COMPONENTS}
    for i, s in enumerate(lines):
        t = s.strip()
        for n, header in COMPONENTS.items():
            # Actual spec uses e.g.:
            # "Component 3: Listening and analysing (*component code: 9MT0/03)"
            # Avoid change-log mentions like "In Component 3: ..."
            if t.lower().startswith("in component"):
                continue
            if re.match(rf"^Component\s+{n}:\s+", t):
                # Avoid picking the Contents-page line like "Component 1: Recording 8"
                # by requiring the real header form (usually includes the component code).
                near = "\n".join(lines[i : i + 6])
                if "(*component code:" not in near.lower():
                    continue
                window = "\n".join(lines[i : i + 200])
                if "Content overview" in window and "Assessment overview" in window:
                    candidates[n].append(i)
    for n in COMPONENTS:
        if not candidates[n]:
            continue
        start = candidates[n][0]
        end = len(lines)
        # end at next component start
        for j in range(start + 1, len(lines)):
            if re.match(r"^Component\s+(?:1|2|3|4):\s+", lines[j].strip()):
                # prefer if that next component occurrence is a real content block
                window = "\n".join(lines[j : j + 160])
                if "Content overview" in window and "Assessment overview" in window:
                    end = j
                    break
        blocks[n] = (start, end)
    return blocks


def _parse_component(component_num: int, block_lines: list[str]) -> list[Node]:
    nodes: list[Node] = []
    comp_code = f"C{component_num}"
    nodes.append(Node(code=comp_code, title=COMPONENTS[component_num], level=0, parent=None))

    # headings we want as L1 nodes
    heading_titles = {
        "Content overview",
        "Assessment overview",
    }

    current_section_code: Optional[str] = None
    current_section_title: Optional[str] = None

    # State for current main bullet (L2)
    current_l2_code: Optional[str] = None
    current_l2_text_parts: list[str] = []
    l2_idx = 0

    # State for current sub-bullet (L3) - we merge wrapped lines into the last created L3 node text
    current_l3_parent: Optional[str] = None
    l3_idx = 0
    l3_text_parts: list[str] = []

    # State for prose paragraph (L2)
    current_para_code: Optional[str] = None
    current_para_parts: list[str] = []

    def _flush_para():
        nonlocal current_para_code, current_para_parts
        if current_section_code and current_para_code and current_para_parts:
            title = _norm(" ".join(current_para_parts))
            if title:
                if len(title) > 900:
                    title = title[:897] + "..."
                nodes.append(Node(code=current_para_code, title=title, level=2, parent=current_section_code))
        current_para_code = None
        current_para_parts = []

    def _flush_l3():
        nonlocal current_l3_parent, l3_idx, l3_text_parts
        if current_l3_parent and l3_text_parts:
            title = _norm(" ".join(l3_text_parts))
            if title:
                if len(title) > 900:
                    title = title[:897] + "..."
                nodes.append(Node(code=f"{current_l3_parent}_S{l3_idx}", title=title, level=3, parent=current_l3_parent))
        l3_text_parts = []

    def flush_l2():
        nonlocal current_l2_code, current_l2_text_parts, current_l3_parent, l3_idx
        # Flush any pending sub-bullet
        _flush_l3()
        current_l3_parent = None
        l3_idx = 0

        if current_section_code and current_l2_code and current_l2_text_parts:
            title = _norm(" ".join(current_l2_text_parts))
            if title:
                if len(title) > 900:
                    title = title[:897] + "..."
                nodes.append(Node(code=current_l2_code, title=title, level=2, parent=current_section_code))
        current_l2_code = None
        current_l2_text_parts = []

    def ensure_section(title: str):
        nonlocal current_section_code, current_section_title, l2_idx
        if current_section_title == title:
            return
        flush_l2()
        _flush_para()
        current_section_title = title
        current_section_code = f"{comp_code}_{_slug(title)}"
        l2_idx = 0
        nodes.append(Node(code=current_section_code, title=title, level=1, parent=comp_code))

    # scan
    i = 0
    while i < len(block_lines):
        raw = block_lines[i]
        s = _norm(raw)
        if not s or _looks_like_header_footer(s):
            i += 1
            continue

        # skip noise rows
        if s in {"Written examination:", "Written/practical examination:"}:
            i += 1
            continue
        if s.startswith(("Written examination:", "Written/practical examination:", "25% of the qualification", "35% of the qualification")):
            i += 1
            continue

        # section headings
        if s in heading_titles:
            ensure_section(s)
            i += 1
            continue

        # if we haven't hit a known section yet, park early content under a generic overview
        if current_section_code is None:
            ensure_section("Overview")

        # bullet parsing
        is_main_bullet = s.startswith(("●", "•"))
        is_sub_bullet = s.startswith("o ") or s.startswith("o\u00a0")

        if is_main_bullet:
            _flush_para()
            flush_l2()
            l2_idx += 1
            current_l2_code = f"{current_section_code}_B{l2_idx}"
            current_l2_text_parts = [_norm(s.lstrip("●•").strip())]
            i += 1
            continue

        if is_sub_bullet:
            _flush_para()
            # attach under current L2 bullet if present; otherwise create a placeholder L2 bullet
            if current_l2_code is None:
                l2_idx += 1
                current_l2_code = f"{current_section_code}_B{l2_idx}"
                current_l2_text_parts = ["(bullet list)"]
                # flush immediately so it exists in DB
                nodes.append(Node(code=current_l2_code, title="(bullet list)", level=2, parent=current_section_code))
                current_l2_text_parts = []
            # new sub-bullet => flush previous sub-bullet
            _flush_l3()
            current_l3_parent = current_l2_code
            l3_idx += 1
            l3_text_parts = [_norm(s[1:].strip())]  # drop leading 'o'
            i += 1
            continue

        # Continuations:
        # - If we're inside a sub-bullet, treat as wrapped continuation of that sub-bullet
        if current_l3_parent and l3_text_parts:
            _append_wrapped(l3_text_parts, s)
            i += 1
            continue

        # - If we're inside a main bullet, treat as wrapped continuation of that bullet
        if current_l2_code is not None and current_l2_text_parts:
            _append_wrapped(current_l2_text_parts, s)
            i += 1
            continue

        # Prose paragraph: accumulate into a single L2 per paragraph under the section
        if current_para_code is None:
            l2_idx += 1
            current_para_code = f"{current_section_code}_P{l2_idx}"
            current_para_parts = [s]
        else:
            _append_wrapped(current_para_parts, s)
        i += 1

    flush_l2()
    _flush_para()
    # de-dupe by code
    uniq: list[Node] = []
    seen = set()
    for n in nodes:
        if n.code in seen:
            continue
        seen.add(n.code)
        uniq.append(n)
    return uniq


def parse_9mt0(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]
    blocks = _find_component_blocks(lines)
    nodes: list[Node] = []
    for n in sorted(blocks.keys()):
        start, end = blocks[n]
        block_lines = lines[start:end]
        nodes.extend(_parse_component(n, block_lines))
    if not nodes:
        raise RuntimeError("No component blocks were parsed for 9MT0 (check PDF extraction).")
    return nodes


def upload_to_staging(nodes: list[Node]) -> None:
    env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
    load_dotenv(env_path)
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    subject_result = supabase.table("staging_aqa_subjects").upsert(
        {
            "subject_name": f"{SUBJECT['name']} (A-Level)",
            "subject_code": SUBJECT["code"],
            "qualification_type": "A-Level",
            "specification_url": SUBJECT["pdf_url"],
            "exam_board": SUBJECT["exam_board"],
        },
        on_conflict="subject_code,qualification_type,exam_board",
    ).execute()
    subject_id = subject_result.data[0]["id"]
    print(f"[OK] Subject ID: {subject_id}")

    # Clear old topics for this subject_id.
    # If deletes are slow/timing out in staging, the recommended workaround is to archive the old
    # subject row by renaming its subject_code and then re-run this scraper (fresh subject_id).
    try:
        deleted_total = 0
        for lvl in (3, 2, 1, 0):
            res = (
                supabase.table("staging_aqa_topics")
                .delete()
                .eq("subject_id", subject_id)
                .eq("topic_level", lvl)
                .execute()
            )
            deleted_total += len(res.data or [])
        print(f"[OK] Cleared old topics ({deleted_total} rows)")
    except Exception as e:
        print(f"[WARN] Could not clear old topics for subject_id {subject_id}: {e}")
        print("[WARN] If you see this repeatedly, rename/archive the subject row (e.g. 9MT0 -> 9MT0_OLD) and rerun.")

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
    print("EDEXCEL A-LEVEL MUSIC TECHNOLOGY (9MT0) - TOPICS SCRAPER (ALL COMPONENTS)")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/Edexcel/A-Level/topics/debug-9mt0-spec.txt")
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}")

    nodes = parse_9mt0(text)
    levels = {}
    for n in nodes:
        levels[n.level] = levels.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(nodes)
    print("\n[OK] 9MT0 topics scrape complete.")


if __name__ == "__main__":
    main()

