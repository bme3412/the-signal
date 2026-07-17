import { useState, useEffect, useCallback } from 'react';
import type { Article, Episode } from './types';
import { ArticleQueue } from './components/ArticleQueue';
import { GeneratePanel } from './components/GeneratePanel';
import { EpisodeList } from './components/EpisodeList';
import { Player } from './components/Player';
import * as api from './api';

type Tab = 'queue' | 'generate' | 'episodes';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('queue');
  const [articles, setArticles] = useState<Article[]>([]);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [playingEpisode, setPlayingEpisode] = useState<Episode | null>(null);
  const [backendDown, setBackendDown] = useState(false);
  const [episodeFocus, setEpisodeFocus] = useState('');

  const loadArticles = useCallback(async () => {
    try {
      const data = await api.listArticles();
      setArticles(data);
    } catch (err) {
      console.error('Failed to load articles:', err);
    }
  }, []);

  const loadEpisodes = useCallback(async () => {
    try {
      const data = await api.listEpisodes();
      setEpisodes(data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
    } catch (err) {
      console.error('Failed to load episodes:', err);
    }
  }, []);

  useEffect(() => {
    api.checkHealth().then((ok) => setBackendDown(!ok));
    loadArticles();
    loadEpisodes();
  }, [loadArticles, loadEpisodes]);

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleEpisodeReady = (episode: Episode) => {
    loadEpisodes();
    setActiveTab('episodes');
    setPlayingEpisode(episode);
  };

  const readyCount = episodes.filter((e) => e.status === 'ready').length;
  const selectedWords = articles
    .filter((a) => selectedIds.has(a.id))
    .reduce((sum, a) => sum + a.word_count, 0);

  const steps: { id: Tab; num: string; label: string; hint: string }[] = [
    {
      id: 'queue',
      num: '01',
      label: 'Queue',
      hint: `${articles.length} article${articles.length === 1 ? '' : 's'}`,
    },
    {
      id: 'generate',
      num: '02',
      label: 'Compose',
      hint: selectedIds.size > 0 ? `${selectedIds.size} selected` : 'pick a style',
    },
    {
      id: 'episodes',
      num: '03',
      label: 'Listen',
      hint: `${readyCount} ready`,
    },
  ];

  const showContinueBar = activeTab === 'queue' && selectedIds.size > 0 && !playingEpisode;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Masthead */}
      <header className="bg-(--color-surface) border-b-2 border-(--color-text-primary)">
        <div className="max-w-3xl mx-auto px-6 pt-6 pb-4 flex items-end justify-between">
          <div className="flex items-center gap-3">
            <span className="onair-dot w-3 h-3 rounded-full bg-(--color-accent) shrink-0" />
            <h1 className="font-display text-3xl font-semibold italic tracking-tight leading-none">
              The Signal
            </h1>
          </div>
          <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-(--color-text-muted) pb-1">
            turn reading into radio
          </span>
        </div>
      </header>

      {/* Backend connectivity warning */}
      {backendDown && (
        <div className="bg-(--color-accent) text-white">
          <div className="max-w-3xl mx-auto px-6 py-2.5 text-sm">
            <strong>No backend connected.</strong>{' '}
            {import.meta.env.VITE_API_URL
              ? 'The configured backend is unreachable — check that it is running.'
              : window.location.hostname === 'localhost'
              ? 'Start it with: cd signal-backend && uvicorn main:app --reload'
              : 'This deployed site has no API server. Run the app locally (localhost:5173), or host the backend and set VITE_API_URL in Vercel.'}
          </div>
        </div>
      )}

      {/* Pipeline nav */}
      <nav className="bg-(--color-surface) border-b border-(--color-border) sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-6">
          <div className="flex items-stretch">
            {steps.map((step, i) => (
              <div key={step.id} className="flex items-stretch">
                {i > 0 && (
                  <span className="self-center px-3 sm:px-5 text-(--color-text-muted) select-none" aria-hidden>
                    →
                  </span>
                )}
                <button
                  onClick={() => setActiveTab(step.id)}
                  className={`relative py-3.5 text-left transition-colors ${
                    activeTab === step.id
                      ? 'text-(--color-text-primary)'
                      : 'text-(--color-text-muted) hover:text-(--color-text-secondary)'
                  }`}
                >
                  <span className="flex items-baseline gap-2">
                    <span
                      className={`font-mono text-[11px] ${
                        activeTab === step.id ? 'text-(--color-accent)' : ''
                      }`}
                    >
                      {step.num}
                    </span>
                    <span className="font-semibold">{step.label}</span>
                    <span className="hidden sm:inline font-mono text-[11px] text-(--color-text-muted)">
                      {step.hint}
                    </span>
                  </span>
                  {activeTab === step.id && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-(--color-accent)" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="flex-1 py-8">
        <div className="max-w-3xl mx-auto px-6">
          {activeTab === 'queue' && (
            <ArticleQueue
              articles={articles}
              selectedIds={selectedIds}
              onToggleSelect={toggleSelect}
              onRefresh={loadArticles}
              onFocusSuggested={setEpisodeFocus}
            />
          )}

          {activeTab === 'generate' && (
            <GeneratePanel
              articles={articles}
              selectedIds={selectedIds}
              onToggleSelect={toggleSelect}
              onEditSelection={() => setActiveTab('queue')}
              focus={episodeFocus}
              onFocusChange={setEpisodeFocus}
              onEpisodeReady={handleEpisodeReady}
            />
          )}

          {activeTab === 'episodes' && (
            <EpisodeList
              episodes={episodes}
              onSelect={setPlayingEpisode}
              onRefresh={loadEpisodes}
            />
          )}
        </div>

        {/* Continue bar: sits right under a short list, pins to the viewport
            bottom while scrolling a long one */}
        {showContinueBar && (
          <div className="sticky bottom-6 z-20 mt-6 px-6 pointer-events-none">
            <div className="max-w-3xl mx-auto flex justify-center">
              <div className="rise pointer-events-auto flex items-center gap-4 bg-(--color-surface) border border-(--color-border) rounded-full pl-5 pr-2 py-2 shadow-[0_8px_30px_rgba(34,29,21,0.15)]">
                <span className="font-mono text-xs text-(--color-text-secondary)">
                  {selectedIds.size} article{selectedIds.size === 1 ? '' : 's'} ·{' '}
                  {selectedWords.toLocaleString()} words
                </span>
                <button
                  onClick={() => setActiveTab('generate')}
                  className="px-4 py-2 bg-(--color-accent) text-white rounded-full font-semibold text-sm hover:opacity-90 transition"
                >
                  Compose episode →
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Player overlay */}
      {playingEpisode && (
        <Player episode={playingEpisode} onClose={() => setPlayingEpisode(null)} />
      )}
    </div>
  );
}

export default App;
