"""Composition root: the only place that knows which adapter backs which port.

Interfaces call :func:`build_container` once at startup and use the services
it returns. To swap an implementation (a different cache, an extra renderer,
a new sink), change it here; nothing else needs to know.
"""

from dataclasses import dataclass, field
from types import TracebackType
from typing import Self

import httpx

from vink import __version__
from vink.adapters.cache import CachingTranscriptSource, FileCache
from vink.adapters.render import MarkdownRenderer
from vink.adapters.sinks import LocalDirectorySink
from vink.adapters.youtube import OEmbedMetadataSource, YouTubeTranscriptSource
from vink.config import Settings
from vink.ports.transcript_source import TranscriptSource
from vink.services import ExportService, TranscriptService

USER_AGENT = f"vink/{__version__}"


@dataclass(frozen=True, slots=True)
class Container:
    """Fully wired services plus the resources they hold.

    Use it as a context manager, or call :meth:`close`, to release network
    connections.
    """

    settings: Settings
    transcripts: TranscriptService
    exports: ExportService
    _http_client: httpx.Client = field(repr=False)

    def close(self) -> None:
        """Release network resources held by adapters."""
        self._http_client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def build_container(settings: Settings | None = None) -> Container:
    """Construct every adapter and service from ``settings``.

    Args:
        settings: Configuration to use; loaded from the environment if omitted.

    Returns:
        A ready-to-use :class:`Container`.
    """
    resolved = settings or Settings()
    http_client = httpx.Client(
        timeout=resolved.http_timeout,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    )

    source: TranscriptSource = YouTubeTranscriptSource()
    if resolved.use_cache:
        source = CachingTranscriptSource(source, FileCache(resolved.cache_dir))

    transcripts = TranscriptService(source=source, metadata=OEmbedMetadataSource(http_client))
    exports = ExportService(
        renderers=[MarkdownRenderer()],
        sink=LocalDirectorySink(resolved.output_dir),
    )
    return Container(
        settings=resolved,
        transcripts=transcripts,
        exports=exports,
        _http_client=http_client,
    )
