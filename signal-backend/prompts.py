from __future__ import annotations

from models import StyleConfig

# --------------- Speakers per tone ---------------

TONE_SPEAKERS: dict[str, list[str]] = {
    "casual": ["ALEX", "JAMIE"],
    "polished": ["HOST"],
    "debate": ["BULL", "BEAR"],
    "technical": ["HOST"],
}

# --------------- Dimension instruction banks ---------------

TONE_INSTRUCTIONS: dict[str, str] = {
    "casual": (
        "Two hosts ALEX and JAMIE, informal. They interrupt, react naturally. "
        "Alex sets up, Jamie pushes back."
    ),
    "polished": "Single narrator HOST, NPR-style. Measured, precise, authoritative.",
    "debate": (
        "Two hosts BULL and BEAR, opposing positions. "
        "Substantive disagreement with data."
    ),
    "technical": "Single HOST, technical deep-dive. Precise terminology, benchmarks.",
}

DEPTH_INSTRUCTIONS: dict[str, str] = {
    "briefing": "Cover ALL articles equally. Key facts, one angle, move on. ~2-3 min each.",
    "deep_dive": (
        "Focus 1-2 most significant. Go deep: implications, context, what people miss."
    ),
    "synthesis": (
        "Connections ACROSS articles. What story emerges? Patterns? Contradictions?"
    ),
}

LENS_INSTRUCTIONS: dict[str, str] = {
    "investor": "Revenue, positioning, TAM, valuation. Financial terminology.",
    "engineer": "Architecture, moat, ecosystem, tradeoffs.",
    "macro": "Policy, supply chain, nation-state, systemic trends.",
    "general": "Why it matters, clear explanations, real-world implications.",
}

PACING_INSTRUCTIONS: dict[str, str] = {
    "rapid": "High energy. Short sentences under 20 words. Fragments.",
    "measured": "Let ideas breathe. Longer sentences. Pauses after insights.",
    "variable": "Fast for facts, slow for analysis. Contrast creates engagement.",
}

HUMOR_INSTRUCTIONS: dict[str, str] = {
    "serious": "None. Content is the entertainment.",
    "dry": "Deadpan. State absurd truths plainly. Note ironies without winking.",
    "playful": "Vivid analogies, pop culture refs. Smart and fun.",
    "roast": "Sharp, opinionated. Call out bad takes. Rhetorical exaggeration.",
}

AUDIENCE_INSTRUCTIONS: dict[str, str] = {
    "insider": "Skip basics. Shorthand freely.",
    "informed": "Brief framing. One sentence context max.",
    "curious": "Define terms naturally. Never condescend.",
}

STRUCTURE_INSTRUCTIONS: dict[str, str] = {
    "narrative": "Story arc. Tension to climactic insight.",
    "ranked": "Biggest first, descending scope.",
    "thematic": "Group by theme not article. Reveal patterns.",
    "contrarian": "Lead with what everyone gets wrong.",
}

CLOSER_INSTRUCTIONS: dict[str, str] = {
    "actionable": "2-3 specific action items.",
    "philosophical": "Zoom out to decade-level implications.",
    "prediction": "Bold, specific, falsifiable prediction.",
    "question": "Open question for thinking time.",
}

# --------------- Prompt builders ---------------


def build_system_prompt(style: StyleConfig, target_words: int = 4500) -> str:
    speakers = TONE_SPEAKERS[style.tone.value]
    is_dialogue = len(speakers) > 1

    if is_dialogue:
        format_block = (
            f"FORMAT: Dialogue between {' and '.join(speakers)}.\n"
            f"Every line MUST start with [{speakers[0]}]: or [{speakers[1]}]:.\n"
            "Alternate speakers naturally. No narration outside dialogue tags."
        )
    else:
        format_block = (
            f"FORMAT: Monologue by {speakers[0]}.\n"
            f"Every line MUST start with [{speakers[0]}]:.\n"
            "No other speakers."
        )

    sections = [
        f"You are a podcast script writer for 'The Signal'.\n",
        f"TONE: {TONE_INSTRUCTIONS[style.tone.value]}",
        f"DEPTH: {DEPTH_INSTRUCTIONS[style.depth.value]}",
        f"LENS: {LENS_INSTRUCTIONS[style.lens.value]}",
        f"PACING: {PACING_INSTRUCTIONS[style.pacing.value]}",
        f"HUMOR: {HUMOR_INSTRUCTIONS[style.humor.value]}",
        f"AUDIENCE: {AUDIENCE_INSTRUCTIONS[style.audience.value]}",
        f"STRUCTURE: {STRUCTURE_INSTRUCTIONS[style.structure.value]}",
        f"CLOSER: {CLOSER_INSTRUCTIONS[style.closer.value]}",
        "",
        format_block,
        "",
        "EPISODE FLOW:",
        "1. Cold open — a hook that pulls listeners in immediately",
        "2. Framing — set the stage, what are we covering and why now",
        "3. Segments — the substance, one per article or theme",
        "4. Closer — wrap with the chosen closer style",
        "",
        f"TARGET: ~{target_words} words ({target_words // 150} minutes at speaking pace).",
        "",
        "RULES:",
        "- No filler phrases ('without further ado', 'let's dive in', 'buckle up')",
        "- Reference specific data points, numbers, quotes from the source material",
        "- Transitions should be organic, not mechanical",
        "- End forward-looking — what to watch for next",
        "- Do NOT include stage directions, sound effects, or metadata",
        "- Output ONLY the script text with speaker tags",
    ]

    return "\n".join(sections)


def build_summary_prompt() -> str:
    return (
        "Summarize the following article in 150-250 words. "
        "Preserve specific numbers, quotes, and data points. "
        "Focus on: key facts, core thesis, and implications. "
        "Write in plain prose, no bullet points."
    )
