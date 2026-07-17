import type { Article, DiscoverResult, Episode, EpisodeAngle, EpisodeRequest, EpisodeScript, VoicesResponse } from './types';

// In production, set VITE_API_URL to your backend URL (e.g., https://api.yourdomain.com)
// and VITE_API_TOKEN to the backend's SIGNAL_API_TOKEN.
const BASE_URL = import.meta.env.VITE_API_URL || '';
const API_TOKEN = import.meta.env.VITE_API_TOKEN || '';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}),
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`HTTP ${res.status}: ${body}`);
  }

  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) return false;
    const body = await res.json();
    return body?.status === 'ok';
  } catch {
    return false;
  }
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

export async function suggestAngles(topic: string, results: DiscoverResult[]): Promise<EpisodeAngle[]> {
  return request('/api/discover/angles', {
    method: 'POST',
    body: JSON.stringify({ topic, results }),
  });
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
  // <audio> elements cannot send headers, so the token rides as a query param
  const suffix = API_TOKEN ? `?token=${encodeURIComponent(API_TOKEN)}` : '';
  return `${BASE_URL}/api/episodes/${episodeId}/audio${suffix}`;
}
