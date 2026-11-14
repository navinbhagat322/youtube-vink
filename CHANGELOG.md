# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-14

### Added

- `vink transcript` command: fetch a YouTube transcript and save it as Markdown
  with YAML front matter and clickable timestamps, or print it with `--stdout`.
- `vink languages` command: list the caption tracks available for a video.
- Language preferences with fallback (`--lang hi,en`), the special value
  `original` for the spoken language, and optional YouTube machine translation.
- Cleaning of caption text into readable paragraphs: sound cues removed,
  fragments merged, speaker changes and pauses respected.
- Local transcript cache.
- MCP server (`vink mcp`) with tools `list_languages`, `get_video_info`,
  `get_chunk`, `get_transcript`, `save_transcript` and `save_notes`, and a
  `make_notes` prompt with `detailed-notes` and `clean-transcript` styles.
- Configuration through `VINK_*` environment variables or a `.env` file.

[Unreleased]: https://github.com/OWNER/vink/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/OWNER/vink/releases/tag/v0.1.0
