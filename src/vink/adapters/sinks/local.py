"""A :class:`~vink.ports.Sink` that writes files into a local directory."""

import logging
import os
import tempfile
from pathlib import Path

from vink.domain.errors import SinkError

logger = logging.getLogger(__name__)


class LocalDirectorySink:
    """Writes each output as a UTF-8 file inside one directory.

    Names must be plain file names: anything containing a path separator or
    referring to a parent directory is rejected, so output can never escape
    the configured directory. Existing files with the same name are replaced.

    Args:
        directory: Destination directory. Created on first write.
    """

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def write(self, name: str, content: str) -> str:
        """Write ``content`` to ``<directory>/<name>`` atomically.

        Returns:
            The absolute path of the written file.

        Raises:
            SinkError: If ``name`` is not a plain file name or the write fails.
        """
        if not name or Path(name).name != name or name in {".", ".."}:
            raise SinkError(f"Refusing to write to unsafe file name {name!r}.")

        target = self._directory / name
        try:
            self._directory.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(dir=self._directory, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
            Path(temp_name).replace(target)
        except OSError as exc:
            raise SinkError(f"Could not write {target}: {exc}") from exc

        location = str(target.resolve())
        logger.info("Wrote %s", location)
        return location
