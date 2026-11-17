"""Evaluation command line.

    uv run python -m app.evaluate deterministic      # no model needed, same result every time
    uv run python -m app.evaluate live --runs 3      # needs Ollama; results vary between runs

The two kinds of result are written to separate reports and are never averaged together.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import date

from app.config import REPO_ROOT, load_settings
from app.evaluate import metrics, runners
from app.index.db import connect
from app.index.indexer import rescan
from app.providers.base import ProviderUnavailable
from app.providers.fake import FakeProvider
from app.providers.ollama import OllamaProvider

REPORTS = REPO_ROOT / "evals" / "reports"
CAVEAT = (
    "> **Read this first.** The demo vault has 40 short fictional notes written by the same "
    "person who wrote the questions. Scores on it show that the pipeline works and let two "
    "configurations be compared; they do **not** predict performance on a real vault.\n"
)


def pct(value: float) -> str:
    return "n/a" if value != value else f"{value:.3f}"  # NaN check


def retrieval_table(results: list[dict]) -> list[str]:
    lines = [
        "| Mode | Subset | n | recall@5 | MRR | nDCG@10 |",
        "|---|---|---|---|---|---|",
    ]
    for result in results:
        for subset, s in result["summary"].items():
            lines.append(
                f"| {result['mode']} | {subset} | {s['n']} | {pct(s['recall@5'])} | "
                f"{pct(s['mrr'])} | {pct(s['ndcg@10'])} |"
            )
    return lines


def miss_list(result: dict) -> list[str]:
    lines = [f"\nQueries where **{result['mode']}** missed a relevant note in the top 5:\n"]
    if not result["misses"]:
        return lines + ["- none"]
    for miss in result["misses"]:
        lines.append(
            f"- `{miss['id']}` ({miss['kind']}) \"{miss['query']}\" — wanted "
            f"{miss['relevant']}, top result was {miss['top'][:1]}"
        )
    return lines


def prf_table(rows: list[tuple[str, dict]]) -> list[str]:
    lines = ["| System | TP | FP | FN | Precision | Recall | F1 |", "|---|---|---|---|---|---|---|"]
    for name, r in rows:
        lines.append(
            f"| {name} | {r['tp']} | {r['fp']} | {r['fn']} | {pct(r['precision'])} | "
            f"{pct(r['recall'])} | {pct(r['f1'])} |"
        )
    return lines


def error_list(result: dict) -> list[str]:
    lines = []
    sections = (("False positives", "false_positives"), ("False negatives", "false_negatives"))
    for label, key in sections:
        lines.append(f"\n{label}:\n")
        lines += [f"- {item}" for item in result[key]] or ["- none"]
    return lines


def write(name: str, markdown: list[str], raw: dict) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.md").write_text("\n".join(markdown) + "\n")
    (REPORTS / f"{name}.json").write_text(json.dumps(raw, indent=2, default=str) + "\n")
    print(f"Wrote {REPORTS / name}.md and .json")


def run_deterministic() -> int:
    problems = runners.check_gold_sentences_exist()
    if problems:
        print("Gold data does not match the demo vault:\n  " + "\n  ".join(problems))
        return 1
    conn = connect(":memory:")
    provider = FakeProvider()
    rescan(conn, runners.DEMO_VAULT, provider)

    keyword = runners.eval_retrieval(conn, None, "keyword")
    fake_semantic = runners.eval_retrieval(conn, provider, "semantic")
    fake_hybrid = runners.eval_retrieval(conn, provider, "hybrid")
    checkbox = runners.eval_checkbox_parsing()
    baseline = runners.eval_task_keyword_baseline()

    md = [
        "# Deterministic evaluation report",
        "",
        "No model is involved in anything on this page, so re-running gives identical numbers.",
        "",
        CAVEAT,
        "## Retrieval — keyword search (SQLite FTS5, BM25)",
        "",
        "This is the real keyword search the app uses.",
        "",
        *retrieval_table([keyword]),
        *miss_list(keyword),
        "",
        "## Retrieval — pipeline check with the fake embedder",
        "",
        "These rows use `FakeProvider`, a hashed bag-of-words stand-in. It is **not** an "
        "embedding model and understands no meaning, so it is expected to fail paraphrase "
        "queries. The rows exist to prove the semantic and hybrid code paths run end to end. "
        "Real-model numbers are in the live report.",
        "",
        *retrieval_table([fake_semantic, fake_hybrid]),
        "",
        "## Task extraction — checkboxes",
        "",
        *prf_table([("Checkbox parser", checkbox)]),
        *error_list(checkbox),
        "",
        "## Task extraction — keyword-rule baseline for implicit tasks",
        "",
        "A rule with no model: a sentence is a task if it contains *need to / must / should / "
        "have to / remember to*. This is the bar the local model has to clear. "
        f"{baseline['ambiguous_predicted']} predictions fell on sentences labelled ambiguous "
        "and were not scored.",
        "",
        *prf_table([("Keyword rule", baseline)]),
        *error_list(baseline),
    ]
    write(
        "deterministic",
        md,
        {
            "retrieval": [keyword, fake_semantic, fake_hybrid],
            "checkbox": checkbox,
            "task_keyword_baseline": baseline,
        },
    )
    return 0


def spread_row(name: str, values: list[float]) -> str:
    s = metrics.mean_and_spread(values)
    return f"| {name} | {pct(s['mean'])} | {pct(s['std'])} | {pct(s['min'])} | {pct(s['max'])} |"


def run_live(runs: int) -> int:
    settings = load_settings()
    provider = OllamaProvider(settings.ollama_url, settings.embed_model, settings.chat_model)
    health = provider.health()
    if not health["ok"]:
        print(f"Live evaluation not run: {health['detail']}")
        return 2
    conn = connect(":memory:")
    try:
        report = rescan(conn, runners.DEMO_VAULT, provider)
        if report.embedding_error:
            raise ProviderUnavailable(report.embedding_error)
        retrieval = [
            runners.eval_retrieval(conn, provider, mode)
            for mode in ("keyword", "semantic", "hybrid")
        ]
        similarities = runners.top_similarities(conn, provider)
        calibration = runners.calibrate_threshold(similarities)
        task_runs = [runners.eval_task_proposals(provider) for _ in range(runs)]
        qa_runs = [
            runners.eval_qa(conn, provider, settings.top_k, settings.abstain_threshold)
            for _ in range(runs)
        ]
    except ProviderUnavailable as exc:
        print(f"Live evaluation stopped: {exc}")
        return 2

    baseline = runners.eval_task_keyword_baseline()
    qa_keys = [
        "correct", "cites_right_note", "source_retrieved", "wrongly_refused",
        "correctly_refused", "answers_with_invalid_citation",
    ]
    md = [
        "# Live-model evaluation report",
        "",
        f"- Date: {date.today().isoformat()}",
        f"- Machine: {platform.platform()} / {platform.machine()} / {platform.processor()}",
        f"- Profile: `{settings.profile}`",
        f"- Embedding model: `{settings.embed_model}`",
        f"- Chat model: `{settings.chat_model}` (temperature 0)",
        f"- Runs of each model-generated metric: {runs}",
        f"- Abstain threshold used: {settings.abstain_threshold}",
        "",
        CAVEAT,
        "Model output can change between runs even at temperature 0, so generated metrics "
        "are reported as mean, standard deviation, minimum and maximum over the runs.",
        "",
        "## Retrieval (one run; fixed for a given embedding model)",
        "",
        *retrieval_table(retrieval),
        *[line for result in retrieval[1:] for line in miss_list(result)],
        "",
        "## Abstain threshold calibration",
        "",
        f"Chosen on the dev split only: **{calibration['threshold']}** "
        f"(dev balanced accuracy {pct(calibration['dev_balanced_accuracy'])}, "
        f"held-out {pct(calibration['heldout_balanced_accuracy'])}). "
        "To use it, set `LNC_ABSTAIN_THRESHOLD` and run this report again; the Q&A numbers "
        "below used the threshold listed at the top.",
        "",
        "## Implicit task proposals",
        "",
        "| Metric | Mean | Std | Min | Max |",
        "|---|---|---|---|---|",
        *[spread_row(k, [r[k] for r in task_runs]) for k in ("precision", "recall", "f1")],
        "",
        f"Keyword-rule baseline (deterministic): precision {pct(baseline['precision'])}, "
        f"recall {pct(baseline['recall'])}, F1 {pct(baseline['f1'])}.",
        "",
        "Errors from the last run:",
        *error_list(task_runs[-1]),
        "",
        "## Grounded Q&A",
        "",
    ]
    for split in ("heldout", "dev", "all"):
        md += [
            f"### Split: {split}",
            "",
            "| Metric | Mean | Std | Min | Max |",
            "|---|---|---|---|---|",
            *[spread_row(k, [r["summary"][split][k] for r in qa_runs]) for k in qa_keys],
            "",
        ]
    md += ["Failures from the last run:", ""]
    md += [
        f"- `{f['id']}` \"{f['question']}\" → ({f['reason']}) {f['answer'][:160]}"
        for f in qa_runs[-1]["failures"]
    ] or ["- none"]
    md += [
        "",
        "## Timing",
        "",
        f"- Q&A set: {pct(metrics.mean_and_spread([r['seconds'] for r in qa_runs])['mean'])} s "
        "per pass (26 questions)",
        f"- Task proposals: "
        f"{pct(metrics.mean_and_spread([r['seconds'] for r in task_runs])['mean'])} s per pass "
        "(40 notes)",
    ]
    write(
        f"live-{settings.profile}",
        md,
        {
            "settings": {
                "profile": settings.profile, "embed_model": settings.embed_model,
                "chat_model": settings.chat_model, "runs": runs,
                "abstain_threshold": settings.abstain_threshold,
            },
            "retrieval": retrieval,
            "similarities": similarities,
            "calibration": calibration,
            "task_runs": task_runs,
            "qa_runs": qa_runs,
        },
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.evaluate")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("deterministic", help="no model needed")
    live = sub.add_parser("live", help="needs Ollama running with both models pulled")
    live.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    if args.command == "deterministic":
        return run_deterministic()
    if args.runs < 1:
        parser.error("--runs must be at least 1")
    return run_live(args.runs)


if __name__ == "__main__":
    sys.exit(main())
