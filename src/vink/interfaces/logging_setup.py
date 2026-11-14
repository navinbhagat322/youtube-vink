"""Logging configuration shared by all entry points.

Library modules never configure logging; only entry points call
:func:`configure_logging`. Logs always go to stderr so they never mix with
command output or the MCP stdio protocol stream.
"""

import logging
import sys

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def configure_logging(level: str) -> None:
    """Send log records at ``level`` and above to stderr."""
    logging.basicConfig(level=level, format=_FORMAT, stream=sys.stderr, force=True)
