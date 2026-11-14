import logging

import pytest

from tests.fakes import FakeMetadataSource, FakeTranscriptSource
from vink.domain.errors import LanguageUnavailableError, TranscriptsDisabledError
from vink.domain.models import TrackKind, VideoMetadata
from vink.domain.video_ref import VideoRef
from vink.services import TranscriptService


def test_get_transcript_cleans_and_paragraphs(
    transcript_service: TranscriptService, video: VideoRef
) -> None:
    transcript = transcript_service.get_transcript(video, ["en"])

    assert transcript.language_code == "en"
    assert transcript.kind is TrackKind.MANUAL
    assert transcript.metadata.title == "Sample Lecture"
    assert [p.text for p in transcript.paragraphs] == [
        "Welcome to the lecture. Today we cover gradient descent.",
        "Any questions so far? Let's continue & finish.",
    ]
    assert transcript.paragraphs[0].start == 2.0


def test_get_transcript_uses_translation_and_warns(
    transcript_service: TranscriptService,
    source: FakeTranscriptSource,
    video: VideoRef,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        transcript = transcript_service.get_transcript(video, ["es"])

    assert transcript.kind is TrackKind.TRANSLATED
    assert source.fetch_calls[0].translate_to == "es"
    assert "YouTube translation" in caplog.text


def test_get_transcript_without_translation_raises(
    transcript_service: TranscriptService, video: VideoRef
) -> None:
    with pytest.raises(LanguageUnavailableError):
        transcript_service.get_transcript(video, ["es"], allow_translation=False)


def test_source_errors_propagate(source: FakeTranscriptSource, video: VideoRef) -> None:
    source.error = TranscriptsDisabledError(video.video_id)
    service = TranscriptService(source=source, metadata=FakeMetadataSource())

    with pytest.raises(TranscriptsDisabledError):
        service.get_transcript(video, ["en"])


def test_metadata_failure_falls_back_to_video_id(
    source: FakeTranscriptSource, video: VideoRef
) -> None:
    service = TranscriptService(source=source, metadata=FakeMetadataSource(fail=True))

    transcript = service.get_transcript(video, ["en"])

    assert transcript.metadata == VideoMetadata(title=video.video_id)


def test_list_tracks_delegates(transcript_service: TranscriptService, video: VideoRef) -> None:
    assert [t.language_code for t in transcript_service.list_tracks(video)] == ["en", "hi"]


def test_chunk_splits_transcript(transcript_service: TranscriptService, video: VideoRef) -> None:
    transcript = transcript_service.get_transcript(video, ["en"])

    chunks = transcript_service.chunk(transcript, target_seconds=30)

    assert [c.paragraphs for c in chunks] == [
        (transcript.paragraphs[0],),
        (transcript.paragraphs[1],),
    ]
