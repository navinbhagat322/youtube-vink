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
from vink.adapters.cache import (
    CachingMetadataSource,
    CachingTranscriptSource,
    FileCache,
    TimedEntries,
)
from vink.adapters.render import MarkdownRenderer
from vink.adapters.sinks import LocalDirectorySink
from vink.adapters.youtube import OEmbedMetadataSource, ProxyOptions, YouTubeTranscriptSource
from vink.config import Settings
from vink.domain.errors import InvalidInputError
from vink.ports.metadata_source import MetadataSource
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

    Raises:
        InvalidInputError: If the proxy configuration (``VINK_PROXY_URL`` or the
            standard ``HTTPS_PROXY`` / ``HTTP_PROXY`` variables) is malformed.
    """
    resolved = settings or Settings()
    proxy = proxy_options(resolved)
    http_client = _http_client(resolved, proxy)

    source: TranscriptSource = YouTubeTranscriptSource(proxy=proxy)
    metadata: MetadataSource = OEmbedMetadataSource(http_client)
    if resolved.use_cache:
        entries = TimedEntries(FileCache(resolved.cache_dir))
        source = CachingTranscriptSource(source, entries)
        metadata = CachingMetadataSource(metadata, entries)

    transcripts = TranscriptService(source=source, metadata=metadata)
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


def proxy_options(settings: Settings) -> ProxyOptions:
    """Translate proxy settings into adapter options."""
    return ProxyOptions(
        url=settings.proxy_url.get_secret_value() if settings.proxy_url else None,
        webshare_username=settings.webshare_username,
        webshare_password=(
            settings.webshare_password.get_secret_value() if settings.webshare_password else None
        ),
    )


def _http_client(settings: Settings, proxy: ProxyOptions) -> httpx.Client:
    """Create the shared HTTP client for metadata lookups.

    An explicitly configured proxy wins over the standard proxy environment
    variables, which are then ignored. Without one, those variables are honoured,
    and a malformed value is reported clearly instead of crashing on startup.
    """
    explicit_proxy = proxy.http_url()
    try:
        return httpx.Client(
            timeout=settings.http_timeout,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            proxy=explicit_proxy,
            trust_env=explicit_proxy is None,
        )
    except (httpx.InvalidURL, ValueError) as exc:
        raise InvalidInputError(
            "Invalid proxy in the HTTPS_PROXY / HTTP_PROXY environment variables "
            f"({_without_secrets(exc)}). Fix or remove them, or set VINK_PROXY_URL instead."
        ) from exc


def _without_secrets(exc: Exception) -> str:
    """Describe a URL error without echoing the URL, which may contain a password."""
    return str(exc).split(":", 1)[0] if "@" in str(exc) else str(exc)
