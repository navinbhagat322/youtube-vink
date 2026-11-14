Turn this video transcript into complete, detailed study notes written in {output_language}.

These are NOT a summary. A reader who never watches the video must be able to
learn everything the speaker taught from these notes alone.

Rules:

1. Keep every point, definition, example, number, step, warning and aside the
   speaker mentions, in the same order they mention them. Do not skip, merge
   away or shorten anything that carries information.
2. Rewrite spoken language into clear written language: remove filler words,
   false starts and repetition, but never remove content.
3. Where the speaker explains a concept briefly or assumes knowledge, add a short
   clarifying explanation so the notes stand on their own. Mark anything you add
   that the speaker did not say with "(note: ...)".
4. Structure: a `##` heading for each topic the speaker moves through, `###` for
   sub-topics, numbered lists for steps or sequences, bullet lists for related
   points, tables when the speaker compares things, and fenced code blocks for
   any code, commands or formulas.
5. Start each `##` section with the timestamp link of the paragraph where that
   topic begins, copied from the transcript, e.g. `[12:30](https://youtu.be/ID?t=750)`.
6. Keep technical terms, names and code identifiers in their original form even
   when writing in another language.
7. Do not invent facts. If the transcript is unclear or garbled (common with
   auto-generated captions), write your best reading followed by "(unclear in
   transcript)".

Process the transcript one part at a time:

- Call `get_video_info` to learn how many parts the transcript has. If a
  `languages` value is needed, pass the same value to every tool call so all
  parts come from the same transcript.
- For each part in order, call `get_chunk` and write the full notes for that part
  before moving on. Continue the heading structure from the previous part rather
  than starting over, and do not repeat content already covered.
- After the last part, add a short "Key takeaways" section and a glossary of the
  important terms the speaker used.
- If asked to save, call `save_notes` with the complete notes.
