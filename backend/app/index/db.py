"""SQLite schema and connection helper. One file holds all app state."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id            INTEGER PRIMARY KEY,
    path          TEXT NOT NULL UNIQUE,
    title         TEXT NOT NULL,
    content_hash  TEXT NOT NULL,
    mtime         REAL NOT NULL,
    body          TEXT NOT NULL,
    tags          TEXT NOT NULL DEFAULT '[]',
    frontmatter   TEXT NOT NULL DEFAULT '{}',
    -- content_hash for which the model was last asked to propose tasks
    proposed_hash TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    id          INTEGER PRIMARY KEY,
    note_id     INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    heading     TEXT NOT NULL,
    text        TEXT NOT NULL,
    embedding   BLOB,          -- float32 vector, L2-normalised; NULL until embedded
    embed_model TEXT
);
CREATE INDEX IF NOT EXISTS chunks_note ON chunks(note_id);

-- Keyword index. rowid is the chunk id.
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    title, heading, text, tokenize = 'porter unicode61'
);

CREATE TABLE IF NOT EXISTS links (
    source_id   INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    target_text TEXT NOT NULL,
    target_id   INTEGER REFERENCES notes(id) ON DELETE SET NULL,
    PRIMARY KEY (source_id, target_text)
);

-- Tasks keep the note path, not a foreign key, so a review decision survives
-- the note being edited, re-indexed or deleted.
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY,
    key         TEXT NOT NULL UNIQUE,   -- hash of (note path, source, normalised text)
    note_path   TEXT NOT NULL,
    source      TEXT NOT NULL CHECK (source IN ('checkbox', 'model')),
    text        TEXT NOT NULL,          -- task wording (editable in review)
    evidence    TEXT NOT NULL,          -- the exact line or sentence it came from
    line        INTEGER,
    done        INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'rejected')),
    orphaned    INTEGER NOT NULL DEFAULT 0  -- evidence no longer present in the vault
);
CREATE INDEX IF NOT EXISTS tasks_note ON tasks(note_path);
"""


def connect(db_path: Path | str) -> sqlite3.Connection:
    if str(db_path) != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn
