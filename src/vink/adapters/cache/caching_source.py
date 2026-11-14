"""A transcript source decorator that caches results in any :class:`~vink.ports.Cache`."""

import logging

from vink.adapters.cache import serialization
from vink.domain.errors import VinkError
from vink.domain.models import RawTranscript, TrackInfo, TrackSelection
from vink.domain.video_ref import VideoRef
from vink.ports.cache import Cache
from vink.ports.transcript_source import TranscriptSource

logger = logging.getLogger(__name__)


class CachingTranscriptSource:
    """Wraps a :class:`~vink.ports.TranscriptSource` and caches its results.

    Services stay unaware of caching: they receive this object as their
    transcript source. Corrupt entries are treated as misses and overwritten.

    Args:
        inner: The source to delegate to on a cache miss.
        cache: Where to store serialized results.
    """

    def __init__(self, inner: TranscriptSource, cache: Cache) -> None:
        self._inner = inner
        self._cache = cache

    def list_tracks(self, video: VideoRef) -> list[TrackInfo]:
        """Return tracks from the cache, or fetch and cache them."""
        key = f"v{serialization.SCHEMA_VERSION}:tracks:{video.video_id}"
        cached = self._cache.get(key)
        if cached is not None:
            try:
                return serialization.load_tracks(cached)
            except ValueError as exc:
                logger.warning("Discarding corrupt cache entry %s: %s", key, exc)

        tracks = self._inner.list_tracks(video)
        self._cache.set(key, serialization.dump_tracks(tracks))
        return tracks

    def fetch(self, video: VideoRef, selection: TrackSelection) -> RawTranscript:
        """Return the transcript from the cache, or fetch and cache it."""
        key = _transcript_key(video, selection)
        cached = self._cache.get(key)
        if cached is not None:
            try:
                transcript = serialization.load_transcript(cached)
            except (ValueError, VinkError) as exc:
                logger.warning("Discarding corrupt cache entry %s: %s", key, exc)
            else:
                logger.debug("Cache hit for %s", key)
                return transcript

        transcript = self._inner.fetch(video, selection)
        self._cache.set(key, serialization.dump_transcript(transcript))
        return transcript


def _transcript_key(video: VideoRef, selection: TrackSelection) -> str:
    """Build a cache key that uniquely identifies one fetched transcript."""
    track = selection.track
    return ":".join(
        [
            f"v{serialization.SCHEMA_VERSION}",
            "transcript",
            video.video_id,
            track.language_code,
            track.kind.value,
            selection.translate_to or "-",
        ]
    )
