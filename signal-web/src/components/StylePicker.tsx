interface Props {
  targetMinutes: number;
  onTargetMinutesChange: (minutes: number) => void;
}

const LENGTH_OPTIONS = [
  { minutes: 10, label: '10 min', hint: 'Quick' },
  { minutes: 15, label: '15 min', hint: 'Short' },
  { minutes: 20, label: '20 min', hint: 'Standard' },
  { minutes: 30, label: '30 min', hint: 'Long' },
  { minutes: 45, label: '45 min', hint: 'Deep' },
];

export function StylePicker({ targetMinutes, onTargetMinutesChange }: Props) {
  return (
    <div className="rise bg-(--color-surface) rounded-2xl p-5 border border-(--color-border) space-y-5">
      <div>
        <h3 className="font-display text-xl font-semibold mb-1">The sound</h3>
        <p className="text-sm text-(--color-text-secondary)">
          Auto — the editor reads the stories and decides how Maya and Dev
          should take them on. Use the Direction field above to steer the
          angle.
        </p>
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
    </div>
  );
}
