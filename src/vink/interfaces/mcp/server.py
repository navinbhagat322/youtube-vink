"""MCP server: tools for reading transcripts and prompts for turning them into notes.

The server does not call any AI model itself. The MCP client (for example
Claude Desktop) reads the transcript chunk by chunk through these tools and
writes the notes, guided by the bundled style prompts.
"""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.shared.exceptions import MCPError
from mcp.types import INVALID_PARAMS

from vink import __version__
from vink.bootstrap import Container
from vink.domain.errors import VinkError
from vink.domain.models import Transcript
from vink.domain.video_ref import parse_video_ref
from vink.interfaces.mcp.schemas import TrackOut, VideoInfo
from vink.processing.timecode import format_timecode
from vink.styles import DEFAULT_STYLE, available_styles, load_style

_INSTRUCTIONS = """\
vink fetches YouTube transcripts (no API key needed) and serves them as clean,
timestamped Markdown. For long videos, call get_video_info first, then read the
transcript one part at a time with get_chunk. Use the make_notes prompt to turn a
video into complete, detailed notes rather than a summary.
"""

_SAME_LANGUAGE = "the same language as the transcript"


def create_server(container: Container) -> MCPServer:
    """Build an MCP server whose tools are backed by ``container``'s services.

    Args:
        container: Wired services and settings.

    Returns:
        A configured server; call ``run("stdio")`` to serve it.
    """
    server: MCPServer = MCPServer(
        name="vink",
        instructions=_INSTRUCTIONS,
        version=__version__,
    )
    settings = container.settings
    transcripts = container.transcripts
    exports = container.exports

    def load(url: str, languages: Sequence[str] | None) -> Transcript:
        return transcripts.get_transcript(
            parse_video_ref(url),
            languages or settings.languages,
            allow_translation=settings.allow_translation,
        )

    @server.tool()
    def list_languages(url: str) -> list[TrackOut]:
        """List the caption languages available for a YouTube video."""
        with _as_tool_error():
            tracks = transcripts.list_tracks(parse_video_ref(url))
        return [
            TrackOut(language_code=t.language_code, language_name=t.language_name, kind=t.kind)
            for t in tracks
        ]

    @server.tool()
    def get_video_info(url: str, languages: list[str] | None = None) -> VideoInfo:
        """Get title, language and the number of transcript parts for a YouTube video.

        Args:
            url: YouTube video URL or ID.
            languages: Preferred language codes, most preferred first, e.g. ["en", "hi"].
                Use "original" for the language spoken in the video. Defaults to
                the server's configured languages.
        """
        with _as_tool_error():
            transcript = load(url, languages)
            chunks = transcripts.chunk(transcript, settings.chunk_seconds)
        return VideoInfo(
            video_id=transcript.video.video_id,
            url=transcript.video.url,
            title=transcript.metadata.title,
            channel=transcript.metadata.channel,
            language_code=transcript.language_code,
            language_name=transcript.language_name,
            caption_kind=transcript.kind,
            duration=format_timecode(transcript.duration),
            paragraph_count=len(transcript.paragraphs),
            chunk_count=len(chunks),
            chunk_minutes=settings.chunk_seconds / 60,
        )

    @server.tool()
    def get_chunk(url: str, part: int, languages: list[str] | None = None) -> str:
        """Get one part of a video's transcript as timestamped Markdown.

        Args:
            url: YouTube video URL or ID.
            part: 1-based part number; get_video_info reports how many parts exist.
            languages: Preferred language codes, as for get_video_info.
        """
        with _as_tool_error():
            transcript = load(url, languages)
            chunks = transcripts.chunk(transcript, settings.chunk_seconds)
            if not 1 <= part <= len(chunks):
                raise ToolError(f"Part must be between 1 and {len(chunks)}, got {part}.")
            return exports.render_chunk(transcript, chunks[part - 1], settings.output_format)

    @server.tool()
    def get_transcript(url: str, languages: list[str] | None = None) -> str:
        """Get a video's complete transcript as timestamped Markdown.

        Prefer get_chunk for videos longer than about 20 minutes.

        Args:
            url: YouTube video URL or ID.
            languages: Preferred language codes, as for get_video_info.
        """
        with _as_tool_error():
            return exports.render(load(url, languages), settings.output_format)

    @server.tool()
    def save_transcript(url: str, languages: list[str] | None = None) -> str:
        """Save a video's transcript as a Markdown file and return its path.

        Args:
            url: YouTube video URL or ID.
            languages: Preferred language codes, as for get_video_info.
        """
        with _as_tool_error():
            return exports.save_transcript(load(url, languages), settings.output_format)

    @server.tool()
    def save_notes(url: str, content: str, suffix: str = "notes") -> str:
        """Save notes you have written for a video as a Markdown file and return its path.

        The file is named after the video title, e.g. "<title> - notes.md".

        Args:
            url: YouTube video URL or ID the notes are about.
            content: The complete notes in Markdown.
            suffix: Label appended to the file name, e.g. "notes" or "clean".
        """
        with _as_tool_error():
            metadata = transcripts.get_metadata(parse_video_ref(url))
            return exports.save_text(metadata.title, content, suffix=suffix, extension="md")

    styles_text = ", ".join(available_styles())

    @server.prompt(
        name="make_notes",
        description=f"Turn a YouTube video into complete notes. Styles: {styles_text}.",
    )
    def make_notes(
        url: str,
        style: str = DEFAULT_STYLE,
        output_language: str = _SAME_LANGUAGE,
    ) -> str:
        """Instructions for writing notes from a video, one transcript part at a time."""
        try:
            instructions = load_style(style, output_language=output_language or _SAME_LANGUAGE)
        except VinkError as exc:
            # MCPError is the only exception type whose message reaches the client.
            raise MCPError(INVALID_PARAMS, str(exc)) from exc
        return f"{instructions}\nVideo: {url}\n"

    return server


@contextmanager
def _as_tool_error() -> Iterator[None]:
    """Report vink errors to the client as tool errors with a readable message."""
    try:
        yield
    except VinkError as exc:
        raise ToolError(str(exc)) from exc
