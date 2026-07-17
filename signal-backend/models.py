from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


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


# --------------- Style ---------------

class StyleConfig(BaseModel):
    depth: Depth = Depth.briefing
    tone: Tone = Tone.casual
    lens: Lens = Lens.investor
    pacing: Pacing = Pacing.variable
    humor: Humor = Humor.dry
    audience: Audience = Audience.informed
    structure: Structure = Structure.ranked
    closer: Closer = Closer.actionable


# --------------- Voice Settings ---------------

class VoiceSettings(BaseModel):
    """Per-voice ElevenLabs settings."""

    stability: float = Field(0.5, ge=0.0, le=1.0)
    similarity_boost: float = Field(0.75, ge=0.0, le=1.0)
    style: float = Field(0.4, ge=0.0, le=1.0)
    use_speaker_boost: bool = True


class SpeakerConfig(BaseModel):
    """Voice assignment and settings for a speaker."""

    voice_id: str
    settings: VoiceSettings = Field(default_factory=VoiceSettings)


# --------------- Audio Production ---------------

class AudioProductionConfig(BaseModel):
    """Audio mixing settings."""

    silence_duration_ms: int = Field(300, ge=100, le=1000)
    fade_in_ms: int = Field(0, ge=0, le=500)
    fade_out_ms: int = Field(0, ge=0, le=500)
    normalize: bool = False
    target_dbfs: float = Field(-16.0, ge=-30.0, le=-6.0)


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

class Episode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str | None = None
    status: EpisodeStatus = EpisodeStatus.queued
    style: StyleConfig = Field(default_factory=StyleConfig)
    article_ids: list[str] = Field(default_factory=list)
    script: EpisodeScript | None = None
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
    article_ids: list[str] = Field(..., min_length=1, max_length=10)
    style: StyleConfig = Field(default_factory=StyleConfig)
    voice_mapping: dict[str, str] | None = None  # Legacy: simple voice ID mapping
    voice_config: dict[str, SpeakerConfig] | None = None  # New: full voice configuration
    audio_config: AudioProductionConfig = Field(default_factory=AudioProductionConfig)
    target_minutes: int = 20
