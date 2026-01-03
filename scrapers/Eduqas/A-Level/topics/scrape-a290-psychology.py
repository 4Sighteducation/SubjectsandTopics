"""
Eduqas/WJEC A Level Psychology (spec from 2015) - Topics Scraper (tables/bullets, max depth L3)

Spec:
  https://www.eduqas.co.uk/media/t3xf3yae/eduqas-a-level-psychology-spec-from-2015-e.pdf

Entry code in spec: A290QS

Deterministic structure:
  - L0: Component 1 / Component 2 / Component 3
  - L1: Major areas (approaches; research-methods sections; behaviours/controversies)
  - L2: Sub-areas (Assumptions/Therapy/Classic research/Debate; categories within behaviours)
  - L3: Bullets / individual items

Ignored:
  - Assessment objectives, maths appendix, admin text
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


BASE_SUBJECT = {
    "name": "Psychology",
    "qualification": "A-Level",
    "pdf_url": "https://www.eduqas.co.uk/media/t3xf3yae/eduqas-a-level-psychology-spec-from-2015-e.pdf",
}

SUBJECTS = [
    {**BASE_SUBJECT, "code": "EDUQAS-A290QS", "exam_board": "EDUQAS"},
    {**BASE_SUBJECT, "code": "WJEC-A290QS", "exam_board": "WJEC"},
]


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
    if "© WJEC" in s or "WJEC CBAC" in s:
        return True
    if s.startswith("A LEVEL PSYCHOLOGY"):
        return True
    if re.fullmatch(r"\d{1,3}", s):
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

    deleted_total = 0
    BATCH = 200
    for lvl in range(7, -1, -1):
        while True:
            rows = (
                supabase.table("staging_aqa_topics")
                .select("id")
                .eq("subject_id", subject_id)
                .eq("exam_board", subject["exam_board"])
                .eq("topic_level", lvl)
                .limit(BATCH)
                .execute()
                .data
                or []
            )
            if not rows:
                break
            ids = [r["id"] for r in rows]
            res = supabase.table("staging_aqa_topics").delete().in_("id", ids).execute()
            deleted_total += len(res.data or [])
    print(f"[OK] Cleared old topics ({deleted_total} rows)")

    inserted = (
        supabase.table("staging_aqa_topics")
        .insert(
            [
                {
                    "subject_id": subject_id,
                    "topic_code": n.code,
                    "topic_name": n.title,
                    "topic_level": n.level,
                    "exam_board": subject["exam_board"],
                }
                for n in nodes
            ]
        )
        .execute()
    )
    print(f"[OK] Uploaded {len(inserted.data)} topics")

    code_to_id = {row["topic_code"]: row["id"] for row in inserted.data}
    linked = 0
    for n in nodes:
        if not n.parent:
            continue
        child_id = code_to_id.get(n.code)
        parent_id = code_to_id.get(n.parent)
        if child_id and parent_id:
            supabase.table("staging_aqa_topics").update({"parent_topic_id": parent_id}).eq("id", child_id).execute()
            linked += 1
    print(f"[OK] Linked {linked} relationships")


def build_nodes(pdf_text: str) -> list[Node]:
    raw_lines = [ln.rstrip("\n") for ln in (pdf_text or "").splitlines()]
    lines = [_norm(ln) for ln in raw_lines]
    lines = [ln for ln in lines if ln and not _looks_like_header_footer(ln)]

    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7\uF0B7\u2023]\s*(.+)$")

    def is_bullet(s: str) -> Optional[str]:
        m = bullet_re.match(s)
        return _norm(m.group(1)) if m else None

    # L0 components
    c1 = "C1"
    c2 = "C2"
    c3 = "C3"
    nodes: list[Node] = []
    nodes.append(Node(code=c1, title="Component 1: Psychology: Past to Present", level=0, parent=None))
    nodes.append(Node(code=c2, title="Component 2: Psychology: Investigating Behaviour", level=0, parent=None))
    nodes.append(Node(code=c3, title="Component 3: Psychology: Implications in the Real World", level=0, parent=None))

    # Locate blocks
    def find_line_idx(prefix: str) -> int:
        for i, ln in enumerate(lines):
            if ln.startswith(prefix):
                return i
        return -1

    i_c1_tbl = find_line_idx("Component 1: Content to be taught")
    i_c2_hdr = find_line_idx("Psychology: Investigating Behaviour")
    i_c2_tbl = find_line_idx("Component 2: Content to be taught")
    i_c3_hdr = find_line_idx("Psychology: Implications in the Real World")
    i_c3_tbl = find_line_idx("Component 3: Content to be taught")
    i_cont = find_line_idx("Controversy in psychology")
    i_ao = find_line_idx("Below are the assessment objectives")

    if min(i_c1_tbl, i_c2_hdr, i_c2_tbl, i_c3_hdr, i_c3_tbl, i_cont) == -1:
        raise RuntimeError("Could not locate Psychology component anchors.")
    if i_ao == -1:
        i_ao = len(lines)

    # --------------------
    # Component 1: 5 approaches table (deterministic parse)
    # --------------------
    approaches = ["Biological", "Psychodynamic", "Behaviourist", "Cognitive", "Positive"]
    block_c1 = lines[i_c1_tbl:i_c2_hdr]

    # index by approach names
    idxs = []
    for i, ln in enumerate(block_c1):
        if ln in approaches:
            idxs.append((ln, i))
    if len(idxs) != 5:
        raise RuntimeError("Could not locate all 5 approaches in Component 1.")
    idxs.sort(key=lambda x: x[1])

    def add_l3_bullets(parent: str, items: list[str], code_prefix: str) -> None:
        b = 0
        for it in items:
            if not it:
                continue
            b += 1
            nodes.append(Node(code=f"{code_prefix}_B{b:03d}", title=_norm(it), level=3, parent=parent))

    for a_idx, (a_name, a_start) in enumerate(idxs):
        a_end = idxs[a_idx + 1][1] if a_idx + 1 < len(idxs) else len(block_c1)
        seg = [ln for ln in block_c1[a_start + 1 : a_end] if ln and ln not in {"Approach", "Assumptions (including)", "Therapy (one per approach)", "Classic research", "Contemporary debate"}]
        a_code = f"{c1}_A{a_idx+1:02d}"
        nodes.append(Node(code=a_code, title=a_name, level=1, parent=c1))

        # Split into: assumptions (bullets, with wrapped continuations) + therapy options + citation + debate.
        # This prevents junk L3 nodes like a bare "OR" and stops wrapped bullet fragments being mis-filed.
        known_therapy_terms = {
            "drug therapy",
            "psychosurgery",
            "aversion therapy",
            "systematic desensitisation",
            "cognitive behavioural therapy",
            "rational emotive behaviour therapy",
            "mindfulness",
            "quality of life therapy",
            "dream analysis",
            "psychodrama",
        }

        def looks_like_therapy_line(s: str) -> bool:
            low = s.lower()
            if low == "or":
                return True
            if low in known_therapy_terms:
                return True
            if "therapy" in low:
                return True
            return False

        # Find citation start (classic research) in the segment.
        cit_start = None
        for j, ln in enumerate(seg):
            if re.search(r"\(\d{4}\)", ln):
                cit_start = j
                break

        pre_cit = seg[:cit_start] if cit_start is not None else seg
        post_cit = seg[cit_start:] if cit_start is not None else []

        assumptions: list[str] = []
        therapy_raw: list[str] = []

        cur_ass_parts: list[str] = []
        in_therapy = False

        def flush_ass() -> None:
            nonlocal cur_ass_parts
            if cur_ass_parts:
                assumptions.append(_norm(" ".join(cur_ass_parts)))
            cur_ass_parts = []

        for ln in pre_cit:
            if not ln:
                continue
            b = is_bullet(ln)
            if b:
                in_therapy = False
                flush_ass()
                cur_ass_parts = [b]
                continue

            if looks_like_therapy_line(ln):
                in_therapy = True
                flush_ass()
                therapy_raw.append(ln)
                continue

            if cur_ass_parts and not in_therapy:
                # wrapped continuation of assumptions bullet (e.g. "influence of childhood" + "experiences")
                cur_ass_parts.append(ln)
                continue

            # fallback: treat remaining pre-citation lines as therapy terms
            in_therapy = True
            flush_ass()
            therapy_raw.append(ln)

        flush_ass()
        l2_ass = f"{a_code}_ASS"
        nodes.append(Node(code=l2_ass, title="Assumptions", level=2, parent=a_code))
        add_l3_bullets(l2_ass, assumptions, l2_ass)

        # Clean therapy options: merge OR and remove bare OR nodes.
        cleaned = [_norm(x) for x in therapy_raw if _norm(x)]
        therapy_lines: list[str] = []
        i = 0
        while i < len(cleaned):
            if cleaned[i].lower() == "or":
                i += 1
                continue
            if i + 2 < len(cleaned) and cleaned[i + 1].lower() == "or":
                therapy_lines.append(f"{cleaned[i]} OR {cleaned[i + 2]}")
                i += 3
                continue
            therapy_lines.append(cleaned[i])
            i += 1

        # Classic research + debate: debate is typically the last line after the citation.
        citation = ""
        debate = ""
        if post_cit:
            if len(post_cit) >= 2:
                debate = post_cit[-1]
                citation = " ".join(post_cit[:-1])
            else:
                citation = post_cit[0]

        l2_th = f"{a_code}_TH"
        nodes.append(Node(code=l2_th, title="Therapy", level=2, parent=a_code))
        add_l3_bullets(l2_th, therapy_lines, l2_th)

        l2_cr = f"{a_code}_CR"
        nodes.append(Node(code=l2_cr, title="Classic research", level=2, parent=a_code))
        if citation:
            nodes.append(Node(code=f"{l2_cr}_CIT", title=_norm(citation), level=3, parent=l2_cr))

        l2_db = f"{a_code}_DB"
        nodes.append(Node(code=l2_db, title="Contemporary debate", level=2, parent=a_code))
        if debate:
            nodes.append(Node(code=f"{l2_db}_T1", title=_norm(debate), level=3, parent=l2_db))

    # --------------------
    # Component 2: Research methods bullets
    # --------------------
    block_c2 = lines[i_c2_tbl:i_c3_hdr]
    # strip the initial boilerplate
    # build L1 headings from non-bullets that look like section titles
    heading_blacklist = {
        "Learners will be expected to demonstrate:",
        "knowledge, understanding and evaluation of:",
        "knowledge and understanding of:",
    }
    cur_h_code: Optional[str] = None
    h_idx = 0
    b_idx = 0
    citation_mode = False
    citation_parts: list[str] = []

    def flush_citation() -> None:
        nonlocal citation_parts, citation_mode, b_idx
        if citation_mode and cur_h_code and citation_parts:
            b_idx += 1
            nodes.append(Node(code=f"{cur_h_code}_I{b_idx:03d}", title=_norm(" ".join(citation_parts)), level=2, parent=cur_h_code))
        citation_parts = []
        citation_mode = False

    for ln in block_c2:
        if ln in heading_blacklist:
            continue
        if ln.lower().startswith("component 2:"):
            continue
        if ln.lower().startswith("each year learners will need"):
            break
        b = is_bullet(ln)
        if b:
            flush_citation()
            if cur_h_code:
                b_idx += 1
                nodes.append(Node(code=f"{cur_h_code}_B{b_idx:03d}", title=b, level=2, parent=cur_h_code))
            continue
        # titles: end with ':' like Social Psychology:
        if ln.endswith(":") and len(ln) <= 45 and ln[0].isupper() and not ln.lower().startswith(("knowledge ", "learners ", "both ")):
            flush_citation()
            h_idx += 1
            cur_h_code = f"{c2}_H{h_idx:02d}"
            nodes.append(Node(code=cur_h_code, title=ln.rstrip(":"), level=1, parent=c2))
            b_idx = 0
            continue
        # citations for Social/Developmental psychology: join wrapped lines until next heading/bullets
        if cur_h_code and re.search(r"\(\d{4}\)", ln):
            citation_mode = True
            citation_parts = [ln]
            continue
        if citation_mode and cur_h_code:
            # keep appending citation wrap lines until we hit another clear heading
            if ln.endswith(":"):
                flush_citation()
                h_idx += 1
                cur_h_code = f"{c2}_H{h_idx:02d}"
                nodes.append(Node(code=cur_h_code, title=ln.rstrip(":"), level=1, parent=c2))
                b_idx = 0
                continue
            # stop citation if the line looks like a new section title
            if len(ln) < 70 and ln[0].isupper() and "." not in ln and "," not in ln and not re.search(r"\d", ln):
                flush_citation()
                h_idx += 1
                cur_h_code = f"{c2}_H{h_idx:02d}"
                nodes.append(Node(code=cur_h_code, title=ln, level=1, parent=c2))
                b_idx = 0
                continue
            citation_parts.append(ln)
            continue

        # other headings (sentence-case) - only if they are short and not full sentences
        if (
            len(ln) < 55
            and ln[0].isupper()
            and "." not in ln
            and not ln.lower().startswith(("both ", "knowledge ", "learners "))
            and ln.lower() not in {"assessment", "investigation one", "investigation two"}
        ):
            flush_citation()
            h_idx += 1
            cur_h_code = f"{c2}_H{h_idx:02d}"
            nodes.append(Node(code=cur_h_code, title=ln, level=1, parent=c2))
            b_idx = 0
            continue

    flush_citation()

    # --------------------
    # Component 3: Applications (behaviours) table + Controversies bullets
    # --------------------
    block_beh = lines[i_c3_tbl:i_cont]
    behaviours = [
        "Addictive behaviours",
        "Autistic spectrum behaviours",
        "Bullying behaviours",
        "Criminal behaviours",
        "Schizophrenia",
        "Stress",
    ]

    # find each behaviour start index
    beh_idxs = []
    for i, ln in enumerate(block_beh):
        if ln in behaviours:
            beh_idxs.append((ln, i))
    beh_idxs.sort(key=lambda x: x[1])

    # parse each behaviour as: For example (bio) bullets; For example (ind diff) bullets; For example (social) bullets; Including (methods) bullets
    for bi, (beh, start) in enumerate(beh_idxs):
        end = beh_idxs[bi + 1][1] if bi + 1 < len(beh_idxs) else len(block_beh)
        seg = [ln for ln in block_beh[start + 1 : end] if ln]
        beh_code = f"{c3}_B{bi+1:02d}"
        nodes.append(Node(code=beh_code, title=beh, level=1, parent=c3))

        cats = [
            ("BIO", "Biological explanations"),
            ("IND", "Individual differences explanations"),
            ("SOC", "Social psychological explanations"),
            ("MOD", "Methods of modifying this behaviour"),
        ]
        cat_items = {k: [] for k, _ in cats}
        cat_idx = 0
        for_example_seen = 0
        in_methods = False

        for ln in seg:
            if ln.lower().startswith("for example"):
                if for_example_seen < 2:
                    cat_idx = for_example_seen
                    for_example_seen += 1
                else:
                    cat_idx = 2
                continue
            if ln.lower().startswith("including"):
                in_methods = True
                cat_idx = 3
                continue
            b = is_bullet(ln)
            if b:
                key = cats[cat_idx][0]
                cat_items[key].append(b)
                continue

        for ci, (k, title) in enumerate(cats, 1):
            l2 = f"{beh_code}_{k}"
            nodes.append(Node(code=l2, title=title, level=2, parent=beh_code))
            add_l3_bullets(l2, cat_items[k], l2)

    # Controversies
    block_cont = lines[i_cont:i_ao]
    cont_parent = f"{c3}_CONT"
    nodes.append(Node(code=cont_parent, title="Controversies", level=1, parent=c3))
    current: Optional[str] = None
    current_code: Optional[str] = None
    c_idx = 0
    b_idx = 0
    for ln in block_cont:
        if ln.lower().startswith("controversy in psychology") or ln.lower().startswith("exploration of the controversy"):
            continue
        if ln.lower().startswith("below are the assessment objectives"):
            break
        b = is_bullet(ln)
        if b:
            if current_code:
                b_idx += 1
                nodes.append(Node(code=f"{current_code}_B{b_idx:03d}", title=b, level=3, parent=current_code))
            continue
        # new controversy heading
        if ln and ln[0].isupper() and len(ln) < 60 and not ln.endswith(":"):
            c_idx += 1
            current_code = f"{cont_parent}_C{c_idx:02d}"
            nodes.append(Node(code=current_code, title=ln, level=2, parent=cont_parent))
            b_idx = 0

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("EDUQAS/WJEC A LEVEL PSYCHOLOGY - TOPICS SCRAPER (L0-L3)")
    print("=" * 80)
    print(f"Spec: {BASE_SUBJECT['pdf_url']}")

    pdf_text = download_pdf_text(BASE_SUBJECT["pdf_url"])
    nodes = build_nodes(pdf_text)

    by_level: dict[int, int] = {}
    for n in nodes:
        by_level[n.level] = by_level.get(n.level, 0) + 1
    print("\n[INFO] Level breakdown:")
    for lvl in sorted(by_level):
        print(f"  - L{lvl}: {by_level[lvl]}")

    for subj in SUBJECTS:
        print(f"\n[INFO] Uploading for exam_board={subj['exam_board']} code={subj['code']} ...")
        upload_to_staging(subject=subj, nodes=nodes)

    print("[OK] Psychology (A-Level) scrape complete (uploaded to EDUQAS + WJEC).")


if __name__ == "__main__":
    main()


