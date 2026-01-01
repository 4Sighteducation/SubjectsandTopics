"""
CCEA - Common Helpers
====================

Shared helpers for:
- Supabase staging uploads (subjects/topics)
- PDF download + text extraction
- AI calls (OpenAI/Anthropic)
- Parsing numbered hierarchy into topic rows
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from supabase import create_client


ENV_PATH = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")


def slugify_code(s: str) -> str:
    s = (s or "").strip().upper()
    s = re.sub(r"&", " AND ", s)
    s = re.sub(r"[^A-Z0-9]+", "_", s)
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
    """
    Simple PDF fetch (no anti-bot handling).

    NOTE: CCEA content is often Cloudflare protected and may return 403 from
    server-side environments (e.g. Railway). Use `download_pdf_with_driver_session`
    when you have a Selenium session that has already cleared Cloudflare.
    """
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    if r.content[:4] != b"%PDF":
        raise ValueError(f"Downloaded content is not a PDF: {url}")
    return r.content


def _browser_headers(*, referer: str | None = None) -> Dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf;q=0.8,*/*;q=0.7",
        "Accept-Language": "en-GB,en;q=0.9",
        "Connection": "keep-alive",
        **({"Referer": referer} if referer else {}),
    }


def build_requests_session_from_selenium(driver: Any, *, referer: str | None = None) -> requests.Session:
    """
    Convert an active Selenium session (that has cleared Cloudflare) into a requests.Session
    by copying cookies + setting browser-like headers.
    """
    sess = requests.Session()
    sess.headers.update(_browser_headers(referer=referer))
    try:
        cookies = driver.get_cookies() or []
    except Exception:
        cookies = []
    for c in cookies:
        try:
            sess.cookies.set(
                c.get("name"),
                c.get("value"),
                domain=c.get("domain"),
                path=c.get("path") or "/",
            )
        except Exception:
            continue
    return sess


def download_pdf_with_driver_session(
    driver: Any,
    url: str,
    *,
    referer: str | None = None,
    timeout: int = 60,
    retries: int = 4,
) -> bytes:
    """
    Download a PDF using cookies from a Selenium session that has cleared Cloudflare.

    This is the key workaround for CCEA PDFs:
    - Selenium (non-headless) clears the JS challenge
    - We reuse those cookies in requests to fetch the actual PDF bytes
    """
    last_err: Exception | None = None
    sess = build_requests_session_from_selenium(driver, referer=referer)

    for attempt in range(1, retries + 1):
        try:
            resp = sess.get(url, timeout=timeout, allow_redirects=True)
            if resp.status_code == 403:
                raise RuntimeError(f"403 Forbidden (source site blocked download): {url}")
            resp.raise_for_status()
            content = resp.content
            if content[:4] != b"%PDF":
                snippet = content[:200].decode("utf-8", errors="ignore")
                raise RuntimeError(f"Downloaded content is not a PDF (got {resp.status_code}). Snippet: {snippet}")
            return content
        except Exception as e:
            last_err = e
            time.sleep(min(2**attempt, 20))

    raise RuntimeError(f"PDF download failed after retries: {url} ({last_err})") from last_err


def ensure_storage_bucket(
    *,
    supabase_url: str,
    service_key: str,
    bucket: str,
    public: bool = True,
) -> None:
    """
    Best-effort: ensure a storage bucket exists.
    Uses the Storage REST API directly (service role key required).
    """
    try:
        r = requests.post(
            f"{supabase_url.rstrip('/')}/storage/v1/bucket",
            headers={
                "Authorization": f"Bearer {service_key}",
                "apikey": service_key,
                "Content-Type": "application/json",
            },
            json={"id": bucket, "name": bucket, "public": public},
            timeout=20,
        )
        # 409 = already exists (OK)
        if r.status_code not in (200, 201, 409):
            logging.warning(f"[CCEA] ensure_storage_bucket unexpected status {r.status_code}: {r.text[:200]}")
    except Exception as e:
        logging.warning(f"[CCEA] ensure_storage_bucket failed (continuing): {e}")


def upload_pdf_bytes_to_storage(
    sb: Any,
    *,
    bucket: str,
    path: str,
    pdf_bytes: bytes,
) -> str:
    """
    Upload PDF bytes to Supabase Storage and return a public URL.
    Bucket should be public for stable URLs stored in DB.
    """
    sb.storage.from_(bucket).upload(
        path,
        pdf_bytes,
        file_options={"content-type": "application/pdf", "upsert": "true"},
    )
    return sb.storage.from_(bucket).get_public_url(path)


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
    batch_size: int = 500,
) -> int:
    # Unique constraint is (subject_id, topic_code) so we must clear all rows for this subject.
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
            "parent_topic_id": None,
        }
        for t in topics
    ]

    def _insert(rows: list) -> None:
        if not rows:
            return
        sb.table("staging_aqa_topics").insert(rows).execute()

    # Batch insert
    for i in range(0, len(payload), batch_size):
        _insert(payload[i : i + batch_size])
        time.sleep(0.1)

    # Second pass: wire up parent_topic_id so the data viewer can collapse/expand properly.
    # We do this after insert because parent_topic_id references UUID ids.
    rows = (
        sb.table("staging_aqa_topics")
        .select("id,topic_code")
        .eq("subject_id", subject_id)
        .execute()
        .data
        or []
    )
    code_to_id = {r["topic_code"]: r["id"] for r in rows if r.get("topic_code") and r.get("id")}
    # Build full-row upserts to avoid NOT NULL violations if a row is unexpectedly missing.
    updates = []
    for t in topics:
        if not t.parent_code:
            continue
        child_id = code_to_id.get(t.code)
        parent_id = code_to_id.get(t.parent_code)
        if child_id and parent_id:
            updates.append(
                {
                    "id": child_id,
                    "subject_id": subject_id,
                    "exam_board": exam_board,
                    "topic_code": t.code,
                    "topic_name": t.title,
                    "topic_level": t.level,
                    "parent_topic_id": parent_id,
                }
            )

    for i in range(0, len(updates), batch_size):
        sb.table("staging_aqa_topics").upsert(updates[i : i + batch_size], on_conflict="id").execute()
        time.sleep(0.05)

    return len(payload)


