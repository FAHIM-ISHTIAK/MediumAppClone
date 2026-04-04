/**
 * Client-side in-memory TTL cache for API GET responses.
 *
 * This is a plain-Map store (no external dependency) that lives for the
 * lifetime of the browser tab.  Entries expire lazily: they are evicted on
 * the next `get()` call once their TTL has elapsed.
 *
 * The cache is a module-level singleton so every `ApiClient` instance shares
 * the same store, which means navigating between pages never re-fetches the
 * same data within the TTL window.
 *
 * Cache keys are the fully-qualified request URLs (including query string)
 * so every unique set of parameters gets its own slot.
 *
 * TTLs (configured in api.ts):
 *   - Article feed      /user/.../articles  → 30 s
 *   - Article detail    /articles/:id       → 60 s
 *   - Search results    /search             → 120 s
 *   - Author profiles   /authors/...        → 30 s
 *   - Publications      /publications/...   → 60 s
 */

interface CacheEntry<T = unknown> {
  data: T;
  /** Unix timestamp (ms) after which this entry is considered stale. */
  expiresAt: number;
}

class QueryCache {
  private readonly store = new Map<string, CacheEntry>();

  /**
   * Return the cached value for *key*, or `null` if the entry is absent or
   * has expired.  Expired entries are lazily evicted on read.
   */
  get<T>(key: string): T | null {
    const entry = this.store.get(key) as CacheEntry<T> | undefined;
    if (!entry) return null;
    if (Date.now() < entry.expiresAt) return entry.data;
    // Lazy eviction
    this.store.delete(key);
    return null;
  }

  /** Store *data* under *key*, expiring after *ttlMs* milliseconds. */
  set<T>(key: string, data: T, ttlMs: number): void {
    this.store.set(key, { data, expiresAt: Date.now() + ttlMs });
  }

  /** Remove a single cache entry (no-op if absent). */
  delete(key: string): void {
    this.store.delete(key);
  }

  /**
   * Remove every cache entry whose key starts with *prefix*.
   * Useful for invalidating an entire resource namespace after a mutation,
   * e.g. `deletePrefix('http://api/articles/abc123')`.
   */
  deletePrefix(prefix: string): void {
    for (const key of this.store.keys()) {
      if (key.startsWith(prefix)) this.store.delete(key);
    }
  }

  /** Evict all entries (e.g. on sign-out). */
  clear(): void {
    this.store.clear();
  }
}

/** Application-wide singleton – import this in api.ts and anywhere else. */
export const queryCache = new QueryCache();
