from vink.domain.errors import LanguageUnavailableError
from vink.domain.models import (
    Chunk,
    Paragraph,
    Segment,
    TrackInfo,
    TrackKind,
    TrackSelection,
    Transcript,
    VideoMetadata,
)
from vink.domain.video_ref import VideoRef


def test_track_selection_reports_translation() -> None:
    track = TrackInfo("en", "English", is_generated=False)

    plain = TrackSelection(track)
    translated = TrackSelection(track, translate_to="hi")

    assert (plain.language_code, plain.kind) == ("en", TrackKind.MANUAL)
    assert (translated.language_code, translated.kind) == ("hi", TrackKind.TRANSLATED)


def test_generated_track_kind() -> None:
    assert TrackInfo("hi", "Hindi", is_generated=True).kind is TrackKind.GENERATED


def test_segment_end() -> None:
    assert Segment(start=1.5, duration=2.0, text="x").end == 3.5


def test_empty_transcript_and_chunk_have_zero_times() -> None:
    transcript = Transcript(
        video=VideoRef("aircAruvnKk"),
        metadata=VideoMetadata(title="t"),
        language_code="en",
        language_name="English",
        kind=TrackKind.MANUAL,
        paragraphs=(),
    )
    chunk = Chunk(index=1, total=1, paragraphs=())

    assert transcript.duration == 0.0
    assert (chunk.start, chunk.end) == (0.0, 0.0)


def test_chunk_times_span_paragraphs() -> None:
    chunk = Chunk(1, 1, (Paragraph(10, 20, "a"), Paragraph(20, 35, "b")))

    assert (chunk.start, chunk.end) == (10, 35)


def test_language_unavailable_message_suggests_alternative() -> None:
    error = LanguageUnavailableError("vid", requested=["fr"], available=["en", "hi"])

    assert "Available: en, hi" in str(error)
    assert "Try --lang en" in str(error)
    assert error.available == ("en", "hi")
