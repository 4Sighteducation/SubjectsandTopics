"""
Eduqas/WJEC A Level Geography (spec from 2016) - Topics Scraper (table bullets, max depth L3)

Spec:
  https://www.eduqas.co.uk/media/ln4locyz/eduqas-a-level-geography-spec-from-2016-e-24-01-2020.pdf

Entry code in spec: A110QS

Required structure (as requested):
  - L0: Component 1..4
  - L1: Focus item (e.g., 1.1.1 The operation of the coast as a system)
  - L2: Geographical content
  - L3: Bulleted content (joined across wrapped lines)
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
    "name": "Geography",
    "qualification": "A-Level",
    "pdf_url": "https://www.eduqas.co.uk/media/ln4locyz/eduqas-a-level-geography-spec-from-2016-e-24-01-2020.pdf",
}

SUBJECTS = [
    {**BASE_SUBJECT, "code": "EDUQAS-A110QS", "exam_board": "EDUQAS"},
    {**BASE_SUBJECT, "code": "WJEC-A110QS", "exam_board": "WJEC"},
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
    if s.startswith("A LEVEL GEOGRAPHY") or s.startswith("GCE A LEVEL GEOGRAPHY"):
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
    # Parse the Focus tables directly from the extracted text, using the explicit focus codes:
    # 1.x.x (Component 1), 2.x.x (Component 2), 3.x.x (Component 3).
    lines = [ln.rstrip("\n") for ln in (pdf_text or "").splitlines()]
    nodes: list[Node] = []
    comp_titles = {
        1: "Component 1: Changing Landscapes and Changing Places",
        2: "Component 2: Global Systems and Global Governance",
        3: "Component 3: Contemporary Themes in Geography",
        4: "Component 4: Independent Investigation",
    }

    focus_re = re.compile(r"^([1-3])\.(\d)\.(\d)\s+(.+)$")
    bullet_re = re.compile(r"^[•\u2022\u25cf\u00b7\uF0B7\u2023]\s*(.+)$")

    for comp in (1, 2, 3, 4):
        c0 = f"C{comp}"
        nodes.append(Node(code=c0, title=comp_titles[comp], level=0, parent=None))

        if comp == 4:
            # keep NEA as a small shell (not table-based)
            c4_p = f"{c0}_PROC"
            nodes.append(Node(code=c4_p, title="Independent Investigation process (NEA)", level=1, parent=c0))
            steps = [
                "Select a question / title and justify the investigation focus",
                "Plan and manage fieldwork (risk assessment, logistics, methods)",
                "Collect primary field data and relevant secondary data",
                "Present and analyse data (quantitative and qualitative)",
                "Evaluate methods, reliability, limitations and conclusions",
                "Write up the investigation (approx. 3000–4000 words per spec)",
            ]
            for i, step in enumerate(steps, 1):
                nodes.append(Node(code=f"{c4_p}_{i:02d}", title=step, level=2, parent=c4_p))

    current_l2: Optional[str] = None
    bullet_idx = 0
    base_code_counts: dict[str, int] = {}
    i = 0
    while i < len(lines):
        s = _norm(lines[i])
        if not s or _looks_like_header_footer(s):
            i += 1
            continue

        m = focus_re.match(s)
        if m:
            comp_digit = int(m.group(1))
            focus_code = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
            title_rest = m.group(4)

            # Handle cases like: "1.2.3 Glacier movement • Differences between ..."
            inline_bullet = None
            if "•" in title_rest:
                left, right = title_rest.split("•", 1)
                title_rest = left.strip()
                inline_bullet = right.strip()

            title_parts = [title_rest]
            j = i + 1
            while j < len(lines):
                nxt = _norm(lines[j])
                if not nxt or _looks_like_header_footer(nxt):
                    j += 1
                    continue
                if focus_re.match(nxt) or bullet_re.match(nxt):
                    break
                # continuation of the focus title (wrapped)
                title_parts.append(nxt)
                j += 1

            l0 = f"C{comp_digit}"
            base = f"{l0}_{focus_code.replace('.', '_')}"
            base_code_counts[base] = base_code_counts.get(base, 0) + 1
            # Some focus codes are reused across different sections/options in the PDF text extraction.
            # Ensure stable uniqueness for (subject_id, topic_code).
            l1 = base if base_code_counts[base] == 1 else f"{base}_D{base_code_counts[base]:02d}"
            nodes.append(Node(code=l1, title=f"{focus_code} {_norm(' '.join(title_parts))}", level=1, parent=l0))
            current_l2 = f"{l1}_GC"
            nodes.append(Node(code=current_l2, title="Geographical content", level=2, parent=l1))
            bullet_idx = 0

            # If bullet content started on the same line, emit it as the first bullet.
            if inline_bullet:
                bullet_idx += 1
                nodes.append(Node(code=f"{current_l2}_B{bullet_idx:03d}", title=_norm(inline_bullet), level=3, parent=current_l2))

            i = j
            continue

        bm = bullet_re.match(s)
        if bm and current_l2:
            bullet_idx += 1
            text_parts = [bm.group(1)]
            j = i + 1
            while j < len(lines):
                nxt = _norm(lines[j])
                if not nxt or _looks_like_header_footer(nxt):
                    j += 1
                    continue
                if focus_re.match(nxt) or bullet_re.match(nxt):
                    break
                text_parts.append(nxt)
                j += 1
            nodes.append(Node(code=f"{current_l2}_B{bullet_idx:03d}", title=_norm(' '.join(text_parts)), level=3, parent=current_l2))
            i = j
            continue

        i += 1

    return nodes


def main() -> None:
    _force_utf8_stdio()
    print("=" * 80)
    print("EDUQAS/WJEC A LEVEL GEOGRAPHY - TOPICS SCRAPER (L0-L3)")
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
    print("[OK] Geography (A-Level) scrape complete (uploaded to EDUQAS + WJEC).")


if __name__ == "__main__":
    main()


