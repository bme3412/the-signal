import type { AudioProductionConfig } from '../types';

interface Props {
  config: AudioProductionConfig;
  onChange: (config: AudioProductionConfig) => void;
}

// Base gap between turns; the mixer varies it per beat (shorter after
// reactions, longer at chapter shifts).
const GAP_PRESETS = [
  { id: 'tight', label: 'Tight', ms: 150, hint: 'Rapid-fire' },
  { id: 'natural', label: 'Natural', ms: 250, hint: 'Default' },
  { id: 'spacious', label: 'Spacious', ms: 450, hint: 'Room to breathe' },
];

function nearestGap(ms: number): string {
  let best = GAP_PRESETS[1].id;
  let bestDist = Infinity;
  for (const p of GAP_PRESETS) {
    const dist = Math.abs(ms - p.ms);
    if (dist < bestDist) {
      bestDist = dist;
      best = p.id;
    }
  }
  return best;
}

function Toggle({
  on,
  onToggle,
  title,
  description,
}: {
  on: boolean;
  onToggle: () => void;
  title: string;
  description: string;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="w-full flex items-center gap-3 text-left"
    >
      <div
        className={`w-10 h-6 rounded-full transition relative shrink-0 ${
          on ? 'bg-(--color-accent)' : 'bg-(--color-border)'
        }`}
      >
        <div
          className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
            on ? 'translate-x-5' : 'translate-x-1'
          }`}
        />
      </div>
      <div>
        <div className="text-sm font-medium">{title}</div>
        <div className="text-xs text-(--color-text-muted)">{description}</div>
      </div>
    </button>
  );
}

export function AudioSettings({ config, onChange }: Props) {
  const update = <K extends keyof AudioProductionConfig>(key: K, value: AudioProductionConfig[K]) => {
    onChange({ ...config, [key]: value });
  };

  const gap = nearestGap(config.gap_medium_ms ?? 250);

  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-display text-lg font-semibold">Production</h3>
        <p className="text-sm text-(--color-text-secondary) mt-0.5">
          Light mix choices — defaults are fine for most episodes.
        </p>
      </div>

      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wider text-(--color-text-muted) mb-1.5">
          Pause between lines
        </p>
        <div className="flex flex-wrap gap-2">
          {GAP_PRESETS.map((p) => {
            const active = gap === p.id;
            return (
              <button
                key={p.id}
                onClick={() => update('gap_medium_ms', p.ms)}
                className={`px-3.5 py-2 rounded-xl border text-left transition ${
                  active
                    ? 'border-(--color-accent) bg-(--color-accent)/10'
                    : 'border-(--color-border) bg-(--color-background) hover:border-(--color-text-muted)'
                }`}
              >
                <div className={`text-sm font-semibold ${active ? 'text-(--color-accent)' : ''}`}>
                  {p.label}
                </div>
                <div className="text-[11px] text-(--color-text-muted)">{p.hint}</div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="space-y-3 pt-1">
        <Toggle
          on={config.intro_music}
          onToggle={() => update('intro_music', !config.intro_music)}
          title="Intro theme"
          description="Short sting that fades under the opening line"
        />
        <Toggle
          on={config.normalize}
          onToggle={() => update('normalize', !config.normalize)}
          title="Normalize volume"
          description="Even out loud and quiet segments"
        />
      </div>
    </div>
  );
}
