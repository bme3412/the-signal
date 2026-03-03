from __future__ import annotations

import io
import os

import structlog

from models import AudioProductionConfig

log = structlog.get_logger()

try:
    from pydub import AudioSegment
    _HAS_PYDUB = True
except ImportError:
    _HAS_PYDUB = False
    log.warning("pydub not available — audio mixing disabled")


def concatenate_segments(
    chunks: list[bytes],
    config: AudioProductionConfig | None = None,
) -> bytes:
    if not _HAS_PYDUB:
        raise RuntimeError("pydub/ffmpeg required for audio mixing")

    cfg = config or AudioProductionConfig()
    silence = AudioSegment.silent(duration=cfg.silence_duration_ms)
    combined = AudioSegment.empty()

    for i, raw in enumerate(chunks):
        seg = AudioSegment.from_mp3(io.BytesIO(raw))

        # Apply fade in/out to each segment
        if cfg.fade_in_ms > 0:
            seg = seg.fade_in(cfg.fade_in_ms)
        if cfg.fade_out_ms > 0:
            seg = seg.fade_out(cfg.fade_out_ms)

        if i > 0:
            combined += silence
        combined += seg

    # Normalize volume if requested
    if cfg.normalize and len(combined) > 0:
        change_in_dbfs = cfg.target_dbfs - combined.dBFS
        combined = combined.apply_gain(change_in_dbfs)
        log.info("audio.normalized", target_dbfs=cfg.target_dbfs, gain_applied=round(change_in_dbfs, 2))

    buf = io.BytesIO()
    combined.export(buf, format="mp3", bitrate="192k")
    return buf.getvalue()


def get_duration(audio_bytes: bytes) -> float:
    if not _HAS_PYDUB:
        return 0.0
    seg = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
    return seg.duration_seconds


def save_audio(episode_id: str, audio_bytes: bytes, storage_path: str) -> str:
    out_dir = os.path.join(storage_path, "episodes")
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{episode_id}.mp3"
    filepath = os.path.join(out_dir, filename)
    with open(filepath, "wb") as f:
        f.write(audio_bytes)
    log.info("audio.saved", path=filepath, size_mb=round(len(audio_bytes) / 1_048_576, 2))
    return f"/data/episodes/{filename}"
