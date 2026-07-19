from __future__ import annotations

from models import EditorialDecision, REGISTERS, TOPIC_CATEGORIES
from personas import HOST_KEYS, persona_prompt_block

# --------------- Register instructions ---------------
# How the hosts should talk about THIS topic — chosen by the editorial
# classifier from the content, never by pipeline config.

REGISTER_INSTRUCTIONS: dict[str, str] = {
    "conversational": (
        "Relaxed and curious — two sharp friends catching up on a story "
        "they both find interesting. Plain language, real reactions."
    ),
    "analytical": (
        "Precise and evidence-first — the hosts care about getting the "
        "numbers and mechanisms right, but stay conversational, never "
        "lecture-y."
    ),
    "playful": (
        "Light and fun — the story has joy or absurdity in it and the "
        "hosts are allowed to enjoy it. Vivid comparisons, gentle teasing."
    ),
    "solemn": (
        "Measured and respectful — the story involves real harm or loss. "
        "No jokes, no hype; careful language and room to breathe."
    ),
}

# Per-line beat labels. Downstream they drive inter-turn gap timing (short
# after reactions/interruptions, longer at transitions) and the naturalness
# lint — expressiveness itself comes from inline audio tags on v3.
DELIVERY_TAGS = (
    "neutral",       # default explanatory beat
    "reaction",      # short reactive beat ("Huh." / "Wait, really?")
    "interrupting",  # cuts the other host off (line ends in an em dash)
    "question",      # genuine question the other host answers
    "thoughtful",    # slower, considering
    "transition",    # shifting to a new thread or chapter
    "closer-beat",   # wrap-up lines
)

# Inline performance tags ElevenLabs v3 renders as actual delivery.
AUDIO_TAGS = (
    "[laughs]",
    "[chuckles]",
    "[sighs]",
    "[curious]",
    "[skeptical]",
    "[excited]",
    "[whispers]",
    "[pause]",
)


# --------------- Prompt builders ---------------


def build_editorial_prompt() -> str:
    """Classify the episode's content and decide how it should sound."""
    categories = ", ".join(TOPIC_CATEGORIES)
    registers = ", ".join(REGISTERS)
    return (
        "You are the editor of a two-host news podcast. Given enriched "
        "articles (and an optional listener focus), decide how this episode "
        "should sound. The hosts stay the same people every episode — you "
        "only pick how they approach THIS topic.\n\n"
        "Return STRICT JSON with exactly these keys:\n"
        f'- "topic_category": one of [{categories}]\n'
        f'- "register": one of [{registers}]. Default "conversational". '
        '"analytical" only when precision genuinely serves the listener; '
        '"playful" when the story has real fun in it; "solemn" only for '
        "stories involving death, disaster, or serious harm.\n"
        '- "chosen_angle": one sentence — the single most interesting '
        "through-line across the articles. If a listener focus is provided, "
        "the angle must serve it.\n"
        '- "framing_note": null unless the story itself demands special '
        "vocabulary. An earnings report may warrant investor framing "
        "(revenue, margins, guidance). A World Cup match must NOT get "
        "financial framing. A protocol deep-dive may warrant engineering "
        "framing. When in doubt: null.\n"
        '- "rationale": one sentence on why you chose this — it gets logged '
        "for the show's producer.\n"
        "Return ONLY the JSON object, no markdown fences, no other text."
    )


def _framing_line(editorial: EditorialDecision) -> str:
    if editorial.framing_note:
        return f"FRAMING: {editorial.framing_note}"
    return (
        "FRAMING: neutral — explain why the story matters in plain terms. "
        "No specialist vocabulary (financial, engineering, or otherwise) "
        "unless a source quote uses it."
    )


