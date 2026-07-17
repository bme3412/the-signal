import type { Article, DiscoverResult, Episode, EpisodeRequest, EpisodeScript, VoicesResponse } from './types';

// In production, set VITE_API_URL to your backend URL (e.g., https://api.yourdomain.com)
const BASE_URL = import.meta.env.VITE_API_URL || '';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`HTTP ${res.status}: ${body}`);
  }

  return res.json();
}

// Articles
export async function listArticles(): Promise<Article[]> {
  return request('/api/articles');
}

export async function submitArticleByUrl(url: string, collection?: string): Promise<Article> {
  return request('/api/articles', {
    method: 'POST',
    body: JSON.stringify({ url, collection }),
  });
}

export async function submitArticleManual(title: string, text: string, source = 'manual'): Promise<Article> {
  return request('/api/articles', {
    method: 'POST',
    body: JSON.stringify({ title, text, source }),
  });
}

export async function deleteArticle(id: string): Promise<void> {
  await request(`/api/articles/${id}`, { method: 'DELETE' });
}

export async function discoverArticles(
  topic: string,
  recency: string = 'week',
  limit: number = 8
): Promise<DiscoverResult[]> {
  return request('/api/discover', {
    method: 'POST',
    body: JSON.stringify({ topic, recency, limit }),
  });
}

// Episodes
export async function getVoices(): Promise<VoicesResponse> {
  return request('/api/episodes/voices');
}

export async function generateEpisode(req: EpisodeRequest): Promise<Episode> {
  return request('/api/episodes/generate', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function getEpisode(id: string): Promise<Episode> {
  return request(`/api/episodes/${id}`);
}

export async function getScript(episodeId: string): Promise<EpisodeScript> {
  return request(`/api/episodes/${episodeId}/script`);
}

export async function listEpisodes(): Promise<Episode[]> {
  return request('/api/episodes');
}

export function getAudioUrl(episodeId: string): string {
  return `${BASE_URL}/api/episodes/${episodeId}/audio`;
}
