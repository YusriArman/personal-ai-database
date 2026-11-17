import { useState } from "react";
import { api } from "../api";
import { messageOf } from "../lib/hooks";
import type { RescanReport, Status } from "../types";

function names(list: string[]) {
  return list.length <= 5 ? list.join(", ") : `${list.slice(0, 5).join(", ")} and ${list.length - 5} more`;
}

export function StatusView({
  status, error, onChange,
}: { status: Status | null; error: string | null; onChange: () => void }) {
  const [report, setReport] = useState<RescanReport | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function scan() {
    setBusy(true);
    setFailure(null);
    try {
      setReport(await api.rescan());
      onChange();
    } catch (reason) {
      setFailure(messageOf(reason));
    } finally {
      setBusy(false);
    }
  }

  if (error) return <p className="error" role="alert">{error}</p>;
  if (!status) return <p className="meta">Checking…</p>;
  const unembedded = status.chunks - status.chunks_embedded;

  return (
    <section>
      <h1>Index</h1>
      <p className="lede">
        The app keeps its own copy of your notes for searching. Your vault is only ever read.
      </p>
      <div className="actions">
        <button type="button" onClick={scan} disabled={busy}>
          {busy ? "Scanning…" : "Scan vault for changes"}
        </button>
      </div>
      {failure && <p className="error" role="alert">{failure}</p>}
      {report && (
        <div className="note" role="status">
          <p>
            {report.added.length} added, {report.updated.length} changed, {report.deleted.length}{" "}
            removed, {report.unchanged} unchanged.
          </p>
          {report.added.length > 0 && <p className="meta">Added: {names(report.added)}</p>}
          {report.updated.length > 0 && <p className="meta">Changed: {names(report.updated)}</p>}
          {report.deleted.length > 0 && <p className="meta">Removed: {names(report.deleted)}</p>}
          {report.embedding_error && (
            <p className="error">
              Notes were indexed for exact-word search only, because the local model could not be
              reached. Start it and scan again.
            </p>
          )}
        </div>
      )}

      <dl className="facts">
        <dt>Vault folder</dt>
        <dd>
          {status.vault}
          {!status.vault_exists && <span className="flag"> (this folder does not exist)</span>}
        </dd>
        <dt>Notes</dt>
        <dd>{status.notes}</dd>
        <dt>Passages</dt>
        <dd>
          {status.chunks}
          {unembedded > 0 && (
            <span className="flag"> ({unembedded} not yet read by the model; scan again once it is running)</span>
          )}
        </dd>
        <dt>Links to missing notes</dt>
        <dd>{status.broken_links}</dd>
        <dt>Notes not yet checked for tasks</dt>
        <dd>{status.notes_awaiting_task_proposals}</dd>
      </dl>

      <h2>Local model</h2>
      <p className={status.model.ok ? "note" : "error"}>{status.model.detail}</p>
      <dl className="facts">
        <dt>Runs through</dt>
        <dd>{status.provider === "fake" ? "Built-in stand-in (no real model; for demos and tests)" : "Ollama on this computer"}</dd>
        <dt>Hardware profile</dt>
        <dd>{status.profile}</dd>
        <dt>Model for meaning search</dt>
        <dd>{status.embed_model}</dd>
        <dt>Model for answers and tasks</dt>
        <dd>{status.chat_model}</dd>
      </dl>
    </section>
  );
}
