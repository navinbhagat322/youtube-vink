# 0001. Use a ports-and-adapters architecture

- Status: Accepted
- Date: 2026-11-14

## Context

vink starts as a YouTube-to-Markdown tool, but the roadmap already includes
more transcript sources (Whisper for videos without captions), more output
formats (PDF, DOCX), more destinations (Notion, Obsidian, Google Docs) and more
entry points (CLI, MCP server, a browser extension). If the core logic called
`youtube-transcript-api`, wrote files and formatted Markdown directly, each of
these additions would mean editing and retesting the core.

## Decision

Organize the code as ports and adapters (hexagonal architecture):

- `domain` holds immutable models and errors with no dependencies.
- `ports` defines small `typing.Protocol` interfaces: `TranscriptSource`,
  `MetadataSource`, `Cache`, `Renderer`, `Sink`.
- `adapters` implement the ports and contain all I/O.
- `services` orchestrate ports and pure `processing` functions.
- `interfaces` (CLI, MCP) use services built by a single composition root,
  `bootstrap.py`.

## Consequences

- New sources, formats and destinations are new files plus one line in
  `bootstrap.py`.
- Services and processing are tested with in-memory fakes, with no network or
  mocks of third-party libraries.
- There is more structure than a single-script tool would need. For the MVP
  that costs a few extra small modules.
- Contributors need to learn the dependency rule. It is documented in
  `docs/architecture.md`.

## Alternatives considered

- **Single module or script.** Fastest to write, but every planned feature
  would grow one file and couple everything to YouTube and Markdown.
- **Plugin system with entry points.** More flexible for third parties, but
  premature before there is more than one implementation of any port. It can be
  layered on top of the ports later.
