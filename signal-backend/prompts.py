from __future__ import annotations

from models import StyleConfig

# --------------- Speakers per tone ---------------

TONE_SPEAKERS: dict[str, list[str]] = {
    "casual": ["ALEX", "JAMIE"],
    "polished": ["ANCHOR", "ANALYST"],
    "debate": ["BULL", "BEAR"],
    "technical": ["LEAD", "PEER"],
}

# Opposing priors — friction generates banter. Every tone is two voices.
PERSONA_PRIORS: dict[str, dict[str, str]] = {
    "casual": {
        "ALEX": (
            "Instinctive optimist who always finds the upside. Leans into "
            "opportunity, momentum, and what could go right. Gets excited by "
            "big moves before the spreadsheet catches up."
        ),
        "JAMIE": (
            "Skeptic who needs the number before believing the story. "
            "Pushes for evidence, flags hype, and won't let a clean narrative "
            "pass without a concrete fact."
        ),
    },
    "polished": {
        "ANCHOR": (
            "Measured NPR-style host. Frames the story, keeps the pace, "
            "asks the clarifying question the listener needs."
        ),
        "ANALYST": (
            "Calm specialist with receipts. Adds context, caveats, and the "
            "number behind the narrative — never a monologue partner who only agrees."
        ),
    },
    "debate": {
        "BULL": (
            "Case-for believer. Argues the constructive thesis with data — "
            "growth, positioning, why the market underprices the upside."
        ),
        "BEAR": (
            "Case-against skeptic. Stresses risks, base rates, and what the "
            "bullish story is ignoring. Demands falsifiable claims."
        ),
    },
    "technical": {
        "LEAD": (
            "Senior engineer walking through architecture and tradeoffs. "
            "Precise terminology, benchmarks, systems thinking."
        ),
        "PEER": (
            "Sharp peer who pressure-tests the design. Asks 'what breaks?', "
            "compares alternatives, won't let jargon paper over a weak claim."
        ),
    },
}

# --------------- Dimension instruction banks ---------------

TONE_INSTRUCTIONS: dict[str, str] = {
    "casual": (
        "Two hosts ALEX and JAMIE with opposing priors. "
        "ALEX is the instinctive optimist; JAMIE is the skeptic who needs the "
        "number. Informal, interruptive, reactive — genuine friction, not "
        "interchangeable narrators."
    ),
    "polished": (
        "Two voices ANCHOR and ANALYST, NPR-style. Measured and precise, "
        "but still a real conversation — ANCHOR frames, ANALYST brings receipts "
        "and gentle pushback. Never a solo monologue."
    ),
    "debate": (
        "Two hosts BULL and BEAR with opposing priors. "
        "BULL argues the constructive case; BEAR stresses risks and base rates. "
        "Substantive disagreement grounded in data."
    ),
    "technical": (
        "Two engineers LEAD and PEER. Precise terminology and benchmarks, "
        "with PEER stress-testing LEAD's claims. Deep-dive dialogue, not a lecture."
    ),
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

DELIVERY_TAGS = (
    "neutral",
    "warm",
    "amused",
    "deadpan",
    "pointed",
    "interrupting",
    "skeptical",
    "excited",
)


def is_dialogue_tone(tone: str) -> bool:
    """True when the tone uses two hosts (all current tones do)."""
    return len(TONE_SPEAKERS.get(tone, [])) > 1


# --------------- Prompt builders ---------------


def build_system_prompt(style: StyleConfig, target_words: int = 4500) -> str:
    """Single-pass script prompt — used for monologue tones."""
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
        "TITLE:",
        "The very first line of your output must be:",
        "TITLE: <a specific, catchy 4-9 word episode title drawn from the content>",
        "Never generic ('News Roundup', 'Today's Episode') — name the actual story.",
        "",
        "CHAPTERS:",
        "Divide the script into chapters. Before each chapter's dialogue, output a "
        "marker on its own line:",
        "### CHAPTER: <short title> [intro|core|optional|closer]",
        "- First chapter: cold open + framing, marked [intro]",
        "- One chapter per article or theme, marked [core]",
        "- 1-2 bonus chapters marked [optional]: a self-contained tangent, deeper "
        "background, or related angle. Place them between core chapters, never first "
        "or last. The episode must flow perfectly if they are skipped — later "
        "chapters must NEVER reference optional content.",
        "- Final chapter: the closer, marked [closer]",
        "",
        f"TARGET: ~{target_words} words ({target_words // 150} minutes at speaking pace).",
        "",
        "WRITE FOR THE EAR, NOT THE EYE — this is the difference between "
        "sounding human and sounding like a robot reading headlines:",
        "- Write in complete, flowing spoken sentences. A voice model reads a "
        "period as a full stop, so strings of fragments ('Sunday. Three p.m. "
        "East Rutherford.') come out clipped and robotic. Instead: 'It's "
        "Sunday afternoon in East Rutherford, New Jersey, and kickoff is at "
        "three Eastern.'",
        "- Vary sentence length. Mix short punchy lines with longer, winding "
        "ones — that rhythm is what makes speech sound alive.",
        "- Use natural connective tissue: 'and', 'but here's the thing', 'so', "
        "'which means', 'now'. Let thoughts run into each other the way people "
        "actually talk.",
        "- Read it aloud in your head. If a line would sound like a stock "
        "ticker or a list of nouns, rewrite it as a sentence a person would say.",
        "- Spell out how things are said: 'two to nothing', not '2-0'; "
        "'ninety-sixth minute', not '96th'. Expand abbreviations.",
        "",
        "RULES:",
        "- No filler phrases ('without further ado', 'let's dive in', 'buckle up')",
        "- Reference specific data points, numbers, quotes from the source material",
        "- Transitions should be organic, not mechanical",
        "- End forward-looking — what to watch for next",
        "- Do NOT include stage directions, sound effects, or metadata",
        "- If KNOWLEDGE BASE CONTEXT is provided, use it for continuity and depth: "
        "reference prior coverage naturally ('as we covered recently...') and draw on "
        "background articles for context — but the episode is about the NEW articles",
        "- Output ONLY the script text with speaker tags",
    ]

    return "\n".join(sections)


