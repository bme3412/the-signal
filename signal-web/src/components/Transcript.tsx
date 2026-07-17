import type { Chapter, Episode, ScriptSegment } from '../types';

export const speakerColors: Record<string, string> = {
  ALEX: '#0a84ff',
  JAMIE: '#ff9500',
  HOST: '#0a84ff',
  BULL: '#34c759',
  BEAR: '#ff3b30',
};

const roleLabels: Record<Chapter['role'], string> = {
  intro: 'Intro',
  core: 'Core',
  optional: 'Bonus',
  closer: 'Closer',
};

function formatDuration(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function Segment({ segment }: { segment: ScriptSegment }) {
  return (
    <div>
      <span
        className="text-xs font-bold"
        style={{ color: speakerColors[segment.speaker] || '#6b7280' }}
      >
        [{segment.speaker}]
      </span>
      <p className="text-sm text-(--color-text-secondary) mt-1">{segment.text}</p>
    </div>
  );
}

interface Props {
  episode: Episode;
  onClose: () => void;
}

export function TranscriptModal({ episode, onClose }: Props) {
  const script = episode.script;
  if (!script) return null;

  const hasChapters = script.chapters && script.chapters.length > 0;

  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-(--color-surface) border border-(--color-border) rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-(--color-border)">
          <div>
            <h3 className="font-display text-xl font-semibold">
              {episode.title || 'Transcript'}
            </h3>
            <p className="text-xs text-(--color-text-muted) mt-0.5">
              {script.word_count.toLocaleString()} words • ~{script.estimated_minutes.toFixed(1)} min
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-(--color-text-muted) hover:text-(--color-text-primary) transition text-xl leading-none"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="overflow-y-auto p-4 space-y-4">
          {hasChapters
            ? script.chapters.map((chapter, ci) => (
                <section key={ci} className="space-y-3">
                  <div className="flex items-center gap-2 bg-(--color-background) rounded-lg px-3 py-2 sticky top-0">
                    <span className="text-sm font-semibold">{chapter.title}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                        chapter.role === 'optional'
                          ? 'bg-(--color-accent-alt)/20 text-(--color-accent-alt)'
                          : 'bg-(--color-border) text-(--color-text-muted)'
                      }`}
                    >
                      {roleLabels[chapter.role]}
                    </span>
                    {chapter.duration_seconds > 0 && (
                      <span className="text-xs text-(--color-text-muted) ml-auto font-mono">
                        {formatDuration(chapter.duration_seconds)}
                      </span>
                    )}
                  </div>
                  {chapter.segment_indices
                    .filter((i) => i >= 0 && i < script.segments.length)
                    .map((i) => (
                      <Segment key={i} segment={script.segments[i]} />
                    ))}
                </section>
              ))
            : script.segments.map((segment, i) => <Segment key={i} segment={segment} />)}
        </div>
      </div>
    </div>
  );
}
