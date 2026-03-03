from __future__ import annotations

from models import Article, Episode, EpisodeStatus


class Store:
    def __init__(self) -> None:
        self._articles: dict[str, Article] = {}
        self._episodes: dict[str, Episode] = {}

    # --- Articles ---

    def add_article(self, article: Article) -> Article:
        self._articles[article.id] = article
        return article

    def get_article(self, article_id: str) -> Article | None:
        return self._articles.get(article_id)

    def list_articles(self) -> list[Article]:
        return list(self._articles.values())

    def update_article(self, article_id: str, **kwargs) -> Article | None:
        article = self._articles.get(article_id)
        if not article:
            return None
        updated = article.model_copy(update=kwargs)
        self._articles[article_id] = updated
        return updated

    def delete_article(self, article_id: str) -> bool:
        return self._articles.pop(article_id, None) is not None

    # --- Episodes ---

    def create_episode(self, episode: Episode) -> Episode:
        self._episodes[episode.id] = episode
        return episode

    def get_episode(self, episode_id: str) -> Episode | None:
        return self._episodes.get(episode_id)

    def list_episodes(self) -> list[Episode]:
        return sorted(self._episodes.values(), key=lambda e: e.created_at, reverse=True)

    def update_episode(self, episode_id: str, **kwargs) -> Episode | None:
        episode = self._episodes.get(episode_id)
        if not episode:
            return None
        updated = episode.model_copy(update=kwargs)
        self._episodes[episode_id] = updated
        return updated

    def update_status(self, episode_id: str, status: EpisodeStatus) -> Episode | None:
        return self.update_episode(episode_id, status=status)
