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


def _export_mp3(seg: "AudioSegment") -> bytes:
    buf = io.BytesIO()
    seg.export(buf, format="mp3", bitrate="192k")
    return buf.getvalue()


def build_episode_audio(
    chunks: list[bytes],
    chapter_indices: list[list[int]],
    config: AudioProductionConfig | None = None,
) -> dict:
    """Mix TTS chunks into per-chapter audio plus the full episode.

    Returns {
        "episode": bytes,
        "chapters": [{"audio": bytes, "duration_seconds", "start_seconds"}],
        "segment_durations": [float per chunk],
    }
    The episode is the chapters joined in order, so chapter start offsets are
    exact positions in the episode file.
    """
    if not _HAS_PYDUB:
        raise RuntimeError("pydub/ffmpeg required for audio mixing")

    cfg = config or AudioProductionConfig()
    silence = AudioSegment.silent(duration=cfg.silence_duration_ms)

    decoded = []
    for raw in chunks:
        seg = AudioSegment.from_mp3(io.BytesIO(raw))
        if cfg.fade_in_ms > 0:
            seg = seg.fade_in(cfg.fade_in_ms)
        if cfg.fade_out_ms > 0:
            seg = seg.fade_out(cfg.fade_out_ms)
        decoded.append(seg)

    chapter_audio = []
    for indices in chapter_indices:
        combined = AudioSegment.empty()
        for j, idx in enumerate(indices):
            if j > 0:
                combined += silence
            combined += decoded[idx]
        chapter_audio.append(combined)

    episode = AudioSegment.empty()
    for i, ch in enumerate(chapter_audio):
        if i > 0:
            episode += silence
        episode += ch

    # Apply the same gain to episode and chapters so adaptive playback
    # matches the full-episode mix in loudness.
    if cfg.normalize and len(episode) > 0:
        gain = cfg.target_dbfs - episode.dBFS
        episode = episode.apply_gain(gain)
        chapter_audio = [ch.apply_gain(gain) for ch in chapter_audio]
        log.info("audio.normalized", target_dbfs=cfg.target_dbfs, gain_applied=round(gain, 2))

    chapters = []
    cursor = 0.0
    for i, ch in enumerate(chapter_audio):
        if i > 0:
            cursor += cfg.silence_duration_ms / 1000
        chapters.append({
            "audio": _export_mp3(ch),
            "duration_seconds": round(ch.duration_seconds, 2),
            "start_seconds": round(cursor, 2),
        })
        cursor += ch.duration_seconds

    return {
        "episode": _export_mp3(episode),
        "chapters": chapters,
        "segment_durations": [round(d.duration_seconds, 2) for d in decoded],
    }


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


def save_chapter_audio(
    episode_id: str, index: int, audio_bytes: bytes, storage_path: str
) -> str:
    out_dir = os.path.join(storage_path, "episodes", episode_id, "chapters")
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{index:02d}.mp3"
    with open(os.path.join(out_dir, filename), "wb") as f:
        f.write(audio_bytes)
    return f"/data/episodes/{episode_id}/chapters/{filename}"
