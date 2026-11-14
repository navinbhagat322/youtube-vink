from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

import pytest
import requests
import youtube_transcript_api as yta
from youtube_transcript_api import YouTubeTranscriptApi

from vink.adapters.youtube import YouTubeTranscriptSource
from vink.domain.errors import (
    LanguageUnavailableError,
    TranscriptFetchError,
    TranscriptsDisabledError,
    VideoUnavailableError,
    VinkError,
)
from vink.domain.models import TrackInfo, TrackKind, TrackSelection
from vink.domain.video_ref import VideoRef

VIDEO = VideoRef("aircAruvnKk")


@dataclass
class _Lang:
    language_code: str


@dataclass
class _Snippet:
    text: str
    start: float
    duration: float


@dataclass
class _Fetched:
    snippets: list[_Snippet]


@dataclass
class _LibTranscript:
    language_code: str
    language: str
    is_generated: bool
    translation_languages: list[_Lang] = field(default_factory=list)
    translated_to: str | None = None

    def translate(self, code: str) -> "_LibTranscript":
        return _LibTranscript(code, f"{code} (translated)", self.is_generated, translated_to=code)

    def fetch(self) -> _Fetched:
        return _Fetched([_Snippet("hello", 1.0, 2.0), _Snippet("world", 3.0, 1.5)])


class _LibTranscriptList(list[_LibTranscript]):
    def find_manually_created_transcript(self, codes: list[str]) -> _LibTranscript:
        return next(t for t in self if not t.is_generated and t.language_code in codes)

    def find_generated_transcript(self, codes: list[str]) -> _LibTranscript:
        return next(t for t in self if t.is_generated and t.language_code in codes)


@dataclass
class _FakeApi:
    transcripts: _LibTranscriptList
    error: Exception | None = None

    def list(self, video_id: str) -> _LibTranscriptList:
        if self.error:
            raise self.error
        return self.transcripts


def _source(api: _FakeApi) -> YouTubeTranscriptSource:
    return YouTubeTranscriptSource(api=cast(YouTubeTranscriptApi, api))


@pytest.fixture
def api() -> _FakeApi:
    return _FakeApi(
        _LibTranscriptList(
            [
                _LibTranscript("en", "English", False, [_Lang("hi"), _Lang("es")]),
                _LibTranscript("en", "English (auto-generated)", True),
            ]
        )
    )


def test_list_tracks_converts_library_objects(api: _FakeApi) -> None:
    tracks = _source(api).list_tracks(VIDEO)

    assert tracks == [
        TrackInfo("en", "English", is_generated=False, translation_codes=frozenset({"hi", "es"})),
        TrackInfo("en", "English (auto-generated)", is_generated=True),
    ]


@pytest.mark.parametrize("is_generated", [False, True])
def test_fetch_picks_track_by_kind(api: _FakeApi, is_generated: bool) -> None:
    track = TrackInfo("en", "English", is_generated=is_generated)

    raw = _source(api).fetch(VIDEO, TrackSelection(track))

    expected_name = "English (auto-generated)" if is_generated else "English"
    assert raw.language_name == expected_name
    assert raw.kind is track.kind
    assert [(s.start, s.duration, s.text) for s in raw.segments] == [
        (1.0, 2.0, "hello"),
        (3.0, 1.5, "world"),
    ]


def test_fetch_translates_when_requested(api: _FakeApi) -> None:
    track = TrackInfo("en", "English", is_generated=False)

    raw = _source(api).fetch(VIDEO, TrackSelection(track, translate_to="hi"))

    assert raw.language_code == "hi"
    assert raw.kind is TrackKind.TRANSLATED
    assert raw.language_name == "hi (translated)"


VID = VIDEO.video_id

ERROR_CASES: list[tuple[Callable[[], Exception], type[VinkError]]] = [
    (lambda: yta.TranscriptsDisabled(VID), TranscriptsDisabledError),
    (lambda: yta.VideoUnavailable(VID), VideoUnavailableError),
    (lambda: yta.InvalidVideoId(VID), VideoUnavailableError),
    (lambda: yta.AgeRestricted(VID), VideoUnavailableError),
    (lambda: yta.VideoUnplayable(VID, "private", []), VideoUnavailableError),
    (lambda: yta.NoTranscriptFound(VID, ["en"], cast(Any, None)), LanguageUnavailableError),
    (lambda: yta.NotTranslatable(VID), LanguageUnavailableError),
    (lambda: yta.TranslationLanguageNotAvailable(VID), LanguageUnavailableError),
    (lambda: yta.RequestBlocked(VID), TranscriptFetchError),
    (lambda: yta.IpBlocked(VID), TranscriptFetchError),
    (lambda: yta.CouldNotRetrieveTranscript(VID), TranscriptFetchError),
    (lambda: requests.ConnectionError("offline"), TranscriptFetchError),
]


@pytest.mark.parametrize(("make_error", "expected"), ERROR_CASES)
def test_library_errors_become_domain_errors(
    api: _FakeApi, make_error: Callable[[], Exception], expected: type[VinkError]
) -> None:
    original = make_error()
    api.error = original

    with pytest.raises(expected) as info:
        _source(api).list_tracks(VIDEO)

    assert info.value.__cause__ is original


def test_blocked_error_explains_cause(api: _FakeApi) -> None:
    api.error = yta.RequestBlocked(VID)

    with pytest.raises(TranscriptFetchError, match="blocking requests"):
        _source(api).list_tracks(VIDEO)
