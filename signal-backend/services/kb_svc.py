from __future__ import annotations

import structlog

from models import Article, EpisodeStatus
from store import Store

log = structlog.get_logger()

_SUMMARY_TRIM = 500


def related_articles(
    articles: list[Article], store: Store, limit: int = 4
) -> list[Article]:
    """Older KB articles related to the given ones, by topic/entity overlap."""
    terms = sorted({t for a in articles for t in (a.topics + a.entities)})
    exclude = {a.id for a in articles}
    if not terms:
        return []
    return store.find_related(terms, exclude_ids=exclude, limit=limit)


def gather_context(
    articles: list[Article],
    store: Store,
    max_related: int = 4,
    max_recent_episodes: int = 3,
) -> str | None:
    """Build the knowledge-base context block injected into script generation.

    Contains summaries of related older articles plus what recent episodes
    covered, so the script can add depth and continuity.
    """
    related = related_articles(articles, store, limit=max_related)

    recent_lines = []
    ready = [e for e in store.list_episodes() if e.status == EpisodeStatus.ready]
    for ep in ready[:max_recent_episodes]:
        titles = []
        for aid in ep.article_ids:
            art = store.get_article(aid)
            if art:
                titles.append(art.title)
        if titles:
            date = ep.created_at.strftime("%b %d")
            recent_lines.append(f"- {date}: {'; '.join(titles)}")

    if not related and not recent_lines:
        return None

    blocks = ["KNOWLEDGE BASE CONTEXT (background only — do not treat as new articles):"]

    if related:
        blocks.append("\nRELATED BACKGROUND ARTICLES:")
        for art in related:
            body = (art.summary or art.text)[:_SUMMARY_TRIM]
            blocks.append(f"- {art.title} ({art.source}): {body}")

    if recent_lines:
        blocks.append("\nPREVIOUSLY COVERED IN RECENT EPISODES:")
        blocks.extend(recent_lines)

    log.info(
        "kb.context",
        related=len(related),
        recent_episodes=len(recent_lines),
    )
    return "\n".join(blocks)
