"""Reference solution for exercise 3."""
import numpy as np


def normalise(vectors: np.ndarray) -> np.ndarray:
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    lengths[lengths == 0] = 1.0  # avoid dividing by zero; the row stays all zeros
    return vectors / lengths


def top_k(query: np.ndarray, vectors: np.ndarray, k: int) -> list[tuple[int, float]]:
    unit_rows = normalise(vectors.astype(float))
    unit_query = normalise(query.astype(float).reshape(1, -1))[0]
    similarities = unit_rows @ unit_query  # dot product of unit vectors = cosine
    order = np.argsort(-similarities, kind="stable")[:k]
    return [(int(i), float(similarities[i])) for i in order]
