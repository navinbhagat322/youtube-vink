import pytest

from vink.domain.errors import InvalidInputError
from vink.domain.models import Paragraph
from vink.processing.chunking import chunk_paragraphs


def _paragraphs(count: int, length: float = 60.0) -> list[Paragraph]:
    return [Paragraph(i * length, (i + 1) * length, f"p{i}") for i in range(count)]


def test_groups_paragraphs_by_target_length() -> None:
    chunks = chunk_paragraphs(_paragraphs(30), target_seconds=600)

    assert [len(c.paragraphs) for c in chunks] == [10, 10, 10]
    assert [c.index for c in chunks] == [1, 2, 3]
    assert all(c.total == 3 for c in chunks)


def test_never_splits_or_drops_paragraphs() -> None:
    paragraphs = _paragraphs(23, length=47)

    chunks = chunk_paragraphs(paragraphs, target_seconds=300)

    assert [p for c in chunks for p in c.paragraphs] == paragraphs


def test_merges_short_tail_into_previous_chunk() -> None:
    chunks = chunk_paragraphs(_paragraphs(21), target_seconds=600)

    assert [len(c.paragraphs) for c in chunks] == [10, 11]


def test_keeps_tail_that_is_long_enough() -> None:
    chunks = chunk_paragraphs(_paragraphs(13), target_seconds=600)

    assert [len(c.paragraphs) for c in chunks] == [10, 3]


def test_short_transcript_is_one_chunk() -> None:
    chunks = chunk_paragraphs(_paragraphs(2), target_seconds=600)

    assert len(chunks) == 1
    assert chunks[0].total == 1


def test_empty_input_gives_no_chunks() -> None:
    assert chunk_paragraphs([], target_seconds=600) == ()


@pytest.mark.parametrize("target", [0, -5])
def test_rejects_non_positive_target(target: float) -> None:
    with pytest.raises(InvalidInputError):
        chunk_paragraphs(_paragraphs(3), target_seconds=target)
