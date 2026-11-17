# Next session

Where the project stands and what to do first.

## State

| Part | Status |
|---|---|
| Ingest, index, incremental rescan | Done, tested |
| Keyword, meaning and hybrid search | Done, tested |
| Links, backlinks, missing links, suggestions | Done, tested |
| Grounded Q&A with citation checks and refusal | Done, tested |
| Checkbox tasks and reviewed model proposals | Done, tested |
| React UI (Search, Ask, Tasks, Notes, Index) | Done; walked through in a browser with the fake model and with a real one |
| Deterministic evaluation | Done: `evals/reports/deterministic.md` |
| Live evaluation on a cloud CPU, `llama3.2:3b` | Done: `evals/reports/live-cloud-cpu.md` |
| Live evaluation on the Mac M4 | **Not run** |
| Live evaluation on the Ryzen 7 | **Not run** |
| `qwen2.5:7b` (the `m4` profile's chat model) | **Never run**; the name is an unverified default |
| Classifier experiment | Done: `experiments/note_classifier/` |
| Learning modules | Done: 6 modules, solutions verified |
| Use on a real vault | **Not done** |

Checks at hand-over: 72 backend tests and 5 UI tests pass; `ruff` and `tsc` are clean.

## Do first, on the Mac

```
git clone https://github.com/YusriArman/personal-ai-database && cd personal-ai-database
make setup && make test
```

1. Follow `docs/MODEL_SETUP.md`: install Ollama, check the model names are still current,
   pull the two models.
2. `LNC_PROFILE=m4 make eval-live` and commit `evals/reports/live-m4.md`. Compare its task
   and Q&A numbers with the cloud report: does the 7B model fix task precision?
3. Set `LNC_ABSTAIN_THRESHOLD` to the value the report calibrates (0.66 with
   `nomic-embed-text` on the cloud run; the default 0.35 never triggers with that model, so
   refusals currently rely on the model alone).
4. Repeat with `LNC_PROFILE=ryzen` on the Ryzen machine.
5. Point `LNC_VAULT` at a copy of a few real notes, with a separate `LNC_DB`, and use it.

## Known weak points

- Task proposals: about three in four are wrong with the 3B model.
- Scores are fitted to the demo vault (see DATA_AND_EVALUATION.md, "What changed").
- On the demo vault, meaning search alone beat hybrid; the default has not been re-examined.
- Not verified on macOS or Windows at all: everything so far ran on Linux.

## Then

Start the learning path at `learning/01_parsing/README.md`. Ideas for extending the app are
in `BACKLOG.md`.
