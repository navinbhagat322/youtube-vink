"""Typed application settings.

Settings are read from, in order of precedence: explicit overrides passed by
an interface (CLI flags, tool arguments), environment variables prefixed with
``VINK_``, a ``.env`` file in the working directory, and the defaults below.
Nothing outside this module reads environment variables.
"""

from pathlib import Path
from typing import Annotated, Literal

from platformdirs import user_cache_path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class Settings(BaseSettings):
    """All user-configurable settings. See ``docs/configuration.md``."""

    model_config = SettingsConfigDict(
        env_prefix="VINK_",
        env_file=".env",
        env_file_encoding="utf-8",
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
