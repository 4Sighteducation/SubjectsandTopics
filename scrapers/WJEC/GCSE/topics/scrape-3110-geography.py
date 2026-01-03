"""
WJEC GCSE Geography (3110) - Topics Scraper (Units 1 & 2 only)

Spec:
  https://www.wjec.co.uk/media/mlyil2jr/wjec-gcse-geography-spec-from-2016-e.pdf

User requirement:
  - Only the exam units are needed:
      - Unit 1: Changing Physical and Human Landscapes
      - Unit 2: Environmental and Development Issues
  - Include Core themes AND both Options in each unit (so centres can choose).

PDF structure:
  - Each theme is organised into Key Ideas.
  - Each Key Idea contains a table with "Key questions" and "Depth of study".
    In extracted text, the Key Questions are listed first, and the Depth of study
    paragraphs usually appear afterwards (in the same order). We align depth blocks
    to questions sequentially.

Hierarchy:
  - L0: Unit 1 / Unit 2
  - L1: Theme (Core Theme 1/2/5/6 + Option Theme 3/4/7/8)
  - L2: Key Idea
  - L3: Key Question
  - L4: Depth of study (1+ paragraphs/bullets)
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
    "name": "Geography",
    "code": "WJEC-3110",
    "qualification": "GCSE",
    "exam_board": "WJEC",
    "pdf_url": "https://www.wjec.co.uk/media/mlyil2jr/wjec-gcse-geography-spec-from-2016-e.pdf",
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
    if re.fullmatch(r"\d{1,3}", s):
        return True
    if s.startswith("GCSE GEOGRAPHY"):
        return True
    return False


def download_pdf_text(url: str) -> str:
    print("[INFO] Downloading PDF...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    reader = PdfReader(BytesIO(resp.content))
    print(f"[OK] Downloaded {len(reader.pages)} pages")
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def parse_geography(text: str) -> list[Node]:
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Find the real subject content blocks: 2.1 Unit 1 -> 2.2 Unit 2 -> 2.3 Unit 3
    u1_re = re.compile(r"^2\.1\s+Unit\s+1\b(?!\s+\d)", flags=re.IGNORECASE)
    u2_re = re.compile(r"^2\.2\s+Unit\s+2\b(?!\s+\d)", flags=re.IGNORECASE)
    u3_re = re.compile(r"^2\.3\s+Unit\s+3\b(?!\s+\d)", flags=re.IGNORECASE)

    def find_block(start_re: re.Pattern, end_re: re.Pattern) -> list[str]:
        """
        Find a unit content slice.
        The PDF contains a contents page with page-number suffixes; our start regex excludes those.
        We still keep detection permissive because extracted headings vary slightly.
        """
        start = None
        for i, raw in enumerate(lines):
            if start_re.match(_norm(raw)):
                start = i
                break
        if start is None:
            return []

        end = len(lines)
        for j in range(start + 1, len(lines)):
            if end_re.match(_norm(lines[j])):
                end = j
                break

        # Fallback: if the expected next-unit header isn't present, stop at Assessment section.
        if end == len(lines):
            for j in range(start + 1, len(lines)):
                sj = _norm(lines[j])
                if sj.startswith("3 Assessment") or sj.startswith("3. Assessment"):
                    end = j
                    break

        return lines[start:end]

    unit1 = find_block(u1_re, u2_re)
    unit2 = find_block(u2_re, u3_re)

    # Patterns inside units
    theme_re = re.compile(r"^(Core Theme\s+\d+|Theme\s+\d+):\s+(.+)$", flags=re.IGNORECASE)
    key_idea_re = re.compile(r"^Key Idea\s+(\d+\.\d+):\s+(.+)$", flags=re.IGNORECASE)
    key_q_re = re.compile(r"^(\d+\.\d+\.\d+)\s+(.+)$")  # 1.1.1 ...
    header_table_re = re.compile(r"^Key questions\s+Depth of study$", flags=re.IGNORECASE)
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7\u2024\u25aa\u25a0\u25e6\u2023\u2043\u2219\u00b7\u2022\u25cf\u25cb\u25a1\u25a3\u25aa\u25a0\u2027\u25cf\u2010\u2013\u2014\u2022\u25cf\u00b7\u2022\u25cf\u25cb\u00b7\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf]\s*(.+)$")
    # The bullet char in this PDF often extracts as ''
    bullet2_re = re.compile(r"^[\u2022\u25cf\u00b7\u25aa\u25a0\u25e6\u2023\u2043\u2219\u00b7\u2022\u25cf\u25cb\u25a1\u25a3\u25aa\u25a0\u2027\u2022\u25cf\u00b7\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf]\s*(.+)$")
    bullet3_re = re.compile(r"^[\u2022\u25cf\u00b7\u25aa\u25a0\u25e6\u2023\u2043\u2219\u00b7\u2022\u25cf\u25cb\u25a1\u25a3\u25aa\u25a0\u2027\u2022\u25cf\u00b7\u2022\u25cf\u2022\u25cf\u2022\u25cf\u2022\u25cf]\s*(.+)$")

    def is_bullet(s: str) -> bool:
        return s.startswith("") or s.startswith("•") or s.startswith("-") or bool(re.match(r"^[•]\s*", s))

    def parse_unit(block: list[str], unit_code: str, unit_title: str) -> list[Node]:
        nodes: list[Node] = []
        nodes.append(Node(code=unit_code, title=unit_title, level=0, parent=None))

        current_theme: Optional[str] = None
        current_key_idea: Optional[str] = None

        # For each key idea, we buffer its lines and parse as a chunk for stable question/depth alignment.
        buf: list[str] = []

        def flush_key_idea_buffer() -> None:
            nonlocal buf
            if not current_key_idea or not buf:
                buf = []
                return

            # 1) Extract key questions (e.g. 1.1.1 ...)
            questions: list[tuple[str, str]] = []
            cur_q_code: Optional[str] = None
            cur_q_parts: list[str] = []
            depth_start_idx = None
            seen_any_q = False

            def flush_q() -> None:
                nonlocal cur_q_code, cur_q_parts
                if cur_q_code and cur_q_parts:
                    questions.append((cur_q_code, _norm(" ".join(cur_q_parts))))
                cur_q_code = None
                cur_q_parts = []

            for i, raw in enumerate(buf):
                s = _norm(raw)
                if _looks_like_header_footer(s) or header_table_re.match(s):
                    continue

                m = key_q_re.match(s)
                if m:
                    flush_q()
                    cur_q_code = m.group(1)
                    cur_q_parts = [m.group(2)]
                    seen_any_q = True
                    continue

                if not seen_any_q or not cur_q_code:
                    continue

                # Question line wraps in this PDF; continuation lines tend to start lowercase or end with '?'
                if s and (s[0].islower() or s.endswith("?")):
                    cur_q_parts.append(s)
                    continue

                # First uppercase non-question line after questions => start of depth of study
                if s and s[0].isupper():
                    flush_q()
                    depth_start_idx = i
                    break

            if depth_start_idx is None:
                flush_q()
                depth_start_idx = len(buf)

            if not questions:
                buf = []
                return

            # 2) Split depth of study into paragraph blocks (blank-line separated) preserving order
            depth_paragraphs: list[list[str]] = []
            cur_par: list[str] = []
            for raw in buf[depth_start_idx:]:
                if raw.strip() == "":
                    if cur_par:
                        depth_paragraphs.append(cur_par)
                        cur_par = []
                    continue
                s = _norm(raw)
                if not s or _looks_like_header_footer(s) or header_table_re.match(s):
                    continue
                if theme_re.match(s) or key_idea_re.match(s) or key_q_re.match(s):
                    continue
                cur_par.append(s)
            if cur_par:
                depth_paragraphs.append(cur_par)

            # 3) Assign each paragraph to the most relevant question by keyword overlap
            STOP = {
                "the",
                "and",
                "or",
                "of",
                "to",
                "in",
                "on",
                "a",
                "an",
                "is",
                "are",
                "be",
                "by",
                "for",
                "how",
                "what",
                "why",
                "can",
                "do",
                "does",
                "their",
                "its",
                "within",
                "with",
                "at",
                "as",
                "from",
                "into",
                "over",
                "this",
                "that",
                "these",
                "those",
            }

            def stem(w: str) -> str:
                w = w.lower()
                w = re.sub(r"[^a-z]", "", w)
                for suf in ("ing", "ed", "es", "s"):
                    if w.endswith(suf) and len(w) > len(suf) + 2:
                        w = w[: -len(suf)]
                        break
                return w

            def token_set(t: str) -> set[str]:
                words = re.findall(r"[A-Za-z]+", t)
                out = set()
                for w in words:
                    sw = stem(w)
                    if not sw or len(sw) < 3 or sw in STOP:
                        continue
                    out.add(sw)
                return out

            q_tokens = [token_set(qtitle) for _, qtitle in questions]

            assignments: list[list[list[str]]] = [[] for _ in questions]  # q_idx -> list of paragraph lines
            last_idx = 0
            for par in depth_paragraphs:
                par_text = _norm(" ".join(par))
                pt = token_set(par_text)
                scores: list[int] = []
                for qi, qt in enumerate(q_tokens):
                    sc = len(pt & qt)
                    # bonus for obvious cue words
                    if "human activity" in par_text.lower() and ("human" in qt or "activ" in qt):
                        sc += 5
                    if "manage" in par_text.lower() and ("manag" in qt or "strateg" in qt):
                        sc += 4
                    scores.append(sc)
                best = max(scores) if scores else 0
                if best == 0:
                    chosen = last_idx
                else:
                    candidates = [i for i, sc in enumerate(scores) if sc == best]
                    # keep ordering: prefer candidates at/after last_idx
                    after = [c for c in candidates if c >= last_idx]
                    chosen = min(after) if after else min(candidates)
                last_idx = chosen
                assignments[chosen].append(par)

            # 4) Emit nodes:
            # - L3: question nodes
            # - L4: suggested study points (split to smaller chunks) from assigned paragraphs
            for (qcode, qtitle), par_list in zip(questions, assignments):
                q_node_code = f"{current_key_idea}_{qcode.replace('.', '_')}"
                nodes.append(Node(code=q_node_code, title=f"{qcode} {qtitle}".strip(), level=3, parent=current_key_idea))

                # Convert assigned paragraphs to small, readable points
                point_idx = 0
                for par in par_list:
                    # further split into items at sentence boundaries for readability
                    text_block = _norm(" ".join(par))
                    # split on sentence ends; keep fairly large pieces if the PDF uses long sentences
                    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", text_block)
                    for piece in pieces:
                        piece = _norm(piece)
                        if not piece:
                            continue
                        point_idx += 1
                        nodes.append(Node(code=f"{q_node_code}_p{point_idx:02d}", title=piece, level=4, parent=q_node_code))

            buf = []

        i = 0
        while i < len(block):
            s = _norm(block[i])
            if not s or _looks_like_header_footer(s):
                i += 1
                continue

            tm = theme_re.match(s)
            if tm:
                flush_key_idea_buffer()
                label = _norm(tm.group(1))
                title = _norm(tm.group(2))
                # Normalize label casing
                label = label.replace("Core theme", "Core Theme")
                theme_code = f"{unit_code}_{label.replace(' ', '_').replace(':', '').replace('/', '_')}"
                current_theme = theme_code
                current_key_idea = None
                nodes.append(Node(code=theme_code, title=f"{label}: {title}", level=1, parent=unit_code))
                i += 1
                continue

            km = key_idea_re.match(s)
            if km and current_theme:
                flush_key_idea_buffer()
                kid = km.group(1)
                ktitle = km.group(2)
                current_key_idea = f"{current_theme}_KI_{kid.replace('.', '_')}"
                nodes.append(Node(code=current_key_idea, title=f"Key Idea {kid}: {ktitle}", level=2, parent=current_theme))
                i += 1
                continue

            # Buffer content lines for current key idea so we can align Qs/Depth reliably
            if current_key_idea:
                buf.append(block[i])
            i += 1

        flush_key_idea_buffer()
        return nodes

    out: list[Node] = []
    out.extend(parse_unit(unit1, "U1", "Unit 1: Changing Physical and Human Landscapes"))
    out.extend(parse_unit(unit2, "U2", "Unit 2: Environmental and Development Issues"))

    # de-dupe by code
    uniq: list[Node] = []
    seen = set()
    for n in out:
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
    print("WJEC GCSE GEOGRAPHY (3110) - TOPICS SCRAPER (U1/U2)")
    print("=" * 80)
    print(f"Spec: {SUBJECT['pdf_url']}\n")

    text = download_pdf_text(SUBJECT["pdf_url"])
    debug_path = Path("scrapers/WJEC/GCSE/topics/debug-wjec-3110-geography-spec.txt")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(text, encoding="utf-8", errors="replace")
    print(f"[OK] Saved debug text to {debug_path.as_posix()}")

    nodes = parse_geography(text)
    levels = {}
    for n in nodes:
        levels[n.level] = levels.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(levels):
        print(f"  - L{lvl}: {levels[lvl]}")

    upload_to_staging(nodes)
    print("\n[OK] WJEC 3110 Geography topics scrape complete.")


if __name__ == "__main__":
    main()


