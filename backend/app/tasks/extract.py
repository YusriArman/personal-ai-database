"""Task extraction in two tiers.

Tier 1 — checkboxes (`- [ ] thing`): parsed exactly, no model involved. These are the
user's own explicit tasks, so they are stored as accepted.

Tier 2 — model proposals: the local model is asked about one sentence at a time,
"is this an action item, true or false?". Sentences it says yes to are stored as
*pending*; nothing proposed by a model becomes a task until the user accepts it in the
review queue. Because the model only ever judges a sentence taken from the note, a
proposal cannot refer to text that is not there.

Why one sentence at a time: the first version sent the whole note and asked for a list of
task sentences. A 3B model then listed nearly every sentence (precision 0.05 in the live
evaluation). A yes/no question per sentence is a much easier job for a small model.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3

from app.ingest.parser import CHECKBOX_RE, FENCE_RE, HEADING_RE, CheckboxTask
from app.providers.base import ModelProvider

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
ABBREVIATION_RE = re.compile(r"\b(Dr|Mr|Mrs|Ms|Prof|St|vs|etc|e\.g|i\.e)\.$", re.I)
CODE_SPAN_RE = re.compile(r"`[^`]*`")
MAX_SENTENCES = 60

SYSTEM_PROMPT = (
    "You find action items in personal notes. An action item is a sentence where the author "
    "commits to doing something specific in the future. Most sentences are NOT action items: "
    "descriptions, facts, decisions already made, things that already happened, feelings, "
    "instructions in reference material and things other people will do are not action items."
)

# The examples are invented and deliberately unrelated to the demo vault.
PROMPT_TEMPLATE = """Decide for one sentence from a personal note whether it is an action item.

Examples:
Sentence: I need to email Dana about the venue.
{{"action_item": true}}
Sentence: Tomorrow I am booking the train tickets.
{{"action_item": true}}
Sentence: The venue holds 200 people.
{{"action_item": false}}
Sentence: We booked the venue last week.
{{"action_item": false}}
Sentence: Dana will send the invoice.
{{"action_item": false}}
Sentence: Use a sharp knife for tomatoes.
{{"action_item": false}}
Sentence: It would be nice to repaint the hall.
{{"action_item": false}}

Note title: {title}
Sentence: {sentence}
"""


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
        for sentence in split_sentences(line):
            if len(sentence) >= 8:
                sentences.append(sentence)
    return sentences[:MAX_SENTENCES]


def split_sentences(line: str) -> list[str]:
    """Split a line into sentences without breaking after "Dr." or inside `code`."""
    # Hide inline code so a "." inside it (as in `find . -name`) is not a sentence end.
    spans: list[str] = []

    def hide(match: re.Match) -> str:
        spans.append(match.group(0))
        return f"\x00{len(spans) - 1}\x00"

    pieces = SENTENCE_SPLIT_RE.split(CODE_SPAN_RE.sub(hide, line))
    merged: list[str] = []
    for piece in pieces:
        if merged and ABBREVIATION_RE.search(merged[-1]):
            merged[-1] = f"{merged[-1]} {piece}"
        else:
            merged.append(piece)
    restore = lambda text: re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], text)  # noqa: E731
    return [restore(piece).strip() for piece in merged if piece.strip()]


def parse_verdict(reply: str) -> bool:
    """Read the model's JSON verdict. Anything that is not exactly
    {"action_item": true} counts as "no": malformed output must never create a task."""
    try:
        data = json.loads(reply)
    except (json.JSONDecodeError, TypeError):
        return False
    return isinstance(data, dict) and data.get("action_item") is True


def propose_for_note(provider: ModelProvider, title: str, body: str) -> list[tuple[str, str]]:
    """Return (task text, evidence sentence) for each sentence the model calls a task.

    The task text starts as the sentence itself; the user can reword it in review.
    """
    proposals: list[tuple[str, str]] = []
    for sentence in candidate_sentences(body):
        reply = provider.generate(
            PROMPT_TEMPLATE.format(title=title, sentence=sentence),
            system=SYSTEM_PROMPT,
            json_mode=True,
        )
        if parse_verdict(reply):
            proposals.append((sentence, sentence))
    return proposals


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

