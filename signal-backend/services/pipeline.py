from __future__ import annotations

import time
from datetime import datetime, timezone

import structlog

from config import Settings
from models import (
    Article,
    AudioProductionConfig,
    Episode,
    EpisodeScript,
    EpisodeStatus,
    PipelineMetrics,
    SpeakerConfig,
    StyleConfig,
)
from services import article_svc, audio_svc, kb_svc, script_svc, tts_svc
from store import Store

log = structlog.get_logger()


def _ms_since(start: float) -> float:
    return round((time.time() - start) * 1000, 1)


async def run_pipeline(
    episode_id: str,
    articles: list[Article],
    style: StyleConfig,
    focus: str | None,
    voice_mapping: dict[str, str] | None,
    voice_config: dict[str, SpeakerConfig] | None,
    audio_config: AudioProductionConfig,
    target_minutes: int,
    store: Store,
    settings: Settings,
) -> Episode:
    metrics = PipelineMetrics()
    pipeline_start = time.time()

    try:
        # 1. Enrich (summary + topics + entities) any articles not yet processed
        store.update_status(episode_id, EpisodeStatus.summarizing)
        t0 = time.time()
        for art in articles:
            if not art.summary:
                enriched = await article_svc.enrich_article(art.text, settings)
                art.summary = enriched["summary"]
                art.topics = enriched["topics"]
                art.entities = enriched["entities"]
                store.update_article(art.id, **enriched)
                log.info("pipeline.enriched", article_id=art.id)
        metrics.summarize_time_ms = _ms_since(t0)

        # 2. Script, with knowledge-base background for depth and continuity
        store.update_status(episode_id, EpisodeStatus.scripting)
        t0 = time.time()
        kb_context = kb_svc.gather_context(articles, store)
        script_text, token_info = await script_svc.generate_script(
            articles, style, target_minutes, settings,
            kb_context=kb_context, focus=focus,
        )
        title, script_text = script_svc.extract_title(script_text)
        if not title and articles:
            title = articles[0].title
        segments, chapters = script_svc.parse_script(script_text)
        metrics.script_time_ms = _ms_since(t0)
        metrics.script_tokens_in = token_info["input_tokens"]
        metrics.script_tokens_out = token_info["output_tokens"]

        word_count = sum(len(s.text.split()) for s in segments)
        episode_script = EpisodeScript(
            raw_text=script_text,
            segments=segments,
            chapters=chapters,
            word_count=word_count,
            estimated_minutes=round(word_count / 150, 1),
        )
        store.update_episode(episode_id, title=title, script=episode_script, metrics=metrics)
        log.info(
            "pipeline.scripted",
            title=title,
            words=word_count,
            segments=len(segments),
            chapters=len(chapters),
        )

        # 3. TTS
        store.update_status(episode_id, EpisodeStatus.synthesizing)
        t0 = time.time()
        audio_chunks = await tts_svc.synthesize_script(
            segments, voice_mapping, voice_config, style.tone.value, settings
        )
        metrics.tts_time_ms = _ms_since(t0)
        metrics.tts_characters = sum(s.char_count for s in segments)

        # 4. Mix — full episode plus one file per chapter for adaptive playback
        store.update_status(episode_id, EpisodeStatus.mixing)
        t0 = time.time()
        mix = audio_svc.build_episode_audio(
            audio_chunks, [c.segment_indices for c in chapters], audio_config
        )
        metrics.mix_time_ms = _ms_since(t0)

        # 5. Save & finish
        for seg, dur in zip(segments, mix["segment_durations"]):
            seg.duration_seconds = dur
        for i, (chapter, built) in enumerate(zip(chapters, mix["chapters"])):
            chapter.duration_seconds = built["duration_seconds"]
            chapter.start_seconds = built["start_seconds"]
            chapter.audio_url = audio_svc.save_chapter_audio(
                episode_id, i, built["audio"], settings.storage_path
            )
        final_audio = mix["episode"]
        audio_url = audio_svc.save_audio(episode_id, final_audio, settings.storage_path)
        duration = audio_svc.get_duration(final_audio)

        metrics.total_time_ms = _ms_since(pipeline_start)
        # Opus-tier pricing ($5/$25 per MTok) + ElevenLabs characters
        metrics.estimated_cost_usd = round(
            (metrics.script_tokens_in * 0.005 / 1000)
            + (metrics.script_tokens_out * 0.025 / 1000)
            + (metrics.tts_characters * 0.030 / 1000),
            4,
        )

        episode = store.update_episode(
            episode_id,
            status=EpisodeStatus.ready,
            script=episode_script,  # now carries measured durations + chapter URLs
            audio_url=audio_url,
            audio_duration_seconds=round(duration, 1),
            metrics=metrics,
            completed_at=datetime.now(timezone.utc),
        )
        log.info(
            "pipeline.complete",
            episode_id=episode_id,
            duration_s=round(duration, 1),
            cost_usd=metrics.estimated_cost_usd,
            total_ms=metrics.total_time_ms,
        )
        return episode

    except Exception as exc:
        metrics.total_time_ms = _ms_since(pipeline_start)
        store.update_episode(
            episode_id,
            status=EpisodeStatus.failed,
            error=str(exc),
            metrics=metrics,
        )
        log.error("pipeline.failed", episode_id=episode_id, error=str(exc))
        raise
