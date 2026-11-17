"""Supervised-learning experiment: can a simple model tell what kind of note it is?

This is a learning exercise that sits beside the app; nothing in the app uses it.

    cd backend && uv run python ../experiments/note_classifier/train.py

Task:     classify a note as project / meeting / journal / reference.
Features: TF-IDF of the note body. Frontmatter and the folder name are NOT used,
          because the label lives there and using it would be cheating (label leakage).
Model:    multinomial logistic regression.
Compared against two baselines, because an accuracy number means nothing on its own.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

# Reuse the app's own parser so the experiment sees exactly what the app sees.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

from app.ingest.parser import parse_note  # noqa: E402
from app.ingest.scanner import scan_vault  # noqa: E402

HERE = Path(__file__).resolve().parent
VAULT = HERE.parents[1] / "demo_vault"
SEED = 0
FOLDS = 5
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def load_dataset() -> tuple[list[str], list[str], list[str]]:
    texts, labels, paths = [], [], []
    for file in scan_vault(VAULT):
        note = parse_note(file.text, Path(file.rel_path).stem)
        label = note.frontmatter.get("type")
        if not label:
            continue
        texts.append(note.body)
        labels.append(str(label))
        paths.append(file.rel_path)
    return texts, labels, paths


def keyword_rule(text: str) -> str:
    """A hand-written baseline: the kind of rule you would write in five minutes."""
    lowered = text.lower()
    if "attendees" in lowered or "## decisions" in lowered:
        return "meeting"
    if not text.lstrip().startswith("#"):
        return "journal"  # journal entries have no heading
    if "`" in text or "##" in text and "- " in text and "i " not in lowered:
        return "reference"
    return "project"


def build_model():
    return make_pipeline(
        TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2), min_df=2),
        LogisticRegression(max_iter=1000, C=10.0, random_state=SEED),
    )


def main() -> None:
    texts, labels, paths = load_dataset()
    y = np.array(labels)
    classes = sorted(set(labels))
    counts = Counter(labels)

    # Stratified k-fold: every note is predicted exactly once by a model that never saw it.
    folds = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    predicted = cross_val_predict(build_model(), texts, y, cv=folds)

    majority = np.array([counts.most_common(1)[0][0]] * len(y))
    rule = np.array([keyword_rule(t) for t in texts])

    def scores(pred: np.ndarray) -> dict:
        return {
            "accuracy": float((pred == y).mean()),
            "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
        }

    # Per-fold accuracy shows how unstable the estimate is with 8 test notes per fold.
    fold_acc = []
    for train_idx, test_idx in folds.split(texts, y):
        model = build_model().fit([texts[i] for i in train_idx], y[train_idx])
        fold_acc.append(float((model.predict([texts[i] for i in test_idx]) == y[test_idx]).mean()))

    # What did the model learn? Fit once on everything and read the largest weights.
    full = build_model().fit(texts, y)
    vocab = np.array(full[0].get_feature_names_out())
    top_terms = {
        cls: vocab[np.argsort(full[1].coef_[i])[::-1][:8]].tolist()
        for i, cls in enumerate(full[1].classes_)
    }

    # Leakage probe: meeting notes carry a date in their title line. Does removing dates matter?
    no_dates = [DATE_RE.sub("", t) for t in texts]
    predicted_no_dates = cross_val_predict(build_model(), no_dates, y, cv=folds)

    matrix = confusion_matrix(y, predicted, labels=classes)
    wrong = [
        {"path": p, "true": t, "predicted": q}
        for p, t, q in zip(paths, y.tolist(), predicted.tolist(), strict=True)
        if t != q
    ]
    results = {
        "n_notes": len(y),
        "class_counts": dict(counts),
        "folds": FOLDS,
        "majority_baseline": scores(majority),
        "keyword_rule_baseline": scores(rule),
        "tfidf_logreg": scores(predicted),
        "tfidf_logreg_fold_accuracy": fold_acc,
        "tfidf_logreg_dates_removed": scores(predicted_no_dates),
        "confusion_matrix": {"labels": classes, "rows_true_cols_predicted": matrix.tolist()},
        "top_terms": top_terms,
        "misclassified": wrong,
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n")

    def row(name: str, s: dict) -> str:
        return f"| {name} | {s['accuracy']:.3f} | {s['macro_f1']:.3f} |"

    lines = [
        "# Note-type classifier — results",
        "",
        f"Generated by `train.py` (seed {SEED}). {len(y)} notes, "
        + ", ".join(f"{counts[c]} {c}" for c in classes)
        + f". {FOLDS}-fold stratified cross-validation: each note is predicted by a model "
        "trained without it.",
        "",
        "| System | Accuracy | Macro F1 |",
        "|---|---|---|",
        row("Majority class (always the most common label)", results["majority_baseline"]),
        row("Hand-written keyword rule", results["keyword_rule_baseline"]),
        row("TF-IDF + logistic regression", results["tfidf_logreg"]),
        row("TF-IDF + logistic regression, dates removed", results["tfidf_logreg_dates_removed"]),
        "",
        "Accuracy per fold (8 notes each): " + ", ".join(f"{a:.3f}" for a in fold_acc),
        "",
        "## Confusion matrix (rows = true, columns = predicted)",
        "",
        "| | " + " | ".join(classes) + " |",
        "|---|" + "---|" * len(classes),
        *[
            f"| **{cls}** | " + " | ".join(str(v) for v in matrix[i]) + " |"
            for i, cls in enumerate(classes)
        ],
        "",
        "## Strongest terms per class",
        "",
        *[f"- **{cls}**: {', '.join(terms)}" for cls, terms in top_terms.items()],
        "",
        "## Misclassified notes",
        "",
        *([f"- `{w['path']}`: true {w['true']}, predicted {w['predicted']}" for w in wrong]
          or ["- none"]),
    ]
    (HERE / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
