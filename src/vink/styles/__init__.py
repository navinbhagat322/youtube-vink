"""Note styles: instruction templates that tell an AI how to turn a transcript into notes.

Each style is a Markdown file in this package. Adding a style means adding a
file — it is discovered automatically. Templates may use these placeholders:

- ``{output_language}`` — the language the notes should be written in.
"""

from importlib import resources
from typing import Final

from vink.domain.errors import InvalidInputError

_SUFFIX: Final = ".md"
DEFAULT_STYLE: Final = "detailed-notes"


def available_styles() -> list[str]:
    """Return the names of all bundled styles, sorted."""
    package = resources.files(__name__)
    return sorted(
        entry.name.removesuffix(_SUFFIX)
        for entry in package.iterdir()
        if entry.is_file() and entry.name.endswith(_SUFFIX)
    )


def load_style(name: str, *, output_language: str) -> str:
    """Load a style template and fill in its placeholders.

    Args:
        name: Style name, e.g. ``"detailed-notes"``.
        output_language: Language for the notes, e.g. ``"English"`` or ``"Hinglish"``.

    Returns:
        The instructions, ready to send to a model.

    Raises:
        InvalidInputError: If no style with that name exists.
    """
    if name not in available_styles():
        raise InvalidInputError(
            f"Unknown style {name!r}. Available: {', '.join(available_styles())}."
        )
    template = resources.files(__name__).joinpath(f"{name}{_SUFFIX}").read_text(encoding="utf-8")
    return template.replace("{output_language}", output_language)
