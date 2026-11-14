# 0002. Fetch transcripts with youtube-transcript-api, not the YouTube Data API

- Status: Accepted
- Date: 2026-11-14

## Context

vink needs the caption text of arbitrary public videos, which is the same text
YouTube shows in its *Show transcript* panel.

The official YouTube Data API v3 has a `captions.download` endpoint, but it
works only for videos owned by the authenticated user (OAuth). It cannot
download captions of other people's videos, which is vink's main use case. It
also requires a Google Cloud project, an API key and quota management.

YouTube's own player loads captions through internal endpoints: the InnerTube
player API lists caption tracks, and each track has a `timedtext` URL that
returns the text with timings.

## Decision

Use the open-source [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api)
library (MIT). It runs locally, talks directly to YouTube, needs no API key,
and handles track listing, manual versus auto-generated tracks, translation
and many error cases.

Use YouTube's public oEmbed endpoint for title and channel, which also needs no
key.

Keep both behind ports (`TranscriptSource`, `MetadataSource`) so they can be
replaced without touching the rest of the code.

## Consequences

- Zero setup for users: no keys, no quota.
- The endpoints are unofficial and may change. Mitigations: keep the library
  updated (Dependabot), isolate it in one adapter, and run integration tests on
  a schedule to detect breakage early.
- YouTube often blocks requests from cloud-provider IP ranges. vink is meant to
  run on the user's own machine; the adapter reports blocking with a clear
  message. Proxy support can be added through the library's proxy
  configuration.
- Videos without any captions are not supported until a transcription adapter
  (e.g. Whisper) is added.

## Alternatives considered

- **YouTube Data API v3.** Cannot download captions of videos the user does
  not own.
- **Calling InnerTube and timedtext directly with httpx.** No extra dependency,
  but it would mean re-implementing and maintaining what the library already
  does well.
- **yt-dlp subtitle download.** Capable, but much heavier. Reconsider it when
  richer metadata (chapters, duration) or audio download for transcription is
  needed.
- **Paid transcript APIs (e.g. Supadata).** They avoid IP blocking for hosted
  deployments, but add cost and send user data to a third party. They could be
  added later as another `TranscriptSource` adapter.
