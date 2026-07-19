"""The Signal's hosts — the same two people every episode.

Personas are first-class and persistent: the editorial register changes HOW
they talk about a topic, never WHO they are. Speaker keys must match the
script parser's tag regex (^[A-Z]+$).
"""

from __future__ import annotations

from pydantic import BaseModel

from models import VoiceSettings

# ElevenLabs voice catalog (name -> voice_id). Used for host defaults and
# exposed to clients for per-host overrides.
VOICES: dict[str, str] = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "drew": "29vD33N1CtxCmqQRPOHJ",
    "sarah": "EXAVITQu4vr4xnSDxMaL",
    "antoni": "ErXwobaYiN019PkySvjV",
    "josh": "TxGEqnHWrfWFTfGW9XjX",
    "arnold": "VR6AewLTigWG4xSOukaG",
    "adam": "pNInz6obpgDQGcFmaJgB",
    "sam": "yoZ06aMxZJJ28mfd3POQ",
    "gigi": "jBpfuIE2acCO8z3wKNLl",
}


class HostPersona(BaseModel):
    key: str  # speaker tag in scripts — must match ^[A-Z]+$
    name: str
    role: str  # one line: their job in the conversation
    background: str  # durable identity, carries across episodes
    signature_moves: list[str]  # habits the writer may use sparingly
    knowledge_areas: list[str]  # what they'd naturally know cold
    blind_spots: list[str]  # what they'd genuinely ask about
    voice_id: str
    voice_settings: VoiceSettings


MAYA = HostPersona(
    key="MAYA",
    name="Maya",
    role=(
        "The explainer — frames each story, keeps the thread, and lands the "
        "key numbers so the listener never gets lost."
    ),
    background=(
        "Former wire-service journalist who spent a decade turning messy "
        "breaking news into clean copy. Allergic to hype; loves a concrete "
        "number and a primary source. Warm but precise — she'd rather say "
        "'we don't know yet' than speculate."
    ),
    signature_moves=[
        "opens a story with the single most surprising fact",
        "translates jargon on the fly ('which in plain terms means…')",
        "gently fact-checks Dev with a better number",
    ],
    knowledge_areas=["journalism", "politics and policy", "media", "history"],
    blind_spots=["deep technical internals", "sports tactics"],
    voice_id=VOICES["rachel"],
    voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.8, style=0.4),
)

DEV = HostPersona(
    key="DEV",
    name="Dev",
    role=(
        "The skeptic — asks the question the listener is thinking, pokes at "
        "weak claims, and wanders into good tangents."
    ),
    background=(
        "Ex-software engineer turned professional generalist. Curious about "
        "everything, impressed by nothing until he understands the mechanism. "
        "Quick to laugh, quicker to say 'wait, how does that actually work?'. "
        "Keeps half-finished side projects and brings them up too often."
    ),
    signature_moves=[
        "interrupts with 'wait —' when a number sounds off",
        "reframes stories as systems ('so the incentive here is…')",
        "self-deprecating asides about his abandoned side projects",
    ],
    knowledge_areas=["software and hardware", "startups", "science", "games"],
    blind_spots=["financial market mechanics", "celebrity culture"],
    voice_id=VOICES["antoni"],
    voice_settings=VoiceSettings(stability=0.4, similarity_boost=0.75, style=0.5),
)

HOSTS: dict[str, HostPersona] = {p.key: p for p in (MAYA, DEV)}
HOST_KEYS: list[str] = list(HOSTS)


def persona_prompt_block(register: str) -> str:
    """The PERSONAS section for script prompts."""
    lines = [
        "THE HOSTS (the same two people every episode — never rename them):",
    ]
    for p in HOSTS.values():
        lines += [
            f"- {p.key} ({p.name}): {p.role}",
            f"  Background: {p.background}",
            f"  Habits (use sparingly, not every chapter): "
            + "; ".join(p.signature_moves),
            f"  Knows cold: {', '.join(p.knowledge_areas)}. "
            f"Genuinely asks about: {', '.join(p.blind_spots)}.",
        ]
    lines.append(
        "Today's register adjusts HOW they talk — never WHO they are. "
        "When the topic hits one host's blind spot, they ask; the other "
        "explains."
    )
    return "\n".join(lines)


def voice_for(speaker_key: str) -> tuple[str, VoiceSettings]:
    """Voice id + settings for a speaker tag; unknown tags get the first host."""
    persona = HOSTS.get(speaker_key) or next(iter(HOSTS.values()))
    return persona.voice_id, persona.voice_settings
