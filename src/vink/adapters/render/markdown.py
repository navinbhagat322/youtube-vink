"""Markdown rendering of transcripts.

Output starts with YAML front matter so the files drop straight into
Markdown-based notes apps such as Obsidian, followed by a readable header and
one paragraph per block, each prefixed with a clickable timestamp.
"""

import json
import re
from typing import Final

from vink.domain.models import Chunk, Paragraph, TrackKind, Transcript
from vink.processing.timecode import format_timecode

_MARKDOWN_SPECIAL: Final = re.compile(r"([\\`*_\[\]<>])")
"""Characters that change meaning inline. Lines never start with user text, so
block-level markers such as ``#`` or ``-`` need no escaping."""

_KIND_LABELS: Final = {
    TrackKind.MANUAL: "creator captions",
    TrackKind.GENERATED: "auto-generated captions",
    TrackKind.TRANSLATED: "machine-translated captions",
}


class MarkdownRenderer:
    """:class:`~vink.ports.Renderer` producing CommonMark with YAML front matter."""

    @property
    def format_name(self) -> str:
        """Identifier used to select this renderer."""
        return "markdown"

    @property
    def file_extension(self) -> str:
        """File extension for Markdown output."""
        return "md"

    def render_transcript(self, transcript: Transcript) -> str:
        """Render the complete transcript with front matter and a header."""
        sections = [
            _front_matter(transcript),
            f"# {_escape(transcript.metadata.title)}",
            _summary_line(transcript),
            "## Transcript",
            *(_paragraph(transcript, p) for p in transcript.paragraphs),
        ]
        return "\n\n".join(sections) + "\n"

    def render_chunk(self, transcript: Transcript, chunk: Chunk) -> str:
        """Render one chunk with a heading that states its position and time range."""
        heading = (
            f"## Part {chunk.index} of {chunk.total} "
            f"({format_timecode(chunk.start)}\u2013{format_timecode(chunk.end)})"  # en dash
        )
        sections = [
            f"# {_escape(transcript.metadata.title)}",
            heading,
            *(_paragraph(transcript, p) for p in chunk.paragraphs),
        ]
        return "\n\n".join(sections) + "\n"


def _front_matter(transcript: Transcript) -> str:
    """Build YAML front matter. Strings are JSON-encoded, which is valid YAML."""
    fields: dict[str, str | None] = {
        "title": transcript.metadata.title,
        "channel": transcript.metadata.channel,
        "url": transcript.video.url,
        "video_id": transcript.video.video_id,
        "language": transcript.language_code,
        "captions": transcript.kind.value,
        "duration": format_timecode(transcript.duration),
    }
    lines = [
        f"{key}: {json.dumps(value, ensure_ascii=False)}"
        for key, value in fields.items()
        if value is not None
    ]
    return "---\n" + "\n".join(lines) + "\n---"


def _summary_line(transcript: Transcript) -> str:
    """Build the one-line header under the title."""
    metadata = transcript.metadata
    parts: list[str] = []
    if metadata.channel:
        channel = _escape(metadata.channel)
        parts.append(
            f"**Channel:** [{channel}]({metadata.channel_url})"
            if metadata.channel_url
            else f"**Channel:** {channel}"
        )
    parts.append(f"**Duration:** {format_timecode(transcript.duration)}")
    parts.append(
        f"**Language:** {_escape(transcript.language_name)} ({_KIND_LABELS[transcript.kind]})"
    )
    parts.append(f"**Source:** <{transcript.video.url}>")
    return " · ".join(parts)


def _paragraph(transcript: Transcript, paragraph: Paragraph) -> str:
    """Render one paragraph with a bold, clickable timestamp."""
    stamp = format_timecode(paragraph.start)
    link = transcript.video.url_at(paragraph.start)
    return f"**[{stamp}]({link})** {_escape(paragraph.text)}"


def _escape(text: str) -> str:
    """Backslash-escape characters that would otherwise be read as Markdown syntax."""
    return _MARKDOWN_SPECIAL.sub(r"\\\1", text)
