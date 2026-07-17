from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar

import structlog
from anthropic import AsyncAnthropic

from config import Settings
from models import Article, Chapter, ChapterRole, ScriptSegment, StyleConfig
from prompts import (
    build_banter_prompt,
    build_outline_prompt,
    build_system_prompt,
    is_dialogue_tone,
)

log = structlog.get_logger()

_T = TypeVar("_T")

_OUTLINE_PULSES = [
    "Lining up the beats…",
    "Sorting what’s core vs. optional…",
    "Hunting for the cold-open hook…",
    "Still outlining — almost there…",
]

_BANTER_PULSES = [
    "Hosts are pushing back on each other…",
    "Tuning the interruptions…",
    "Making the callbacks land…",
    "Still writing banter — worth the wait…",
]

_MONO_PULSES = [
    "Finding the through-line…",
    "Tightening the closer…",
    "Still writing — hang tight…",
]


async def _await_with_pulse(
    awaitable: Awaitable[_T],
    on_pulse: Callable[[str], None] | None,
    pulses: Sequence[str],
    interval: float = 3.8,
) -> _T:
    """Emit progress lines while a long model call runs."""
    if on_pulse is None:
        return await awaitable
    task = asyncio.ensure_future(awaitable)
    pulse_i = 0
    while not task.done():
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=interval)
        except asyncio.TimeoutError:
            if pulse_i < len(pulses):
                on_pulse(pulses[pulse_i])
            elif pulse_i == len(pulses):
                on_pulse("Still going — good shows aren’t instant…")
            pulse_i += 1
    return task.result()

_SPEAKER_RE = re.compile(r"^\[([A-Z]+)\]:\s*(.*)", re.MULTILINE)
_CHAPTER_RE = re.compile(
    r"^#*\s*CHAPTER:\s*(.+?)\s*\[(intro|core|optional|closer)\]\s*$",
    re.IGNORECASE,
)
_TITLE_RE = re.compile(
    r"^#*[ \t]*TITLE:[ \t]*(.*?)[ \t]*$", re.IGNORECASE | re.MULTILINE
)
# Trailing "| delivery: tag" on a dialogue line (tag = word chars / hyphen).
_DELIVERY_RE = re.compile(
    r"\s*\|\s*delivery:\s*([a-zA-Z][\w-]*)\s*$", re.IGNORECASE
)


def extract_title(text: str) -> tuple[str | None, str]:
    """Pull the TITLE: line off the top of a script.

    Only searches the first 500 characters so a stray mention mid-script
    can't hijack the title. Returns (title or None, script without the line).
    """
    m = _TITLE_RE.search(text[:500])
    if not m:
        return None, text
    title = m.group(1).strip().strip('"').strip()
    cleaned = (text[: m.start()] + text[m.end():]).strip()
    return (title or None), cleaned


def _split_delivery(line: str) -> tuple[str, str | None]:
    """Strip a trailing `| delivery: tag` from spoken text."""
    m = _DELIVERY_RE.search(line)
    if not m:
        return line.strip(), None
    text = line[: m.start()].strip()
    return text, m.group(1).lower()


def _article_user_message(
    articles: list[Article],
    focus: str | None,
    kb_context: str | None,
    lead: str,
) -> str:
    article_blocks = []
    for i, a in enumerate(articles, 1):
        body = a.summary or a.text[:3000]
        article_blocks.append(
            f"--- ARTICLE {i}: {a.title} (source: {a.source}) ---\n{body}"
        )

    user_msg = lead + "\n\n" + "\n\n".join(article_blocks)
    if focus:
        user_msg += (
            f'\n\nEPISODE DIRECTION: Frame the entire episode around: "{focus}". '
            "The title, cold open, and chapter structure should all serve this "
            "direction; give articles that don't serve it only brief treatment."
        )
    if kb_context:
        user_msg += "\n\n" + kb_context
    return user_msg


async def _claude_text(
    system: str,
    user_msg: str,
    settings: Settings,
) -> tuple[str, dict]:
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    resp = await client.messages.create(
        model=settings.claude_model,
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    token_info = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }
    return resp.content[0].text, token_info


def _sum_tokens(*infos: dict) -> dict:
    return {
        "input_tokens": sum(i["input_tokens"] for i in infos),
        "output_tokens": sum(i["output_tokens"] for i in infos),
    }


async def generate_outline(
    articles: list[Article],
    style: StyleConfig,
    target_minutes: int,
    settings: Settings,
    kb_context: str | None = None,
    focus: str | None = None,
) -> tuple[str, dict]:
    target_words = target_minutes * 150
    system = build_outline_prompt(style, target_words=target_words)
    user_msg = _article_user_message(
        articles, focus, kb_context,
        lead="Build a content-only outline covering these articles:",
    )
    outline, token_info = await _claude_text(system, user_msg, settings)
    log.info(
        "script.outline",
        words=len(outline.split()),
        input_tokens=token_info["input_tokens"],
        output_tokens=token_info["output_tokens"],
    )
    return outline, token_info


