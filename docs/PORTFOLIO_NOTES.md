# Portfolio notes

Material for describing this project in an application or interview. Everything here is
backed by something in the repository; check a number against its report before quoting it.

## One-line description

A local-only search and question-answering tool for an Obsidian vault: hybrid retrieval,
answers with verified citations, reviewed task extraction, and an evaluation suite that
reports its own weaknesses.

## What makes it more than a tutorial project

- **Evaluation is part of the product.** Gold data with dev and held-out splits, baselines,
  deterministic and live-model results kept in separate reports, repeated runs with spread.
- **The model is checked by code.** Citations are validated against what was retrieved; a
  malformed model reply can never create a task; the app refuses rather than guesses.
- **Failure is designed for.** With the model off, keyword search, links and checkbox tasks
  keep working and the UI says exactly what is unavailable.
- **Testable without a model.** A provider interface with a deterministic fake lets 72 tests
  run in about a second.

## Three stories worth telling

**1. The evaluation caught what the tests could not.** All tests passed, then the first run
against a real 3B model showed task extraction proposing almost every sentence (precision
0.05) and a third of answers being a bare "[1]". Unit tests with a fake model cannot see
this. I changed the design (one yes/no question per sentence) and F1 rose from 0.09 to 0.39.
The before and after reports are both in `evals/reports/`.

**2. The model still loses to a regex, and the docs say so.** A five-phrase keyword rule
scores F1 0.70 on task extraction; the model scores 0.39 (recall 1.0, precision 0.24). I
kept the model because in a review queue a missed task is invisible and a wrong one costs a
click, and wrote down that this is a judgement and not a measured win.

**3. A classifier that lost to an if-statement.** TF-IDF + logistic regression on note type
scored 0.625 against 0.875 for a hand-written rule, with 40 notes. The write-up explains
why (8 examples per class), and shows the model's strongest "meeting" feature was the year
in the title.

## Honest limits to state up front

- Measured on a 40-note fictional vault, on a cloud CPU. Not yet on the target hardware.
- Prompts were revised after seeing results on the same data, so current scores are fitted.
- Answer correctness is substring matching.

## Skills demonstrated

Python (FastAPI, SQLite/FTS5, NumPy, pytest), information retrieval (BM25, embeddings,
rank fusion), LLM integration with output validation, evaluation design, scikit-learn,
React and TypeScript.

## Before showing it to anyone

Run `make eval-live` on your own machine and replace the cloud numbers with yours, write
questions for a slice of your real vault, and be ready to explain any function in
`backend/app/` — the learning path exists so that you can.
