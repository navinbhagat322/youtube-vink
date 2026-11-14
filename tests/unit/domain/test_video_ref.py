import pytest

from vink.domain.errors import InvalidInputError
from vink.domain.video_ref import VideoRef, parse_video_ref

VIDEO_ID = "aircAruvnKk"


@pytest.mark.parametrize(
    "value",
    [
        VIDEO_ID,
        f"  {VIDEO_ID}  ",
        f"https://www.youtube.com/watch?v={VIDEO_ID}",
        f"https://www.youtube.com/watch?v={VIDEO_ID}&t=30s&si=abc",
        f"https://youtube.com/watch?feature=share&v={VIDEO_ID}",
        f"https://m.youtube.com/watch?v={VIDEO_ID}",
        f"https://music.youtube.com/watch?v={VIDEO_ID}",
        f"youtube.com/watch?v={VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}?si=xyz&t=12",
        f"https://www.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/live/{VIDEO_ID}?feature=share",
        f"https://www.youtube.com/embed/{VIDEO_ID}",
        f"https://www.youtube.com/v/{VIDEO_ID}",
    ],
)
def test_parse_video_ref_accepts_common_forms(value: str) -> None:
    assert parse_video_ref(value).video_id == VIDEO_ID


@pytest.mark.parametrize(
    "value",
    [
        "",
        "not a url",
        "https://example.com/watch?v=aircAruvnKk",
        "https://www.youtube.com/watch?v=short",
        "https://www.youtube.com/playlist?list=PL123",
        "https://www.youtube.com/@channel",
        "https://youtu.be/",
    ],
)
def test_parse_video_ref_rejects_invalid_input(value: str) -> None:
    with pytest.raises(InvalidInputError):
        parse_video_ref(value)


def test_video_ref_rejects_malformed_id() -> None:
    with pytest.raises(InvalidInputError):
        VideoRef("bad id!")


def test_video_ref_builds_urls() -> None:
    video = VideoRef(VIDEO_ID)

    assert video.url == f"https://www.youtube.com/watch?v={VIDEO_ID}"
    assert video.url_at(75.9) == f"https://youtu.be/{VIDEO_ID}?t=75"
