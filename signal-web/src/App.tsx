import { useState, useEffect, useCallback, useRef } from 'react';
import type { Article, Episode } from './types';
import { ArticleQueue } from './components/ArticleQueue';
import { GeneratePanel } from './components/GeneratePanel';
import { EpisodeList } from './components/EpisodeList';
import { Player } from './components/Player';
import * as api from './api';

type Tab = 'queue' | 'generate' | 'episodes';

/** Group key for exclusive topic selection (one collection at a time). */
function collectionKey(article: Article) {
  return article.collection || '__ungrouped__';
}

/** Article ids in the newest topic (by latest article timestamp). */
function newestCollectionIds(data: Article[]): string[] {
  if (data.length === 0) return [];
  const latestByCol = new Map<string, number>();
  for (const a of data) {
    const key = collectionKey(a);
    const t = new Date(a.created_at).getTime();
    latestByCol.set(key, Math.max(latestByCol.get(key) ?? 0, t));
  }
  let bestKey = collectionKey(data[0]);
  let bestT = -1;
  for (const [key, t] of latestByCol) {
    if (t > bestT) {
      bestT = t;
      bestKey = key;
    }
  }
  return data.filter((a) => collectionKey(a) === bestKey).map((a) => a.id);
}

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('queue');
  const [articles, setArticles] = useState<Article[]>([]);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [playingEpisode, setPlayingEpisode] = useState<Episode | null>(null);
  const [backendDown, setBackendDown] = useState(false);
  const [episodeFocus, setEpisodeFocus] = useState('');
  const [composeBusy, setComposeBusy] = useState(false);
  // Track which article IDs we've already seen so new ones can be auto-selected.
  const knownArticleIds = useRef<Set<string>>(new Set());

  const loadArticles = useCallback(async () => {
    try {
      const data = await api.listArticles();
      const liveIds = data.map((a) => a.id);
      const live = new Set(liveIds);
      const known = knownArticleIds.current;
      const brandNew = liveIds.filter((id) => !known.has(id));
      knownArticleIds.current = live;
      const byId = new Map(data.map((a) => [a.id, a]));

      setArticles(data);
      // One topic at a time: never merge articles across collections.
      setSelectedIds((prev) => {
        if (prev.size === 0 && live.size > 0) {
          return new Set(newestCollectionIds(data));
        }
        const kept = [...prev].filter((id) => live.has(id));
        if (kept.length === 0) {
          return brandNew.length > 0
            ? new Set(
                data
                  .filter((a) => brandNew.includes(a.id))
                  .filter((a) => collectionKey(a) === collectionKey(byId.get(brandNew[0])!))
                  .map((a) => a.id)
              )
            : new Set(newestCollectionIds(data));
        }
        const activeKey = collectionKey(byId.get(kept[0])!);
        const next = new Set(kept.filter((id) => collectionKey(byId.get(id)!) === activeKey));
        // Auto-check new articles only if they belong to the active topic.
        for (const id of brandNew) {
          const a = byId.get(id);
          if (a && collectionKey(a) === activeKey) next.add(id);
        }
        return next;
      });
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
      const article = articles.find((a) => a.id === id);
      if (!article) return prev;
      const key = collectionKey(article);
      if (prev.has(id)) {
        const next = new Set(prev);
        next.delete(id);
        return next;
      }
      // Selecting from another topic replaces the selection — no cross-topic merge.
      const next = new Set<string>();
      for (const sid of prev) {
        const a = articles.find((x) => x.id === sid);
        if (a && collectionKey(a) === key) next.add(sid);
      }
      next.add(id);
      return next;
    });
  };

  /** Replace selection with these ids (one topic). Used after Discover / group check. */
  const selectIds = (ids: string[]) => {
    setSelectedIds(new Set(ids));
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

  const showContinueBar =
    activeTab === 'queue' && selectedIds.size > 0 && !playingEpisode && !composeBusy;

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
            your reading, as a podcast
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

      {/* Main content — pad bottom when compose bar / studio dock is up */}
      <main className={`flex-1 py-8 ${showContinueBar || composeBusy ? 'pb-28' : ''}`}>
        <div className="max-w-3xl mx-auto px-6">
          {activeTab === 'queue' && (
            <ArticleQueue
              articles={articles}
              selectedIds={selectedIds}
              onToggleSelect={toggleSelect}
              onSelectIds={selectIds}
              onRefresh={loadArticles}
              onFocusSuggested={setEpisodeFocus}
            />
          )}

          {(activeTab === 'generate' || composeBusy) && (
            <GeneratePanel
              articles={articles}
              selectedIds={selectedIds}
              onToggleSelect={toggleSelect}
              onEditSelection={() => setActiveTab('queue')}
              onGoListen={() => setActiveTab('episodes')}
              onGoCompose={() => setActiveTab('generate')}
              visible={activeTab === 'generate'}
              onBusyChange={setComposeBusy}
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
      </main>

      {/* Fixed compose CTA — always visible at the bottom of the viewport */}
      {showContinueBar && (
        <div className="fixed inset-x-0 bottom-0 z-30 border-t-2 border-(--color-text-primary) bg-(--color-surface) shadow-[0_-12px_40px_rgba(34,29,21,0.12)]">
          <div className="max-w-3xl mx-auto px-6 py-4 flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-6">
            <div className="flex-1 min-w-0">
              <p className="font-display text-lg font-semibold leading-tight">
                Ready to compose
              </p>
              <p className="font-mono text-xs text-(--color-text-secondary) mt-0.5">
                {selectedIds.size} article{selectedIds.size === 1 ? '' : 's'} ·{' '}
                {selectedWords.toLocaleString()} words selected
              </p>
            </div>
            <button
              onClick={() => setActiveTab('generate')}
              className="w-full sm:w-auto shrink-0 px-6 py-3.5 bg-(--color-accent) text-white rounded-full font-semibold text-base hover:opacity-90 transition shadow-sm"
            >
              Compose episode →
            </button>
          </div>
        </div>
      )}

      {/* Player overlay */}
      {playingEpisode && (
        <Player episode={playingEpisode} onClose={() => setPlayingEpisode(null)} />
      )}
    </div>
  );
}

export default App;
