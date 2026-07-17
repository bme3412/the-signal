import { useState } from 'react';
import type { DiscoverResult } from '../types';
import * as api from '../api';

interface Props {
  onClose: () => void;
  onAdded: () => void;
}

const recencyOptions = [
  { value: 'day', label: 'Past day' },
  { value: 'week', label: 'Past week' },
  { value: 'month', label: 'Past month' },
  { value: 'any', label: 'Any time' },
];

type AddState = 'adding' | 'added' | { error: string };

export function DiscoverModal({ onClose, onAdded }: Props) {
  const [topic, setTopic] = useState('');
  const [searchedTopic, setSearchedTopic] = useState('');
  const [recency, setRecency] = useState('week');
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [results, setResults] = useState<DiscoverResult[] | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [addStates, setAddStates] = useState<Record<string, AddState>>({});
  const [addingAll, setAddingAll] = useState(false);

  const search = async (e: React.FormEvent) => {
    e.preventDefault();
    setSearching(true);
    setSearchError(null);
    setResults(null);
    setSelected(new Set());
    setAddStates({});
    setSearchedTopic(topic.trim());
    try {
      setResults(await api.discoverArticles(topic, recency));
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const toggle = (url: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(url)) {
        next.delete(url);
      } else {
        next.add(url);
      }
      return next;
    });
  };

  const addSelected = async () => {
    setAddingAll(true);
    for (const url of selected) {
      if (addStates[url] === 'added') continue;
      setAddStates((s) => ({ ...s, [url]: 'adding' }));
      try {
        await api.submitArticleByUrl(url, searchedTopic);
        setAddStates((s) => ({ ...s, [url]: 'added' }));
        onAdded();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed';
        setAddStates((s) => ({ ...s, [url]: { error: message } }));
      }
    }
    setAddingAll(false);
  };

  const pendingCount = [...selected].filter((u) => addStates[u] !== 'added').length;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-(--color-surface) rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col border border-(--color-border)"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 pb-4">
          <h3 className="font-display text-xl font-semibold mb-1">Discover by topic</h3>
          <p className="text-sm text-(--color-text-secondary) mb-4">
            Search the web for recent coverage, then pick what goes in the queue.
          </p>

          <form onSubmit={search} className="flex gap-2">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. semiconductor export controls"
              className="flex-1 px-4 py-2.5 bg-(--color-background) border border-(--color-border) rounded-lg focus:outline-none focus:border-(--color-accent)"
              autoFocus
              required
              minLength={2}
            />
            <select
              value={recency}
              onChange={(e) => setRecency(e.target.value)}
              className="px-3 py-2.5 bg-(--color-background) border border-(--color-border) rounded-lg text-sm text-(--color-text-secondary) focus:outline-none"
            >
              {recencyOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <button
              type="submit"
              disabled={searching}
              className="px-5 py-2.5 bg-(--color-accent) text-white rounded-lg font-semibold text-sm hover:opacity-90 transition disabled:opacity-50"
            >
              {searching ? 'Searching…' : 'Search'}
            </button>
          </form>

          {searchError && <p className="text-red-600 text-sm mt-3">{searchError}</p>}
        </div>

        {/* Results */}
        <div className="flex-1 overflow-y-auto px-6 space-y-2">
          {results && results.length === 0 && (
            <p className="text-(--color-text-muted) text-sm py-6 text-center">
              Nothing found — try a broader topic or a longer time window.
            </p>
          )}
          {results?.map((r) => {
            const state = addStates[r.url];
            const isAdded = r.in_queue || state === 'added';
            const isSelected = selected.has(r.url);
            return (
              <div
                key={r.url}
                onClick={() => !isAdded && toggle(r.url)}
                className={`p-3 rounded-xl border transition ${
                  isAdded
                    ? 'bg-(--color-background) border-(--color-border) opacity-60'
                    : isSelected
                    ? 'bg-(--color-accent)/10 border-(--color-accent) cursor-pointer'
                    : 'bg-(--color-surface) border-(--color-border) hover:border-(--color-text-muted) cursor-pointer'
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    checked={isSelected || isAdded}
                    disabled={isAdded}
                    onChange={() => toggle(r.url)}
                    onClick={(e) => e.stopPropagation()}
                    className="mt-1 w-4 h-4 accent-(--color-accent)"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm truncate">{r.title}</span>
                      {isAdded && (
                        <span className="font-mono text-[10px] text-(--color-accent-alt) shrink-0">
                          IN QUEUE
                        </span>
                      )}
                      {state === 'adding' && (
                        <span className="font-mono text-[10px] text-(--color-text-muted) shrink-0">
                          ADDING…
                        </span>
                      )}
                    </div>
                    {r.description && (
                      <p className="text-xs text-(--color-text-secondary) mt-0.5 line-clamp-2">
                        {r.description}
                      </p>
                    )}
                    <span className="font-mono text-[11px] text-(--color-text-muted)">{r.source}</span>
                    {typeof state === 'object' && (
                      <p className="text-xs text-red-600 mt-1">{state.error}</p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="p-6 pt-4 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-(--color-text-secondary) hover:text-(--color-text-primary) transition text-sm"
          >
            {Object.values(addStates).some((s) => s === 'added') ? 'Done' : 'Cancel'}
          </button>
          {results && results.length > 0 && (
            <button
              onClick={addSelected}
              disabled={pendingCount === 0 || addingAll}
              className="px-5 py-2.5 bg-(--color-accent) text-white rounded-full font-semibold text-sm hover:opacity-90 transition disabled:opacity-50"
            >
              {addingAll
                ? 'Adding…'
                : `Add ${pendingCount || ''} to queue`.replace('  ', ' ')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
