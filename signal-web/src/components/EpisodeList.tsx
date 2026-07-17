import { useState } from 'react';
import type { Episode, EpisodeStatus } from '../types';
import { TranscriptModal } from './Transcript';

interface Props {
  episodes: Episode[];
  onSelect: (episode: Episode) => void;
  onRefresh: () => void;
}

const statusConfig: Record<EpisodeStatus, { label: string; color: string; icon: string }> = {
  queued: { label: 'Queued', color: '#6b7280', icon: '⏳' },
  summarizing: { label: 'Summarizing', color: '#0a84ff', icon: '📝' },
  scripting: { label: 'Writing Script', color: '#0a84ff', icon: '✍️' },
  synthesizing: { label: 'Generating Audio', color: '#bf5af2', icon: '🔊' },
  mixing: { label: 'Mixing', color: '#bf5af2', icon: '🎛️' },
  ready: { label: 'Ready', color: '#34c759', icon: '✅' },
  failed: { label: 'Failed', color: '#ff3b30', icon: '❌' },
};

export function EpisodeList({ episodes, onSelect, onRefresh }: Props) {
  const [transcriptEpisode, setTranscriptEpisode] = useState<Episode | null>(null);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Episodes</h2>
        <button
          onClick={onRefresh}
          className="px-3 py-1.5 text-[--color-text-secondary] hover:text-[--color-text-primary] transition text-sm"
        >
          ↻ Refresh
        </button>
      </div>

      {episodes.length === 0 ? (
        <div className="text-center py-12 text-[--color-text-muted]">
          <p>No episodes yet.</p>
          <p className="text-sm mt-2">Generate your first episode from the Queue tab.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {episodes.map((episode) => {
            const status = statusConfig[episode.status];
            const isPlayable = episode.status === 'ready';

            return (
              <div
                key={episode.id}
                onClick={() => isPlayable && onSelect(episode)}
                role="button"
                className={`w-full p-4 rounded-xl border text-left transition ${
                  isPlayable
                    ? 'bg-[--color-surface] border-[--color-border] hover:border-[--color-accent-blue] cursor-pointer'
                    : 'bg-[--color-surface]/50 border-[--color-border] cursor-default'
                }`}
              >
                <div className="flex items-center gap-4">
                  {/* Play indicator or status icon */}
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl ${
                      isPlayable
                        ? 'bg-[--color-accent-blue]/20 text-[--color-accent-blue]'
                        : 'bg-[--color-border]/50'
                    }`}
                  >
                    {isPlayable ? '▶' : status.icon}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate">
                        Episode • {episode.article_ids.length} articles
                      </span>
                      {!isPlayable && (
                        <span
                          className="px-2 py-0.5 rounded-full text-xs"
                          style={{ backgroundColor: `${status.color}20`, color: status.color }}
                        >
                          {status.label}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-sm text-[--color-text-muted]">
                      <span>{formatDate(episode.created_at)}</span>
                      {episode.audio_duration_seconds && (
                        <>
                          <span>•</span>
                          <span>{formatDuration(episode.audio_duration_seconds)}</span>
                        </>
                      )}
                      {episode.metrics && (
                        <>
                          <span>•</span>
                          <span>${episode.metrics.estimated_cost_usd.toFixed(2)}</span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Transcript */}
                  {episode.script && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setTranscriptEpisode(episode);
                      }}
                      title="View transcript"
                      className="px-3 py-1.5 rounded-lg text-sm bg-[--color-background] border border-[--color-border] text-[--color-text-secondary] hover:text-[--color-text-primary] hover:border-[--color-accent-blue] transition shrink-0"
                    >
                      📄 Transcript
                    </button>
                  )}
                </div>

                {/* Error message */}
                {episode.status === 'failed' && episode.error && (
                  <p className="mt-2 text-sm text-red-400 truncate">{episode.error}</p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {transcriptEpisode && (
        <TranscriptModal episode={transcriptEpisode} onClose={() => setTranscriptEpisode(null)} />
      )}
    </div>
  );
}
