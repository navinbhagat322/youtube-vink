"""Caching decorators for the transcript and metadata ports."""

import logging
from datetime import timedelta
from typing import Final

from vink.adapters.cache import serialization
from vink.adapters.cache.entries import TimedEntries
from vink.domain.models import RawTranscript, TrackInfo, TrackSelection, VideoMetadata
from vink.domain.video_ref import VideoRef
from vink.ports.metadata_source import MetadataSource
from vink.ports.transcript_source import TranscriptSource

logger = logging.getLogger(__name__)

DEFAULT_TRACKS_TTL: Final = timedelta(days=1)
"""Creators can add captions after upload, so the list of tracks is refreshed daily."""

DEFAULT_METADATA_TTL: Final = timedelta(days=7)
"""Titles change rarely; refresh them weekly."""

_PREFIX: Final = f"v{serialization.SCHEMA_VERSION}"


class CachingTranscriptSource:
    """Wraps a :class:`~vink.ports.TranscriptSource` and caches its results.

    Services stay unaware of caching: they receive this object as their
    transcript source. Fetched transcripts never expire, because a caption
    track's text does not change once published; the list of available tracks
    expires after ``tracks_ttl``.

    Args:
        inner: The source to delegate to on a cache miss.
        entries: Where to store results.
        tracks_ttl: How long a cached list of tracks stays valid.
    """

    def __init__(
        self,
        inner: TranscriptSource,
        entries: TimedEntries,
        *,
        tracks_ttl: timedelta = DEFAULT_TRACKS_TTL,
    ) -> None:
        self._inner = inner
        self._entries = entries
        self._tracks_ttl = tracks_ttl.total_seconds()

    def list_tracks(self, video: VideoRef) -> list[TrackInfo]:
        """Return tracks from the cache, or fetch and cache them."""
        key = f"{_PREFIX}:tracks:{video.video_id}"
        cached = self._entries.get(key, max_age=self._tracks_ttl)
        if cached is not None:
            try:
                return serialization.tracks_from_data(cached)
            except ValueError as exc:
                logger.warning("Discarding corrupt cache entry %s: %s", key, exc)

        tracks = self._inner.list_tracks(video)
        self._entries.set(key, serialization.tracks_to_data(tracks))
        return tracks

    def fetch(self, video: VideoRef, selection: TrackSelection) -> RawTranscript:
        """Return the transcript from the cache, or fetch and cache it."""
        key = _transcript_key(video, selection)
        cached = self._entries.get(key)
        if cached is not None:
            try:
                transcript = serialization.transcript_from_data(cached)
            except ValueError as exc:
                logger.warning("Discarding corrupt cache entry %s: %s", key, exc)
            else:
                logger.debug("Cache hit for %s", key)
                return transcript

        transcript = self._inner.fetch(video, selection)
        self._entries.set(key, serialization.transcript_to_data(transcript))
        return transcript


class CachingMetadataSource:
    """Wraps a :class:`~vink.ports.MetadataSource` and caches successful lookups.

    Failures are not cached, so a temporary network problem is retried on the
    next call.

    Args:
        inner: The source to delegate to on a cache miss.
        entries: Where to store results.
        ttl: How long cached metadata stays valid.
    """

    def __init__(
        self,
        inner: MetadataSource,
        entries: TimedEntries,
        *,
        ttl: timedelta = DEFAULT_METADATA_TTL,
    ) -> None:
        self._inner = inner
        self._entries = entries
        self._ttl = ttl.total_seconds()

    def get_metadata(self, video: VideoRef) -> VideoMetadata:
        """Return metadata from the cache, or fetch and cache it."""
        key = f"{_PREFIX}:metadata:{video.video_id}"
        cached = self._entries.get(key, max_age=self._ttl)
        if cached is not None:
            try:
                return serialization.metadata_from_data(cached)
            except ValueError as exc:
                logger.warning("Discarding corrupt cache entry %s: %s", key, exc)

        metadata = self._inner.get_metadata(video)
        self._entries.set(key, serialization.metadata_to_data(metadata))
        return metadata


def _transcript_key(video: VideoRef, selection: TrackSelection) -> str:
    """Build a cache key that uniquely identifies one fetched transcript."""
    track = selection.track
    return ":".join(
        [
            _PREFIX,
            "transcript",
            video.video_id,
            track.language_code,
            track.kind.value,
            selection.translate_to or "-",
        ]
    )
