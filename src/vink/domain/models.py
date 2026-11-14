"""Core data models.

All models are immutable. Times are stored as seconds (``float``) and only
formatted for display at render time.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from vink.domain.video_ref import VideoRef


class TrackKind(StrEnum):
    """How a caption track was produced."""

    MANUAL = "manual"
    """Uploaded or written by the creator."""

    GENERATED = "generated"
    """Created by YouTube's automatic speech recognition."""

    TRANSLATED = "translated"
    """Machine-translated by YouTube from another track."""


@dataclass(frozen=True, slots=True)
class TrackInfo:
    """A caption track that is available for a video.

    Attributes:
        language_code: BCP-47-style code, e.g. ``"en"``, ``"hi"``, ``"pt-BR"``.
        language_name: Human-readable name as reported by YouTube.
        is_generated: ``True`` for auto-generated (ASR) tracks.
        translation_codes: Languages YouTube can machine-translate this track into.
    """

    language_code: str
    language_name: str
    is_generated: bool
    translation_codes: frozenset[str] = field(default_factory=frozenset)

    @property
    def kind(self) -> TrackKind:
        """Whether the track is manual or auto-generated."""
        return TrackKind.GENERATED if self.is_generated else TrackKind.MANUAL


@dataclass(frozen=True, slots=True)
class TrackSelection:
    """Which track to fetch, and optionally which language to translate it into.

    Attributes:
        track: The source track to fetch.
        translate_to: Target language code, or ``None`` to use the track as-is.
    """

    track: TrackInfo
    translate_to: str | None = None

    @property
    def language_code(self) -> str:
        """Language code of the text that will be produced."""
        return self.translate_to or self.track.language_code

    @property
    def kind(self) -> TrackKind:
        """Kind of the resulting transcript."""
        return TrackKind.TRANSLATED if self.translate_to else self.track.kind


@dataclass(frozen=True, slots=True)
class Segment:
    """One caption cue as delivered by the source.

    Attributes:
        start: Start time in seconds.
        duration: Display duration in seconds.
        text: Caption text, possibly a sentence fragment.
    """

    start: float
    duration: float
    text: str

    @property
    def end(self) -> float:
        """End time in seconds."""
        return self.start + self.duration


@dataclass(frozen=True, slots=True)
class VideoMetadata:
    """Descriptive information about a video.

    Attributes:
        title: Video title.
        channel: Channel display name, if known.
        channel_url: Link to the channel, if known.
    """

    title: str
    channel: str | None = None
    channel_url: str | None = None


@dataclass(frozen=True, slots=True)
class RawTranscript:
    """Caption segments exactly as fetched, before any cleaning.

    Attributes:
        video: The video the transcript belongs to.
        language_code: Language of the text.
        language_name: Human-readable language name.
        kind: How the track was produced.
        segments: Caption cues in playback order.
    """

    video: VideoRef
    language_code: str
    language_name: str
    kind: TrackKind
    segments: tuple[Segment, ...]


@dataclass(frozen=True, slots=True)
class Paragraph:
    """A readable block of transcript text with its time range.

    Attributes:
        start: Start time in seconds.
        end: End time in seconds.
        text: Cleaned paragraph text.
    """

    start: float
    end: float
    text: str


@dataclass(frozen=True, slots=True)
class Transcript:
    """A cleaned, paragraphed transcript ready for rendering.

    Attributes:
        video: The video the transcript belongs to.
        metadata: Title and channel information.
        language_code: Language of the text.
        language_name: Human-readable language name.
        kind: How the underlying track was produced.
        paragraphs: Paragraphs in playback order.
    """

    video: VideoRef
    metadata: VideoMetadata
    language_code: str
    language_name: str
    kind: TrackKind
    paragraphs: tuple[Paragraph, ...]

    @property
    def duration(self) -> float:
        """Time of the last spoken word, in seconds."""
        return self.paragraphs[-1].end if self.paragraphs else 0.0


@dataclass(frozen=True, slots=True)
class Chunk:
    """A contiguous slice of a transcript, sized for one pass of note generation.

    Attributes:
        index: 1-based position of this chunk.
        total: Total number of chunks in the transcript.
        paragraphs: Paragraphs contained in this chunk.
    """

    index: int
    total: int
    paragraphs: tuple[Paragraph, ...]

    @property
    def start(self) -> float:
        """Start time of the first paragraph, in seconds."""
        return self.paragraphs[0].start if self.paragraphs else 0.0

    @property
    def end(self) -> float:
        """End time of the last paragraph, in seconds."""
        return self.paragraphs[-1].end if self.paragraphs else 0.0
