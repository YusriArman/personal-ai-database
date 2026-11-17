"""Exercise 4 — reciprocal rank fusion."""


def rrf(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Fuse several ranked lists of ids into one.

    Each list adds 1 / (k + rank) to an id's score, where rank starts at 1.
    Return (id, score) pairs, highest score first; break ties by id, ascending.
    """
    raise NotImplementedError("Write rrf")
