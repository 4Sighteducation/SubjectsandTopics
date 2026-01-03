"""
Edexcel A-Level Music Technology (9MT0) - Topics Scraper (ALL COMPONENTS)

Scrapes specification content for all four components:
  - Component 1: Recording (NEA)
  - Component 2: Technology-based Composition (NEA)
  - Component 3: Listening and analysing (exam)
  - Component 4: Producing and analysing (practical exam)

Hierarchy:
  - L0: Component 1..4
  - L1: Topic rows (e.g. "1.1 Capture of sound")
  - L2: Content rows (from the table "Content" column)
  - L3: Skills bullets (from the table "Skills, knowledge and understanding" column)

Design goal:
Only model the structured "Area of Study ... / Topic Content Skills..." tables.
Skip narrative prose, assessment admin, and PDF headers/footers to avoid noisy/irrelevant trees.
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
    Find the main component content blocks (NOT the early "Qualification at a glance" table).

    The spec includes multiple occurrences of "Component N: ...":
    - Contents / qualification-at-a-glance (often includes "(*component code: 9MT0/0N)")
    - The real component section later, which starts with an "Overview" heading.

    We specifically pick the later, real section (e.g. pages ~8, 21, 34, 42 in extracted text).
    """
    blocks: dict[int, tuple[int, int]] = {}

    def _is_main_component_header_at(i: int, n: int) -> bool:
        """True if line i is the real component header (followed by 'Overview'), not TOC/at-a-glance."""
        t = (lines[i] or "").strip()
        if not re.fullmatch(rf"Component\s+{n}:\s+.+", t):
            return False
        # Exclude at-a-glance headers (contain component code)
        near = "\n".join((lines[i : i + 8]))
        if "(*component code:" in near.lower():
            return False
        # Exclude contents-page style lines (end with a page number)
        if re.search(r"\s\d{1,3}$", t):
            return False
        # Real section is immediately followed by "Overview"
        window = "\n".join(lines[i : i + 25])
        if "Overview" not in window:
            return False
        return True

    # find starts
    starts: dict[int, int] = {}
    for n in COMPONENTS:
        for i in range(len(lines)):
            if _is_main_component_header_at(i, n):
                starts[n] = i
                break

    # compute ends
    for n, start in starts.items():
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if any(_is_main_component_header_at(j, k) for k in COMPONENTS if k != n):
                end = j
                break
            # also stop at admin section if it occurs inside the slice
            sj = (lines[j] or "").strip()
            if sj.startswith("Assessment Objectives") or sj.startswith("3 Administration and general"):
                end = j
                break
        blocks[n] = (start, end)
    return blocks


