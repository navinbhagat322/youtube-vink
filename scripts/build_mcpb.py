"""Build the Claude Desktop extension bundle (``vink-<version>.mcpb``).

The bundle uses the MCPB ``uv`` server type: it contains vink's source,
``pyproject.toml`` and ``uv.lock``, and the host installs the locked runtime
dependencies. No Python packages are vendored.

Usage::

    uv run python scripts/build_mcpb.py            # writes dist-mcpb/vink-<version>.mcpb
    uv run python scripts/build_mcpb.py --out DIR  # choose the output directory

Requires Node.js (for ``npx``). The packer version is pinned below.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parent.parent
TEMPLATE: Final = ROOT / "packaging" / "mcpb" / "manifest.json"
ICON: Final = ROOT / "docs" / "assets" / "logo.png"
MCPB_CLI: Final = "@anthropic-ai/mcpb@2.1.2"

# Everything the host needs to install and run vink with `uv run --directory`.
BUNDLE_FILES: Final = ("pyproject.toml", "uv.lock", "README.md", "LICENSE")
BUNDLE_TREES: Final = ("src",)
IGNORED: Final = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def project_version() -> str:
    """Read vink's version from ``pyproject.toml``."""
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def render_manifest(version: str) -> dict[str, object]:
    """Return the manifest template with the release version filled in."""
    manifest: dict[str, object] = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    manifest["version"] = version
    return manifest


def stage(target: Path, version: str) -> None:
    """Copy exactly the files the bundle needs into ``target``."""
    for name in BUNDLE_FILES:
        shutil.copy2(ROOT / name, target / name)
    for tree in BUNDLE_TREES:
        shutil.copytree(ROOT / tree, target / tree, ignore=IGNORED)
    shutil.copy2(ICON, target / "icon.png")
    manifest = json.dumps(render_manifest(version), indent=2, ensure_ascii=False) + "\n"
    (target / "manifest.json").write_text(manifest, encoding="utf-8")


def pack(staging: Path, output: Path) -> None:
    """Validate and pack the staged bundle with the official MCPB CLI."""
    npx = shutil.which("npx")
    if npx is None:
        sys.exit("npx not found: install Node.js to build the .mcpb bundle.")
    subprocess.run([npx, "--yes", MCPB_CLI, "validate", str(staging)], check=True)  # noqa: S603
    subprocess.run([npx, "--yes", MCPB_CLI, "pack", str(staging), str(output)], check=True)  # noqa: S603


def main() -> None:
    """Build ``vink-<version>.mcpb`` into the output directory."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "dist-mcpb", help="Output directory.")
    args = parser.parse_args()

    version = project_version()
    out_dir: Path = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"vink-{version}.mcpb"

    with tempfile.TemporaryDirectory(prefix="vink-mcpb-") as tmp:
        staging = Path(tmp) / "vink"
        staging.mkdir()
        stage(staging, version)
        pack(staging, output)

    print(output)  # noqa: T201 - the script's result, for CI logs


if __name__ == "__main__":
    main()
