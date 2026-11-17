import { api } from "../api";
import { useLoad } from "../lib/hooks";
import { parseBlocks, splitWikilinks } from "../lib/text";
import type { NoteDetail, NoteRef } from "../types";

function Inline({ text, note }: { text: string; note: NoteDetail }) {
  const byName = new Map(note.outgoing.map((n) => [n.title.toLowerCase(), n]));
  for (const n of note.outgoing) {
    byName.set(n.path.replace(/\.md$/, "").split("/").pop()!.toLowerCase(), n);
  }
  return (
    <>
      {splitWikilinks(text).map((part, i) => {
        if (part.kind !== "link") return <span key={i}>{part.kind === "text" ? part.text : ""}</span>;
        const target = byName.get(part.target.toLowerCase());
        return target ? (
          <a key={i} href={`#/note/${target.id}`}>{part.label}</a>
        ) : (
          <span key={i} className="broken" title="No note with this name exists">{part.label}</span>
        );
      })}
    </>
  );
}

function RefList({ title, items, empty }: { title: string; items: NoteRef[]; empty: string }) {
  return (
    <div>
      <h2>{title}</h2>
      {items.length === 0 ? (
        <p className="empty">{empty}</p>
      ) : (
        <ul className="refs">
          {items.map((n) => (
            <li key={n.id}>
              <a href={`#/note/${n.id}`}>{n.title}</a>
              {n.similarity !== undefined && (
                <span className="meta"> similarity {n.similarity.toFixed(2)}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function NoteView({ id }: { id: number }) {
  const { data: note, error } = useLoad(() => api.note(id), id);
  if (error) return <p className="error" role="alert">{error}</p>;
  if (!note || note.id !== id) return <p className="meta">Loading note…</p>;
  const blocks = parseBlocks(note.body);
  const hasTitleHeading = blocks[0]?.kind === "heading" && blocks[0].level === 1;

  return (
    <section className="note-layout">
      <article className="reading">
        {!hasTitleHeading && <h1>{note.title}</h1>}
        <p className="meta ui">
          {note.path}
          {note.tags.map((tag) => (
            <span key={tag} className="tag">#{tag}</span>
          ))}
        </p>
        {blocks.map((block, i) => {
          if (block.kind === "heading") {
            const Tag = block.level === 1 ? "h1" : block.level === 2 ? "h2" : "h3";
            return <Tag key={i}>{block.text}</Tag>;
          }
          if (block.kind === "code") return <pre key={i}>{block.text}</pre>;
          if (block.kind === "item") {
            return (
              <p key={i} className={`item ${block.checkbox}`}>
                <span className="box" aria-hidden="true">
                  {block.checkbox === "done" ? "✓" : block.checkbox === "none" ? "•" : ""}
                </span>
                <span>
                  <Inline text={block.text} note={note} />
                </span>
              </p>
            );
          }
          return (
            <p key={i}>
              <Inline text={block.text} note={note} />
            </p>
          );
        })}
      </article>
      <aside aria-label="Connections">
        <RefList title="Links to" items={note.outgoing} empty="This note links to nothing." />
        <RefList title="Linked from" items={note.backlinks} empty="No other note links here." />
        <RefList
          title="Similar, not linked yet"
          items={note.suggestions}
          empty="No suggestions. They need the local model to have read your notes."
        />
        {note.broken.length > 0 && (
          <div>
            <h2>Links to missing notes</h2>
            <ul className="refs">
              {note.broken.map((b) => (
                <li key={b.target} className="broken">{b.target}</li>
              ))}
            </ul>
          </div>
        )}
      </aside>
    </section>
  );
}
