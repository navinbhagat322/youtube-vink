"""Serving the MCP server over Streamable HTTP, protected by a bearer token.

This lets vink run on one machine (for example a home server whose IP YouTube
does not block) and be used by MCP clients elsewhere (for example a hosted
agent platform). See ``docs/hosting.md`` and ``docs/adr/0004-http-hosting.md``.
"""

import hmac
import ipaddress
import logging
from collections.abc import Sequence
from typing import Final

import uvicorn
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from vink import __version__
from vink.domain.errors import InvalidInputError

logger = logging.getLogger(__name__)

MCP_PATH: Final = "/mcp"
HEALTH_PATH: Final = "/healthz"

_KEYGEN_HINT: Final = (
    "Generate one with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
)


def check_http_security(*, host: str, token: str | None, allow_unauthenticated: bool) -> None:
    """Refuse to start an HTTP server that anyone on the network could use.

    Args:
        host: Interface the server will bind to.
        token: Bearer token clients must send, if configured.
        allow_unauthenticated: Explicit opt-out of authentication for local testing.

    Raises:
        InvalidInputError: If the combination is unsafe.
    """
    if token:
        return
    if not allow_unauthenticated:
        raise InvalidInputError(
            "The HTTP transport requires an access token. Set VINK_AUTH_TOKEN "
            f"(at least 16 characters). {_KEYGEN_HINT}. For local testing only, pass "
            "--insecure-no-auth together with --host 127.0.0.1."
        )
    if not _is_loopback(host):
        raise InvalidInputError(
            f"--insecure-no-auth is only allowed on 127.0.0.1 or localhost, not {host!r}. "
            "Set VINK_AUTH_TOKEN to serve on other interfaces."
        )


def build_http_app(
    server: MCPServer,
    *,
    host: str,
    token: str | None,
    allowed_hosts: Sequence[str] = (),
) -> ASGIApp:
    """Wrap ``server`` in an ASGI app with a health check and optional token auth.

    Args:
        server: The configured MCP server.
        host: Interface the server binds to; used for the SDK's default host checks.
        token: Bearer token required on every MCP request, or ``None`` for none.
        allowed_hosts: Accepted ``Host`` header values. When empty and a token is
            set, any host is accepted, which is what tunnels and reverse proxies
            need; the token is the access control.

    Returns:
        An ASGI application serving MCP at :data:`MCP_PATH` and a health check at
        :data:`HEALTH_PATH`.
    """
    app = server.streamable_http_app(
        streamable_http_path=MCP_PATH,
        stateless_http=True,
        transport_security=_transport_security(token=token, allowed_hosts=allowed_hosts),
        host=host,
    )
    app.add_route(HEALTH_PATH, _health, methods=["GET"])
    if token:
        return BearerTokenMiddleware(app, token=token, exempt_paths=frozenset({HEALTH_PATH}))
    return app


def serve_http(app: ASGIApp, *, host: str, port: int, log_level: str) -> None:
    """Run ``app`` with uvicorn until interrupted."""
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level=log_level.lower(),
        proxy_headers=True,
        server_header=False,
    )
    uvicorn.Server(config).run()


class BearerTokenMiddleware:
    """ASGI middleware that requires ``Authorization: Bearer <token>`` on HTTP requests.

    Tokens are compared in constant time. Non-HTTP scopes (such as lifespan
    events) and the exempt paths pass through untouched.

    Args:
        app: The application to protect.
        token: The expected token.
        exempt_paths: Paths reachable without a token, such as a health check.
    """

    def __init__(self, app: ASGIApp, *, token: str, exempt_paths: frozenset[str]) -> None:
        self._app = app
        self._token = token.encode("utf-8")
        self._exempt_paths = exempt_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pass authorized requests through; answer the rest with 401."""
        if scope["type"] != "http" or scope["path"] in self._exempt_paths:
            await self._app(scope, receive, send)
            return
        if self._is_authorized(scope):
            await self._app(scope, receive, send)
            return
        logger.warning("Rejected unauthenticated request to %s", scope["path"])
        response = JSONResponse(
            {"error": "unauthorized", "message": "Send 'Authorization: Bearer <token>'."},
            status_code=401,
            headers={"WWW-Authenticate": 'Bearer realm="vink"'},
        )
        await response(scope, receive, send)

    def _is_authorized(self, scope: Scope) -> bool:
        headers = dict(scope.get("headers", []))
        scheme, _, credentials = headers.get(b"authorization", b"").partition(b" ")
        if scheme.lower() != b"bearer":
            return False
        return hmac.compare_digest(credentials.strip(), self._token)


def _transport_security(
    *, token: str | None, allowed_hosts: Sequence[str]
) -> TransportSecuritySettings | None:
    """Choose DNS-rebinding protection settings for the SDK's HTTP transport."""
    if allowed_hosts:
        return TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=list(allowed_hosts),
            allowed_origins=[f"https://{host}" for host in allowed_hosts],
        )
    if token:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    return None  # SDK default: accept only localhost Host headers on loopback binds


async def _health(_: Request) -> Response:
    """Report that the server is up, without authentication or upstream calls."""
    return JSONResponse({"status": "ok", "name": "vink", "version": __version__})


def _is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False
