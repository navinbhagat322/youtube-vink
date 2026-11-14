"""Port for turning transcripts into an output format."""

from typing import Protocol

from vink.domain.models import Chunk, Transcript


class Renderer(Protocol):
    """Renders transcripts into a text-based output format such as Markdown."""

    @property
    def format_name(self) -> str:
        """Short identifier used to select this renderer, e.g. ``"markdown"``."""
        ...

    @property
    def file_extension(self) -> str:
        """File extension for rendered output, without the dot, e.g. ``"md"``."""
        ...

    def render_transcript(self, transcript: Transcript) -> str:
        """Render the complete transcript, including a metadata header."""
        ...

    def render_chunk(self, transcript: Transcript, chunk: Chunk) -> str:
        """Render one chunk of ``transcript`` with a short context header."""
        ...