def build_outline_prompt(style: StyleConfig, target_words: int = 4500) -> str:
    """Pass 1: content-only outline — no dialogue, no personas."""
    minutes = target_words // 150
    return "\n".join([
        "You plan podcast episode outlines for 'The Signal'.",
        "Your ONLY job is content: facts, order, and chapter structure.",
        "Do NOT write dialogue. Do NOT invent host names or banter.",
        "Do NOT write spoken lines. Plain talking points only.",
        "",
        f"DEPTH: {DEPTH_INSTRUCTIONS[style.depth.value]}",
        f"LENS: {LENS_INSTRUCTIONS[style.lens.value]}",
        f"AUDIENCE: {AUDIENCE_INSTRUCTIONS[style.audience.value]}",
        f"STRUCTURE: {STRUCTURE_INSTRUCTIONS[style.structure.value]}",
        f"CLOSER: {CLOSER_INSTRUCTIONS[style.closer.value]}",
        "",
        f"TARGET LENGTH: enough substance for ~{target_words} spoken words "
        f"(~{minutes} minutes). Scale talking-point density accordingly.",
        "",
        "OUTPUT FORMAT:",
        "TITLE: <specific, catchy 4-9 word episode title drawn from the content>",
        "",
        "Then chapters. Before each chapter, a marker on its own line:",
        "### CHAPTER: <short title> [intro|core|optional|closer]",
        "- First chapter: cold-open hook + framing, marked [intro]",
        "- One chapter per article or theme, marked [core]",
        "- 1-2 bonus chapters marked [optional]: self-contained tangent or deeper "
        "background between cores — never first or last. Later chapters must NEVER "
        "depend on optional content (skippable).",
        "- Final chapter: closer beat matching CLOSER style, marked [closer]",
        "",
        "Under each chapter, a numbered list of talking points. Each point must:",
        "- Be a concrete fact, number, quote, or implication from the sources",
        "- Preserve specific data (dollar amounts, percentages, names, dates)",
        "- Stay in plain prose bullets — no [SPEAKER] tags, no dialogue",
        "",
        "If KNOWLEDGE BASE CONTEXT is provided, fold continuity into the outline "
        "as factual background points — but the episode is about the NEW articles.",
        "Output ONLY the title, chapter markers, and talking points.",
    ])


