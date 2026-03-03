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
    setPlayingEpisode(episode);
  };

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'queue', label: 'Queue', icon: '📥' },
    { id: 'generate', label: 'Generate', icon: '✨' },
    { id: 'episodes', label: 'Episodes', icon: '🎧' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-[--color-border] bg-[--color-surface]">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <span className="text-2xl">📻</span>
            <span>The Signal</span>
          </h1>
          <span className="text-sm text-[--color-text-muted]">AI Podcast Generator</span>
        </div>
      </header>

      {/* Tab bar */}
      <nav className="border-b border-[--color-border] bg-[--color-surface]/50 sticky top-0 z-10 backdrop-blur">
        <div className="max-w-5xl mx-auto px-4">
          <div className="flex gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 font-medium transition relative ${
                  activeTab === tab.id
                    ? 'text-[--color-accent-blue]'
                    : 'text-[--color-text-muted] hover:text-[--color-text-secondary]'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
                {activeTab === tab.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[--color-accent-blue]" />
                )}
                {tab.id === 'queue' && selectedIds.size > 0 && (
                  <span className="ml-2 px-1.5 py-0.5 text-xs bg-[--color-accent-blue] text-white rounded-full">
                    {selectedIds.size}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="flex-1 py-6">
        <div className="max-w-5xl mx-auto px-4">
          {activeTab === 'queue' && (
            <ArticleQueue
              articles={articles}
              selectedIds={selectedIds}
              onToggleSelect={toggleSelect}
              onRefresh={loadArticles}
            />
          )}

          {activeTab === 'generate' && (
            <GeneratePanel
              articles={articles}
              selectedIds={selectedIds}
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

      {/* Player overlay */}
      {playingEpisode && (
        <Player episode={playingEpisode} onClose={() => setPlayingEpisode(null)} />
      )}
    </div>
  );
}

export default App;
