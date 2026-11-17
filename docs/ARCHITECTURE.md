# Architecture

```
 Obsidian vault (read only)
        │  scan: hash every .md file
        ▼
 ingest/   parser  → title, tags, links, checkboxes
           chunker → sections of at most ~1200 characters
        │
        ▼
 index/    one SQLite file
           notes · chunks (+ embedding blob) · chunks_fts (FTS5) · links · tasks
        │
        ├── retrieve/  keyword (BM25) · semantic (cosine) · hybrid (RRF)
        ├── connect/   links, backlinks, broken links, similar-but-unlinked
        ├── answer/    retrieve → prompt with numbered sources → check citations
        └── tasks/     checkboxes (exact) · model proposals (reviewed)
        │
        ▼
 api/      FastAPI, JSON over http://127.0.0.1:8000
        ▼
 frontend/ React + TypeScript (Vite), http://localhost:5173
```

All model calls go through `providers/`: `OllamaProvider` for real use, `FakeProvider`
for tests and demos.

## Decisions and why

**One SQLite file, no vector database.** A personal vault is thousands of chunks, not
millions. Comparing a query against every stored vector with NumPy takes milliseconds, and
the whole retrieval path stays short enough to read in one sitting
(`backend/app/retrieve/search.py`). If a vault ever grows past a few hundred thousand chunks,
this is the part to replace.

**The vault is never written to.** Indexing reads files; accepted tasks live in SQLite and
are exported as text you copy yourself. A bug in this app cannot damage your notes.

**Incremental rescans by content hash.** Each note's SHA-256 is stored. Unchanged notes are
skipped, changed notes are re-chunked and re-embedded, missing notes are removed. Links are
re-resolved every time, because adding or deleting one note can repair or break links in
others (`backend/app/index/indexer.py`).

**A provider seam.** The app talks to a `ModelProvider` with three methods: `embed`,
`generate`, `health`. Tests use `FakeProvider`, so the full suite runs in about a second with
no model, and a test can script exactly what the "model" says, including nonsense.

**No cloud fallback, visible degradation.** If Ollama is down, keyword search, links and
checkbox tasks keep working. Meaning search, Ask and task proposals return an explicit error;
the app never quietly substitutes keyword results under a "hybrid" label.

**Citations are checked by code.** The model is told to cite sources as `[n]`. Afterwards
`check_citations` verifies each number refers to a passage that was actually retrieved.
Invalid markers are removed and an answer with no valid citation is shown with a warning
(`backend/app/answer/qa.py`).

**Two ways to refuse.** Before calling the model, the best passage must reach a similarity
threshold; otherwise the app refuses without generating anything. If the model is called, it
can still reply `NOT_IN_NOTES`. A reply that is only a citation marker with no words is
treated as no answer rather than shown. The threshold depends on the embedding model and is
calibrated by `make eval-live` on the dev split only.

**Model proposals need evidence and approval.** The model is asked a yes/no question about
one sentence at a time, so a proposal is always a sentence that really is in the note. Only
an exact `{"action_item": true}` counts as yes; anything malformed counts as no. Proposals
are *pending* until you accept them. Checkboxes are your own explicit tasks, so they are
accepted as they are. (The first design sent the whole note and asked for a list; a small
model then listed almost every sentence. See DATA_AND_EVALUATION.md.)

**Review decisions survive edits.** A task is keyed by note path, source and normalised
text, not by a database id that changes on re-index. Rejecting a proposal and then editing
the note does not bring it back.

## Data model

| Table | Holds |
|---|---|
| `notes` | path, title, content hash, body, tags, frontmatter, hash last analysed for tasks |
| `chunks` | note id, position, heading trail, text, embedding (float32, unit length), model name |
| `chunks_fts` | FTS5 index over title, heading and text (Porter stemming) |
| `links` | source note, link text, resolved target (NULL when the target does not exist) |
| `tasks` | key, note path, source (checkbox/model), text, evidence, done, status, orphaned |

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/status` | counts, model health, settings in use |
| POST | `/api/rescan` | sync the index with the vault |
| GET | `/api/search?q=&mode=&k=` | mode is `keyword`, `semantic` or `hybrid` |
| GET | `/api/notes`, `/api/notes/{id}` | list; one note with its connections and tasks |
| GET | `/api/links/broken` | every link to a missing note |
| POST | `/api/ask` | grounded answer with sources |
| GET | `/api/tasks?status=` | tasks |
| POST | `/api/tasks/propose` | ask the model to find tasks in notes not yet analysed |
| PATCH | `/api/tasks/{id}` | accept, reject or reword |
| GET | `/api/tasks/export` | accepted tasks as a markdown checklist |

Error codes: 400 bad input, 404 not found, 409 nothing embedded yet, 503 local model unreachable.