def build_banter_prompt(style: StyleConfig, target_words: int = 4500) -> str:
    """Pass 2: dramatize an outline into friction-heavy dialogue."""
    speakers = TONE_SPEAKERS[style.tone.value]
    priors = PERSONA_PRIORS.get(style.tone.value, {})
    persona_lines = [
        f"- {name}: {priors[name]}" for name in speakers if name in priors
    ]
    tags = ", ".join(DELIVERY_TAGS)
    minutes = target_words // 150

    return "\n".join([
        "You dramatize podcast outlines into spoken banter for 'The Signal'.",
        "The outline already has the facts and chapter order. Your ONLY job is "
        "performance: convert talking points into natural back-and-forth dialogue.",
        "Do NOT invent new major facts. Do NOT reorder chapters. Do NOT drop "
        "required numbers/quotes from the outline — react to them.",
        "",
        f"TONE: {TONE_INSTRUCTIONS[style.tone.value]}",
        f"PACING: {PACING_INSTRUCTIONS[style.pacing.value]}",
        f"HUMOR: {HUMOR_INSTRUCTIONS[style.humor.value]}",
        "",
        "PERSONAS (opposing priors — this friction IS the banter):",
        *persona_lines,
        "",
        "FORMAT:",
        f"Dialogue between {' and '.join(speakers)}.",
        f"Every spoken line MUST start with [{speakers[0]}]: or [{speakers[1]}]:.",
        "Keep the outline's TITLE line and ### CHAPTER markers exactly "
        "(same titles and roles). No narration outside speaker tags.",
        "",
        "Each spoken line MUST end with a delivery tag:",
        f"[SPEAKER]: <spoken text> | delivery: <tag>",
        f"Allowed tags: {tags}",
        "Use interrupting on cut-off lines; amused/deadpan/pointed/skeptical/"
        "excited when the reaction has a clear emotional color; neutral/warm "
        "for explanatory beats.",
        "",
        "BANTER RULES (mechanical — follow all of them):",
        "- At least one genuine pushback or disagreement per chapter — not "
        "'yes, and' agreement theater. Pushback = a sharper question or a "
        "better number, not doom.",
        "- Ban stock transitions: never write 'that's a great point', "
        "'absolutely', 'exactly', 'so true', 'couldn't agree more', or "
        "'let's dive in'. Earn every reaction with something specific.",
        "- Ground reactions in an actual number, quote, or fact from the "
        "outline ('wait — two point eight trillion?') — not generic enthusiasm.",
        "- Include at least one interruption: a cut-off clause ending in an "
        "em dash (—).",
        "- Include at least one callback to something said earlier — warm "
        "recognition, not a gotcha.",
        "- Vary line length HARD: force some one-word or two-word retorts next "
        "to longer explanatory lines. Uniform line length is the tell of fake "
        "banter.",
        "",
        "SOUND HUMAN, NOT LIKE A THRILLER OR A ROBOT:",
        "- Talk like two sharp friends catching up on the news over coffee — "
        "curious, concrete, lightly skeptical. Warmth beats intensity.",
        "- Ban conspiratorial / cable-news stakes: no 'geopolitical strategy', "
        "'the real story they don't want you to know', 'nobody's talking about', "
        "'everything just changed forever', 'wake-up call for the West', or "
        "ominous 'if X rests on Y' framing unless the source literally says it.",
        "- Ban robotic tells: no stacked rhetorical setups ('look, the story "
        "here isn't just…'), no repeated 'here's the thing', no lecture cadence "
        "where one host dumps a paragraph and the other only reacts.",
        "- Prefer specific curiosity ('how did they train that?') over grand "
        "claims. Let the facts carry drama; hosts don't manufacture it.",
        "- Finish thoughts in complete spoken sentences. Interruptions are "
        "spice, not the whole meal.",
        "- Spell out speech: 'two point eight trillion', not '2.8T'; expand "
        "abbreviations the first time.",
        f"- Aim for ~{target_words} words (~{minutes} minutes) of dialogue total.",
        "",
        "Output ONLY the TITLE line, chapter markers, and tagged dialogue lines.",
    ])


def build_angles_prompt() -> str:
    return (
        "You plan podcast episodes. Given a topic and a numbered list of "
        "candidate articles, propose 2-4 DISTINCT episode directions — "
        "different editorial angles the episode could take, not restatements "
        "of the topic.\n"
        "Return STRICT JSON: an array of objects with exactly these keys:\n"
        '- "title": punchy 3-8 word episode angle\n'
        '- "description": one sentence on what this episode would explore\n'
        '- "article_indices": the 0-based indices of the 2-5 articles that '
        "genuinely support this direction\n"
        "Only use indices from the list. Return ONLY the JSON array."
    )


def build_enrichment_prompt() -> str:
    return (
        "Analyze the following article and return STRICT JSON with exactly these keys:\n"
        '- "summary": a 150-250 word plain-prose summary preserving specific numbers, '
        "quotes, and data points, covering key facts, core thesis, and implications\n"
        '- "topics": 3-6 short lowercase topic tags (e.g. "semiconductors", "ai chips")\n'
        '- "entities": companies, people, and products mentioned, up to 10\n'
        "Return ONLY the JSON object, no markdown fences, no other text."
    )
