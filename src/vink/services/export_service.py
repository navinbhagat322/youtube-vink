"""Use cases for rendering transcripts and delivering output."""

from collections.abc import Iterable

from vink.domain.errors import InvalidInputError
from vink.domain.models import Chunk, Transcript
from vink.ports.renderer import Renderer
from vink.ports.sink import Sink
from vink.processing.filenames import safe_filename


class ExportService:
    """Renders transcripts into a chosen format and hands them to a sink.

    Args:
        renderers: Every available renderer; each is selected by its ``format_name``.
        sink: Where saved output is delivered.
    """

    def __init__(self, renderers: Iterable[Renderer], sink: Sink) -> None:
        self._renderers = {renderer.format_name: renderer for renderer in renderers}
        self._sink = sink

    @property
    def formats(self) -> list[str]:
        """Names of all available output formats."""
        return sorted(self._renderers)

    def render(self, transcript: Transcript, fmt: str) -> str:
        """Render the full transcript in format ``fmt``."""
        return self._renderer(fmt).render_transcript(transcript)

    def render_chunk(self, transcript: Transcript, chunk: Chunk, fmt: str) -> str:
        """Render one chunk of ``transcript`` in format ``fmt``."""
        return self._renderer(fmt).render_chunk(transcript, chunk)

    def save_transcript(self, transcript: Transcript, fmt: str) -> str:
        """Render the transcript and save it, named after the video title.

        Returns:
            Where the output was saved.
        """
        renderer = self._renderer(fmt)
        name = f"{safe_filename(transcript.metadata.title)}.{renderer.file_extension}"
        return self._sink.write(name, renderer.render_transcript(transcript))

    def save_text(self, title: str, content: str, *, suffix: str, extension: str) -> str:
        """Save already-rendered content, such as notes written by an AI client.

        Args:
            title: Base name, typically the video title; it is sanitized.
            content: The content to save, unchanged.
            suffix: Appended to the title, e.g. ``"notes"`` gives ``"<title> - notes"``.
            extension: File extension without the dot.

        Returns:
            Where the output was saved.
        """
        stem = safe_filename(f"{title} - {suffix}" if suffix else title)
        return self._sink.write(f"{stem}.{safe_filename(extension)}", content)

    def _renderer(self, fmt: str) -> Renderer:
        try:
            return self._renderers[fmt]
        except KeyError:
            available = ", ".join(self.formats)
            raise InvalidInputError(
                f"Unknown output format {fmt!r}. Available: {available}."
            ) from None
