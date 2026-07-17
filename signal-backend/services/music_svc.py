from __future__ import annotations

import os

import httpx
import structlog

from config import Settings

log = structlog.get_logger()

_API_BASE = "https://api.elevenlabs.io"
_THEME_PROMPT = (
    "A short, warm podcast intro sting for a news and analysis show. Modern, "
    "confident, and clean — a few bars of understated electronic keys with a "
    "light rhythmic pulse that resolves cleanly. No vocals."
)
_THEME_LENGTH_MS = 8000


async def get_theme(settings: Settings) -> bytes | None:
    """Return the podcast intro theme, generating and caching it on first use.

    A user-supplied `data/theme.mp3` always takes precedence. Otherwise the
    theme is generated once via the ElevenLabs Music API and cached to
    `data/theme_generated.mp3` so every episode reuses the same sting.
    Returns None if no theme is available (e.g. no API key).
    """
    custom = os.path.join(settings.storage_path, "theme.mp3")
    if os.path.exists(custom):
        with open(custom, "rb") as f:
            return f.read()

    cached = os.path.join(settings.storage_path, "theme_generated.mp3")
    if os.path.exists(cached):
        with open(cached, "rb") as f:
            return f.read()

    if not settings.elevenlabs_api_key:
        return None

    try:
        audio = await _generate_theme(settings)
    except Exception as exc:
        log.warning("music.theme_generation_failed", error=str(exc))
        return None

    os.makedirs(settings.storage_path, exist_ok=True)
    with open(cached, "wb") as f:
        f.write(audio)
    log.info("music.theme_generated", bytes=len(audio))
    return audio


async def _generate_theme(settings: Settings) -> bytes:
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(
            f"{_API_BASE}/v1/music",
            headers={"xi-api-key": settings.elevenlabs_api_key},
            json={
                "prompt": _THEME_PROMPT,
                "music_length_ms": _THEME_LENGTH_MS,
                "model_id": "music_v1",
                "force_instrumental": True,
            },
        )
        resp.raise_for_status()
        return resp.content
