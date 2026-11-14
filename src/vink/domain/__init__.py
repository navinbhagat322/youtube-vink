"""Domain layer: immutable data models and errors.

Everything here is pure Python with no I/O and no third-party imports. Every
other layer depends on this one; this one depends on nothing.
"""

from vink.domain.errors import (
    CacheError,
    InvalidInputError,
    LanguageUnavailableError,
    MetadataFetchError,
    RenderError,
    SinkError,
    TranscriptError,
    TranscriptFetchError,
    TranscriptsDisabledError,
    VideoUnavailableError,
    VinkError,
)
from vink.domain.models import (
    Chunk,
    Paragraph,
    RawTranscript,
    Segment,
    TrackInfo,
    TrackKind,
    TrackSelection,
    Transcript,
    VideoMetadata,
)
from vink.domain.video_ref import VideoRef, parse_video_ref

__all__ = [
    "CacheError",
    "Chunk",
    "InvalidInputError",
    "LanguageUnavailableError",
    "MetadataFetchError",
    "Paragraph",
    "RawTranscript",
    "RenderError",
    "Segment",
    "SinkError",
    "TrackInfo",
    "TrackKind",
    "TrackSelection",
    "Transcript",
    "TranscriptError",
    "TranscriptFetchError",
    "TranscriptsDisabledError",
    "VideoMetadata",
    "VideoRef",
    "VideoUnavailableError",
    "VinkError",
    "parse_video_ref",
]
