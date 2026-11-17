"""Run with:  uv run pytest ../learning/04_rank_fusion   (from backend/)"""
import pytest


def test_scores(target):
    fused = dict(target.rrf([["a", "b", "c"], ["c", "a"]], k=60))
    assert fused["a"] == pytest.approx(1 / 61 + 1 / 62)
    assert fused["b"] == pytest.approx(1 / 62)
    assert fused["c"] == pytest.approx(1 / 63 + 1 / 61)


def test_order_and_ties(target):
    assert [i for i, _ in target.rrf([["a", "b", "c"], ["c", "a"]])] == ["a", "c", "b"]
    assert [i for i, _ in target.rrf([["z"], ["y"]])] == ["y", "z"]  # tie -> by id
    assert target.rrf([]) == []


def test_agreement_beats_a_single_first_place(target):
    order = [i for i, _ in target.rrf([["solo", "both"], ["both", "other"]])]
    assert order[0] == "both"
