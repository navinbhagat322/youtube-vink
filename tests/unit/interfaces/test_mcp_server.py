from collections.abc import Callable
from pathlib import Path

import pytest
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.shared.exceptions import MCPError
from mcp.types import CallToolResult, GetPromptResult, TextContent

from tests.fakes import FakeTranscriptSource, InMemorySink
from vink.bootstrap import Container
from vink.config import Settings
from vink.domain.errors import TranscriptsDisabledError
from vink.interfaces.mcp import create_server

VIDEO_URL = "https://youtu.be/dQw4w9WgXcQ"

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def server(make_container: Callable[[Settings], Container], tmp_path: Path) -> MCPServer:
    settings = Settings(chunk_seconds=60, output_dir=tmp_path, cache_dir=tmp_path / "cache")
    return create_server(make_container(settings))


def _text(result: object) -> str:
    assert isinstance(result, CallToolResult)
    block = result.content[0]
    assert isinstance(block, TextContent)
    return block.text


async def test_registers_expected_tools_and_prompts(server: MCPServer) -> None:
    tools = {tool.name for tool in await server.list_tools()}
    prompts = {prompt.name for prompt in await server.list_prompts()}

    assert tools == {
        "list_languages",
        "get_video_info",
        "get_chunk",
        "get_transcript",
        "save_transcript",
        "save_notes",
    }
    assert prompts == {"make_notes"}


async def test_get_video_info_returns_structured_result(server: MCPServer) -> None:
    result = await server.call_tool("get_video_info", {"url": VIDEO_URL})

    assert isinstance(result, CallToolResult)
    info = result.structured_content
    assert info is not None
    assert info["title"] == "Sample Lecture"
    assert info["language_code"] == "en"
    assert info["caption_kind"] == "manual"
    assert info["chunk_count"] == 1
    assert info["chunk_minutes"] == 1.0


async def test_list_languages(server: MCPServer) -> None:
    result = await server.call_tool("list_languages", {"url": VIDEO_URL})

    assert isinstance(result, CallToolResult)
    assert result.structured_content is not None
    assert "'language_code': 'hi'" in str(result.structured_content)


async def test_get_chunk_returns_markdown(server: MCPServer) -> None:
    text = _text(await server.call_tool("get_chunk", {"url": VIDEO_URL, "part": 1}))

    assert "## Part 1 of 1" in text
    assert "gradient descent" in text


@pytest.mark.parametrize("part", [0, 2])
async def test_get_chunk_rejects_out_of_range_part(server: MCPServer, part: int) -> None:
    with pytest.raises(ToolError, match="Part must be between 1 and 1"):
        await server.call_tool("get_chunk", {"url": VIDEO_URL, "part": part})


async def test_get_transcript_honours_languages(
    server: MCPServer, source: FakeTranscriptSource
) -> None:
    text = _text(await server.call_tool("get_transcript", {"url": VIDEO_URL, "languages": ["hi"]}))

    assert 'language: "hi"' in text
    assert source.fetch_calls[-1].language_code == "hi"


async def test_save_transcript_and_notes(server: MCPServer, sink: InMemorySink) -> None:
    await server.call_tool("save_transcript", {"url": VIDEO_URL})
    await server.call_tool("save_notes", {"url": VIDEO_URL, "content": "# My notes"})

    assert set(sink.files) == {"Sample Lecture.md", "Sample Lecture - notes.md"}
    assert sink.files["Sample Lecture - notes.md"] == "# My notes"


async def test_domain_errors_become_tool_errors(
    server: MCPServer, source: FakeTranscriptSource
) -> None:
    source.error = TranscriptsDisabledError("dQw4w9WgXcQ")

    with pytest.raises(ToolError, match="has no transcripts"):
        await server.call_tool("get_transcript", {"url": VIDEO_URL})


async def test_invalid_url_becomes_tool_error(server: MCPServer) -> None:
    with pytest.raises(ToolError, match="Could not find a YouTube video ID"):
        await server.call_tool("get_transcript", {"url": "nope"})


async def test_make_notes_prompt_includes_style_and_language(server: MCPServer) -> None:
    result = await server.get_prompt(
        "make_notes", {"url": VIDEO_URL, "output_language": "Hinglish"}
    )

    assert isinstance(result, GetPromptResult)
    content = result.messages[0].content
    assert isinstance(content, TextContent)
    assert "detailed study notes written in Hinglish" in content.text
    assert content.text.rstrip().endswith(f"Video: {VIDEO_URL}")


async def test_make_notes_prompt_rejects_unknown_style(server: MCPServer) -> None:
    with pytest.raises(MCPError, match="Unknown style"):
        await server.get_prompt("make_notes", {"url": VIDEO_URL, "style": "haiku"})
