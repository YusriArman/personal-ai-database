import { useState } from "react";
import { api } from "../api";
import { messageOf, useLoad } from "../lib/hooks";
import type { Task } from "../types";

function TaskSource({ task }: { task: Task }) {
  if (task.note_id === null) return <span className="meta">from {task.note_path} (note removed)</span>;
  return (
    <span className="meta">
      from <a href={`#/note/${task.note_id}`}>{task.note_title}</a>
    </span>
  );
}

export function TasksView({ onChange }: { onChange: () => void }) {
  const { data: tasks, error, reload } = useLoad(api.tasks);
  const [notice, setNotice] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<{ id: number; text: string } | null>(null);
  const [exported, setExported] = useState<string | null>(null);

  async function act(work: () => Promise<string | void>) {
    setFailure(null);
    setNotice(null);
    try {
      const message = await work();
      if (message) setNotice(message);
      reload();
      onChange();
    } catch (reason) {
      setFailure(messageOf(reason));
    }
  }

  async function propose() {
    setBusy(true);
    await act(async () => {
      const result = await api.proposeTasks();
      if (result.notes_analysed === 0) return "Every note has already been checked.";
      return `Checked ${result.notes_analysed} notes and found ${result.new_proposals} possible tasks.`;
    });
    setBusy(false);
  }

  const decide = (task: Task, status: Task["status"]) =>
    act(async () => {
      const text = editing?.id === task.id ? editing.text : undefined;
      await api.updateTask(task.id, { status, text });
      setEditing(null);
    });

  if (error) return <p className="error" role="alert">{error}</p>;
  if (!tasks) return <p className="meta">Loading tasks…</p>;

  const pending = tasks.filter((t) => t.status === "pending");
  const open = tasks.filter((t) => t.status === "accepted" && !t.done);
  const done = tasks.filter((t) => t.status === "accepted" && t.done);
  const rejected = tasks.filter((t) => t.status === "rejected");

  return (
    <section>
      <h1>Tasks</h1>
      <p className="lede">
        Checkboxes in your notes appear here as they are. Tasks the model thinks it found in your
        writing wait for your decision first.
      </p>
      <div className="actions">
        <button type="button" onClick={propose} disabled={busy}>
          {busy ? "Reading notes…" : "Find tasks in my writing"}
        </button>
        <button
          type="button"
          className="quiet"
          onClick={() => act(async () => setExported(await api.exportTasks()))}
        >
          Show as checklist
        </button>
      </div>
      {notice && <p className="note" role="status">{notice}</p>}
      {failure && <p className="error" role="alert">{failure}</p>}
      {exported !== null && (
        <div className="export">
          <p className="meta">Copy this wherever you like. Your notes are never changed.</p>
          <textarea readOnly value={exported} rows={10} aria-label="Accepted tasks as markdown" />
        </div>
      )}

      <h2>Waiting for your decision ({pending.length})</h2>
      {pending.length === 0 ? (
        <p className="empty">Nothing to review. Use “Find tasks in my writing” after adding notes.</p>
      ) : (
        <ul className="review">
          {pending.map((task) => (
            <li key={task.id}>
              {editing?.id === task.id ? (
                <input
                  value={editing.text}
                  onChange={(e) => setEditing({ id: task.id, text: e.target.value })}
                  aria-label="Task wording"
                />
              ) : (
                <p className="task-text">{task.text}</p>
              )}
              <blockquote className="reading">{task.evidence}</blockquote>
              <TaskSource task={task} />
              <div className="actions">
                <button type="button" onClick={() => decide(task, "accepted")}>
                  Accept
                </button>
                <button type="button" className="quiet" onClick={() => decide(task, "rejected")}>
                  Reject
                </button>
                {editing?.id !== task.id && (
                  <button
                    type="button"
                    className="quiet"
                    onClick={() => setEditing({ id: task.id, text: task.text })}
                  >
                    Reword
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <h2>To do ({open.length})</h2>
      <TaskList tasks={open} empty="No open tasks." onUndo={(t) => decide(t, "pending")} />
      <h2>Done ({done.length})</h2>
      <TaskList tasks={done} empty="Nothing ticked off in your notes yet." onUndo={(t) => decide(t, "pending")} />
      {rejected.length > 0 && (
        <details>
          <summary>Rejected ({rejected.length})</summary>
          <TaskList tasks={rejected} empty="" onUndo={(t) => decide(t, "pending")} />
        </details>
      )}
    </section>
  );
}

function TaskList({ tasks, empty, onUndo }: { tasks: Task[]; empty: string; onUndo: (task: Task) => void }) {
  if (tasks.length === 0) return <p className="empty">{empty}</p>;
  return (
    <ul className="tasks">
      {tasks.map((task) => (
        <li key={task.id} className={task.done ? "done" : ""}>
          <span className="box" aria-hidden="true">{task.done ? "✓" : ""}</span>
          <span>
            {task.text}
            {task.orphaned && <span className="flag"> (its sentence is no longer in the note)</span>}
            <br />
            <TaskSource task={task} />
            {task.source === "model" && (
              <>
                {" "}
                <button type="button" className="link" onClick={() => onUndo(task)}>
                  Review again
                </button>
              </>
            )}
          </span>
        </li>
      ))}
    </ul>
  );
}
