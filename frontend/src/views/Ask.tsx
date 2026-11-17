import { type FormEvent, useState } from "react";
import { api } from "../api";
import { messageOf } from "../lib/hooks";
import { splitCitations } from "../lib/text";
import type { Answer } from "../types";

const WHY: Record<Answer["reason"], string> = {
  answered: "",
  no_sources: "No notes matched this question at all.",
  low_similarity: "The closest notes were not similar enough to the question to trust an answer.",
  model_declined: "The model read the closest notes and found no answer in them.",
};

export function AskView() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [focus, setFocus] = useState<number | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    setBusy(true);
    setError(null);
    setAnswer(null);
    setFocus(null);
    try {
      setAnswer(await api.ask(question));
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h1>Ask your notes</h1>
      <p className="lede">
        Answers come only from your notes, and every claim points at the passage it came from.
      </p>
      <form onSubmit={submit} className="query">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Try: When is the project proposal due?"
          aria-label="Question"
          autoFocus
        />
        <button type="submit" disabled={busy || !question.trim()}>
          {busy ? "Reading notes…" : "Ask"}
        </button>
      </form>
      {error && <p className="error" role="alert">{error}</p>}
      {answer && (
        <div className="answer-layout">
          <div>
            {answer.abstained ? (
              <div className="refusal">
                <p className="reading">{answer.text}</p>
                <p className="meta">{WHY[answer.reason]}</p>
              </div>
            ) : (
              <>
                <p className="reading answer">
                  {splitCitations(answer.text, answer.cited).map((part, i) =>
                    part.kind === "cite" ? (
                      <button
                        key={i}
                        type="button"
                        className="cite"
                        aria-label={`Show source ${part.number}`}
                        aria-pressed={focus === part.number}
                        onClick={() => setFocus(part.number)}
                      >
                        {part.number}
                      </button>
                    ) : (
                      <span key={i}>{part.kind === "text" ? part.text : ""}</span>
                    ),
                  )}
                </p>
                {!answer.grounded && (
                  <p className="error" role="alert">
                    This answer cites none of your notes, so it may not come from them. Check it
                    against the passages before relying on it.
                  </p>
                )}
                {answer.invalid_citations.length > 0 && (
                  <p className="meta">
                    The model cited {answer.invalid_citations.length} source
                    {answer.invalid_citations.length > 1 ? "s" : ""} that did not exist; those
                    references were removed.
                  </p>
                )}
              </>
            )}
          </div>
          {answer.sources.length > 0 && (
            <aside aria-label="Passages the answer could use">
              <h2>{answer.abstained ? "Closest passages" : "Passages used"}</h2>
              <ol className="sources">
                {answer.sources.map((source, i) => {
                  const number = i + 1;
                  const cited = answer.cited.includes(number);
                  return (
                    <li
                      key={source.chunk_id}
                      className={[cited ? "cited" : "", focus === number ? "focus" : ""].join(" ")}
                    >
                      <span className="cite static">{number}</span>
                      <a href={`#/note/${source.note_id}`}>{source.title}</a>
                      {source.heading && <span className="where">in {source.heading}</span>}
                      <p className="reading">{source.text}</p>
                    </li>
                  );
                })}
              </ol>
            </aside>
          )}
        </div>
      )}
    </section>
  );
}
