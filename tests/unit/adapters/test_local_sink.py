from pathlib import Path

import pytest

from vink.adapters.sinks import LocalDirectorySink
from vink.domain.errors import SinkError


def test_writes_file_and_returns_absolute_path(tmp_path: Path) -> None:
    sink = LocalDirectorySink(tmp_path / "out")

    location = sink.write("notes.md", "# Hi ✓")

    assert Path(location) == (tmp_path / "out" / "notes.md").resolve()
    assert Path(location).read_text(encoding="utf-8") == "# Hi ✓"


def test_replaces_existing_file(tmp_path: Path) -> None:
    sink = LocalDirectorySink(tmp_path)

    sink.write("a.md", "old")
    sink.write("a.md", "new")

    assert (tmp_path / "a.md").read_text() == "new"
    assert [p.name for p in tmp_path.iterdir()] == ["a.md"]


@pytest.mark.parametrize("name", ["", ".", "..", "../escape.md", "sub/file.md", "/abs.md"])
def test_rejects_unsafe_names(tmp_path: Path, name: str) -> None:
    with pytest.raises(SinkError):
        LocalDirectorySink(tmp_path).write(name, "x")


def test_write_failure_raises_sink_error(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("x")

    with pytest.raises(SinkError):
        LocalDirectorySink(blocker / "sub").write("a.md", "x")
