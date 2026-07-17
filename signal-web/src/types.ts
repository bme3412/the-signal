// Style dimensions
export type Depth = 'briefing' | 'deep_dive' | 'synthesis';
export type Tone = 'casual' | 'polished' | 'debate' | 'technical';
export type Lens = 'investor' | 'engineer' | 'macro' | 'general';
export type Pacing = 'rapid' | 'measured' | 'variable';
export type Humor = 'serious' | 'dry' | 'playful' | 'roast';
export type Audience = 'insider' | 'informed' | 'curious';
export type Structure = 'narrative' | 'ranked' | 'thematic' | 'contrarian';
export type Closer = 'actionable' | 'philosophical' | 'prediction' | 'question';

export interface StyleConfig {
  depth: Depth;
  tone: Tone;
  lens: Lens;
  pacing: Pacing;
  humor: Humor;
  audience: Audience;
  structure: Structure;
  closer: Closer;
}

export const defaultStyleConfig: StyleConfig = {
  depth: 'briefing',
  tone: 'casual',
  lens: 'investor',
  pacing: 'variable',
  humor: 'dry',
  audience: 'informed',
  structure: 'ranked',
  closer: 'actionable',
};

// Voice settings
export interface VoiceSettings {
  stability: number;
  similarity_boost: number;
  style: number;
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

export interface VoicesResponse {
  voices: VoiceInfo[];
  defaults: Record<string, Record<string, string>>;
  settings_ranges: {
    stability: { min: number; max: number; default: number };
    similarity_boost: { min: number; max: number; default: number };
    style: { min: number; max: number; default: number };
  };
}

// Audio production
export interface AudioProductionConfig {
  silence_duration_ms: number;
  fade_in_ms: number;
  fade_out_ms: number;
  normalize: boolean;
  target_dbfs: number;
}

export const defaultAudioConfig: AudioProductionConfig = {
  silence_duration_ms: 300,
  fade_in_ms: 0,
  fade_out_ms: 0,
  normalize: false,
  target_dbfs: -16.0,
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

export interface Episode {
  id: string;
  title: string | null;
  focus: string | null;
  status: EpisodeStatus;
  progress?: ProgressEvent[];
  style: StyleConfig;
  article_ids: string[];
  script: EpisodeScript | null;
  audio_url: string | null;
  audio_duration_seconds: number | null;
  metrics: PipelineMetrics | null;
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface EpisodeRequest {
  article_ids: string[];
  style: StyleConfig;
  focus?: string;
  voice_mapping?: Record<string, string>;
  voice_config?: Record<string, SpeakerConfig>;
  audio_config: AudioProductionConfig;
  target_minutes: number;
}

// Presets
export interface StylePreset {
  id: string;
  name: string;
  subtitle: string;
  icon: string;
  gradient: [string, string];
  config: StyleConfig;
}

export const builtInPresets: StylePreset[] = [
  {
    id: 'morning',
    name: 'Morning Brief',
    subtitle: 'Fast, polished, investor-grade',
    icon: '🌅',
    gradient: ['#0a84ff', '#00c7be'],
    config: {
      depth: 'briefing', tone: 'polished', lens: 'investor',
      pacing: 'rapid', humor: 'serious', audience: 'insider',
      structure: 'ranked', closer: 'actionable',
    },
  },
  {
    id: 'deep',
    name: 'Deep Cut',
    subtitle: 'Technical deep-dive, measured pace',
    icon: '🔍',
    gradient: ['#bf5af2', '#5856d6'],
    config: {
      depth: 'deep_dive', tone: 'technical', lens: 'engineer',
      pacing: 'measured', humor: 'dry', audience: 'insider',
      structure: 'narrative', closer: 'prediction',
    },
  },
  {
    id: 'hot',
    name: 'Hot Take',
    subtitle: 'Debate format, sharp opinions',
    icon: '🔥',
    gradient: ['#ff3b30', '#ff9500'],
    config: {
      depth: 'synthesis', tone: 'debate', lens: 'investor',
      pacing: 'variable', humor: 'roast', audience: 'informed',
      structure: 'contrarian', closer: 'prediction',
    },
  },
  {
    id: 'explain',
    name: 'Explain It',
    subtitle: 'Casual, curious, big picture',
    icon: '💡',
    gradient: ['#ffcc00', '#34c759'],
    config: {
      depth: 'synthesis', tone: 'casual', lens: 'general',
      pacing: 'variable', humor: 'playful', audience: 'curious',
      structure: 'thematic', closer: 'question',
    },
  },
];

// Dimension metadata
export const dimensionMeta = {
  depth: {
    label: 'Depth',
    options: [
      { value: 'briefing', label: 'Briefing', desc: 'Hit every story, keep it moving' },
      { value: 'deep_dive', label: 'Deep Dive', desc: 'Go deep on what matters most' },
      { value: 'synthesis', label: 'Synthesis', desc: 'Find the thread across stories' },
    ],
  },
  tone: {
    label: 'Tone',
    options: [
      { value: 'casual', label: 'Casual', desc: 'Two hosts, natural banter' },
      { value: 'polished', label: 'Polished', desc: 'NPR-quality solo narrator' },
      { value: 'debate', label: 'Debate', desc: 'Bull vs Bear, opposing views' },
      { value: 'technical', label: 'Technical', desc: 'Precise deep-dive analysis' },
    ],
  },
  lens: {
    label: 'Lens',
    options: [
      { value: 'investor', label: 'Investor', desc: 'Revenue, TAM, valuation' },
      { value: 'engineer', label: 'Engineer', desc: 'Architecture, moats, tradeoffs' },
      { value: 'macro', label: 'Macro', desc: 'Policy, supply chains, trends' },
      { value: 'general', label: 'General', desc: 'Why it matters to everyone' },
    ],
  },
  pacing: {
    label: 'Pacing',
    options: [
      { value: 'rapid', label: 'Rapid', desc: 'High energy, punchy' },
      { value: 'measured', label: 'Measured', desc: 'Let ideas breathe' },
      { value: 'variable', label: 'Variable', desc: 'Fast facts, slow analysis' },
    ],
  },
  humor: {
    label: 'Humor',
    options: [
      { value: 'serious', label: 'Serious', desc: 'Content is the entertainment' },
      { value: 'dry', label: 'Dry', desc: 'Deadpan, note the ironies' },
      { value: 'playful', label: 'Playful', desc: 'Analogies, pop culture refs' },
      { value: 'roast', label: 'Roast', desc: 'Sharp, opinionated takes' },
    ],
  },
  audience: {
    label: 'Audience',
    options: [
      { value: 'insider', label: 'Insider', desc: 'Skip the basics, use shorthand' },
      { value: 'informed', label: 'Informed', desc: 'Brief framing, one line max' },
      { value: 'curious', label: 'Curious', desc: 'Define terms naturally' },
    ],
  },
  structure: {
    label: 'Structure',
    options: [
      { value: 'narrative', label: 'Narrative', desc: 'Story arc to climactic insight' },
      { value: 'ranked', label: 'Ranked', desc: 'Biggest story first' },
      { value: 'thematic', label: 'Thematic', desc: 'Group by theme, not article' },
      { value: 'contrarian', label: 'Contrarian', desc: 'What everyone gets wrong' },
    ],
  },
  closer: {
    label: 'Closer',
    options: [
      { value: 'actionable', label: 'Actionable', desc: '2-3 specific action items' },
      { value: 'philosophical', label: 'Philosophical', desc: 'Decade-level implications' },
      { value: 'prediction', label: 'Prediction', desc: 'Bold, falsifiable prediction' },
      { value: 'question', label: 'Question', desc: 'Open question to ponder' },
    ],
  },
} as const;
