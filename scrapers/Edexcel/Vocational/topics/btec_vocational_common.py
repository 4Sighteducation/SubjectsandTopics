"""
Edexcel BTEC Vocational - Common Helpers
=======================================

Generic helpers for:
- Supabase staging upload
- PDF download + text extraction (pdfplumber)
- AI calls (OpenAI / Anthropic)
- Parsing a numbered hierarchy into topic rows
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import List, Optional

import requests
from dotenv import load_dotenv
from supabase import create_client


ENV_PATH = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")


def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"&", " and ", s)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def load_supabase():
    load_dotenv(ENV_PATH)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_KEY not found in .env")
    return create_client(url, key)


def resolve_ai_provider():
    """
    Returns tuple(provider, client)
    provider in {"openai","anthropic"}
    """
    load_dotenv(ENV_PATH)
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if openai_key:
        try:
            from openai import OpenAI

            return ("openai", OpenAI(api_key=openai_key))
        except Exception:
            pass

    if anthropic_key:
        try:
            import anthropic

            return ("anthropic", anthropic.Anthropic(api_key=anthropic_key))
        except Exception:
            pass

    raise RuntimeError("No AI API keys found (OPENAI_API_KEY or ANTHROPIC_API_KEY)")


def call_ai(provider: str, client, *, prompt: str, max_tokens: int = 16000) -> str:
    last_err: Exception | None = None
    for attempt in range(1, 6):
        try:
            if provider == "openai":
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You extract hierarchical curriculum topic structures from specification documents. Follow instructions exactly.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content or ""

            if provider == "anthropic":
                msg = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}],
                )
                return msg.content[0].text or ""

            raise ValueError(f"Unknown AI provider: {provider}")
        except Exception as e:
            last_err = e
            time.sleep(2**attempt)

    raise RuntimeError(f"AI call failed after retries: {last_err}") from last_err


def download_pdf(url: str, *, timeout: int = 60) -> bytes:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    if r.content[:4] != b"%PDF":
        raise ValueError(f"Downloaded content is not a PDF: {url}")
    return r.content


def extract_pdf_text(pdf_content: bytes) -> str:
    try:
        import pdfplumber
    except ImportError as e:
        raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber") from e

    logging.getLogger("pdfminer").setLevel(logging.ERROR)

    text = []
    with pdfplumber.open(BytesIO(pdf_content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True)
            if page_text:
                text.append(page_text)
    return "\n".join(text)


def slice_relevant_text(text: str, *, keywords: List[str], max_chars: int = 220_000) -> str:
    if not text:
        return ""
    low = text.lower()
    hits = [low.find(k.lower()) for k in keywords]
    hits = [h for h in hits if h >= 0]
    start = min(hits) if hits else 0
    return text[start : start + max_chars]


@dataclass(frozen=True)
class ParsedTopic:
    code: str
    title: str
    level: int
    parent_code: Optional[str]


_NUM_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$")


def parse_numbered_hierarchy(
    hierarchy_text: str,
    *,
    code_prefix: str,
    base_parent_code: Optional[str],
    level_offset: int = 0,
    level_cap: int = 4,
) -> List[ParsedTopic]:
    out: List[ParsedTopic] = []
    if not hierarchy_text:
        return out

    for raw in hierarchy_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _NUM_RE.match(line)
        if not m:
            continue
        number = m.group(1)
        title = m.group(2).strip()

        lvl = number.count(".") + level_offset
        if lvl > level_cap:
            continue

        code = f"{code_prefix}-{number.replace('.', '-')}"

        if "." in number:
            parent_number = number.rsplit(".", 1)[0]
            parent = f"{code_prefix}-{parent_number.replace('.', '-')}"
        else:
            parent = base_parent_code

        out.append(ParsedTopic(code=code, title=title, level=lvl, parent_code=parent))

    return out


def upsert_staging_subject(
    sb,
    *,
    exam_board: str,
    qualification_type: str,
    subject_name: str,
    subject_code: str,
    specification_url: str,
) -> str:
    res = (
        sb.table("staging_aqa_subjects")
        .upsert(
            {
                "exam_board": exam_board,
                "qualification_type": qualification_type,
                "subject_name": subject_name,
                "subject_code": subject_code,
                "specification_url": specification_url,
            },
            on_conflict="subject_code,qualification_type,exam_board",
        )
        .execute()
    )
    if not res.data:
        raise RuntimeError("Failed to upsert staging_aqa_subjects")
    return res.data[0]["id"]


def replace_subject_topics(
    sb,
    *,
    subject_id: str,
    exam_board: str,
    topics: List[ParsedTopic],
    batch_size: int = 200,
) -> int:
    # IMPORTANT:
    # In our Supabase staging schema, topic uniqueness is enforced by (subject_id, topic_code).
    # exam_board is NOT part of that unique key, so we must clear ALL topics for this subject_id
    # before inserting, regardless of exam_board value (including NULL / legacy rows).
    sb.table("staging_aqa_topics").delete().eq("subject_id", subject_id).execute()

    if not topics:
        return 0

    payload = [
        {
            "subject_id": subject_id,
            "exam_board": exam_board,
            "topic_code": t.code,
            "topic_name": t.title,
            "topic_level": t.level,
        }
        for t in topics
    ]

    def _is_timeout_error(e: Exception) -> bool:
        msg = str(e).lower()
        return ("statement timeout" in msg) or ("code" in msg and "57014" in msg)

    def _insert_with_split(rows: list, *, size: int) -> list:
        """
        Insert rows with adaptive splitting to avoid Supabase/Postgres statement timeouts.
        """
        if not rows:
            return []
        try:
            res = sb.table("staging_aqa_topics").insert(rows).execute()
            return res.data or []
        except Exception as e:
            if len(rows) == 1 or not _is_timeout_error(e):
                raise
            # Split and retry
            mid = max(1, len(rows) // 2)
            left = _insert_with_split(rows[:mid], size=max(1, size // 2))
            right = _insert_with_split(rows[mid:], size=max(1, size // 2))
            return left + right

    inserted_all = []
    for i in range(0, len(payload), batch_size):
        batch = payload[i : i + batch_size]
        inserted_all.extend(_insert_with_split(batch, size=batch_size))

    code_to_id = {row["topic_code"]: row["id"] for row in inserted_all}

    for t in topics:
        if not t.parent_code:
            continue
        child_id = code_to_id.get(t.code)
        parent_id = code_to_id.get(t.parent_code)
        if not child_id or not parent_id:
            continue
        sb.table("staging_aqa_topics").update({"parent_topic_id": parent_id}).eq("id", child_id).execute()

    return len(inserted_all)


