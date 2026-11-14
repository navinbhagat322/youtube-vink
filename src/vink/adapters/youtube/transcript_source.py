"""Caption tracks from YouTube via the open-source ``youtube-transcript-api`` library.

The library reads the same internal endpoints YouTube's own player uses, so no
API key is required. See ``docs/adr/0002-transcripts-without-data-api.md``.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from youtube_transcript_api import (
    AgeRestricted,
    CouldNotRetrieveTranscript,
    InvalidVideoId,
    IpBlocked,
    NoTranscriptFound,
    NotTranslatable,
    RequestBlocked,
    TranscriptsDisabled,
    TranslationLanguageNotAvailable,
    VideoUnavailable,
    VideoUnplayable,
    YouTubeTranscriptApi,
)
from youtube_transcript_api import Transcript as LibraryTranscript

from vink.domain.errors import (
    LanguageUnavailableError,
    TranscriptFetchError,
    TranscriptsDisabledError,
    VideoUnavailableError,
)
from vink.domain.models import RawTranscript, Segment, TrackInfo, TrackSelection
from vink.domain.video_ref import VideoRef

logger = logging.getLogger(__name__)


class YouTubeTranscriptSource:
    """:class:`~vink.ports.TranscriptSource` backed by ``youtube-transcript-api``.

    Args:
        api: Library client to use. Inject a configured instance to set a proxy
            or a custom HTTP session; defaults to a plain client.
    """

    def __init__(self, api: YouTubeTranscriptApi | None = None) -> None:
        self._api = api or YouTubeTranscriptApi()

    def list_tracks(self, video: VideoRef) -> list[TrackInfo]:
        """Return every caption track available for ``video``."""
        with _translate_errors(video.video_id):
            transcript_list = self._api.list(video.video_id)
            tracks = [_to_track_info(item) for item in transcript_list]
        logger.debug("Found %d caption tracks for %s", len(tracks), video.video_id)
        return tracks

    def fetch(self, video: VideoRef, selection: TrackSelection) -> RawTranscript:
        """Fetch the transcript described by ``selection``."""
        track = selection.track
        with _translate_errors(video.video_id, requested=selection.language_code):
            transcript_list = self._api.list(video.video_id)
            if track.is_generated:
                source = transcript_list.find_generated_transcript([track.language_code])
            else:
                source = transcript_list.find_manually_created_transcript([track.language_code])
            if selection.translate_to:
                source = source.translate(selection.translate_to)
            fetched = source.fetch()

        segments = tuple(
            Segment(start=snippet.start, duration=snippet.duration, text=snippet.text)
            for snippet in fetched.snippets
        )
        logger.info(
            "Fetched %d segments (%s, %s) for %s",
            len(segments),
            selection.language_code,
            selection.kind,
            video.video_id,
        )
        return RawTranscript(
            video=video,
            language_code=selection.language_code,
            language_name=source.language,
            kind=selection.kind,
            segments=segments,
        )


def _to_track_info(item: LibraryTranscript) -> TrackInfo:
    """Convert a library transcript descriptor into a domain :class:`TrackInfo`."""
    return TrackInfo(
        language_code=item.language_code,
        language_name=item.language,
        is_generated=item.is_generated,
        translation_codes=frozenset(lang.language_code for lang in item.translation_languages),
    )


@contextmanager
def _translate_errors(video_id: str, requested: str | None = None) -> Iterator[None]:
    """Convert ``youtube-transcript-api`` and network exceptions into domain errors."""
    try:
        yield
    except TranscriptsDisabled as exc:
        raise TranscriptsDisabledError(video_id) from exc
    except (VideoUnavailable, InvalidVideoId) as exc:
        raise VideoUnavailableError(video_id, "the video does not exist or was removed") from exc
    except AgeRestricted as exc:
        raise VideoUnavailableError(video_id, "the video is age-restricted") from exc
    except VideoUnplayable as exc:
        raise VideoUnavailableError(video_id, "the video is not playable") from exc
    except (NoTranscriptFound, NotTranslatable, TranslationLanguageNotAvailable) as exc:
        raise LanguageUnavailableError(
            video_id, requested=[requested] if requested else [], available=[]
        ) from exc
    except (RequestBlocked, IpBlocked) as exc:
        raise TranscriptFetchError(
            "YouTube is blocking requests from this network (common on cloud servers). "
            "Run vink from a home or office connection, or configure a proxy."
        ) from exc
    except CouldNotRetrieveTranscript as exc:
        raise TranscriptFetchError(f"Could not retrieve transcript for {video_id}.") from exc
    except OSError as exc:  # requests.RequestException derives from OSError
        raise TranscriptFetchError(f"Network error while contacting YouTube: {exc}") from exc
