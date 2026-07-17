from __future__ import annotations

import re

import structlog
from anthropic import AsyncAnthropic

from config import Settings
from models import Article, Chapter, ChapterRole, ScriptSegment, StyleConfig
from prompts import build_system_prompt

log = structlog.get_logger()

_SPEAKER_RE = re.compile(r"^\[([A-Z]+)\]:\s*(.*)", re.MULTILINE)
_CHAPTER_RE = re.compile(
    r"^#*\s*CHAPTER:\s*(.+?)\s*\[(intro|core|optional|closer)\]\s*$",
    re.IGNORECASE,
)
_TITLE_RE = re.compile(
    r"^#*[ \t]*TITLE:[ \t]*(.*?)[ \t]*$", re.IGNORECASE | re.MULTILINE
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


async def generate_script(
    articles: list[Article],
    style: StyleConfig,
    target_minutes: int,
    settings: Settings,
    kb_context: str | None = None,
    focus: str | None = None,
) -> tuple[str, dict]:
    target_words = target_minutes * 150
    system = build_system_prompt(style, target_words=target_words)

    article_blocks = []
    for i, a in enumerate(articles, 1):
        body = a.summary or a.text[:3000]
        article_blocks.append(
            f"--- ARTICLE {i}: {a.title} (source: {a.source}) ---\n{body}"
        )

    user_msg = (
        "Write a podcast script covering these articles:\n\n"
        + "\n\n".join(article_blocks)
    )
    if focus:
        user_msg += (
            f'\n\nEPISODE DIRECTION: Frame the entire episode around: "{focus}". '
            "The title, cold open, and chapter structure should all serve this "
            "direction; give articles that don't serve it only brief treatment."
        )
    if kb_context:
        user_msg += "\n\n" + kb_context

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    resp = await client.messages.create(
        model=settings.claude_model,
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )

    script_text = resp.content[0].text
    token_info = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }

    log.info(
        "script.generated",
        words=len(script_text.split()),
        input_tokens=token_info["input_tokens"],
        output_tokens=token_info["output_tokens"],
    )
    return script_text, token_info


def parse_script(text: str) -> tuple[list[ScriptSegment], list[Chapter]]:
    segments: list[ScriptSegment] = []
    chapters: list[Chapter] = []
    current_chapter: Chapter | None = None
    current_speaker: str | None = None
    current_lines: list[str] = []

    def flush_segment() -> None:
        nonlocal current_speaker, current_lines
        if current_speaker and current_lines:
            joined = " ".join(current_lines)
            segments.append(ScriptSegment(
                speaker=current_speaker,
                text=joined,
                char_count=len(joined),
            ))
            if current_chapter is not None:
                current_chapter.segment_indices.append(len(segments) - 1)
        current_speaker = None
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
            current_lines = [m.group(2)]
        elif current_speaker and line.strip():
            current_lines.append(line.strip())

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
