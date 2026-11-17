# Plan

The plan this project was built from, kept for reference. It was reconstructed from a
summary of the original brief, so anything the summary left out is not reflected here.
Status of each part is in [NEXT_SESSION.md](NEXT_SESSION.md).

## Context

Yusri wants a local-only app that searches, connects and extracts tasks from a personal
Obsidian vault, built as a learning vehicle (Python, ML, data, AI integration) before
internships. Requirements carried over from the summary:

- No cloud APIs at runtime; no cloud fallback. Local models via Ollama.
- Mac M4 is the primary target, Ryzen 7 the secondary; both must be usable.
- Evaluation is first-class: honest metrics, deterministic tests separated from
  variable live-model tests, no inflated fixture scores.
- Learning material accompanies the build (exercises, hints, reference solutions).
- No intentional TODOs in the finished version; blockers reported with recovery steps.

## Architecture

```
local-notes-companion/
  backend/            Python 3.12, FastAPI, uv, pytest, ruff
    app/
      ingest/         vault scanner, markdown parser, chunker
      index/          SQLite schema, FTS5, embedding store
      retrieve/       keyword, semantic, hybrid (RRF)
      connect/        wikilinks, backlinks, suggested links
      answer/         grounded Q&A with citations + abstention
      tasks/          checkbox parser, LLM task proposals, review queue
      providers/      ModelProvider protocol: OllamaProvider, FakeProvider
      api/            FastAPI routes
    tests/
  frontend/           React + TypeScript + Vite, Vitest
  demo_vault/         ~40 fictional Obsidian notes (no real personal data)
  evals/              golden sets, runners, committed reports
  experiments/        TF-IDF + logistic regression classifier
  learning/           exercises, hints, reference solutions
  docs/
```

Key design choices:
- **Vault is read-only.** The app never writes into the Obsidian vault; all state is in
  one SQLite file. Accepted tasks live in SQLite and can be exported as markdown.
- **SQLite for everything**: notes, chunks, links, FTS5 keyword index, embeddings as
  float32 blobs. Semantic search is brute-force cosine in NumPy — correct and fast at
  personal-vault scale, and readable for learning. No vector DB.
- **Incremental rescans** by content hash + mtime: changed notes re-chunk and re-embed,
  deleted notes are removed, unchanged notes are skipped.
- **Provider seam.** `ModelProvider` (embed, generate) has `OllamaProvider` for real use
  and a deterministic `FakeProvider` (hash-based embeddings, scripted generations) so the
  whole test suite runs without a model.
- **Models** (names and sizes verified against the Ollama library at setup time, recorded
  in `MODEL_SETUP.md`): one small embedding model, one ~7–8B chat model for the M4, and
  a ~3B chat model as the Ryzen/CPU profile. Selected by a config profile, never by
  falling back to a cloud model. If Ollama is down, the UI says so and keyword search
  keeps working.
- **Grounded Q&A**: retrieve top-k chunks, prompt with numbered sources, require
  citations, validate every citation refers to a retrieved chunk, and abstain ("not in
  your notes") when retrieval scores are below a threshold.
- **Task extraction in two tiers**: deterministic `- [ ]` / `- [x]` parsing (exact), and
  LLM-proposed implicit tasks ("I need to email…") that land in a review queue with the
  source sentence shown; nothing is accepted without the user's click.

## Milestones (vertical slices, each ends runnable and tested)

1. **Skeleton + demo vault** — repo layout, uv/Vite setup, fictional vault with
   frontmatter, tags, wikilinks, checkboxes, implicit tasks and a few deliberately hard
   cases (near-duplicate notes, unanswerable topics).
2. **Ingest + keyword search** — scanner, parser, chunker, SQLite/FTS5, `/search`,
   minimal React search page with snippets.
3. **Semantic + hybrid retrieval** — embeddings via provider, cosine search, reciprocal
   rank fusion; UI toggle for keyword / semantic / hybrid.
4. **Connections** — outgoing links, backlinks, broken links, and "related but
   unlinked" suggestions from embedding neighbours; note detail page.
5. **Grounded Q&A** — answer endpoint with citations and abstention; UI shows the
   answer beside the exact source chunks.
6. **Task review** — two-tier extraction, review queue (accept / edit / reject),
   task list with links back to the source note.
7. **Rescan** — incremental re-index, status panel (notes indexed, stale, model health).
8. **Evaluations** — see below.
9. **Supervised experiment** — see below.
10. **Learning path + docs + acceptance walkthrough.**

## Evaluation

Golden data lives in `evals/` and is written before tuning; a held-out portion of
queries is never used for threshold or prompt tuning.

| Area | Metric | Type |
|---|---|---|
| Retrieval (keyword / semantic / hybrid) | recall@5, MRR, nDCG@10 | deterministic given a fixed embedding model |
| Checkbox task parsing | precision / recall / F1 | deterministic |
| LLM task proposals | precision / recall / F1 against labelled sentences | live, variable |
| Q&A citations | % of citations pointing to a retrieved chunk | deterministic check on live output |
| Q&A correctness | key-fact match against reference answers | live, variable |
| Q&A abstention | correct refusals on unanswerable questions | live, variable |

Honesty rules: live-model evals run N≥3 times and report mean and spread, with the model
name, quantisation and hardware in the report; deterministic and live results are in
separate tables and never averaged together; reports state that a ~40-note fictional
vault is small and that scores do not predict performance on a real vault; failures are
listed by example, not just aggregated. `pytest` covers deterministic tests only;
`make eval-live` is a separate command.

## Supervised-learning experiment (separate from the app)

`experiments/note_classifier/`: classify demo notes by type (e.g. meeting / project /
journal / reference) with TF-IDF + logistic regression in scikit-learn. Stratified
split, majority-class and keyword-rule baselines, cross-validation, confusion matrix,
top weighted terms per class, and a written note on what the tiny dataset can and
cannot show. Not wired into the app.

## Learning path

`learning/` holds one module per milestone: a concept note, an exercise that asks Yusri
to rebuild a small piece (e.g. chunker, RRF, cosine search, citation validator, F1
scorer) against provided tests, graded hints, and a reference solution that points at
the real source file. Ordered from Python fundamentals to retrieval to evaluation.

## Documentation

`README`, `PLAN`, `ARCHITECTURE`, `MODEL_SETUP`, `LEARNING_PATH`, `DATA_AND_EVALUATION`,
`TROUBLESHOOTING`, `BACKLOG`, `PORTFOLIO_NOTES`, `NEXT_SESSION` — all under `docs/`
except `README`.

## Environment limits to plan around

- A cloud session can build and run the full deterministic suite (FakeProvider) and the
  UI. Live-model evals and performance checks need Ollama on the Mac M4 and the Ryzen
  machine; if they cannot be run from the build session, they are reported as "not run"
  with the exact commands, never filled in with estimated numbers.
- The real vault never leaves the Mac and is never committed; `.gitignore` covers the
  SQLite file and any vault path config.

## Verification

1. `uv run pytest` and `npm test` pass with no model running.
2. `uv run ruff check`, `tsc --noEmit`, `npm run build` are clean.
3. Acceptance walkthrough on the demo vault, driven in a real browser: index → keyword,
   semantic and hybrid search → open a note and its links/backlinks/suggestions → ask an
   answerable and an unanswerable question → review extracted tasks → edit, add and
   delete a note, rescan, confirm results change accordingly.
4. `make eval` writes the deterministic report; `make eval-live` on the Mac writes the
   live report with model and hardware recorded.
5. Kill Ollama and confirm the app degrades to keyword search with a clear message.
6. Run the classifier experiment end to end and check the report matches its output.
