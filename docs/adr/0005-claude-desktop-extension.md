# 0005. Ship a Claude Desktop extension using the MCPB `uv` server type

- Status: Accepted
- Date: 2026-11-19

## Context

Adding vink to Claude Desktop meant editing a JSON file and knowing about
`uvx`. Worse, `uvx` sometimes rebuilds its cached environment when the server
starts. That rebuild downloads dozens of packages and can exceed Claude
Desktop's 60-second startup limit, so vink silently failed to appear. New
users hit this on their very first start.

Claude Desktop supports MCP Bundles (`.mcpb`): installable extensions with a
manifest, an icon and a settings form. Manifest version 0.4 adds a `uv`
server type: the bundle contains source code and `pyproject.toml`, and the
host installs dependencies with uv.

## Decision

- Publish `vink-<version>.mcpb` with every GitHub release, built by
  `scripts/build_mcpb.py` from the template `packaging/mcpb/manifest.json`.
- Use the `uv` server type and run
  `uv run --directory ${__dirname} --frozen --no-dev vink mcp`, so the locked
  runtime dependencies are installed into the extension's own environment
  without development tools.
- Expose the optional settings (languages, save folder, Webshare, proxy URL)
  as `user_config` fields, with secrets marked `sensitive`.
- Treat empty environment values as unset (`env_ignore_empty`), because the
  host passes blank optional fields as empty strings.
- Stamp the version from `pyproject.toml` at build time, and test that the
  manifest's tools and environment variables match the code.

## Consequences

- Claude Desktop users install vink by double-clicking a file and filling in an
  optional form, with no JSON or terminal.
- After the first start, the extension starts in well under a second, because
  its environment lives in the extension folder and is not rebuilt.
- The bundle depends on uv being available to the host. The MCPB docs say the
  host manages Python and dependencies, but not whether Claude Desktop ships
  uv; the README tells users to install uv if Claude asks for it.
- Building the bundle needs Node.js (for the official `mcpb` packer), in CI
  and for local builds.

## Alternatives considered

- **Keep `uvx` instructions only.** No new artifact, but leaves the first-start
  timeout and the JSON editing in place.
- **The `python` server type with vendored packages.** Avoids uv, but the
  bundle would have to include compiled dependencies for every platform and
  Python version.
- **A Node.js wrapper.** The MCPB docs recommend Node because Claude ships it,
  but vink is a Python project and a wrapper would add a second runtime and
  codebase.