def _parse_component(component_num: int, block_lines: list[str]) -> list[Node]:
    nodes: list[Node] = []
    comp_code = f"C{component_num}"
    nodes.append(Node(code=comp_code, title=COMPONENTS[component_num], level=0, parent=None))

    # NOTE: This function is being rewritten to parse AoS tables (Topic/Content/Skills) only.
    # We only parse the structured AoS tables, which always include a header like:
    #   "Topic Content Skills, knowledge and understanding"
    # and contain topic codes like "1.1", "2.4", "3.1" etc.
    topic_re = re.compile(r"^(\d{1,2})\.(\d{1,2})\s+(.+)$")
    area_re = re.compile(r"^Area of Study\s+\d+\s*:", flags=re.IGNORECASE)

    def _is_table_header_line(s: str) -> bool:
        t = (s or "").strip()
        if not t:
            return False
        # The header sometimes wraps onto 2 lines; we treat any "Topic Content" line as a header.
        if t.startswith("Topic Content"):
            return True
        if t in {"understanding", "Skills, knowledge and", "Skills, knowledge and understanding"}:
            return True
        return False

    current_topic_code: Optional[str] = None
    current_topic_title_parts: list[str] = []

    current_content_parts: list[str] = []
    current_bullets: list[str] = []
    content_idx = 0
    seen_any_table = False

    def _finalize_topic_title() -> None:
        if not current_topic_code:
            return
        title = _norm(" ".join(current_topic_title_parts))
        title = re.sub(r"\s+continued$", "", title, flags=re.IGNORECASE).strip()
        if not title:
            title = "(topic)"
        if any(n.code == current_topic_code for n in nodes):
            return
        m = re.search(r"_T(\d{1,2})_(\d{1,2})$", current_topic_code)
        prefix = f"{m.group(1)}.{m.group(2)} " if m else ""
        nodes.append(Node(code=current_topic_code, title=f"{prefix}{title}".strip(), level=1, parent=comp_code))

    def _flush_content_row() -> None:
        nonlocal current_content_parts, current_bullets, content_idx
        if not current_topic_code or not current_content_parts:
            current_content_parts = []
            current_bullets = []
            return
        _finalize_topic_title()
        content_idx += 1
        content_title = _norm(" ".join(current_content_parts))
        if content_title:
            if len(content_title) > 900:
                content_title = content_title[:897] + "..."
            content_code = f"{current_topic_code}_C{content_idx}"
            nodes.append(Node(code=content_code, title=content_title, level=2, parent=current_topic_code))
            for bi, b in enumerate(current_bullets, 1):
                btxt = _norm(b)
                if not btxt:
                    continue
                if len(btxt) > 900:
                    btxt = btxt[:897] + "..."
                nodes.append(Node(code=f"{content_code}_S{bi}", title=btxt, level=3, parent=content_code))
        current_content_parts = []
        current_bullets = []

    def _flush_topic() -> None:
        nonlocal current_topic_code, current_topic_title_parts, content_idx
        _flush_content_row()
        current_topic_code = None
        current_topic_title_parts = []
        content_idx = 0

    def _split_inline_bullets(s: str) -> tuple[str, list[str]]:
        if "●" not in s and "•" not in s:
            return s, []
        s2 = s.replace("•", "●")
        parts = [p.strip() for p in s2.split("●")]
        left = parts[0]
        bullets = [p for p in parts[1:] if p]
        return left, bullets

    def _split_topic_title_and_first_content(left: str, *, allow_fallback_split: bool) -> tuple[str, Optional[str]]:
        """
        In extracted table rows, Topic and first Content label are sometimes collapsed into one string:
          "Mastering Perceived volume"
          "EQ Different types of EQ used in a recording"
          "Acoustics How the live room acoustics affect the recording"
          "Sampling Pitch mapping"
          "Stereo Pan"
        We try to split that into:
          topic_title="Mastering", first_content="Perceived volume"
        without inventing anything.
        """
        s = _norm(left)
        if not s:
            return "", None

        # Special-case: "digital Digital ..." where the first "digital" belongs to the topic title
        if "digital Digital " in s:
            topic, content = s.split("digital Digital ", 1)
            topic = _norm(topic + "digital")
            content = _norm("Digital " + content)
            return topic, (content or None)

        # Split on common content-label starters
        starters = (
            "How",
            "Uses",
            "Different",
            "Principles",
            "Understanding",
            "Core",
            "Perceived",
            "Technical",
            "Connectivity",
            "Digital",
            "The",
        )
        m = re.search(rf"\b({'|'.join(starters)})\b", s)
        if m and m.start() > 0:
            topic = _norm(s[: m.start()])
            content = _norm(s[m.start() :])
            if topic and content:
                return topic, content

        # Fallback: only when we have evidence this line collapsed Topic+Content (e.g. inline bullets present).
        # This avoids breaking true wrapped topic titles like "Capture of" + "sound".
        if not allow_fallback_split:
            return s, None

        # Fallback: 2-word case like "Stereo Pan" or 1-word topic like "Sampling Pitch mapping"
        words = s.split()
        if len(words) >= 2:
            topic = words[0]
            content = _norm(" ".join(words[1:]))
            # Don't split if the "topic" would be something too generic like "and"
            if topic.lower() not in {"and", "or"} and content:
                return topic, content

        return s, None

    def _append_bullet_text(txt: str) -> None:
        nonlocal current_bullets
        if not txt:
            return
        if not current_bullets:
            current_bullets.append(txt)
            return
        if txt[0].islower() or current_bullets[-1].endswith("-"):
            current_bullets[-1] = _norm(f"{current_bullets[-1]} {txt}")
        else:
            current_bullets.append(txt)

    in_table = False
    i = 0
    while i < len(block_lines):
        sn = _norm(block_lines[i])
        if not sn or _looks_like_header_footer(sn):
            i += 1
            continue

        if sn.startswith("Assessment information") or sn.startswith("Assessment Objectives"):
            _flush_topic()
            break

        if area_re.match(sn):
            in_table = False
            i += 1
            continue

        if _is_table_header_line(sn):
            in_table = True
            seen_any_table = True
            i += 1
            continue

        if in_table and sn.startswith("Students "):
            _flush_topic()
            in_table = False
            i += 1
            continue

        if not in_table:
            i += 1
            continue

        m = topic_re.match(sn)
        if m:
            major, minor, rest = m.group(1), m.group(2), m.group(3)
            _flush_topic()
            current_topic_code = f"{comp_code}_T{major}_{minor}"
            left, inline_bullets = _split_inline_bullets(_norm(rest))
            topic_title, first_content = _split_topic_title_and_first_content(
                left,
                allow_fallback_split=bool(inline_bullets),
            )
            current_topic_title_parts = [topic_title]

            # Topic title wrap: lowercase continuation or "continued"
            j = i + 1
            if first_content is None:
                while j < len(block_lines):
                    nxt = _norm(block_lines[j])
                    if not nxt or _looks_like_header_footer(nxt) or _is_table_header_line(nxt) or area_re.match(nxt) or topic_re.match(nxt):
                        break
                    if nxt.startswith(("●", "•")):
                        break
                    if nxt.lower() == "continued" or nxt[0].islower():
                        current_topic_title_parts.append(nxt)
                        j += 1
                        continue
                    break

            _finalize_topic_title()

            # If we recovered a first content label from the topic line, use it.
            if first_content:
                current_content_parts = [first_content]
            elif inline_bullets:
                # If there are inline bullets but no obvious content label, attach to a generic container.
                current_content_parts = ["(content)"]

            for b in inline_bullets:
                _append_bullet_text(_norm(b))

            i = j
            continue

        if sn.startswith(("●", "•")):
            _finalize_topic_title()
            _append_bullet_text(_norm(sn.lstrip("●•").strip()))
            i += 1
            continue

        _finalize_topic_title()
        if current_topic_code:
            left, inline_bullets = _split_inline_bullets(sn)

            if current_bullets and left and left[0].isupper():
                _flush_content_row()

            if not current_content_parts:
                current_content_parts = [_norm(left)]
            else:
                if left and (left[0].islower() or left.startswith(("and ", "or ", "including ", "to ", "with ", "for "))):
                    _append_wrapped(current_content_parts, left)
                else:
                    _flush_content_row()
                    current_content_parts = [_norm(left)]

            for b in inline_bullets:
                _append_bullet_text(_norm(b))

        i += 1

    _flush_topic()
    if not seen_any_table:
        return nodes
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

