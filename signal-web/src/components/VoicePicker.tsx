import type { HostInfo, VoiceInfo, SpeakerConfig, VoiceSettings } from '../types';

interface Props {
  hosts: Record<string, HostInfo>;
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

/** Friendly delivery presets — map to the technical ElevenLabs knobs. */
const DELIVERY_PRESETS: {
  id: string;
  label: string;
  hint: string;
  settings: Pick<VoiceSettings, 'stability' | 'style' | 'similarity_boost'>;
}[] = [
  {
    id: 'natural',
    label: 'Natural',
    hint: 'Balanced',
    settings: { stability: 0.4, style: 0.5, similarity_boost: 0.75 },
  },
  {
    id: 'expressive',
    label: 'Expressive',
    hint: 'More range',
    settings: { stability: 0.25, style: 0.7, similarity_boost: 0.7 },
  },
  {
    id: 'steady',
    label: 'Steady',
    hint: 'Even tone',
    settings: { stability: 0.65, style: 0.3, similarity_boost: 0.8 },
  },
];

const PACE_PRESETS: { id: string; label: string; speed: number }[] = [
  { id: 'slower', label: 'Slower', speed: 0.85 },
  { id: 'normal', label: 'Normal', speed: 1.0 },
  { id: 'faster', label: 'Faster', speed: 1.1 },
];

const HOST_COLORS = ['#0a84ff', '#ff9500', '#2d6a5f'];

function nearestDelivery(settings: VoiceSettings): string {
  let best = DELIVERY_PRESETS[0].id;
  let bestDist = Infinity;
  for (const p of DELIVERY_PRESETS) {
    const dist =
      Math.abs(settings.stability - p.settings.stability) +
      Math.abs(settings.style - p.settings.style);
    if (dist < bestDist) {
      bestDist = dist;
      best = p.id;
    }
  }
  return best;
}

function nearestPace(speed: number): string {
  let best = PACE_PRESETS[1].id;
  let bestDist = Infinity;
  for (const p of PACE_PRESETS) {
    const dist = Math.abs(speed - p.speed);
    if (dist < bestDist) {
      bestDist = dist;
      best = p.id;
    }
  }
  return best;
}

export function VoicePicker({ hosts, voices, voiceConfig, onChange }: Props) {
  const speakers = Object.keys(hosts);

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

  const applyDelivery = (speaker: string, presetId: string) => {
    const preset = DELIVERY_PRESETS.find((p) => p.id === presetId);
    if (!preset) return;
    const current = getConfig(speaker);
    onChange({
      ...voiceConfig,
      [speaker]: {
        ...current,
        settings: { ...current.settings, ...preset.settings },
      },
    });
  };

  const applyPace = (speaker: string, speed: number) => {
    const current = getConfig(speaker);
    onChange({
      ...voiceConfig,
      [speaker]: {
        ...current,
        settings: { ...current.settings, speed },
      },
    });
  };

  if (voices.length === 0 || speakers.length === 0) {
    return (
      <div className="space-y-2">
        <h3 className="font-display text-lg font-semibold">Voices</h3>
        <div className="flex items-center gap-2 text-(--color-text-muted) text-sm py-2">
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
          Loading voices…
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-display text-lg font-semibold">Voices</h3>
        <p className="text-sm text-(--color-text-secondary) mt-0.5">
          One voice per host. Delivery and pace stay simple.
        </p>
      </div>

      <div className="space-y-3">
        {speakers.map((speaker, idx) => {
          const config = getConfig(speaker);
          const host = hosts[speaker];
          const meta = {
            role: host?.role ?? 'Host',
            color: HOST_COLORS[idx % HOST_COLORS.length],
          };
          const delivery = nearestDelivery(config.settings);
          const pace = nearestPace(config.settings.speed ?? 1);

          return (
            <div
              key={speaker}
              className="rounded-xl border border-(--color-border) bg-(--color-background) p-4 space-y-3"
            >
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-bold tracking-wide" style={{ color: meta.color }}>
                  {speaker}
                </span>
                <span className="text-xs text-(--color-text-muted)">{meta.role}</span>
              </div>

              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-(--color-text-muted) mb-1.5">
                  Voice
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {voices.map((voice) => {
                    const isSelected = config.voice_id === voice.id;
                    return (
                      <button
                        key={voice.id}
                        onClick={() => updateConfig(speaker, { voice_id: voice.id })}
                        className={`px-3 py-1.5 rounded-full text-sm transition border capitalize ${
                          isSelected
                            ? 'bg-(--color-accent)/15 border-(--color-accent) text-(--color-accent)'
                            : 'bg-(--color-surface) border-(--color-border) text-(--color-text-secondary) hover:border-(--color-text-muted)'
                        }`}
                      >
                        {voice.name}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="grid sm:grid-cols-2 gap-3">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-(--color-text-muted) mb-1.5">
                    Delivery
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {DELIVERY_PRESETS.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => applyDelivery(speaker, p.id)}
                        title={p.hint}
                        className={`px-2.5 py-1 rounded-full text-xs transition border ${
                          delivery === p.id
                            ? 'bg-(--color-accent)/15 border-(--color-accent) text-(--color-accent)'
                            : 'bg-(--color-surface) border-(--color-border) text-(--color-text-secondary) hover:border-(--color-text-muted)'
                        }`}
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-(--color-text-muted) mb-1.5">
                    Pace
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {PACE_PRESETS.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => applyPace(speaker, p.speed)}
                        className={`px-2.5 py-1 rounded-full text-xs transition border ${
                          pace === p.id
                            ? 'bg-(--color-accent)/15 border-(--color-accent) text-(--color-accent)'
                            : 'bg-(--color-surface) border-(--color-border) text-(--color-text-secondary) hover:border-(--color-text-muted)'
                        }`}
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
