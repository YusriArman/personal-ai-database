"""Run the gold sets against the system and return plain dicts of results."""

from __future__ import annotations

import json
import re
import sqlite3
import time
from pathlib import Path

from app.answer.qa import answer_question
from app.config import REPO_ROOT
from app.evaluate import metrics
from app.ingest.parser import parse_note
from app.ingest.scanner import scan_vault
from app.providers.base import ModelProvider
from app.retrieve.search import search_notes, semantic_search
from app.tasks.extract import candidate_sentences, normalise, propose_for_note

DATA = REPO_ROOT / "evals" / "data"
DEMO_VAULT = REPO_ROOT / "demo_vault"
CUE_RE = re.compile(r"\b(need to|must|should|have to|remember to)\b", re.I)


def load(name: str) -> dict:
    return json.loads((DATA / f"{name}.json").read_text())


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


# --------------------------------------------------------------------------- retrieval


def eval_retrieval(conn: sqlite3.Connection, provider: ModelProvider | None, mode: str) -> dict:
    """recall@5, MRR and nDCG@10 per query, plus averages by split and by kind."""
    rows = []
    for q in load("retrieval")["queries"]:
        ranked = [h.path for h in search_notes(conn, provider, q["query"], mode, 10)]
        relevant = set(q["relevant"])
        rows.append(
            {
                "id": q["id"],
                "split": q["split"],
                "kind": q["kind"],
                "query": q["query"],
                "recall@5": metrics.recall_at_k(ranked, relevant, 5),
                "mrr": metrics.reciprocal_rank(ranked, relevant),
                "ndcg@10": metrics.ndcg_at_k(ranked, relevant, 10),
                "top": ranked[:3],
                "relevant": q["relevant"],
            }
        )

    def summarise(subset: list[dict]) -> dict:
        return {
            "n": len(subset),
            **{m: _mean([r[m] for r in subset]) for m in ("recall@5", "mrr", "ndcg@10")},
        }

    groups = {"all": rows}
    for key in ("split", "kind"):
        for value in sorted({r[key] for r in rows}):
            groups[f"{key}={value}"] = [r for r in rows if r[key] == value]
    return {
        "mode": mode,
        "summary": {name: summarise(subset) for name, subset in groups.items()},
        "misses": [r for r in rows if r["recall@5"] < 1.0],
    }


# ------------------------------------------------------------------------------- tasks


def eval_checkbox_parsing() -> dict:
    """Compare the parser's checkbox tasks with the hand-written gold list."""
    gold_by_note = load("tasks")["checkbox"]
    gold = {(p, text, done) for p, items in gold_by_note.items() for text, done in items}
    predicted = set()
    for file in scan_vault(DEMO_VAULT):
        for task in parse_note(file.text, Path(file.rel_path).stem).tasks:
            predicted.add((file.rel_path, task.text, task.done))
    result = metrics.precision_recall_f1(predicted, gold)
    result["false_positives"] = sorted(map(list, predicted - gold))
    result["false_negatives"] = sorted(map(list, gold - predicted))
    return result


def _gold_sentences(section: dict) -> set[tuple[str, str]]:
    return {(path, normalise(s)) for path, sentences in section.items() for s in sentences}


def score_task_predictions(predicted: set[tuple[str, str]]) -> dict:
    """Score (note path, normalised evidence sentence) pairs against the gold labels."""
    data = load("tasks")
    gold = _gold_sentences(data["implicit"])
    ambiguous = _gold_sentences(data["ambiguous"])
    result = metrics.precision_recall_f1(predicted, gold, ignore=ambiguous)
    kept = predicted - ambiguous
    result["false_positives"] = sorted(map(list, kept - gold))
    result["false_negatives"] = sorted(map(list, gold - kept))
    result["ambiguous_predicted"] = len(predicted & ambiguous)
    return result


def check_gold_sentences_exist() -> list[str]:
    """Gold labels that do not match any candidate sentence would silently become
    unreachable false negatives. Returns a list of such problems (should be empty)."""
    data = load("tasks")
    files = {f.rel_path: f for f in scan_vault(DEMO_VAULT)}
    problems = []
    for section in ("implicit", "ambiguous"):
        for path, sentences in data[section].items():
            if path not in files:
                problems.append(f"{section}: no such note {path}")
                continue
            body = parse_note(files[path].text, "x").body
            candidates = {normalise(s) for s in candidate_sentences(body)}
            for sentence in sentences:
                if normalise(sentence) not in candidates:
                    problems.append(f"{section}: not a candidate sentence in {path}: {sentence}")
    return problems


def eval_task_keyword_baseline() -> dict:
    """A rule with no model: any sentence containing need to / must / should / have to /
    remember to is a task. The local model has to beat this to be worth running."""
    predicted = set()
    for file in scan_vault(DEMO_VAULT):
        body = parse_note(file.text, "x").body
        for sentence in candidate_sentences(body):
            if CUE_RE.search(sentence):
                predicted.add((file.rel_path, normalise(sentence)))
    return score_task_predictions(predicted)


