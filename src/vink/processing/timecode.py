"""Formatting seconds as human-readable timecodes."""


def format_timecode(seconds: float) -> str:
    """Format ``seconds`` as ``M:SS`` or ``H:MM:SS``.

    Fractions are truncated, and negative values are treated as zero.

    Examples:
        >>> format_timecode(65.9)
        '1:05'
        >>> format_timecode(3723)
        '1:02:03'
    """
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
