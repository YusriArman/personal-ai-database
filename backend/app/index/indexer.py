"""Bring the SQLite index in line with the vault on disk.

A rescan is incremental: a note whose content hash is unchanged is skipped entirely,
a changed note is re-parsed, re-chunked and re-embedded, and a note that has gone from
disk is removed. If the model is unavailable the keyword index is still built and the
chunks are embedded on a later rescan.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from app.connect.links import resolve_all_links
from app.ingest.chunker import chunk_note
from app.ingest.parser import parse_note
from app.ingest.scanner import VaultFile, scan_vault
from app.providers.base import ModelProvider, ProviderUnavailable
from app.tasks.extract import sync_checkbox_tasks

EMBED_BATCH = 32


@dataclass
class RescanReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    unchanged: int = 0
    chunks_embedded: int = 0
    chunks_missing_embedding: int = 0
    embedding_error: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def to_blob(vector: list[float]) -> bytes:
    """Store a vector as normalised float32 so cosine similarity is a dot product."""
    arr = np.asarray(vector, dtype=np.float32)
    norm = float(np.linalg.norm(arr))
    if norm > 0:
        arr = arr / norm
    return arr.tobytes()


def embedding_text(title: str, heading: str, text: str) -> str:
    """What gets embedded for a chunk: its text plus where it sits."""
    header = title if not heading else f"{title} — {heading}"
    return f"{header}\n{text}"


def _delete_note(conn: sqlite3.Connection, note_id: int) -> None:
    conn.execute(
        "DELETE FROM chunks_fts WHERE rowid IN (SELECT id FROM chunks WHERE note_id = ?)",
        (note_id,),
    )
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))  # cascades chunks and links


def _write_note(conn: sqlite3.Connection, file: VaultFile, existing_id: int | None) -> None:
    parsed = parse_note(file.text, fallback_title=Path(file.rel_path).stem)
    values = (
        parsed.title,
        file.content_hash,
        file.mtime,
        parsed.body,
        json.dumps(parsed.tags),
        json.dumps(parsed.frontmatter, default=str),
    )
    if existing_id is None:
        note_id = conn.execute(
            "INSERT INTO notes (title, content_hash, mtime, body, tags, frontmatter, path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (*values, file.rel_path),
        ).lastrowid
    else:
        note_id = existing_id
        conn.execute(
            "UPDATE notes SET title = ?, content_hash = ?, mtime = ?, body = ?, tags = ?, "
            "frontmatter = ? WHERE id = ?",
            (*values, note_id),
        )
        conn.execute(
            "DELETE FROM chunks_fts WHERE rowid IN (SELECT id FROM chunks WHERE note_id = ?)",
            (note_id,),
        )
        conn.execute("DELETE FROM chunks WHERE note_id = ?", (note_id,))
        conn.execute("DELETE FROM links WHERE source_id = ?", (note_id,))

    for chunk in chunk_note(parsed.body):
        chunk_id = conn.execute(
            "INSERT INTO chunks (note_id, position, heading, text) VALUES (?, ?, ?, ?)",
            (note_id, chunk.position, chunk.heading, chunk.text),
        ).lastrowid
        conn.execute(
            "INSERT INTO chunks_fts (rowid, title, heading, text) VALUES (?, ?, ?, ?)",
            (chunk_id, parsed.title, chunk.heading, chunk.text),
        )
    for target in parsed.links:
        conn.execute(
            "INSERT OR IGNORE INTO links (source_id, target_text) VALUES (?, ?)",
            (note_id, target),
        )
    sync_checkbox_tasks(conn, file.rel_path, parsed.tasks)


def embed_pending(conn: sqlite3.Connection, provider: ModelProvider) -> tuple[int, str | None]:
    """Embed every chunk that has no vector for the current embedding model.

    Returns (number embedded, error message or None). A provider failure is reported,
    not raised, so indexing still succeeds for keyword search.
    """
    rows = conn.execute(
        "SELECT c.id, n.title, c.heading, c.text FROM chunks c JOIN notes n ON n.id = c.note_id "
        "WHERE c.embedding IS NULL OR c.embed_model IS NOT ? ORDER BY c.id",
        (provider.embed_model,),
    ).fetchall()
    done = 0
    for start in range(0, len(rows), EMBED_BATCH):
        batch = rows[start : start + EMBED_BATCH]
        texts = [embedding_text(r["title"], r["heading"], r["text"]) for r in batch]
        try:
            vectors = provider.embed(texts)
        except ProviderUnavailable as exc:
            conn.commit()
            return done, str(exc)
        for row, vector in zip(batch, vectors, strict=True):
            conn.execute(
                "UPDATE chunks SET embedding = ?, embed_model = ? WHERE id = ?",
                (to_blob(vector), provider.embed_model, row["id"]),
            )
        done += len(batch)
    conn.commit()
    return done, None


def rescan(conn: sqlite3.Connection, vault: Path, provider: ModelProvider | None) -> RescanReport:
    report = RescanReport()
    files = {f.rel_path: f for f in scan_vault(vault)}
    known = {r["path"]: r for r in conn.execute("SELECT id, path, content_hash FROM notes")}

    for path, row in known.items():
        if path not in files:
            _delete_note(conn, row["id"])
            sync_checkbox_tasks(conn, path, [])
            conn.execute(
                "DELETE FROM tasks WHERE note_path = ? AND source = 'model' AND status = 'pending'",
                (path,),
            )
            conn.execute(
                "UPDATE tasks SET orphaned = 1 WHERE note_path = ? AND source = 'model'", (path,)
            )
            report.deleted.append(path)

    for path, file in files.items():
        row = known.get(path)
        if row is None:
            _write_note(conn, file, None)
            report.added.append(path)
        elif row["content_hash"] != file.content_hash:
            _write_note(conn, file, row["id"])
            report.updated.append(path)
        else:
            report.unchanged += 1

    resolve_all_links(conn)
    conn.commit()

    if provider is not None:
        report.chunks_embedded, report.embedding_error = embed_pending(conn, provider)
        report.chunks_missing_embedding = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE embedding IS NULL OR embed_model IS NOT ?",
            (provider.embed_model,),
        ).fetchone()[0]
    else:
        report.chunks_missing_embedding = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE embedding IS NULL"
        ).fetchone()[0]
    return report
