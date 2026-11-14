from pathlib import Path

import pytest

from vink.adapters.render import MarkdownRenderer
from vink.domain.models import Chunk, Paragraph, TrackKind, Transcript, VideoMetadata
from vink.domain.video_ref import VideoRef

EXPECTED = Path(__file__).parents[2] / "fixtures" / "expected"


@pytest.fixture
def transcript() -> Transcript:
    return Transcript(
        video=VideoRef("aircAruvnKk"),
        metadata=VideoMetadata(
            title='Neural Networks: "Part 1" [intro]',
            channel="Example_Channel",
            channel_url="https://www.youtube.com/@example",
        ),
        language_code="en",
        language_name="English",
        kind=TrackKind.MANUAL,
        paragraphs=(
            Paragraph(4.2, 48.0, "A network has *layers* of neurons."),
            Paragraph(49.0, 125.5, "Each weight w_ij connects two neurons <in> adjacent layers."),
        ),
    )


def _assert_matches_golden(actual: str, name: str) -> None:
    path: Path = EXPECTED / name
    assert actual == path.read_text(encoding="utf-8")


def test_render_transcript_matches_golden_file(transcript: Transcript) -> None:
    _assert_matches_golden(MarkdownRenderer().render_transcript(transcript), "transcript.md")


def test_render_chunk_matches_golden_file(transcript: Transcript) -> None:
    chunk = Chunk(index=2, total=3, paragraphs=transcript.paragraphs[1:])

    _assert_matches_golden(MarkdownRenderer().render_chunk(transcript, chunk), "chunk.md")


def test_header_without_channel_or_url() -> None:
    transcript = Transcript(
        video=VideoRef("aircAruvnKk"),
        metadata=VideoMetadata(title="T", channel="Only Name"),
        language_code="hi",
        language_name="Hindi",
        kind=TrackKind.TRANSLATED,
        paragraphs=(),
    )

    output = MarkdownRenderer().render_transcript(transcript)

    assert "**Channel:** Only Name ·" in output
    assert "machine-translated captions" in output
    assert "channel_url" not in output


def test_renderer_identity() -> None:
    renderer = MarkdownRenderer()

    assert (renderer.format_name, renderer.file_extension) == ("markdown", "md")
