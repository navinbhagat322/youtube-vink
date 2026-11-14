Turn this video transcript into a clean, readable written version in {output_language}.

This must stay as close to word-for-word as possible. It is an edited
transcript, not notes and not a summary.

Rules:

1. Keep everything the speaker says, in the same order. Do not summarize,
   condense or reorder.
2. Fix only what makes speech hard to read: add punctuation and capitalization,
   remove filler words ("um", "uh", "you know"), false starts and accidental
   repetitions, and correct obvious caption recognition errors.
3. If {output_language} differs from the transcript language, translate
   faithfully, sentence by sentence, keeping technical terms, names and code
   identifiers in their original form.
4. Break the text into paragraphs where the speaker changes thought, and add a
   `##` heading whenever the topic clearly changes.
5. Keep the timestamp link at the start of each paragraph, copied from the transcript.
6. If a passage is garbled, write your best reading followed by "(unclear in transcript)".

Process the transcript one part at a time:

- Call `get_video_info` to learn how many parts the transcript has. If a
  `languages` value is needed, pass the same value to every tool call so all
  parts come from the same transcript.
- For each part in order, call `get_chunk` and write its full clean version before
  moving on.
- If asked to save, call `save_notes` with the complete text and suffix "clean".
