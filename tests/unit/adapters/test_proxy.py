from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig

from vink.adapters.youtube import ProxyOptions


def test_direct_connection_by_default() -> None:
    options = ProxyOptions()

    assert not options.enabled
    assert options.library_config() is None
    assert options.http_url() is None


def test_generic_proxy_applies_to_both_schemes() -> None:
    options = ProxyOptions(url="http://user:pass@proxy.example:8080")

    config = options.library_config()

    assert options.enabled
    assert isinstance(config, GenericProxyConfig)
    assert config.to_requests_dict() == {
        "http": "http://user:pass@proxy.example:8080",
        "https": "http://user:pass@proxy.example:8080",
    }
    assert options.http_url() == "http://user:pass@proxy.example:8080"


def test_webshare_uses_rotating_endpoint() -> None:
    options = ProxyOptions(webshare_username="alice", webshare_password="s3cret")

    config = options.library_config()

    assert isinstance(config, WebshareProxyConfig)
    url = options.http_url()
    assert url is not None
    assert "alice-rotate" in url
    assert "p.webshare.io" in url


def test_repr_never_shows_credentials() -> None:
    options = ProxyOptions(url="http://user:pass@proxy.example:8080")
    webshare = ProxyOptions(webshare_username="alice", webshare_password="s3cret")

    assert "pass" not in repr(options)
    assert "s3cret" not in repr(webshare)
    assert repr(webshare) == "ProxyOptions(kind='webshare')"
