from __future__ import annotations

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from config import Settings, get_settings
from models import Article, ArticleCreate, DiscoverRequest, DiscoverResult
from services import article_svc, kb_svc
from store import Store

log = structlog.get_logger()

router = APIRouter(prefix="/api", tags=["articles"])


def _get_store(request: Request):
    return request.app.state.store


async def _enrich_in_background(
    article_id: str, text: str, store: Store, settings: Settings
) -> None:
    try:
        enriched = await article_svc.enrich_article(text, settings)
        store.update_article(article_id, **enriched)
        log.info("article.enriched_on_ingest", article_id=article_id)
    except Exception as exc:
        log.warning("article.enrich_failed", article_id=article_id, error=str(exc))


@router.post("/articles", response_model=Article)
async def create_article(
    body: ArticleCreate, request: Request, background_tasks: BackgroundTasks
):
    store = _get_store(request)
    settings = get_settings()

    if body.url:
        extracted = await article_svc.fetch_and_extract(body.url, settings)
        word_count = len(extracted["text"].split())
        if not body.text and word_count < 80:
            raise HTTPException(
                422,
                f"Only {word_count} words extracted — the page is likely paywalled "
                "or JS-rendered. Set FIRECRAWL_API_KEY in .env for stronger "
                "extraction, or paste the text manually.",
            )
        article = Article(
            title=body.title or extracted["title"],
            source=body.source or extracted["source"],
            url=body.url,
            text=body.text or extracted["text"],
            word_count=len((body.text or extracted["text"]).split()),
        )
    elif body.text:
        article = Article(
            title=body.title or "Untitled",
            source=body.source or "manual",
            text=body.text,
            word_count=len(body.text.split()),
        )
    else:
        raise HTTPException(400, "Provide url or text")

    store.add_article(article)
    if settings.anthropic_api_key:
        background_tasks.add_task(
            _enrich_in_background, article.id, article.text, store, settings
        )
    return article


_RECENCY_TBS = {"day": "qdr:d", "week": "qdr:w", "month": "qdr:m"}


@router.post("/discover", response_model=list[DiscoverResult])
async def discover_articles(body: DiscoverRequest, request: Request):
    """Web-search a topic and return candidate articles to queue."""
    settings = get_settings()
    if not settings.firecrawl_api_key:
        raise HTTPException(
            400, "Topic discovery requires FIRECRAWL_API_KEY in .env (firecrawl.dev)"
        )
    try:
        results = await article_svc.search_topic(
            body.topic, settings, limit=body.limit, tbs=_RECENCY_TBS.get(body.recency)
        )
    except Exception as exc:
        raise HTTPException(502, f"Topic search failed: {exc}")

    queued_urls = {a.url for a in _get_store(request).list_articles() if a.url}
    return [
        DiscoverResult(**r, in_queue=r["url"] in queued_urls)
        for r in results
    ]


@router.get("/articles", response_model=list[Article])
async def list_articles(request: Request):
    return _get_store(request).list_articles()


@router.get("/articles/search", response_model=list[Article])
async def search_articles(q: str, request: Request, limit: int = 10):
    return _get_store(request).search_articles(q, limit=limit)


@router.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: str, request: Request):
    article = _get_store(request).get_article(article_id)
    if not article:
        raise HTTPException(404, "Article not found")
    return article


@router.get("/articles/{article_id}/related", response_model=list[Article])
async def related_articles(article_id: str, request: Request, limit: int = 5):
    store = _get_store(request)
    article = store.get_article(article_id)
    if not article:
        raise HTTPException(404, "Article not found")
    return kb_svc.related_articles([article], store, limit=limit)


@router.delete("/articles/{article_id}")
async def delete_article(article_id: str, request: Request):
    if not _get_store(request).delete_article(article_id):
        raise HTTPException(404, "Article not found")
    return {"deleted": True}
