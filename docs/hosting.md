# Running vink on a server

vink reads captions the same way YouTube's own player does. YouTube refuses
most of these requests when they come from **data-center IP addresses**: AWS,
Google Cloud, Azure, DigitalOcean, Render, Fly.io, GitHub Actions and most
hosted sandboxes. On such machines vink reports:

```text
YouTube is blocking requests from this network (common on cloud servers).
```

There are two ways around it:

| Option | Where vink runs | Cost | Best for |
|--------|-----------------|------|----------|
| [A. Host on a home or office machine](#a-host-on-a-home-or-office-machine) | A computer on a residential or office connection, reached over HTTPS | Free | Personal use, small teams |
| [B. Use a residential proxy](#b-use-a-residential-proxy) | Anywhere, including the cloud | Paid proxy plan | Hosted platforms, larger volumes |

---

## A. Host on a home or office machine

```text
MCP client (cloud)  ──HTTPS──►  Cloudflare Tunnel  ──►  vink on your machine  ──►  YouTube
```

YouTube sees a normal residential IP, so no proxy is needed.

### 1. Create an access token

The HTTP server refuses to start without one:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Keep it secret. Anyone with the token can use your machine's connection to
fetch transcripts.

### 2. Run vink over HTTP

```bash
VINK_AUTH_TOKEN='paste-your-token' vink mcp --transport http --port 8000
```

```text
vink MCP server on http://127.0.0.1:8000/mcp (bearer token required)
```

Check it:

```bash
curl http://127.0.0.1:8000/healthz
```

```json
{"status":"ok","name":"vink","version":"0.2.0"}
```

The server binds to `127.0.0.1` by default, so only local programs (such as
the tunnel below) can reach it. To expose it on your network instead, add
`--host 0.0.0.0`.

### 3. Publish it with Cloudflare Tunnel

[Install `cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/),
then try a temporary tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

It prints a URL like `https://random-words.trycloudflare.com`. Your MCP endpoint
is that URL plus `/mcp`.

Quick tunnels get a new URL every time they start. For a permanent address on
your own domain, create a
[named tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-local-tunnel/).
Then also set `VINK_ALLOWED_HOSTS=vink.yourdomain.com` so vink accepts only
requests addressed to that hostname.

[Tailscale Funnel](https://tailscale.com/kb/1223/funnel) and
[ngrok](https://ngrok.com/) work the same way.

### 4. Connect your MCP client

Use the **Streamable HTTP** transport:

| Field | Value |
|-------|-------|
| URL | `https://vink.yourdomain.com/mcp` |
| Header | `Authorization: Bearer <your token>` |

For example, a client that accepts JSON configuration:

```json
{
  "mcpServers": {
    "vink": {
      "type": "http",
      "url": "https://vink.yourdomain.com/mcp",
      "headers": { "Authorization": "Bearer paste-your-token" }
    }
  }
}
```

Claude Code:

```bash
claude mcp add --transport http vink https://vink.yourdomain.com/mcp \
  --header "Authorization: Bearer paste-your-token"
```

Files saved with `save_transcript` and `save_notes` are written on the machine
running vink, by default in `~/Documents/vink`.

### 5. Keep it running

**Linux (systemd).** Create `/etc/systemd/system/vink.service`:

```ini
[Unit]
Description=vink MCP server
After=network-online.target
Wants=network-online.target

[Service]
User=vink
Environment=VINK_AUTH_TOKEN=paste-your-token
Environment=VINK_OUTPUT_DIR=/home/vink/notes
ExecStart=/home/vink/.local/bin/vink mcp --transport http --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now vink
```

Better still, put the token in a file only root can read and reference it with
`EnvironmentFile=` instead of `Environment=`.

**macOS.** Run it in a terminal you leave open, or create a `launchd` agent in
`~/Library/LaunchAgents/` that starts `vink mcp --transport http` at login.

Run `cloudflared` as a service too; see `cloudflared service install`.

### Limits

- The machine must stay on and online.
- Heavy use from one IP address can still be rate-limited by YouTube. For many
  users, combine this with option B.

---

## B. Use a residential proxy

Run vink anywhere and send its YouTube traffic through a proxy that uses
residential IP addresses. **Data-center proxies do not help**, because their IPs
are blocked too.

### Webshare (recommended)

[Webshare](https://www.webshare.io/) rotating residential proxies are supported
natively: vink retries with a fresh IP when one is blocked. Buy a *Residential*
plan (not "Proxy Server" or "Static Residential"), then set:

```bash
VINK_WEBSHARE_USERNAME=your-proxy-username
VINK_WEBSHARE_PASSWORD=your-proxy-password
```

### Any other provider

```bash
VINK_PROXY_URL=http://username:password@proxy.example.com:8080
```

The URL must start with `http://` or `https://` and include a numeric port.
URL-encode special characters in the password (`@` becomes `%40`). vink checks
the format at startup and explains what is wrong.

### Why vink has its own proxy setting

The standard `HTTPS_PROXY` variable also affects other tools. In particular
`uvx` reads it while downloading vink, so a broken or slow proxy can stop
vink from even starting. `VINK_PROXY_URL` and the Webshare settings apply only
to vink's requests to YouTube. If both are set, vink's own setting wins.

### Example: a stdio server on a hosted agent platform

```text
Command:   uvx
Arguments: ["vink", "mcp"]
Environment:
  VINK_WEBSHARE_USERNAME=your-proxy-username
  VINK_WEBSHARE_PASSWORD=your-proxy-password
  VINK_OUTPUT_DIR=/tmp/vink
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `YouTube is blocking requests from this network` | Data-center IP | Option A or B |
| `YouTube is blocking requests through the configured proxy` | The proxy's IPs are blocked | Use a rotating residential plan |
| `Could not reach YouTube through the configured proxy` | Wrong proxy host, port or credentials | Check the proxy settings |
| `Invalid VINK_PROXY_URL: …` | Malformed proxy URL | Follow the hint in the message |
| `The HTTP transport requires an access token` | `VINK_AUTH_TOKEN` not set | Create one (step A.1) |
| HTTP `401 Unauthorized` | Missing or wrong `Authorization` header | Send `Authorization: Bearer <token>` |
| HTTP `421` "Invalid Host header" | `VINK_ALLOWED_HOSTS` does not list the hostname | Add it, or unset the variable |
| MCP client says "Connection closed" right after starting | vink exited during startup | Run the same command in a terminal to see the error |
