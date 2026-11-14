"""Shared fixtures."""

from pathlib import Path

import pytest

from tests.fakes import FakeMetadataSource, FakeTranscriptSource, InMemorySink
from vink.adapters.render import MarkdownRenderer
from vink.domain.models import Segment, TrackInfo
from vink.domain.video_ref import VideoRef
from vink.services import ExportService, TranscriptService

FIXTURES = Path(__file__).parent / "fixtures"

VIDEO_ID = "dQw4w9WgXcQ"


@pytest.fixture
def video() -> VideoRef:
    return VideoRef(VIDEO_ID)


@pytest.fixture
def tracks() -> list[TrackInfo]:
    """A typical video: creator English captions, auto Hindi, translatable to Spanish."""
    return [
        TrackInfo("en", "English", is_generated=False, translation_codes=frozenset({"es", "fr"})),
        TrackInfo("hi", "Hindi (auto-generated)", is_generated=True),
    ]


@pytest.fixture
def segments() -> tuple[Segment, ...]:
    return (
        Segment(0.0, 2.0, "[Music]"),
        Segment(2.0, 3.0, "Welcome to the lecture."),
        Segment(5.0, 4.0, "Today we cover"),
        Segment(9.0, 3.0, "gradient descent."),
        Segment(60.0, 5.0, ">> Any questions so far?"),
        Segment(65.0, 4.0, "Let's continue &amp; finish."),
    )


@pytest.fixture
def source(tracks: list[TrackInfo], segments: tuple[Segment, ...]) -> FakeTranscriptSource:
    return FakeTranscriptSource(tracks=tracks, segments=segments)


@pytest.fixture
def metadata() -> FakeMetadataSource:
    return FakeMetadataSource()


@pytest.fixture
def transcript_service(
    source: FakeTranscriptSource, metadata: FakeMetadataSource
) -> TranscriptService:
    return TranscriptService(source=source, metadata=metadata)


@pytest.fixture
def sink() -> InMemorySink:
    return InMemorySink()


@pytest.fixture
def export_service(sink: InMemorySink) -> ExportService:
    return ExportService(renderers=[MarkdownRenderer()], sink=sink)
