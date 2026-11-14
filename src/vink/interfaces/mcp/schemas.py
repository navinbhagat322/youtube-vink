"""Structured tool results returned by the MCP server."""

from pydantic import BaseModel, Field


class TrackOut(BaseModel):
    """A caption track available for a video."""

    language_code: str = Field(description="Language code, e.g. 'en' or 'hi'.")
    language_name: str = Field(description="Human-readable language name.")
    kind: str = Field(description="'manual' (creator captions) or 'generated' (automatic).")


class VideoInfo(BaseModel):
    """What a client needs to know before reading a transcript chunk by chunk."""

    video_id: str
    url: str
    title: str
    channel: str | None
    language_code: str = Field(description="Language of the selected transcript.")
    language_name: str
    caption_kind: str = Field(description="'manual', 'generated' or 'translated'.")
    duration: str = Field(description="Length of the spoken content, H:MM:SS or M:SS.")
    paragraph_count: int
    chunk_count: int = Field(description="Number of parts; read each with get_chunk.")
    chunk_minutes: float = Field(description="Approximate length of each part in minutes.")
