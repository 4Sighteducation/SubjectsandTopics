"""
WJEC GCSE Digital Media and Film (3670) - Topics Scraper (Unit 1 only)

Spec (Teaching from 2026 / award from 2028):
  https://www.wjec.co.uk/media/yg3m0sy1/wjec-gcse-digital-media-and-film-specification.pdf

User target structure:
  - L0: Unit 1: Exploring key concepts and issues (exam)
  - L1: 1.1 Welsh and global films / 1.2 Video gaming / 1.3 Online news & social media
  - L2: numbered subtopics (e.g. 1.1.1 How film creates meaning for audiences)
  - L3+: parse the “Further information” column into headings + bullet hierarchies

Set films (for 1.1):
  - Under 1.1, add L2 nodes for each selectable film pair. Under each pair, duplicate
    the 1.1.1–1.1.5 subtopic subtree one level deeper. This makes flashcard generation
    film-pair-aware without requiring cross-links in the DB.
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
    "name": "Digital Media and Film",
    "code": "WJEC-3670",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/yg3m0sy1/wjec-gcse-digital-media-and-film-specification.pdf",
}


UNIT1_TITLE = "Unit 1: Exploring key concepts and issues"


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
    if re.fullmatch(r"\d{1,3}", s):
        return True
    if s.startswith("GCSE DIGITAL MEDIA AND FILM"):
        return True
    return False


def download_pdf_text(url: str) -> str:
    print("[INFO] Downloading PDF...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    reader = PdfReader(BytesIO(resp.content))
    print(f"[OK] Downloaded {len(reader.pages)} pages")
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def _add_node(nodes: list[Node], code: str, title: str, level: int, parent: Optional[str]) -> None:
    nodes.append(Node(code=code, title=_norm(title), level=level, parent=parent))


def _clone_subtree(nodes: list[Node], *, root_code: str, new_parent_code: str, code_prefix: str, level_offset: int) -> None:
    """
    Clone a subtree rooted at root_code into new_parent_code.
    - All cloned codes are prefixed with code_prefix.
    - Levels are offset by level_offset.
    """
    by_code = {n.code: n for n in nodes}
    children: dict[str, list[str]] = {}
    for n in nodes:
        if n.parent:
            children.setdefault(n.parent, []).append(n.code)

    def dfs(old_code: str, new_parent: str) -> None:
        old = by_code[old_code]
        new_code = f"{code_prefix}{old_code}"
        _add_node(nodes, new_code, old.title, old.level + level_offset, new_parent)
        for ch in children.get(old_code, []):
            dfs(ch, new_code)

    dfs(root_code, new_parent_code)


def parse_digital_media_and_film_unit1(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Find real Unit 1 section (avoid contents line "Unit 1 .... 10")
    unit1_re = re.compile(r"^Unit\s+1\b(?!\s+\.{2,}|\s+\d)", flags=re.IGNORECASE)
    start = None
    for i, raw in enumerate(lines):
        s = _norm(raw)
        if not unit1_re.match(s):
            continue
        window = "\n".join(_norm(x) for x in lines[i : i + 120])
        if "Exploring key concepts and issues" in window and "Areas of content" in window and "1.1 Welsh and global films" in window:
            start = i
            break
    if start is None:
        raise RuntimeError("Could not locate Unit 1 section.")

    # End Unit 1 at the next major section (Assessment objectives) or Unit 2
    end = len(lines)
    stop_re = re.compile(r"^3\.1\s+Assessment Objectives", flags=re.IGNORECASE)
    unit2_re = re.compile(r"^Unit\s+2\b(?!\s+\.{2,}|\s+\d)", flags=re.IGNORECASE)
    for j in range(start + 1, len(lines)):
        sj = _norm(lines[j])
        if stop_re.match(sj) or unit2_re.match(sj):
            end = j
            break

    block = lines[start:end]

    # Headings
    l1_re = re.compile(r"^(1\.[1-3])\s+(.+)$")
    l2_re = re.compile(r"^(1\.[1-3]\.\d)\s+(.+)$")  # 1.1.1 etc

    # Further info section parsing
    learner_head_re = re.compile(r"^Learners should\s+(understand|know|be able to)\b", flags=re.IGNORECASE)
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7�]\s*(.+)$")

    # Film pair list section markers (within 1.1)
    films_set_re = re.compile(r"^Films set for study\b", flags=re.IGNORECASE)
    content_header_re = re.compile(r"^Content\s+Further information\b", flags=re.IGNORECASE)

    nodes: list[Node] = []

    unit_code = "U1"
    _add_node(nodes, unit_code, UNIT1_TITLE, 0, None)

    # First pass: create L1 + L2 skeleton from the “Areas of content” lists
    current_l1_code: Optional[str] = None
    l1_codes: dict[str, str] = {}
    l2_codes: dict[str, str] = {}  # key like "1.1.1" -> code

    for raw in block:
        s = _norm(raw)
        if not s or _looks_like_header_footer(s):
            continue
        m1 = l1_re.match(s)
        if m1:
            num, title = m1.group(1), m1.group(2)
            current_l1_code = f"{unit_code}_{num.replace('.', '_')}"
            l1_codes[num] = current_l1_code
            _add_node(nodes, current_l1_code, f"{num} {title}", 1, unit_code)
            continue
        m2 = l2_re.match(s)
        if m2 and current_l1_code:
            num, title = m2.group(1), m2.group(2)
            # Avoid duplicates from later table blocks by only adding the first time
            if num in l2_codes:
                continue
            code = f"{current_l1_code}_{num.split('.')[-1]}"
            l2_codes[num] = code
            _add_node(nodes, code, f"{num} {title}", 2, current_l1_code)

    # Parse film pairs (1.1) from the list, so we can create film-pair nodes and later clone.
    # The PDF often wraps a single pair across multiple lines (e.g. directors split onto next line),
    # so we build entries by accumulating until a blank line separator.
    film_pairs: list[str] = []
    in_films = False
    i = 0
    while i < len(block):
        s = _norm(block[i])
        if not s or _looks_like_header_footer(s):
            i += 1
            continue
        if films_set_re.match(s):
            in_films = True
            i += 1
            continue
        if in_films and content_header_re.match(s):
            in_films = False
            i += 1
            continue
        if not in_films:
            i += 1
            continue

        # Skip headers and notes inside the films section
        sl = s.lower()
        if sl.startswith(("for this section", "welsh films", "global films", "*it is the centre", "set films are reviewed", "centres are notified")):
            i += 1
            continue
        if s.startswith("*"):
            i += 1
            continue

        # Pair entries contain " and " between the Welsh and Global film
        if " and " in s:
            parts = [s]
            j = i + 1
            while j < len(block):
                nxt_raw = block[j]
                nxt = _norm(nxt_raw)
                if not nxt or _looks_like_header_footer(nxt):
                    j += 1
                    continue
                # stop on section notes or the next heading
                if nxt.startswith("*") or content_header_re.match(nxt) or films_set_re.match(nxt):
                    break
                # a new pair entry begins
                if " and " in nxt and parts:
                    break
                parts.append(nxt)
                # the pairs are separated by blank lines; if next raw line is blank, we'll stop naturally by skipping empties
                j += 1
                # heuristic: stop once we have an age rating token near the end (PG/12/12A/15*)
                if re.search(r"\b(PG|12A|12|15\*)\b\s*$", _norm(" ".join(parts))):
                    break
            pair = _norm(" ".join(parts))
            # avoid capturing non-pair explanation lines
            if "(" in pair and ")" in pair and " and " in pair:
                film_pairs.append(pair)
            i = j
            continue

        i += 1

    # Second pass: attach parsed “Further information” content under each L2 subtopic
    # We scan by encountering a subtopic code-only marker line like "1.1.1" and then
    # parse until the next subtopic marker or the next L1 section.
    code_only_re = re.compile(r"^(1\.[1-3]\.\d)\s*$")
    current_sub: Optional[str] = None  # e.g. "1.1.1"
    current_l2_code: Optional[str] = None
    current_l3_code: Optional[str] = None
    open_depth1: Optional[str] = None  # code of “including:” heading under L3
    open_depth2: Optional[str] = None  # code of short “mise-en-scène, including:” heading
    idx1 = 0
    idx2 = 0
    idx_b = 0

    def reset_nesting() -> None:
        nonlocal open_depth1, open_depth2
        open_depth1 = None
        open_depth2 = None

    def start_l3(title: str) -> None:
        nonlocal current_l3_code, idx1, idx2, idx_b
        if not current_l2_code:
            return
        idx1 += 1
        idx2 = 0
        idx_b = 0
        reset_nesting()
        t = _norm(title)
        t = re.sub(r"^Learners should\s+", "", t, flags=re.IGNORECASE).strip()
        t = t.rstrip(":").strip()
        current_l3_code = f"{current_l2_code}_s{idx1:02d}"
        _add_node(nodes, current_l3_code, t, 3, current_l2_code)

    def add_heading(level: int, parent: str, text_: str, prefix: str) -> str:
        nonlocal idx2
        idx2 += 1
        code = f"{parent}_{prefix}{idx2:02d}"
        _add_node(nodes, code, _norm(text_), level, parent)
        return code

    def add_bullet(level: int, parent: str, text_: str) -> None:
        nonlocal idx_b
        idx_b += 1
        _add_node(nodes, f"{parent}_b{idx_b:02d}", _norm(text_), level, parent)

    for raw in block:
        s = _norm(raw)
        if not s or _looks_like_header_footer(s):
            continue
        if content_header_re.match(s):
            continue
        mco = code_only_re.match(s)
        if mco:
            current_sub = mco.group(1)
            current_l2_code = l2_codes.get(current_sub)
            current_l3_code = None
            idx1 = 0
            reset_nesting()
            continue
        if not current_l2_code:
            continue

        # L3 headings (Learners should ...)
        if learner_head_re.match(s):
            start_l3(s)
            continue

        if not current_l3_code:
            continue

        bm = bullet_re.match(s)
        if not bm:
            continue
        bt = _norm(bm.group(1))

        # Heading heuristics:
        # - A bullet ending with ':' or containing 'including:' is often a structural heading.
        is_heading = bt.endswith(":") or bt.lower().endswith("including:") or bt.lower().endswith("including") or bt.lower().endswith("for example:")

        if is_heading:
            # depth2 headings are typically short and have a comma before 'including:' (e.g. 'mise-en-scène, including:')
            if bt.lower().endswith("including:") and "," in bt and len(bt) <= 45 and open_depth1:
                open_depth2 = add_heading(5, open_depth1, bt.rstrip(":"), "h")
                continue
            # depth1 heading under the L3
            open_depth1 = add_heading(4, current_l3_code, bt.rstrip(":"), "h")
            open_depth2 = None
            continue

        # Non-heading bullets attach to deepest open heading
        if open_depth2:
            add_bullet(6, open_depth2, bt)
        elif open_depth1:
            add_bullet(5, open_depth1, bt)
        else:
            add_bullet(4, current_l3_code, bt)

    # Add set-film options under a separate L0 to keep maximum depth manageable.
    # This still enables film-pair-aware flashcard generation without creating >L6 nodes.
    l1_11_code = l1_codes.get("1.1")
    if l1_11_code and film_pairs:
        set_films_code = f"{unit_code}_SET_FILMS"
        _add_node(nodes, set_films_code, "Set films for study (choose one pair)", 0, None)
        base_subs = [k for k in sorted(l2_codes.keys()) if k.startswith("1.1.")]
        for i, pair in enumerate(film_pairs, start=1):
            pair_code = f"{set_films_code}_pair{i:02d}"
            _add_node(nodes, pair_code, pair, 1, set_films_code)
            for sub in base_subs:
                root = l2_codes[sub]
                _clone_subtree(nodes, root_code=root, new_parent_code=pair_code, code_prefix=f"{pair_code}__", level_offset=0)

    # De-dupe by code
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
    print("WJEC GCSE DIGITAL MEDIA AND FILM (3670) - UNIT 1 TOPICS SCRAPER")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3670-digital-media-and-film-spec.txt")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}")

    nodes = parse_digital_media_and_film_unit1(text)
    levels = {}
    for n in nodes:
        levels[n.level] = levels.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(nodes)
    print("\n[OK] WJEC 3670 Digital Media and Film (Unit 1) topics scrape complete.")


if __name__ == "__main__":
    main()


