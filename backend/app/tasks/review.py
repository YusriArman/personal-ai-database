"""The review queue: list tasks, accept / reject / reword them, export accepted ones."""

from __future__ import annotations

import sqlite3

STATUSES = ("pending", "accepted", "rejected")


def _row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "note_path": row["note_path"],
        "note_id": row["note_id"],
        "note_title": row["note_title"],
        "source": row["source"],
        "text": row["text"],
        "evidence": row["evidence"],
        "line": row["line"],
        "done": bool(row["done"]),
        "status": row["status"],
        "orphaned": bool(row["orphaned"]),
    }


SELECT = (
    "SELECT t.*, n.id AS note_id, n.title AS note_title FROM tasks t "
    "LEFT JOIN notes n ON n.path = t.note_path"
)


def list_tasks(
    conn: sqlite3.Connection, status: str | None = None, note_path: str | None = None
) -> list[dict]:
    clauses, params = [], []
    if status is not None:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        clauses.append("t.status = ?")
        params.append(status)
    if note_path is not None:
        clauses.append("t.note_path = ?")
        params.append(note_path)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(f"{SELECT}{where} ORDER BY t.note_path, t.line, t.id", params)
    return [_row(r) for r in rows]


def get_task(conn: sqlite3.Connection, task_id: int) -> dict | None:
    row = conn.execute(f"{SELECT} WHERE t.id = ?", (task_id,)).fetchone()
    return _row(row) if row else None


def update_task(
    conn: sqlite3.Connection, task_id: int, status: str | None = None, text: str | None = None
) -> dict | None:
    if get_task(conn, task_id) is None:
        return None
    if status is not None:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    if text is not None:
        if not text.strip():
            raise ValueError("task text cannot be empty")
        conn.execute("UPDATE tasks SET text = ? WHERE id = ?", (text.strip(), task_id))
    conn.commit()
    return get_task(conn, task_id)


def export_markdown(conn: sqlite3.Connection) -> str:
    """Accepted tasks as a markdown checklist, grouped by note. The app never writes
    this into the vault; the user copies it wherever they want."""
    lines = ["# Tasks", ""]
    current = None
    for task in list_tasks(conn, status="accepted"):
        if task["note_path"] != current:
            current = task["note_path"]
            title = task["note_title"] or current
            if len(lines) > 2:
                lines.append("")
            lines.append(f"## {title}")
        box = "x" if task["done"] else " "
        lines.append(f"- [{box}] {task['text']}")
    return "\n".join(lines) + "\n"
