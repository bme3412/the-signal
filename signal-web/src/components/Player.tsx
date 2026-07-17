import { useState, useRef, useEffect, useMemo } from 'react';
import type { Episode, EpisodeLink, ScriptSegment } from '../types';
import { getAudioUrl, getEpisodeLinks } from '../api';
import { speakerColors } from './Transcript';

interface Props {
  episode: Episode;
  onClose: () => void;
}

interface TimedSegment extends ScriptSegment {
  index: number;
  start: number;
  end: number;
}

function formatTime(seconds: number) {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function buildTimeline(
  segments: ScriptSegment[],
  totalDuration: number,
): TimedSegment[] {
  const measured = segments.reduce((s, seg) => s + (seg.duration_seconds || 0), 0);
  const totalChars = segments.reduce((s, seg) => s + Math.max(seg.char_count, 1), 0) || 1;
  let cursor = 0;
  return segments.map((seg, index) => {
    const dur =
      seg.duration_seconds > 0
        ? seg.duration_seconds
        : measured > 0
          ? 0
          : (Math.max(seg.char_count, 1) / totalChars) * (totalDuration || 1);
    const start = cursor;
    const end = cursor + Math.max(dur, 0.01);
    cursor = end;
    return { ...seg, index, start, end };
  });
}

/** Links whose label appears in the spoken text (longest label first). */
function linksForText(text: string, links: EpisodeLink[]): EpisodeLink[] {
  const lower = text.toLowerCase();
  return links
    .filter((l) => l.kind === 'context' && l.label && lower.includes(l.label.toLowerCase()))
    .sort((a, b) => b.label.length - a.label.length);
}

function Waveform({ active, color }: { active: boolean; color: string }) {
  const bars = 12;
  return (
    <div className="flex items-end justify-center gap-1 h-14" aria-hidden>
      {Array.from({ length: bars }, (_, i) => (
        <span
          key={i}
          className={`wave-bar rounded-full ${active ? 'wave-bar-active' : ''}`}
          style={{
            backgroundColor: color,
            animationDelay: `${i * 0.08}s`,
            height: active ? undefined : `${20 + ((i * 17) % 40)}%`,
            opacity: active ? 0.85 : 0.25,
          }}
        />
      ))}
    </div>
  );
}

export function Player({ episode, onClose }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const feedRef = useRef<HTMLDivElement>(null);
  const activeLineRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(episode.audio_duration_seconds || 0);
  const [links, setLinks] = useState<EpisodeLink[]>(episode.links || []);
  const [linksLoading, setLinksLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (episode.links && episode.links.length > 0) {
      setLinks(episode.links);
      return;
    }
    setLinksLoading(true);
    getEpisodeLinks(episode.id)
      .then((data) => {
        if (!cancelled) setLinks(data);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLinksLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [episode.id, episode.links]);

  const sourceLinks = useMemo(
    () => links.filter((l) => l.kind === 'source'),
    [links],
  );
  const contextLinks = useMemo(
    () => links.filter((l) => l.kind === 'context'),
    [links],
  );

  const timeline = useMemo(() => {
    const segs = episode.script?.segments || [];
    return buildTimeline(segs, duration || episode.audio_duration_seconds || 0);
  }, [episode.script, duration, episode.audio_duration_seconds]);

  const currentIndex = useMemo(() => {
    if (timeline.length === 0) return -1;
    const idx = timeline.findIndex((s) => currentTime < s.end - 0.05);
    if (idx === -1) return timeline.length - 1;
    for (let i = 0; i < timeline.length; i++) {
      if (currentTime >= timeline[i].start && currentTime < timeline[i].end) return i;
    }
    return Math.max(0, idx);
  }, [timeline, currentTime]);

  const currentSeg = currentIndex >= 0 ? timeline[currentIndex] : null;
  const revealed = timeline.slice(0, Math.max(0, currentIndex + 1));
  const speakerColor = speakerColors[currentSeg?.speaker || ''] || 'var(--color-accent)';

  const liveLinks = useMemo(() => {
    if (!currentSeg) return [] as EpisodeLink[];
    return linksForText(currentSeg.text, contextLinks).slice(0, 4);
  }, [currentSeg, contextLinks]);

  const seenLinks = useMemo(() => {
    const out: EpisodeLink[] = [];
    const seen = new Set<string>();
    for (const seg of revealed) {
      for (const link of linksForText(seg.text, contextLinks)) {
        if (!seen.has(link.url)) {
          seen.add(link.url);
          out.push(link);
        }
      }
    }
    return out;
  }, [revealed, contextLinks]);

  const chapters = episode.script?.chapters || [];

  const chapterStarts = useMemo(() => {
    return chapters.map((ch, i) => {
      const firstIdx = ch.segment_indices[0] ?? 0;
      const timed = timeline.find((s) => s.index === firstIdx);
      const start =
        typeof ch.start_seconds === 'number' && ch.start_seconds > 0
          ? ch.start_seconds
          : timed?.start ?? 0;
      return { chapter: ch, index: i, start };
    });
  }, [chapters, timeline]);

  const activeChapterIndex = useMemo(() => {
    if (chapterStarts.length === 0) return -1;
    let idx = 0;
    for (let i = 0; i < chapterStarts.length; i++) {
      if (currentTime >= chapterStarts[i].start - 0.05) idx = i;
    }
    return idx;
  }, [chapterStarts, currentTime]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => setDuration(audio.duration);
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('ended', handleEnded);

    audio.play().catch(() => {});

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('ended', handleEnded);
    };
  }, []);

  useEffect(() => {
    activeLineRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [currentIndex]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) audio.play().catch(console.error);
    else audio.pause();
  };

  const seek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = Number(e.target.value);
  };

  const seekTo = (seconds: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = Math.max(0, Math.min(duration || seconds, seconds));
  };

  const skip = (seconds: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = Math.max(0, Math.min(duration, audio.currentTime + seconds));
  };

  const remaining = Math.max(0, (duration || 0) - currentTime);
  const progressPct = duration > 0 ? (currentTime / duration) * 100 : 0;

  const chapterFor = (segIndex: number) =>
    chapters.find((c) => c.segment_indices.includes(segIndex));

  const jumpChapter = (delta: number) => {
    if (chapterStarts.length === 0) return;
    const next = Math.max(0, Math.min(chapterStarts.length - 1, activeChapterIndex + delta));
    seekTo(chapterStarts[next].start + 0.05);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || (e.target as HTMLElement)?.isContentEditable) {
        return;
      }
      if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
      } else if (e.code === 'ArrowLeft' || e.key === 'j') {
        e.preventDefault();
        skip(e.shiftKey ? -30 : -15);
      } else if (e.code === 'ArrowRight' || e.key === 'l') {
        e.preventDefault();
        skip(e.shiftKey ? 30 : 15);
      } else if (e.key === '[') {
        e.preventDefault();
        jumpChapter(-1);
      } else if (e.key === ']') {
        e.preventDefault();
        jumpChapter(1);
      } else if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [duration, activeChapterIndex, chapterStarts.length]);

  const readingLinks =
    liveLinks.length > 0 ? liveLinks : seenLinks.length > 0 ? seenLinks.slice(0, 5) : contextLinks.slice(0, 5);

  return (
    <div className="fixed inset-0 bg-(--color-background) z-50 flex flex-col">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-(--color-border) shrink-0">
        <button
          onClick={onClose}
          className="text-(--color-text-secondary) hover:text-(--color-text-primary) text-sm"
        >
          ← Listen
        </button>
        <h2 className="font-display text-base font-semibold italic">Now playing</h2>
        <div className="font-mono text-xs text-(--color-text-muted) tabular-nums min-w-[4.5rem] text-right">
          {formatTime(remaining)} left
        </div>
      </div>

      <div className="flex-1 min-h-0 grid grid-rows-[auto_minmax(0,1fr)] lg:grid-rows-1 lg:grid-cols-[minmax(280px,38%)_minmax(0,1fr)]">
        {/* Stage + reading — scrolls as one column on desktop */}
        <aside className="min-h-0 max-h-[46vh] lg:max-h-none overflow-y-auto border-b lg:border-b-0 lg:border-r border-(--color-border)">
          <div className="px-5 pt-4 pb-5 max-w-md mx-auto lg:mx-0 lg:max-w-none">
            <div className="flex items-start gap-3">
              <div className="relative shrink-0 w-16 h-16 sm:w-20 sm:h-20 rounded-xl bg-(--color-surface) border border-(--color-border) flex items-center justify-center overflow-hidden">
                <div
                  className={`absolute inset-0 signal-rings ${isPlaying ? 'signal-rings-active' : ''}`}
                  style={{ ['--ring-color' as string]: speakerColor }}
                />
                <Waveform active={isPlaying} color={speakerColor} />
              </div>
              <div className="min-w-0 flex-1 pt-0.5">
                <h3 className="font-display text-lg font-semibold leading-snug line-clamp-2">
                  {episode.title || 'Episode'}
                </h3>
                <p className="text-(--color-text-muted) text-xs mt-1">
                  {episode.article_ids.length} article
                  {episode.article_ids.length === 1 ? '' : 's'} ·{' '}
                  {formatTime(duration || episode.audio_duration_seconds || 0)}
                </p>
                {currentSeg && (
                  <div className="mt-1.5 flex items-center gap-1.5">
                    <span
                      className="w-1.5 h-1.5 rounded-full"
                      style={{ backgroundColor: speakerColor }}
                    />
                    <span
                      className="text-[11px] font-bold tracking-wider"
                      style={{ color: speakerColor }}
                    >
                      {currentSeg.speaker}
                    </span>
                    {activeChapterIndex >= 0 && (
                      <span className="font-mono text-[10px] text-(--color-text-muted) truncate">
                        · {chapterStarts[activeChapterIndex].chapter.title}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-4 flex items-baseline gap-2">
              <span className="font-mono text-2xl font-semibold tabular-nums tracking-tight">
                {formatTime(currentTime)}
              </span>
              <span className="text-(--color-text-muted) text-xs">/</span>
              <span className="font-mono text-xs text-(--color-text-muted) tabular-nums">
                {formatTime(duration)}
              </span>
            </div>

            <div className="mt-2">
              <div className="relative h-1.5 rounded-full bg-(--color-border) overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 bg-(--color-accent) transition-[width] duration-150"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
              <input
                type="range"
                min={0}
                max={duration || 100}
                step={0.1}
                value={currentTime}
                onChange={seek}
                className="w-full mt-1 accent-(--color-accent)"
                aria-label="Seek"
              />
            </div>

            <div className="flex items-center justify-center gap-5 mt-3">
              <button
                type="button"
                onClick={() => jumpChapter(-1)}
                disabled={activeChapterIndex <= 0}
                className="text-(--color-text-secondary) hover:text-(--color-text-primary) transition disabled:opacity-30"
                title="Previous chapter ["
              >
                <span className="text-lg">⏮</span>
                <span className="text-[10px] block">chap</span>
              </button>
              <button
                type="button"
                onClick={() => skip(-15)}
                className="text-(--color-text-secondary) hover:text-(--color-text-primary) transition"
              >
                <span className="text-xl">⟲</span>
                <span className="text-[10px] block">15s</span>
              </button>
              <button
                type="button"
                onClick={togglePlay}
                className="w-14 h-14 rounded-full bg-(--color-accent) text-white flex items-center justify-center text-xl hover:opacity-90 transition shadow-sm"
              >
                {isPlaying ? '⏸' : '▶'}
              </button>
              <button
                type="button"
                onClick={() => skip(30)}
                className="text-(--color-text-secondary) hover:text-(--color-text-primary) transition"
              >
                <span className="text-xl">⟳</span>
                <span className="text-[10px] block">30s</span>
              </button>
              <button
                type="button"
                onClick={() => jumpChapter(1)}
                disabled={
                  activeChapterIndex < 0 || activeChapterIndex >= chapterStarts.length - 1
                }
                className="text-(--color-text-secondary) hover:text-(--color-text-primary) transition disabled:opacity-30"
                title="Next chapter ]"
              >
                <span className="text-lg">⏭</span>
                <span className="text-[10px] block">chap</span>
              </button>
            </div>

            {chapterStarts.length > 0 && (
              <div className="mt-4">
                <p className="font-mono text-[10px] uppercase tracking-wider text-(--color-text-muted) mb-1.5">
                  Chapters
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {chapterStarts.map(({ chapter, index, start }) => (
                    <button
                      key={`${chapter.title}-${index}`}
                      type="button"
                      onClick={() => seekTo(start + 0.05)}
                      className={`text-left px-2.5 py-1.5 rounded-lg border text-xs transition max-w-full ${
                        index === activeChapterIndex
                          ? 'border-(--color-accent) bg-(--color-accent)/10 text-(--color-accent)'
                          : 'border-(--color-border) bg-(--color-surface) text-(--color-text-secondary) hover:border-(--color-accent)'
                      }`}
                    >
                      <span className="font-medium line-clamp-1">{chapter.title}</span>
                      <span className="font-mono text-[10px] text-(--color-text-muted) block">
                        {formatTime(start)}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-5 space-y-4">
              {sourceLinks.length > 0 && (
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-wider text-(--color-text-muted) mb-1.5">
                    Sources
                  </p>
                  <ul className="space-y-1.5">
                    {sourceLinks.map((link) => (
                      <li key={link.url}>
                        <a
                          href={link.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block rounded-lg border border-(--color-border) bg-(--color-surface) px-3 py-2 hover:border-(--color-accent) transition"
                        >
                          <div className="text-xs font-medium leading-snug line-clamp-2">
                            {link.title}
                          </div>
                          <div className="font-mono text-[10px] text-(--color-text-muted) mt-0.5">
                            {link.source || 'source'} ↗
                          </div>
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {(readingLinks.length > 0 || linksLoading) && (
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-wider text-(--color-text-muted) mb-1.5">
                    {linksLoading
                      ? 'Finding related reading…'
                      : liveLinks.length > 0
                        ? 'Related right now'
                        : 'Further reading'}
                  </p>
                  <ul className="space-y-1.5 pb-2">
                    {readingLinks.map((link) => {
                      const isLive = liveLinks.some((l) => l.url === link.url);
                      return (
                        <li key={link.url}>
                          <a
                            href={link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`block rounded-lg border px-3 py-2 transition ${
                              isLive
                                ? 'border-(--color-accent) bg-(--color-accent)/8'
                                : 'border-(--color-border) bg-(--color-surface) hover:border-(--color-accent)'
                            }`}
                          >
                            <div className="flex items-baseline gap-2">
                              <span className="text-[10px] font-bold uppercase tracking-wide text-(--color-accent) shrink-0">
                                {link.label}
                              </span>
                              <span className="font-mono text-[10px] text-(--color-text-muted) truncate">
                                {link.source}
                              </span>
                            </div>
                            <div className="text-xs font-medium leading-snug mt-0.5 line-clamp-2">
                              {link.title}
                            </div>
                            {link.snippet && (
                              <p className="text-[11px] text-(--color-text-muted) mt-0.5 line-clamp-2">
                                {link.snippet}
                              </p>
                            )}
                          </a>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}
            </div>

            <p className="font-mono text-[10px] text-(--color-text-muted) pt-1">
              Space play · ←/→ seek · [/] chapters · Esc back
            </p>
          </div>
        </aside>

        {/* Transcript */}
        <section className="min-h-0 flex flex-col bg-(--color-surface)/40">
          <div className="px-5 py-3 border-b border-(--color-border) flex items-center justify-between shrink-0 gap-3">
            <div className="min-w-0">
              <h4 className="font-display font-semibold">Live transcript</h4>
              <p className="text-xs text-(--color-text-muted)">
                Tap a line to jump · scroll freely
              </p>
            </div>
            <span className="font-mono text-[11px] text-(--color-text-muted) shrink-0">
              {revealed.length}/{timeline.length}
            </span>
          </div>

          <div ref={feedRef} className="flex-1 min-h-0 overflow-y-auto px-5 py-4 space-y-3">
            {timeline.length === 0 && (
              <p className="text-sm text-(--color-text-muted)">No script available for this episode.</p>
            )}

            {revealed.map((seg) => {
              const isActive = seg.index === currentIndex;
              const chapter = chapterFor(seg.index);
              const prevChapter =
                seg.index > 0 ? chapterFor(seg.index - 1) : undefined;
              const showChapter =
                chapter && (!prevChapter || prevChapter.title !== chapter.title);
              const segLinks = linksForText(seg.text, contextLinks).slice(0, 2);

              return (
                <div key={seg.index}>
                  {showChapter && (
                    <div className="flex items-center gap-2 mb-2 mt-1 sticky top-0 z-[1] bg-(--color-surface)/90 backdrop-blur-sm py-1 -mx-1 px-1">
                      <span className="font-mono text-[10px] uppercase tracking-wider text-(--color-text-muted)">
                        {chapter.role}
                      </span>
                      <span className="text-xs font-semibold text-(--color-text-secondary)">
                        {chapter.title}
                      </span>
                    </div>
                  )}
                  <div
                    ref={isActive ? activeLineRef : undefined}
                    onClick={() => seekTo(seg.start + 0.05)}
                    className={`feed-line rounded-xl border px-3.5 py-3 cursor-pointer transition ${
                      isActive
                        ? 'border-(--color-accent) bg-(--color-accent)/8 shadow-sm'
                        : 'border-(--color-border) bg-(--color-surface) hover:border-(--color-text-muted)'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className="text-[11px] font-bold tracking-wide"
                        style={{ color: speakerColors[seg.speaker] || '#6b7280' }}
                      >
                        {seg.speaker}
                      </span>
                      <span className="font-mono text-[10px] text-(--color-text-muted)">
                        {formatTime(seg.start)}
                      </span>
                      {isActive && isPlaying && (
                        <span className="ml-auto flex items-center gap-1">
                          <span className="studio-dot w-1.5 h-1.5 rounded-full bg-(--color-accent)" />
                          <span className="font-mono text-[10px] text-(--color-accent)">
                            speaking
                          </span>
                        </span>
                      )}
                    </div>
                    <p
                      className={`text-sm leading-relaxed ${
                        isActive
                          ? 'text-(--color-text-primary)'
                          : 'text-(--color-text-secondary)'
                      }`}
                    >
                      {seg.text}
                    </p>
                    {segLinks.length > 0 && (
                      <div className="flex flex-col gap-1 mt-2">
                        {segLinks.map((link) => (
                          <a
                            key={link.url}
                            href={link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-[11px] px-2 py-1 rounded-lg border border-(--color-border) text-(--color-text-secondary) hover:border-(--color-accent) hover:text-(--color-accent) transition"
                          >
                            <span className="font-bold text-(--color-accent)">{link.label}</span>
                            {' · '}
                            <span className="line-clamp-1 inline">{link.title}</span>
                            {' ↗'}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {currentIndex >= 0 && currentIndex < timeline.length - 1 && (
              <div className="opacity-35 pointer-events-none">
                <p className="font-mono text-[10px] uppercase tracking-wider text-(--color-text-muted) mb-2">
                  Up next
                </p>
                <div className="rounded-xl border border-dashed border-(--color-border) px-3.5 py-3">
                  <span
                    className="text-[11px] font-bold"
                    style={{
                      color: speakerColors[timeline[currentIndex + 1].speaker] || '#6b7280',
                    }}
                  >
                    {timeline[currentIndex + 1].speaker}
                  </span>
                  <p className="text-sm text-(--color-text-muted) mt-1 line-clamp-2">
                    {timeline[currentIndex + 1].text}
                  </p>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>

      <audio
        ref={audioRef}
        src={episode.audio_url ? getAudioUrl(episode.id) : undefined}
        preload="metadata"
      />
    </div>
  );
}
