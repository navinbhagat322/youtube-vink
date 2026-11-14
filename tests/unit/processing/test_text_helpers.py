import pytest

from vink.processing.filenames import safe_filename
from vink.processing.timecode import format_timecode


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0, "0:00"), (5.9, "0:05"), (65, "1:05"), (3599, "59:59"), (3723, "1:02:03"), (-3, "0:00")],
)
def test_format_timecode(seconds: float, expected: str) -> None:
    assert format_timecode(seconds) == expected


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Simple Title", "Simple Title"),
        ("What is AI? | Part 1/3", "What is AI Part 1 3"),
        ('a<b>c:d"e\\f*g', "a b c d e f g"),
        ("../../etc/passwd", "etc passwd"),
        ("  ...dots and spaces...  ", "dots and spaces"),
        ("line\nbreak\ttab", "line break tab"),
        ("न्यूरल नेटवर्क क्या है?", "न्यूरल नेटवर्क क्या है"),
        ("CON", "_CON"),
        ("nul.txt", "_nul.txt"),
        ("", "untitled"),
        ("???", "untitled"),
    ],
)
def test_safe_filename(title: str, expected: str) -> None:
    assert safe_filename(title) == expected


def test_safe_filename_truncates() -> None:
    assert safe_filename("a" * 50 + " " + "b" * 100, max_length=52) == "a" * 50 + " b"
