"""A :class:`~vink.ports.Cache` that stores entries as files in a directory."""

import hashlib
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class FileCache:
    """Stores each entry as a UTF-8 file named after the SHA-256 of its key.

    Failures are logged and treated as cache misses, never raised: the cache
    is an optimization and must not break the main workflow.

    Args:
        directory: Directory to store entries in. Created on first write.
    """

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def get(self, key: str) -> str | None:
        """Return the cached value for ``key``, or ``None`` on a miss or read error."""
        path = self._path_for(key)
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except OSError as exc:
            logger.warning("Ignoring unreadable cache entry %s: %s", path, exc)
            return None

    def set(self, key: str, value: str) -> None:
        """Store ``value`` under ``key`` atomically; log and continue on failure."""
        path = self._path_for(key)
        try:
            self._directory.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(dir=self._directory, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(value)
            Path(temp_name).replace(path)
        except OSError as exc:
            logger.warning("Could not write cache entry %s: %s", path, exc)

    def _path_for(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self._directory / f"{digest}.json"
