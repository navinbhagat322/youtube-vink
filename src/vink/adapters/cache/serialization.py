"""Conversion between domain models and JSON-compatible data for caching.

The format is versioned through :data:`SCHEMA_VERSION`, which is part of every
cache key. Bump it whenever a shape below changes; old entries then simply
stop matching and are refetched.

``*_from_data`` functions raise :class:`ValueError` for malformed input so
callers can treat a corrupt entry as a cache miss.
"""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any, Final

from vink.domain.errors import VinkError
from vink.domain.models import RawTranscript, Segment, TrackInfo, TrackKind, VideoMetadata
from vink.domain.video_ref import VideoRef

SCHEMA_VERSION: Final = 2

JsonData = Any
"""Data produced by :func:`json.loads`; validated by the ``*_from_data`` functions."""


def tracks_to_data(tracks: Sequence[TrackInfo]) -> JsonData:
    """Convert tracks to JSON-compatible data."""
    return [
        {
            "language_code": track.language_code,
            "language_name": track.language_name,
            "is_generated": track.is_generated,
            "translation_codes": sorted(track.translation_codes),
        }
        for track in tracks
    ]


def tracks_from_data(data: JsonData) -> list[TrackInfo]:
    """Rebuild tracks from :func:`tracks_to_data` output."""
    with _malformed("tracks"):
        if not isinstance(data, list):
            raise TypeError("expected a list")
        return [
            TrackInfo(
                language_code=str(item["language_code"]),
                language_name=str(item["language_name"]),
                is_generated=bool(item["is_generated"]),
                translation_codes=frozenset(str(c) for c in item["translation_codes"]),
            )
            for item in data
        ]


def transcript_to_data(transcript: RawTranscript) -> JsonData:
    """Convert a raw transcript to JSON-compatible data."""
    return {
        "video_id": transcript.video.video_id,
        "language_code": transcript.language_code,
        "language_name": transcript.language_name,
        "kind": transcript.kind.value,
        "segments": [[s.start, s.duration, s.text] for s in transcript.segments],
    }


def transcript_from_data(data: JsonData) -> RawTranscript:
    """Rebuild a raw transcript from :func:`transcript_to_data` output."""
    with _malformed("transcript"):
        return RawTranscript(
            video=VideoRef(str(data["video_id"])),
            language_code=str(data["language_code"]),
            language_name=str(data["language_name"]),
            kind=TrackKind(data["kind"]),
            segments=tuple(
                Segment(start=float(start), duration=float(duration), text=str(text))
                for start, duration, text in data["segments"]
            ),
        )


def metadata_to_data(metadata: VideoMetadata) -> JsonData:
    """Convert video metadata to JSON-compatible data."""
    return {
        "title": metadata.title,
        "channel": metadata.channel,
        "channel_url": metadata.channel_url,
    }


def metadata_from_data(data: JsonData) -> VideoMetadata:
    """Rebuild video metadata from :func:`metadata_to_data` output."""
    with _malformed("metadata"):
        channel, channel_url = data["channel"], data["channel_url"]
        return VideoMetadata(
            title=str(data["title"]),
            channel=None if channel is None else str(channel),
            channel_url=None if channel_url is None else str(channel_url),
        )


@contextmanager
def _malformed(what: str) -> Iterator[None]:
    """Turn shape errors raised inside the block into a uniform :class:`ValueError`."""
    try:
        yield
    except (KeyError, TypeError, ValueError, VinkError) as exc:
        raise ValueError(f"Malformed cached {what}: {exc!r}") from exc
