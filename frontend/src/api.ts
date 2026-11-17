import type {
  Answer, Hit, Mode, NoteDetail, NoteListItem, RescanReport, Status, Task,
} from "./types";

/** An error whose message is safe to show to the user as-is. */
export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, init);
  } catch {
    throw new ApiError(
      "The app's server is not running. Start it with `make api` and reload this page.",
    );
  }
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Not JSON (for example the dev proxy's error page): the server is unreachable.
      if (response.status >= 500) {
        detail = "The app's server is not running. Start it with `make api` and reload this page.";
      }
    }
    throw new ApiError(detail);
  }
  const type = response.headers.get("content-type") ?? "";
  return (type.includes("json") ? response.json() : response.text()) as Promise<T>;
}

const json = (method: string, body?: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: body === undefined ? undefined : JSON.stringify(body),
});

export const api = {
  status: () => request<Status>("/api/status"),
  rescan: () => request<RescanReport>("/api/rescan", json("POST")),
  search: (q: string, mode: Mode) =>
    request<{ results: Hit[] }>(`/api/search?q=${encodeURIComponent(q)}&mode=${mode}`),
  notes: () => request<NoteListItem[]>("/api/notes"),
  note: (id: number) => request<NoteDetail>(`/api/notes/${id}`),
  ask: (question: string) => request<Answer>("/api/ask", json("POST", { question })),
  tasks: () => request<Task[]>("/api/tasks"),
  proposeTasks: () =>
    request<{ notes_analysed: number; new_proposals: number }>("/api/tasks/propose", json("POST")),
  updateTask: (id: number, patch: { status?: Task["status"]; text?: string }) =>
    request<Task>(`/api/tasks/${id}`, json("PATCH", patch)),
  exportTasks: () => request<string>("/api/tasks/export"),
};
