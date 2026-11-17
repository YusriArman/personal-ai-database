"""Connections between notes: explicit wikilinks, backlinks, broken links, and
suggested links between notes that are similar but not yet linked."""

from __future__ import annotations

import sqlite3
from pathlib import PurePosixPath

import numpy as np


def _lookup_keys(path: str, title: str) -> set[str]:
    """Every string a [[wikilink]] could use to point at this note."""
    p = PurePosixPath(path)
    return {title.lower(), p.stem.lower(), p.with_suffix("").as_posix().lower(), path.lower()}


def resolve_all_links(conn: sqlite3.Connection) -> None:
    """Fill links.target_id by matching link text to note titles, file names or paths.

    Run after every rescan, because adding a note can fix a previously broken link
    and deleting one can break a link in a note that did not itself change.
    """
    index: dict[str, int] = {}
    for row in conn.execute("SELECT id, path, title FROM notes ORDER BY id"):
        for key in _lookup_keys(row["path"], row["title"]):
            index.setdefault(key, row["id"])  # first note wins on an ambiguous name
    for row in conn.execute("SELECT source_id, target_text FROM links").fetchall():
        target = index.get(row["target_text"].strip().lower())
        conn.execute(
            "UPDATE links SET target_id = ? WHERE source_id = ? AND target_text = ?",
            (target, row["source_id"], row["target_text"]),
        )


def outgoing(conn: sqlite3.Connection, note_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT l.target_text, n.id, n.title, n.path FROM links l "
        "JOIN notes n ON n.id = l.target_id WHERE l.source_id = ? ORDER BY n.title",
        (note_id,),
    )
    return [{"id": r["id"], "title": r["title"], "path": r["path"]} for r in rows]


def backlinks(conn: sqlite3.Connection, note_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT n.id, n.title, n.path FROM links l JOIN notes n ON n.id = l.source_id "
        "WHERE l.target_id = ? AND l.source_id != ? ORDER BY n.title",
        (note_id, note_id),
    )
    return [{"id": r["id"], "title": r["title"], "path": r["path"]} for r in rows]


def broken(conn: sqlite3.Connection, note_id: int | None = None) -> list[dict]:
    sql = (
        "SELECT l.target_text, n.id, n.title, n.path FROM links l "
        "JOIN notes n ON n.id = l.source_id WHERE l.target_id IS NULL"
    )
    params: tuple = ()
    if note_id is not None:
        sql += " AND l.source_id = ?"
        params = (note_id,)
    rows = conn.execute(sql + " ORDER BY n.title, l.target_text", params)
    return [
        {"target": r["target_text"], "source_id": r["id"], "source_title": r["title"]}
        for r in rows
    ]


def note_vectors(conn: sqlite3.Connection, embed_model: str) -> dict[int, np.ndarray]:
    """One vector per note: the normalised mean of its chunk vectors."""
    sums: dict[int, np.ndarray] = {}
    for row in conn.execute(
        "SELECT note_id, embedding FROM chunks WHERE embedding IS NOT NULL AND embed_model = ?",
        (embed_model,),
    ):
        vec = np.frombuffer(row["embedding"], dtype=np.float32)
        sums[row["note_id"]] = sums.get(row["note_id"], 0) + vec
    out: dict[int, np.ndarray] = {}
    for note_id, total in sums.items():
        norm = float(np.linalg.norm(total))
        if norm > 0:
            out[note_id] = total / norm
    return out


def suggestions(
    conn: sqlite3.Connection,
    note_id: int,
    embed_model: str,
    limit: int = 5,
    min_similarity: float = 0.3,
) -> list[dict]:
    """Notes similar to this one that are not linked to it in either direction."""
    vectors = note_vectors(conn, embed_model)
    if note_id not in vectors:
        return []
    linked = {
        r[0]
        for r in conn.execute(
            "SELECT target_id FROM links WHERE source_id = ? AND target_id IS NOT NULL "
            "UNION SELECT source_id FROM links WHERE target_id = ?",
            (note_id, note_id),
        )
    }
    me = vectors[note_id]
    scored = [
        (float(vec @ me), other)
        for other, vec in vectors.items()
        if other != note_id and other not in linked
    ]
    scored = [pair for pair in scored if pair[0] >= min_similarity]
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    out: list[dict] = []
    for similarity, other in scored[:limit]:
        row = conn.execute("SELECT id, title, path FROM notes WHERE id = ?", (other,)).fetchone()
        out.append(
            {
                "id": row["id"],
                "title": row["title"],
                "path": row["path"],
                "similarity": round(similarity, 3),
            }
        )
    return out
