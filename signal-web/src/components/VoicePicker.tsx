import { useState } from 'react';
import type { Tone, VoiceInfo, SpeakerConfig, VoiceSettings } from '../types';

interface Props {
  tone: Tone;
  voices: VoiceInfo[];
  voiceConfig: Record<string, SpeakerConfig>;
  onChange: (config: Record<string, SpeakerConfig>) => void;
}

const defaultVoiceSettings: VoiceSettings = {
  stability: 0.4,
  similarity_boost: 0.75,
  style: 0.5,
  speed: 1.0,
  use_speaker_boost: true,
};

function getSpeakersForTone(tone: Tone): string[] {
  switch (tone) {
    case 'casual':
      return ['ALEX', 'JAMIE'];
    case 'polished':
    case 'technical':
      return ['HOST'];
    case 'debate':
      return ['BULL', 'BEAR'];
  }
}

const speakerColors: Record<string, string> = {
  ALEX: '#0a84ff',
  JAMIE: '#ff9500',
  HOST: '#0a84ff',
  BULL: '#34c759',
  BEAR: '#ff3b30',
};

export function VoicePicker({ tone, voices, voiceConfig, onChange }: Props) {
  const [expandedSpeaker, setExpandedSpeaker] = useState<string | null>(null);
  const speakers = getSpeakersForTone(tone);

  const getConfig = (speaker: string): SpeakerConfig => {
    return voiceConfig[speaker] || { voice_id: '', settings: { ...defaultVoiceSettings } };
  };

  const updateConfig = (speaker: string, updates: Partial<SpeakerConfig>) => {
    const current = getConfig(speaker);
    onChange({
      ...voiceConfig,
      [speaker]: { ...current, ...updates },
    });
  };

  const updateSettings = (speaker: string, key: keyof VoiceSettings, value: number | boolean) => {
    const current = getConfig(speaker);
    onChange({
      ...voiceConfig,
      [speaker]: {
        ...current,
        settings: { ...current.settings, [key]: value },
      },
    });
  };

  if (voices.length === 0) {
    return (
      <div className="bg-(--color-surface) rounded-xl p-4 border border-(--color-border)">
        <div className="flex items-center gap-2 text-(--color-text-muted)">
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
          <span>Loading voices...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-(--color-surface) rounded-xl p-4 border border-(--color-border) space-y-4">
      <h4 className="font-medium">Voice Selection</h4>

      {speakers.map((speaker) => {
        const config = getConfig(speaker);
        const isExpanded = expandedSpeaker === speaker;
        const color = speakerColors[speaker] || '#6b7280';

        return (
          <div key={speaker} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold" style={{ color }}>
                {speaker}
              </span>
              <button
                onClick={() => setExpandedSpeaker(isExpanded ? null : speaker)}
                className={`text-xs px-2 py-1 rounded transition ${
                  isExpanded
                    ? 'bg-(--color-accent)/20 text-(--color-accent)'
                    : 'text-(--color-text-muted) hover:text-(--color-text-secondary)'
                }`}
              >
                ⚙ Settings
              </button>
            </div>

            {/* Voice selection */}
            <div className="flex flex-wrap gap-2">
              {voices.map((voice) => {
                const isSelected = config.voice_id === voice.id;
                return (
                  <button
                    key={voice.id}
                    onClick={() => updateConfig(speaker, { voice_id: voice.id })}
                    className={`px-3 py-1.5 rounded-full text-sm transition border capitalize ${
                      isSelected
                        ? 'bg-(--color-accent)/20 border-(--color-accent) text-(--color-accent)'
                        : 'bg-transparent border-(--color-border) text-(--color-text-secondary) hover:border-(--color-text-muted)'
                    }`}
                  >
                    {voice.name}
                  </button>
                );
              })}
            </div>

            {/* Voice settings */}
            {isExpanded && (
              <div className="mt-3 pt-3 border-t border-(--color-border) space-y-3">
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-(--color-text-muted)">Stability</span>
                    <span className="font-mono">{Math.round(config.settings.stability * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={config.settings.stability}
                    onChange={(e) => updateSettings(speaker, 'stability', Number(e.target.value))}
                  />
                  <p className="text-xs text-(--color-text-muted) mt-0.5">Higher = more consistent</p>
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-(--color-text-muted)">Clarity</span>
                    <span className="font-mono">{Math.round(config.settings.similarity_boost * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={config.settings.similarity_boost}
                    onChange={(e) => updateSettings(speaker, 'similarity_boost', Number(e.target.value))}
                  />
                  <p className="text-xs text-(--color-text-muted) mt-0.5">Higher = clearer voice</p>
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-(--color-text-muted)">Style</span>
                    <span className="font-mono">{Math.round(config.settings.style * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={config.settings.style}
                    onChange={(e) => updateSettings(speaker, 'style', Number(e.target.value))}
                  />
                  <p className="text-xs text-(--color-text-muted) mt-0.5">Higher = more expressive</p>
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-(--color-text-muted)">Pace</span>
                    <span className="font-mono">{(config.settings.speed ?? 1).toFixed(2)}x</span>
                  </div>
                  <input
                    type="range"
                    min={0.7}
                    max={1.2}
                    step={0.05}
                    value={config.settings.speed ?? 1}
                    onChange={(e) => updateSettings(speaker, 'speed', Number(e.target.value))}
                  />
                  <p className="text-xs text-(--color-text-muted) mt-0.5">Conversational is ~1.0x</p>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
