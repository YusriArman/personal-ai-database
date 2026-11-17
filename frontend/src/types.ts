export type Mode = "keyword" | "semantic" | "hybrid";

export interface Hit {
  chunk_id: number;
  note_id: number;
  path: string;
  title: string;
  heading: string;
  text: string;
  score: number;
  snippet: string;
  similarity: number | null;
}

export interface NoteRef {
  id: number;
  title: string;
  path: string;
  similarity?: number;
}

export interface Task {
  id: number;
  note_path: string;
  note_id: number | null;
  note_title: string | null;
  source: "checkbox" | "model";
  text: string;
  evidence: string;
  line: number | null;
  done: boolean;
  status: "pending" | "accepted" | "rejected";
  orphaned: boolean;
}

export interface NoteDetail {
  id: number;
  path: string;
  title: string;
  body: string;
  tags: string[];
  outgoing: NoteRef[];
  backlinks: NoteRef[];
  broken: { target: string }[];
  suggestions: NoteRef[];
  tasks: Task[];
}

export interface NoteListItem {
  id: number;
  path: string;
  title: string;
  tags: string[];
}

export interface Answer {
  question: string;
  text: string;
  abstained: boolean;
  reason: "answered" | "no_sources" | "low_similarity" | "model_declined" | "empty_answer";
  sources: Hit[];
  cited: number[];
  invalid_citations: number[];
  grounded: boolean;
  top_similarity: number | null;
}

export interface Status {
  vault: string;
  vault_exists: boolean;
  profile: string;
  provider: string;
  embed_model: string;
  chat_model: string;
  model: { ok: boolean; detail: string };
  notes: number;
  chunks: number;
  chunks_embedded: number;
  broken_links: number;
  tasks_pending: number;
  notes_awaiting_task_proposals: number;
}

export interface RescanReport {
  added: string[];
  updated: string[];
  deleted: string[];
  unchanged: number;
  chunks_embedded: number;
  chunks_missing_embedding: number;
  embedding_error: string | null;
}
