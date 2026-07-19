from __future__ import annotations

import io
import os

import structlog

from models import AudioProductionConfig, Chapter, ScriptSegment

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


def derive_gaps(
    segments: list[ScriptSegment],
    chapters: list[Chapter],
    cfg: AudioProductionConfig,
) -> list[int]:
    """Silence (ms) BEFORE each segment, from conversational beats.

    Short after interruptions and reactions, slightly longer after a
    question (a beat to think), medium otherwise. First segment of each
    chapter gets 0 — the chapter join supplies gap_chapter_ms.
    """
    medium = cfg.effective_medium_ms()
    gaps = [medium] * len(segments)
    for ch in chapters:
        for j, idx in enumerate(ch.segment_indices):
            if j == 0:
                gaps[idx] = 0
                continue
            seg = segments[idx]
            prev = segments[ch.segment_indices[j - 1]]
            if seg.delivery in ("interrupting", "reaction"):
                gaps[idx] = cfg.gap_short_ms
            elif prev.delivery == "question":
                gaps[idx] = cfg.gap_short_ms + 50
            elif seg.delivery == "transition":
                gaps[idx] = medium + 150
            else:
                gaps[idx] = medium
    return gaps


def _intro_bed(music: bytes, speech_lead_ms: int = 2500) -> "AudioSegment":
    """Turn a music clip into an intro bed: it plays, then fades out over its
    tail so speech can duck in on top. Returns the faded music segment."""
    bed = AudioSegment.from_file(io.BytesIO(music))
    # Fade the last stretch so the theme resolves under the opening line.
    fade_ms = min(len(bed), max(1500, len(bed) - speech_lead_ms))
    return bed.fade_out(fade_ms)


def build_episode_audio(
    chunks: list[bytes],
    chapter_indices: list[list[int]],
    config: AudioProductionConfig | None = None,
    intro_music: bytes | None = None,
    gaps: list[int] | None = None,
) -> dict:
    """Mix TTS chunks into per-chapter audio plus the full episode.

    ``gaps`` is per-segment leading silence in ms (from derive_gaps); when
    omitted, every intra-chapter join falls back to the medium gap.

    Returns {
        "episode": bytes,
        "chapters": [{"audio": bytes, "duration_seconds", "start_seconds"}],
        "segment_durations": [float per chunk],
    }
    The episode is the chapters joined in order, so chapter start offsets are
    exact positions in the episode file. An optional music theme is prepended
    to the first chapter (so walk-mode playback still reproduces the full mix),
    with the opening line ducking in under its fade-out tail.
    """
    if not _HAS_PYDUB:
        raise RuntimeError("pydub/ffmpeg required for audio mixing")

    cfg = config or AudioProductionConfig()
    chapter_silence = AudioSegment.silent(duration=cfg.gap_chapter_ms)

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
                gap_ms = gaps[idx] if gaps else cfg.effective_medium_ms()
                if gap_ms > 0:
                    combined += AudioSegment.silent(duration=gap_ms)
            combined += decoded[idx]
        chapter_audio.append(combined)

    if intro_music and chapter_audio:
        try:
            bed = _intro_bed(intro_music)
            opener = chapter_audio[0]
            lead_ms = min(2500, len(bed))  # first line ducks in this early
            pos = max(0, len(bed) - lead_ms)
            # Pad the music so overlay (which truncates to the base length)
            # has room for the full opening chapter, then lay speech on top.
            total = pos + len(opener)
            padded = bed + AudioSegment.silent(duration=max(0, total - len(bed)))
            chapter_audio[0] = padded.overlay(opener, position=pos)
        except Exception as exc:  # never let a bad theme break the episode
            log.warning("audio.intro_music_failed", error=str(exc))

    episode = AudioSegment.empty()
    for i, ch in enumerate(chapter_audio):
        if i > 0:
            episode += chapter_silence
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
            # Must mirror the chapter join above or the manifest's
            # start_seconds drift from the real episode positions.
            cursor += cfg.gap_chapter_ms / 1000
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
