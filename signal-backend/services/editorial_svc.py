from __future__ import annotations

import json

import structlog
from anthropic import AsyncAnthropic

from config import Settings
from models import Article, EditorialDecision, REGISTERS, TOPIC_CATEGORIES
from prompts import build_editorial_prompt

log = structlog.get_logger()


def _fallback(articles: list[Article], focus: str | None, reason: str) -> EditorialDecision:
    return EditorialDecision(
        topic_category="general",
        register="conversational",
        chosen_angle=focus or (articles[0].title if articles else ""),
        framing_note=None,
        rationale=f"classifier fallback: {reason}",
    )


def parse_decision(raw: str) -> EditorialDecision:
    """Parse the classifier's strict-JSON reply; raises on unusable output.

    Unknown categories/registers coerce to safe defaults rather than failing —
    a slightly-off label must never block an episode.
    """
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object in reply")
    data = json.loads(raw[start : end + 1])

    category = str(data.get("topic_category", "")).strip().lower()
    if category not in TOPIC_CATEGORIES:
        category = "general"
    register = str(data.get("register", "")).strip().lower()
    if register not in REGISTERS:
        register = "conversational"

    framing = data.get("framing_note")
    framing_note = str(framing).strip() if framing else None
    if framing_note and framing_note.lower() in {"null", "none", ""}:
        framing_note = None

    return EditorialDecision(
        topic_category=category,
        register=register,
        chosen_angle=str(data.get("chosen_angle", "")).strip(),
        framing_note=framing_note,
        rationale=str(data.get("rationale", "")).strip(),
    )


async def decide(
    articles: list[Article],
    focus: str | None,
    settings: Settings,
) -> EditorialDecision:
    """One small Claude call that decides how this episode should sound.

    Best-effort: any model or parse failure returns a neutral fallback so the
    classifier can never block an episode.
    """
    lines = []
    for i, a in enumerate(articles, 1):
        bits = [f"{i}. {a.title} ({a.source})"]
        if a.topics:
            bits.append(f"   topics: {', '.join(a.topics)}")
        if a.entities:
            bits.append(f"   entities: {', '.join(a.entities[:6])}")
        if a.summary:
            bits.append(f"   summary: {a.summary[:400]}")
        lines.append("\n".join(bits))
    user_msg = "ARTICLES:\n" + "\n".join(lines)
    if focus:
        user_msg += f"\n\nLISTENER FOCUS: {focus}"

    try:
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        resp = await client.messages.create(
            model=settings.claude_model,
            max_tokens=500,
            system=build_editorial_prompt(),
            messages=[{"role": "user", "content": user_msg}],
        )
        decision = parse_decision(resp.content[0].text)
    except Exception as exc:
        log.warning("editorial.decide_failed", error=str(exc))
        return _fallback(articles, focus, str(exc))

    log.info(
        "editorial.decision",
        topic_category=decision.topic_category,
        register=decision.register,
        angle=decision.chosen_angle,
        framing=decision.framing_note,
        rationale=decision.rationale,
    )
    return decision
