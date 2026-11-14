from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from vink import __version__
from vink.bootstrap import Container
from vink.config import Settings
from vink.domain.errors import InvalidInputError
from vink.interfaces.mcp import create_server
from vink.interfaces.mcp.http import (
    HEALTH_PATH,
    MCP_PATH,
    build_http_app,
    check_http_security,
)

TOKEN = "unit-test-token-0123456789"
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "0"},
    },
}
ACCEPT = {"Accept": "application/json, text/event-stream"}

ClientFactory = Callable[..., TestClient]


@pytest.fixture
def make_client(
    make_container: Callable[[Settings], Container], tmp_path: Path
) -> Iterator[ClientFactory]:
    clients: list[TestClient] = []

    def factory(
        *, token: str | None = TOKEN, allowed_hosts: tuple[str, ...] = (), base_url: str = ""
    ) -> TestClient:
        server = create_server(make_container(Settings(output_dir=tmp_path)))
        app = build_http_app(server, host="127.0.0.1", token=token, allowed_hosts=allowed_hosts)
        client = TestClient(app, base_url=base_url or "http://127.0.0.1:8000")
        client.__enter__()  # run the lifespan so the MCP session manager starts
        clients.append(client)
        return client

    yield factory
    for client in clients:
        client.__exit__(None, None, None)


def _initialize(client: TestClient, **headers: str) -> int:
    return client.post(MCP_PATH, json=INITIALIZE, headers=ACCEPT | headers).status_code


class TestAuthentication:
    def test_health_needs_no_token(self, make_client: ClientFactory) -> None:
        response = make_client().get(HEALTH_PATH)

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "name": "vink", "version": __version__}

    def test_missing_token_is_rejected(self, make_client: ClientFactory) -> None:
        response = make_client().post(MCP_PATH, json=INITIALIZE, headers=ACCEPT)

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"].startswith("Bearer")

    @pytest.mark.parametrize(
        "header", [f"Bearer {TOKEN}x", "Bearer ", f"Basic {TOKEN}", TOKEN, f"bearer{TOKEN}"]
    )
    def test_wrong_credentials_are_rejected(self, make_client: ClientFactory, header: str) -> None:
        assert _initialize(make_client(), Authorization=header) == 401

    @pytest.mark.parametrize("header", [f"Bearer {TOKEN}", f"bearer {TOKEN}", f"Bearer  {TOKEN} "])
    def test_valid_token_is_accepted(self, make_client: ClientFactory, header: str) -> None:
        assert _initialize(make_client(), Authorization=header) == 200

    def test_without_token_no_auth_is_required(self, make_client: ClientFactory) -> None:
        assert _initialize(make_client(token=None)) == 200


class TestHostChecks:
    def test_any_host_is_accepted_with_token(self, make_client: ClientFactory) -> None:
        client = make_client(base_url="https://vink.example.com")

        assert _initialize(client, Authorization=f"Bearer {TOKEN}") == 200

    def test_allowed_hosts_are_enforced(self, make_client: ClientFactory) -> None:
        good = make_client(allowed_hosts=("vink.example.com",), base_url="https://vink.example.com")
        bad = make_client(allowed_hosts=("vink.example.com",), base_url="https://evil.example.com")

        assert _initialize(good, Authorization=f"Bearer {TOKEN}") == 200
        assert _initialize(bad, Authorization=f"Bearer {TOKEN}") == 421


class TestSecurityPolicy:
    def test_token_allows_any_host(self) -> None:
        check_http_security(host="0.0.0.0", token=TOKEN, allow_unauthenticated=False)

    def test_missing_token_is_refused(self) -> None:
        with pytest.raises(InvalidInputError, match="VINK_AUTH_TOKEN"):
            check_http_security(host="127.0.0.1", token=None, allow_unauthenticated=False)

    @pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
    def test_no_auth_allowed_on_loopback(self, host: str) -> None:
        check_http_security(host=host, token=None, allow_unauthenticated=True)

    @pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.5", "vink.example.com"])
    def test_no_auth_refused_elsewhere(self, host: str) -> None:
        with pytest.raises(InvalidInputError, match=r"only allowed on 127\.0\.0\.1"):
            check_http_security(host=host, token=None, allow_unauthenticated=True)