def build_outline_prompt(
    editorial: EditorialDecision, target_words: int = 4500
) -> str:
    """Pass 1: content-only outline — no dialogue, no personas."""
    minutes = target_words // 150
    return "\n".join([
        "You plan podcast episode outlines for 'The Signal'.",
        "Your ONLY job is content: facts, order, and chapter structure.",
        "Do NOT write dialogue. Do NOT invent host names or banter.",
        "Do NOT write spoken lines. Plain talking points only.",
        "",
        f"ANGLE: {editorial.chosen_angle or 'the strongest through-line across the articles'}",
        f"REGISTER: {REGISTER_INSTRUCTIONS.get(editorial.register, REGISTER_INSTRUCTIONS['conversational'])}",
        _framing_line(editorial),
        "",
        "ORDERING: lead with the biggest story unless the angle implies a "
        "narrative arc. Give each article brief one-sentence context; go "
        "deeper only where the material earns it.",
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
        "- Final chapter: a forward-looking closer — what to watch for next, "
        "marked [closer]",
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


def build_banter_prompt(
    editorial: EditorialDecision,
    target_words: int = 4500,
    use_audio_tags: bool = False,
) -> str:
    """Pass 2: turn an outline into the transcript of a real conversation."""
    tags = ", ".join(DELIVERY_TAGS)
    minutes = target_words // 150
    a, b = HOST_KEYS[0], HOST_KEYS[1]

    sections = [
        "You are transcribing a real conversation between two people who "
        "host a show together and genuinely like each other. You are not "
        f"'writing dialogue' — you are capturing how {a} and {b} actually "
        "talk when the mics are on.",
        "The outline already has the facts and chapter order. Your ONLY job "
        "is the conversation: how these two people would really work through "
        "this material together.",
        "Do NOT invent new major facts. Do NOT reorder chapters. Do NOT drop "
        "required numbers/quotes from the outline — react to them.",
        "",
        f"REGISTER: {REGISTER_INSTRUCTIONS.get(editorial.register, REGISTER_INSTRUCTIONS['conversational'])}",
        _framing_line(editorial),
        "",
        persona_prompt_block(editorial.register),
        "",
        "FORMAT:",
        f"Every spoken line MUST start with [{a}]: or [{b}]:.",
        "Keep the outline's TITLE line and ### CHAPTER markers exactly "
        "(same titles and roles). No narration outside speaker tags.",
        "Each spoken line MUST end with a beat tag:",
        "[SPEAKER]: <spoken text> | delivery: <tag>",
        f"Allowed tags: {tags}",
        "reaction = a short reactive beat; interrupting = cutting the other "
        "off (line ends in an em dash); question = a genuine question the "
        "other answers; thoughtful = slower, considering; transition = "
        "shifting threads; closer-beat = wrap-up lines; neutral = everything "
        "else.",
        "",
        "CONVERSATION SHAPE (all mechanical — follow all of them):",
        "- Vary turn length HARD. Put one-to-five-word reactions ('Huh.' / "
        "'Okay, wait.' / 'That's so many.') next to sixty-to-eighty-word "
        "explanations. Never three consecutive turns of similar length.",
        "- At least one genuine question per chapter — one host actually "
        "doesn't know the answer, and the other actually answers it. Use "
        "their blind spots: when the topic hits one, they ask.",
        "- At least one light disagreement or bit of teasing per episode, "
        "resolved by a fact or a concession — not by folding instantly.",
        "- At least one genuine pushback per chapter — a sharper question or "
        "a better number, not doom, and not 'yes, and' agreement theater.",
        "- Include at least one interruption: a cut-off clause ending in an "
        "em dash (—), tagged interrupting.",
        "- Include at least one callback to something said earlier — warm "
        "recognition, not a gotcha.",
        "- Transitions are conversational ('okay, but the thing I actually "
        "wanted to ask you about—'), never 'moving on to our next story'.",
        "- Ground reactions in an actual number, quote, or fact from the "
        "outline ('wait — two point eight trillion?') — never generic "
        "enthusiasm.",
        "- The intro is the two of them starting to talk, not a template "
        "('Welcome back to…'). The outro is them running out of road on the "
        "topic, plus what they're watching next.",
        "",
        "SOUND HUMAN, NOT LIKE A THRILLER OR A ROBOT:",
        "- Talk like two sharp friends catching up on the news over coffee — "
        "curious, concrete, lightly skeptical. Warmth beats intensity.",
        "- Ban stock phrases: 'that's a great point', 'absolutely', "
        "'exactly', 'so true', 'couldn't agree more', 'let's dive in', "
        "'buckle up', 'without further ado'.",
        "- Ban conspiratorial / cable-news stakes: no 'the real story they "
        "don't want you to know', 'nobody's talking about', 'everything just "
        "changed forever', 'wake-up call for the West', or ominous framing "
        "unless the source literally says it.",
        "- Ban robotic tells: no stacked rhetorical setups ('look, the story "
        "here isn't just…'), no repeated 'here's the thing', no lecture "
        "cadence where one host dumps a paragraph and the other only reacts.",
        "- Prefer specific curiosity ('how did they train that?') over grand "
        "claims. Let the facts carry drama; hosts don't manufacture it.",
        "- Finish thoughts in complete spoken sentences. Interruptions are "
        "spice, not the whole meal.",
        "",
        "WRITE FOR THE EAR, NOT THE EYE:",
        "- Every sentence must pass the read-aloud test: if you said it to a "
        "friend, would it sound like talking or like an essay? Contractions "
        "always; short clauses; no essay-paragraph structure.",
        "- A voice model reads a period as a full stop, so strings of "
        "fragments ('Sunday. Three p.m. East Rutherford.') come out clipped "
        "and robotic — write flowing spoken sentences instead.",
        "- Vary sentence length. Mix short punchy lines with longer, winding "
        "ones — that rhythm is what makes speech sound alive.",
        "- Spell out speech: 'two point eight trillion', not '2.8T'; 'two to "
        "nothing', not '2-0'; 'ninety-sixth minute', not '96th'. Expand "
        "abbreviations the first time.",
        f"- Aim for ~{target_words} words (~{minutes} minutes) of dialogue "
        "total.",
    ]

    if use_audio_tags:
        sections += [
            "",
            "AUDIO TAGS (rendered as real delivery by the voice model):",
            "Sprinkle an inline performance tag where a human would audibly "
            f"react: {', '.join(AUDIO_TAGS)}.",
            f"Example: [{b}]: [laughs] Wait — two point eight trillion? "
            "| delivery: reaction",
            "A tag colors the words right after it. At most ONE tag per "
            "line; most lines have NONE. Never stack tags, never use a tag "
            "as the whole line.",
        ]

    sections += [
        "",
        "Output ONLY the TITLE line, chapter markers, and tagged dialogue "
        "lines.",
    ]
    return "\n".join(sections)


def build_revision_prompt(flag_details: list[str]) -> str:
    """One bounded script-doctor pass over a linted script."""
    numbered = [f"{i}. {d}" for i, d in enumerate(flag_details, 1)]
    return "\n".join([
        "You are a script doctor for a two-host podcast. The script below "
        "failed a naturalness check. Fix ONLY the flagged problems.",
        "",
        "PROBLEMS TO FIX:",
        *numbered,
        "",
        "RULES:",
        "- Preserve the TITLE line (if present) and every ### CHAPTER marker "
        "exactly — same titles, same roles, same order.",
        f"- Keep the line format: [{HOST_KEYS[0]}]: or [{HOST_KEYS[1]}]: "
        "prefix, '| delivery: <tag>' suffix on every spoken line.",
        "- Keep all facts, numbers, and quotes. Keep roughly the same length.",
        "- Do NOT rewrite lines that aren't implicated by a flag.",
        "- Output the FULL corrected script in the identical format — no "
        "commentary, no diff, no explanations.",
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
