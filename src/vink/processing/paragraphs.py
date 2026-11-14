"""Grouping caption fragments into readable paragraphs."""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from vink.domain.models import Paragraph, Segment
from vink.processing.cleaning import clean_caption_text

_SENTENCE_END: Final = re.compile(
    r"[.!?"
    r"\u0964\u0965"  # Devanagari danda and double danda
    r"\u3002\uff01\uff1f"  # CJK full stop, fullwidth ! and ?
    r"\u2026"  # ellipsis
    r"][\"'\u201d\u2019)\]]*$"  # optional closing quotes or brackets
)
"""Sentence-final punctuation, optionally followed by closing quotes or brackets."""

_SPACE_BEFORE_PUNCTUATION: Final = re.compile(r"\s+([,.!?;:।॥])")


@dataclass(frozen=True, slots=True)
class ParagraphOptions:
    """Tuning knobs for paragraph building.

    Attributes:
        target_seconds: Prefer to end a paragraph at a sentence boundary after this long.
        max_seconds: Always end a paragraph after this long, even mid-sentence.
            Auto-generated captions often have no punctuation, so this keeps
            paragraphs readable.
        pause_seconds: A silence at least this long starts a new paragraph.
        min_seconds: Never end a paragraph because of a pause before this long.
    """

    target_seconds: float = 45.0
    max_seconds: float = 90.0
    pause_seconds: float = 2.5
    min_seconds: float = 10.0


def build_paragraphs(
    segments: Sequence[Segment],
    options: ParagraphOptions | None = None,
) -> tuple[Paragraph, ...]:
    """Clean caption segments and merge them into paragraphs.

    A new paragraph starts when the speaker changes, after a long pause, at a
    sentence boundary once the paragraph is long enough, or unconditionally
    once it reaches ``max_seconds``. Segments that contain only noise (for
    example ``[Music]``) are dropped.

    Args:
        segments: Caption cues in playback order.
        options: Paragraph tuning; defaults are suitable for lectures and talks.

    Returns:
        Paragraphs in playback order.
    """
    opts = options or ParagraphOptions()
    paragraphs: list[Paragraph] = []
    parts: list[str] = []
    start = 0.0
    end = 0.0

    for segment in segments:
        cleaned = clean_caption_text(segment.text)
        if not cleaned.text:
            continue
        if parts and (
            cleaned.speaker_change or _should_break(parts[-1], start, end, segment.start, opts)
        ):
            paragraphs.append(_make_paragraph(parts, start, end))
            parts = []
        if not parts:
            start = segment.start
        parts.append(cleaned.text)
        end = max(end, segment.end)

    if parts:
        paragraphs.append(_make_paragraph(parts, start, end))
    return tuple(paragraphs)


def _should_break(
    last_text: str,
    paragraph_start: float,
    paragraph_end: float,
    next_start: float,
    opts: ParagraphOptions,
) -> bool:
    """Decide whether the next segment should start a new paragraph."""
    elapsed = next_start - paragraph_start
    pause = next_start - paragraph_end
    if elapsed >= opts.max_seconds:
        return True
    if elapsed >= opts.target_seconds and _SENTENCE_END.search(last_text):
        return True
    return pause >= opts.pause_seconds and elapsed >= opts.min_seconds


def _make_paragraph(parts: Sequence[str], start: float, end: float) -> Paragraph:
    """Join text fragments into one paragraph with tidy spacing."""
    text = _SPACE_BEFORE_PUNCTUATION.sub(r"\1", " ".join(parts))
    return Paragraph(start=start, end=end, text=text)
