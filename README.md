<p align="center">
  <img src="https://raw.githubusercontent.com/navinbhagat322/youtube-vink/main/docs/assets/logo.png" alt="vink logo" width="112" height="112">
</p>

<h1 align="center">vink</h1>

<p align="center">
  Turn YouTube transcripts into clean, timestamped Markdown and into complete,
  detailed notes instead of short summaries.
</p>

<p align="center">
  <a href="https://github.com/navinbhagat322/youtube-vink/actions/workflows/ci.yml"><img src="https://github.com/navinbhagat322/youtube-vink/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/vink/"><img src="https://img.shields.io/pypi/v/vink" alt="PyPI version"></a>
  <a href="https://pypi.org/project/vink/"><img src="https://img.shields.io/pypi/pyversions/vink" alt="Python versions"></a>
  <a href="https://github.com/navinbhagat322/youtube-vink/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/vink" alt="License"></a>
</p>

## Why

Most "YouTube to notes" tools summarize. They squeeze an hour of teaching into a
page and drop the examples, steps and asides that made the video useful. vink
works the other way around. It extracts the full transcript YouTube already
has, cleans it into readable paragraphs with timestamps, and serves it in parts
so an AI client can write notes for each part without leaving anything out.

## Features

- **No API key.** Reads the same captions YouTube's player shows in its
  *Show transcript* panel.
- **Any language.** Choose preferred languages in order (`en,hi`). Manual
  captions are preferred over auto-generated ones, with YouTube translation as
  a fallback. Use `original` for the language spoken in the video.
- **Readable output.** Merges caption fragments into paragraphs, removes
  `[Music]`-style noise, and puts a clickable timestamp on every paragraph.
- **Notes-app friendly.** Markdown with YAML front matter, ready for Obsidian
  and similar apps.
- **MCP server.** Lets Claude Desktop (or any MCP client) read long videos
  chunk by chunk and write full notes, with bundled note-style prompts.
- **Local cache.** Each transcript is fetched once; the list of available
  languages is refreshed daily.
- **Runs anywhere.** Serve MCP over HTTP with token authentication, or route
  requests through a residential proxy when YouTube blocks a cloud server.

## Installation

Requires Python 3.11+.

From PyPI, as a standalone command:

```bash
uv tool install vink      # or: pipx install vink
vink --version
```

From source (for development), with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/navinbhagat322/youtube-vink.git
cd youtube-vink
uv sync
```

From a source checkout, prefix the commands below with `uv run`.

## Quickstart

```bash
vink transcript https://youtu.be/aircAruvnKk
```

```text
/your/current/folder/output/But what is a neural network Deep learning chapter 1.md
```

The file looks like this:

```markdown
---
title: "But what is a neural network? | Deep learning chapter 1"
channel: "3Blue1Brown"
url: "https://www.youtube.com/watch?v=aircAruvnKk"
video_id: "aircAruvnKk"
language: "en"
captions: "manual"
duration: "18:25"
---

# But what is a neural network? | Deep learning chapter 1

