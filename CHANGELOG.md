# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-11-14

### Added

- `vink mcp --transport http` serves the MCP server over Streamable HTTP, so
  vink can run on one machine (for example a home server YouTube does not
  block) and be used by MCP clients elsewhere. Includes `--host`, `--port` and
  a `/healthz` endpoint.
- Bearer-token authentication for the HTTP server via `VINK_AUTH_TOKEN`. The
  server refuses to start without a token unless `--insecure-no-auth` is given
  on a loopback address. `VINK_ALLOWED_HOSTS` optionally restricts the accepted
  hostnames.
- Proxy support for reaching YouTube from cloud servers: `VINK_PROXY_URL` for
  any HTTP(S) proxy, and `VINK_WEBSHARE_USERNAME` / `VINK_WEBSHARE_PASSWORD`
  for Webshare rotating residential proxies with automatic retries.
- `docs/hosting.md`: running vink on a server with Cloudflare Tunnel, systemd,
  or a residential proxy, plus troubleshooting.

### Fixed

- A malformed `HTTPS_PROXY` / `HTTP_PROXY` value no longer crashes vink at
  startup with a traceback (which MCP clients showed only as "Connection
  closed"); vink now explains which variable is wrong.

### Changed

- Configuration errors name the environment variable to fix (for example
  `Invalid VINK_PROXY_URL: ...`) and never echo values, which may be secrets.
- When YouTube blocks a request, the error now says whether a proxy was used
  and links to the hosting guide.

## [0.1.1] - 2026-11-14

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
- Added a project logo.

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

[Unreleased]: https://github.com/navinbhagat322/youtube-vink/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/navinbhagat322/youtube-vink/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/navinbhagat322/youtube-vink/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/navinbhagat322/youtube-vink/releases/tag/v0.1.0
