from vink.domain.models import Segment
from vink.processing.paragraphs import ParagraphOptions, build_paragraphs


def _segments(texts: list[str], step: float = 5.0) -> list[Segment]:
    return [Segment(start=i * step, duration=step, text=t) for i, t in enumerate(texts)]


def test_merges_fragments_into_one_paragraph() -> None:
    paragraphs = build_paragraphs(_segments(["Hello", "there ,", "friend."]))

    assert len(paragraphs) == 1
    assert paragraphs[0].text == "Hello there, friend."
    assert (paragraphs[0].start, paragraphs[0].end) == (0.0, 15.0)


def test_drops_noise_only_segments() -> None:
    paragraphs = build_paragraphs(_segments(["[Music]", "Real words."]))

    assert [p.text for p in paragraphs] == ["Real words."]
    assert paragraphs[0].start == 5.0


def test_empty_input() -> None:
    assert build_paragraphs([]) == ()


def test_breaks_at_sentence_end_after_target() -> None:
    options = ParagraphOptions(target_seconds=10, max_seconds=100)
    texts = ["One.", "Two", "three.", "Four."]

    paragraphs = build_paragraphs(_segments(texts), options)

    assert [p.text for p in paragraphs] == ["One. Two three.", "Four."]


def test_breaks_after_devanagari_danda() -> None:
    options = ParagraphOptions(target_seconds=5, max_seconds=100)

    paragraphs = build_paragraphs(_segments(["यह पहला वाक्य है।", "दूसरा"]), options)

    assert len(paragraphs) == 2


def test_breaks_unpunctuated_text_at_max_length() -> None:
    options = ParagraphOptions(target_seconds=10, max_seconds=20)

    paragraphs = build_paragraphs(_segments(["word"] * 10), options)

    assert len(paragraphs) == 3
    assert all(p.end - p.start <= 20 for p in paragraphs)


def test_breaks_on_long_pause_once_minimum_reached() -> None:
    options = ParagraphOptions(target_seconds=100, max_seconds=200, pause_seconds=2, min_seconds=5)
    segments = [Segment(0, 3, "a"), Segment(3, 3, "b"), Segment(10, 2, "c")]

    paragraphs = build_paragraphs(segments, options)

    assert [p.text for p in paragraphs] == ["a b", "c"]


def test_ignores_pause_before_minimum_length() -> None:
    options = ParagraphOptions(pause_seconds=2, min_seconds=30)
    segments = [Segment(0, 1, "a"), Segment(5, 1, "b")]

    assert len(build_paragraphs(segments, options)) == 1


def test_speaker_change_starts_new_paragraph() -> None:
    paragraphs = build_paragraphs(_segments(["Question", ">> Answer"]))

    assert [p.text for p in paragraphs] == ["Question", "Answer"]


def test_overlapping_cues_keep_latest_end() -> None:
    segments = [Segment(0, 10, "long cue"), Segment(2, 1, "short")]

    assert build_paragraphs(segments)[0].end == 10
