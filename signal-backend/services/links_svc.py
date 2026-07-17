from __future__ import annotations

import asyncio
import re

import structlog

from config import Settings
from models import Article, EpisodeLink, EpisodeScript
from services import article_svc
from services.source_quality import (
    PREFERRED_SITE_QUERY,
    host_from_url,
    is_reputable,
    rank_results,
    reputation_score,
)

log = structlog.get_logger()

_MAX_CONTEXT_SEARCHES = 3
_MIN_ACCEPT_SCORE = 1
_SEARCH_TIMEOUT_S = 12.0


def seed_source_links(articles: list[Article]) -> list[EpisodeLink]:
    """Queued article URLs only — available the moment the episode is ready."""
    links: list[EpisodeLink] = []
    used: set[str] = set()
    for art in articles:
        if art.url and art.url not in used:
            used.add(art.url)
            links.append(
                EpisodeLink(
                    label=art.source or "Source",
                    title=art.title,
                    url=art.url,
                    source=host_from_url(art.url) or (art.source or ""),
                    snippet=(art.summary or "")[:220],
                    kind="source",
                )
            )
    return links


def _pick_entities(articles: list[Article], script: EpisodeScript | None) -> list[str]:
    """Entities that actually show up in the spoken script, ranked by frequency."""
    script_text = ""
    if script:
        script_text = " ".join(s.text for s in script.segments).lower()
    counts: dict[str, int] = {}
    for art in articles:
        for ent in art.entities or []:
            e = ent.strip()
            if len(e) < 2:
                continue
            hits = script_text.count(e.lower()) if script_text else 1
            if script_text and hits == 0:
                continue
            counts[e] = counts.get(e, 0) + hits + 1
    ranked = sorted(counts.keys(), key=lambda k: (-counts[k], -len(k)))
    return ranked[:_MAX_CONTEXT_SEARCHES]


def _context_terms(articles: list[Article], title: str | None, focus: str | None) -> str:
    bits: list[str] = []
    if focus:
        bits.append(focus[:80])
    elif title:
        bits.append(title)
    topics = []
    for a in articles:
        topics.extend(a.topics or [])
    seen: set[str] = set()
    for t in topics:
        tl = t.lower().strip()
        if tl and tl not in seen:
            seen.add(tl)
            bits.append(t)
        if len(seen) >= 2:
            break
    return " ".join(bits)[:120]


def _pick_from_results(
    results: list[dict],
    label: str,
    used_urls: set[str],
    *,
    require_reputable: bool,
) -> EpisodeLink | None:
    for item in rank_results(results, label):
        url = item.get("url") or ""
        if not url or url in used_urls:
            continue
        score = reputation_score(url)
        if score < _MIN_ACCEPT_SCORE:
            continue
        if require_reputable and not is_reputable(url):
            continue
        used_urls.add(url)
        return EpisodeLink(
            label=label,
            title=(item.get("title") or label).strip(),
            url=url,
            source=item.get("source") or host_from_url(url),
            snippet=(item.get("description") or "")[:220],
            kind="context",
        )
    return None


async def _search_topic_bounded(query: str, settings: Settings, limit: int) -> list[dict]:
    try:
        return await asyncio.wait_for(
            article_svc.search_topic(query, settings, limit=limit),
            timeout=_SEARCH_TIMEOUT_S,
        )
    except Exception as exc:
        log.warning("links.search_failed", query=query[:80], error=str(exc))
        return []


async def _search_one(
    label: str,
    context: str,
    settings: Settings,
    used_urls: set[str],
) -> EpisodeLink | None:
    """Find one contextual link, preferring reputable news/analysis outlets."""
    base = f"{label} {context}".strip()
    news = await _search_topic_bounded(base, settings, limit=8)

    link = _pick_from_results(news, label, used_urls, require_reputable=True)
    if link:
        return link

    # One bounded fallback toward preferred outlets — skip if first pass was empty.
    if news:
        preferred = await _search_topic_bounded(
            f"{label} ({PREFERRED_SITE_QUERY})",
            settings,
            limit=6,
        )
        link = _pick_from_results(preferred, label, used_urls, require_reputable=True)
        if link:
            return link

    link = _pick_from_results(news, label, used_urls, require_reputable=False)
    if link:
        log.info("links.fallback_non_tier", label=label, url=link.url)
    return link


async def curate_links(
    articles: list[Article],
    script: EpisodeScript | None,
    title: str | None,
    focus: str | None,
    settings: Settings,
) -> list[EpisodeLink]:
    """Build a reading list: source articles + contextual web results per entity."""
    links = seed_source_links(articles)
    used_urls = {l.url for l in links}

    if not settings.firecrawl_api_key:
        log.info("links.skip_search", reason="no_firecrawl_key")
        return links

    entities = _pick_entities(articles, script)
    context = _context_terms(articles, title, focus)
    if not entities and script:
        blob = " ".join(s.text for s in script.segments)
        proper = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b", blob)
        skip = {"The", "This", "That", "And", "But", "For", "With", "From"}
        entities = [p for p in dict.fromkeys(proper) if p not in skip][:3]

    # Sequential — keeps used_urls consistent; each search is time-bounded.
    for label in entities:
        link = await _search_one(label, context, settings, used_urls)
        if link:
            links.append(link)

    log.info(
        "links.curated",
        sources=sum(1 for l in links if l.kind == "source"),
        context=sum(1 for l in links if l.kind == "context"),
        reputable_context=sum(
            1 for l in links if l.kind == "context" and is_reputable(l.url)
        ),
    )
    return links
