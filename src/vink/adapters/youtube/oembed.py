"""Video metadata from YouTube's public oEmbed endpoint.

oEmbed returns the title and channel without an API key and is far lighter
than downloading the watch page. It does not provide duration or chapters;
those will come from a richer adapter (e.g. ``yt-dlp``) when needed.
"""

import logging
from typing import Final

import httpx

from vink.domain.errors import MetadataFetchError
from vink.domain.models import VideoMetadata
from vink.domain.video_ref import VideoRef

logger = logging.getLogger(__name__)

OEMBED_URL: Final = "https://www.youtube.com/oembed"


class OEmbedMetadataSource:
    """:class:`~vink.ports.MetadataSource` backed by YouTube oEmbed.

    Args:
        client: HTTP client to use. The caller owns it and must close it.
            It should be configured with timeouts and a ``User-Agent``.
    """

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def get_metadata(self, video: VideoRef) -> VideoMetadata:
        """Return the title and channel of ``video``.

        Raises:
            MetadataFetchError: If the request fails or the response is malformed.
        """
        try:
            response = self._client.get(OEMBED_URL, params={"url": video.url, "format": "json"})
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise MetadataFetchError(
                f"Metadata lookup for {video.video_id} failed with HTTP {exc.response.status_code}."
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise MetadataFetchError(f"Metadata lookup for {video.video_id} failed: {exc}") from exc

        title = payload.get("title") if isinstance(payload, dict) else None
        if not isinstance(title, str) or not title:
            raise MetadataFetchError(f"Metadata for {video.video_id} has no title.")

        return VideoMetadata(
            title=title,
            channel=_optional_str(payload.get("author_name")),
            channel_url=_optional_str(payload.get("author_url")),
        )


def _optional_str(value: object) -> str | None:
    """Return ``value`` if it is a non-empty string, else ``None``."""
    return value if isinstance(value, str) and value else None
