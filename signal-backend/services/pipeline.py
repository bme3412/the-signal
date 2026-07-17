from __future__ import annotations

import re
import time
from collections.abc import Sequence
from datetime import datetime, timezone

import structlog

from config import Settings
from models import (
    Article,
    AudioProductionConfig,
    Chapter,
    Episode,
    EpisodeScript,
    EpisodeStatus,
    PipelineMetrics,
    SpeakerConfig,
    StyleConfig,
)
from services import article_svc, audio_svc, kb_svc, links_svc, music_svc, script_svc, tts_svc
from store import Store

log = structlog.get_logger()

_SHORT_TITLE = 48
_TEASER_LEN = 100

def _ms_since(start: float) -> float:
    return round((time.time() - start) * 1000, 1)


def _short_title(title: str) -> str:
    t = title.strip()
    if len(t) <= _SHORT_TITLE:
        return t
    return t[: _SHORT_TITLE - 1].rstrip() + "…"


def _word_set(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2}


def _too_similar(a: str, b: str, threshold: float = 0.32) -> bool:
    wa, wb = _word_set(a), _word_set(b)
    if not wa or not wb:
        return False
    if len(wa & wb) / len(wa | wb) >= threshold:
        return True
    # Same standout figure (e.g. 2.8 trillion) ⇒ same beat, skip.
    nums_a = set(re.findall(r"\d+(?:\.\d+)?", a))
    nums_b = set(re.findall(r"\d+(?:\.\d+)?", b))
    shared_nums = {n for n in (nums_a & nums_b) if len(n) >= 2 or "." in n}
    return bool(shared_nums)


def _teaser(article: Article, avoid: Sequence[str] = ()) -> str | None:
    """Pull a short hook — prefer numbers, skip near-duplicates of prior hooks."""
    source = (article.summary or article.text or "").strip()
    if not source:
        return None
    sentences = re.split(r"(?<=[.!?])\s+", source)
    ranked = sorted(
        sentences,
        key=lambda s: (1 if re.search(r"\d", s) else 0, -abs(len(s) - 90)),
        reverse=True,
    )
    for s in ranked:
        clean = s.strip().strip('"')
        if not (36 <= len(clean) <= 200):
            continue
        if any(_too_similar(clean, prev) for prev in avoid):
            continue
        if len(clean) > _TEASER_LEN:
            return clean[: _TEASER_LEN - 1].rstrip() + "…"
        return clean
    return None


def _distinct_hooks(articles: list[Article], limit: int = 2) -> list[str]:
    hooks: list[str] = []
    for art in articles:
        h = _teaser(art, avoid=hooks)
        if h:
            hooks.append(h)
        if len(hooks) >= limit:
            break
    return hooks


