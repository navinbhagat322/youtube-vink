"""Choosing the best caption track for a list of preferred languages."""

from collections.abc import Iterable, Sequence
from typing import Final

from vink.domain.errors import LanguageUnavailableError
from vink.domain.models import TrackInfo, TrackSelection

ORIGINAL_LANGUAGE: Final = "original"
"""Special language value meaning "the language spoken in the video"."""


def select_track(
    tracks: Sequence[TrackInfo],
    preferred: Sequence[str],
    *,
    video_id: str,
    allow_translation: bool = True,
) -> TrackSelection:
    """Choose the best caption track for the requested languages.

    For each preferred language, in order, a manual track beats an
    auto-generated one, and an exact code match (``pt-BR``) beats a base match
    (``pt``). Only when no track matches any preferred language does YouTube
    machine translation come into play, and then manual source tracks are
    preferred over auto-generated ones.

    The special value :data:`ORIGINAL_LANGUAGE` stands for the language spoken
    in the video, which is the language of the auto-generated track.

    Args:
        tracks: All caption tracks available for the video.
        preferred: Language codes in order of preference, e.g. ``["en", "hi"]``.
        video_id: Used only for error messages.
        allow_translation: Whether YouTube machine translation may be used.

    Returns:
        The selected track, possibly with a translation target.

    Raises:
        LanguageUnavailableError: If nothing matches and translation is not possible.
    """
    languages = _resolve_languages(preferred, tracks)
    manual = [track for track in tracks if not track.is_generated]
    generated = [track for track in tracks if track.is_generated]

    for language in languages:
        for pool in (manual, generated):
            match = _find_by_language(pool, language)
            if match is not None:
                return TrackSelection(track=match)

    if allow_translation:
        for language in languages:
            for source in (*manual, *generated):
                target = _match_code(language, source.translation_codes)
                if target is not None:
                    return TrackSelection(track=source, translate_to=target)

    raise LanguageUnavailableError(
        video_id=video_id,
        requested=languages,
        available=_unique(track.language_code for track in tracks),
    )


def _resolve_languages(preferred: Sequence[str], tracks: Sequence[TrackInfo]) -> list[str]:
    """Replace :data:`ORIGINAL_LANGUAGE` with a real code and drop duplicates."""
    spoken = next((track.language_code for track in tracks if track.is_generated), None)
    if spoken is None and tracks:
        spoken = tracks[0].language_code

    resolved: list[str] = []
    for language in preferred:
        code = spoken if language.lower() == ORIGINAL_LANGUAGE else language
        if code is not None:
            resolved.append(code)
    return _unique(resolved)


def _find_by_language(pool: Sequence[TrackInfo], language: str) -> TrackInfo | None:
    """Return the first track in ``pool`` whose language matches ``language``."""
    code = _match_code(language, [track.language_code for track in pool])
    if code is None:
        return None
    return next(track for track in pool if track.language_code == code)


def _match_code(wanted: str, candidates: Iterable[str]) -> str | None:
    """Return the candidate matching ``wanted`` exactly, else by base language.

    Matching is case-insensitive. ``"en"`` matches ``"en-GB"`` and
    ``"en-GB"`` matches ``"en"`` when no exact match exists.
    """
    options = list(candidates)
    wanted_lower = wanted.lower()
    for code in options:
        if code.lower() == wanted_lower:
            return code
    wanted_base = _base(wanted_lower)
    for code in options:
        if _base(code.lower()) == wanted_base:
            return code
    return None


def _base(code: str) -> str:
    """Return the primary language subtag: ``"pt-br"`` → ``"pt"``."""
    return code.split("-", 1)[0]


def _unique(values: Iterable[str]) -> list[str]:
    """Return ``values`` without duplicates, preserving order."""
    return list(dict.fromkeys(values))
