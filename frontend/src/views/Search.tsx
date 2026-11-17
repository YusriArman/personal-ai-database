import { type FormEvent, useState } from "react";
import { api } from "../api";
import { messageOf } from "../lib/hooks";
import { splitMarks } from "../lib/text";
import type { Hit, Mode } from "../types";

const MODES: { mode: Mode; label: string; hint: string }[] = [
  { mode: "hybrid", label: "Both", hint: "Combines exact words and meaning" },
  { mode: "keyword", label: "Exact words", hint: "Finds the words you typed. Works without the model" },
  { mode: "semantic", label: "Meaning", hint: "Finds notes about the same idea in different words" },
];

export function Snippet({ text }: { text: string }) {
  return (
    <>
      {splitMarks(text).map((part, i) =>
        part.kind === "mark" ? <mark key={i}>{part.text}</mark> : <span key={i}>{part.kind === "text" ? part.text : ""}</span>,
      )}
    </>
  );
}

export function SearchView({ modelReady }: { modelReady: boolean }) {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<Mode>("hybrid");
  const [results, setResults] = useState<Hit[] | null>(null);
  const [searched, setSearched] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(nextMode: Mode, text = query) {
    if (!text.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const response = await api.search(text, nextMode);
      setResults(response.results);
      setSearched(text);
    } catch (reason) {
      setResults(null);
      setError(messageOf(reason));
    } finally {
      setBusy(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void run(mode);
  }

  function choose(next: Mode) {
    setMode(next);
    void run(next);
  }

  return (
    <section>
      <h1>Search your notes</h1>
      <form onSubmit={submit} className="query">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Try: motor driver overheating"
          aria-label="Search query"
          autoFocus
        />
        <button type="submit" disabled={busy || !query.trim()}>
          {busy ? "Searching…" : "Search"}
        </button>
      </form>
      <div className="segmented" role="radiogroup" aria-label="How to search">
        {MODES.map((m) => (
          <button
            key={m.mode}
            type="button"
            role="radio"
            aria-checked={mode === m.mode}
            title={m.hint}
            onClick={() => choose(m.mode)}
          >
            {m.label}
          </button>
        ))}
      </div>
      {!modelReady && mode !== "keyword" && (
        <p className="note">
          The local model is not ready, so only “Exact words” will work. See the{" "}
          <a href="#/status">Index</a> page.
        </p>
      )}
      {error && <p className="error" role="alert">{error}</p>}
      {results && results.length === 0 && (
        <p className="empty">
          Nothing matched “{searched}”.{" "}
          {mode === "keyword" ? "Try “Meaning” to match different wording." : "Try other words."}
        </p>
      )}
      {results && results.length > 0 && (
        <ol className="results">
          {results.map((hit) => (
            <li key={hit.chunk_id}>
              <a className="result-title" href={`#/note/${hit.note_id}`}>
                {hit.title}
              </a>
              {hit.heading && <span className="where">in {hit.heading}</span>}
              <p className="reading">
                <Snippet text={hit.snippet || hit.text.slice(0, 240)} />
              </p>
              <p className="meta">
                {hit.path}
                {hit.similarity !== null && `, similarity ${hit.similarity.toFixed(2)}`}
              </p>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
