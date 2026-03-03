from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from config import get_settings
from models import Article, ArticleCreate
from services import article_svc

router = APIRouter(prefix="/api", tags=["articles"])


def _get_store(request: Request):
    return request.app.state.store


@router.post("/articles", response_model=Article)
async def create_article(body: ArticleCreate, request: Request):
    store = _get_store(request)
    settings = get_settings()

    if body.url:
        extracted = await article_svc.fetch_and_extract(body.url)
        article = Article(
            title=body.title or extracted["title"],
            source=body.source or extracted["source"],
            url=body.url,
            text=body.text or extracted["text"],
            word_count=len(extracted["text"].split()),
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

    return store.add_article(article)


@router.get("/articles", response_model=list[Article])
async def list_articles(request: Request):
    return _get_store(request).list_articles()


@router.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: str, request: Request):
    article = _get_store(request).get_article(article_id)
    if not article:
        raise HTTPException(404, "Article not found")
    return article


@router.delete("/articles/{article_id}")
async def delete_article(article_id: str, request: Request):
    if not _get_store(request).delete_article(article_id):
        raise HTTPException(404, "Article not found")
    return {"deleted": True}
