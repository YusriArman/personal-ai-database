import { api } from "./api";
import { useHashRoute, useLoad } from "./lib/hooks";
import { AskView } from "./views/Ask";
import { NoteView } from "./views/NoteView";
import { NotesView } from "./views/Notes";
import { SearchView } from "./views/Search";
import { StatusView } from "./views/Status";
import { TasksView } from "./views/Tasks";

const NAV = [
  { route: "search", label: "Search" },
  { route: "ask", label: "Ask" },
  { route: "tasks", label: "Tasks" },
  { route: "notes", label: "Notes" },
  { route: "status", label: "Index" },
];

export function App() {
  const route = useHashRoute();
  const status = useLoad(api.status, route);
  const [section, argument] = route.split("/");
  const current = section === "note" ? "notes" : section;
  const s = status.data;

  return (
    <div className="shell">
      <header className="sidebar">
        <a className="brand" href="#/search">
          Notes Companion
        </a>
        <nav aria-label="Sections">
          {NAV.map((item) => (
            <a
              key={item.route}
              href={`#/${item.route}`}
              aria-current={current === item.route ? "page" : undefined}
            >
              {item.label}
              {item.route === "tasks" && s && s.tasks_pending > 0 && (
                <span className="count" title="Tasks waiting for review">
                  {s.tasks_pending}
                </span>
              )}
            </a>
          ))}
        </nav>
        <a className="health" href="#/status">
          {status.error ? (
            <span className="dot off" />
          ) : (
            <span className={s?.model.ok ? "dot on" : "dot off"} />
          )}
          {status.error
            ? "Server not running"
            : !s
              ? "Checking…"
              : s.model.ok
                ? `Model ready, ${s.notes} notes`
                : `Keyword only, ${s.notes} notes`}
        </a>
      </header>
      <main>
        {section === "search" && <SearchView modelReady={Boolean(s?.model.ok)} />}
        {section === "ask" && <AskView />}
        {section === "tasks" && <TasksView onChange={status.reload} />}
        {section === "notes" && <NotesView />}
        {section === "note" && <NoteView id={Number(argument)} />}
        {section === "status" && <StatusView status={s} error={status.error} onChange={status.reload} />}
      </main>
    </div>
  );
}