**Channel:** [3Blue1Brown](https://www.youtube.com/@3blue1brown) · **Duration:** 18:25 · ...

## Transcript

**[0:04](https://youtu.be/aircAruvnKk?t=4)** This is a 3. It's sloppily written and rendered ...
```

## Usage: CLI

```text
vink transcript URL [--lang en,hi] [--output-dir DIR] [--stdout]
                    [--translate | --no-translate] [--cache | --no-cache]
vink languages URL
vink mcp [--transport stdio|http] [--host HOST] [--port PORT]
vink --version
```

| Command | What it does |
|---------|--------------|
| `transcript` | Fetches a transcript and saves it as Markdown (or prints it with `--stdout`). |
| `languages` | Lists the caption tracks a video has. |
| `mcp` | Runs the MCP server: over stdio for local clients (default), or over HTTP for remote ones. |

Examples:

```bash
# Hindi if available, otherwise English
vink transcript https://youtu.be/VIDEO_ID --lang hi,en

# The language spoken in the video, printed to the terminal
vink transcript VIDEO_ID --lang original --stdout

# See what is available first
vink languages https://youtu.be/VIDEO_ID
```

Add `-v` before the command for progress logs, e.g. `vink -v transcript ...`.

Exit codes: `0` success, `1` the transcript could not be fetched, `2` invalid
input or options.

## Usage: MCP (Claude Desktop)

Add vink to your Claude Desktop config. On macOS it is at
`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vink": {
      "command": "uvx",
      "args": ["vink", "mcp"],
      "env": { "VINK_LANGUAGES": "en" }
    }
  }
}
```

Notes are saved to `~/Documents/vink` unless you set `VINK_OUTPUT_DIR` in
`env`. If Claude Desktop cannot find `uvx`, use its absolute path (`which uvx`).
To run from a source checkout, see [docs/mcp.md](docs/mcp.md).

Restart Claude Desktop, then either:

- choose the **make_notes** prompt, enter a video URL, and optionally a style
  and output language (for example `Hinglish`), or
- just ask: *"Make detailed notes from https://youtu.be/VIDEO_ID and save them."*

| Tool | Purpose |
|------|---------|
| `list_languages` | Caption languages available for a video |
| `get_video_info` | Title, language, duration and number of parts |
| `get_chunk` | One part of the transcript as Markdown |
| `get_transcript` | The whole transcript (best for short videos) |
| `save_transcript` | Save the transcript as a Markdown file |
| `save_notes` | Save notes the client has written |

Bundled note styles: `detailed-notes` (default) and `clean-transcript`.
See [docs/mcp.md](docs/mcp.md) for details and setup for other clients.

## Running on a server

YouTube blocks most requests from cloud servers (AWS, GCP, hosted sandboxes).
vink supports two ways around it:

- **Host it at home and connect remotely.** Run vink over HTTP on a machine
  with a residential connection and publish it with a tunnel. No proxy needed.

  ```bash
  VINK_AUTH_TOKEN='a-long-random-secret' vink mcp --transport http --port 8000
  ```

- **Use a residential proxy** wherever vink runs:

  ```bash
  VINK_PROXY_URL=http://user:pass@proxy.example.com:8080 vink mcp
  ```

  Webshare rotating proxies are supported natively via
  `VINK_WEBSHARE_USERNAME` and `VINK_WEBSHARE_PASSWORD`.

Step-by-step instructions, including Cloudflare Tunnel and systemd, are in
[docs/hosting.md](docs/hosting.md).

## Configuration

Every setting has a sensible default and can be set with an environment
variable or a `.env` file. Common ones:

| Variable | Default | Meaning |
|----------|---------|---------|
| `VINK_LANGUAGES` | `en` | Preferred languages, comma-separated |
| `VINK_OUTPUT_DIR` | `output` (CLI), `~/Documents/vink` (MCP) | Where files are saved |
| `VINK_CHUNK_SECONDS` | `600` | Length of one part for `get_chunk` |
| `VINK_PROXY_URL` | none | Proxy for requests to YouTube |
| `VINK_AUTH_TOKEN` | none | Required token for `vink mcp --transport http` |

The full list is in [docs/configuration.md](docs/configuration.md).

## How it works

```
URL → caption track selection → fetch → clean → paragraphs → chunks → Markdown → file
```

vink uses a ports-and-adapters architecture. Fetching, rendering and saving
each sit behind a small interface, so new output formats (PDF, DOCX) and
destinations (Notion, Obsidian) can be added without touching the core. See
[docs/architecture.md](docs/architecture.md).

## Limitations

- Only videos that have captions (manual or auto-generated) are supported.
  Transcribing audio for videos without captions is planned.
- YouTube often blocks requests from cloud-server IP addresses. See
  [Running on a server](#running-on-a-server).
- vink uses YouTube's internal caption endpoints through
  [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api).
  These can change without notice. Keep dependencies up to date.
- Playlists are not supported yet.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup,
workflow and conventions.

## License

[MIT](LICENSE)
