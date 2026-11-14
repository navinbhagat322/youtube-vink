# Architecture

vink is built so that each part can be replaced or extended without touching
the rest. Fetching transcripts, rendering output and delivering files each sit
behind a small interface. Today's implementations (YouTube, Markdown, a local
folder) are just the first adapters.

## Layers

```
src/vink/
├── domain/        Immutable models and errors. Pure Python, no I/O.
├── ports/         typing.Protocol interfaces the core depends on.
├── processing/    Pure functions: track selection, cleaning, paragraphs, chunking.
├── services/      Use cases that orchestrate ports and processing.
├── adapters/      Implementations of ports. All I/O lives here.
├── interfaces/    Entry points: CLI, MCP server (stdio and HTTP).
├── styles/        Note-style prompt templates.
├── bootstrap.py   Composition root: picks the adapter for each port.
└── config.py      Typed settings.
```

### The dependency rule

Imports only point inward:

```
interfaces ──► services ──► ports ◄── adapters
                  │                      │
                  ▼                      ▼
             processing ──────────►   domain
```

- `domain` imports nothing from vink and no third-party packages.
- `services` depend on `ports`, never on concrete `adapters`.
- `adapters` implement `ports` and may reuse pure `processing` helpers.
- `interfaces` get their services from `bootstrap.build_container()` and never
  construct adapters themselves.

`bootstrap.py` is the only module that knows which adapter backs which port.

## Data flow

```
URL
 │  domain.parse_video_ref
 ▼
VideoRef ──► TranscriptSource.list_tracks ──► [TrackInfo]
                                                 │ processing.select_track
                                                 ▼
                                           TrackSelection
                                                 │ TranscriptSource.fetch
                                                 ▼
MetadataSource.get_metadata ──┐            RawTranscript (segments)
                              │                  │ processing.build_paragraphs
                              ▼                  ▼
                            Transcript (metadata + paragraphs)
                                 │
                 ┌───────────────┼──────────────────┐
                 ▼               ▼                  ▼
       Renderer.render_    processing.        Renderer.render_chunk
       transcript          chunk_paragraphs   (MCP get_chunk)
                 │
                 ▼
            Sink.write ──► file
```

## Ports

| Port | Responsibility | Current adapter |
|------|----------------|-----------------|
| `TranscriptSource` | List and fetch caption tracks | `YouTubeTranscriptSource` (youtube-transcript-api, optionally through a proxy), wrapped by `CachingTranscriptSource` |
| `MetadataSource` | Title and channel | `OEmbedMetadataSource` (YouTube oEmbed), wrapped by `CachingMetadataSource` |
| `Cache` | Key-value storage for the caching decorator | `FileCache` |
| `Renderer` | Turn a transcript or chunk into text | `MarkdownRenderer` |
| `Sink` | Deliver rendered output | `LocalDirectorySink` |

Ports accept and return domain models and raise domain errors only. Adapters
translate library types and exceptions at the boundary.

### Caching as a decorator

`CachingTranscriptSource` and `CachingMetadataSource` implement their ports by
wrapping another implementation of the same port. Services don't know caching
exists. Turning it off (`VINK_USE_CACHE=false`) just means bootstrap skips the
wrappers. Entries are stored with a timestamp (`TimedEntries`), so each kind of
data can have its own lifetime: caption text never expires, track lists expire
after a day, metadata after a week. Raw segments are cached, not cleaned
paragraphs, so improvements to cleaning apply to cached videos straight away.

## Network access and hosting

Proxy settings are translated by `bootstrap.proxy_options()` into
`adapters.youtube.ProxyOptions`, which both YouTube adapters use: the transcript
source via `youtube-transcript-api`'s proxy configuration, and the metadata
source via the shared `httpx` client. Services never see proxies.

`interfaces/mcp/http.py` serves the same `MCPServer` over Streamable HTTP. It
adds a health check and wraps the app in `BearerTokenMiddleware`; the MCP tools
are unchanged. See [ADR 0004](adr/0004-http-transport-and-proxies.md).

## Error handling

All errors derive from `vink.domain.errors.VinkError`. Interfaces decide how to
present them: the CLI prints a message and exits with code 1 (or 2 for invalid
input), and the MCP server returns a tool error with the same message.
Metadata failures are non-fatal, and the video ID is used as the title.

## Extending vink

| To add | Implement | Location | Then |
|--------|-----------|----------|------|
| Whisper transcription for videos without captions | `TranscriptSource` | `adapters/whisper/` | Compose it as a fallback in `bootstrap.py` |
| PDF / DOCX / HTML output | `Renderer` | `adapters/render/` | Add it to the renderer list in `bootstrap.py` |
| Notion / Obsidian / Google Docs | `Sink` | `adapters/sinks/` | Select it via a setting in `bootstrap.py` |
| Richer metadata (chapters, duration) | `MetadataSource` | `adapters/ytdlp/` | Swap it in `bootstrap.py` |
| A new note style | — | `styles/<name>.md` | Nothing: discovered automatically |
| HTTP API or browser-extension bridge | — | `interfaces/http/` | Reuse `build_container()` |

Heavy dependencies for new adapters belong in optional extras, imported inside
the adapter, so the core stays light.

## Decisions

Significant decisions are recorded in [docs/adr](adr/).
