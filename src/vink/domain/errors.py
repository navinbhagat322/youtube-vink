"""Error hierarchy for vink.

Every error raised by vink derives from :class:`VinkError`. Adapters translate
third-party exceptions into these types so that services and interfaces never
depend on library-specific errors.

Messages are written for end users: they say what happened and, where
possible, what to try next.
"""

from collections.abc import Sequence


class VinkError(Exception):
    """Base class for all vink errors."""


class InvalidInputError(VinkError):
    """The user supplied an argument vink cannot interpret, such as a malformed URL."""


class VideoUnavailableError(VinkError):
    """The video is private, deleted, age-restricted, or otherwise not playable."""

    def __init__(self, video_id: str, reason: str) -> None:
        super().__init__(f"Video {video_id} is unavailable: {reason}")
        self.video_id = video_id
        self.reason = reason


class TranscriptError(VinkError):
    """Base class for problems obtaining a transcript."""


class TranscriptsDisabledError(TranscriptError):
    """The video has no caption tracks at all."""

    def __init__(self, video_id: str) -> None:
        super().__init__(
            f"Video {video_id} has no transcripts. The creator may have disabled captions."
        )
        self.video_id = video_id


class LanguageUnavailableError(TranscriptError):
    """None of the requested languages is available, directly or by translation."""

    def __init__(
        self,
        video_id: str,
        requested: Sequence[str],
        available: Sequence[str],
    ) -> None:
        requested_text = ", ".join(requested) or "(none)"
        available_text = ", ".join(available) or "(none)"
        hint = f" Try --lang {available[0]}." if available else ""
        super().__init__(
            f"No transcript in [{requested_text}] for video {video_id}. "
            f"Available: {available_text}.{hint}"
        )
        self.video_id = video_id
        self.requested = tuple(requested)
        self.available = tuple(available)


class TranscriptFetchError(TranscriptError):
    """A network or upstream failure prevented fetching the transcript."""


class MetadataFetchError(VinkError):
    """Video metadata (title, channel) could not be retrieved.

    Metadata is non-essential: services may fall back to placeholder values.
    """


class CacheError(VinkError):
    """The local cache could not be read or written."""


class RenderError(VinkError):
    """A transcript could not be rendered into the requested format."""


class SinkError(VinkError):
    """Rendered output could not be delivered to its destination."""
