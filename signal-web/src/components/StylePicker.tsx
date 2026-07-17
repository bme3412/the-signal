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
      {/* Presets */}
      <div>
        <h3 className="font-display text-xl font-semibold mb-3">The sound</h3>
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

      {/* Duration */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium">Length</span>
          <span className="text-(--color-accent) font-mono text-sm">{targetMinutes} min</span>
        </div>
        <input
          type="range"
          min={5}
          max={60}
          step={5}
          value={targetMinutes}
          onChange={(e) => onTargetMinutesChange(Number(e.target.value))}
        />
      </div>

      {/* Fine-tune (collapsed by default) */}
      <div className="border-t border-(--color-border) pt-4 -mb-1">
        <button
          onClick={() => setShowFineTune(!showFineTune)}
          className="w-full flex items-center justify-between text-sm"
        >
          <span className="text-(--color-text-secondary)">
            Fine-tune{' '}
            <span className="font-mono text-[11px] text-(--color-text-muted)">
              {styleSummary}
            </span>
          </span>
          <span className="text-(--color-text-muted)">{showFineTune ? '▴' : '▾'}</span>
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
