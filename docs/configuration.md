# Configuration

vink works with no configuration at all. Each setting can be changed in one of
these ways (highest priority first):

1. Command-line options, e.g. `--lang hi,en`.
2. Environment variables prefixed with `VINK_`.
3. A `.env` file in the current working directory (see `.env.example`).
4. Built-in defaults.

## Settings

| Setting | Environment variable | Default | CLI option | Description |
|---------|----------------------|---------|------------|-------------|
| Languages | `VINK_LANGUAGES` | `en` | `--lang`, `-l` | Preferred transcript languages, comma-separated, most preferred first. `original` means the language spoken in the video. |
| Allow translation | `VINK_ALLOW_TRANSLATION` | `true` | `--translate` / `--no-translate` | Use YouTube machine translation when no track matches any preferred language. |
| Output directory | `VINK_OUTPUT_DIR` | `output` (CLI), `~/Documents/vink` (MCP server)² | `--output-dir`, `-o` | Where saved files go. Relative paths are relative to the working directory. |
| Output format | `VINK_OUTPUT_FORMAT` | `markdown` | `--format`, `-f` | Format for saved and printed output. |
| Cache directory | `VINK_CACHE_DIR` | platform user cache dir¹ | — | Where fetched transcripts are cached. |
| Use cache | `VINK_USE_CACHE` | `true` | `--cache` / `--no-cache` | Read from and write to the transcript cache. |
| Chunk length | `VINK_CHUNK_SECONDS` | `600` | — | Target length in seconds of one part served by the MCP `get_chunk` tool. Minimum 60. |
| HTTP timeout | `VINK_HTTP_TIMEOUT` | `10` | — | Timeout in seconds for metadata requests. |
| Log level | `VINK_LOG_LEVEL` | `WARNING` | `-v` (sets `INFO`) | `DEBUG`, `INFO`, `WARNING` or `ERROR`. Logs go to stderr. |

¹ `~/Library/Caches/vink` on macOS, `~/.cache/vink` on Linux,
`%LOCALAPPDATA%\vink\Cache` on Windows.

² MCP clients usually start servers with `/` as the working directory, so the
MCP server uses an absolute folder in your Documents directory unless
`VINK_OUTPUT_DIR` is set.

## How a transcript track is chosen

Given `VINK_LANGUAGES=hi,en`:

1. A creator-uploaded Hindi track.
2. An auto-generated Hindi track.
3. A creator-uploaded English track.
4. An auto-generated English track.
5. If none exist and translation is allowed: a YouTube machine translation into
   Hindi (then English), preferring a creator-uploaded source track.

Codes match exactly first, then by base language, so `en` matches `en-GB` and
`pt-BR` falls back to `pt`.

If nothing matches, vink lists the available languages. You can also check
first with `vink languages URL`.

## What is cached, and for how long

| Data | Kept for | Why |
|------|----------|-----|
| Fetched caption text | Forever | A published caption track does not change. |
| List of available tracks | 1 day | Creators sometimes add captions after upload. |
| Title and channel | 7 days | These change rarely. |

## Clearing the cache

The cache only stores data fetched from YouTube. It is safe to delete at any time:

```bash
rm -rf ~/Library/Caches/vink   # macOS
rm -rf ~/.cache/vink           # Linux
```

Or bypass it for one run with `--no-cache`.
