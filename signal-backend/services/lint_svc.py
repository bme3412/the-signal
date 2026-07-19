"""Naturalness lint — cheap, rules-based checks on a parsed script.

Flags the mechanical tells of fake conversation (uniform turns, no
questions, register leakage, unspeakable tokens). Severity "revise" triggers
one bounded LLM revision pass; "warn" is logged only.
"""

from __future__ import annotations

import re
import statistics

import structlog

from models import (
    Chapter,
    EditorialDecision,
    LintFlag,
    LintReport,
    ScriptSegment,
)
from services.script_svc import strip_audio_tags

log = structlog.get_logger()

# Categories whose stories legitimately use financial vocabulary.
_FINANCIAL_CATEGORIES = {"finance_markets"}

# Clearly-financial jargon; leaking into a sports/culture episode with no
# framing_note is the "investor lens on the World Cup" failure mode.
_FINANCE_JARGON = (
    r"\bTAM\b",
    r"(?i)\bEBITDA\b",
    r"(?i)\bbasis points?\b",
    r"(?i)\bprice targets?\b",
    r"(?i)\bvaluations?\b",
    r"(?i)\bmarket cap\b",
    r"(?i)\bshareholders?\b",
    r"(?i)\bquarterly earnings\b",
    r"(?i)\btotal addressable market\b",
)

# Digits and symbols the TTS voice mangles — scripts must spell speech out.
_UNSPEAKABLE = re.compile(r"\d|%|\$|&|\bQ[1-4]\b")

# Standalone agreement theater (whole short line).
_STOCK_REACTIONS = {"absolutely", "exactly", "so true", "totally"}

# Stock phrases banned anywhere.
_BANNED_PHRASES = (
    "great point",
    "couldn't agree more",
    "let's dive in",
    "buckle up",
    "without further ado",
)

_MIN_TURNS_FOR_VARIANCE = 8


def _words(seg: ScriptSegment) -> int:
    return len(strip_audio_tags(seg.text).split())


def _check_turn_variance(segments: list[ScriptSegment]) -> list[LintFlag]:
    if len(segments) < _MIN_TURNS_FOR_VARIANCE:
        return []
    counts = [_words(s) for s in segments]
    mean = statistics.mean(counts)
    if mean <= 0:
        return []
    cv = statistics.pstdev(counts) / mean
    flags = []
    if cv < 0.55:
        flags.append(LintFlag(
            rule="turn_variance",
            severity="revise",
            detail=(
                f"Turn lengths are too uniform (variation {cv:.2f}) — real "
                "co-hosts mix one-word reactions with long explanations. "
                "Break up the pattern with short reactive beats."
            ),
        ))
    for i in range(len(counts) - 3):
        window = counts[i : i + 4]
        w_mean = statistics.mean(window)
        if w_mean > 8 and all(abs(c - w_mean) <= 0.25 * w_mean for c in window):
            flags.append(LintFlag(
                rule="turn_variance",
                severity="revise",
                segment_index=i,
                detail=(
                    f"Turns {i}-{i + 3} are all nearly the same length — "
                    "alternating equal blocks reads as fake banter."
                ),
            ))
            break
    return flags


def _check_questions(
    segments: list[ScriptSegment], chapters: list[Chapter]
) -> list[LintFlag]:
    flags = []
    chapters_without = []
    for ch in chapters:
        if len(ch.segment_indices) < 3:
            continue
        if not any("?" in segments[i].text for i in ch.segment_indices):
            chapters_without.append(ch.title)
    if chapters_without:
        severity = "revise" if len(chapters_without) > len(chapters) / 2 else "warn"
        flags.append(LintFlag(
            rule="missing_questions",
            severity=severity,
            detail=(
                "No genuine question in chapter(s): "
                + ", ".join(chapters_without)
                + ". One host should actually ask, the other actually answer."
            ),
        ))
    return flags


def _check_register(
    segments: list[ScriptSegment], editorial: EditorialDecision | None
) -> list[LintFlag]:
    if editorial is None:
        return []
    if editorial.topic_category in _FINANCIAL_CATEGORIES or editorial.framing_note:
        return []
    flags = []
    for i, seg in enumerate(segments):
        for pattern in _FINANCE_JARGON:
            m = re.search(pattern, seg.text)
            if m:
                flags.append(LintFlag(
                    rule="register_mismatch",
                    severity="revise",
                    segment_index=i,
                    detail=(
                        f"Financial jargon '{m.group(0)}' in a "
                        f"{editorial.topic_category} episode with neutral "
                        "framing — rephrase in plain terms."
                    ),
                ))
                break
    return flags[:5]


def _check_unspeakable(segments: list[ScriptSegment]) -> list[LintFlag]:
    flags = []
    for i, seg in enumerate(segments):
        m = _UNSPEAKABLE.search(strip_audio_tags(seg.text))
        if m:
            flags.append(LintFlag(
                rule="unspeakable",
                severity="revise",
                segment_index=i,
                detail=(
                    f"Unspeakable token '{m.group(0)}' in line {i} "
                    f"('{seg.text[:60]}…') — spell it out the way a person "
                    "would say it."
                ),
            ))
    return flags[:5]


def _check_banned_phrases(segments: list[ScriptSegment]) -> list[LintFlag]:
    flags = []
    heres_the_thing = 0
    for i, seg in enumerate(segments):
        lowered = seg.text.lower()
        stripped = strip_audio_tags(lowered).strip(" .!—-")
        if stripped in _STOCK_REACTIONS:
            flags.append(LintFlag(
                rule="banned_phrases",
                severity="revise",
                segment_index=i,
                detail=(
                    f"Standalone '{stripped}' is agreement theater — react "
                    "to a specific fact instead."
                ),
            ))
            continue
        for phrase in _BANNED_PHRASES:
            if phrase in lowered:
                flags.append(LintFlag(
                    rule="banned_phrases",
                    severity="revise",
                    segment_index=i,
                    detail=f"Stock phrase '{phrase}' in line {i} — cut it.",
                ))
                break
        heres_the_thing += lowered.count("here's the thing")
    if heres_the_thing >= 2:
        flags.append(LintFlag(
            rule="banned_phrases",
            severity="revise",
            detail="'here's the thing' appears more than once — a robotic tell.",
        ))
    return flags[:5]


def _check_reactions(
    segments: list[ScriptSegment], chapters: list[Chapter]
) -> list[LintFlag]:
    flags = []
    for ch in chapters:
        if len(ch.segment_indices) < 4:
            continue
        if not any(_words(segments[i]) <= 5 for i in ch.segment_indices):
            flags.append(LintFlag(
                rule="missing_reactions",
                severity="warn",
                detail=(
                    f"Chapter '{ch.title}' has no short reactive beat — "
                    "every turn is a speech."
                ),
            ))
    return flags


def lint(
    segments: list[ScriptSegment],
    chapters: list[Chapter],
    editorial: EditorialDecision | None,
) -> LintReport:
    flags = [
        *_check_turn_variance(segments),
        *_check_questions(segments, chapters),
        *_check_register(segments, editorial),
        *_check_unspeakable(segments),
        *_check_banned_phrases(segments),
        *_check_reactions(segments, chapters),
    ]
    report = LintReport(flags=flags)
    log.info(
        "lint.report",
        flags=len(flags),
        revise=sum(1 for f in flags if f.severity == "revise"),
        rules=sorted({f.rule for f in flags}),
    )
    return report
