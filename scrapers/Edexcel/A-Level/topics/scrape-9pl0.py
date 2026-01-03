"""
Edexcel A-Level Politics (9PL0) - Topics Scraper

Parses the specification "content tables" into a clean hierarchy.

Hierarchy:
  - L0: Component 1..3
  - L1: Section (e.g. UK Politics / Core Political Ideas / UK Government / Non-core Political Ideas / USA / Global)
  - L2: Content area (e.g. "1 Democracy and participation")
  - L3+: Numbered subheadings (e.g. 1.1, 2.2, 2.2.1 ...)
  - L{n}+1: Bullets under each numbered heading (• ...)
  - L{n}+2: Sub-bullets under a bullet (o ...)

Notes:
- The PDF is table-based; pypdf extraction interleaves columns, but keeps enough structure
  to parse numeric headings and bullets reliably.
- We intentionally IGNORE "Key terminology" (it is not uploaded as topics).
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
    "name": "Politics",
    "code": "9PL0",
    "qualification": "A-Level",
    # Standardise like other staging rows
    "exam_board": "EDEXCEL",
    "pdf_url": "https://qualifications.pearson.com/content/dam/pdf/A%20Level/Politics/2017/Specification%20and%20sample%20assessments/A-level-Politics-Specification.pdf",
}


def _force_utf8_stdio() -> None:
    if (sys.stdout.encoding or "").lower() != "utf-8":
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
    if "Pearson Edexcel Level 3 Advanced GCE in Politics" in s:
        return True
    if "Specification" in s and "© Pearson Education Limited" in s:
        return True
    if s.startswith("Issue ") and "© Pearson Education Limited" in s:
        return True
    # page numbers
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
    1: "Component 1: UK Politics and Core Political Ideas",
    2: "Component 2: UK Government and Non-core Political Ideas",
    3: "Component 3: Comparative Politics",
}


def _find_component_blocks(lines: list[str]) -> dict[int, tuple[int, int]]:
    """
    Find the best block for each component by selecting the occurrence that is NOT the contents page.
    """
    blocks: dict[int, tuple[int, int]] = {}
    candidates: dict[int, list[int]] = {k: [] for k in COMPONENTS}

    def _line_matches_component(i: int, header: str) -> bool:
        s1 = _norm(lines[i])
        s2 = _norm(lines[i + 1]) if i + 1 < len(lines) else ""
        combo = _norm(f"{s1} {s2}") if s2 else s1
        # Intentionally do NOT use startswith(): TOC lines often end with a page number (e.g. "... 7")
        # and would incorrectly match the real header.
        return s1 == header or combo == header

    for i, raw in enumerate(lines):
        for n, header in COMPONENTS.items():
            if _line_matches_component(i, header):
                # Reject TOC-style lines like "... 7" by checking for "content" tables nearby.
                window = "\n".join(lines[i : i + 900])
                # Component 1/2 have explicit "* content" headings; component 3 starts with USA/Global sections.
                if n == 1 and "UK Politics content" in window and "Core Political Ideas content" in window:
                    candidates[n].append(i)
                elif n == 2 and "UK Government content" in window and "Non-core Political Ideas content" in window:
                    candidates[n].append(i)
                elif n == 3 and ("Government and Politics of the USA" in window or "Global Politics" in window):
                    candidates[n].append(i)

    for n in COMPONENTS:
        if not candidates[n]:
            continue
        start = candidates[n][0]
        end = len(lines)
        for j in range(start + 1, len(lines)):
            sj = _norm(lines[j])
            # next component start
            m = re.match(r"^Component\s+([1-3]):", sj)
            if m:
                next_n = int(m.group(1))
                if next_n != n:
                    end = j
                    break
            if sj.startswith("Assessment Objectives") or sj.startswith("3 Administration and general"):
                end = j
                break
        blocks[n] = (start, end)

    return blocks


HEADING_RE = re.compile(r"^(\d+(?:\.\d+){1,3})\s+(.+)$")  # 1.1, 2.2.1, ...
AREA_RE = re.compile(r"^(\d{1,2})\s+([A-Za-z].+)$")  # 1 Democracy and...

def _parse_ideas_options(
    *,
    section_code: str,
    section_title: str,
    parent_code: str,
    block_lines: list[str],
    option_headers: list[str],
    option_header_style: str,
) -> list[Node]:
    """
    Parse Core/Non-core Political Ideas blocks where each option (e.g. Liberalism, Anarchism option)
    contains 3 content areas (numbered 1/2/3) and then bullets directly (no 1.1-style headings).

    Output structure:
      L1: section
      L2: option (e.g. Liberalism)
      L3: content area (e.g. "1 Liberalism: core ideas and principles")
      L4: bullets (• ...)
      L5: sub-bullets (o ...)
    """
    nodes: list[Node] = []
    nodes.append(Node(code=section_code, title=section_title, level=1, parent=parent_code))

    lines = [_norm(ln) for ln in block_lines]

    def is_option_header(line: str, header: str) -> bool:
        if option_header_style == "exact":
            return line == header
        # "suffix": headers like "Anarchism option"
        return line == f"{header} option" or line == header

    def is_key_terminology_line(s: str) -> bool:
        return s == "Key terminology" or s.lower().startswith("key terminology")

    content_area_re = re.compile(r"^([1-3])\s+(.+)$")

    current_option_code: Optional[str] = None
    current_area_code: Optional[str] = None
    bullet_idx = 0
    current_bullet_code: Optional[str] = None
    current_bullet_parts: list[str] = []
    sub_idx = 0
    current_sub_parts: list[str] = []
    in_terms = False

    def flush_sub() -> None:
        nonlocal current_sub_parts
        if current_bullet_code and current_sub_parts:
            t = _norm(" ".join(current_sub_parts))
            if t:
                nodes.append(Node(code=f"{current_bullet_code}_o{sub_idx}", title=t, level=5, parent=current_bullet_code))
        current_sub_parts = []

    def flush_bullet() -> None:
        nonlocal current_bullet_parts, current_bullet_code, sub_idx
        flush_sub()
        if current_area_code and current_bullet_code and current_bullet_parts:
            t = _norm(" ".join(current_bullet_parts))
            if t:
                nodes.append(Node(code=current_bullet_code, title=t, level=4, parent=current_area_code))
        current_bullet_parts = []
        current_bullet_code = None
        sub_idx = 0

    def start_option(opt: str) -> None:
        nonlocal current_option_code, current_area_code, bullet_idx, in_terms
        flush_bullet()
        current_option_code = f"{section_code}_opt_{_slug(opt)}"
        nodes.append(Node(code=current_option_code, title=opt, level=2, parent=section_code))
        current_area_code = None
        bullet_idx = 0
        in_terms = False

    def start_area(num: str, title: str) -> None:
        nonlocal current_area_code, bullet_idx, in_terms
        flush_bullet()
        if not current_option_code:
            return
        current_area_code = f"{current_option_code}_A{num}"
        nodes.append(Node(code=current_area_code, title=f"{num} {title}".strip(), level=3, parent=current_option_code))
        bullet_idx = 0
        in_terms = False

    def start_bullet(text: str) -> None:
        nonlocal bullet_idx, current_bullet_code, current_bullet_parts
        flush_bullet()
        if not current_area_code:
            return
        bullet_idx += 1
        current_bullet_code = f"{current_area_code}_B{bullet_idx}"
        current_bullet_parts = [text]

    def start_sub(text: str) -> None:
        nonlocal sub_idx, current_sub_parts
        if not current_bullet_code:
            start_bullet("(bullet list)")
        flush_sub()
        sub_idx += 1
        current_sub_parts = [text]

    i = 0
    while i < len(lines):
        s = lines[i]
        if not s or _looks_like_header_footer(s):
            i += 1
            continue

        # stop conditions
        if s.startswith("Assessment overview") or s.startswith("Assessment Objectives") or s.startswith("3 Administration and general"):
            break

        matched_opt = None
        for opt in option_headers:
            if is_option_header(s, opt):
                matched_opt = opt
                break
        if matched_opt:
            start_option(matched_opt)
            i += 1
            continue

        if not current_option_code:
            i += 1
            continue

        if s.startswith("Subject content Students should gain knowledge and understanding"):
            i += 1
            continue

        m = content_area_re.match(s)
        if m:
            start_area(m.group(1), m.group(2))
            i += 1
            continue

        if is_key_terminology_line(s):
            in_terms = True
            i += 1
            continue
        if in_terms:
            if s.startswith(("•", "o ")) or content_area_re.match(s):
                in_terms = False
                continue
            i += 1
            continue

        if s.startswith("•"):
            start_bullet(_norm(s.lstrip("•").strip()))
            i += 1
            continue
        if s.startswith("o "):
            start_sub(_norm(s[2:].strip()))
            i += 1
            continue

        if current_sub_parts:
            _append_wrapped(current_sub_parts, s)
            i += 1
            continue
        if current_bullet_parts:
            _append_wrapped(current_bullet_parts, s)
            i += 1
            continue

        i += 1

    flush_bullet()
    return nodes


def _parse_section(section_code: str, section_title: str, block_lines: list[str], parent_code: str) -> list[Node]:
    nodes: list[Node] = []
    nodes.append(Node(code=section_code, title=section_title, level=1, parent=parent_code))

    current_area_code: Optional[str] = None
    current_area_num: Optional[str] = None
    current_heading_code_by_numeric: dict[str, str] = {}
    current_heading_numeric: Optional[str] = None
    current_heading_level: Optional[int] = None

    # bullet state under a numbered heading
    current_bullet_parent: Optional[str] = None
    current_bullet_level: Optional[int] = None
    bullet_idx = 0
    current_bullet_parts: list[str] = []
    sub_idx = 0
    current_sub_parts: list[str] = []

    # key terminology state (we intentionally IGNORE key terminology rows)
    in_terms = False

    def flush_sub() -> None:
        nonlocal current_sub_parts
        if current_bullet_parent and current_sub_parts:
            t = _norm(" ".join(current_sub_parts))
            if t:
                nodes.append(
                    Node(
                        code=f"{current_bullet_parent}_o{sub_idx}",
                        title=t,
                        level=(current_bullet_level or 0) + 1,
                        parent=current_bullet_parent,
                    )
                )
        current_sub_parts = []

    def flush_bullet() -> None:
        nonlocal current_bullet_parent, current_bullet_parts, sub_idx, current_bullet_level
        flush_sub()
        if current_bullet_parent and current_bullet_parts:
            t = _norm(" ".join(current_bullet_parts))
            if t:
                nodes.append(Node(code=current_bullet_parent, title=t, level=current_bullet_level or 0, parent=current_heading_code_by_numeric.get(current_heading_numeric or "", current_area_code)))
        current_bullet_parent = None
        current_bullet_parts = []
        sub_idx = 0
        current_bullet_level = None

    def start_bullet(text: str) -> None:
        nonlocal bullet_idx, current_bullet_parent, current_bullet_parts, current_bullet_level, current_bullet_parent
        flush_bullet()
        if not current_heading_code_by_numeric.get(current_heading_numeric or ""):
            return
        bullet_idx += 1
        current_bullet_parent = f"{current_heading_code_by_numeric[current_heading_numeric]}_B{bullet_idx}"
        current_bullet_level = (current_heading_level or 0) + 1
        current_bullet_parts = [text]

    def start_sub_bullet(text: str) -> None:
        nonlocal sub_idx, current_sub_parts
        if not current_bullet_parent:
            # If we see a sub-bullet without a bullet, create a placeholder bullet.
            start_bullet("(bullet list)")
        flush_sub()
        sub_idx += 1
        current_sub_parts = [text]

    def flush_terms() -> None:
        nonlocal in_terms
        in_terms = False

    i = 0
    while i < len(block_lines):
        raw = block_lines[i]
        sn = _norm(raw)
        if not sn or _looks_like_header_footer(sn):
            i += 1
            continue

        # Stop at the next big section / admin.
        if sn.startswith("Assessment overview") or sn.startswith("Assessment information") or sn.startswith("Assessment Objectives"):
            flush_bullet()
            break

        # Skip table preface
        if sn.startswith("Subject content Students should gain knowledge and understanding of"):
            i += 1
            continue

        # Detect content area start (e.g. "1 Democracy and participation").
        area_m = AREA_RE.match(sn)
        if area_m and "." not in area_m.group(1):
            # Validate by looking ahead for "Key terminology" soon (table structure).
            window = "\n".join(block_lines[i : i + 12])
            if "Key terminology" in window:
                flush_bullet()
                flush_terms()
                in_terms = False

                num = area_m.group(1)
                title_parts = [area_m.group(2)]
                j = i + 1
                while j < len(block_lines):
                    nxt = _norm(block_lines[j])
                    if not nxt or _looks_like_header_footer(nxt):
                        j += 1
                        continue
                    if nxt.startswith("Key terminology"):
                        break
                    if HEADING_RE.match(nxt):
                        break
                    if AREA_RE.match(nxt) and "Key terminology" in "\n".join(block_lines[j : j + 12]):
                        break
                    # wrapped continuation of area title
                    if nxt[0].islower():
                        title_parts.append(nxt)
                        j += 1
                        continue
                    break

                area_title = _norm(" ".join(title_parts))
                current_area_num = num
                current_area_code = f"{section_code}_A{num}"
                nodes.append(Node(code=current_area_code, title=f"{num} {area_title}".strip(), level=2, parent=section_code))

                # reset numeric heading map per area
                current_heading_code_by_numeric = {}
                current_heading_numeric = None
                current_heading_level = None
                bullet_idx = 0

                i = j
                continue

        if not current_area_code:
            i += 1
            continue

        # Key terminology
        if sn.startswith("Key terminology"):
            flush_bullet()
            # Ignore key terminology rows entirely (do not create nodes)
            in_terms = True
            i += 1
            continue

        # Exit terms list when we hit a numbered heading
        if in_terms and HEADING_RE.match(sn):
            flush_terms()
            # fall through to heading parsing

        if in_terms:
            i += 1
            continue

        # Numbered heading (1.1, 2.2.1 ...)
        hm = HEADING_RE.match(sn)
        if hm:
            flush_bullet()
            numeric = hm.group(1)
            title = _norm(hm.group(2))
            parts = numeric.split(".")
            level = len(parts) + 1  # 1.1 => 3, 2.2.1 => 4, etc.

            parent = current_area_code
            if len(parts) > 2:
                parent_numeric = ".".join(parts[:-1])
                parent = current_heading_code_by_numeric.get(parent_numeric, current_area_code)

            code = f"{section_code}_{numeric.replace('.', '_')}"
            nodes.append(Node(code=code, title=f"{numeric} {title}".strip(), level=level, parent=parent))
            current_heading_code_by_numeric[numeric] = code
            current_heading_numeric = numeric
            current_heading_level = level
            bullet_idx = 0
            i += 1
            continue

        # Bullets under current heading
        if sn.startswith("•"):
            if current_heading_numeric:
                text = _norm(sn.lstrip("•").strip())
                start_bullet(text)
            i += 1
            continue

        if sn.startswith("o "):
            text = _norm(sn[2:].strip())
            start_sub_bullet(text)
            i += 1
            continue

        # Wrapped continuation of a bullet/sub-bullet
        if current_sub_parts:
            _append_wrapped(current_sub_parts, sn)
            i += 1
            continue
        if current_bullet_parts:
            _append_wrapped(current_bullet_parts, sn)
            i += 1
            continue

        i += 1

    flush_bullet()
    return nodes


def _parse_component(component_num: int, block_lines: list[str]) -> list[Node]:
    nodes: list[Node] = []
    comp_code = f"C{component_num}"
    nodes.append(Node(code=comp_code, title=COMPONENTS[component_num], level=0, parent=None))

    text = "\n".join(block_lines)

    def slice_between(start_marker: str, end_markers: list[str]) -> list[str]:
        if start_marker not in text:
            return []
        start_idx = next(i for i, ln in enumerate(block_lines) if _norm(ln) == start_marker)
        end_idx = len(block_lines)
        for j in range(start_idx + 1, len(block_lines)):
            sj = _norm(block_lines[j])
            if sj in end_markers:
                end_idx = j
                break
        return block_lines[start_idx:end_idx]

    if component_num == 1:
        uk = slice_between("UK Politics content", ["Core Political Ideas content", COMPONENTS[2], COMPONENTS[3], "Assessment Objectives"])
        cpi = slice_between("Core Political Ideas content", [COMPONENTS[2], COMPONENTS[3], "Assessment Objectives"])
        if uk:
            nodes.extend(_parse_section(f"{comp_code}_uk_politics", "UK Politics", uk, comp_code))
        if cpi:
            nodes.extend(
                _parse_ideas_options(
                    section_code=f"{comp_code}_core_political_ideas",
                    section_title="Core Political Ideas",
                    parent_code=comp_code,
                    block_lines=cpi,
                    option_headers=["Liberalism", "Conservatism", "Socialism"],
                    option_header_style="exact",
                )
            )

    elif component_num == 2:
        ukg = slice_between("UK Government content", ["Non-core Political Ideas content", COMPONENTS[3], "Assessment Objectives"])
        ncpi = slice_between("Non-core Political Ideas content", [COMPONENTS[3], "Assessment Objectives"])
        if ukg:
            nodes.extend(_parse_section(f"{comp_code}_uk_government", "UK Government", ukg, comp_code))
        if ncpi:
            nodes.extend(
                _parse_ideas_options(
                    section_code=f"{comp_code}_non_core_political_ideas",
                    section_title="Non-core Political Ideas",
                    parent_code=comp_code,
                    block_lines=ncpi,
                    option_headers=["Anarchism", "Ecologism", "Feminism", "Multiculturalism", "Nationalism"],
                    option_header_style="suffix",
                )
            )

    else:
        # Component 3: Comparative Politics (USA or Global). We parse both sections into staging.
        usa_start = None
        global_start = None
        for i, ln in enumerate(block_lines):
            s = _norm(ln)
            if s == "Government and Politics of the USA" and usa_start is None:
                usa_start = i
            if s == "Global Politics" and global_start is None:
                global_start = i
        if usa_start is not None:
            end = global_start if global_start is not None else len(block_lines)
            nodes.extend(_parse_section(f"{comp_code}_usa", "Government and Politics of the USA", block_lines[usa_start:end], comp_code))
        if global_start is not None:
            nodes.extend(_parse_section(f"{comp_code}_global", "Global Politics", block_lines[global_start:], comp_code))

    # de-dupe by code
    uniq: list[Node] = []
    seen = set()
    for n in nodes:
        if n.code in seen:
            continue
        seen.add(n.code)
        uniq.append(n)
    return uniq


def parse_9pl0(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]
    blocks = _find_component_blocks(lines)
    nodes: list[Node] = []
    for n in sorted(blocks.keys()):
        start, end = blocks[n]
        nodes.extend(_parse_component(n, lines[start:end]))
    if not nodes:
        raise RuntimeError("No component blocks were parsed for 9PL0 (check PDF extraction).")
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

    # Clear old topics by level (deepest first) to avoid self-referential FK issues.
    max_level = max((n.level for n in nodes), default=0)
    deleted_total = 0
    for lvl in range(max_level, -1, -1):
        res = (
            supabase.table("staging_aqa_topics")
            .delete()
            .eq("subject_id", subject_id)
            .eq("topic_level", lvl)
            .execute()
        )
        deleted_total += len(res.data or [])
    print(f"[OK] Cleared old topics ({deleted_total} rows)")

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
    print("EDEXCEL A-LEVEL POLITICS (9PL0) - TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/Edexcel/A-Level/topics/debug-9pl0-spec.txt")
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}")

    nodes = parse_9pl0(text)
    levels = {}
    for n in nodes:
        levels[n.level] = levels.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(nodes)
    print("\n[OK] 9PL0 topics scrape complete.")


if __name__ == "__main__":
    main()


