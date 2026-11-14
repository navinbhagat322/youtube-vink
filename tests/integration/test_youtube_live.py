"""Tests against real YouTube. Run with: uv run pytest -m integration"""

from pathlib import Path

import pytest

from vink.bootstrap import build_container
from vink.config import Settings
from vink.domain.models import TrackKind
from vink.domain.video_ref import parse_video_ref

pytestmark = pytest.mark.integration

# "But what is a neural network?" by 3Blue1Brown: long-lived, many caption tracks.
VIDEO_URL = "https://www.youtube.com/watch?v=aircAruvnKk"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(cache_dir=tmp_path / "cache", output_dir=tmp_path / "out")


def test_fetches_and_saves_english_transcript(settings: Settings) -> None:
    with build_container(settings) as container:
        transcript = container.transcripts.get_transcript(parse_video_ref(VIDEO_URL), ["en"])
        location = container.exports.save_transcript(transcript, "markdown")

    assert transcript.metadata.channel == "3Blue1Brown"
    assert transcript.kind is TrackKind.MANUAL
    assert transcript.duration > 15 * 60
    assert Path(location).read_text(encoding="utf-8").startswith("---\ntitle:")


def test_original_language_uses_generated_track(settings: Settings) -> None:
    with build_container(settings) as container:
        transcript = container.transcripts.get_transcript(parse_video_ref(VIDEO_URL), ["original"])

    assert transcript.language_code == "en"
