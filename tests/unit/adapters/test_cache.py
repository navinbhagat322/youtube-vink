from pathlib import Path

import pytest

from tests.fakes import FakeTranscriptSource, InMemoryCache
from vink.adapters.cache import CachingTranscriptSource, FileCache, serialization
from vink.domain.models import RawTranscript, Segment, TrackInfo, TrackKind, TrackSelection
from vink.domain.video_ref import VideoRef


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
        assert serialization.load_tracks(serialization.dump_tracks(tracks)) == tracks

    def test_transcript_round_trip(self, video: VideoRef) -> None:
        raw = RawTranscript(video, "hi", "Hindi", TrackKind.GENERATED, (Segment(1, 2, "नमस्ते"),))

        assert serialization.load_transcript(serialization.dump_transcript(raw)) == raw

    @pytest.mark.parametrize("data", ["{}", "[]", "[{}]", "nope", '"string"'])
    def test_malformed_tracks_raise_value_error(self, data: str) -> None:
        if data == "[]":
            assert serialization.load_tracks(data) == []
            return
        with pytest.raises(ValueError, match=r".+"):
            serialization.load_tracks(data)

    @pytest.mark.parametrize("data", ["[]", "{}", '{"video_id": "aircAruvnKk"}', "nope"])
    def test_malformed_transcript_raises_value_error(self, data: str) -> None:
        with pytest.raises(ValueError, match=r".+"):
            serialization.load_transcript(data)


class TestCachingTranscriptSource:
    def test_second_call_is_served_from_cache(
        self, source: FakeTranscriptSource, video: VideoRef
    ) -> None:
        caching = CachingTranscriptSource(source, InMemoryCache())
        selection = TrackSelection(source.tracks[0])

        first_tracks = caching.list_tracks(video)
        first = caching.fetch(video, selection)
        second_tracks = caching.list_tracks(video)
        second = caching.fetch(video, selection)

        assert (first_tracks, first) == (second_tracks, second)
        assert source.list_calls == 1
        assert len(source.fetch_calls) == 1

    def test_different_selections_are_cached_separately(
        self, source: FakeTranscriptSource, video: VideoRef
    ) -> None:
        caching = CachingTranscriptSource(source, InMemoryCache())
        track = source.tracks[0]

        caching.fetch(video, TrackSelection(track))
        caching.fetch(video, TrackSelection(track, translate_to="es"))

        assert len(source.fetch_calls) == 2

    def test_corrupt_entries_are_refetched(
        self, source: FakeTranscriptSource, video: VideoRef
    ) -> None:
        cache = InMemoryCache()
        caching = CachingTranscriptSource(source, cache)
        selection = TrackSelection(source.tracks[0])
        caching.list_tracks(video)
        caching.fetch(video, selection)
        for key in cache.entries:
            cache.entries[key] = "corrupt"

        caching.list_tracks(video)
        caching.fetch(video, selection)

        assert source.list_calls == 2
        assert len(source.fetch_calls) == 2
