"""Cleaning raw caption text."""

import html
import re
from dataclasses import dataclass
from typing import Final

_SOUND_CUE: Final = re.compile(r"\[[^\]]*\]")
"""Bracketed cues such as ``[Music]``, ``[Applause]`` or ``[संगीत]``."""

_MUSIC_SYMBOLS: Final = re.compile(r"[♪♫♬]+")
_SPEAKER_MARKER: Final = re.compile(r"^\s*(?:>>|&gt;&gt;)\s*")
_WHITESPACE: Final = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class CleanedText:
    """Result of cleaning one caption cue.

    Attributes:
        text: The cleaned text; empty if the cue held only noise.
        speaker_change: ``True`` if the cue began with a ``>>`` speaker marker.
    """

    text: str
    speaker_change: bool


def clean_caption_text(raw: str) -> CleanedText:
    """Normalize one caption cue into plain readable text.

    Decodes HTML entities, detects a leading ``>>`` speaker-change marker,
    removes bracketed sound cues and music symbols, and collapses whitespace.

    Args:
        raw: Caption text exactly as delivered by the source.

    Returns:
        The cleaned text and whether a new speaker starts here.
    """
    speaker_change = bool(_SPEAKER_MARKER.match(raw))
    text = _SPEAKER_MARKER.sub("", raw)
    text = html.unescape(text)
    text = _SOUND_CUE.sub(" ", text)
    text = _MUSIC_SYMBOLS.sub(" ", text)
    text = _WHITESPACE.sub(" ", text).strip()
    return CleanedText(text=text, speaker_change=speaker_change)
