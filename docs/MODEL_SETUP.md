# Model setup

The app needs two local models served by Ollama: a small **embedding model** (turns text
into vectors for meaning search) and a **chat model** (writes answers and proposes tasks).

## Install and pull

1. Install Ollama from https://ollama.com/download (macOS app, or the Linux/Windows installer).
2. Pull the models for your machine:

| Profile | Machine | Embedding | Chat | Approx. download |
|---|---|---|---|---|
| `m4` | Mac M4 | `nomic-embed-text` | `qwen2.5:7b` | 0.3 GB + 4.7 GB |
| `ryzen` | Ryzen 7 (CPU or modest GPU) | `nomic-embed-text` | `llama3.2:3b` | 0.3 GB + 2.0 GB |

```
ollama pull nomic-embed-text
ollama pull qwen2.5:7b        # m4
ollama pull llama3.2:3b       # ryzen
```

3. Make sure it is running: `ollama list` should print the models. On macOS the menu-bar app
   keeps the server running; elsewhere run `ollama serve`.

These model names are defaults chosen when the project was written. The Ollama library
changes; before relying on them, check https://ollama.com/library for what is current and
what fits your memory. Any embedding model and any chat model Ollama serves will work —
set the variables below, rescan (changing the embedding model re-embeds everything
automatically), and run `make eval-live` to see whether the change helped.

Rule of thumb for memory: a model needs roughly its download size in free RAM (unified memory
on the Mac), plus a couple of GB of headroom.

## Settings

All settings are environment variables, read at start-up (`backend/app/config.py`).

| Variable | Default | Meaning |
|---|---|---|
| `LNC_VAULT` | `demo_vault/` | Folder of markdown notes to index (read only) |
| `LNC_DB` | `data/companion.db` | Where the index is stored |
| `LNC_PROFILE` | `m4` | `m4` or `ryzen`; picks the default models |
| `LNC_EMBED_MODEL` | from profile | Override the embedding model |
| `LNC_CHAT_MODEL` | from profile | Override the chat model |
| `LNC_OLLAMA_URL` | `http://127.0.0.1:11434` | Where Ollama listens |
| `LNC_PROVIDER` | `ollama` | `fake` uses the built-in stand-in (demos, tests) |
| `LNC_TOP_K` | `5` | Passages given to the model per question |
| `LNC_ABSTAIN_THRESHOLD` | `0.35` | Minimum similarity before Ask will answer |

`LNC_ABSTAIN_THRESHOLD` depends on the embedding model: different models put "related" and
"unrelated" text at different similarity levels. `make eval-live` prints a value calibrated
on the dev questions; set it and re-run to confirm.

Use a separate `LNC_DB` for each vault, so the demo index and your real index never mix.

## There is no cloud fallback

Nothing in the code can call a hosted model. If Ollama is not running, the **Index** page
says so, and search by exact words, links and checkbox tasks continue to work.
