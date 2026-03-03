from __future__ import annotations

import httpx
import structlog
from bs4 import BeautifulSoup
from readability import Document

from anthropic import AsyncAnthropic
from config import Settings
from prompts import build_summary_prompt

log = structlog.get_logger()

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


async def fetch_and_extract(url: str) -> dict:
    async with httpx.AsyncClient(
        headers={"User-Agent": _USER_AGENT},
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    doc = Document(resp.text)
    soup = BeautifulSoup(doc.summary(), "lxml")
    text = soup.get_text(separator="\n", strip=True)

    title = doc.title() or url
    source = httpx.URL(url).host

    log.info("article.extracted", url=url, title=title, words=len(text.split()))
    return {"title": title, "text": text, "source": source}


async def summarize_article(text: str, settings: Settings) -> str:
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    resp = await client.messages.create(
        model=settings.claude_model,
        max_tokens=512,
        system=build_summary_prompt(),
        messages=[{"role": "user", "content": text[:8000]}],
    )
    return resp.content[0].text
