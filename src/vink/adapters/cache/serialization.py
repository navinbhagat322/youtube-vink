"""JSON (de)serialization of domain models for caching.

The format is versioned through :data:`SCHEMA_VERSION`, which is part of every
cache key. Bump it whenever the shape below changes; old entries then simply
stop matching and are refetched.
"""

import json
from collections.abc import Sequence
from typing import Any, Final

from vink.domain.models import RawTranscript, Segment, TrackInfo, TrackKind
from vink.domain.video_ref import VideoRef

SCHEMA_VERSION: Final = 1


def dump_tracks(tracks: Sequence[TrackInfo]) -> str:
    """Serialize a list of tracks to JSON."""
    return json.dumps(
        [
            {
                "language_code": track.language_code,
                "language_name": track.language_name,
                "is_generated": track.is_generated,
                "translation_codes": sorted(track.translation_codes),
            }
            for track in tracks
        ],
        ensure_ascii=False,
    )


def load_tracks(data: str) -> list[TrackInfo]:
    """Deserialize tracks produced by :func:`dump_tracks`.

    Raises:
        ValueError: If ``data`` is not valid serialized tracks.
    """
    try:
        return [
            TrackInfo(
                language_code=str(item["language_code"]),
                language_name=str(item["language_name"]),
                is_generated=bool(item["is_generated"]),
                translation_codes=frozenset(str(c) for c in item["translation_codes"]),
            )
            for item in _load_json(data, list)
        ]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Malformed cached tracks: {exc}") from exc


def dump_transcript(transcript: RawTranscript) -> str:
    """Serialize a raw transcript to JSON."""
    return json.dumps(
        {
            "video_id": transcript.video.video_id,
            "language_code": transcript.language_code,
            "language_name": transcript.language_name,
            "kind": transcript.kind.value,
            "segments": [[s.start, s.duration, s.text] for s in transcript.segments],
        },
        ensure_ascii=False,
    )


def load_transcript(data: str) -> RawTranscript:
    """Deserialize a transcript produced by :func:`dump_transcript`.

    Raises:
        ValueError: If ``data`` is not a valid serialized transcript.
    """
    try:
        payload = _load_json(data, dict)
        return RawTranscript(
            video=VideoRef(str(payload["video_id"])),
            language_code=str(payload["language_code"]),
            language_name=str(payload["language_name"]),
            kind=TrackKind(payload["kind"]),
            segments=tuple(
                Segment(start=float(start), duration=float(duration), text=str(text))
                for start, duration, text in payload["segments"]
            ),
        )
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Malformed cached transcript: {exc}") from exc


def _load_json(data: str, expected: type) -> Any:
    """Parse JSON and check the top-level type."""
    value = json.loads(data)
    if not isinstance(value, expected):
        raise ValueError(f"Expected JSON {expected.__name__}, got {type(value).__name__}")
    return value
