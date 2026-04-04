"""Lightweight in-memory TTL cache for service-layer results.

Stores arbitrary Python objects keyed by a string with a per-key
time-to-live (TTL).  Expired entries are evicted lazily on the next
``get`` call for that key.

All methods are **synchronous** — no ``asyncio.Lock`` is needed because:
  • Python's GIL prevents concurrent dict mutations across threads, and
  • in a single-process async server (uvicorn) coroutines only yield at
    ``await`` points, so plain dict access between awaits is atomic.

Usage
-----
    from app.common.cache import cache_store

    # Try cache first, fall back to DB:
    result = cache_store.get("articles:list:latest:1:20")
    if result is None:
        result = await expensive_db_query()
        cache_store.set("articles:list:latest:1:20", result, ttl=30)
    return result

    # Invalidate an entire namespace (prefix match):
    cache_store.delete_prefix("articles:list:")
"""

import time
from typing import Any


class _InMemoryCache:
    """A single-process in-memory store with per-key TTL."""

    def __init__(self) -> None:
        # {key: (value, monotonic_expires_at)}
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        """Return the cached value for *key*, or ``None`` if missing / expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() < expires_at:
            return value
        # Lazy eviction of expired entry
        del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        """Store *value* under *key*, expiring after *ttl* seconds."""
        self._store[key] = (value, time.monotonic() + ttl)

    def delete(self, key: str) -> None:
        """Remove a single key (no-op if absent)."""
        self._store.pop(key, None)

    def delete_prefix(self, prefix: str) -> None:
        """Remove every key that starts with *prefix*."""
        to_delete = [k for k in self._store if k.startswith(prefix)]
        for k in to_delete:
            del self._store[k]

    def clear(self) -> None:
        """Evict all cached entries."""
        self._store.clear()


# ---------------------------------------------------------------------------
# Application-wide singleton – import and use this directly.
# ---------------------------------------------------------------------------
cache_store = _InMemoryCache()
