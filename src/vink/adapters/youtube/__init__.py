"""YouTube adapters: caption tracks via ``youtube-transcript-api``, metadata via oEmbed."""

from vink.adapters.youtube.oembed import OEmbedMetadataSource
from vink.adapters.youtube.proxy import ProxyOptions
from vink.adapters.youtube.transcript_source import YouTubeTranscriptSource

__all__ = ["OEmbedMetadataSource", "ProxyOptions", "YouTubeTranscriptSource"]
