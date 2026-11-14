"""Ports: the interfaces the core depends on.

Each port is a :class:`typing.Protocol`. Adapters in :mod:`vink.adapters`
implement them; :mod:`vink.bootstrap` decides which adapter backs which port.
Ports accept and return domain models and raise domain errors only.
"""

from vink.ports.cache import Cache
from vink.ports.metadata_source import MetadataSource
from vink.ports.renderer import Renderer
from vink.ports.sink import Sink
from vink.ports.transcript_source import TranscriptSource

__all__ = ["Cache", "MetadataSource", "Renderer", "Sink", "TranscriptSource"]
