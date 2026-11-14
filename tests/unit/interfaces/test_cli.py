from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.fakes import FakeTranscriptSource
from vink import __version__
from vink.bootstrap import Container
from vink.config import Settings, default_mcp_output_dir
from vink.domain.errors import TranscriptsDisabledError
from vink.interfaces.cli.app import EXIT_ERROR, EXIT_USAGE, CliState, app

VIDEO_URL = "https://youtu.be/dQw4w9WgXcQ"

ContainerFactory = Callable[[Settings], Container]


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def captured_settings() -> list[Settings]:
    return []


@pytest.fixture
def state(make_container: ContainerFactory, captured_settings: list[Settings]) -> CliState:
    def factory(settings: Settings) -> Container:
        captured_settings.append(settings)
        return make_container(settings)

    return CliState(container_factory=factory)


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == f"vink {__version__}"


def test_transcript_saves_file_and_prints_location(
    runner: CliRunner, state: CliState, tmp_path: Path
) -> None:
    result = runner.invoke(app, ["transcript", VIDEO_URL, "-o", str(tmp_path)], obj=state)

    assert result.exit_code == 0, result.output
    assert result.output.strip() == "memory://Sample Lecture.md"


def test_transcript_stdout_prints_markdown(runner: CliRunner, state: CliState) -> None:
    result = runner.invoke(app, ["transcript", VIDEO_URL, "--stdout"], obj=state)

    assert result.exit_code == 0, result.output
    assert result.output.startswith('---\ntitle: "Sample Lecture"')
    assert "Welcome to the lecture." in result.output


def test_transcript_passes_options_to_settings(
    runner: CliRunner, state: CliState, captured_settings: list[Settings], tmp_path: Path
) -> None:
    args = ["transcript", VIDEO_URL, "--lang", "hi, en", "--no-translate", "--no-cache"]
    args += ["-o", str(tmp_path), "--stdout"]

    result = runner.invoke(app, args, obj=state)

    assert result.exit_code == 0, result.output
    settings = captured_settings[0]
    assert settings.languages == ("hi", "en")
    assert settings.allow_translation is False
    assert settings.use_cache is False
    assert settings.output_dir == tmp_path


def test_invalid_url_exits_with_usage_error(runner: CliRunner, state: CliState) -> None:
    result = runner.invoke(app, ["transcript", "not a video"], obj=state)

    assert result.exit_code == EXIT_USAGE
    assert "Could not find a YouTube video ID" in result.output


def test_invalid_setting_exits_with_usage_error(runner: CliRunner, state: CliState) -> None:
    result = runner.invoke(app, ["transcript", VIDEO_URL, "--lang", " , "], obj=state)

    assert result.exit_code == EXIT_USAGE
    assert "Invalid VINK_LANGUAGES" in result.output


def test_unknown_format_exits_with_usage_error(runner: CliRunner, state: CliState) -> None:
    result = runner.invoke(app, ["transcript", VIDEO_URL, "-f", "pdf"], obj=state)

    assert result.exit_code == EXIT_USAGE
    assert "Unknown output format" in result.output


def test_domain_error_exits_with_error_code(
    runner: CliRunner, state: CliState, source: FakeTranscriptSource
) -> None:
    source.error = TranscriptsDisabledError("dQw4w9WgXcQ")

    result = runner.invoke(app, ["transcript", VIDEO_URL], obj=state)

    assert result.exit_code == EXIT_ERROR
    assert "has no transcripts" in result.output


def test_languages_lists_tracks(runner: CliRunner, state: CliState) -> None:
    result = runner.invoke(app, ["languages", VIDEO_URL], obj=state)

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0].split() == ["CODE", "TYPE", "LANGUAGE"]
    assert lines[1].split() == ["en", "manual", "English"]
    assert lines[2].split()[:2] == ["hi", "generated"]


class _ServerStub:
    started: tuple[Settings, str]

    def __init__(self, container: Container) -> None:
        self.container = container

    def run(self, transport: str) -> None:
        _ServerStub.started = (self.container.settings, transport)


def test_mcp_defaults_to_absolute_output_dir(
    runner: CliRunner, state: CliState, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("VINK_OUTPUT_DIR", raising=False)
    monkeypatch.setattr("vink.interfaces.mcp.server.create_server", _ServerStub)

    result = runner.invoke(app, ["mcp"], obj=state)

    assert result.exit_code == 0, result.output
    settings, transport = _ServerStub.started
    assert settings.output_dir == default_mcp_output_dir()
    assert transport == "stdio"


def test_mcp_respects_configured_output_dir(
    runner: CliRunner, state: CliState, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("VINK_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr("vink.interfaces.mcp.server.create_server", _ServerStub)

    runner.invoke(app, ["mcp"], obj=state)

    assert _ServerStub.started[0].output_dir == tmp_path


class TestMcpHttpCommand:
    @pytest.fixture
    def served(self, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
        calls: dict[str, object] = {}

        def fake_serve(app: object, *, host: str, port: int, log_level: str) -> None:
            calls.update(app=app, host=host, port=port, log_level=log_level)

        monkeypatch.setattr("vink.interfaces.mcp.http.serve_http", fake_serve)
        for name in ("VINK_AUTH_TOKEN", "VINK_MCP_TRANSPORT", "VINK_MCP_HOST", "VINK_MCP_PORT"):
            monkeypatch.delenv(name, raising=False)
        return calls

    def test_serves_http_with_token(
        self,
        runner: CliRunner,
        state: CliState,
        monkeypatch: pytest.MonkeyPatch,
        served: dict[str, object],
    ) -> None:
        monkeypatch.setenv("VINK_AUTH_TOKEN", "t" * 32)

        result = runner.invoke(
            app, ["mcp", "-t", "http", "--host", "0.0.0.0", "-p", "9000"], obj=state
        )

        assert result.exit_code == 0, result.output
        assert (served["host"], served["port"]) == ("0.0.0.0", 9000)
        assert "bearer token required" in result.output

    def test_refuses_http_without_token(
        self, runner: CliRunner, state: CliState, served: dict[str, object]
    ) -> None:
        result = runner.invoke(app, ["mcp", "--transport", "http"], obj=state)

        assert result.exit_code == EXIT_USAGE
        assert "requires an access token" in result.output
        assert not served

    def test_insecure_local_mode(
        self, runner: CliRunner, state: CliState, served: dict[str, object]
    ) -> None:
        result = runner.invoke(app, ["mcp", "-t", "http", "--insecure-no-auth"], obj=state)

        assert result.exit_code == 0, result.output
        assert served["host"] == "127.0.0.1"
        assert "NO AUTHENTICATION" in result.output

    def test_rejects_unknown_transport(self, runner: CliRunner, state: CliState) -> None:
        result = runner.invoke(app, ["mcp", "-t", "carrier-pigeon"], obj=state)

        assert result.exit_code == EXIT_USAGE
        assert "Invalid VINK_MCP_TRANSPORT" in result.output
