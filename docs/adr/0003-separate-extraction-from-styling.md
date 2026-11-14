# 0003. Keep transcript extraction independent of AI styling

- Status: Accepted
- Date: 2026-11-14

## Context

vink's purpose is detailed notes, not summaries. Notes require an AI model.
Extracting and cleaning a transcript does not. When generic tools combine both
steps into one AI call over a whole transcript, the result gets compressed
into a summary because of output-length limits.

## Decision

Split the pipeline into two independent stages:

1. **Extraction** (deterministic, no AI): fetch captions, clean them, build
   paragraphs, split them into time-based chunks, and render Markdown. This is
   what the CLI and the MCP tools provide.
2. **Styling** (AI): turn each chunk into notes in a chosen style and language.
   In the MVP the MCP client's own model does this, guided by prompt templates
   in `vink/styles/`. A future adapter may call a model API directly for batch
   use.

Chunks never split a paragraph, and very short trailing chunks are merged into
the previous one.

## Consequences

- Extraction is free, fast, testable and useful on its own: a clean
  timestamped transcript.
- Processing each chunk separately keeps every part within the model's output
  budget, which is how "no detail dropped" is achieved.
- Output language is a styling concern. vink can extract in the spoken
  language and let the model write notes in English, Hindi, Hinglish or any
  other language.
- Note quality depends on the client's model and on the prompt templates,
  which can be improved without code changes.

## Alternatives considered

- **Call an LLM API inside vink for every request.** Simple for end users, but
  requires an API key, adds cost, and ties the core to one provider. Kept as a
  future optional adapter.
- **Send the whole transcript in one request.** Simplest, but produces
  summaries for anything longer than a few minutes, which is the problem vink
  exists to solve.
