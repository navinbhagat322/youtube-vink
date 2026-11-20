<p align="center">
  <img src="https://raw.githubusercontent.com/navinbhagat322/youtube-vink/main/docs/assets/logo.png" alt="vink logo" width="112" height="112">
</p>

<h1 align="center">vink</h1>

<p align="center">
  <strong>YouTube videos into complete, detailed notes, not summaries.</strong><br>
  Clean, timestamped transcripts for you, and an MCP server for your AI assistant.
</p>

<p align="center">
  <a href="https://github.com/navinbhagat322/youtube-vink/actions/workflows/ci.yml"><img src="https://github.com/navinbhagat322/youtube-vink/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/vink/"><img src="https://img.shields.io/pypi/v/vink?cacheSeconds=3600" alt="PyPI version"></a>
  <a href="https://pypi.org/project/vink/"><img src="https://img.shields.io/pypi/pyversions/vink?cacheSeconds=3600" alt="Python versions"></a>
  <a href="https://github.com/navinbhagat322/youtube-vink/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/vink?cacheSeconds=3600" alt="License"></a>
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> ·
  <a href="#use-it-with-your-ai-assistant">AI assistants</a> ·
  <a href="#running-on-a-server">Hosting</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="https://github.com/navinbhagat322/youtube-vink/tree/main/docs">Docs</a>
</p>

---

## Why vink?

Most "YouTube to notes" tools summarize. An hour of teaching becomes a page,
and the examples, steps and asides that made the video worth watching are
gone.

vink does the opposite. It takes the full transcript YouTube already has,
turns it into readable, timestamped text, and hands it to your AI assistant
**one part at a time**, so nothing is lost when notes are written.

| | Typical summarizer | vink |
|---|---|---|
| A 1-hour lecture becomes | A few bullet points | Complete notes, section by section |
| Examples and steps | Mostly dropped | Kept, in order |
| Jump back to the video | Rarely | Every paragraph links to its timestamp |
| Your notes app | Copy and paste | Markdown with front matter, ready for Obsidian |
| Setup | Account and API key | `uvx vink`. No key needed |

## Features

<table>
  <tr>
    <td width="50%" valign="top">
      <strong>No API key</strong><br>
      Reads the same captions YouTube shows in its <em>Show transcript</em> panel.
    </td>
    <td width="50%" valign="top">
      <strong>Any language</strong><br>
      Pick languages in order of preference (<code>hi,en</code>). Creator captions
      are preferred, with auto-generated captions and translation as fallbacks.
    </td>
  </tr>
  <tr>
    <td valign="top">
      <strong>Readable output</strong><br>
      Caption fragments become paragraphs, <code>[Music]</code>-style noise is
      removed, and every paragraph gets a clickable timestamp.
    </td>
    <td valign="top">
      <strong>Built for AI assistants</strong><br>
      An MCP server for Claude, Cursor and others, with note-writing prompts in
      any output language, including Hinglish.
    </td>
  </tr>
  <tr>
    <td valign="top">
      <strong>Fast repeat access</strong><br>
      Transcripts are cached locally, so each video is fetched only once.
    </td>
    <td valign="top">
      <strong>Runs anywhere</strong><br>
      Serve over HTTP with token authentication, or use a residential proxy when
      YouTube blocks a cloud server.
    </td>
  </tr>
</table>

## Quickstart

**1. Install** (Python 3.11+):

```bash
uv tool install vink        # or: pipx install vink
```

**2. Get a transcript:**

```bash
vink transcript https://youtu.be/aircAruvnKk
```

```text
/your/folder/output/But what is a neural network Deep learning chapter 1.md
```

**3. Open the file.** It looks like this:

```markdown
---
title: "But what is a neural network? | Deep learning chapter 1"
channel: "3Blue1Brown"
language: "en"
captions: "manual"
duration: "18:25"
---

# But what is a neural network? | Deep learning chapter 1

**Channel:** 3Blue1Brown · **Duration:** 18:25 · **Language:** English (creator captions)

## Transcript

**[0:04](https://youtu.be/aircAruvnKk?t=4)** This is a 3. It's sloppily written and rendered
at an extremely low resolution of 28x28 pixels, but your brain has no trouble ...

**[0:49](https://youtu.be/aircAruvnKk?t=49)** But if I told you, hey, sit down and write for me
a program that takes in a grid of 28x28 pixels ...
```

