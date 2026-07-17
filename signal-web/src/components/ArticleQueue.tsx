import { useMemo, useState } from 'react';
import type { Article } from '../types';
import { DiscoverModal } from './DiscoverModal';
import * as api from '../api';

const UNGROUPED = 'Saved articles';

interface Props {
  articles: Article[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onRefresh: () => void | Promise<void>;
  onFocusSuggested: (focus: string) => void;
  onSelectIds: (ids: string[]) => void;
}

export function ArticleQueue({
  articles,
  selectedIds,
  onToggleSelect,
  onRefresh,
  onFocusSuggested,
  onSelectIds,
}: Props) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDiscover, setShowDiscover] = useState(false);
  /** Which topic group's More panel is open. */
  const [moreGroup, setMoreGroup] = useState<string | null>(null);
  /** Collection to attach when adding via Discover / Add article. */
  const [activeCollection, setActiveCollection] = useState<string | null>(null);
  // Groups start open; track which ones the user has collapsed.
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());

  const toggleExpanded = (name: string) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const openDiscover = (groupName?: string) => {
    setActiveCollection(groupName && groupName !== UNGROUPED ? groupName : null);
    setShowDiscover(true);
    setMoreGroup(null);
  };

  const openAdd = (groupName?: string) => {
    setActiveCollection(groupName && groupName !== UNGROUPED ? groupName : null);
    setShowAddModal(true);
    setMoreGroup(null);
  };

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
      const collection = activeCollection || undefined;
      if (addMode === 'url') {
        await api.submitArticleByUrl(url, collection);
      } else {
        await api.submitArticleManual(title, text, 'manual', collection);
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
    // Newest topic first; ungrouped saves last. Never merge distinct collections.
    return [...map.entries()].sort(([aName, aArts], [bName, bArts]) => {
      if (aName === UNGROUPED) return 1;
      if (bName === UNGROUPED) return -1;
      const aLatest = Math.max(...aArts.map((x) => new Date(x.created_at).getTime()));
      const bLatest = Math.max(...bArts.map((x) => new Date(x.created_at).getTime()));
      return bLatest - aLatest;
    });
  }, [articles]);

  const toggleGroup = (groupArticles: Article[], allSelected: boolean) => {
    if (allSelected) {
      // Deselect this topic only.
      onSelectIds([]);
    } else {
      // Exclusive: check this topic alone — never merge with another.
      onSelectIds(groupArticles.map((a) => a.id));
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl font-semibold">The queue</h2>
          <p className="text-sm text-(--color-text-secondary) mt-1">
            One topic at a time — pick a group for the next episode.
          </p>
        </div>
        {articles.length > 0 && (
          <button
            onClick={() => openDiscover()}
            className="shrink-0 px-4 py-2 rounded-full font-semibold text-sm border bg-(--color-surface) text-(--color-text-secondary) border-(--color-border) hover:border-(--color-accent) hover:text-(--color-text-primary) transition"
          >
            New topic
          </button>
        )}
      </div>

      {articles.length === 0 ? (
        <div className="rise text-center py-16 px-6 bg-(--color-surface) border border-(--color-border) rounded-2xl space-y-4">
          <div>
            <p className="font-display text-2xl italic mb-2">Nothing in the queue.</p>
            <p className="text-(--color-text-secondary)">
              Add an article by URL or paste text — it becomes tomorrow's episode.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            <button
              onClick={() => openDiscover()}
              className="px-4 py-2 bg-(--color-surface) border border-(--color-border) text-(--color-text-secondary) rounded-full font-semibold text-sm hover:border-(--color-accent) hover:text-(--color-text-primary) transition"
            >
              Discover topic
            </button>
            <button
              onClick={() => openAdd()}
              className="px-4 py-2 bg-(--color-accent) text-white rounded-full font-semibold text-sm hover:opacity-90 transition"
            >
              + Add article
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {groups.map(([name, groupArticles]) => {
            const allSelected = groupArticles.every((a) => selectedIds.has(a.id));
            const someSelected = groupArticles.some((a) => selectedIds.has(a.id));
            const isExpanded = !collapsedGroups.has(name);
            const selectedCount = groupArticles.filter((a) => selectedIds.has(a.id)).length;
            const moreOpen = moreGroup === name;
            const isTopic = name !== UNGROUPED;
            return (
              <section
                key={name}
                className="bg-(--color-surface) border border-(--color-border) rounded-2xl overflow-hidden"
              >
                <div className="flex items-center gap-3 px-4 py-3">
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
                  <button
                    onClick={() => toggleExpanded(name)}
                    className="flex items-baseline gap-3 flex-1 min-w-0 text-left"
                  >
                    <h3 className="font-display text-lg font-semibold italic truncate">{name}</h3>
                    <span className="font-mono text-[11px] text-(--color-text-muted) shrink-0">
                      {groupArticles.length} article{groupArticles.length === 1 ? '' : 's'}
                      {selectedCount > 0 && ` · ${selectedCount} selected`}
                    </span>
                  </button>
                  <button
                    onClick={() => toggleExpanded(name)}
                    className="shrink-0 w-8 h-8 flex items-center justify-center rounded-full text-lg font-semibold leading-none bg-(--color-background) border border-(--color-border) text-(--color-text-secondary) hover:border-(--color-accent) hover:text-(--color-text-primary) transition"
                    aria-expanded={isExpanded}
                    aria-label={isExpanded ? 'Collapse group' : 'Expand group'}
                    title={isExpanded ? 'Collapse' : 'Expand'}
                  >
                    {isExpanded ? '−' : '+'}
                  </button>
                </div>
                {isExpanded && (
                <div className="px-3 pb-3 space-y-2 border-t border-(--color-border) pt-3">
                  {groupArticles.map((article) => (
                    <div
                      key={article.id}
                      className={`p-4 rounded-xl border transition cursor-pointer ${
                        selectedIds.has(article.id)
                          ? 'bg-(--color-accent)/10 border-(--color-accent)'
                          : 'bg-(--color-background) border-(--color-border) hover:border-(--color-text-muted)'
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

                  {/* More — add further articles into this topic */}
                  <div className="pt-1">
                    <button
                      onClick={() => setMoreGroup(moreOpen ? null : name)}
                      aria-expanded={moreOpen}
                      className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition ${
                        moreOpen
                          ? 'bg-(--color-accent) text-white border-(--color-accent)'
                          : 'bg-(--color-background) text-(--color-text-secondary) border-(--color-border) hover:border-(--color-accent) hover:text-(--color-text-primary)'
                      }`}
                    >
                      {moreOpen ? 'Less' : 'More'}
                    </button>
                    <div className="more-panel mt-2" data-open={moreOpen}>
                      <div className="more-panel-inner">
                        <div className="flex flex-wrap gap-2 pb-1">
                          {isTopic && (
                            <button
                              onClick={() => openDiscover(name)}
                              className="px-4 py-2 bg-(--color-background) border border-(--color-border) text-(--color-text-secondary) rounded-full font-semibold text-sm hover:border-(--color-accent) hover:text-(--color-text-primary) transition"
                            >
                              Find more on this topic
                            </button>
                          )}
                          <button
                            onClick={() => openAdd(name)}
                            className="px-4 py-2 bg-(--color-accent) text-white rounded-full font-semibold text-sm hover:opacity-90 transition"
                          >
                            + Add article
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                )}
              </section>
            );
          })}
        </div>
      )}

      {showDiscover && (
        <DiscoverModal
          initialTopic={activeCollection || ''}
          forceCollection={activeCollection || undefined}
          onClose={() => setShowDiscover(false)}
          onAdded={onRefresh}
          onFocusSuggested={onFocusSuggested}
          onFinished={async (info) => {
            setShowDiscover(false);
            await onRefresh();
            // Expand the topic and check every article in that category.
            try {
              const latest = await api.listArticles();
              const urlSet = new Set(info.urls);
              // Prefer the group we opened from when searching for more on a topic.
              const collection = info.collection || activeCollection || '';
              const groupName = collection || UNGROUPED;
              const inCollection = collection
                ? latest.filter((a) => a.collection === collection)
                : latest.filter((a) => a.url && urlSet.has(a.url));
              const ids = inCollection.map((a) => a.id);
              if (ids.length > 0) onSelectIds(ids);
              setCollapsedGroups((prev) => {
                if (!prev.has(groupName)) return prev;
                const next = new Set(prev);
                next.delete(groupName);
                return next;
              });
            } catch (err) {
              console.error('Failed to select discovered articles:', err);
            }
          }}
        />
      )}

      {/* Add Article Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-(--color-surface) rounded-2xl p-6 w-full max-w-lg border border-(--color-border)">
            <h3 className="font-display text-xl font-semibold mb-1">Add article</h3>
            {activeCollection && (
              <p className="text-sm text-(--color-text-secondary) mb-4">
                Adding to <span className="italic">{activeCollection}</span>
              </p>
            )}
            {!activeCollection && <div className="mb-4" />}

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
