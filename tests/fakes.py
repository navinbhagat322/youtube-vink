"""In-memory fakes implementing vink's ports, for fast tests without I/O."""

from dataclasses import dataclass, field

from vink.domain.errors import MetadataFetchError
from vink.domain.models import RawTranscript, Segment, TrackInfo, TrackSelection, VideoMetadata
from vink.domain.video_ref import VideoRef


@dataclass
class FakeTranscriptSource:
    """Serves fixed tracks and segments, and records every call."""

    tracks: list[TrackInfo]
    segments: tuple[Segment, ...]
    error: Exception | None = None
    list_calls: int = 0
    fetch_calls: list[TrackSelection] = field(default_factory=list)

    def list_tracks(self, video: VideoRef) -> list[TrackInfo]:
        self.list_calls += 1
        if self.error:
            raise self.error
        return list(self.tracks)

    def fetch(self, video: VideoRef, selection: TrackSelection) -> RawTranscript:
        self.fetch_calls.append(selection)
        if self.error:
            raise self.error
        return RawTranscript(
            video=video,
            language_code=selection.language_code,
            language_name=f"Language {selection.language_code}",
            kind=selection.kind,
            segments=self.segments,
        )


@dataclass
class FakeMetadataSource:
    """Returns fixed metadata, or fails if ``fail`` is set."""

    metadata: VideoMetadata = field(
        default_factory=lambda: VideoMetadata(
            title="Sample Lecture", channel="Sample Channel", channel_url="https://example.com/c"
        )
    )
    fail: bool = False

    def get_metadata(self, video: VideoRef) -> VideoMetadata:
        if self.fail:
            raise MetadataFetchError("metadata unavailable")
        return self.metadata


@dataclass
class InMemoryCache:
    """A dictionary-backed cache."""

    entries: dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> str | None:
        return self.entries.get(key)

    def set(self, key: str, value: str) -> None:
        self.entries[key] = value


@dataclass
class InMemorySink:
    """Collects written content by name."""

    files: dict[str, str] = field(default_factory=dict)

    def write(self, name: str, content: str) -> str:
        self.files[name] = content
        return f"memory://{name}"
