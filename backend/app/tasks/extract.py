"""Task extraction in two tiers.

Tier 1 — checkboxes (`- [ ] thing`): parsed exactly, no model involved. These are the
user's own explicit tasks, so they are stored as accepted.

Tier 2 — model proposals: sentences that imply a task ("I need to email Dana") are
proposed by the local model and stored as *pending*. Nothing proposed by a model
becomes a task until the user accepts it in the review queue. Every proposal must
point at a sentence that really exists in the note, otherwise it is dropped.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3

from app.ingest.parser import CHECKBOX_RE, FENCE_RE, HEADING_RE, CheckboxTask
from app.providers.base import ModelProvider

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
MAX_SENTENCES = 60

SYSTEM_PROMPT = (
    "You find action items in personal notes. An action item is something the note's "
    "author still intends or needs to do. Do not include things already done, things "
    "other people will do, general facts, or ideas with no commitment."
)

PROMPT_TEMPLATE = """Note title: {title}

Numbered sentences from the note:
{sentences}

Return JSON of the form {{"tasks": [{{"sentence": <number>, "task": "<short imperative>"}}]}}.
Use only sentence numbers from the list. If there are no action items return {{"tasks": []}}."""


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def task_key(note_path: str, source: str, text: str) -> str:
    raw = f"{note_path}\x00{source}\x00{normalise(text)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def sync_checkbox_tasks(
    conn: sqlite3.Connection, note_path: str, tasks: list[CheckboxTask]
) -> None:
    """Make stored checkbox tasks for one note match what is in the file now."""
    current: dict[str, CheckboxTask] = {}
    for task in tasks:
        current.setdefault(task_key(note_path, "checkbox", task.text), task)

    for row in conn.execute(
        "SELECT id, key FROM tasks WHERE note_path = ? AND source = 'checkbox'", (note_path,)
    ).fetchall():
        if row["key"] not in current:
            conn.execute("DELETE FROM tasks WHERE id = ?", (row["id"],))

    for key, task in current.items():
        conn.execute(
            """
            INSERT INTO tasks (key, note_path, source, text, evidence, line, done, status)
            VALUES (?, ?, 'checkbox', ?, ?, ?, ?, 'accepted')
            ON CONFLICT(key) DO UPDATE SET line = excluded.line, done = excluded.done,
                                           orphaned = 0
            """,
            (key, note_path, task.text, task.text, task.line, int(task.done)),
        )


def candidate_sentences(body: str) -> list[str]:
    """Prose sentences a task could hide in: no headings, code, or checkbox lines
    (checkboxes are already handled exactly by tier 1)."""
    sentences: list[str] = []
    in_fence = False
    for line in body.split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or HEADING_RE.match(line) or CHECKBOX_RE.match(line):
            continue
        line = re.sub(r"^\s*(?:[-*+]|\d+\.)\s+", "", line).strip()
        if not line:
            continue
        for sentence in SENTENCE_SPLIT_RE.split(line):
            sentence = sentence.strip()
            if len(sentence) >= 8:
                sentences.append(sentence)
    return sentences[:MAX_SENTENCES]


def parse_proposals(reply: str, sentences: list[str]) -> list[tuple[str, str]]:
    """Validate the model's JSON reply. Returns (task text, evidence sentence) pairs.

    Anything malformed or pointing at a sentence number that does not exist is dropped:
    a proposal with no real evidence is a hallucination and must never reach review.
    """
    try:
        data = json.loads(reply)
    except (json.JSONDecodeError, TypeError):
        return []
    items = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    out: list[tuple[str, str]] = []
    seen: set[int] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        number, text = item.get("sentence"), item.get("task")
        if isinstance(number, bool) or not isinstance(number, int) or not isinstance(text, str):
            continue
        if not (1 <= number <= len(sentences)) or not text.strip() or number in seen:
            continue
        seen.add(number)
        out.append((text.strip(), sentences[number - 1]))
    return out


def propose_for_note(provider: ModelProvider, title: str, body: str) -> list[tuple[str, str]]:
    sentences = candidate_sentences(body)
    if not sentences:
        return []
    numbered = "\n".join(f"[{i}] {s}" for i, s in enumerate(sentences, start=1))
    reply = provider.generate(
        PROMPT_TEMPLATE.format(title=title, sentences=numbered),
        system=SYSTEM_PROMPT,
        json_mode=True,
    )
    return parse_proposals(reply, sentences)


def propose_tasks(conn: sqlite3.Connection, provider: ModelProvider) -> dict:
    """Ask the model for tasks in every note not yet analysed at its current content.

    Raises ProviderUnavailable if the model cannot be reached; notes analysed before
    the failure keep their results.
    """
    notes = conn.execute(
        "SELECT id, path, title, body, content_hash FROM notes "
        "WHERE proposed_hash IS NOT content_hash ORDER BY path"
    ).fetchall()
    proposed = 0
    for note in notes:
        proposals = propose_for_note(provider, note["title"], note["body"])
        keys = {
            task_key(note["path"], "model", evidence): (text, evidence)
            for text, evidence in proposals
        }
        # Proposals whose sentence has gone: drop if never reviewed, else mark orphaned.
        body_text = normalise(note["body"])
        for row in conn.execute(
            "SELECT id, key, status, evidence FROM tasks "
            "WHERE note_path = ? AND source = 'model'",
            (note["path"],),
        ).fetchall():
            if row["key"] in keys or normalise(row["evidence"]) in body_text:
                continue
            if row["status"] == "pending":
                conn.execute("DELETE FROM tasks WHERE id = ?", (row["id"],))
            else:
                conn.execute("UPDATE tasks SET orphaned = 1 WHERE id = ?", (row["id"],))
        for key, (text, evidence) in keys.items():
            cursor = conn.execute(
                "INSERT OR IGNORE INTO tasks (key, note_path, source, text, evidence, status) "
                "VALUES (?, ?, 'model', ?, ?, 'pending')",
                (key, note["path"], text, evidence),
            )
            proposed += cursor.rowcount
        conn.execute(
            "UPDATE notes SET proposed_hash = content_hash WHERE id = ?", (note["id"],)
        )
        conn.commit()
    return {"notes_analysed": len(notes), "new_proposals": proposed}

