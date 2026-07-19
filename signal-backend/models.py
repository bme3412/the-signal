from __future__ import annotations

import warnings
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


# --------------- LEGACY wire-compat ---------------
# TODO(ios-compat): the iOS client decodes Episode.style as a non-optional
# StyleConfig with these exact enum values. Style no longer influences
# generation — the editorial classifier (EditorialDecision) decides framing
# from the content. Delete this whole block once iOS ships without StyleConfig.

class Depth(str, Enum):
    briefing = "briefing"
    deep_dive = "deep_dive"
    synthesis = "synthesis"


class Tone(str, Enum):
    casual = "casual"
    polished = "polished"
    debate = "debate"
    technical = "technical"


class Lens(str, Enum):
    investor = "investor"
    engineer = "engineer"
    macro = "macro"
    general = "general"


class Pacing(str, Enum):
    rapid = "rapid"
    measured = "measured"
    variable = "variable"


class Humor(str, Enum):
    serious = "serious"
    dry = "dry"
    playful = "playful"
    roast = "roast"


class Audience(str, Enum):
    insider = "insider"
    informed = "informed"
    curious = "curious"


class Structure(str, Enum):
    narrative = "narrative"
    ranked = "ranked"
    thematic = "thematic"
    contrarian = "contrarian"


class Closer(str, Enum):
    actionable = "actionable"
    philosophical = "philosophical"
    prediction = "prediction"
    question = "question"


class EpisodeStatus(str, Enum):
    queued = "queued"
    summarizing = "summarizing"
    scripting = "scripting"
    synthesizing = "synthesizing"
    mixing = "mixing"
    ready = "ready"
    failed = "failed"


class StyleConfig(BaseModel):
    depth: Depth = Depth.briefing
    tone: Tone = Tone.casual
    lens: Lens = Lens.investor
    pacing: Pacing = Pacing.variable
    humor: Humor = Humor.dry
    audience: Audience = Audience.informed
    structure: Structure = Structure.ranked
    closer: Closer = Closer.actionable

# --------------- end LEGACY wire-compat ---------------


# --------------- Editorial ---------------

TOPIC_CATEGORIES = (
    "finance_markets",
    "tech",
    "science",
    "sports",
    "politics_policy",
    "culture",
    "health",
    "general",
)

REGISTERS = ("conversational", "analytical", "playful", "solemn")


# "register" shadows an internal (non-field) BaseModel function; the field
# behaves normally, so silence pydantic's shadow warning for this class.
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message='Field name "register"')

    class EditorialDecision(BaseModel):
        """How this episode should sound — derived from content, not config.

        Produced by the editorial classifier after enrichment, stored on the
        episode so the call is inspectable and loggable.
        """

        topic_category: str = "general"
        register: str = "conversational"
        chosen_angle: str = ""  # one-sentence editorial spine of the episode
        # Special vocabulary ONLY when the story demands it (e.g. an earnings
        # report warrants investor terms). None = neutral, plain-terms framing.
        framing_note: str | None = None
        rationale: str = ""


# --------------- Naturalness lint ---------------

class LintFlag(BaseModel):
    rule: str
    severity: str = "warn"  # warn | revise (revise triggers one rewrite pass)
    detail: str
    segment_index: int | None = None


class LintReport(BaseModel):
    flags: list[LintFlag] = Field(default_factory=list)
    revised: bool = False  # a revision pass ran (regardless of outcome)

    @property
    def needs_revision(self) -> bool:
        return any(f.severity == "revise" for f in self.flags)


# --------------- Voice Settings ---------------

class VoiceSettings(BaseModel):
    """Per-voice ElevenLabs settings.

    Defaults are tuned for warm, natural podcast delivery: lower stability
    gives the voice emotional range (higher = flatter/robotic), and speed 1.0
    is normal conversational pace (0.7–1.2 supported).
    """

    stability: float = Field(0.4, ge=0.0, le=1.0)
    similarity_boost: float = Field(0.75, ge=0.0, le=1.0)
    style: float = Field(0.5, ge=0.0, le=1.0)
    speed: float = Field(1.0, ge=0.7, le=1.2)
    use_speaker_boost: bool = True


class SpeakerConfig(BaseModel):
    """Voice assignment and settings for a speaker."""

    voice_id: str
    settings: VoiceSettings = Field(default_factory=VoiceSettings)


# --------------- Audio Production ---------------

class AudioProductionConfig(BaseModel):
    """Audio mixing settings.

    Inter-turn silence is variable: short after reactions/interruptions,
    medium by default, long at chapter boundaries — fixed gaps are one of
    the strongest robotic tells.
    """

    # DEPRECATED: old clients' single fixed gap. If a client explicitly sends
    # a value, it becomes the medium gap (see effective_medium_ms).
    silence_duration_ms: int = Field(300, ge=100, le=1000)
    gap_short_ms: int = Field(120, ge=0, le=1000)
    gap_medium_ms: int = Field(250, ge=50, le=1000)
    gap_chapter_ms: int = Field(600, ge=100, le=2000)
    fade_in_ms: int = Field(0, ge=0, le=500)
    fade_out_ms: int = Field(0, ge=0, le=500)
    normalize: bool = False
    target_dbfs: float = Field(-16.0, ge=-30.0, le=-6.0)
    intro_music: bool = False  # prepend a music theme sting to the episode

    def effective_medium_ms(self) -> int:
        """Honor a legacy client's explicit silence_duration_ms."""
        if (
            "silence_duration_ms" in self.model_fields_set
            and "gap_medium_ms" not in self.model_fields_set
        ):
            return self.silence_duration_ms
        return self.gap_medium_ms


