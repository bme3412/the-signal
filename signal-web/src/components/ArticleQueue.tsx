import { useMemo, useState } from 'react';
import type { Article } from '../types';
import { DiscoverModal } from './DiscoverModal';
import * as api from '../api';

const UNGROUPED = 'Saved articles';

interface Props {
  articles: Article[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onRefresh: () => void;
  onFocusSuggested: (focus: string) => void;
}

export function ArticleQueue({ articles, selectedIds, onToggleSelect, onRefresh, onFocusSuggested }: Props) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDiscover, setShowDiscover] = useState(false);
  const [addMode, setAddMode] = useState<'url' | 'manual'>('url');
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (addMode === 'url') {
        await api.submitArticleByUrl(url);
      } else {
        await api.submitArticleManual(title, text);
      }
      setShowAddModal(false);
      setUrl('');
      setTitle('');
      setText('');
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add article');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteArticle(id);
      onRefresh();
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  const groups = useMemo(() => {
    const map = new Map<string, Article[]>();
    for (const article of articles) {
      const key = article.collection || UNGROUPED;
      const list = map.get(key) || [];
      list.push(article);
      map.set(key, list);
    }
    // Topic groups first (newest article first within each), loose saves last
    return [...map.entries()].sort(([a], [b]) =>
      a === UNGROUPED ? 1 : b === UNGROUPED ? -1 : 0
    );
  }, [articles]);

  const toggleGroup = (groupArticles: Article[], allSelected: boolean) => {
    for (const article of groupArticles) {
      const isSelected = selectedIds.has(article.id);
      if (allSelected ? isSelected : !isSelected) {
        onToggleSelect(article.id);
      }
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="font-display text-2xl font-semibold">The queue</h2>
          <p className="text-sm text-(--color-text-secondary) mt-1">
            Save articles here, then select the ones for your next episode.
          </p>
        </div>
        <div className="flex gap-2 shrink-0">
          <button
            onClick={() => setShowDiscover(true)}
            className="px-4 py-2 bg-(--color-surface) border border-(--color-border) text-(--color-text-secondary) rounded-full font-semibold text-sm hover:border-(--color-accent) hover:text-(--color-text-primary) transition"
          >
            Discover topic
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-(--color-accent) text-white rounded-full font-semibold text-sm hover:opacity-90 transition"
          >
            + Add article
          </button>
        </div>
      </div>

      {articles.length === 0 ? (
        <div className="rise text-center py-16 px-6 bg-(--color-surface) border border-(--color-border) rounded-2xl">
          <p className="font-display text-2xl italic mb-2">Nothing in the queue.</p>
          <p className="text-(--color-text-secondary)">
            Add an article by URL or paste text — it becomes tomorrow's episode.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {groups.map(([name, groupArticles]) => {
            const allSelected = groupArticles.every((a) => selectedIds.has(a.id));
            const someSelected = groupArticles.some((a) => selectedIds.has(a.id));
            return (
              <section key={name}>
                <div className="flex items-center gap-3 mb-2 px-1">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    ref={(el) => {
                      if (el) el.indeterminate = someSelected && !allSelected;
                    }}
                    onChange={() => toggleGroup(groupArticles, allSelected)}
                    title={allSelected ? 'Deselect all' : 'Select all in this topic'}
                    className="w-4 h-4 accent-(--color-accent)"
                  />
                  <h3 className="font-display text-lg font-semibold italic">{name}</h3>
                  <span className="font-mono text-[11px] text-(--color-text-muted)">
                    {groupArticles.length} article{groupArticles.length === 1 ? '' : 's'}
                  </span>
                </div>
                <div className="space-y-2">
                  {groupArticles.map((article) => (
                    <div
                      key={article.id}
                      className={`p-4 rounded-xl border transition cursor-pointer ${
                        selectedIds.has(article.id)
                          ? 'bg-(--color-accent)/10 border-(--color-accent)'
                          : 'bg-(--color-surface) border-(--color-border) hover:border-(--color-text-muted)'
                      }`}
                      onClick={() => onToggleSelect(article.id)}
                    >
                      <div className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          checked={selectedIds.has(article.id)}
                          onChange={() => onToggleSelect(article.id)}
                          className="mt-1 w-4 h-4 accent-(--color-accent)"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium truncate">{article.title}</h3>
                          <div className="flex items-center gap-3 mt-1 text-sm text-(--color-text-muted)">
                            <span>{article.source}</span>
                            <span>•</span>
                            <span>{article.word_count.toLocaleString()} words</span>
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(article.id);
                          }}
                          className="p-2 text-(--color-text-muted) hover:text-red-500 transition"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}

      {showDiscover && (
        <DiscoverModal
          onClose={() => setShowDiscover(false)}
          onAdded={onRefresh}
          onFocusSuggested={onFocusSuggested}
        />
      )}

      {/* Add Article Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-(--color-surface) rounded-2xl p-6 w-full max-w-lg border border-(--color-border)">
            <h3 className="font-display text-xl font-semibold mb-4">Add article</h3>

            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setAddMode('url')}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  addMode === 'url'
                    ? 'bg-(--color-accent) text-white'
                    : 'bg-(--color-background) text-(--color-text-secondary)'
                }`}
              >
                From URL
              </button>
              <button
                onClick={() => setAddMode('manual')}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  addMode === 'manual'
                    ? 'bg-(--color-accent) text-white'
                    : 'bg-(--color-background) text-(--color-text-secondary)'
                }`}
              >
                Manual Entry
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {addMode === 'url' ? (
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/article"
                  className="w-full px-4 py-3 bg-(--color-background) border border-(--color-border) rounded-lg focus:outline-none focus:border-(--color-accent)"
                  required
                />
              ) : (
                <>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Article title"
                    className="w-full px-4 py-3 bg-(--color-background) border border-(--color-border) rounded-lg focus:outline-none focus:border-(--color-accent)"
                    required
                  />
                  <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Paste article content..."
                    rows={6}
                    className="w-full px-4 py-3 bg-(--color-background) border border-(--color-border) rounded-lg focus:outline-none focus:border-(--color-accent) resize-none"
                    required
                  />
                </>
              )}

              {error && <p className="text-red-600 text-sm">{error}</p>}

              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-(--color-text-secondary) hover:text-(--color-text-primary) transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 bg-(--color-accent) text-white rounded-lg font-medium hover:opacity-90 transition disabled:opacity-50"
                >
                  {loading ? 'Adding...' : 'Add'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
