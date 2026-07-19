import { useState, useEffect, useRef } from 'react';
import type { Article, Episode, SpeakerConfig, AudioProductionConfig, VoiceInfo, HostInfo, EpisodeStatus } from '../types';
import { defaultAudioConfig } from '../types';
import { StylePicker } from './StylePicker';
import { VoicePicker } from './VoicePicker';
import { AudioSettings } from './AudioSettings';
import * as api from '../api';

interface Props {
  articles: Article[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onEditSelection: () => void;
  onGoListen: () => void;
  onGoCompose: () => void;
  /** False when user navigated away during generation — keep mounted, show slim bar. */
  visible: boolean;
  onBusyChange: (busy: boolean) => void;
  focus: string;
  onFocusChange: (focus: string) => void;
  onEpisodeReady: (episode: Episode) => void;
}

const statusSteps: { status: EpisodeStatus; label: string; vibe: string }[] = [
  { status: 'summarizing', label: 'Reading', vibe: 'Getting cozy with the stories' },
  { status: 'scripting', label: 'Writing', vibe: 'Shaping the show' },
  { status: 'synthesizing', label: 'Voicing', vibe: 'Hosts on the mic' },
  { status: 'mixing', label: 'Mixing', vibe: 'Sewing the takes together' },
  { status: 'ready', label: 'Ready', vibe: 'You’re on air' },
];

export function GeneratePanel({
  articles,
  selectedIds,
  onToggleSelect,
  onEditSelection,
  onGoListen,
  onGoCompose,
  visible,
  onBusyChange,
  focus,
  onFocusChange,
  onEpisodeReady,
}: Props) {
  const [targetMinutes, setTargetMinutes] = useState(20);
  const [voiceConfig, setVoiceConfig] = useState<Record<string, SpeakerConfig>>({});
  const [audioConfig, setAudioConfig] = useState<AudioProductionConfig>(defaultAudioConfig);
  const [voices, setVoices] = useState<VoiceInfo[]>([]);
  const [hosts, setHosts] = useState<Record<string, HostInfo>>({});

  const [generating, setGenerating] = useState(false);
  const [currentEpisode, setCurrentEpisode] = useState<Episode | null>(null);
  const [error, setError] = useState<string | null>(null);
  const feedRef = useRef<HTMLDivElement>(null);

  const selectedArticles = articles.filter((a) => selectedIds.has(a.id));
  const totalWords = selectedArticles.reduce((sum, a) => sum + a.word_count, 0);
  const estimatedCost = targetMinutes * 0.03;

  useEffect(() => {
    onBusyChange(generating);
  }, [generating, onBusyChange]);

  // Load voices
  useEffect(() => {
    api.getVoices().then((res) => {
      setVoices(res.voices);
      setHosts(res.hosts ?? {});
    }).catch(console.error);
  }, []);

  // Poll for episode completion
  useEffect(() => {
    if (!currentEpisode || currentEpisode.status === 'ready' || currentEpisode.status === 'failed') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const updated = await api.getEpisode(currentEpisode.id);
        setCurrentEpisode(updated);

        if (updated.status === 'ready') {
          setGenerating(false);
          onEpisodeReady(updated);
        } else if (updated.status === 'failed') {
          setGenerating(false);
          setError(updated.error || 'Generation failed');
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1200);

    return () => clearInterval(interval);
  }, [currentEpisode, onEpisodeReady]);

  // Auto-scroll the narration feed to the newest line
  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: 'smooth' });
  }, [currentEpisode?.progress?.length]);

  const handleGenerate = async () => {
    if (selectedArticles.length === 0) return;

    setGenerating(true);
    setError(null);
    setCurrentEpisode(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });

    try {
      const episode = await api.generateEpisode({
        article_ids: selectedArticles.map((a) => a.id),
        focus: focus.trim() || undefined,
        voice_config: Object.keys(voiceConfig).length > 0 ? voiceConfig : undefined,
        audio_config: audioConfig,
        target_minutes: targetMinutes,
      });
      setCurrentEpisode(episode);
    } catch (err) {
      setGenerating(false);
      setError(err instanceof Error ? err.message : 'Generation failed');
    }
  };

  const getStepIndex = (status: EpisodeStatus) => {
    const idx = statusSteps.findIndex((s) => s.status === status);
    return idx === -1 ? 0 : idx;
  };

  const currentStep = currentEpisode
    ? statusSteps[getStepIndex(currentEpisode.status)] ?? statusSteps[0]
    : null;
  const latestMessage =
    currentEpisode?.progress && currentEpisode.progress.length > 0
      ? currentEpisode.progress[currentEpisode.progress.length - 1].message
      : currentStep?.vibe ?? 'Warming up the studio…';

  // Fixed studio overlay when Compose is focused; slim bar when browsing away.
  if (generating) {
    const currentIdx = currentEpisode
      ? getStepIndex(currentEpisode.status)
      : 0;

    if (!visible) {
      return (
        <div className="fixed inset-x-0 bottom-0 z-40 border-t-2 border-(--color-text-primary) bg-(--color-surface) shadow-[0_-12px_40px_rgba(34,29,21,0.12)]">
          <div className="max-w-3xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3">
            <span className="studio-dot w-2 h-2 rounded-full bg-(--color-accent) shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold truncate">
                {currentStep?.label ?? 'Working'} — {latestMessage}
              </p>
              <p className="font-mono text-[10px] uppercase tracking-wider text-(--color-text-muted)">
                Generation continues in the background
              </p>
            </div>
            <button
              type="button"
              onClick={onGoCompose}
              className="shrink-0 px-3 py-2 text-sm font-semibold text-(--color-accent) hover:underline"
            >
              Studio
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="fixed inset-0 z-40 bg-(--color-background) flex flex-col">
        <div className="shrink-0 flex items-center justify-between px-4 sm:px-6 py-3 border-b border-(--color-border)">
          <div className="flex items-center gap-2 min-w-0">
            <span className="studio-dot w-2 h-2 rounded-full bg-(--color-accent) shrink-0" />
            <span className="font-display font-semibold italic truncate">In the studio</span>
          </div>
          <button
            type="button"
            onClick={onGoListen}
            className="text-sm text-(--color-text-secondary) hover:text-(--color-accent) transition shrink-0"
          >
            Browse Listen →
          </button>
        </div>

        <div className="flex-1 min-h-0 flex items-center justify-center p-4 sm:p-6">
          <div className="studio-panel w-full max-w-lg max-h-full flex flex-col bg-(--color-surface) border-2 border-(--color-text-primary) rounded-2xl shadow-[0_16px_50px_rgba(34,29,21,0.12)] overflow-hidden">
            <div className="shrink-0 px-5 sm:px-6 pt-5 pb-3 text-center">
              <p className="font-display text-2xl font-semibold italic leading-tight">
                {currentStep?.label ?? 'Reading'}
              </p>
              <p className="text-sm text-(--color-text-muted) mt-1">
                {currentStep?.vibe ?? 'Warming up the studio…'}
              </p>
              <p
                key={latestMessage}
                className="feed-line text-sm sm:text-base text-(--color-text-secondary) mt-3 leading-snug"
              >
                {latestMessage}
              </p>
            </div>

            <div className="shrink-0 px-5 sm:px-6 pb-3 flex items-center gap-1.5">
              {statusSteps.filter((s) => s.status !== 'ready').map((step, i) => {
                const isComplete = i < currentIdx;
                const isCurrent = i === currentIdx;
                return (
                  <div key={step.status} className="flex-1 min-w-0">
                    <div
                      className={`h-1.5 rounded-full transition-all duration-500 ${
                        isComplete || isCurrent
                          ? 'bg-(--color-accent)'
                          : 'bg-(--color-border)'
                      } ${isCurrent ? 'opacity-100' : isComplete ? 'opacity-70' : 'opacity-40'}`}
                    />
                    <p
                      className={`mt-1.5 font-mono text-[10px] uppercase tracking-wider text-center truncate ${
                        isCurrent
                          ? 'text-(--color-accent)'
                          : 'text-(--color-text-muted)'
                      }`}
                    >
                      {step.label}
                    </p>
                  </div>
                );
              })}
            </div>

            <div
              ref={feedRef}
              className="flex-1 min-h-0 overflow-y-auto mx-5 sm:mx-6 mb-4 rounded-xl bg-(--color-background) border border-(--color-border) px-4 py-3 space-y-2.5"
            >
              {currentEpisode?.progress && currentEpisode.progress.length > 0 ? (
                currentEpisode.progress.map((event, i, arr) => {
                  const isLast = i === arr.length - 1;
                  return (
                    <div
                      key={`${event.at}-${i}`}
                      className={`feed-line text-sm leading-snug ${
                        isLast
                          ? 'text-(--color-text-primary) font-medium'
                          : 'text-(--color-text-muted)'
                      }`}
                    >
                      {event.message}
                      {isLast && (
                        <span className="ml-1 text-(--color-accent) animate-pulse">✦</span>
                      )}
                    </div>
                  );
                })
              ) : (
                <p className="text-sm text-(--color-text-muted)">Cueing the hosts…</p>
              )}
            </div>

            <p className="shrink-0 px-5 pb-4 text-center font-mono text-[10px] uppercase tracking-wider text-(--color-text-muted)">
              Safe to browse — we’ll open the episode when it’s ready
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!visible) return null;

  if (selectedArticles.length === 0) {
    return (
      <div className="rise text-center py-16 px-6 bg-(--color-surface) border border-(--color-border) rounded-2xl">
        <p className="font-display text-2xl italic mb-2">Nothing selected yet.</p>
        <p className="text-(--color-text-secondary) mb-6">
          Pick the stories you want in this episode from the queue first.
        </p>
        <button
          onClick={onEditSelection}
          className="px-5 py-2.5 bg-(--color-accent) text-white rounded-full font-semibold text-sm hover:opacity-90 transition"
        >
          ← Back to the queue
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Selection summary */}
      <div className="rise bg-(--color-surface) rounded-2xl p-5 border border-(--color-border)">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display text-xl font-semibold">In this episode</h2>
          <button
            onClick={onEditSelection}
            className="text-sm text-(--color-accent) hover:underline underline-offset-2"
          >
            Edit selection
          </button>
        </div>
        <ul className="space-y-1.5 mb-4">
          {selectedArticles.map((a) => (
            <li key={a.id} className="flex items-center gap-2 text-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-(--color-accent) shrink-0" />
              <span className="truncate">{a.title}</span>
              <span className="font-mono text-[11px] text-(--color-text-muted) shrink-0">
                {a.source}
              </span>
              <button
                onClick={() => onToggleSelect(a.id)}
                title="Remove from episode"
                className="ml-auto shrink-0 text-(--color-text-muted) hover:text-(--color-accent) transition px-1"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
        {/* Direction: free text, pre-filled when an angle was chosen in Discover */}
        <div className="border-t border-(--color-border) pt-3 mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-(--color-text-secondary) shrink-0">
              Direction
            </span>
            <input
              type="text"
              value={focus}
              onChange={(e) => onFocusChange(e.target.value)}
              placeholder="Optional: what should this episode be about?"
              maxLength={300}
              className="flex-1 px-3 py-1.5 text-sm bg-(--color-background) border border-(--color-border) rounded-lg focus:outline-none focus:border-(--color-accent)"
            />
            {focus && (
              <button
                onClick={() => onFocusChange('')}
                title="Clear direction"
                className="text-(--color-text-muted) hover:text-(--color-accent) transition px-1"
              >
                ✕
              </button>
            )}
          </div>
        </div>
        <div className="flex items-center justify-between text-sm border-t border-(--color-border) pt-3">
          <span className="text-(--color-text-secondary)">~{targetMinutes} min episode</span>
          <span className="font-mono text-xs text-(--color-text-muted)">
            {totalWords.toLocaleString()} words · ~${estimatedCost.toFixed(2)}
          </span>
        </div>
      </div>

      <StylePicker
        targetMinutes={targetMinutes}
        onTargetMinutesChange={setTargetMinutes}
      />

      {/* Voices & production — always open, kept readable */}
      <div className="bg-(--color-surface) rounded-2xl border border-(--color-border) p-5 space-y-8">
        <VoicePicker hosts={hosts} voices={voices} voiceConfig={voiceConfig} onChange={setVoiceConfig} />
        <div className="border-t border-(--color-border)" />
        <AudioSettings config={audioConfig} onChange={setAudioConfig} />
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center gap-2 text-red-700 font-medium mb-1">
            <span>⚠</span>
            <span>Generation Failed</span>
          </div>
          <p className="text-sm text-red-600">{error}</p>
          <button
            onClick={handleGenerate}
            className="mt-3 px-4 py-2 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 transition"
          >
            Retry
          </button>
        </div>
      )}

      {/* Generate button */}
      <button
        onClick={handleGenerate}
        disabled={selectedArticles.length === 0 || generating}
        className="w-full py-4 bg-(--color-accent) text-white rounded-xl font-semibold text-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        Generate episode
      </button>
    </div>
  );
}
