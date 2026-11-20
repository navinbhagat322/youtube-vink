"""Guards that keep the Claude Desktop extension manifest in sync with the code."""

import importlib.util
import json
import re
import tomllib
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

from vink.bootstrap import Container
from vink.config import Settings
from vink.interfaces.mcp import create_server

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = json.loads((ROOT / "packaging" / "mcpb" / "manifest.json").read_text(encoding="utf-8"))
USER_CONFIG_REF = re.compile(r"\$\{user_config\.(\w+)\}")


def _load_build_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_mcpb", ROOT / "scripts" / "build_mcpb.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_uses_uv_server_type_without_dev_dependencies() -> None:
    server = MANIFEST["server"]
    args = server["mcp_config"]["args"]

    assert MANIFEST["manifest_version"] == "0.4"
    assert server["type"] == "uv"
    assert (ROOT / server["entry_point"]).is_file()
    assert {"--frozen", "--no-dev"} <= set(args)
    assert args[-2:] == ["vink", "mcp"]


def test_env_vars_are_real_settings() -> None:
    settings_fields = set(Settings.model_fields)

    for name in MANIFEST["server"]["mcp_config"]["env"]:
        assert name.startswith("VINK_")
        assert name.removeprefix("VINK_").lower() in settings_fields


def test_every_user_config_field_is_used_and_defined() -> None:
    env_values = " ".join(MANIFEST["server"]["mcp_config"]["env"].values())
    referenced = set(USER_CONFIG_REF.findall(env_values))

    assert referenced == set(MANIFEST["user_config"])


def test_secrets_are_marked_sensitive() -> None:
    config = MANIFEST["user_config"]

    assert config["webshare_password"]["sensitive"] is True
    assert config["proxy_url"]["sensitive"] is True


@pytest.mark.anyio
async def test_declared_tools_match_server(
    make_container: Callable[[Settings], Container], tmp_path: Path
) -> None:
    server = create_server(make_container(Settings(output_dir=tmp_path)))

    registered = {tool.name for tool in await server.list_tools()}

    assert {tool["name"] for tool in MANIFEST["tools"]} == registered


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class TestBuildScript:
    def test_manifest_gets_project_version(self) -> None:
        build = _load_build_script()
        with (ROOT / "pyproject.toml").open("rb") as handle:
            version = tomllib.load(handle)["project"]["version"]

        assert build.render_manifest(build.project_version())["version"] == version

    def test_stage_copies_only_runtime_files(self, tmp_path: Path) -> None:
        build = _load_build_script()

        build.stage(tmp_path, "9.9.9")

        names = {path.name for path in tmp_path.iterdir()}
        assert names == {
            "manifest.json",
            "icon.png",
            "pyproject.toml",
            "uv.lock",
            "README.md",
            "LICENSE",
            "src",
        }
        assert json.loads((tmp_path / "manifest.json").read_text())["version"] == "9.9.9"
        assert not list(tmp_path.rglob("__pycache__"))
        assert (tmp_path / "src" / "vink" / "styles" / "detailed-notes.md").is_file()
