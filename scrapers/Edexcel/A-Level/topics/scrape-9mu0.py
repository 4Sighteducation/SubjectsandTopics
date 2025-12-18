"""
Edexcel A-Level Music (9MU0) - Component 3: Appraising (ONLY)

User requirement:
- Only scrape Component 3 (starts ~page 74 in the specification PDF).
- Create a clean hierarchy suitable for the data viewer / card generation:
  - L0: Component 3: Appraising
  - L1: Areas of Study (each AoS) + "Musical elements" + "Musical contexts" + "Musical language"
  - L2/L3: Set works (under each AoS) + bullet points / prose statements under elements/contexts/language.

Notes:
- The PDF uses tables; pypdf text extraction interleaves "Content" and "Guidance" columns.
  We keep "Content" and skip obvious guidance lines using heuristics.
- We force UTF-8 output for Windows consoles.
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


def _force_utf8_stdio() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _slug(s: str) -> str:
    s = _norm_space(s).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "x"


def _looks_like_header_footer(line: str) -> bool:
    s = (line or "").strip()
    if not s:
        return True
    if "Pearson Edexcel Level 3 Advanced GCE in Music" in s:
        return True
    if "Specification" in s and "© Pearson Education Limited" in s:
        return True
    if s.startswith("Issue ") and "© Pearson Education Limited" in s:
        return True
    # page numbers
    if re.fullmatch(r"\d{1,3}", s):
        return True
    return False


def _is_guidance_line(line: str) -> bool:
    """
    Best-effort heuristics to drop the right-hand "Guidance" column when PDF text extraction
    interleaves columns. For Music, guidance is often prose like "Students should..." etc.
    """
    s = _norm_space(line)
    if not s:
        return True
    if s.startswith(("Students ", "Teachers ", "Centres ", "Candidates ")):
        return True
    if "will be expected" in s.lower() or "should be familiar" in s.lower():
        return True
    return False


def _append_wrapped(items: list[str], s: str) -> None:
    s = _norm_space(s)
    if not s:
        return
    if not items:
        items.append(s)
        return
    # wrapped continuation
    if s[0].islower() or s.startswith(("and ", "or ", "including ", "to ", "with ", "for ")):
        items[-1] = _norm_space(f"{items[-1]} {s}")
    else:
        items.append(s)


@dataclass(frozen=True)
class TopicRow:
    code: str
    title: str
    level: int
    parent: Optional[str]


SUBJECT = {
    "code": "9MU0",
    "name": "Music",
    "qualification": "A-Level",
    # standardise like other staging rows
    "exam_board": "EDEXCEL",
    "pdf_url": "https://qualifications.pearson.com/content/dam/pdf/A%20Level/Music/2016/Specification%20and%20sample%20assessments/Pearson_Edexcel_Level_3_Advanced_GCE_in_Music_9MU0_specification_issue7.pdf",
}


def download_pdf_text(pdf_url: str) -> str:
    print("[INFO] Downloading PDF...")
    resp = requests.get(pdf_url, timeout=60)
    resp.raise_for_status()
    reader = PdfReader(BytesIO(resp.content))
    print(f"[OK] Downloaded {len(reader.pages)} pages")
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    return text


def _find_component3_block(lines: list[str]) -> tuple[int, int]:
    """
    Find the best slice of lines corresponding to Component 3: Appraising.
    Returns (start_idx, end_idx).
    """
    candidates = []
    for i, s in enumerate(lines):
        if s.strip() == "Component 3: Appraising":
            window = "\n".join(lines[i : i + 120])
            # We want the actual content section, not contents mentions.
            if "Areas of study" in window or "Area of study" in window or "Set works" in window:
                candidates.append(i)
    if not candidates:
        # fallback: sometimes "Component 3: Appraising" is wrapped
        for i, s in enumerate(lines):
            if "Component 3:" in s and "Appraising" in s:
                window = "\n".join(lines[i : i + 120])
                if "Areas of study" in window or "Set works" in window:
                    candidates.append(i)
                    break
    if not candidates:
        raise RuntimeError("Could not locate 'Component 3: Appraising' in extracted PDF text.")

    start = candidates[0]
    # End at next component header or end of file
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].strip().startswith("Component 4:") or lines[j].strip().startswith("Component 2:") or lines[j].strip().startswith("Component 1:"):
            end = j
            break
    return start, end


KNOWN_AOS = [
    "Vocal Music",
    "Instrumental Music",
    "Music for Film",
    "Popular Music and Jazz",
    "Fusions",
    "New Directions",
]

# Some extracted tables lose the leftmost word due to PDF column clipping, yielding "Music and Jazz".
AOS_ALIASES = {
    "Music and Jazz": "Popular Music and Jazz",
}


def _parse_set_works(lines: list[str]) -> tuple[list[TopicRow], int]:
    """
    Parse the "Areas of study and set works" table-like block.
    Returns (topics, next_index_after_table).
    """
    topics: list[TopicRow] = []
    i = 0
    # find table header
    while i < len(lines):
        s = _norm_space(lines[i])
        if s.lower() in {"area of study", "areas of study"}:
            # usually followed by "Set works"
            # advance into the table body
            i += 1
            break
        if "Area of study" in s and "Set works" in s:
            i += 1
            break
        i += 1

    # if header not found, bail out
    if i >= len(lines):
        return topics, 0

    current_area: Optional[str] = None
    current_area_code: Optional[str] = None
    work_parts: list[str] = []
    work_idx = 0

    def flush_work():
        nonlocal work_parts, work_idx
        if current_area_code and work_parts:
            title = _norm_space(" ".join(work_parts))
            if title:
                work_idx += 1
                topics.append(
                    TopicRow(
                        code=f"{current_area_code}_SW{work_idx}",
                        title=title,
                        level=2,
                        parent=current_area_code,
                    )
                )
        work_parts = []

    # table ends when we hit "Musical contexts" or "Musical elements" or another component heading
    while i < len(lines):
        raw = lines[i]
        s = _norm_space(raw)
        if not s or _looks_like_header_footer(s):
            i += 1
            continue

        # end markers
        if s in {"Musical contexts", "Musical elements", "Musical language"} or s.startswith("Component "):
            flush_work()
            break
        if s.startswith("Full details of the exact versions") or s.startswith("Full details of the areas of study"):
            flush_work()
            break

        # Sometimes header row repeats on next page
        if s.lower() in {"area of study", "set works", "areas of study"}:
            i += 1
            continue

        # Handle split AoS labels caused by narrow table cells, e.g. "Popular Music and" + "Jazz"
        next_s = _norm_space(lines[i + 1]) if i + 1 < len(lines) else ""
        combined = _norm_space(f"{s} {next_s}") if next_s else ""
        if combined in KNOWN_AOS or combined in AOS_ALIASES:
            flush_work()
            current_area = AOS_ALIASES.get(combined, combined)
            current_area_code = f"AOS_{_slug(current_area)}"
            work_idx = 0
            topics.append(TopicRow(code=current_area_code, title=current_area, level=1, parent="C3"))
            i += 2
            continue

        # detect an AoS row.
        # In this PDF extraction the table often appears like:
        #   "Vocal Music ● J. S. Bach, Cantata, Ein feste Burg"
        # rather than AoS on its own line.
        matched_aos = None
        remainder = ""
        for aos in KNOWN_AOS + list(AOS_ALIASES.keys()) + ["Fusion"]:
            if s == aos:
                if aos == "Fusion":
                    matched_aos = "Fusions"
                else:
                    matched_aos = AOS_ALIASES.get(aos, aos)
                remainder = ""
                break
            if s.startswith(aos + " "):
                if aos == "Fusion":
                    matched_aos = "Fusions"
                else:
                    matched_aos = AOS_ALIASES.get(aos, aos)
                remainder = s[len(aos) :].strip()
                break
            if s.startswith(aos + "●"):
                if aos == "Fusion":
                    matched_aos = "Fusions"
                else:
                    matched_aos = AOS_ALIASES.get(aos, aos)
                remainder = s[len(aos) :].strip()
                break

        if matched_aos:
            flush_work()
            current_area = matched_aos
            current_area_code = f"AOS_{_slug(current_area)}"
            work_idx = 0
            topics.append(TopicRow(code=current_area_code, title=current_area, level=1, parent="C3"))

            # If the first set work is on the same line, split by bullets and add immediately.
            if remainder:
                # remainder often begins with a bullet; treat as the start of the first work,
                # and allow the next lines to continue it (so we don't split mid-title).
                remainder = _norm_space(remainder.lstrip("•●").strip())
                # If multiple bullets appear on the same line, split and flush each.
                parts = [_norm_space(p.lstrip("•●").strip()) for p in remainder.split("●") if _norm_space(p)]
                if parts:
                    # start first work
                    work_parts = [parts[0]]
                    # any additional parts are additional works
                    for extra in parts[1:]:
                        flush_work()
                        work_parts = [extra]
            i += 1
            continue

        # ignore the "Area of study / Set works" table title row if it appears
        if current_area is None:
            i += 1
            continue

        # Parse set work rows.
        # Many rows start with a bullet in the extracted text.
        if s.startswith("●") or s.startswith("•"):
            flush_work()
            work_parts = [_norm_space(s.lstrip("●•").strip())]
            i += 1
            continue

        # If we drift out of the table into general skills prose, stop.
        if re.match(r"^(analyse|formulate|comment|use|show|demonstrate)\b", s, flags=re.IGNORECASE):
            flush_work()
            break

        # Otherwise treat as continuation of current work, or a new work if it looks like one.
        is_new_work = (
            bool(re.match(r"^[A-Z]\.\s*[A-Z]\.", s))
            or ("," in s and re.match(r"^[A-Z][A-Za-z\.\-’' ]{1,40},", s) is not None)
            or bool(re.match(r"^[A-Z][A-Za-z\.\-’' ]{2,40}\s+[A-Z][A-Za-z\.\-’' ]{2,40},", s))
        )

        if is_new_work and work_parts:
            flush_work()
            work_parts = [s]
        else:
            if not work_parts:
                work_parts = [s]
            else:
                _append_wrapped(work_parts, s)
        i += 1

    flush_work()
    return topics, i


def _parse_bulleted_section(
    lines: list[str],
    start_at: int,
    section_title: str,
    stop_titles: set[str],
) -> tuple[list[TopicRow], int]:
    """
    Parse a section like "Musical elements" / "Musical contexts" / "Musical language".
    """
    topics: list[TopicRow] = []
    i = start_at
    section_code = f"C3_{_slug(section_title)}"
    topics.append(TopicRow(code=section_code, title=section_title, level=1, parent="C3"))

    current_sub_code: Optional[str] = None
    current_sub_title: Optional[str] = None
    current_items: list[str] = []
    item_idx = 0

    def flush_items():
        nonlocal item_idx, current_items
        if current_sub_code:
            for s in current_items:
                item_idx += 1
                topics.append(TopicRow(code=f"{current_sub_code}_{item_idx}", title=s, level=3, parent=current_sub_code))
        current_items = []
        item_idx = 0

    def flush_sub():
        nonlocal current_sub_code, current_sub_title
        if current_sub_code and current_sub_title:
            flush_items()
        current_sub_code = None
        current_sub_title = None

    # consume possible "This includes:" line etc.
    while i < len(lines):
        s = _norm_space(lines[i])
        if not s or _looks_like_header_footer(s):
            i += 1
            continue
        if s in stop_titles or s.startswith("Component "):
            flush_sub()
            break

        if s == section_title:
            i += 1
            continue

        if _is_guidance_line(s):
            i += 1
            continue

        # Bullet line
        bullet = None
        if s.startswith("•"):
            bullet = _norm_space(s.lstrip("•").strip())
        elif s.startswith("- "):
            bullet = _norm_space(s[2:])

        if bullet:
            if not current_sub_code:
                # Some sections are just a bullet list; create a simple container
                current_sub_title = section_title
                current_sub_code = f"{section_code}_items"
                topics.append(TopicRow(code=current_sub_code, title=current_sub_title, level=2, parent=section_code))
            _append_wrapped(current_items, bullet)
            i += 1
            continue

        # Subheading detection (e.g. "Texture", "Musical contexts", etc.)
        looks_like_subheading = (
            len(s) <= 90
            and len(s.split()) <= 12
            and not s.endswith(".")
            and s[0].isupper()
            and not s.startswith(("As ", "The ", "This ", "These "))
            and not re.search(r"\b(Students|Candidates|Centres)\b", s)
            and not re.match(r"^\d", s)
        )

        if looks_like_subheading:
            flush_sub()
            current_sub_title = s
            current_sub_code = f"{section_code}_{_slug(s)}"
            topics.append(TopicRow(code=current_sub_code, title=current_sub_title, level=2, parent=section_code))
            i += 1
            continue

        # Prose line: keep as a content statement under current subheading (or under section)
        if not current_sub_code:
            current_sub_title = section_title
            current_sub_code = f"{section_code}_prose"
            topics.append(TopicRow(code=current_sub_code, title=current_sub_title, level=2, parent=section_code))

        _append_wrapped(current_items, s)
        i += 1

    flush_sub()
    return topics, i


def parse_music_component3(text: str) -> list[TopicRow]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Save a debug slice around Component 3 for inspection
    start, end = _find_component3_block(lines)
    comp_lines = lines[start:end]

    topics: list[TopicRow] = []
    topics.append(TopicRow(code="C3", title="Component 3: Appraising", level=0, parent=None))

    # Parse set works table
    set_work_topics, next_i = _parse_set_works(comp_lines)
    topics.extend(set_work_topics)

    # Parse musical elements/contexts/language
    stop_titles = {"Musical elements", "Musical contexts", "Musical language", "Component 4: Composing", "Component 1: Performing", "Component 2:"}

    i = max(next_i, 0)
    while i < len(comp_lines):
        s = _norm_space(comp_lines[i])
        if not s or _looks_like_header_footer(s):
            i += 1
            continue
        if s == "Musical elements":
            t, i2 = _parse_bulleted_section(comp_lines, i + 1, "Musical elements", {"Musical contexts", "Musical language"},)
            topics.extend(t)
            i = i2
            continue
        if s == "Musical contexts":
            t, i2 = _parse_bulleted_section(comp_lines, i + 1, "Musical contexts", {"Musical language"},)
            topics.extend(t)
            i = i2
            continue
        if s == "Musical language":
            t, i2 = _parse_bulleted_section(comp_lines, i + 1, "Musical language", set(),)
            topics.extend(t)
            i = i2
            continue
        i += 1

    # Deduplicate by code
    uniq: list[TopicRow] = []
    seen = set()
    for t in topics:
        if t.code in seen:
            continue
        seen.add(t.code)
        uniq.append(t)
    return uniq


def upload_to_staging(rows: list[TopicRow]) -> None:
    env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
    load_dotenv(env_path)
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    print(f"\n[INFO] Uploading {len(rows)} topics to staging...")

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

    supabase.table("staging_aqa_topics").delete().eq("subject_id", subject_id).execute()
    print("[OK] Cleared old topics")

    to_insert = [
        {
            "subject_id": subject_id,
            "topic_code": r.code,
            "topic_name": r.title,
            "topic_level": r.level,
            "exam_board": SUBJECT["exam_board"],
        }
        for r in rows
    ]
    inserted = supabase.table("staging_aqa_topics").insert(to_insert).execute()
    print(f"[OK] Uploaded {len(inserted.data)} topics")

    code_to_id = {t["topic_code"]: t["id"] for t in inserted.data}
    linked = 0
    for r in rows:
        if not r.parent:
            continue
        parent_id = code_to_id.get(r.parent)
        child_id = code_to_id.get(r.code)
        if parent_id and child_id:
            supabase.table("staging_aqa_topics").update({"parent_topic_id": parent_id}).eq("id", child_id).execute()
            linked += 1
    print(f"[OK] Linked {linked} relationships")


def main() -> None:
    _force_utf8_stdio()

    print("=" * 80)
    print("EDEXCEL A-LEVEL MUSIC (9MU0) - COMPONENT 3: APPRAISING")
    print("=" * 80)
    print("Target: Component 3 only (Areas of Study + Set Works + Musical elements/contexts/language)\n")

    text = download_pdf_text(SUBJECT["pdf_url"])

    # Save full debug text (local repo file; do not commit)
    debug_path = Path("scrapers/Edexcel/A-Level/topics/debug-9mu0-spec.txt")
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}")

    rows = parse_music_component3(text)
    # quick counts
    levels = {}
    for r in rows:
        levels[r.level] = levels.get(r.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(rows)
    print("\n[OK] 9MU0 Component 3 scrape complete.")


if __name__ == "__main__":
    main()