## Use it with your AI assistant

vink includes an [MCP](https://modelcontextprotocol.io) server. Your assistant
reads the transcript part by part and writes full notes, with no API key and
nothing extra to pay.

### Claude Desktop: one-click install

1. Download **`vink-<version>.mcpb`** from the
   [latest release](https://github.com/navinbhagat322/youtube-vink/releases/latest).
2. Double-click it, or drag it into Claude Desktop's **Settings → Extensions**.
3. Click **Install**. Optionally pick your languages and save folder in the
   form Claude shows.

Then ask:

> Make detailed notes from https://youtu.be/aircAruvnKk in Hinglish and save them.

Or choose **+ → Add from vink → make_notes**.

The extension runs vink with [uv](https://docs.astral.sh/uv/). If Claude
reports that `uv` is missing, install it first.

<details>
<summary><strong>Claude Desktop: manual setup</strong></summary>

Add this to `claude_desktop_config.json`
(macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`),
then restart Claude:

```json
{
  "mcpServers": {
    "vink": {
      "command": "uvx",
      "args": ["vink", "mcp"]
    }
  }
}
```

</details>

<details>
<summary><strong>Claude Code</strong></summary>

```bash
claude mcp add vink --scope user -- uvx vink mcp
```

</details>

<details>
<summary><strong>Cursor</strong></summary>

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "vink": { "command": "uvx", "args": ["vink", "mcp"] }
  }
}
```

</details>

<details>
<summary><strong>VS Code (GitHub Copilot)</strong></summary>

```bash
code --add-mcp '{"name":"vink","command":"uvx","args":["vink","mcp"]}'
```

</details>

<details>
<summary><strong>Any other MCP client</strong></summary>

Most clients accept the standard block:

```json
{
  "mcpServers": {
    "vink": { "command": "uvx", "args": ["vink", "mcp"] }
  }
}
```

If the client cannot find `uvx`, use its full path (run `which uvx`).

</details>

> **Tip for `uvx` setups:** run `uvx vink --version` once in a terminal before
> adding vink to a client. The first run downloads vink's dependencies, which
> can take longer than a client is willing to wait for a server to start.

### What your assistant can do

| Tool | What it does |
|------|--------------|
| `list_languages` | Lists the caption languages a video has |
| `get_video_info` | Title, language, duration and number of parts |
| `get_chunk` | One part of the transcript, as Markdown |
| `get_transcript` | The whole transcript, for short videos |
| `save_transcript` | Saves the transcript as a Markdown file |
| `save_notes` | Saves the notes your assistant wrote |

Two note styles are included: **detailed-notes**, complete study notes (the
default), and **clean-transcript**, an edited transcript that stays close to
word for word. Files are saved to `~/Documents/vink` unless you set
`VINK_OUTPUT_DIR`.

More details: [docs/mcp.md](https://github.com/navinbhagat322/youtube-vink/blob/main/docs/mcp.md).

## Command line

```text
vink transcript URL   Save a transcript as Markdown
vink languages URL    List the caption languages a video has
vink mcp              Run the MCP server
```

```bash
# Hindi if available, otherwise English
vink transcript https://youtu.be/VIDEO_ID --lang hi,en

# The language spoken in the video, printed to the terminal
vink transcript VIDEO_ID --lang original --stdout
```

<details>
<summary><strong>All options</strong></summary>

```text
vink transcript URL [--lang en,hi] [--output-dir DIR] [--format markdown] [--stdout]
                    [--translate | --no-translate] [--cache | --no-cache]
vink languages URL [--cache | --no-cache]
vink mcp [--transport stdio|http] [--host HOST] [--port PORT] [--insecure-no-auth]
vink [-v | --verbose] [--version] COMMAND
```

| Option | Meaning |
|--------|---------|
| `--lang` | Preferred languages, most preferred first. `original` means the spoken language. |
| `--stdout` | Print instead of saving a file. |
| `--no-translate` | Never fall back to YouTube's machine translation. |
| `--no-cache` | Fetch fresh data from YouTube. |
| `-v` | Show progress logs (place it before the command). |

Exit codes: `0` success, `1` the transcript could not be fetched, `2` invalid
input or options.

</details>

## Running on a server

YouTube blocks most requests from cloud servers (AWS, GCP, hosted sandboxes).
On your own computer everything just works. For servers, pick one of these:

| | Host at home | Residential proxy |
|---|---|---|
| **Idea** | Run vink on a home machine; connect to it over HTTPS | Run vink anywhere; send YouTube traffic through a proxy |
| **Cost** | Free | Paid proxy plan |
| **Key setting** | `VINK_AUTH_TOKEN` | `VINK_PROXY_URL` |

Host at home:

```bash
VINK_AUTH_TOKEN='a-long-random-secret' vink mcp --transport http --port 8000
```

Residential proxy:

```bash
VINK_PROXY_URL='http://user:pass@proxy.example.com:8080' vink mcp
```

Webshare rotating residential proxies are supported out of the box via
`VINK_WEBSHARE_USERNAME` and `VINK_WEBSHARE_PASSWORD`.

The step-by-step guide covers Cloudflare Tunnel, systemd and troubleshooting:
[docs/hosting.md](https://github.com/navinbhagat322/youtube-vink/blob/main/docs/hosting.md).

## Configuration

Everything works without configuration. To change a default, set an
environment variable or put it in a `.env` file:

| Variable | Default | What it does |
|----------|---------|--------------|
| `VINK_LANGUAGES` | `en` | Preferred languages, comma-separated |
| `VINK_OUTPUT_DIR` | `./output` (CLI), `~/Documents/vink` (MCP) | Where files are saved |
| `VINK_CHUNK_SECONDS` | `600` | Length of one part for `get_chunk` |
| `VINK_PROXY_URL` | none | Proxy for requests to YouTube |
| `VINK_AUTH_TOKEN` | none | Token required by the HTTP server |

All settings: [docs/configuration.md](https://github.com/navinbhagat322/youtube-vink/blob/main/docs/configuration.md).

## How it works

```text
YouTube URL
   │
   ├─ pick the best caption track   (your languages · creator > auto > translated)
   ├─ fetch and cache it
   ├─ clean it into paragraphs       (noise removed · timestamps kept)
   ├─ split it into ~10-minute parts
   └─ Markdown file  ──or──  MCP tools → your AI assistant → detailed notes
```

Fetching, rendering and saving each sit behind a small interface, so new
formats (PDF, DOCX) and destinations (Notion, Obsidian) can be added without
touching the core. See
[docs/architecture.md](https://github.com/navinbhagat322/youtube-vink/blob/main/docs/architecture.md).

## FAQ

<details>
<summary><strong>Do I need a YouTube API key?</strong></summary>

No. The official YouTube Data API only lets you download captions for videos
you own. vink reads the same caption data YouTube's own player uses, through the
open-source
[`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api)
library.

</details>

<details>
<summary><strong>Does it work for videos without captions?</strong></summary>

Not yet. vink needs either creator-uploaded or auto-generated captions.
Transcribing the audio of videos without captions is planned.

</details>

<details>
<summary><strong>Can I get notes in Hindi, Hinglish or another language?</strong></summary>

Yes. The transcript can be in any language the video has, and the
`make_notes` prompt can write the notes in any language you name, including
Hinglish.

</details>

<details>
<summary><strong>Why does it say "YouTube is blocking requests"?</strong></summary>

You are running vink on a cloud server, and YouTube blocks data-center IP
addresses. See [Running on a server](#running-on-a-server).

</details>

## Contributing

Contributions are welcome: bug reports, new output formats, destinations and
note styles. See
[CONTRIBUTING.md](https://github.com/navinbhagat322/youtube-vink/blob/main/CONTRIBUTING.md)
to get started.

## License

[MIT](https://github.com/navinbhagat322/youtube-vink/blob/main/LICENSE)
