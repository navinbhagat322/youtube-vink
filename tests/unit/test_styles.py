import pytest

from vink.domain.errors import InvalidInputError
from vink.styles import DEFAULT_STYLE, available_styles, load_style


class TestStyles:
    def test_bundled_styles_are_discovered(self) -> None:
        assert {"detailed-notes", "clean-transcript"} <= set(available_styles())
        assert DEFAULT_STYLE in available_styles()

    def test_load_style_fills_language(self) -> None:
        text = load_style("clean-transcript", output_language="Hindi")

        assert "{output_language}" not in text
        assert "readable written version in Hindi" in text

    def test_unknown_style_raises(self) -> None:
        with pytest.raises(InvalidInputError, match="Available:"):
            load_style("nope", output_language="English")