_CHAPTER_LABELS = {
    "intro": "Cold open",
    "core": "Chapter",
    "optional": "Bonus",
    "closer": "Closer",
}


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

    def narrate(stage: EpisodeStatus, message: str) -> None:
        store.add_progress(episode_id, stage, message)

    try:
        # 1. Enrich — keep the feed light; don’t re-narrate every known article.
        store.update_status(episode_id, EpisodeStatus.summarizing)
        known = [a for a in articles if a.summary]
        fresh = [a for a in articles if not a.summary]
        n = len(articles)
        t0 = time.time()

        if known and not fresh:
            sources = sorted({a.source for a in known if a.source})
            src_bit = f" ({', '.join(sources[:3])})" if sources else ""
            narrate(
                EpisodeStatus.summarizing,
                f"We’ve got {n} pieces on the desk{src_bit} — skimming for "
                f"what’s sharp…",
            )
            hooks = _distinct_hooks(known, limit=2)
            if hooks:
                narrate(EpisodeStatus.summarizing, f"Worth noting: {hooks[0]}")
            if len(hooks) > 1:
                narrate(EpisodeStatus.summarizing, f"Also: {hooks[1]}")
            narrate(
                EpisodeStatus.summarizing,
                "Stack’s familiar — jumping straight into the show shape.",
            )
        else:
            narrate(
                EpisodeStatus.summarizing,
                f"Warming up with {n} stor{'y' if n == 1 else 'ies'}"
                + (f" ({len(fresh)} new to dig into)" if fresh and known else "")
                + "…",
            )
            used_hooks: list[str] = []
            if known:
                narrate(
                    EpisodeStatus.summarizing,
                    f"Skipping reread on {len(known)} we already know.",
                )
                used_hooks = _distinct_hooks(known, limit=1)
                if used_hooks:
                    narrate(
                        EpisodeStatus.summarizing,
                        f"Quick callback: {used_hooks[0]}",
                    )

            for art in fresh:
                short = _short_title(art.title)
                narrate(
                    EpisodeStatus.summarizing,
                    f"Fresh ink — reading “{short}”…",
                )
                enriched = await article_svc.enrich_article(art.text, settings)
                art.summary = enriched["summary"]
                art.topics = enriched["topics"]
                art.entities = enriched["entities"]
                store.update_article(art.id, **enriched)
                hook = _teaser(art, avoid=used_hooks)
                if hook:
                    narrate(EpisodeStatus.summarizing, f"Ooh — {hook}")
                    used_hooks.append(hook)
                log.info("pipeline.enriched", article_id=art.id)
            narrate(
                EpisodeStatus.summarizing,
                "Alright — time to shape the show.",
            )
        metrics.summarize_time_ms = _ms_since(t0)

        # 2. Script, with knowledge-base background for depth and continuity
        store.update_status(episode_id, EpisodeStatus.scripting)
        t0 = time.time()
        kb_context = kb_svc.gather_context(articles, store)
        if kb_context and focus:
            narrate(
                EpisodeStatus.scripting,
                f"Pulling prior coverage, steered toward: {focus}",
            )
        elif kb_context:
            narrate(
                EpisodeStatus.scripting,
                "Pulling a little prior coverage for continuity…",
            )
        elif focus:
            narrate(
                EpisodeStatus.scripting,
                f"North star for this one: {focus}",
            )

        def on_script_pass(message: str) -> None:
            narrate(EpisodeStatus.scripting, message)

        script_text, token_info = await script_svc.generate_script(
            articles, style, target_minutes, settings,
            kb_context=kb_context, focus=focus,
            on_pass=on_script_pass,
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
        if title:
            narrate(
                EpisodeStatus.scripting,
                f"Working title vibes: “{title}”",
            )
        narrate(
            EpisodeStatus.scripting,
            f"Script’s in — {len(chapters)} chapters, about "
            f"{episode_script.estimated_minutes:g} minutes of show.",
        )
        log.info(
            "pipeline.scripted",
            title=title,
            words=word_count,
            segments=len(segments),
            chapters=len(chapters),
        )

        # 3. TTS — progress follows chapter switches, not every speaker line.
        store.update_status(episode_id, EpisodeStatus.synthesizing)
        narrate(
            EpisodeStatus.synthesizing,
            f"Voices up — {len(chapters)} chapters to record…",
        )
        t0 = time.time()

        seg_to_chapter: dict[int, Chapter] = {}
        for ch in chapters:
            for i in ch.segment_indices:
                seg_to_chapter[i] = ch

        last_chapter_key: tuple[str, str] | None = None

        def on_segment(index: int, speaker: str, text: str) -> None:
            nonlocal last_chapter_key
            ch = seg_to_chapter.get(index)
            if ch is None:
                return
            key = (ch.role.value, ch.title)
            if key == last_chapter_key:
                return
            last_chapter_key = key
            label = _CHAPTER_LABELS.get(ch.role.value, "Chapter")
            narrate(
                EpisodeStatus.synthesizing,
                f"{label} · {ch.title}",
            )

        audio_chunks = await tts_svc.synthesize_script(
            segments, voice_mapping, voice_config, style.tone.value, settings,
            on_segment=on_segment,
        )
        metrics.tts_time_ms = _ms_since(t0)
        metrics.tts_characters = sum(s.char_count for s in segments)

        # 4. Mix — full episode plus one file per chapter for adaptive playback
        store.update_status(episode_id, EpisodeStatus.mixing)
        t0 = time.time()
        intro_music = None
        if audio_config.intro_music:
            narrate(EpisodeStatus.mixing, "Dropping in the theme sting…")
            intro_music = await music_svc.get_theme(settings)
        narrate(
            EpisodeStatus.mixing,
            "Sewing the takes together — almost in your ears…",
        )
        mix = audio_svc.build_episode_audio(
            audio_chunks, [c.segment_indices for c in chapters], audio_config,
            intro_music=intro_music,
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

        narrate(
            EpisodeStatus.mixing,
            "Pulling a reading list for the things we talked about…",
        )
        try:
            links = await links_svc.curate_links(
                articles, episode_script, title, focus, settings,
            )
        except Exception as exc:
            log.warning("links.curate_failed", error=str(exc))
            links = []

        mins, secs = int(duration // 60), int(duration % 60)
        narrate(
            EpisodeStatus.ready,
            f"You’re on air — {mins}m {secs:02d}s, fresh and ready to play.",
        )

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
            links=links,
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
        narrate(EpisodeStatus.failed, f"Failed: {exc}")
        store.update_episode(
            episode_id,
            status=EpisodeStatus.failed,
            error=str(exc),
            metrics=metrics,
        )
        log.error("pipeline.failed", episode_id=episode_id, error=str(exc))
        raise
