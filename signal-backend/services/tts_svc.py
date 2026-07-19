from __future__ import annotations

from typing import Callable

import httpx
import structlog

from config import Settings
from models import ScriptSegment, SpeakerConfig, VoiceSettings
from personas import HOSTS, VOICES, voice_for
from services.script_svc import strip_audio_tags

log = structlog.get_logger()

_API_BASE = "https://api.elevenlabs.io"

# eleven_v3 accepts ~5000 chars per request (v2: 10000). Turns are single
# dialogue lines, far below either — assert so a parser bug fails loudly.
_V3_CHAR_LIMIT = 5000

# v3 stability is modal: Creative (0.0), Natural (0.5), Robust (1.0).
_V3_STABILITY_MODES = (0.0, 0.5, 1.0)


def _is_v3(model_id: str) -> bool:
    return model_id.startswith("eleven_v3")


def snap_v3_stability(value: float) -> float:
    """Snap a continuous stability to the nearest v3 mode."""
    return min(_V3_STABILITY_MODES, key=lambda mode: abs(mode - value))


def build_tts_body(
    text: str, model_id: str, vs: VoiceSettings
) -> dict:
    """Request body for one segment, adapted to the model's capabilities.

    v3: inline audio tags stay in the text; stability snapped to a mode;
    style/speed omitted (v2-only knobs). v2: tags stripped so they're never
    read aloud; full continuous settings.
    """
    if _is_v3(model_id):
        assert len(text) < _V3_CHAR_LIMIT, f"segment too long for v3: {len(text)}"
        return {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": snap_v3_stability(vs.stability),
                "similarity_boost": vs.similarity_boost,
                "use_speaker_boost": vs.use_speaker_boost,
            },
        }
    return {
        "text": strip_audio_tags(text),
        "model_id": model_id,
        "voice_settings": {
            "stability": vs.stability,
            "similarity_boost": vs.similarity_boost,
            "style": vs.style,
            "speed": vs.speed,
            "use_speaker_boost": vs.use_speaker_boost,
        },
    }


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
    body = build_tts_body(text, settings.elevenlabs_model, vs)

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=body, headers=headers)
        if (
            resp.status_code == 400
            and _is_v3(settings.elevenlabs_model)
            and body["voice_settings"]["stability"] != 0.5
        ):
            # Some v3 deployments reject non-Natural modes — retry once.
            log.warning(
                "tts.v3_stability_rejected",
                stability=body["voice_settings"]["stability"],
            )
            body["voice_settings"]["stability"] = 0.5
            resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        return resp.content


async def synthesize_script(
    segments: list[ScriptSegment],
    voice_mapping: dict[str, str] | None,
    voice_config: dict[str, SpeakerConfig] | None,
    settings: Settings,
    on_segment: Callable[[int, str, str], None] | None = None,
) -> list[bytes]:
    audio_chunks: list[bytes] = []
    for i, seg in enumerate(segments):
        if on_segment:
            on_segment(i, seg.speaker, seg.text)
        # Priority: voice_config > voice_mapping > host persona defaults
        if voice_config and seg.speaker in voice_config:
            config = voice_config[seg.speaker]
            voice_id = config.voice_id
            base_settings = config.settings
        elif voice_mapping and seg.speaker in voice_mapping:
            voice_id = voice_mapping[seg.speaker]
            base_settings = None
        else:
            voice_id, base_settings = voice_for(seg.speaker)

        voice_settings = base_settings or VoiceSettings()
        log.info(
            "tts.segment",
            index=i,
            speaker=seg.speaker,
            delivery=seg.delivery,
            chars=seg.char_count,
            stability=voice_settings.stability,
        )
        chunk = await synthesize_segment(seg.text, voice_id, settings, voice_settings)
        audio_chunks.append(chunk)

    return audio_chunks


def get_voices_info() -> dict:
    """Return available voices and the hosts' default voice assignments."""
    host_map = {key: p.voice_id for key, p in HOSTS.items()}
    return {
        "voices": [{"id": vid, "name": name} for name, vid in VOICES.items()],
        "hosts": {
            key: {"name": p.name, "role": p.role, "voice_id": p.voice_id}
            for key, p in HOSTS.items()
        },
        # Legacy shape: clients expecting {tone: {SPEAKER: voice_id}} get the
        # same host map under every key they might look up.
        "defaults": {tone: host_map for tone in ("casual", "polished", "debate", "technical")},
        "settings_ranges": {
            "stability": {"min": 0.0, "max": 1.0, "default": 0.4},
            "similarity_boost": {"min": 0.0, "max": 1.0, "default": 0.75},
            "style": {"min": 0.0, "max": 1.0, "default": 0.5},
            "speed": {"min": 0.7, "max": 1.2, "default": 1.0},
        },
    }
