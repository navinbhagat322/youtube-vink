# 0004. Serve MCP over HTTP with a bearer token, and add vink-specific proxy settings

- Status: Accepted
- Date: 2026-11-14

## Context

YouTube blocks caption requests from data-center IP addresses (see ADR 0002).
Users running vink inside hosted agent platforms and cloud sandboxes hit this
immediately. Two ways around it exist: run vink on a machine with a
residential IP and reach it remotely, or route vink's YouTube traffic through
a residential proxy.

vink 0.1 supported neither. It only spoke MCP over stdio, and the only way to
use a proxy was the standard `HTTPS_PROXY` variable. That variable caused a
real failure: `uvx` read it while installing vink, and a malformed value
crashed vink's HTTP client at startup, which MCP clients reported only as
"Connection closed".

## Decision

1. **Streamable HTTP transport.** `vink mcp --transport http` serves the MCP
   endpoint at `/mcp` and an unauthenticated health check at `/healthz`. It
   runs in stateless mode, so no session state is lost behind tunnels or on
   restart.
2. **Mandatory bearer-token authentication.** The HTTP server refuses to start
   without `VINK_AUTH_TOKEN` (at least 16 characters). `--insecure-no-auth`
   exists for local testing and is accepted only on loopback addresses. Tokens
   are compared in constant time.
3. **Host checks follow the deployment.** By default, with a token, any `Host`
   header is accepted, because tunnels and reverse proxies forward the public
   hostname. `VINK_ALLOWED_HOSTS` turns on the SDK's DNS-rebinding protection
   for a fixed hostname. Without a token, the SDK's localhost-only default
   applies.
4. **vink-specific proxy settings.** `VINK_PROXY_URL` (any HTTP(S) proxy) and
   `VINK_WEBSHARE_USERNAME` / `VINK_WEBSHARE_PASSWORD` (rotating residential,
   with automatic retry on blocks) apply only to vink's YouTube and metadata
   requests. They take precedence over `HTTPS_PROXY`, which stays supported.
5. **Fail fast and clearly.** Proxy URLs are validated at startup. Errors name
   the environment variable, explain the fix, and never echo credentials.

## Consequences

- vink can be hosted on a home machine behind Cloudflare Tunnel with no proxy
  cost, or in the cloud with a residential proxy.
- New runtime dependencies on `uvicorn` and `starlette`. Both were already
  installed as dependencies of the MCP SDK; they are now declared explicitly
  because vink imports them.
- A token is a single shared secret. Multi-user access control (OAuth, per-user
  tokens) is out of scope until there is a need for it.

## Alternatives considered

- **OAuth via the MCP SDK's authorization support.** The standard for public
  MCP servers, but it needs an authorization server and is far heavier than a
  personal or team deployment needs. Can be added later behind the same
  `--transport http` flag.
- **Leave authentication to the tunnel** (e.g. Cloudflare Access). Useful as an
  extra layer, but vink should be safe by default without relying on
  infrastructure the user may not configure.
- **Only document `HTTPS_PROXY`.** No code needed, but it affects unrelated
  tools such as `uvx`, and malformed values produced unexplained crashes.
