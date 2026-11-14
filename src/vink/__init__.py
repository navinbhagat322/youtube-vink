"""vink — turn YouTube transcripts into clean, timestamped Markdown and detailed notes."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("vink")
except PackageNotFoundError:  # pragma: no cover - only when running from an uninstalled tree
    __version__ = "0.0.0"

__all__ = ["__version__"]
