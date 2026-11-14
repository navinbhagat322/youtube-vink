"""Proxy options for reaching YouTube from networks it blocks, such as cloud servers.

YouTube refuses most requests from data-center IP ranges. Routing them through
a residential proxy avoids that. Two kinds are supported:

- any HTTP(S) proxy URL, and
- Webshare rotating residential proxies, which ``youtube-transcript-api``
  supports natively: it retries with a fresh IP when a request is blocked.

See ``docs/hosting.md``.
"""

from dataclasses import dataclass, field

from youtube_transcript_api.proxies import GenericProxyConfig, ProxyConfig, WebshareProxyConfig


@dataclass(frozen=True, slots=True)
class ProxyOptions:
    """How vink should reach YouTube. All fields empty means a direct connection.

    Attributes:
        url: A generic HTTP(S) proxy URL, including credentials if needed.
        webshare_username: Webshare rotating residential proxy username.
        webshare_password: Webshare rotating residential proxy password.
    """

    url: str | None = None
    webshare_username: str | None = None
    webshare_password: str | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        kind = "webshare" if self.webshare_username else ("url" if self.url else "direct")
        return f"ProxyOptions(kind={kind!r})"

    @property
    def enabled(self) -> bool:
        """Whether any proxy is configured."""
        return self.url is not None or self.webshare_username is not None

    def library_config(self) -> ProxyConfig | None:
        """Return the equivalent ``youtube-transcript-api`` proxy configuration."""
        if self.webshare_username and self.webshare_password:
            return WebshareProxyConfig(
                proxy_username=self.webshare_username,
                proxy_password=self.webshare_password,
            )
        if self.url:
            return GenericProxyConfig(http_url=self.url, https_url=self.url)
        return None

    def http_url(self) -> str | None:
        """Return a single proxy URL for other HTTP clients, such as metadata lookups."""
        config = self.library_config()
        if isinstance(config, WebshareProxyConfig):
            return str(config.url)
        return self.url
