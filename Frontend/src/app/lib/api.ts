/**
 * API client for the Medium Clone FastAPI backend.
 *
 * All response types match the backend's camelCase pydantic serialization.
 */

import { queryCache } from './queryCache';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface PaginationMeta {
  page: number;
  limit: number;
  totalItems: number;
  totalPages: number;
}

export interface ArticleAuthor {
  id: string;
  name: string;
  avatar: string | null;
  bio: string | null;
}

export interface ArticleSummary {
  id: string;
  title: string;
  subtitle: string | null;
  author: ArticleAuthor;
  publication: string | null;
  readingTime: number;
  tags: string[];
  claps: number;
  date: string;
  coverImage: string | null;
}

export interface ArticleDetail {
  id: string;
  title: string;
  subtitle: string | null;
  author: ArticleAuthor;
  publication: string | null;
  readingTime: number;
  tags: string[];
  claps: number;
  date: string;
  content: string[];
  coverImage: string | null;
}

export interface UserInfo {
  id: string;
  email: string;
  name: string;
  avatar: string | null;
  bio: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface AuthorProfile {
  id: string;
  name: string;
  avatar: string | null;
  bio: string | null;
  followers: number;
  following: number;
  articles: number;
  isFollowing: boolean;
}

export interface ResponseItem {
  id: string;
  articleId: string;
  articleTitle: string;
  text: string;
  date: string;
  likes: number;
  author: ArticleAuthor;
  parentId: string | null;
  replyCount: number;
  isEdited: boolean;
}

export interface InlineResponseItem {
  id: string;
  articleId: string;
  userId: string;
  selectedText: string;
  paragraphIndex: number;
  text: string;
  date: string;
  likes: number;
}

export interface HighlightItem {
  id: string;
  articleId: string;
  articleTitle: string;
  text: string;
  color: string;
  date: string;
  paragraphIndex: number | null;
}

export interface ReadingHistoryEntry {
  id: string;
  articleId: string;
  title: string;
  date: string;
  timeSpent: number;
  readPercentage: number;
  tags: string[];
}

export interface AnalyticsTagCount {
  tag: string;
  count: number;
}

export interface ReadingStreak {
  currentDays: number;
  longestDays: number;
}

export interface MonthlyBreakdown {
  month: string;
  articlesRead: number;
  timeSpentMinutes: number;
}

export interface ReadingAnalytics {
  totalArticlesRead: number;
  totalTimeSpentMinutes: number;
  averageReadingTimeMinutes: number;
  averageReadPercentage: number;
  topTags: AnalyticsTagCount[];
  readingStreak: ReadingStreak;
  monthlyBreakdown: MonthlyBreakdown[];
}

export interface SearchSection {
  data: any[];
  total: number;
}

export interface SearchResponse {
  stories: SearchSection | null;
  people: SearchSection | null;
  publications: SearchSection | null;
  pagination: PaginationMeta;
}

export interface FollowState {
  following: boolean;
  followerCount: number;
}

export interface ClapResponse {
  totalClaps: number;
}

export interface ResponseClapResponse {
  likes: number;
}

export interface SaveResponse {
  saved: boolean;
  articleId: string;
}

export interface Paginated<T> {
  data: T[];
  pagination: PaginationMeta;
  totalResponseCount?: number;
  total_response_count?: number;
}

// ─── API Client ──────────────────────────────────────────────────────────────

export class ApiClient {
  private getToken: () => Promise<string | null>;

  constructor(getToken: () => Promise<string | null>) {
    this.getToken = getToken;
  }

  private async headers(auth = false): Promise<Record<string, string>> {
    const h: Record<string, string> = { 'Content-Type': 'application/json' };
    if (auth) {
      const token = await this.getToken();
      if (token) h['Authorization'] = `Bearer ${token}`;
    }
    return h;
  }

  /**
   * Return the cache TTL in milliseconds for a given HTTP method + path, or
   * `null` if the response should not be cached.
   *
   * Only cacheable (read-only, non-personalised) resources:
   *   /user/{id}/articles  → article feed        30 s
   *   /search              → search results     120 s
   */
  private _getCacheTtlMs(method: string, path: string): number | null {
    if (method !== 'GET') return null;
    if (/^\/user\/[^/]+\/articles/.test(path))           return 30_000;
    if (path.startsWith('/search'))                       return 120_000;
    return null;
  }

  private async request<T>(
    method: string,
    path: string,
    options: { body?: unknown; auth?: boolean; params?: Record<string, string | number> } = {}
  ): Promise<T> {
    const { body, auth = false, params } = options;

    let url = `${API_URL}${path}`;
    if (params) {
      const qs = new URLSearchParams();
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null && v !== '') qs.append(k, String(v));
      }
      const qsStr = qs.toString();
      if (qsStr) url += `?${qsStr}`;
    }

    // ── Client-side cache check ───────────────────────────────────────────
    const cacheTtl = this._getCacheTtlMs(method, path);
    if (cacheTtl !== null) {
      const hit = queryCache.get<T>(url);
      if (hit !== null) return hit;
    }

