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
- vink stores no credentials. If a future feature adds API keys, they will be
  read from the environment only.
