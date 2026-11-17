"""Exercise 6 — evaluation metrics from first principles."""


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    """Fraction of the relevant items that appear in the first k results."""
    raise NotImplementedError("Write recall_at_k")


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    """1 / position of the first relevant result (positions start at 1); 0 if none."""
    raise NotImplementedError("Write reciprocal_rank")


def precision_recall_f1(predicted: set[str], gold: set[str]) -> tuple[float, float, float]:
    """precision = correct / predicted, recall = correct / gold,
    f1 = 2pr / (p + r). Any division by zero gives 0.0."""
    raise NotImplementedError("Write precision_recall_f1")
