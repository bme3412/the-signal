from __future__ import annotations

from typing import Callable

import httpx
import structlog

from config import Settings
from models import ScriptSegment, SpeakerConfig, VoiceSettings

log = structlog.get_logger()

VOICES: dict[str, str] = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "drew": "29vD33N1CtxCmqQRPOHJ",
    "sarah": "EXAVITQu4vr4xnSDxMaL",
    "antoni": "ErXwobaYiN019PkySvjV",
    "josh": "TxGEqnHWrfWFTfGW9XjX",
    "arnold": "VR6AewLTigWG4xSOukaG",
    "adam": "pNInz6obpgDQGcFmaJgB",
    "sam": "yoZ06aMxZJJ28mfd3POQ",
    "gigi": "jBpfuIE2acCO8z3wKNLl",
}

DEFAULT_VOICE_MAP: dict[str, dict[str, str]] = {
    "casual": {"ALEX": VOICES["antoni"], "JAMIE": VOICES["rachel"]},
    "polished": {"HOST": VOICES["josh"]},
    "debate": {"BULL": VOICES["drew"], "BEAR": VOICES["sam"]},
    "technical": {"HOST": VOICES["adam"]},
}

_API_BASE = "https://api.elevenlabs.io"


async def synthesize_segment(
    text: str,
    voice_id: str,
    settings: Settings,
    voice_settings: VoiceSettings | None = None,
) -> bytes:
    vs = voice_settings or VoiceSettings()
    url = f"{_API_BASE}/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
    }
    body = {
        "text": text,
        "model_id": settings.elevenlabs_model,
        "voice_settings": {
            "stability": vs.stability,
            "similarity_boost": vs.similarity_boost,
            "style": vs.style,
            "speed": vs.speed,
            "use_speaker_boost": vs.use_speaker_boost,
        },
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        return resp.content


async def synthesize_script(
    segments: list[ScriptSegment],
    voice_mapping: dict[str, str] | None,
    voice_config: dict[str, SpeakerConfig] | None,
    tone: str,
    settings: Settings,
    on_segment: Callable[[int, str], None] | None = None,
) -> list[bytes]:
    defaults = DEFAULT_VOICE_MAP.get(tone, DEFAULT_VOICE_MAP["casual"])

    audio_chunks: list[bytes] = []
    for i, seg in enumerate(segments):
        if on_segment:
            on_segment(i, seg.speaker)
        # Priority: voice_config > voice_mapping > defaults
        if voice_config and seg.speaker in voice_config:
            config = voice_config[seg.speaker]
            voice_id = config.voice_id
            voice_settings = config.settings
        elif voice_mapping and seg.speaker in voice_mapping:
            voice_id = voice_mapping[seg.speaker]
            voice_settings = None
        else:
            voice_id = defaults.get(seg.speaker, list(defaults.values())[0])
            voice_settings = None

        log.info("tts.segment", index=i, speaker=seg.speaker, chars=seg.char_count)
        chunk = await synthesize_segment(seg.text, voice_id, settings, voice_settings)
        audio_chunks.append(chunk)

    return audio_chunks


def get_voices_info() -> dict:
    """Return available voices and default mappings for the API."""
    return {
        "voices": [{"id": vid, "name": name} for name, vid in VOICES.items()],
        "defaults": DEFAULT_VOICE_MAP,
        "settings_ranges": {
            "stability": {"min": 0.0, "max": 1.0, "default": 0.4},
            "similarity_boost": {"min": 0.0, "max": 1.0, "default": 0.75},
            "style": {"min": 0.0, "max": 1.0, "default": 0.5},
            "speed": {"min": 0.7, "max": 1.2, "default": 1.0},
        },
    }
