"""Building safe file names from untrusted text such as video titles."""

import re
import unicodedata
from typing import Final

_FORBIDDEN: Final = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
_WHITESPACE: Final = re.compile(r"\s+")
_WINDOWS_RESERVED: Final = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{n}" for n in range(1, 10)}
    | {f"LPT{n}" for n in range(1, 10)}
)
_FALLBACK: Final = "untitled"


def safe_filename(text: str, *, max_length: int = 120) -> str:
    """Turn arbitrary text into a file name that is safe on every major OS.

    Path separators, reserved characters and control characters are replaced
    with spaces; whitespace is collapsed; leading and trailing dots and spaces
    are removed; Windows reserved device names are prefixed. Non-ASCII letters
    (for example Hindi titles) are kept.

    Args:
        text: Untrusted input, typically a video title.
        max_length: Maximum length of the result, excluding any extension.

    Returns:
        A non-empty file name stem without an extension.
    """
    name = unicodedata.normalize("NFC", text)
    name = _FORBIDDEN.sub(" ", name)
    name = _WHITESPACE.sub(" ", name).strip(" .")
    name = name[:max_length].rstrip(" .")
    if not name:
        return _FALLBACK
    if name.split(".", 1)[0].upper() in _WINDOWS_RESERVED:
        name = f"_{name}"
    return name
