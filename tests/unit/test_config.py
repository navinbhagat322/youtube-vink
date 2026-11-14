from pathlib import Path

import pytest
from pydantic import ValidationError

from vink.bootstrap import build_container
from vink.config import Settings


class TestSettings:
    def test_defaults(self) -> None:
        settings = Settings()

        assert settings.languages == ("en",)
        assert settings.allow_translation is True
        assert settings.chunk_seconds == 600

    def test_reads_environment(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv("VINK_LANGUAGES", "hi, en ,original")
        monkeypatch.setenv("VINK_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("VINK_ALLOW_TRANSLATION", "false")

        settings = Settings()

        assert settings.languages == ("hi", "en", "original")
        assert settings.output_dir == tmp_path
        assert settings.allow_translation is False

    def test_explicit_values_override_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("VINK_LANGUAGES", "hi")

        assert Settings.model_validate({"languages": "fr"}).languages == ("fr",)

    @pytest.mark.parametrize(
        "overrides",
        [{"languages": ""}, {"chunk_seconds": 10}, {"http_timeout": 0}, {"log_level": "LOUD"}],
    )
    def test_rejects_invalid_values(self, overrides: dict[str, object]) -> None:
        with pytest.raises(ValidationError):
            Settings(**overrides)  # type: ignore[arg-type]  # deliberately invalid input


@pytest.mark.parametrize("use_cache", [True, False])
def test_build_container_wires_services(tmp_path: Path, use_cache: bool) -> None:
    settings = Settings(cache_dir=tmp_path / "c", output_dir=tmp_path / "o", use_cache=use_cache)

    with build_container(settings) as container:
        assert container.settings is settings
        assert container.exports.formats == ["markdown"]
