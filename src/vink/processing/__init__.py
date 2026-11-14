"""Processing layer: pure, deterministic transformations.

Functions here take domain models and return domain models. They perform no
I/O, which makes them trivial to test and safe to reuse from any interface.
"""

from vink.processing.chunking import chunk_paragraphs
from vink.processing.cleaning import clean_caption_text
from vink.processing.filenames import safe_filename
from vink.processing.paragraphs import ParagraphOptions, build_paragraphs
from vink.processing.timecode import format_timecode
from vink.processing.track_selection import ORIGINAL_LANGUAGE, select_track

__all__ = [
    "ORIGINAL_LANGUAGE",
    "ParagraphOptions",
    "build_paragraphs",
    "chunk_paragraphs",
    "clean_caption_text",
    "format_timecode",
    "safe_filename",
    "select_track",
]
