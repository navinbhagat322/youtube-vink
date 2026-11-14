"""Port for a simple key-value cache."""

from typing import Protocol


class Cache(Protocol):
    """Stores serialized values under string keys.

    The cache is an optimization only: a miss must never be an error, and
    callers must work correctly when every lookup misses.
    """

    def get(self, key: str) -> str | None:
        """Return the cached value for ``key``, or ``None`` on a miss."""
        ...

    def set(self, key: str, value: str) -> None:
        """Store ``value`` under ``key``, replacing any existing value."""
        ...
