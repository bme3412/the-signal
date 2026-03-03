from __future__ import annotations

import re

import structlog
from anthropic import AsyncAnthropic

from config import Settings
from models import Article, ScriptSegment, StyleConfig
from prompts import build_system_prompt

log = structlog.get_logger()

_SPEAKER_RE = re.compile(r"^\[([A-Z]+)\]:\s*(.*)", re.MULTILINE)


async def generate_script(
    articles: list[Article],
    style: StyleConfig,
    target_minutes: int,
    settings: Settings,
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


def parse_script(text: str) -> list[ScriptSegment]:
    segments: list[ScriptSegment] = []
    current_speaker: str | None = None
    current_lines: list[str] = []

    for line in text.split("\n"):
        m = _SPEAKER_RE.match(line)
        if m:
            if current_speaker and current_lines:
                joined = " ".join(current_lines)
                segments.append(ScriptSegment(
                    speaker=current_speaker,
                    text=joined,
                    char_count=len(joined),
                ))
            current_speaker = m.group(1)
            current_lines = [m.group(2)]
        elif current_speaker and line.strip():
            current_lines.append(line.strip())

    if current_speaker and current_lines:
        joined = " ".join(current_lines)
        segments.append(ScriptSegment(
            speaker=current_speaker,
            text=joined,
            char_count=len(joined),
        ))

    return segments