async def dramatize_outline(
    outline: str,
    style: StyleConfig,
    target_minutes: int,
    settings: Settings,
) -> tuple[str, dict]:
    target_words = target_minutes * 150
    system = build_banter_prompt(style, target_words=target_words)
    user_msg = (
        "Dramatize this outline into banter. Preserve TITLE and CHAPTER "
        "markers. Tag every line with | delivery: <tag>.\n\n"
        f"{outline}"
    )
    script_text, token_info = await _claude_text(system, user_msg, settings)
    log.info(
        "script.dramatized",
        words=len(script_text.split()),
        input_tokens=token_info["input_tokens"],
        output_tokens=token_info["output_tokens"],
    )
    return script_text, token_info


async def generate_script_monologue(
    articles: list[Article],
    style: StyleConfig,
    target_minutes: int,
    settings: Settings,
    kb_context: str | None = None,
    focus: str | None = None,
) -> tuple[str, dict]:
    target_words = target_minutes * 150
    system = build_system_prompt(style, target_words=target_words)
    user_msg = _article_user_message(
        articles, focus, kb_context,
        lead="Write a podcast script covering these articles:",
    )
    script_text, token_info = await _claude_text(system, user_msg, settings)
    log.info(
        "script.generated",
        words=len(script_text.split()),
        input_tokens=token_info["input_tokens"],
        output_tokens=token_info["output_tokens"],
        mode="monologue",
    )
    return script_text, token_info


async def generate_script(
    articles: list[Article],
    style: StyleConfig,
    target_minutes: int,
    settings: Settings,
    kb_context: str | None = None,
    focus: str | None = None,
    on_pass: Callable[[str], None] | None = None,
) -> tuple[str, dict]:
    """Generate a full script.

    Dialogue tones use outline → dramatize (two passes). Monologue tones
    stay single-pass. ``on_pass`` is an optional callback ``(label: str)``
    for pipeline narration between passes.
    """
    if is_dialogue_tone(style.tone.value):
        if on_pass:
            on_pass(
                "Sketching the bones first — the facts, the order, the beats…"
            )
        outline, t1 = await _await_with_pulse(
            generate_outline(
                articles, style, target_minutes, settings,
                kb_context=kb_context, focus=focus,
            ),
            on_pass,
            _OUTLINE_PULSES,
        )
        if on_pass:
            on_pass(
                "Now the fun part — turning that outline into real host banter…"
            )
        script_text, t2 = await _await_with_pulse(
            dramatize_outline(outline, style, target_minutes, settings),
            on_pass,
            _BANTER_PULSES,
        )
        token_info = _sum_tokens(t1, t2)
        log.info(
            "script.generated",
            words=len(script_text.split()),
            input_tokens=token_info["input_tokens"],
            output_tokens=token_info["output_tokens"],
            mode="outline_dramatize",
        )
        return script_text, token_info

    if on_pass:
        on_pass("Writing it like a show, not a memo…")
    return await _await_with_pulse(
        generate_script_monologue(
            articles, style, target_minutes, settings,
            kb_context=kb_context, focus=focus,
        ),
        on_pass,
        _MONO_PULSES,
    )


def parse_script(text: str) -> tuple[list[ScriptSegment], list[Chapter]]:
    segments: list[ScriptSegment] = []
    chapters: list[Chapter] = []
    current_chapter: Chapter | None = None
    current_speaker: str | None = None
    current_delivery: str | None = None
    current_lines: list[str] = []

    def flush_segment() -> None:
        nonlocal current_speaker, current_lines, current_delivery
        if current_speaker and current_lines:
            joined = " ".join(current_lines)
            segments.append(ScriptSegment(
                speaker=current_speaker,
                text=joined,
                delivery=current_delivery,
                char_count=len(joined),
            ))
            if current_chapter is not None:
                current_chapter.segment_indices.append(len(segments) - 1)
        current_speaker = None
        current_delivery = None
        current_lines = []

    for line in text.split("\n"):
        cm = _CHAPTER_RE.match(line.strip())
        if cm:
            flush_segment()
            current_chapter = Chapter(
                title=cm.group(1),
                role=ChapterRole(cm.group(2).lower()),
            )
            chapters.append(current_chapter)
            continue
        m = _SPEAKER_RE.match(line)
        if m:
            flush_segment()
            current_speaker = m.group(1)
            spoken, delivery = _split_delivery(m.group(2))
            current_delivery = delivery
            current_lines = [spoken] if spoken else []
        elif current_speaker and line.strip():
            # Continuation lines may also carry a delivery tag on the last piece.
            spoken, delivery = _split_delivery(line.strip())
            if delivery:
                current_delivery = delivery
            if spoken:
                current_lines.append(spoken)

    flush_segment()

    chapters = [c for c in chapters if c.segment_indices]

    # Dialogue before the first marker belongs to no chapter; give it one so
    # every synthesized segment is reachable through the manifest.
    covered = {i for c in chapters for i in c.segment_indices}
    orphaned = [i for i in range(len(segments)) if i not in covered]
    if chapters and orphaned:
        chapters.insert(0, Chapter(
            title="Opening",
            role=ChapterRole.intro,
            segment_indices=orphaned,
        ))

    if not chapters and segments:
        # Model skipped the markers — fall back to one all-core chapter so the
        # pipeline and manifest still work.
        log.warning("script.no_chapter_markers")
        chapters = [Chapter(
            title="Episode",
            role=ChapterRole.core,
            segment_indices=list(range(len(segments))),
        )]

    return segments, chapters
