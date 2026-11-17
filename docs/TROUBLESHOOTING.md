# Troubleshooting

Start with the **Index** page in the app, or `curl http://127.0.0.1:8000/api/status`.
It reports the vault path, counts and what is wrong with the model, if anything.

| What you see | Cause | Fix |
|---|---|---|
| "The app's server is not running" | The API is not started, or not on port 8000 | `make api` in its own terminal; leave it running |
| "Ollama is not reachable … Start it with `ollama serve`" | Ollama is not running | Open the Ollama app (macOS) or run `ollama serve`. Check with `ollama list` |
| "Missing models: …" | A model in your profile is not downloaded | `ollama pull <name>`; names in [MODEL_SETUP.md](MODEL_SETUP.md) |
| "No embeddings in the index yet" | Notes were scanned while the model was down | Start Ollama, then **Scan vault for changes**. Only the missing embeddings are computed |
| Index page shows "N not yet read by the model" | Same as above, partially | Scan again with Ollama running |
| "Vault folder not found" | `LNC_VAULT` points nowhere | Fix the path; quote it if it contains spaces |
| "Query embedding size does not match the index" | Embedding model was changed without a rescan | Scan again; everything is re-embedded for the new model |
| Ask refuses questions you know are answerable | Abstain threshold too high for your embedding model | Run `make eval-live`, set `LNC_ABSTAIN_THRESHOLD` to the calibrated value |
| Ask answers questions it should refuse | Threshold too low | Same procedure; raise it |
| First answer takes a long time | Ollama is loading the model into memory | Normal; later answers are faster. A smaller chat model helps on the Ryzen machine |
| "Find tasks in my writing" is slow | One model call per changed note | Normal on first run; afterwards only edited notes are re-read |
| A rejected task came back | The sentence it was based on was edited, which makes it a new sentence | Reject it again; unchanged sentences never return |
| Port 5173 or 8000 already in use | Another process holds it | `make api` uses 8000; run `uvicorn … --port 8001` and change the proxy in `frontend/vite.config.ts` |
| `make test` fails right after cloning | Dependencies not installed | `make setup` |

## Starting over

The index is disposable. Stop the API, delete `data/companion.db`, start the API and scan
again. Your vault is untouched. The only thing lost is your accept/reject decisions on
proposed tasks, so use **Show as checklist** first if you want to keep them.

## Confirming nothing leaves the machine

The backend makes HTTP requests to exactly one address, `LNC_OLLAMA_URL`
(`backend/app/providers/ollama.py`), which defaults to this computer. The UI loads no
remote fonts, scripts or analytics. To check for yourself, turn off Wi-Fi: everything
keeps working.
