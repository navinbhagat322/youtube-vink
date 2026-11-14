"""The ``vink`` command-line application."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, NoReturn

import typer
from pydantic import ValidationError

from vink import __version__
from vink.bootstrap import Container, build_container
from vink.config import Settings
from vink.domain.errors import InvalidInputError, VinkError
from vink.domain.video_ref import parse_video_ref
from vink.interfaces.logging_setup import configure_logging

EXIT_ERROR = 1
EXIT_USAGE = 2

app = typer.Typer(
    name="vink",
    help="Turn YouTube transcripts into clean, timestamped Markdown.",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
)


@dataclass(slots=True)
class CliState:
    """Per-invocation state shared between the root callback and commands.

    Attributes:
        container_factory: Builds the service container; replaced in tests.
        verbose: Whether ``--verbose`` was given.
    """

    container_factory: Callable[[Settings], Container] = build_container
    verbose: bool = False


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"vink {__version__}")
        raise typer.Exit


@app.callback()
def root(
    ctx: typer.Context,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show progress and debug logs on stderr.")
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
) -> None:
    """Turn YouTube transcripts into clean, timestamped Markdown."""
    state = ctx.obj if isinstance(ctx.obj, CliState) else CliState()
    state.verbose = verbose
    ctx.obj = state


@app.command("transcript")
def transcript_command(
    ctx: typer.Context,
    url: Annotated[str, typer.Argument(help="YouTube video URL or 11-character video ID.")],
    lang: Annotated[
        str | None,
        typer.Option(
            "--lang",
            "-l",
            help="Preferred languages, comma-separated, e.g. 'en,hi'. "
            "Use 'original' for the language spoken in the video.",
        ),
    ] = None,
    output_dir: Annotated[
        Path | None, typer.Option("--output-dir", "-o", help="Directory to save into.")
    ] = None,
    fmt: Annotated[str | None, typer.Option("--format", "-f", help="Output format.")] = None,
    stdout: Annotated[
        bool, typer.Option("--stdout", help="Print to stdout instead of saving a file.")
    ] = False,
    translate: Annotated[
        bool | None,
        typer.Option(
            "--translate/--no-translate",
            help="Allow YouTube machine translation when no track matches.",
        ),
    ] = None,
    cache: Annotated[
        bool | None, typer.Option("--cache/--no-cache", help="Use the local transcript cache.")
    ] = None,
) -> None:
    """Fetch a video's transcript and save it as a Markdown file."""
    overrides = {
        "languages": lang,
        "output_dir": output_dir,
        "output_format": fmt,
        "allow_translation": translate,
        "use_cache": cache,
    }
    with _session(ctx, overrides) as container:
        settings = container.settings
        transcript = container.transcripts.get_transcript(
            parse_video_ref(url),
            settings.languages,
            allow_translation=settings.allow_translation,
        )
        if stdout:
            typer.echo(container.exports.render(transcript, settings.output_format), nl=False)
        else:
            typer.echo(container.exports.save_transcript(transcript, settings.output_format))


@app.command("languages")
def languages_command(
    ctx: typer.Context,
    url: Annotated[str, typer.Argument(help="YouTube video URL or 11-character video ID.")],
    cache: Annotated[
        bool | None, typer.Option("--cache/--no-cache", help="Use the local transcript cache.")
    ] = None,
) -> None:
    """List the transcript languages available for a video."""
    with _session(ctx, {"use_cache": cache}) as container:
        tracks = container.transcripts.list_tracks(parse_video_ref(url))

    rows = [("CODE", "TYPE", "LANGUAGE")]
    rows += [(t.language_code, t.kind.value, t.language_name) for t in tracks]
    widths = [max(len(row[i]) for row in rows) for i in range(2)]
    for code, kind, name in rows:
        typer.echo(f"{code:<{widths[0]}}  {kind:<{widths[1]}}  {name}")


@app.command("mcp")
def mcp_command(ctx: typer.Context) -> None:
    """Run the MCP server over stdio (for Claude Desktop and other MCP clients)."""
    from vink.interfaces.mcp.server import create_server  # noqa: PLC0415 - heavy, CLI-optional

    with _session(ctx, {}) as container:
        create_server(container).run("stdio")


@contextmanager
def _session(ctx: typer.Context, overrides: dict[str, Any]) -> Iterator[Container]:
    """Build settings and a container, and turn vink errors into clean CLI exits."""
    state = ctx.obj if isinstance(ctx.obj, CliState) else CliState()
    try:
        settings = Settings(**{k: v for k, v in overrides.items() if v is not None})
    except ValidationError as exc:
        _fail(_describe_validation_error(exc), EXIT_USAGE)

    configure_logging("INFO" if state.verbose else settings.log_level)
    try:
        with state.container_factory(settings) as container:
            yield container
    except InvalidInputError as exc:
        _fail(str(exc), EXIT_USAGE)
    except VinkError as exc:
        _fail(str(exc), EXIT_ERROR)


def _describe_validation_error(exc: ValidationError) -> str:
    """Summarize pydantic validation errors as one line per invalid setting."""
    return "\n".join(
        f"Invalid value for {'.'.join(str(p) for p in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )


def _fail(message: str, code: int) -> NoReturn:
    """Print ``message`` to stderr and exit with ``code``."""
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(code)


def main() -> None:
    """Console-script entry point."""
    app()
