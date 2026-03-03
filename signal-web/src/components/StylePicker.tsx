import type { StyleConfig } from '../types';
import { dimensionMeta, builtInPresets } from '../types';

interface Props {
  style: StyleConfig;
  onChange: (style: StyleConfig) => void;
  targetMinutes: number;
  onTargetMinutesChange: (minutes: number) => void;
}

export function StylePicker({ style, onChange, targetMinutes, onTargetMinutesChange }: Props) {
  const updateDimension = <K extends keyof StyleConfig>(key: K, value: StyleConfig[K]) => {
    onChange({ ...style, [key]: value });
  };

  return (
    <div className="space-y-6">
      {/* Presets */}
      <div>
        <h3 className="text-xs font-bold text-[--color-text-muted] tracking-wider mb-3">PRESETS</h3>
        <div className="flex gap-3 overflow-x-auto pb-2">
          {builtInPresets.map((preset) => {
            const isActive = JSON.stringify(style) === JSON.stringify(preset.config);
            return (
              <button
                key={preset.id}
                onClick={() => onChange(preset.config)}
                className={`flex-shrink-0 p-3 rounded-xl border transition text-left w-36 ${
                  isActive
                    ? 'border-[--color-accent-blue] bg-[--color-accent-blue]/10'
                    : 'border-[--color-border] bg-[--color-surface] hover:border-[--color-text-muted]'
                }`}
              >
                <div className="text-2xl mb-1">{preset.icon}</div>
                <div className="font-medium text-sm">{preset.name}</div>
                <div className="text-xs text-[--color-text-muted] mt-1">{preset.subtitle}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Duration Slider */}
      <div className="bg-[--color-surface] rounded-xl p-4 border border-[--color-border]">
        <div className="flex items-center justify-between mb-2">
          <span className="font-medium">Target Duration</span>
          <span className="text-[--color-accent-blue] font-mono">{targetMinutes} min</span>
        </div>
        <input
          type="range"
          min={5}
          max={60}
          step={5}
          value={targetMinutes}
          onChange={(e) => onTargetMinutesChange(Number(e.target.value))}
        />
        <div className="flex justify-between text-xs text-[--color-text-muted] mt-1">
          <span>5 min</span>
          <span>60 min</span>
        </div>
      </div>

      {/* Style Dimensions */}
      <div className="space-y-4">
        {(['depth', 'tone', 'lens', 'pacing', 'humor', 'audience', 'structure', 'closer'] as const).map((key) => {
          const meta = dimensionMeta[key];
          return (
            <div key={key} className="bg-[--color-surface] rounded-xl p-4 border border-[--color-border]">
              <h4 className="font-medium mb-3">{meta.label}</h4>
              <div className="flex flex-wrap gap-2">
                {meta.options.map((opt) => {
                  const isSelected = style[key] === opt.value;
                  return (
                    <button
                      key={opt.value}
                      onClick={() => updateDimension(key, opt.value as StyleConfig[typeof key])}
                      className={`px-3 py-1.5 rounded-full text-sm transition border ${
                        isSelected
                          ? 'bg-[--color-accent-blue]/20 border-[--color-accent-blue] text-[--color-accent-blue]'
                          : 'bg-transparent border-[--color-border] text-[--color-text-secondary] hover:border-[--color-text-muted]'
                      }`}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
              <p className="text-xs text-[--color-text-muted] mt-2">
                {meta.options.find((o) => o.value === style[key])?.desc}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
