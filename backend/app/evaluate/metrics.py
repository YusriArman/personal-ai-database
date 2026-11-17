"""Evaluation metrics as small pure functions. Each one is a few lines on purpose:
you should be able to check any reported number by hand."""

from __future__ import annotations

import math
from statistics import mean, pstdev


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    """Fraction of the relevant items that appear in the top k."""
    if not relevant:
        raise ValueError("a query needs at least one relevant item")
    return len(set(ranked[:k]) & relevant) / len(relevant)


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    """1 / rank of the first relevant item, or 0 if none was returned."""
    for rank, item in enumerate(ranked, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    """Normalised discounted cumulative gain with binary relevance.

    A relevant item at rank r earns 1 / log2(r + 1); the total is divided by the best
    possible total, so 1.0 means every relevant item is ranked as high as it can be.
    """
    if not relevant:
        raise ValueError("a query needs at least one relevant item")
    dcg = sum(1 / math.log2(r + 1) for r, item in enumerate(ranked[:k], 1) if item in relevant)
    ideal = sum(1 / math.log2(r + 1) for r in range(1, min(len(relevant), k) + 1))
    return dcg / ideal


def precision_recall_f1(predicted: set, gold: set, ignore: set | None = None) -> dict:
    """Set-based precision, recall and F1.

    Items in `ignore` (ambiguous cases) are removed from the predictions first, so
    predicting one is neither rewarded nor punished.
    """
    predicted = predicted - (ignore or set())
    tp = len(predicted & gold)
    fp = len(predicted - gold)
    fn = len(gold - predicted)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def facts_present(answer: str, facts: list) -> bool:
    """True if every fact is in the answer. A fact given as a list passes if any one
    of its alternatives is present. Matching is case-insensitive substring matching:
    crude, but transparent — it can be fooled by an answer that mentions the right
    number in the wrong context."""
    text = answer.lower()
    for fact in facts:
        options = fact if isinstance(fact, list) else [fact]
        if not any(str(option).lower() in text for option in options):
            return False
    return True


def mean_and_spread(values: list[float]) -> dict:
    """Mean, population standard deviation, min and max across repeated runs."""
    if not values:
        raise ValueError("no values")
    return {
        "mean": mean(values),
        "std": pstdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
        "runs": len(values),
    }
