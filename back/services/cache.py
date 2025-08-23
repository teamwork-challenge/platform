from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Generic, Optional, TypeVar, Dict, Tuple

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    value: T
    expires_at: datetime
    hard_expires_at: Optional[datetime] = None

    def is_valid(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        if now >= self.expires_at:
            return False
        if self.hard_expires_at is not None and now >= self.hard_expires_at:
            return False
        return True


class InMemoryCache(Generic[T]):
    """A minimal in-memory cache with per-item TTL and optional hard deadline.

    - TTL: soft expiration, default 10 minutes
    - hard_expires_at: absolute timestamp to invalidate, e.g., end of current round
    """

    def __init__(self, default_ttl: timedelta | None = timedelta(minutes=10)) -> None:
        self._store: Dict[str, CacheEntry[T]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[T]:
        entry: Optional[CacheEntry[T]] = self._store.get(key)
        if entry is None:
            return None
        if not entry.is_valid():
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: T, ttl: Optional[timedelta] = None, hard_expires_at: Optional[datetime] = None) -> None:
        ttl_ = ttl if ttl is not None else self._default_ttl
        now = datetime.now(timezone.utc)
        expires_at = now + (ttl_ or timedelta(0))
        self._store[key] = CacheEntry[T](value=value, expires_at=expires_at, hard_expires_at=hard_expires_at)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
