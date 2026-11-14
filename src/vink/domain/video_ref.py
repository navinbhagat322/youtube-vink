"""Parsing user input into a validated YouTube video reference."""

import re
from dataclasses import dataclass
from typing import Final
from urllib.parse import parse_qs, urlparse

from vink.domain.errors import InvalidInputError

_VIDEO_ID_PATTERN: Final = re.compile(r"^[A-Za-z0-9_-]{11}$")
_YOUTUBE_HOSTS: Final = frozenset(
    {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}
)
_SHORT_HOSTS: Final = frozenset({"youtu.be", "www.youtu.be"})
_PATH_PREFIXES: Final = ("shorts", "live", "embed", "v")


@dataclass(frozen=True, slots=True)
class VideoRef:
    """A validated reference to a single YouTube video.

    Attributes:
        video_id: The 11-character YouTube video ID.
    """

    video_id: str

    def __post_init__(self) -> None:
        if not _VIDEO_ID_PATTERN.fullmatch(self.video_id):
            raise InvalidInputError(f"Not a valid YouTube video ID: {self.video_id!r}")

    @property
    def url(self) -> str:
        """Canonical watch URL for the video."""
        return f"https://www.youtube.com/watch?v={self.video_id}"

    def url_at(self, seconds: float) -> str:
        """Return a short link that starts playback at ``seconds``."""
        return f"https://youtu.be/{self.video_id}?t={int(seconds)}"


def parse_video_ref(value: str) -> VideoRef:
    """Parse a YouTube URL or bare video ID into a :class:`VideoRef`.

    Accepts ``watch?v=`` URLs, ``youtu.be`` short links, ``/shorts/``,
    ``/live/``, ``/embed/`` and ``/v/`` paths, and bare 11-character IDs.
    Extra query parameters such as ``t=`` or ``si=`` are ignored.

    Args:
        value: The user-supplied URL or ID.

    Returns:
        The parsed video reference.

    Raises:
        InvalidInputError: If no video ID can be found in ``value``.
    """
    text = value.strip()
    if _VIDEO_ID_PATTERN.fullmatch(text):
        return VideoRef(text)

    candidate = text if "://" in text else f"https://{text}"
    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    video_id: str | None = None
    if host in _SHORT_HOSTS and path_parts:
        video_id = path_parts[0]
    elif host in _YOUTUBE_HOSTS:
        if path_parts[:1] == ["watch"]:
            video_id = next(iter(parse_qs(parsed.query).get("v", [])), None)
        elif len(path_parts) >= 2 and path_parts[0] in _PATH_PREFIXES:
            video_id = path_parts[1]

    if video_id is None or not _VIDEO_ID_PATTERN.fullmatch(video_id):
        raise InvalidInputError(
            f"Could not find a YouTube video ID in {value!r}. "
            "Pass a video URL (e.g. https://youtu.be/VIDEO_ID) or an 11-character ID."
        )
    return VideoRef(video_id)
