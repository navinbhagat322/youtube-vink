"""Splitting a transcript into chunks for note generation."""

from collections.abc import Sequence
from typing import Final

from vink.domain.errors import InvalidInputError
from vink.domain.models import Chunk, Paragraph

_MIN_TAIL_RATIO: Final = 0.25
"""A final chunk shorter than this fraction of the target is merged into the previous one."""


def chunk_paragraphs(paragraphs: Sequence[Paragraph], target_seconds: float) -> tuple[Chunk, ...]:
    """Group paragraphs into chunks of roughly ``target_seconds`` each.

    Paragraphs are never split, so chunks always begin and end on a paragraph
    boundary. A very short trailing chunk is merged into the one before it so
    the last pass of note generation is not wasted on a few sentences.

    Args:
        paragraphs: Paragraphs in playback order.
        target_seconds: Desired chunk length in seconds; must be positive.

    Returns:
        Chunks with 1-based indexes. Empty if there are no paragraphs.

    Raises:
        InvalidInputError: If ``target_seconds`` is not positive.
    """
    if target_seconds <= 0:
        raise InvalidInputError(f"Chunk length must be positive, got {target_seconds}.")

    groups: list[list[Paragraph]] = []
    for paragraph in paragraphs:
        if groups and paragraph.start - groups[-1][0].start < target_seconds:
            groups[-1].append(paragraph)
        else:
            groups.append([paragraph])

    if len(groups) > 1:
        tail = groups[-1]
        if tail[-1].end - tail[0].start < target_seconds * _MIN_TAIL_RATIO:
            groups[-2].extend(groups.pop())

    total = len(groups)
    return tuple(
        Chunk(index=number, total=total, paragraphs=tuple(group))
        for number, group in enumerate(groups, start=1)
    )
