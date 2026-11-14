import pytest

from vink.processing.cleaning import clean_caption_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("hello   world", "hello world"),
        ("  padded\ntext  ", "padded text"),
        ("[Music]", ""),
        ("[Applause] thank you", "thank you"),
        ("♪ la la ♪", "la la"),
        ("rock &amp; roll", "rock & roll"),
        ("[संगीत] नमस्ते दोस्तों", "नमस्ते दोस्तों"),
    ],
)
def test_clean_caption_text(raw: str, expected: str) -> None:
    assert clean_caption_text(raw).text == expected


@pytest.mark.parametrize("raw", [">> next speaker", "&gt;&gt; next speaker", "  >>next speaker"])
def test_detects_speaker_change(raw: str) -> None:
    result = clean_caption_text(raw)

    assert result.speaker_change
    assert result.text == "next speaker"


def test_plain_text_is_not_speaker_change() -> None:
    assert not clean_caption_text("a > b").speaker_change
