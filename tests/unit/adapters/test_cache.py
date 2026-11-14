from pathlib import Path

import pytest

from tests.fakes import FakeMetadataSource, FakeTranscriptSource, InMemoryCache
from vink.adapters.cache import (
    CachingMetadataSource,
    CachingTranscriptSource,
    FileCache,
    TimedEntries,
    serialization,
)
from vink.domain.errors import MetadataFetchError
from vink.domain.models import (
    RawTranscript,
    Segment,
    TrackInfo,
    TrackKind,
    TrackSelection,
    VideoMetadata,
)
from vink.domain.video_ref import VideoRef

DAY = 24 * 3600.0


class FakeClock:
    def __init__(self) -> None:
        self.now = 1_000_000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def entries(clock: FakeClock) -> TimedEntries:
    return TimedEntries(InMemoryCache(), clock=clock)


class TestFileCache:
    def test_round_trip(self, tmp_path: Path) -> None:
        cache = FileCache(tmp_path / "cache")

        cache.set("key", "värde ✓")

        assert cache.get("key") == "värde ✓"

    def test_miss_returns_none(self, tmp_path: Path) -> None:
        assert FileCache(tmp_path).get("absent") is None

    def test_overwrites_existing_value(self, tmp_path: Path) -> None:
        cache = FileCache(tmp_path)

        cache.set("key", "old")
        cache.set("key", "new")

        assert cache.get("key") == "new"
        assert len(list(tmp_path.iterdir())) == 1

    def test_write_failure_is_not_raised(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        blocker = tmp_path / "file"
        blocker.write_text("x")
        cache = FileCache(blocker / "sub")  # parent is a file, so mkdir fails

        cache.set("key", "value")

        assert cache.get("key") is None
        assert "Could not write cache entry" in caplog.text

    def test_unreadable_entry_is_a_miss(self, tmp_path: Path) -> None:
        cache = FileCache(tmp_path)
        cache.set("key", "value")
        entry = next(tmp_path.iterdir())
        entry.unlink()
        entry.mkdir()  # reading a directory raises IsADirectoryError

        assert cache.get("key") is None


class TestSerialization:
    def test_tracks_round_trip(self, tracks: list[TrackInfo]) -> None:
        data = serialization.tracks_to_data(tracks)

        assert serialization.tracks_from_data(data) == tracks

    def test_transcript_round_trip(self, video: VideoRef) -> None:
        raw = RawTranscript(video, "hi", "Hindi", TrackKind.GENERATED, (Segment(1, 2, "नमस्ते"),))

        assert serialization.transcript_from_data(serialization.transcript_to_data(raw)) == raw

    @pytest.mark.parametrize(
        "metadata", [VideoMetadata("T", "C", "https://c"), VideoMetadata("Only title")]
    )
    def test_metadata_round_trip(self, metadata: VideoMetadata) -> None:
        data = serialization.metadata_to_data(metadata)

        assert serialization.metadata_from_data(data) == metadata

    @pytest.mark.parametrize("data", [{}, "x", [{}], [{"language_code": "en"}], None])
    def test_malformed_tracks_raise_value_error(self, data: object) -> None:
        with pytest.raises(ValueError, match="Malformed cached tracks"):
            serialization.tracks_from_data(data)

    @pytest.mark.parametrize(
        "data", [[], {}, {"video_id": "aircAruvnKk"}, {"video_id": "bad id"}, None]
    )
    def test_malformed_transcript_raises_value_error(self, data: object) -> None:
        with pytest.raises(ValueError, match="Malformed cached transcript"):
            serialization.transcript_from_data(data)

    @pytest.mark.parametrize("data", [{}, [], None, {"title": "t"}])
    def test_malformed_metadata_raises_value_error(self, data: object) -> None:
        with pytest.raises(ValueError, match="Malformed cached metadata"):
            serialization.metadata_from_data(data)


class TestTimedEntries:
    def test_round_trip(self, entries: TimedEntries) -> None:
        entries.set("k", {"a": [1, "ü"]})

        assert entries.get("k") == {"a": [1, "ü"]}

    def test_miss(self, entries: TimedEntries) -> None:
        assert entries.get("absent") is None

    def test_expires_after_max_age(self, entries: TimedEntries, clock: FakeClock) -> None:
        entries.set("k", 1)

        clock.now += 60
        fresh = entries.get("k", max_age=120)
        clock.now += 61
        stale = entries.get("k", max_age=120)

        assert (fresh, stale) == (1, None)
        assert entries.get("k") == 1  # no max_age: never expires

    @pytest.mark.parametrize("raw", ["not json", "[]", '{"data": 1}', '{"saved_at": "x"}'])
    def test_corrupt_entries_are_misses(self, raw: str) -> None:
        cache = InMemoryCache({"k": raw})

        assert TimedEntries(cache).get("k") is None


class TestCachingTranscriptSource:
    def test_second_call_is_served_from_cache(
        self, source: FakeTranscriptSource, video: VideoRef, entries: TimedEntries
    ) -> None:
        caching = CachingTranscriptSource(source, entries)
        selection = TrackSelection(source.tracks[0])

        first_tracks = caching.list_tracks(video)
        first = caching.fetch(video, selection)
        second_tracks = caching.list_tracks(video)
        second = caching.fetch(video, selection)

        assert (first_tracks, first) == (second_tracks, second)
        assert source.list_calls == 1
        assert len(source.fetch_calls) == 1

    def test_track_list_is_refreshed_after_ttl_but_transcripts_are_not(
        self,
        source: FakeTranscriptSource,
        video: VideoRef,
        entries: TimedEntries,
        clock: FakeClock,
    ) -> None:
        caching = CachingTranscriptSource(source, entries)
        selection = TrackSelection(source.tracks[0])
        caching.list_tracks(video)
        caching.fetch(video, selection)

        clock.now += 2 * DAY
        caching.list_tracks(video)
        caching.fetch(video, selection)

        assert source.list_calls == 2
        assert len(source.fetch_calls) == 1

    def test_different_selections_are_cached_separately(
        self, source: FakeTranscriptSource, video: VideoRef, entries: TimedEntries
    ) -> None:
        caching = CachingTranscriptSource(source, entries)
        track = source.tracks[0]

        caching.fetch(video, TrackSelection(track))
        caching.fetch(video, TrackSelection(track, translate_to="es"))

        assert len(source.fetch_calls) == 2

    def test_malformed_entries_are_refetched(
        self, source: FakeTranscriptSource, video: VideoRef
    ) -> None:
        cache = InMemoryCache()
        entries = TimedEntries(cache)
        caching = CachingTranscriptSource(source, entries)
        selection = TrackSelection(source.tracks[0])
        caching.list_tracks(video)
        caching.fetch(video, selection)
        for key in cache.entries:
            entries.set(key, {"unexpected": True})

        caching.list_tracks(video)
        caching.fetch(video, selection)

        assert source.list_calls == 2
        assert len(source.fetch_calls) == 2


class CountingMetadataSource(FakeMetadataSource):
    calls: int = 0

    def get_metadata(self, video: VideoRef) -> VideoMetadata:
        self.calls += 1
        return super().get_metadata(video)


class TestCachingMetadataSource:
    def test_caches_until_ttl(
        self, video: VideoRef, entries: TimedEntries, clock: FakeClock
    ) -> None:
        inner = CountingMetadataSource()
        caching = CachingMetadataSource(inner, entries)

        first = caching.get_metadata(video)
        second = caching.get_metadata(video)
        clock.now += 8 * DAY
        caching.get_metadata(video)

        assert first == second == inner.metadata
        assert inner.calls == 2

    def test_failures_are_not_cached(self, video: VideoRef, entries: TimedEntries) -> None:
        inner = CountingMetadataSource(fail=True)
        caching = CachingMetadataSource(inner, entries)

        for _ in range(2):
            with pytest.raises(MetadataFetchError):
                caching.get_metadata(video)

        assert inner.calls == 2

    def test_malformed_entry_is_refetched(self, video: VideoRef, entries: TimedEntries) -> None:
        inner = CountingMetadataSource()
        caching = CachingMetadataSource(inner, entries)
        caching.get_metadata(video)
        entries.set(f"v{serialization.SCHEMA_VERSION}:metadata:{video.video_id}", [])

        assert caching.get_metadata(video) == inner.metadata
        assert inner.calls == 2
