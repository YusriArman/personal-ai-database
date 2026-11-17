"""Run with:  uv run pytest ../learning/06_metrics   (from backend/)"""
import pytest


def test_recall_at_k(target):
    assert target.recall_at_k(["a", "x", "b"], {"a", "b"}, 2) == 0.5
    assert target.recall_at_k(["a", "x", "b"], {"a", "b"}, 3) == 1.0
    assert target.recall_at_k([], {"a"}, 5) == 0.0


def test_reciprocal_rank(target):
    assert target.reciprocal_rank(["x", "y", "a"], {"a"}) == pytest.approx(1 / 3)
    assert target.reciprocal_rank(["a"], {"a"}) == 1.0
    assert target.reciprocal_rank(["x"], {"a"}) == 0.0


def test_precision_recall_f1(target):
    p, r, f = target.precision_recall_f1({"a", "b", "c", "d"}, {"a", "e"})
    assert (p, r) == (0.25, 0.5) and f == pytest.approx(1 / 3)
    assert target.precision_recall_f1(set(), {"a"}) == (0.0, 0.0, 0.0)
    assert target.precision_recall_f1({"a"}, {"a"}) == (1.0, 1.0, 1.0)
