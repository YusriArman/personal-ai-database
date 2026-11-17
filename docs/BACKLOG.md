# Backlog

Ideas that were deliberately left out, roughly in the order I would do them. None is
needed for the app to work as described.

## Worth doing next

- **Evaluate on a real vault.** Hand-write 15–20 questions and relevance labels for your
  own notes. Everything below should be judged against that, not the demo vault.
- **Re-rank the top results.** A small cross-encoder over the top 20 hybrid hits usually
  improves ordering. Measure with nDCG@10 before and after.
- **Streaming answers.** Ask currently waits for the whole answer. Ollama can stream;
  the API would need server-sent events and the UI incremental rendering.
- **Search filters.** Restrict by folder, tag or date range. The data is already in `notes`.
- **Watch the vault.** Rescan automatically when files change instead of pressing a button.

## Quality

- **Sentence splitting** for task proposals is a regex on `. ! ?`. It mis-splits
  abbreviations ("Dr. Lim" is handled only because the gold data was checked against it).
- **Chunk overlap.** Chunks do not overlap, so a fact spanning a section boundary can be
  split. Try a one-sentence overlap and measure.
- **Answer correctness by substring** can be fooled. An LLM judge, or exact-match on
  extracted values, would be stricter.
- **Ambiguous wikilinks.** Two notes with the same file name in different folders: the
  first one wins. Obsidian's own shortest-path rule is not implemented.
- **Aliases.** Frontmatter `aliases:` are not used when resolving links.

## Scale

- Embeddings are loaded from SQLite on every semantic query. Fine for thousands of chunks;
  cache the matrix in memory, or move to an ANN index, beyond roughly 100k.
- Task proposals make one model call per changed note, sequentially.

## Not planned

- Writing back to the vault (ticking checkboxes, inserting links). Read-only is a safety
  property, not a missing feature.
- Any hosted model, sync service or account.
