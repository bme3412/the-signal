from __future__ import annotations

import json

import httpx
import structlog
from bs4 import BeautifulSoup
from readability import Document

from anthropic import AsyncAnthropic
from config import Settings
from prompts import build_angles_prompt, build_enrichment_prompt
from services.source_quality import rank_results, reputation_score

log = structlog.get_logger()

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


async def fetch_and_extract(url: str, settings: Settings | None = None) -> dict:
    """Extract an article's title and text from a URL.

    Prefers Firecrawl when configured (handles JS-rendered pages and most
    anti-bot walls); falls back to plain readability extraction.
    """
    if settings and settings.firecrawl_api_key:
        try:
            return await _extract_via_firecrawl(url, settings)
        except Exception as exc:
            log.warning("article.firecrawl_failed", url=url, error=str(exc))
    return await _extract_via_readability(url)


async def _extract_via_firecrawl(url: str, settings: Settings) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.firecrawl.dev/v2/scrape",
            headers={"Authorization": f"Bearer {settings.firecrawl_api_key}"},
            json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
        )
        resp.raise_for_status()
        payload = resp.json()

    data = payload.get("data") or {}
    text = (data.get("markdown") or "").strip()
    if not payload.get("success") or not text:
        raise ValueError(f"Firecrawl returned no content: {payload.get('error', 'unknown')}")

    metadata = data.get("metadata") or {}
    title = metadata.get("title") or url
    source = httpx.URL(url).host

    log.info("article.extracted_firecrawl", url=url, title=title, words=len(text.split()))
    return {"title": title, "text": text, "source": source}


async def search_topic(
    query: str,
    settings: Settings,
    limit: int = 8,
    tbs: str | None = None,
) -> list[dict]:
    """Find candidate articles for a topic via Firecrawl search.

    Returns [{"title", "url", "description", "source"}], news results first.
    `tbs` is a Google-style recency filter (qdr:d / qdr:w / qdr:m).
    """
    body: dict = {"query": query, "limit": limit, "sources": ["news", "web"]}
    if tbs:
        body["tbs"] = tbs

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.firecrawl.dev/v2/search",
            headers={"Authorization": f"Bearer {settings.firecrawl_api_key}"},
            json=body,
        )
        resp.raise_for_status()
        payload = resp.json()

    if not payload.get("success"):
        raise ValueError(f"Firecrawl search failed: {payload.get('error', 'unknown')}")

    data = payload.get("data") or {}
    if isinstance(data, list):  # v1-style flat list
        raw = data
    else:
        raw = (data.get("news") or []) + (data.get("web") or [])

    results: list[dict] = []
    seen: set[str] = set()
    for item in raw:
        url = item.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        results.append({
            "title": (item.get("title") or url).strip(),
            "url": url,
            "description": (item.get("description") or item.get("snippet") or "").strip(),
            "source": httpx.URL(url).host or "",
        })

    # Prefer known outlets (Reuters, FT, etc.) over aggregators / social / SEO farms.
    filtered = [r for r in results if reputation_score(r.get("url") or "") >= 0]
    ordered = rank_results(filtered)

    log.info(
        "article.topic_search",
        query=query,
        results=len(ordered[:limit]),
        reputable=sum(
            1 for r in ordered[:limit] if reputation_score(r.get("url") or "") >= 7
        ),
    )
    return ordered[:limit]


async def suggest_angles(
    topic: str, results: list[dict], settings: Settings
) -> list[dict]:
    """Propose 2-4 episode directions from discovery candidates.

    Returns [{"title", "description", "article_indices"}]; empty list on any
    model or parse failure — angles are an enhancement, never a blocker.
    """
    lines = [
        f"{i}. {r.get('title', '')} — {r.get('description') or 'no description'} "
        f"({r.get('source', '')})"
        for i, r in enumerate(results)
    ]
    user_msg = f"TOPIC: {topic}\n\nCANDIDATE ARTICLES:\n" + "\n".join(lines)

    try:
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        resp = await client.messages.create(
            model=settings.claude_model,
            max_tokens=800,
            system=build_angles_prompt(),
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = resp.content[0].text
        start, end = raw.find("["), raw.rfind("]")
        data = json.loads(raw[start : end + 1])
    except Exception as exc:
        log.warning("article.angles_failed", topic=topic, error=str(exc))
        return []

    angles = []
    for item in data if isinstance(data, list) else []:
        indices = [
            i for i in item.get("article_indices", [])
            if isinstance(i, int) and 0 <= i < len(results)
        ]
        title = str(item.get("title", "")).strip()
        if title and indices:
            angles.append({
                "title": title,
                "description": str(item.get("description", "")).strip(),
                "article_indices": indices,
            })
    log.info("article.angles", topic=topic, count=len(angles))
    return angles[:4]


async def _extract_via_readability(url: str) -> dict:
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


async def enrich_article(text: str, settings: Settings) -> dict:
    """Summarize and tag an article for the knowledge base.

    Returns {"summary": str, "topics": list[str], "entities": list[str]}.
    """
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    resp = await client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=build_enrichment_prompt(),
        messages=[{"role": "user", "content": text[:8000]}],
    )
    raw = resp.content[0].text
    enriched = _parse_enrichment(raw)
    log.info(
        "article.enriched",
        topics=enriched["topics"],
        entities=len(enriched["entities"]),
    )
    return enriched


def _parse_enrichment(raw: str) -> dict:
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(raw[start : end + 1])
            return {
                "summary": str(data.get("summary", "")).strip() or raw,
                "topics": [str(t).strip().lower() for t in data.get("topics", []) if str(t).strip()],
                "entities": [str(e).strip() for e in data.get("entities", []) if str(e).strip()],
            }
        except (json.JSONDecodeError, AttributeError):
            pass
    log.warning("article.enrichment_parse_failed")
    return {"summary": raw, "topics": [], "entities": []}
