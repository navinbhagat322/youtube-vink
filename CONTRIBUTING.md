# Contributing to vink

Thanks for helping. This guide covers setup, the development workflow, and
the conventions every change follows.

## Development setup

You need Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/navinbhagat322/youtube-vink.git
cd youtube-vink
uv sync                      # creates .venv with runtime + dev dependencies
uv run pre-commit install    # runs format, lint and type checks before each commit
```

## Running checks

Run the same checks CI runs:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest --cov
```

Tests that call real YouTube are excluded by default. Run them with:

```bash
uv run pytest -m integration
```

## Project layout

```
src/vink/
├── domain/       # immutable models and errors (no I/O, no third-party imports)
├── ports/        # Protocol interfaces the core depends on
├── processing/   # pure functions: track selection, cleaning, paragraphs, chunks
├── services/     # use cases that orchestrate ports and processing
├── adapters/     # implementations: YouTube, cache, Markdown, local files
├── interfaces/   # entry points: CLI and MCP server
├── styles/       # note-style prompt templates (Markdown files)
├── bootstrap.py  # wires adapters into services
└── config.py     # typed settings
```

Read [docs/architecture.md](docs/architecture.md) before making structural
changes. The key rule is that dependencies point inward: services depend on
ports, never on adapters.

## Common changes

**Add an output format** (e.g. PDF): implement the `Renderer` protocol in
`src/vink/adapters/render/`, register it in `bootstrap.py`, and add a golden
file test in `tests/unit/adapters/`.

**Add a destination** (e.g. Notion): implement the `Sink` protocol in
`src/vink/adapters/sinks/` and wire it in `bootstrap.py`. Put heavy
dependencies in an optional extra (`vink[notion]`) and import them inside the
adapter.

**Add a note style**: add a Markdown file to `src/vink/styles/`. It is
discovered automatically. Use `{output_language}` where the target language
belongs.

## Conventions

- **Style:** PEP 8 via `ruff format`, line length 100, Google-style docstrings
  on all public code, full type hints (`mypy --strict`).
- **Errors:** raise errors from `vink.domain.errors`. Adapters convert library
  exceptions with `raise ... from exc`. Messages should tell the user what to
  do next.
- **Logging:** `logging.getLogger(__name__)`, never `print()`. Nothing may
  write to stdout from the MCP server.
- **Tests:** unit tests never touch the network. Use the fakes in
  `tests/fakes.py`. Every bug fix starts with a failing test.

## Commits and pull requests

We use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```
feat(youtube): fall back to auto-generated captions
fix(processing): keep Devanagari punctuation when merging segments
docs: explain MCP setup on Windows
```

Scopes follow the architecture: `domain`, `processing`, `services`, `youtube`,
`cache`, `render`, `sinks`, `cli`, `mcp`, `config`, `deps`.

Before opening a pull request:

- [ ] All checks above pass.
- [ ] New behavior has tests.
- [ ] User-visible changes are noted under `[Unreleased]` in `CHANGELOG.md`.
- [ ] Docs are updated for new options or behavior.

Keep pull requests small and focused. They are squash-merged, so the PR title
becomes the commit message.

## Reporting bugs

Open an issue with the video URL (if public), the command you ran, the full
error output, and `vink --version`. For security issues, see
[SECURITY.md](SECURITY.md).

## Code of conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
