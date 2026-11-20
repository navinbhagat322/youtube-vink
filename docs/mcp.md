# Using vink with MCP clients

vink includes an [MCP](https://modelcontextprotocol.io) server. It gives an AI
client (Claude Desktop, Claude Code, or any MCP-compatible app) tools to read
YouTube transcripts and prompts for turning them into notes. The server calls
no AI model itself: your client writes the notes, so vink needs no API key.

## Setup

### Claude Desktop extension (easiest)

Each [GitHub release](https://github.com/navinbhagat322/youtube-vink/releases/latest)
includes `vink-<version>.mcpb`, a Claude Desktop extension. Double-click it, or
drag it into **Settings → Extensions**, and click **Install**. Claude shows a
form for the optional settings:

| Setting | Default | Maps to |
|---------|---------|---------|
| Transcript languages | `en` | `VINK_LANGUAGES` |
| Save folder | `Documents/vink` | `VINK_OUTPUT_DIR` |
| Webshare proxy username / password | empty | `VINK_WEBSHARE_USERNAME` / `VINK_WEBSHARE_PASSWORD` |
| Other proxy URL | empty | `VINK_PROXY_URL` |

Leave the proxy fields empty on a home or office connection. The extension uses
the MCPB `uv` server type: it contains vink's source and lock file, and
dependencies are installed with [uv](https://docs.astral.sh/uv/) rather than
bundled.

### Claude Desktop (manual)

Edit `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "vink": {
      "command": "uvx",
      "args": ["vink", "mcp"],
      "env": {
        "VINK_OUTPUT_DIR": "/absolute/path/to/your/notes",
        "VINK_LANGUAGES": "en"
      }
    }
  }
}
```

`uvx` downloads and runs the latest vink from PyPI. `VINK_OUTPUT_DIR` is
optional; without it, files are saved to `~/Documents/vink`. If Claude Desktop cannot
find `uvx`, use its absolute path (run `which uvx`). To run from a source
checkout instead, use `"command": "uv"` with
`"args": ["--directory", "/absolute/path/to/youtube-vink", "run", "vink", "mcp"]`.

Restart Claude Desktop. vink's tools appear in the tools menu.

### Claude Code

```bash
claude mcp add vink -- uvx vink mcp
```

### Remote clients (Streamable HTTP)

To use vink from a client on another machine, for example a hosted agent
platform, run it as an HTTP server:

```bash
VINK_AUTH_TOKEN='a-long-random-secret' vink mcp --transport http --port 8000
```

Clients connect to `http://HOST:8000/mcp` with the header
`Authorization: Bearer a-long-random-secret`. `GET /healthz` reports whether
the server is up. [hosting.md](hosting.md) explains how to publish it safely
with a tunnel, and how to use a proxy when the server's IP is blocked by
YouTube.

## Tools

| Tool | Arguments | Returns |
|------|-----------|---------|
| `list_languages` | `url` | Available caption tracks |
| `get_video_info` | `url`, `languages?` | Title, channel, selected language, duration, `chunk_count` |
| `get_chunk` | `url`, `part` (1-based), `languages?` | One part of the transcript as Markdown |
| `get_transcript` | `url`, `languages?` | The full transcript as Markdown |
| `save_transcript` | `url`, `languages?` | Path of the saved transcript file |
| `save_notes` | `url`, `content`, `suffix="notes"` | Path of the saved notes file (`<title> - <suffix>.md`) |

`languages` is a list of codes in order of preference, such as `["hi", "en"]`.
If you leave it out, the server's `VINK_LANGUAGES` setting is used.

## The `make_notes` prompt

| Argument | Default | Example |
|----------|---------|---------|
| `url` | (required) | `https://youtu.be/aircAruvnKk` |
| `style` | `detailed-notes` | `clean-transcript` |
| `output_language` | same as the transcript | `English`, `Hindi`, `Hinglish` |

The prompt tells the client to call `get_video_info`, then read each part with
`get_chunk` and write full notes for it before moving on. This keeps long
videos from being squashed into a summary.

### Styles

- **detailed-notes:** complete study notes. Every point, example and step is
  kept, with headings, lists, tables and code blocks, a timestamp per section,
  and key takeaways plus a glossary at the end.
- **clean-transcript:** close to word for word. Filler and false starts are
  removed, punctuation is fixed, and text is split into paragraphs with
  headings. Nothing is summarized.

To add a style, drop a Markdown file into `src/vink/styles/`. Use
`{output_language}` where the language should go.

## Tips

- For Hindi or mixed-language videos, auto-generated captions are often in
  Devanagari. Fetch them with `languages: ["original"]` and ask for
  `output_language: Hinglish` (Roman script) if that suits you better.
- Very long videos (2+ hours) can exceed a single conversation. Ask the client
  to save notes after every few parts.
- Repeated calls for the same video are served from the local cache.
