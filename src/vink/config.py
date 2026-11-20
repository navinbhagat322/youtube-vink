"""Typed application settings.

Settings are read from, in order of precedence: explicit overrides passed by
an interface (CLI flags, tool arguments), environment variables prefixed with
``VINK_``, a ``.env`` file in the working directory, and the defaults below.
Nothing outside this module reads environment variables.
"""

from pathlib import Path
from typing import Annotated, Any, Literal, Self
from urllib.parse import urlsplit

from platformdirs import user_cache_path, user_documents_path
from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]
McpTransport = Literal["stdio", "http"]

_PROXY_SCHEMES = frozenset({"http", "https"})
_MIN_TOKEN_LENGTH = 16


def default_mcp_output_dir() -> Path:
    """Output folder for the MCP server when none is configured: ``~/Documents/vink``."""
    return user_documents_path() / "vink"


class Settings(BaseSettings):
    """All user-configurable settings. See ``docs/configuration.md``."""

    model_config = SettingsConfigDict(
        env_prefix="VINK_",
        env_file=".env",
        env_file_encoding="utf-8",
        # Treat VINK_X= (empty) as "not set". Installers such as Claude Desktop
        # extensions pass optional fields the user left blank as empty strings.
        env_ignore_empty=True,
        extra="ignore",
        frozen=True,
    )

    languages: Annotated[tuple[str, ...], NoDecode] = Field(
        default=("en",),
        description="Preferred transcript languages, most preferred first.",
    )
    allow_translation: bool = Field(
        default=True,
        description="Fall back to YouTube machine translation when no track matches.",
    )
    output_dir: Path = Field(
        default=Path("output"),
        description="Directory where generated files are written.",
    )
    output_format: str = Field(default="markdown", description="Default output format.")
    cache_dir: Path = Field(
        default_factory=lambda: user_cache_path("vink"),
        description="Directory for the local transcript cache.",
    )
    use_cache: bool = Field(default=True, description="Cache fetched transcripts locally.")
    chunk_seconds: int = Field(
        default=600,
        ge=60,
        description="Target chunk length in seconds for chunked note generation.",
    )
    http_timeout: float = Field(
        default=10.0,
        gt=0,
        description="Timeout in seconds for HTTP requests.",
    )
    log_level: LogLevel = Field(default="WARNING", description="Logging verbosity.")

    # --- Network: proxies -------------------------------------------------
    proxy_url: SecretStr | None = Field(
        default=None,
        description="HTTP(S) proxy for all YouTube requests, e.g. http://user:pass@host:8080.",
    )
    webshare_username: str | None = Field(
        default=None,
        description="Webshare rotating residential proxy username.",
    )
    webshare_password: SecretStr | None = Field(
        default=None,
        description="Webshare rotating residential proxy password.",
    )

    # --- MCP server -------------------------------------------------------
    mcp_transport: McpTransport = Field(
        default="stdio",
        description="'stdio' for local clients, 'http' to serve over Streamable HTTP.",
    )
    mcp_host: str = Field(default="127.0.0.1", description="Interface the HTTP server binds to.")
    mcp_port: int = Field(default=8000, ge=1, le=65535, description="HTTP server port.")
    auth_token: SecretStr | None = Field(
        default=None,
        description="Bearer token HTTP clients must send. Required for the HTTP transport.",
    )
    allowed_hosts: Annotated[tuple[str, ...], NoDecode] = Field(
        default=(),
        description="Host headers the HTTP server accepts, e.g. vink.example.com. Empty: any.",
    )

    @field_validator("languages", mode="before")
    @classmethod
    def _split_languages(cls, value: object) -> object:
        """Accept ``"en,hi"`` as well as a sequence of codes."""
        if isinstance(value, str):
            value = value.split(",")
        if isinstance(value, list | tuple):
            codes = tuple(str(code).strip() for code in value if str(code).strip())
            if not codes:
                raise ValueError("at least one language code is required")
            return codes
        return value

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def _split_hosts(cls, value: object) -> object:
        """Accept ``"a.example.com,b.example.com"`` as well as a sequence."""
        if isinstance(value, str):
            value = value.split(",")
        if isinstance(value, list | tuple):
            return tuple(str(host).strip() for host in value if str(host).strip())
        return value

    @field_validator("proxy_url")
    @classmethod
    def _check_proxy_url(cls, value: SecretStr | None) -> SecretStr | None:
        """Reject malformed proxy URLs at startup instead of on the first request."""
        if value is None:
            return None
        problem = proxy_url_problem(value.get_secret_value())
        if problem:
            raise ValueError(problem)
        return value

    @field_validator("auth_token")
    @classmethod
    def _check_token(cls, value: SecretStr | None) -> SecretStr | None:
        """Require tokens long enough to resist guessing."""
        if value is not None and len(value.get_secret_value()) < _MIN_TOKEN_LENGTH:
            raise ValueError(f"must be at least {_MIN_TOKEN_LENGTH} characters")
        return value

    @model_validator(mode="after")
    def _check_proxy_combination(self) -> Self:
        """Webshare needs both credentials and cannot be combined with a generic proxy."""
        webshare_parts = (self.webshare_username, self.webshare_password)
        if any(webshare_parts) and not all(webshare_parts):
            raise ValueError("set both VINK_WEBSHARE_USERNAME and VINK_WEBSHARE_PASSWORD")
        if all(webshare_parts) and self.proxy_url is not None:
            raise ValueError("set either VINK_PROXY_URL or the Webshare credentials, not both")
        return self

    def with_defaults(self, **defaults: Any) -> Self:
        """Return a copy where fields the user did not set take the given values.

        A field counts as set if it came from an explicit argument, an
        environment variable or the ``.env`` file. Values are trusted
        program constants and are not re-validated.
        """
        missing = {k: v for k, v in defaults.items() if k not in self.model_fields_set}
        return self.model_copy(update=missing) if missing else self


def proxy_url_problem(url: str) -> str | None:
    """Explain what is wrong with a proxy URL, or return ``None`` if it looks valid.

    The credentials are never included in the explanation.
    """
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return "proxy URL has an invalid port; it must be a number, e.g. http://host:8080"
    if parts.scheme not in _PROXY_SCHEMES:
        return "proxy URL must start with http:// or https://"
    if not parts.hostname:
        return "proxy URL has no host, e.g. http://user:pass@proxy.example.com:8080"
    if port is None:
        return "proxy URL needs a port, e.g. http://proxy.example.com:8080"
    return None
