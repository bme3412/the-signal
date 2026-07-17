from __future__ import annotations

import re
from urllib.parse import urlparse

import structlog

from config import Settings
from models import Article, EpisodeLink, EpisodeScript
from services import article_svc

log = structlog.get_logger()

_MAX_CONTEXT_SEARCHES = 4
_SKIP_HOSTS = (
    "pinterest.",
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
)


def _host(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def _score_result(item: dict, label: str) -> int:
    title = (item.get("title") or "").lower()
    desc = (item.get("description") or "").lower()
    url = (item.get("url") or "").lower()
    lab = label.lower()
    score = 0
    if lab in title:
        score += 4
    if lab in desc:
        score += 2
    if any(bad in url for bad in ("wikipedia.org", "wiki/")):
        score -= 2  # prefer primary reporting over encyclopedia stubs
    if any(skip in url for skip in _SKIP_HOSTS):
        score -= 5
    if item.get("source") and "news" in (item.get("source") or "").lower():
        score += 1
    return score


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
            # Prefer entities the hosts actually say.
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
    # Dedupe topics, keep a couple for query grounding.
    seen: set[str] = set()
    for t in topics:
        tl = t.lower().strip()
        if tl and tl not in seen:
            seen.add(tl)
            bits.append(t)
        if len(seen) >= 2:
            break
    return " ".join(bits)[:120]


async def _search_one(
    label: str,
    context: str,
    settings: Settings,
    used_urls: set[str],
) -> EpisodeLink | None:
    query = f"{label} {context}".strip()
    try:
        results = await article_svc.search_topic(query, settings, limit=5)
    except Exception as exc:
        log.warning("links.search_failed", label=label, error=str(exc))
        return None

    ranked = sorted(results, key=lambda r: _score_result(r, label), reverse=True)
    for item in ranked:
        url = item.get("url") or ""
        if not url or url in used_urls:
            continue
        if _score_result(item, label) < 0:
            continue
        used_urls.add(url)
        return EpisodeLink(
            label=label,
            title=(item.get("title") or label).strip(),
            url=url,
            source=item.get("source") or _host(url),
            snippet=(item.get("description") or "")[:220],
            kind="context",
        )
    return None


async def curate_links(
    articles: list[Article],
    script: EpisodeScript | None,
    title: str | None,
    focus: str | None,
    settings: Settings,
) -> list[EpisodeLink]:
    """Build a reading list: source articles + contextual web results per entity."""
    links: list[EpisodeLink] = []
    used_urls: set[str] = set()

    for art in articles:
        if art.url and art.url not in used_urls:
            used_urls.add(art.url)
            links.append(
                EpisodeLink(
                    label=art.source or "Source",
                    title=art.title,
                    url=art.url,
                    source=_host(art.url) or (art.source or ""),
                    snippet=(art.summary or "")[:220],
                    kind="source",
                )
            )

    if not settings.firecrawl_api_key:
        log.info("links.skip_search", reason="no_firecrawl_key")
        return links

    entities = _pick_entities(articles, script)
    context = _context_terms(articles, title, focus)
    if not entities:
        # Fall back to a couple of distinctive proper nouns from the script.
        if script:
            blob = " ".join(s.text for s in script.segments)
            proper = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b", blob)
            # Filter commons
            skip = {"The", "This", "That", "And", "But", "For", "With", "From"}
            entities = [p for p in dict.fromkeys(proper) if p not in skip][:3]

    # Sequential so used_urls stays consistent and we don't stampede Firecrawl.
    for label in entities:
        link = await _search_one(label, context, settings, used_urls)
        if link:
            links.append(link)

    log.info(
        "links.curated",
        sources=sum(1 for l in links if l.kind == "source"),
        context=sum(1 for l in links if l.kind == "context"),
    )
    return links
