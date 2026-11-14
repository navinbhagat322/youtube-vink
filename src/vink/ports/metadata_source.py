"""Port for obtaining video metadata."""

from typing import Protocol

from vink.domain.models import VideoMetadata
from vink.domain.video_ref import VideoRef


class MetadataSource(Protocol):
    """Looks up descriptive information such as title and channel."""

    def get_metadata(self, video: VideoRef) -> VideoMetadata:
        """Return metadata for ``video``.

        Raises:
            VideoUnavailableError: If the video cannot be found.
            TranscriptFetchError: On network or upstream failure.
        """
        ...
