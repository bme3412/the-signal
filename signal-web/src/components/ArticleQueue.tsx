import { useState } from 'react';
import type { Article } from '../types';
import * as api from '../api';

interface Props {
  articles: Article[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onRefresh: () => void;
}

export function ArticleQueue({ articles, selectedIds, onToggleSelect, onRefresh }: Props) {
  const [showAddModal, setShowAddModal] = useState(false);
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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Article Queue</h2>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-[--color-accent-blue] text-white rounded-lg font-medium hover:opacity-90 transition"
        >
          + Add Article
        </button>
      </div>

      {articles.length === 0 ? (
        <div className="text-center py-12 text-[--color-text-muted]">
          <p>No articles in queue.</p>
          <p className="text-sm mt-2">Add articles to generate a podcast episode.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {articles.map((article) => (
            <div
              key={article.id}
              className={`p-4 rounded-xl border transition cursor-pointer ${
                selectedIds.has(article.id)
                  ? 'bg-[--color-accent-blue]/10 border-[--color-accent-blue]'
                  : 'bg-[--color-surface] border-[--color-border] hover:border-[--color-text-muted]'
              }`}
              onClick={() => onToggleSelect(article.id)}
            >
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={selectedIds.has(article.id)}
                  onChange={() => onToggleSelect(article.id)}
                  className="mt-1 w-4 h-4 accent-[--color-accent-blue]"
                  onClick={(e) => e.stopPropagation()}
                />
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium truncate">{article.title}</h3>
                  <div className="flex items-center gap-3 mt-1 text-sm text-[--color-text-muted]">
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
                  className="p-2 text-[--color-text-muted] hover:text-red-500 transition"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Article Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-[--color-surface] rounded-2xl p-6 w-full max-w-lg border border-[--color-border]">
            <h3 className="text-lg font-semibold mb-4">Add Article</h3>

            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setAddMode('url')}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  addMode === 'url'
                    ? 'bg-[--color-accent-blue] text-white'
                    : 'bg-[--color-background] text-[--color-text-secondary]'
                }`}
              >
                From URL
              </button>
              <button
                onClick={() => setAddMode('manual')}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  addMode === 'manual'
                    ? 'bg-[--color-accent-blue] text-white'
                    : 'bg-[--color-background] text-[--color-text-secondary]'
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
                  className="w-full px-4 py-3 bg-[--color-background] border border-[--color-border] rounded-lg focus:outline-none focus:border-[--color-accent-blue]"
                  required
                />
              ) : (
                <>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Article title"
                    className="w-full px-4 py-3 bg-[--color-background] border border-[--color-border] rounded-lg focus:outline-none focus:border-[--color-accent-blue]"
                    required
                  />
                  <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Paste article content..."
                    rows={6}
                    className="w-full px-4 py-3 bg-[--color-background] border border-[--color-border] rounded-lg focus:outline-none focus:border-[--color-accent-blue] resize-none"
                    required
                  />
                </>
              )}

              {error && <p className="text-red-500 text-sm">{error}</p>}

              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-[--color-text-secondary] hover:text-[--color-text-primary] transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 bg-[--color-accent-blue] text-white rounded-lg font-medium hover:opacity-90 transition disabled:opacity-50"
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
