from __future__ import annotations

import os

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse

from config import get_settings
from models import (
    Episode,
    EpisodeManifest,
    EpisodeRequest,
    EpisodeScript,
    EpisodeStatus,
    ManifestChapter,
)
from services.pipeline import run_pipeline
from services.tts_svc import get_voices_info

router = APIRouter(prefix="/api", tags=["episodes"])


@router.get("/episodes/voices")
async def list_voices():
    """Return available voices and default mappings."""
    return get_voices_info()


def _get_store(request: Request):
    return request.app.state.store


@router.post("/episodes/generate", response_model=Episode)
async def generate_episode(
    body: EpisodeRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    store = _get_store(request)
    settings = get_settings()

    articles = []
    for aid in body.article_ids:
        art = store.get_article(aid)
        if not art:
            raise HTTPException(404, f"Article {aid} not found")
        articles.append(art)

    episode = Episode(
        article_ids=body.article_ids,
        style=body.style,
        focus=body.focus,
        status=EpisodeStatus.queued,
    )
    store.create_episode(episode)

    background_tasks.add_task(
        run_pipeline,
        episode_id=episode.id,
        articles=articles,
        style=body.style,
        focus=body.focus,
        voice_mapping=body.voice_mapping,
        voice_config=body.voice_config,
        audio_config=body.audio_config,
        target_minutes=body.target_minutes,
        store=store,
        settings=settings,
    )

    return episode


@router.get("/episodes", response_model=list[Episode])
async def list_episodes(request: Request):
    return _get_store(request).list_episodes()


@router.get("/episodes/{episode_id}", response_model=Episode)
async def get_episode(episode_id: str, request: Request):
    episode = _get_store(request).get_episode(episode_id)
    if not episode:
        raise HTTPException(404, "Episode not found")
    return episode


@router.get("/episodes/{episode_id}/script", response_model=EpisodeScript)
async def get_episode_script(episode_id: str, request: Request):
    episode = _get_store(request).get_episode(episode_id)
    if not episode:
        raise HTTPException(404, "Episode not found")
    if not episode.script:
        raise HTTPException(404, "Script not yet available")
    return episode.script


@router.get("/episodes/{episode_id}/manifest", response_model=EpisodeManifest)
async def get_episode_manifest(episode_id: str, request: Request):
    """Per-chapter audio map for adaptive playback."""
    episode = _get_store(request).get_episode(episode_id)
    if not episode:
        raise HTTPException(404, "Episode not found")
    script = episode.script
    if episode.status != EpisodeStatus.ready or not script or not script.chapters:
        raise HTTPException(404, "Manifest not yet available")

    chapters = [
        ManifestChapter(
            index=i,
            title=ch.title,
            role=ch.role,
            audio_url=ch.audio_url,
            duration_seconds=ch.duration_seconds,
            start_seconds=ch.start_seconds,
            segments=[script.segments[j] for j in ch.segment_indices],
        )
        for i, ch in enumerate(script.chapters)
    ]
    return EpisodeManifest(
        episode_id=episode.id,
        title=episode.title,
        status=episode.status,
        total_duration_seconds=episode.audio_duration_seconds or 0.0,
        chapters=chapters,
    )


@router.get("/episodes/{episode_id}/audio")
async def get_episode_audio(episode_id: str, request: Request):
    episode = _get_store(request).get_episode(episode_id)
    if not episode:
        raise HTTPException(404, "Episode not found")

    settings = get_settings()
    filepath = os.path.join(settings.storage_path, "episodes", f"{episode_id}.mp3")
    if not os.path.exists(filepath):
        raise HTTPException(404, "Audio not yet available")

    return FileResponse(filepath, media_type="audio/mpeg", filename=f"{episode_id}.mp3")
