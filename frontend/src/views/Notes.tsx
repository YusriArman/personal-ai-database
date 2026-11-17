import { useState } from "react";
import { api } from "../api";
import { useLoad } from "../lib/hooks";

export function NotesView() {
  const { data: notes, error } = useLoad(api.notes);
  const [filter, setFilter] = useState("");
  if (error) return <p className="error" role="alert">{error}</p>;
  if (!notes) return <p className="meta">Loading notes…</p>;

  const needle = filter.trim().toLowerCase();
  const shown = notes.filter(
    (n) =>
      !needle ||
      n.title.toLowerCase().includes(needle) ||
      n.tags.some((t) => t.toLowerCase().includes(needle)),
  );
  const folders = new Map<string, typeof notes>();
  for (const note of shown) {
    const folder = note.path.includes("/") ? note.path.slice(0, note.path.lastIndexOf("/")) : "Vault";
    folders.set(folder, [...(folders.get(folder) ?? []), note]);
  }

  return (
    <section>
      <h1>All notes</h1>
      {notes.length === 0 ? (
        <p className="empty">
          No notes indexed yet. Open the <a href="#/status">Index</a> page and scan your vault.
        </p>
      ) : (
        <>
          <input
            type="search"
            className="filter"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter by title or tag"
            aria-label="Filter notes"
          />
          {shown.length === 0 && <p className="empty">No note title or tag contains “{filter}”.</p>}
          {[...folders.entries()].map(([folder, items]) => (
            <div key={folder}>
              <h2>{folder}</h2>
              <ul className="note-list">
                {items.map((note) => (
                  <li key={note.id}>
                    <a href={`#/note/${note.id}`}>{note.title}</a>
                    {note.tags.map((tag) => (
                      <span key={tag} className="tag">#{tag}</span>
                    ))}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </>
      )}
    </section>
  );
}
