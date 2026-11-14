# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- The MCP server now saves files to `~/Documents/vink` by default. Previously it
  used a relative `output` folder, which fails when an MCP client such as
  Claude Desktop starts the server from `/`.
- Newly added captions are now found: the cached list of available tracks
  expires after one day instead of never.

### Changed

- Video titles are cached for seven days, so reading a long video part by part
  no longer makes a network request for every part.
- Officially support Python 3.14.
- Each release now also creates a GitHub release with the built files.

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
- Distribution on PyPI (`uv tool install vink`, `uvx vink mcp`).

[Unreleased]: https://github.com/navinbhagat322/youtube-vink/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/navinbhagat322/youtube-vink/releases/tag/v0.1.0
