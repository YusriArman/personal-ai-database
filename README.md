# Local Notes Companion

Search, connect and pull tasks out of an Obsidian vault, entirely on your own computer.
No cloud API is called at any point; the language model runs locally through
[Ollama](https://ollama.com).

What it does:

- **Search** by exact words (SQLite FTS5), by meaning (local embeddings), or both combined.
- **Connections**: links, backlinks, links to missing notes, and similar notes you have not linked yet.
- **Ask**: answers drawn only from your notes, each claim tied to the passage it came from,
  with a refusal when the notes do not contain the answer.
- **Tasks**: every checkbox in the vault, plus tasks the model finds in your prose, which wait
  for you to accept or reject them.
- **Rescan**: picks up edited, new and deleted notes without re-reading the rest.

Your vault is only ever read. All app state lives in one SQLite file under `data/`.

## Quick start (no model needed)

Requires [uv](https://docs.astral.sh/uv/) and Node 20+.

```
make setup
LNC_PROVIDER=fake make api      # terminal 1
make ui                         # terminal 2, then open http://localhost:5173
```

Open **Index** and press **Scan vault for changes**. This uses the bundled fictional vault in
`demo_vault/` and a built-in stand-in for the model, so you can click through everything.
The stand-in understands no meaning: use it to see the app work, not to judge answer quality.

## Real use (local model)

1. Install Ollama and pull the models: see [docs/MODEL_SETUP.md](docs/MODEL_SETUP.md).
2. Point the app at your vault and start it:

```
LNC_VAULT="$HOME/Documents/MyVault" LNC_PROFILE=m4 make api
make ui
```

Use `LNC_PROFILE=ryzen` on the Ryzen machine. All settings are listed in
[docs/MODEL_SETUP.md](docs/MODEL_SETUP.md).

## Checking it works

```
make test        # 68 backend tests + 5 UI tests, no model needed
make lint
make eval        # deterministic evaluation -> evals/reports/deterministic.md
make eval-live   # needs Ollama -> evals/reports/live-<profile>.md
make experiment  # the note-type classifier
```

## Where to read next

| If you want to… | Read |
|---|---|
| Understand how the pieces fit | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Learn by rebuilding parts of it | [docs/LEARNING_PATH.md](docs/LEARNING_PATH.md) |
| Know what the numbers mean | [docs/DATA_AND_EVALUATION.md](docs/DATA_AND_EVALUATION.md) |
| Fix something that is not working | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| Pick up where the last session stopped | [docs/NEXT_SESSION.md](docs/NEXT_SESSION.md) |
