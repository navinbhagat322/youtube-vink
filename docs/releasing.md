# Releasing

vink is published to [PyPI](https://pypi.org/project/vink/) by the
`Release` GitHub Actions workflow whenever a version tag is pushed. It uses
[trusted publishing](https://docs.pypi.org/trusted-publishers/): PyPI trusts
this repository's workflow directly, so no API token is stored anywhere.

## One-time setup

1. **Create a PyPI account** at <https://pypi.org/account/register/> and turn on
   two-factor authentication (required for publishing).
2. **Register a pending publisher.** On PyPI go to *Your account → Publishing →
   Add a new pending publisher → GitHub* and enter:

   | Field | Value |
   |-------|-------|
   | PyPI project name | `vink` |
   | Owner | `navinbhagat322` |
   | Repository name | `youtube-vink` |
   | Workflow name | `release.yml` |
   | Environment name | `pypi` |

   A pending publisher reserves the name until the first upload creates the
   project.
3. **Create the GitHub environment.** In the repository go to *Settings →
   Environments → New environment*, name it `pypi`, and optionally add yourself
   as a required reviewer so every release waits for your approval.

Optional dry run: repeat steps 1–2 on <https://test.pypi.org> and temporarily
add `repository-url: https://test.pypi.org/legacy/` to the publish step.

## Cutting a release

1. Make sure `main` is green in CI.
2. Bump the version (SemVer) in `pyproject.toml`:

   ```bash
   uv version --bump minor    # or: patch, major
   ```

3. In `CHANGELOG.md`, move the entries under `[Unreleased]` into a new
   `## [X.Y.Z] - YYYY-MM-DD` section and update the comparison links at the
   bottom.
4. Commit, tag and push:

   ```bash
   git add pyproject.toml uv.lock CHANGELOG.md
   git commit -m "chore(release): vX.Y.Z"
   git tag vX.Y.Z
   git push origin main vX.Y.Z
   ```

5. The `Release` workflow checks that the tag matches the version, runs the
   tests, builds the sdist and wheel, and publishes them. If you configured a
   reviewer, approve the deployment under the workflow run.
6. After publishing, the workflow creates a GitHub release for the tag with
   generated notes and these files attached: the wheel, the sdist, and the
   Claude Desktop extension `vink-X.Y.Z.mcpb`. Edit it to paste the changelog
   section if you want hand-written notes.

## Building locally

To build the Claude Desktop extension (needs Node.js for `npx`):

```bash
uv run python scripts/build_mcpb.py     # writes dist-mcpb/vink-X.Y.Z.mcpb
```

The manifest template is `packaging/mcpb/manifest.json`; the script fills in
the version from `pyproject.toml`.


To inspect what will be uploaded:

```bash
uv build
uvx twine check dist/*
```

PyPI never allows re-uploading the same version. If a release is broken, fix
it and publish a new patch version.
