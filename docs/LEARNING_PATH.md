# Learning path

The app is small enough to understand completely. This path takes you through it by having
you rebuild its core pieces, in the order data flows through the system.

## How each module works

Every folder in `learning/` has:

- `README.md` — the idea in a paragraph, then the exercise
- `exercise.py` — functions for you to write (they raise `NotImplementedError` until you do)
- `test_<module>.py` — tests that tell you when you are right
- hints inside the README, collapsed, to open one at a time
- `solution.py` — one correct answer
- a pointer to the real source file, which handles more cases than the exercise

From `backend/`:

```
uv run pytest ../learning/01_parsing                          # your code
LEARNING_TARGET=solution uv run pytest ../learning/01_parsing # the reference
```

All 17 exercise tests fail until you write the code; all 17 pass against the solutions.

## The modules

| # | Module | You build | Real source | Skills |
|---|---|---|---|---|
| 1 | `01_parsing` | checkbox and wikilink extraction | `backend/app/ingest/parser.py` | regular expressions, line-by-line state |
| 2 | `02_chunking` | greedy paragraph packing | `backend/app/ingest/chunker.py` | string handling, edge cases |
| 3 | `03_cosine_search` | vector normalisation and top-k search | `backend/app/retrieve/search.py` | NumPy, linear algebra basics |
| 4 | `04_rank_fusion` | reciprocal rank fusion | `backend/app/retrieve/search.py` | dictionaries, sorting with keys |
| 5 | `05_citations` | citation validation | `backend/app/answer/qa.py` | checking model output with code |
| 6 | `06_metrics` | recall@k, MRR, precision/recall/F1 | `backend/app/evaluate/metrics.py` | evaluation thinking |

Suggested pace: one module per sitting. Do them in order; 3 and 4 build on each other.

## After each module: read the real thing

The exercise is a simplified version. Open the real source and answer:

1. What input does the real code handle that my version would get wrong?
2. Which test in `backend/tests/` covers that case? Run just that test.
3. Break the real code on purpose (change a `<=` to `<`, delete a line), run `make test`,
   and see which test catches it. Then undo the change.

Step 3 is the fastest way to learn what a test suite is for.

## Reconstruction tasks (no scaffolding)

Once the six modules pass, try these against the real codebase. Each has tests already, so
you know when you are done. Work on a git branch so `git diff main` shows your version
against the original.

1. **Rewrite `keyword_search`** (`backend/app/retrieve/search.py`). Delete the body, keep the
   signature. Passing: `uv run pytest tests/test_search.py`. You will need the SQLite FTS5
   documentation for `MATCH`, `bm25()` and `snippet()`.
2. **Rewrite `resolve_all_links`** (`backend/app/connect/links.py`). Passing:
   `uv run pytest tests/test_links.py`.
3. **Rewrite `sync_checkbox_tasks`** (`backend/app/tasks/extract.py`). Passing:
   `uv run pytest tests/test_tasks.py`. The hard part is what happens when a checkbox is
   ticked, reworded or removed between scans.
4. **Rewrite `rescan`** (`backend/app/index/indexer.py`). Passing:
   `uv run pytest tests/test_indexer.py tests/test_api.py`. This is the largest one.

## Experiments that teach evaluation

Each of these changes one thing and measures the effect with `make eval` or `make eval-live`.
Write down your prediction first.

- Change `max_chars` in `chunk_note` from 1200 to 300, then to 4000. What happens to
  recall@5, and why would very large chunks hurt meaning search?
- Change the BM25 column weights in `keyword_search` from `3.0, 2.0, 1.0` to `1.0, 1.0, 1.0`.
- Change `RRF_K` from 60 to 1. Which queries change rank?
- Swap the embedding model (`LNC_EMBED_MODEL`) and compare the paraphrase rows.
- Reword the Q&A system prompt in `qa.py` and see whether "wrongly refused" or
  "correctly refused" moves. Use the dev split to choose, the held-out split to judge.
- Run the classifier experiment (`experiments/note_classifier/README.md`) and work through
  its "things to try".

## Where this leads

| Next step | Why it follows from this project |
|---|---|
| A cross-encoder re-ranker on the top 20 results | The standard next gain after hybrid search; you already have the eval to prove it helps |
| Evaluate on your own vault with your own questions | The demo scores do not transfer; writing gold data is a core skill |
| Replace brute-force search with an ANN index (e.g. sqlite-vec, FAISS) | Learn when approximate search is worth its complexity, by measuring the speed/recall trade |
| Streaming answers over server-sent events | Real LLM apps stream; teaches async Python and incremental UI |
| An LLM-as-judge for answer correctness | Substring matching is crude; learn the method and its own failure modes |
| Fine-tune or few-shot the task extractor on your accept/reject decisions | Your review queue is a labelled dataset you are already creating |
