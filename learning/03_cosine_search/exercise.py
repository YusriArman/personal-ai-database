"""Exercise 3 — rank vectors by cosine similarity, using NumPy."""
import numpy as np


def normalise(vectors: np.ndarray) -> np.ndarray:
    """Scale each row of an (n, d) array to length 1. A row of zeros stays zeros."""
    raise NotImplementedError("Write normalise")


def top_k(query: np.ndarray, vectors: np.ndarray, k: int) -> list[tuple[int, float]]:
    """Return (row index, cosine similarity) for the k rows most similar to `query`,
    best first. Neither input is normalised when it arrives."""
    raise NotImplementedError("Write top_k")
