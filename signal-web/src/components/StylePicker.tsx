import { useState } from 'react';
import type { StyleConfig } from '../types';
import { dimensionMeta, builtInPresets } from '../types';

interface Props {
  style: StyleConfig;
  onChange: (style: StyleConfig) => void;
  targetMinutes: number;
  onTargetMinutesChange: (minutes: number) => void;
}

const dimensionKeys = [
  'depth', 'tone', 'lens', 'pacing', 'humor', 'audience', 'structure', 'closer',
] as const;

const LENGTH_OPTIONS = [
  { minutes: 10, label: '10 min', hint: 'Quick' },
  { minutes: 15, label: '15 min', hint: 'Short' },
  { minutes: 20, label: '20 min', hint: 'Standard' },
  { minutes: 30, label: '30 min', hint: 'Long' },
  { minutes: 45, label: '45 min', hint: 'Deep' },
];

export function StylePicker({ style, onChange, targetMinutes, onTargetMinutesChange }: Props) {
  const [showFineTune, setShowFineTune] = useState(false);

  const updateDimension = <K extends keyof StyleConfig>(key: K, value: StyleConfig[K]) => {
    onChange({ ...style, [key]: value });
  };

  const activePreset = builtInPresets.find(
    (p) => JSON.stringify(style) === JSON.stringify(p.config)
  );

  const styleSummary = activePreset
    ? activePreset.name
    : dimensionKeys
        .slice(0, 3)
        .map((k) => dimensionMeta[k].options.find((o) => o.value === style[k])?.label)
        .join(' · ') + ' · …';

  return (
    <div className="rise bg-(--color-surface) rounded-2xl p-5 border border-(--color-border) space-y-5">
      <div>
        <h3 className="font-display text-xl font-semibold mb-1">The sound</h3>
        <p className="text-sm text-(--color-text-secondary) mb-3">
          Pick a preset — fine-tune only if you want to.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {builtInPresets.map((preset) => {
            const isActive = activePreset?.id === preset.id;
            return (
              <button
                key={preset.id}
                onClick={() => onChange(preset.config)}
                className={`p-3 rounded-xl border transition text-left ${
                  isActive
                    ? 'border-(--color-accent) bg-(--color-accent)/10'
                    : 'border-(--color-border) bg-(--color-background) hover:border-(--color-text-muted)'
                }`}
              >
                <div className="font-medium text-sm">{preset.name}</div>
                <div className="text-xs text-(--color-text-muted) mt-0.5 leading-snug">
                  {preset.subtitle}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <span className="text-sm font-medium">Length</span>
        <div className="mt-2 flex flex-wrap gap-2">
          {LENGTH_OPTIONS.map((opt) => {
            const active = targetMinutes === opt.minutes;
            return (
              <button
                key={opt.minutes}
                onClick={() => onTargetMinutesChange(opt.minutes)}
                className={`px-3.5 py-2 rounded-xl border text-left transition min-w-[4.5rem] ${
                  active
                    ? 'border-(--color-accent) bg-(--color-accent)/10'
                    : 'border-(--color-border) bg-(--color-background) hover:border-(--color-text-muted)'
                }`}
              >
                <div className={`text-sm font-semibold ${active ? 'text-(--color-accent)' : ''}`}>
                  {opt.label}
                </div>
                <div className="text-[11px] text-(--color-text-muted)">{opt.hint}</div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="border-t border-(--color-border) pt-4 -mb-1">
        <button
          onClick={() => setShowFineTune(!showFineTune)}
          className="w-full flex items-center justify-between text-sm"
          aria-expanded={showFineTune}
        >
          <span className="text-(--color-text-secondary)">
            Fine-tune{' '}
            <span className="font-mono text-[11px] text-(--color-text-muted)">
              {styleSummary}
            </span>
          </span>
          <span className="text-(--color-text-muted) text-lg leading-none w-6 text-center">
            {showFineTune ? '−' : '+'}
          </span>
        </button>

        {showFineTune && (
          <div className="mt-4 space-y-4">
            {dimensionKeys.map((key) => {
              const meta = dimensionMeta[key];
              return (
                <div key={key} className="flex flex-wrap items-baseline gap-x-3 gap-y-1.5">
                  <span className="w-20 shrink-0 text-xs font-semibold text-(--color-text-secondary)">
                    {meta.label}
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {meta.options.map((opt) => {
                      const isSelected = style[key] === opt.value;
                      return (
                        <button
                          key={opt.value}
                          onClick={() => updateDimension(key, opt.value as StyleConfig[typeof key])}
                          title={opt.desc}
                          className={`px-2.5 py-1 rounded-full text-xs transition border ${
                            isSelected
                              ? 'bg-(--color-accent)/15 border-(--color-accent) text-(--color-accent)'
                              : 'bg-transparent border-(--color-border) text-(--color-text-secondary) hover:border-(--color-text-muted)'
                          }`}
                        >
                          {opt.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
