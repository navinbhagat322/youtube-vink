"""Timestamped JSON entries on top of any :class:`~vink.ports.Cache`."""

import json
import logging
import time
from collections.abc import Callable

from vink.adapters.cache.serialization import JsonData
from vink.ports.cache import Cache

logger = logging.getLogger(__name__)

Clock = Callable[[], float]
"""Returns the current time in seconds since the epoch."""


class TimedEntries:
    """Stores JSON data with the time it was saved, and expires it on read.

    Corrupt and expired entries are treated as misses, so callers simply
    refetch and overwrite them.

    Args:
        cache: Underlying key-value store.
        clock: Time source; injectable for tests.
    """

    def __init__(self, cache: Cache, clock: Clock = time.time) -> None:
        self._cache = cache
        self._clock = clock

    def get(self, key: str, *, max_age: float | None = None) -> JsonData | None:
        """Return the data stored under ``key``.

        Args:
            key: Cache key.
            max_age: Maximum age in seconds, or ``None`` for entries that never expire.

        Returns:
            The stored data, or ``None`` if missing, corrupt or older than ``max_age``.
        """
        raw = self._cache.get(key)
        if raw is None:
            return None
        try:
            envelope = json.loads(raw)
            saved_at = float(envelope["saved_at"])
            data = envelope["data"]
        except (ValueError, TypeError, KeyError) as exc:
            logger.warning("Discarding corrupt cache entry %s: %s", key, exc)
            return None
        if max_age is not None and self._clock() - saved_at > max_age:
            logger.debug("Cache entry %s expired", key)
            return None
        return data

    def set(self, key: str, data: JsonData) -> None:
        """Store ``data`` under ``key`` with the current time."""
        envelope = {"saved_at": self._clock(), "data": data}
        self._cache.set(key, json.dumps(envelope, ensure_ascii=False))