    const doFetch = async (tokenOverride?: string | null) => {
      const headers = await this.headers(auth);
      if (tokenOverride) headers['Authorization'] = `Bearer ${tokenOverride}`;
      return fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });
    };

    let res = await doFetch();

    if (res.status === 401 && auth && this.getToken) {
      // Allow caller to inject refresh logic or token retry
      const retryToken = await this.getToken();
      if (retryToken) {
         res = await doFetch(retryToken);
      }
    }

    if (res.status === 204) return undefined as T;

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `API error ${res.status}`);
    }

    const data: T = await res.json();

    // ── Populate cache ────────────────────────────────────────────────────
    if (cacheTtl !== null) {
      queryCache.set<T>(url, data, cacheTtl);
    }

    return data;
  }

  // ── Auth ──────────────────────────────────────────────────────────────────

  syncUser(): Promise<UserInfo> {
    return this.request('POST', '/auth/sync', { auth: true });
  }

  getMe(): Promise<UserInfo> {
    return this.request('GET', '/auth/me', { auth: true });
  }

  // ── Articles ──────────────────────────────────────────────────────────────

  getArticles(opts: {
    userId?: string;
    tag?: string;
    sort?: string;
    page?: number;
    limit?: number;
  } = {}): Promise<Paginated<ArticleSummary>> {
    // The feed endpoint requires a userId in the path but doesn't filter by it.
    const uid = opts.userId || '00000000-0000-0000-0000-000000000000';
    const params: Record<string, string | number> = {};
    if (opts.tag) params.tag = opts.tag;
    if (opts.sort) params.sort = opts.sort;
    if (opts.page) params.page = opts.page;
    if (opts.limit) params.limit = opts.limit;
    return this.request('GET', `/user/${uid}/articles`, { params });
  }

  getArticle(articleId: string): Promise<ArticleDetail> {
    return this.request('GET', `/articles/${articleId}`);
  }

  clapArticle(articleId: string, userId: string, count = 1): Promise<ClapResponse> {
    return this.request('POST', `/articles/${articleId}/clap/${userId}`, {
      auth: true,
      body: { userId, count },
    });
  }

  trackReading(articleId: string, timeSpent: number, readPercentage = 0): Promise<{ tracked: boolean }> {
    return this.request('POST', `/articles/${articleId}/track`, {
      auth: true,
      body: { timeSpent, readPercentage },
    });
  }

  /**
   * Fire-and-forget reading tracker using fetch with keepalive.
   * Reliable even during page unload / SPA navigation.
   */
  trackReadingBeacon(articleId: string, timeSpent: number, readPercentage = 0): void {
    const url = `${API_URL}/articles/${articleId}/track`;
    const body = JSON.stringify({ timeSpent, readPercentage });

    // getToken() resolves synchronously (returns ref value wrapped in Promise)
    this.getToken().then((token) => {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      // fetch with keepalive survives page unload
      fetch(url, {
        method: 'POST',
        headers,
        body,
        keepalive: true,
      }).catch(() => {});
    }).catch(() => {});
  }

  saveArticle(userId: string, articleId: string): Promise<SaveResponse> {
    return this.request('POST', `/users/${userId}/library/saved/${articleId}`, { auth: true });
  }

  getSavedArticleState(userId: string, articleId: string): Promise<SaveResponse> {
    return this.request('GET', `/users/${userId}/library/saved/${articleId}`, { auth: true });
  }

  unsaveArticle(userId: string, articleId: string): Promise<void> {
    return this.request('DELETE', `/users/${userId}/library/saved/${articleId}`, { auth: true });
  }

  // ── Responses (Comments) ──────────────────────────────────────────────────

  getResponses(articleId: string, page = 1, limit = 20): Promise<Paginated<ResponseItem>> {
    return this.request('GET', `/articles/${articleId}/responses`, {
      params: { page, limit },
    });
  }

  createResponse(articleId: string, userId: string, text: string): Promise<ResponseItem> {
    return this.request('POST', `/articles/${articleId}/responses/${userId}`, {
      auth: true,
      body: { userId, text },
    });
  }

  deleteResponse(articleId: string, userId: string, responseId: string): Promise<void> {
    return this.request('DELETE', `/articles/${articleId}/responses/${userId}/${responseId}`, {
      auth: true,
    });
  }

  updateResponse(articleId: string, userId: string, responseId: string, text: string): Promise<ResponseItem> {
    return this.request('PUT', `/articles/${articleId}/responses/${userId}/${responseId}`, {
      auth: true,
      body: { userId, text },
    });
  }

  getReplies(articleId: string, responseId: string, page = 1, limit = 20): Promise<Paginated<ResponseItem>> {
    return this.request('GET', `/articles/${articleId}/responses/${responseId}/replies`, {
      params: { page, limit },
    });
  }

  createReply(articleId: string, responseId: string, userId: string, text: string): Promise<ResponseItem> {
    return this.request('POST', `/articles/${articleId}/responses/${responseId}/replies/${userId}`, {
      auth: true,
      body: { userId, text },
    });
  }

  clapResponse(articleId: string, responseId: string, userId: string, count = 1): Promise<ResponseClapResponse> {
    return this.request('POST', `/articles/${articleId}/responses/${responseId}/clap/${userId}`, {
      auth: true,
      body: { userId, count },
    });
  }

  // ── Inline Responses ──────────────────────────────────────────────────────

  getInlineResponses(articleId: string, page = 1, limit = 50): Promise<Paginated<InlineResponseItem>> {
    return this.request('GET', `/articles/${articleId}/inline-responses`, {
      auth: true,
      params: { page, limit },
    });
  }

  createInlineResponse(
    articleId: string,
    userId: string,
    data: { selectedText: string; paragraphIndex: number; text: string }
  ): Promise<InlineResponseItem> {
    return this.request('POST', `/articles/${articleId}/inline-responses/${userId}`, {
      auth: true,
      body: { userId, ...data },
    });
  }

  // ── Highlights ────────────────────────────────────────────────────────────

  getArticleHighlights(articleId: string, userId: string): Promise<Paginated<HighlightItem>> {
    return this.request('GET', `/articles/${articleId}/highlights/${userId}`, { auth: true });
  }

  createHighlight(
    articleId: string,
    userId: string,
    data: { text: string; color?: string; paragraphIndex?: number }
  ): Promise<HighlightItem> {
    return this.request('POST', `/articles/${articleId}/highlight/${userId}`, {
      auth: true,
      body: { userId, articleId, ...data },
    });
  }

  deleteHighlight(articleId: string, userId: string, highlightId: string): Promise<void> {
    return this.request('DELETE', `/articles/${articleId}/highlights/${userId}/${highlightId}`, {
      auth: true,
    });
  }

  // ── Authors ───────────────────────────────────────────────────────────────

  getAuthors(page = 1, limit = 20): Promise<Paginated<AuthorProfile>> {
    return this.request('GET', '/authors', { params: { page, limit }, auth: true });
  }

  getAuthor(authorId: string): Promise<AuthorProfile> {
    return this.request('GET', `/authors/${authorId}`, { auth: true });
  }

  followAuthor(authorId: string, userId: string): Promise<FollowState> {
    return this.request('POST', `/authors/${authorId}/follow/${userId}`, { auth: true });
  }

  unfollowAuthor(authorId: string, userId: string): Promise<FollowState> {
    return this.request('DELETE', `/authors/${authorId}/unfollow/${userId}`, { auth: true });
  }

  // ── Publications ──────────────────────────────────────────────────────────

  followPublication(publicationId: string, userId: string): Promise<FollowState> {
    return this.request('POST', `/publications/${publicationId}/follow/${userId}`, { auth: true });
  }

  unfollowPublication(publicationId: string, userId: string): Promise<FollowState> {
    return this.request('DELETE', `/publications/${publicationId}/unfollow/${userId}`, { auth: true });
  }

  // ── Search ────────────────────────────────────────────────────────────────

  search(q: string, type?: string, page = 1, limit = 20): Promise<SearchResponse> {
    const params: Record<string, string | number> = { q, page, limit };
    if (type) params.type = type;
    return this.request('GET', '/search', { params });
  }

  // ── Library ───────────────────────────────────────────────────────────────

  getSavedArticles(userId: string, page = 1, limit = 20): Promise<Paginated<ArticleSummary>> {
    return this.request('GET', `/users/${userId}/library/saved`, {
      auth: true,
      params: { page, limit },
    });
  }

  getLibraryHighlights(userId: string, page = 1, limit = 20): Promise<Paginated<HighlightItem>> {
    return this.request('GET', `/users/${userId}/library/highlights`, {
      auth: true,
      params: { page, limit },
    });
  }

  getReadingHistory(userId: string, page = 1, limit = 20): Promise<Paginated<ReadingHistoryEntry>> {
    return this.request('GET', `/users/${userId}/library/history`, {
      auth: true,
      params: { page, limit },
    });
  }

  getUserResponses(userId: string, page = 1, limit = 20): Promise<Paginated<ResponseItem>> {
    return this.request('GET', `/users/${userId}/library/responses`, {
      auth: true,
      params: { page, limit },
    });
  }

  getUserInlineResponses(userId: string, page = 1, limit = 50): Promise<Paginated<InlineResponseItem>> {
    return this.request('GET', `/users/${userId}/library/inline-responses`, {
      auth: true,
      params: { page, limit },
    });
  }

  deleteLibraryHighlight(userId: string, highlightId: string): Promise<void> {
    return this.request('DELETE', `/users/${userId}/library/highlights/${highlightId}`, {
      auth: true,
    });
  }

  deleteHistoryEntry(userId: string, historyId: string): Promise<void> {
    return this.request('DELETE', `/users/${userId}/library/history/${historyId}`, {
      auth: true,
    });
  }

  deleteLibraryResponse(userId: string, articleId: string, responseId: string): Promise<void> {
    return this.request('DELETE', `/users/${userId}/library/responses/${articleId}/${responseId}`, {
      auth: true,
    });
  }

  getReadingAnalytics(userId: string): Promise<ReadingAnalytics> {
    return this.request('GET', `/users/${userId}/library/history/analytics`, { auth: true });
  }
}
