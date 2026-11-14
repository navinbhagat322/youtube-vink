import pytest

from tests.fakes import InMemorySink
from vink.domain.errors import InvalidInputError
from vink.domain.models import Chunk, Paragraph, TrackKind, Transcript, VideoMetadata
from vink.domain.video_ref import VideoRef
from vink.services import ExportService


@pytest.fixture
def transcript(video: VideoRef) -> Transcript:
    return Transcript(
        video=video,
        metadata=VideoMetadata(title="What is AI? Part 1/2"),
        language_code="en",
        language_name="English",
        kind=TrackKind.MANUAL,
        paragraphs=(Paragraph(0, 10, "Hello."),),
    )


def test_save_transcript_names_file_after_title(
    export_service: ExportService, sink: InMemorySink, transcript: Transcript
) -> None:
    location = export_service.save_transcript(transcript, "markdown")

    assert location == "memory://What is AI Part 1 2.md"
    assert "Hello." in sink.files["What is AI Part 1 2.md"]


def test_save_text_adds_suffix_and_sanitizes(
    export_service: ExportService, sink: InMemorySink
) -> None:
    export_service.save_text("A/B", "# notes", suffix="notes", extension="md")
    export_service.save_text("Plain", "x", suffix="", extension="txt")

    assert sink.files == {"A B - notes.md": "# notes", "Plain.txt": "x"}


def test_render_and_render_chunk(export_service: ExportService, transcript: Transcript) -> None:
    chunk = Chunk(1, 1, transcript.paragraphs)

    assert "## Transcript" in export_service.render(transcript, "markdown")
    assert "## Part 1 of 1" in export_service.render_chunk(transcript, chunk, "markdown")


def test_unknown_format_lists_available(
    export_service: ExportService, transcript: Transcript
) -> None:
    with pytest.raises(InvalidInputError, match="Available: markdown"):
        export_service.render(transcript, "pdf")


def test_formats(export_service: ExportService) -> None:
    assert export_service.formats == ["markdown"]
