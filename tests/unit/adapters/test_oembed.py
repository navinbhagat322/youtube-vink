from collections.abc import Callable

import httpx
import pytest

from vink.adapters.youtube import OEmbedMetadataSource
from vink.adapters.youtube.oembed import OEMBED_URL
from vink.domain.errors import MetadataFetchError
from vink.domain.models import VideoMetadata
from vink.domain.video_ref import VideoRef

VIDEO = VideoRef("aircAruvnKk")


def _source(handler: Callable[[httpx.Request], httpx.Response]) -> OEmbedMetadataSource:
    return OEmbedMetadataSource(httpx.Client(transport=httpx.MockTransport(handler)))


def test_returns_title_and_channel() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={"title": "A Talk", "author_name": "Chan", "author_url": "https://yt/@chan"},
        )

    metadata = _source(handler).get_metadata(VIDEO)

    assert metadata == VideoMetadata("A Talk", "Chan", "https://yt/@chan")
    assert str(seen[0].url).startswith(OEMBED_URL)
    assert seen[0].url.params["url"] == VIDEO.url


def test_missing_author_fields_are_none() -> None:
    metadata = _source(lambda _: httpx.Response(200, json={"title": "T"})).get_metadata(VIDEO)

    assert metadata == VideoMetadata("T", None, None)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(404, text="Not Found"),
        httpx.Response(401, text="Unauthorized"),
        httpx.Response(200, text="not json"),
        httpx.Response(200, json=["unexpected"]),
        httpx.Response(200, json={"title": ""}),
    ],
)
def test_bad_responses_raise_metadata_error(response: httpx.Response) -> None:
    with pytest.raises(MetadataFetchError):
        _source(lambda _: response).get_metadata(VIDEO)


def test_network_error_raises_metadata_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    with pytest.raises(MetadataFetchError):
        _source(handler).get_metadata(VIDEO)
