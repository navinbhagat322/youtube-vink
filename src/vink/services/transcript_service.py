"""Use cases for discovering, fetching and preparing transcripts."""

import logging
from collections.abc import Sequence

from vink.domain.errors import MetadataFetchError
from vink.domain.models import Chunk, TrackInfo, TrackKind, Transcript, VideoMetadata
from vink.domain.video_ref import VideoRef
from vink.ports.metadata_source import MetadataSource
from vink.ports.transcript_source import TranscriptSource
from vink.processing.chunking import chunk_paragraphs
from vink.processing.paragraphs import ParagraphOptions, build_paragraphs
from vink.processing.track_selection import select_track

logger = logging.getLogger(__name__)


class TranscriptService:
    """Fetches transcripts and turns them into clean, chunkable documents.

    Args:
        source: Where caption tracks come from.
        metadata: Where titles and channel names come from.
        paragraph_options: Tuning for paragraph building.
    """

    def __init__(
        self,
        source: TranscriptSource,
        metadata: MetadataSource,
        *,
        paragraph_options: ParagraphOptions | None = None,
    ) -> None:
        self._source = source
        self._metadata = metadata
        self._paragraph_options = paragraph_options or ParagraphOptions()

    def list_tracks(self, video: VideoRef) -> list[TrackInfo]:
        """Return every caption track available for ``video``."""
        return self._source.list_tracks(video)

    def get_metadata(self, video: VideoRef) -> VideoMetadata:
        """Return metadata for ``video``, falling back to the video ID as title.

        Metadata is cosmetic, so a failed lookup is logged rather than raised.
        """
        try:
            return self._metadata.get_metadata(video)
        except MetadataFetchError as exc:
            logger.warning("Using video ID as title: %s", exc)
            return VideoMetadata(title=video.video_id)

    def get_transcript(
        self,
        video: VideoRef,
        languages: Sequence[str],
        *,
        allow_translation: bool = True,
    ) -> Transcript:
        """Fetch the best transcript for ``languages`` and clean it into paragraphs.

        Args:
            video: The video to fetch.
            languages: Preferred language codes, most preferred first. The value
                ``"original"`` means the language spoken in the video.
            allow_translation: Whether YouTube machine translation may be used
                when no track matches.

        Returns:
            The cleaned transcript with metadata.

        Raises:
            TranscriptError: If no suitable transcript can be fetched.
            VideoUnavailableError: If the video cannot be accessed.
        """
        tracks = self._source.list_tracks(video)
        selection = select_track(
            tracks,
            languages,
            video_id=video.video_id,
            allow_translation=allow_translation,
        )
        if selection.kind is TrackKind.TRANSLATED:
            logger.warning(
                "No %s track; using YouTube translation from %s",
                selection.language_code,
                selection.track.language_code,
            )

        raw = self._source.fetch(video, selection)
        return Transcript(
            video=video,
            metadata=self.get_metadata(video),
            language_code=raw.language_code,
            language_name=raw.language_name,
            kind=raw.kind,
            paragraphs=build_paragraphs(raw.segments, self._paragraph_options),
        )

    def chunk(self, transcript: Transcript, target_seconds: float) -> tuple[Chunk, ...]:
        """Split ``transcript`` into chunks of roughly ``target_seconds`` each."""
        return chunk_paragraphs(transcript.paragraphs, target_seconds)
