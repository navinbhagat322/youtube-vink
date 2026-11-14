"""Port for obtaining caption tracks."""

from typing import Protocol

from vink.domain.models import RawTranscript, TrackInfo, TrackSelection
from vink.domain.video_ref import VideoRef


class TranscriptSource(Protocol):
    """Lists and fetches caption tracks for a video.

    Implementations raise :class:`~vink.domain.errors.TranscriptError` subclasses
    or :class:`~vink.domain.errors.VideoUnavailableError` on failure.
    """

    def list_tracks(self, video: VideoRef) -> list[TrackInfo]:
        """Return every caption track available for ``video``."""
        ...

    def fetch(self, video: VideoRef, selection: TrackSelection) -> RawTranscript:
        """Fetch the transcript described by ``selection``."""
        ...
