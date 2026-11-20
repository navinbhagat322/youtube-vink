from pathlib import Path

import pytest
from pydantic import ValidationError

from vink.bootstrap import build_container, proxy_options
from vink.config import Settings, default_mcp_output_dir
from vink.domain.errors import InvalidInputError


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


class TestWithDefaults:
    def test_applies_to_unset_fields(self, tmp_path: Path) -> None:
        settings = Settings().with_defaults(output_dir=tmp_path)

        assert settings.output_dir == tmp_path

    def test_keeps_values_from_environment(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("VINK_OUTPUT_DIR", str(tmp_path / "mine"))

        settings = Settings().with_defaults(output_dir=tmp_path / "default")

        assert settings.output_dir == tmp_path / "mine"

    def test_default_mcp_output_dir_is_absolute(self) -> None:
        path = default_mcp_output_dir()

        assert path.is_absolute()
        assert path.name == "vink"


class TestProxySettings:
    @pytest.mark.parametrize(
        ("url", "problem"),
        [
            ("http://PROXY_USERNAME:PROXY_PASSWORD@PROXY_HOST:PROXY_PORT", "invalid port"),
            ("socks5://proxy.example:1080", "http:// or https://"),
            ("http://user:pass@proxy.example", "needs a port"),
            ("http://:8080", "no host"),
        ],
    )
    def test_rejects_malformed_proxy_urls(self, url: str, problem: str) -> None:
        with pytest.raises(ValidationError, match=problem):
            Settings(proxy_url=url)  # type: ignore[arg-type]  # pydantic coerces str

    def test_accepts_valid_proxy_and_hides_it(self) -> None:
        settings = Settings(proxy_url="http://user:pass@proxy.example:8080")  # type: ignore[arg-type]

        assert settings.proxy_url is not None
        assert settings.proxy_url.get_secret_value() == "http://user:pass@proxy.example:8080"
        assert "user:pass@" not in repr(settings)

    def test_webshare_requires_both_credentials(self) -> None:
        with pytest.raises(ValidationError, match="set both"):
            Settings(webshare_username="alice")

    def test_webshare_and_proxy_url_are_exclusive(self) -> None:
        with pytest.raises(ValidationError, match="not both"):
            Settings.model_validate(
                {
                    "proxy_url": "http://proxy.example:8080",
                    "webshare_username": "alice",
                    "webshare_password": "s3cret",
                }
            )


class TestHttpSettings:
    def test_defaults(self) -> None:
        settings = Settings()

        assert (settings.mcp_transport, settings.mcp_host, settings.mcp_port) == (
            "stdio",
            "127.0.0.1",
            8000,
        )
        assert settings.auth_token is None
        assert settings.allowed_hosts == ()

    def test_reads_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("VINK_MCP_TRANSPORT", "http")
        monkeypatch.setenv("VINK_AUTH_TOKEN", "x" * 32)
        monkeypatch.setenv("VINK_ALLOWED_HOSTS", "vink.example.com, other.example.com")

        settings = Settings()

        assert settings.mcp_transport == "http"
        assert settings.auth_token is not None
        assert settings.allowed_hosts == ("vink.example.com", "other.example.com")

    @pytest.mark.parametrize(
        "overrides", [{"auth_token": "short"}, {"mcp_port": 0}, {"mcp_transport": "sse"}]
    )
    def test_rejects_invalid_values(self, overrides: dict[str, object]) -> None:
        with pytest.raises(ValidationError):
            Settings.model_validate(overrides)


class TestBootstrapProxy:
    def test_explicit_proxy_ignores_environment(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("HTTPS_PROXY", "http://broken:PORT")
        settings = Settings.model_validate(
            {"proxy_url": "http://proxy.example:8080", "cache_dir": tmp_path}
        )

        with build_container(settings) as container:
            assert container.settings.proxy_url is not None

    def test_malformed_environment_proxy_is_reported_clearly(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("HTTPS_PROXY", "http://user:secret@PROXY_HOST:PROXY_PORT")

        with pytest.raises(InvalidInputError, match="HTTPS_PROXY") as info:
            build_container(Settings(cache_dir=tmp_path))

        assert "secret" not in str(info.value)

    def test_webshare_options_are_passed_to_adapters(self) -> None:
        settings = Settings.model_validate(
            {"webshare_username": "alice", "webshare_password": "s3cret"}
        )

        options = proxy_options(settings)

        assert options.webshare_username == "alice"
        assert options.webshare_password == "s3cret"
        assert options.enabled


class TestEmptyEnvironmentValues:
    @pytest.mark.parametrize(
        "name",
        [
            "VINK_PROXY_URL",
            "VINK_WEBSHARE_USERNAME",
            "VINK_WEBSHARE_PASSWORD",
            "VINK_LANGUAGES",
            "VINK_OUTPUT_DIR",
            "VINK_AUTH_TOKEN",
        ],
    )
    def test_empty_value_means_not_set(self, monkeypatch: pytest.MonkeyPatch, name: str) -> None:
        monkeypatch.setenv(name, "")

        settings = Settings()

        assert settings == Settings.model_validate({})
        assert name.removeprefix("VINK_").lower() not in settings.model_fields_set