def eval_task_proposals(provider: ModelProvider) -> dict:
    """One full pass of model task proposals over the demo vault."""
    predicted = set()
    started = time.perf_counter()
    for file in scan_vault(DEMO_VAULT):
        parsed = parse_note(file.text, Path(file.rel_path).stem)
        for _text, evidence in propose_for_note(provider, parsed.title, parsed.body):
            predicted.add((file.rel_path, normalise(evidence)))
    result = score_task_predictions(predicted)
    result["seconds"] = time.perf_counter() - started
    return result


# --------------------------------------------------------------------------------- Q&A


def top_similarities(conn: sqlite3.Connection, provider: ModelProvider) -> list[dict]:
    """Best chunk similarity for every question: the signal the abstain threshold uses."""
    out = []
    for q in load("qa")["questions"]:
        hits = semantic_search(conn, provider, q["question"], 1)
        out.append(
            {
                "id": q["id"],
                "split": q["split"],
                "unanswerable": bool(q.get("unanswerable")),
                "similarity": hits[0].similarity if hits else 0.0,
            }
        )
    return out


def calibrate_threshold(similarities: list[dict]) -> dict:
    """Pick the abstain threshold on the dev split only, then report how it does on the
    held-out split. Balanced accuracy = mean of (answerable kept, unanswerable refused)."""

    def balanced_accuracy(rows: list[dict], threshold: float) -> float:
        answerable = [r for r in rows if not r["unanswerable"]]
        unanswerable = [r for r in rows if r["unanswerable"]]
        kept = _mean([float(r["similarity"] >= threshold) for r in answerable])
        refused = _mean([float(r["similarity"] < threshold) for r in unanswerable])
        return (kept + refused) / 2

    dev = [r for r in similarities if r["split"] == "dev"]
    heldout = [r for r in similarities if r["split"] == "heldout"]
    candidates = [i / 100 for i in range(0, 100)]
    best = max(candidates, key=lambda t: (balanced_accuracy(dev, t), -t))
    return {
        "threshold": best,
        "dev_balanced_accuracy": balanced_accuracy(dev, best),
        "heldout_balanced_accuracy": balanced_accuracy(heldout, best),
        "note": "Similarity alone separates answerable from unanswerable only roughly; "
        "the model's own refusal is the second line of defence.",
    }


def eval_qa(
    conn: sqlite3.Connection, provider: ModelProvider, top_k: int, abstain_threshold: float
) -> dict:
    """One full pass over the Q&A set."""
    rows = []
    started = time.perf_counter()
    for q in load("qa")["questions"]:
        answer = answer_question(conn, provider, q["question"], top_k, abstain_threshold)
        row = {
            "id": q["id"],
            "split": q["split"],
            "question": q["question"],
            "unanswerable": bool(q.get("unanswerable")),
            "abstained": answer.abstained,
            "reason": answer.reason,
            "answer": answer.text,
            "invalid_citations": answer.invalid_citations,
        }
        if not row["unanswerable"]:
            cited_paths = {answer.sources[n - 1].path for n in answer.cited}
            row["correct"] = (not answer.abstained) and metrics.facts_present(
                answer.text, q["facts"]
            )
            row["cites_right_note"] = q["source"] in cited_paths
            row["source_retrieved"] = q["source"] in {h.path for h in answer.sources}
        rows.append(row)

    def summarise(subset: list[dict]) -> dict:
        answerable = [r for r in subset if not r["unanswerable"]]
        unanswerable = [r for r in subset if r["unanswerable"]]
        answered = [r for r in subset if not r["abstained"]]
        return {
            "answerable_n": len(answerable),
            "unanswerable_n": len(unanswerable),
            "correct": _mean([float(r["correct"]) for r in answerable]),
            "cites_right_note": _mean([float(r["cites_right_note"]) for r in answerable]),
            "source_retrieved": _mean([float(r["source_retrieved"]) for r in answerable]),
            "wrongly_refused": _mean([float(r["abstained"]) for r in answerable]),
            "correctly_refused": _mean([float(r["abstained"]) for r in unanswerable]),
            "answers_with_invalid_citation": _mean(
                [float(bool(r["invalid_citations"])) for r in answered]
            ),
        }

    return {
        "summary": {
            "all": summarise(rows),
            "dev": summarise([r for r in rows if r["split"] == "dev"]),
            "heldout": summarise([r for r in rows if r["split"] == "heldout"]),
        },
        "seconds": time.perf_counter() - started,
        "failures": [
            r for r in rows
            if (r["unanswerable"] and not r["abstained"])
            or (not r["unanswerable"] and not r["correct"])
        ],
    }
