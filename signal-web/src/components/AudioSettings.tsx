import type { AudioProductionConfig } from '../types';

interface Props {
  config: AudioProductionConfig;
  onChange: (config: AudioProductionConfig) => void;
}

export function AudioSettings({ config, onChange }: Props) {
  const update = <K extends keyof AudioProductionConfig>(key: K, value: AudioProductionConfig[K]) => {
    onChange({ ...config, [key]: value });
  };

  return (
    <div className="bg-[--color-surface] rounded-xl p-4 border border-[--color-border] space-y-4">
      <h4 className="font-medium">Audio Production</h4>

      {/* Silence duration */}
      <div>
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-[--color-text-secondary]">Gap Between Segments</span>
          <span className="font-mono text-[--color-text-muted]">{config.silence_duration_ms}ms</span>
        </div>
        <input
          type="range"
          min={100}
          max={1000}
          step={50}
          value={config.silence_duration_ms}
          onChange={(e) => update('silence_duration_ms', Number(e.target.value))}
        />
        <p className="text-xs text-[--color-text-muted] mt-1">
          Shorter for rapid-fire, longer for dramatic pauses
        </p>
      </div>

      {/* Fade controls */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-[--color-text-secondary]">Fade In</span>
            <span className="font-mono text-[--color-text-muted]">{config.fade_in_ms}ms</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => update('fade_in_ms', Math.max(0, config.fade_in_ms - 50))}
              disabled={config.fade_in_ms <= 0}
              className="w-8 h-8 rounded-full bg-[--color-background] border border-[--color-border] text-[--color-text-secondary] hover:border-[--color-text-muted] disabled:opacity-50 transition"
            >
              −
            </button>
            <span className="flex-1 text-center font-mono text-sm">{config.fade_in_ms}</span>
            <button
              onClick={() => update('fade_in_ms', Math.min(500, config.fade_in_ms + 50))}
              disabled={config.fade_in_ms >= 500}
              className="w-8 h-8 rounded-full bg-[--color-background] border border-[--color-border] text-[--color-text-secondary] hover:border-[--color-text-muted] disabled:opacity-50 transition"
            >
              +
            </button>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-[--color-text-secondary]">Fade Out</span>
            <span className="font-mono text-[--color-text-muted]">{config.fade_out_ms}ms</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => update('fade_out_ms', Math.max(0, config.fade_out_ms - 50))}
              disabled={config.fade_out_ms <= 0}
              className="w-8 h-8 rounded-full bg-[--color-background] border border-[--color-border] text-[--color-text-secondary] hover:border-[--color-text-muted] disabled:opacity-50 transition"
            >
              −
            </button>
            <span className="flex-1 text-center font-mono text-sm">{config.fade_out_ms}</span>
            <button
              onClick={() => update('fade_out_ms', Math.min(500, config.fade_out_ms + 50))}
              disabled={config.fade_out_ms >= 500}
              className="w-8 h-8 rounded-full bg-[--color-background] border border-[--color-border] text-[--color-text-secondary] hover:border-[--color-text-muted] disabled:opacity-50 transition"
            >
              +
            </button>
          </div>
        </div>
      </div>

      {/* Normalize toggle */}
      <label className="flex items-center gap-3 cursor-pointer">
        <div
          className={`w-10 h-6 rounded-full transition relative ${
            config.normalize ? 'bg-[--color-accent-blue]' : 'bg-[--color-border]'
          }`}
          onClick={() => update('normalize', !config.normalize)}
        >
          <div
            className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
              config.normalize ? 'translate-x-5' : 'translate-x-1'
            }`}
          />
        </div>
        <div>
          <div className="text-sm">Normalize Volume</div>
          <div className="text-xs text-[--color-text-muted]">Even out audio levels across segments</div>
        </div>
      </label>
    </div>
  );
}
