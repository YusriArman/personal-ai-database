"""Run with:  uv run pytest ../learning/03_cosine_search   (from backend/)"""
import numpy as np
import pytest


def test_normalise(target):
    out = target.normalise(np.array([[3.0, 4.0], [0.0, 0.0], [0.0, 2.0]]))
    assert out.tolist() == [[0.6, 0.8], [0.0, 0.0], [0.0, 1.0]]


def test_top_k_orders_by_angle_not_length(target):
    vectors = np.array([[10.0, 0.0], [1.0, 1.0], [0.0, 5.0], [-1.0, 0.0]])
    result = target.top_k(np.array([2.0, 0.0]), vectors, 3)
    assert [i for i, _ in result] == [0, 1, 2]
    assert result[0][1] == pytest.approx(1.0)
    assert result[1][1] == pytest.approx(2 ** -0.5)
    assert result[2][1] == pytest.approx(0.0)


def test_top_k_larger_than_data(target):
    assert len(target.top_k(np.array([1.0, 0.0]), np.array([[1.0, 0.0]]), 5)) == 1
