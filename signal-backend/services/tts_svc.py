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
    "polished": {"ANCHOR": VOICES["josh"], "ANALYST": VOICES["sarah"]},
    "debate": {"BULL": VOICES["drew"], "BEAR": VOICES["sam"]},
    "technical": {"LEAD": VOICES["adam"], "PEER": VOICES["antoni"]},
}

_API_BASE = "https://api.elevenlabs.io"

# Per-line delivery nudges applied on top of the speaker's base VoiceSettings.
# Animated/reactive lines: lower stability + higher style. Flat/deadpan: opposite.
_DELIVERY_DELTAS: dict[str, dict[str, float]] = {
    "neutral": {},
    "warm": {"stability": -0.05, "style": 0.05},
    "amused": {"stability": -0.15, "style": 0.2},
    "deadpan": {"stability": 0.2, "style": -0.2},
    "pointed": {"stability": -0.1, "style": 0.15},
    "interrupting": {"stability": -0.2, "style": 0.25, "speed": 0.05},
    "skeptical": {"stability": -0.1, "style": 0.1},
    "excited": {"stability": -0.2, "style": 0.25, "speed": 0.08},
}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def apply_delivery(
    base: VoiceSettings | None,
    delivery: str | None,
) -> VoiceSettings:
    """Nudge base voice settings from a segment delivery tag."""
    vs = (base or VoiceSettings()).model_copy()
    if not delivery:
        return vs
    deltas = _DELIVERY_DELTAS.get(delivery.lower())
    if not deltas:
        return vs
    vs.stability = _clamp(vs.stability + deltas.get("stability", 0.0), 0.0, 1.0)
    vs.style = _clamp(vs.style + deltas.get("style", 0.0), 0.0, 1.0)
    vs.similarity_boost = _clamp(
        vs.similarity_boost + deltas.get("similarity_boost", 0.0), 0.0, 1.0
    )
    vs.speed = _clamp(vs.speed + deltas.get("speed", 0.0), 0.7, 1.2)
    return vs


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
    on_segment: Callable[[int, str, str], None] | None = None,
) -> list[bytes]:
    defaults = DEFAULT_VOICE_MAP.get(tone, DEFAULT_VOICE_MAP["casual"])

    audio_chunks: list[bytes] = []
    for i, seg in enumerate(segments):
        if on_segment:
            on_segment(i, seg.speaker, seg.text)
        # Priority: voice_config > voice_mapping > defaults
        if voice_config and seg.speaker in voice_config:
            config = voice_config[seg.speaker]
            voice_id = config.voice_id
            base_settings = config.settings
        elif voice_mapping and seg.speaker in voice_mapping:
            voice_id = voice_mapping[seg.speaker]
            base_settings = None
        else:
            voice_id = defaults.get(seg.speaker, list(defaults.values())[0])
            base_settings = None

        voice_settings = apply_delivery(base_settings, seg.delivery)
        log.info(
            "tts.segment",
            index=i,
            speaker=seg.speaker,
            delivery=seg.delivery,
            chars=seg.char_count,
            stability=voice_settings.stability,
            style=voice_settings.style,
            speed=voice_settings.speed,
        )
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
