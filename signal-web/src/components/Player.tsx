import { useState, useRef, useEffect } from 'react';
import type { Episode } from '../types';
import { getAudioUrl } from '../api';
import { speakerColors } from './Transcript';

interface Props {
  episode: Episode;
  onClose: () => void;
}

export function Player({ episode, onClose }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [showScript, setShowScript] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => setDuration(audio.duration);
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('ended', handleEnded);
    };
  }, []);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const seek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = Number(e.target.value);
  };

  const skip = (seconds: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = Math.max(0, Math.min(duration, audio.currentTime + seconds));
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 bg-(--color-background) z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-(--color-border)">
        <button onClick={onClose} className="text-(--color-text-secondary) hover:text-(--color-text-primary)">
          ← Back
        </button>
        <h2 className="font-display text-lg font-semibold italic">Now playing</h2>
        <button
          onClick={() => setShowScript(!showScript)}
          className={`px-3 py-1 rounded-lg text-sm transition ${
            showScript
              ? 'bg-(--color-accent) text-white'
              : 'bg-(--color-surface) text-(--color-text-secondary)'
          }`}
        >
          Script
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Main player area */}
        <div className={`flex-1 flex flex-col items-center justify-center p-8 ${showScript ? 'w-1/2' : 'w-full'}`}>
          {/* Episode info */}
          <div className="text-center mb-8">
            <div className="w-32 h-32 rounded-2xl bg-(--color-surface) border border-(--color-border) flex items-center justify-center mb-4 mx-auto shadow-[0_8px_30px_rgba(34,29,21,0.1)]">
              <svg viewBox="0 0 100 100" className="w-20 h-20">
                <circle cx="50" cy="50" r="12" fill="var(--color-accent)">
                  {isPlaying && (
                    <animate attributeName="opacity" values="1;0.55;1" dur="2s" repeatCount="indefinite" />
                  )}
                </circle>
                <circle cx="50" cy="50" r="26" fill="none" stroke="var(--color-accent)" strokeWidth="4" opacity="0.45" />
                <circle cx="50" cy="50" r="40" fill="none" stroke="var(--color-accent)" strokeWidth="3" opacity="0.18" />
              </svg>
            </div>
            <h3 className="font-display text-xl font-semibold">Episode</h3>
            <p className="text-(--color-text-muted) text-sm mt-1">
              {episode.article_ids.length} articles • {episode.script?.estimated_minutes.toFixed(1)} min
            </p>
          </div>

          {/* Segment visualization */}
          {episode.script && (
            <div className="w-full max-w-md mb-8">
              <div className="h-2 rounded-full bg-(--color-border) flex overflow-hidden">
                {episode.script.segments.map((seg, i) => (
                  <div
                    key={i}
                    style={{
                      width: `${(seg.char_count / episode.script!.segments.reduce((a, s) => a + s.char_count, 0)) * 100}%`,
                      backgroundColor: speakerColors[seg.speaker] || '#6b7280',
                    }}
                  />
                ))}
              </div>
              <div className="flex justify-center gap-4 mt-2">
                {[...new Set(episode.script.segments.map((s) => s.speaker))].map((speaker) => (
                  <div key={speaker} className="flex items-center gap-1 text-xs">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: speakerColors[speaker] || '#6b7280' }}
                    />
                    <span className="text-(--color-text-muted)">{speaker}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Progress bar */}
          <div className="w-full max-w-md">
            <input
              type="range"
              min={0}
              max={duration || 100}
              value={currentTime}
              onChange={seek}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-(--color-text-muted) mt-1">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-6 mt-6">
            <button
              onClick={() => skip(-15)}
              className="text-(--color-text-secondary) hover:text-(--color-text-primary) transition"
            >
              <span className="text-2xl">⟲</span>
              <span className="text-xs block">15s</span>
            </button>

            <button
              onClick={togglePlay}
              className="w-16 h-16 rounded-full bg-(--color-accent) text-white flex items-center justify-center text-2xl hover:opacity-90 transition"
            >
              {isPlaying ? '⏸' : '▶'}
            </button>

            <button
              onClick={() => skip(30)}
              className="text-(--color-text-secondary) hover:text-(--color-text-primary) transition"
            >
              <span className="text-2xl">⟳</span>
              <span className="text-xs block">30s</span>
            </button>
          </div>
        </div>

        {/* Script panel */}
        {showScript && episode.script && (
          <div className="w-1/2 border-l border-(--color-border) overflow-y-auto p-4">
            <h4 className="font-semibold mb-4 sticky top-0 bg-(--color-background) py-2">Script</h4>
            <div className="space-y-4">
              {episode.script.segments.map((seg, i) => (
                <div key={i}>
                  <span
                    className="text-xs font-bold"
                    style={{ color: speakerColors[seg.speaker] || '#6b7280' }}
                  >
                    [{seg.speaker}]
                  </span>
                  <p className="text-sm text-(--color-text-secondary) mt-1">{seg.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Audio element */}
      <audio ref={audioRef} src={episode.audio_url ? getAudioUrl(episode.id) : undefined} preload="metadata" />
    </div>
  );
}
