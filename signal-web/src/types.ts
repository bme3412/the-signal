// Editorial — the backend classifies the topic and decides how the
// episode sounds; there are no user-facing style knobs anymore.
export interface EditorialDecision {
  topic_category: string;
  register: string;
  chosen_angle: string;
  framing_note: string | null;
  rationale: string;
}

export interface LintFlag {
  rule: string;
  severity: 'warn' | 'revise' | string;
  detail: string;
  segment_index: number | null;
}

export interface LintReport {
  flags: LintFlag[];
  revised: boolean;
}

// Voice settings
export interface VoiceSettings {
  stability: number;
  similarity_boost: number;
  style: number;
  speed: number;
  use_speaker_boost: boolean;
}

export interface SpeakerConfig {
  voice_id: string;
  settings: VoiceSettings;
}

export interface VoiceInfo {
  id: string;
  name: string;
}

export interface HostInfo {
  name: string;
  role: string;
  voice_id: string;
}

export interface VoicesResponse {
  voices: VoiceInfo[];
  hosts: Record<string, HostInfo>;
  defaults: Record<string, Record<string, string>>;
  settings_ranges: {
    stability: { min: number; max: number; default: number };
    similarity_boost: { min: number; max: number; default: number };
    style: { min: number; max: number; default: number };
  };
}

// Audio production. Inter-turn gaps are variable (short after reactions,
// long at chapter shifts) — these are the base values.
export interface AudioProductionConfig {
  gap_short_ms?: number;
  gap_medium_ms?: number;
  gap_chapter_ms?: number;
  fade_in_ms: number;
  fade_out_ms: number;
  normalize: boolean;
  target_dbfs: number;
  intro_music: boolean;
}

export const defaultAudioConfig: AudioProductionConfig = {
  fade_in_ms: 0,
  fade_out_ms: 0,
  normalize: false,
  target_dbfs: -16.0,
  intro_music: false,
};

// Article
export interface Article {
  id: string;
  title: string;
  source: string;
  url: string | null;
  text: string;
  summary: string | null;
  topics: string[];
  entities: string[];
  collection: string | null;
  word_count: number;
  created_at: string;
}

// Discovery
export interface DiscoverResult {
  title: string;
  url: string;
  description: string;
  source: string;
  in_queue: boolean;
}

export interface EpisodeAngle {
  title: string;
  description: string;
  article_indices: number[];
}

// Episode
export type EpisodeStatus = 'queued' | 'summarizing' | 'scripting' | 'synthesizing' | 'mixing' | 'ready' | 'failed';

export interface ScriptSegment {
  speaker: string;
  text: string;
  delivery?: string | null;
  char_count: number;
  duration_seconds: number;
}

export type ChapterRole = 'intro' | 'core' | 'optional' | 'closer';

export interface Chapter {
  title: string;
  role: ChapterRole;
  segment_indices: number[];
  audio_url: string | null;
  duration_seconds: number;
  start_seconds: number;
}

export interface EpisodeScript {
  raw_text: string;
  segments: ScriptSegment[];
  chapters: Chapter[];
  word_count: number;
  estimated_minutes: number;
}

export interface ManifestChapter {
  index: number;
  title: string;
  role: ChapterRole;
  audio_url: string | null;
  duration_seconds: number;
  start_seconds: number;
  segments: ScriptSegment[];
}

export interface EpisodeManifest {
  episode_id: string;
  title: string | null;
  status: EpisodeStatus;
  total_duration_seconds: number;
  chapters: ManifestChapter[];
}

export interface PipelineMetrics {
  summarize_time_ms: number;
  script_time_ms: number;
  tts_time_ms: number;
  mix_time_ms: number;
  total_time_ms: number;
  script_tokens_in: number;
  script_tokens_out: number;
  tts_characters: number;
  estimated_cost_usd: number;
}

export interface ProgressEvent {
  stage: EpisodeStatus;
  message: string;
  at: string;
}

export interface EpisodeLink {
  label: string;
  title: string;
  url: string;
  source: string;
  snippet: string;
  kind: 'source' | 'context' | string;
}

export interface Episode {
  id: string;
  title: string | null;
  focus: string | null;
  status: EpisodeStatus;
  progress?: ProgressEvent[];
  editorial?: EditorialDecision | null;
  lint?: LintReport | null;
  article_ids: string[];
  script: EpisodeScript | null;
  links?: EpisodeLink[];
  audio_url: string | null;
  audio_duration_seconds: number | null;
  metrics: PipelineMetrics | null;
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface EpisodeRequest {
  article_ids: string[];
  focus?: string;
  voice_mapping?: Record<string, string>;
  voice_config?: Record<string, SpeakerConfig>;
  audio_config: AudioProductionConfig;
  target_minutes: number;
}