# --------------- Article ---------------

class Article(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    source: str
    url: str | None = None
    text: str
    summary: str | None = None
    topics: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    collection: str | None = None  # e.g. the discovery topic that found it
    word_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ArticleCreate(BaseModel):
    url: str | None = None
    title: str | None = None
    text: str | None = None
    source: str | None = None
    collection: str | None = None


class DiscoverRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    limit: int = Field(8, ge=1, le=20)
    recency: str = "week"  # day | week | month | any


class DiscoverResult(BaseModel):
    title: str
    url: str
    description: str = ""
    source: str = ""
    in_queue: bool = False


class AnglesRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    results: list[DiscoverResult] = Field(..., min_length=2, max_length=20)


class EpisodeAngle(BaseModel):
    title: str
    description: str = ""
    article_indices: list[int]


# --------------- Script ---------------

class ChapterRole(str, Enum):
    intro = "intro"
    core = "core"
    optional = "optional"
    closer = "closer"


class ScriptSegment(BaseModel):
    speaker: str
    text: str
    delivery: str | None = None  # interrupting | amused | deadpan | ...
    char_count: int = 0
    duration_seconds: float = 0.0


class Chapter(BaseModel):
    """A coherent block of the episode — the unit an adaptive player can
    skip (role=optional) or must keep (intro/core/closer)."""

    title: str
    role: ChapterRole = ChapterRole.core
    segment_indices: list[int] = Field(default_factory=list)
    audio_url: str | None = None
    duration_seconds: float = 0.0
    start_seconds: float = 0.0


class EpisodeScript(BaseModel):
    raw_text: str
    segments: list[ScriptSegment]
    chapters: list[Chapter] = Field(default_factory=list)
    word_count: int = 0
    estimated_minutes: float = 0.0


# --------------- Pipeline Metrics ---------------

class PipelineMetrics(BaseModel):
    summarize_time_ms: float = 0
    script_time_ms: float = 0
    tts_time_ms: float = 0
    mix_time_ms: float = 0
    total_time_ms: float = 0
    script_tokens_in: int = 0
    script_tokens_out: int = 0
    tts_characters: int = 0
    estimated_cost_usd: float = 0.0


# --------------- Episode ---------------

class ProgressEvent(BaseModel):
    stage: EpisodeStatus
    message: str
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EpisodeLink(BaseModel):
    """A curated URL that supports something said in the episode.

    kind=source — one of the queued articles used to write the show
    kind=context — web result found for an entity/topic the hosts discuss
    """

    label: str  # entity or short topic this link is about
    title: str
    url: str
    source: str = ""  # hostname
    snippet: str = ""
    kind: str = "context"  # source | context


class Episode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str | None = None
    focus: str | None = None  # editorial direction the script was steered by
    status: EpisodeStatus = EpisodeStatus.queued
    progress: list[ProgressEvent] = Field(default_factory=list)
    # LEGACY shim — see StyleConfig block. Always the defaults; ignored.
    style: StyleConfig = Field(default_factory=StyleConfig)
    editorial: EditorialDecision | None = None
    lint: LintReport | None = None
    article_ids: list[str] = Field(default_factory=list)
    script: EpisodeScript | None = None
    links: list[EpisodeLink] = Field(default_factory=list)
    audio_url: str | None = None
    audio_duration_seconds: float | None = None
    metrics: PipelineMetrics | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class ManifestChapter(BaseModel):
    index: int
    title: str
    role: ChapterRole
    audio_url: str | None
    duration_seconds: float
    start_seconds: float
    segments: list[ScriptSegment]


class EpisodeManifest(BaseModel):
    """Per-chapter audio map for adaptive playback: play chapters in order,
    drop or keep 'optional' ones to fit the listener's remaining time, always
    end on the 'closer'."""

    episode_id: str
    title: str | None = None
    status: EpisodeStatus
    total_duration_seconds: float
    chapters: list[ManifestChapter]


class EpisodeRequest(BaseModel):
    # Old clients may still send a "style" object — pydantic ignores extras.
    article_ids: list[str] = Field(..., min_length=1, max_length=10)
    focus: str | None = Field(None, max_length=300)
    voice_mapping: dict[str, str] | None = None  # Legacy: simple voice ID mapping
    voice_config: dict[str, SpeakerConfig] | None = None  # New: full voice configuration
    audio_config: AudioProductionConfig = Field(default_factory=AudioProductionConfig)
    target_minutes: int = 20
