import { useState, useEffect } from 'react';
import type { Article, Episode, StyleConfig, SpeakerConfig, AudioProductionConfig, VoiceInfo, EpisodeStatus } from '../types';
import { defaultStyleConfig, defaultAudioConfig } from '../types';
import { StylePicker } from './StylePicker';
import { VoicePicker } from './VoicePicker';
import { AudioSettings } from './AudioSettings';
import * as api from '../api';

interface Props {
  articles: Article[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onEditSelection: () => void;
  focus: string;
  onFocusChange: (focus: string) => void;
  onEpisodeReady: (episode: Episode) => void;
}

const statusSteps: { status: EpisodeStatus; label: string }[] = [
  { status: 'summarizing', label: 'Summarizing' },
  { status: 'scripting', label: 'Writing Script' },
  { status: 'synthesizing', label: 'Generating Audio' },
  { status: 'mixing', label: 'Mixing' },
  { status: 'ready', label: 'Ready' },
];

export function GeneratePanel({ articles, selectedIds, onToggleSelect, onEditSelection, focus, onFocusChange, onEpisodeReady }: Props) {
  const [style, setStyle] = useState<StyleConfig>(defaultStyleConfig);
  const [targetMinutes, setTargetMinutes] = useState(20);
  const [voiceConfig, setVoiceConfig] = useState<Record<string, SpeakerConfig>>({});
  const [audioConfig, setAudioConfig] = useState<AudioProductionConfig>(defaultAudioConfig);
  const [voices, setVoices] = useState<VoiceInfo[]>([]);

  const [generating, setGenerating] = useState(false);
  const [currentEpisode, setCurrentEpisode] = useState<Episode | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [showProduction, setShowProduction] = useState(false);

  const selectedArticles = articles.filter((a) => selectedIds.has(a.id));
  const totalWords = selectedArticles.reduce((sum, a) => sum + a.word_count, 0);
  const estimatedCost = targetMinutes * 0.03;

  // Load voices
  useEffect(() => {
    api.getVoices().then((res) => setVoices(res.voices)).catch(console.error);
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
    }, 2000);

    return () => clearInterval(interval);
  }, [currentEpisode, onEpisodeReady]);

  const handleGenerate = async () => {
    if (selectedArticles.length === 0) return;

    setGenerating(true);
    setError(null);
    setCurrentEpisode(null);

    try {
      const episode = await api.generateEpisode({
        article_ids: selectedArticles.map((a) => a.id),
        style,
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

      {/* Style picker */}
      <StylePicker
        style={style}
        onChange={setStyle}
        targetMinutes={targetMinutes}
        onTargetMinutesChange={setTargetMinutes}
      />

      {/* Voices & production (collapsed by default) */}
      <div className="bg-(--color-surface) rounded-2xl border border-(--color-border) overflow-hidden">
        <button
          onClick={() => setShowProduction(!showProduction)}
          className="w-full p-4 flex items-center justify-between text-sm"
        >
          <span className="text-(--color-text-secondary)">Voices &amp; production</span>
          <span className="text-(--color-text-muted)">{showProduction ? '▴' : '▾'}</span>
        </button>
        {showProduction && (
          <div className="px-4 pb-4 space-y-6">
            <VoicePicker tone={style.tone} voices={voices} voiceConfig={voiceConfig} onChange={setVoiceConfig} />
            <AudioSettings config={audioConfig} onChange={setAudioConfig} />
          </div>
        )}
      </div>

      {/* Progress card */}
      {currentEpisode && generating && (
        <div className="bg-(--color-surface) rounded-xl p-4 border border-(--color-border)">
          <div className="flex items-center justify-between mb-4">
            <span className="font-medium">Pipeline</span>
            <div className="w-4 h-4 border-2 border-(--color-accent) border-t-transparent rounded-full animate-spin" />
          </div>
          <div className="space-y-2">
            {statusSteps.map((step, i) => {
              const currentIdx = getStepIndex(currentEpisode.status);
              const isComplete = i < currentIdx;
              const isCurrent = i === currentIdx;

              return (
                <div key={step.status} className="flex items-center gap-3">
                  <div
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                      isComplete
                        ? 'bg-green-500 text-white'
                        : isCurrent
                        ? 'bg-(--color-accent) text-white'
                        : 'bg-(--color-border) text-(--color-text-muted)'
                    }`}
                  >
                    {isComplete ? '✓' : i + 1}
                  </div>
                  <span
                    className={
                      isCurrent
                        ? 'text-(--color-text-primary)'
                        : isComplete
                        ? 'text-(--color-text-secondary)'
                        : 'text-(--color-text-muted)'
                    }
                  >
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

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
        {generating ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>Generating...</span>
          </>
        ) : (
          <span>Generate episode</span>
        )}
      </button>
    </div>
  );
}
