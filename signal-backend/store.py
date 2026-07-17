from __future__ import annotations

import os
import sqlite3
import threading

from models import Article, Episode, EpisodeStatus, ProgressEvent


def _fts_quote(term: str) -> str:
    return '"' + term.replace('"', '""') + '"'


class Store:
    """SQLite-backed store.

    Articles and episodes are persisted as JSON documents keyed by id.
    An FTS5 index over article title/text/summary/topics/entities powers
    knowledge-base search and related-article lookup.
    """

    def __init__(self, db_path: str = "./data/signal.db") -> None:
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS episodes (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                    id UNINDEXED, title, body, summary, topics, entities
                );
                """
            )

    # --- Articles ---

    def _index_article(self, article: Article) -> None:
        self._conn.execute("DELETE FROM articles_fts WHERE id = ?", (article.id,))
        self._conn.execute(
            "INSERT INTO articles_fts (id, title, body, summary, topics, entities) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                article.id,
                article.title,
                article.text,
                article.summary or "",
                " ".join(article.topics),
                " ".join(article.entities),
            ),
        )

    def add_article(self, article: Article) -> Article:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO articles (id, data, created_at) VALUES (?, ?, ?)",
                (article.id, article.model_dump_json(), article.created_at.isoformat()),
            )
            self._index_article(article)
        return article

    def get_article(self, article_id: str) -> Article | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM articles WHERE id = ?", (article_id,)
            ).fetchone()
        return Article.model_validate_json(row["data"]) if row else None

    def list_articles(self) -> list[Article]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT data FROM articles ORDER BY created_at"
            ).fetchall()
        return [Article.model_validate_json(r["data"]) for r in rows]

    def update_article(self, article_id: str, **kwargs) -> Article | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM articles WHERE id = ?", (article_id,)
            ).fetchone()
            if not row:
                return None
            updated = Article.model_validate_json(row["data"]).model_copy(update=kwargs)
            with self._conn:
                self._conn.execute(
                    "UPDATE articles SET data = ? WHERE id = ?",
                    (updated.model_dump_json(), article_id),
                )
                self._index_article(updated)
        return updated

    def delete_article(self, article_id: str) -> bool:
        with self._lock, self._conn:
            cur = self._conn.execute(
                "DELETE FROM articles WHERE id = ?", (article_id,)
            )
            self._conn.execute("DELETE FROM articles_fts WHERE id = ?", (article_id,))
        return cur.rowcount > 0

    # --- Knowledge base search ---

    def _fts_search(
        self, match_expr: str, limit: int, exclude_ids: set[str] | None = None
    ) -> list[Article]:
        exclude_ids = exclude_ids or set()
        with self._lock:
            try:
                rows = self._conn.execute(
                    "SELECT id FROM articles_fts WHERE articles_fts MATCH ? "
                    "ORDER BY rank LIMIT ?",
                    (match_expr, limit + len(exclude_ids)),
                ).fetchall()
            except sqlite3.OperationalError:
                return []  # malformed FTS query
            ids = [r["id"] for r in rows if r["id"] not in exclude_ids][:limit]
            articles = []
            for aid in ids:
                row = self._conn.execute(
                    "SELECT data FROM articles WHERE id = ?", (aid,)
                ).fetchone()
                if row:
                    articles.append(Article.model_validate_json(row["data"]))
        return articles

    def search_articles(self, query: str, limit: int = 10) -> list[Article]:
        """Full-text search; all terms must match."""
        terms = [_fts_quote(t) for t in query.split()]
        if not terms:
            return []
        return self._fts_search(" ".join(terms), limit)

    def find_related(
        self, terms: list[str], exclude_ids: set[str] | None = None, limit: int = 5
    ) -> list[Article]:
        """Articles matching ANY of the given topic/entity terms, best first."""
        quoted = [_fts_quote(t) for t in terms if t.strip()]
        if not quoted:
            return []
        return self._fts_search(" OR ".join(quoted), limit, exclude_ids)

    # --- Episodes ---

    def create_episode(self, episode: Episode) -> Episode:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO episodes (id, data, created_at) VALUES (?, ?, ?)",
                (episode.id, episode.model_dump_json(), episode.created_at.isoformat()),
            )
        return episode

    def get_episode(self, episode_id: str) -> Episode | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM episodes WHERE id = ?", (episode_id,)
            ).fetchone()
        return Episode.model_validate_json(row["data"]) if row else None

    def list_episodes(self) -> list[Episode]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT data FROM episodes ORDER BY created_at DESC"
            ).fetchall()
        return [Episode.model_validate_json(r["data"]) for r in rows]

    def update_episode(self, episode_id: str, **kwargs) -> Episode | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM episodes WHERE id = ?", (episode_id,)
            ).fetchone()
            if not row:
                return None
            updated = Episode.model_validate_json(row["data"]).model_copy(update=kwargs)
            with self._conn:
                self._conn.execute(
                    "UPDATE episodes SET data = ? WHERE id = ?",
                    (updated.model_dump_json(), episode_id),
                )
        return updated

    def update_status(self, episode_id: str, status: EpisodeStatus) -> Episode | None:
        return self.update_episode(episode_id, status=status)

    def add_progress(
        self, episode_id: str, stage: EpisodeStatus, message: str
    ) -> Episode | None:
        """Append a human-readable progress line to an episode's live log."""
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM episodes WHERE id = ?", (episode_id,)
            ).fetchone()
            if not row:
                return None
            episode = Episode.model_validate_json(row["data"])
            episode.progress.append(ProgressEvent(stage=stage, message=message))
            with self._conn:
                self._conn.execute(
                    "UPDATE episodes SET data = ? WHERE id = ?",
                    (episode.model_dump_json(), episode_id),
                )
        return episode
