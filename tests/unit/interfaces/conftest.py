"""Fixtures for interface tests: a container wired with fake-backed services."""

from collections.abc import Callable

import httpx
import pytest

from vink.bootstrap import Container
from vink.config import Settings
from vink.services import ExportService, TranscriptService


@pytest.fixture
def make_container(
    transcript_service: TranscriptService, export_service: ExportService
) -> Callable[[Settings], Container]:
    """A container factory that wires the fake-backed services into real settings."""

    def factory(settings: Settings) -> Container:
        return Container(
            settings=settings,
            transcripts=transcript_service,
            exports=export_service,
            _http_client=httpx.Client(),
        )

    return factory
