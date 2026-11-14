"""Port for delivering rendered output to a destination."""

from typing import Protocol


class Sink(Protocol):
    """Delivers rendered content somewhere: a folder, a notes app, a document store."""

    def write(self, name: str, content: str) -> str:
        """Store ``content`` under ``name`` and return where it ended up.

        Args:
            name: Destination-relative name, e.g. ``"My Video.md"``.
            content: The rendered content.

        Returns:
            A human-readable location such as a file path or URL.

        Raises:
            SinkError: If the content cannot be delivered.
        """
        ...
