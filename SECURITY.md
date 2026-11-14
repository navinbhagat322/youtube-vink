# Security Policy

## Supported versions

Only the latest release receives security fixes while the project is in `0.x`.

## Reporting a vulnerability

Please do not open a public issue for security problems.

Report privately through GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
on this repository. Include:

- a description of the issue and its impact,
- steps to reproduce,
- the affected version (`vink --version`).

You can expect an acknowledgement within 7 days. Once a fix is released, we
will credit you in the release notes unless you prefer otherwise.

## Scope notes

- vink writes files only inside the configured output and cache directories.
  File names derived from video titles are sanitized, and a write that would
  escape the output directory is refused. Report any way around this.
- Transcript text and video titles are treated as untrusted data. They are
  rendered as escaped text and never executed.
- `vink mcp --transport http` refuses to start without an access token
  (`VINK_AUTH_TOKEN`), except with `--insecure-no-auth` on a loopback address.
  Tokens are compared in constant time. Report any way to reach the MCP
  endpoint without a valid token.
- Proxy URLs and passwords are never printed in error messages or logs.
- vink stores no credentials. Tokens and proxy credentials are read from the
  environment only.
