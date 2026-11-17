"""Exercise 5 — validate the citations in a model's answer."""


def check_citations(answer: str, source_count: int) -> tuple[list[int], list[int]]:
    """Find every [n] marker in the answer.

    Return (valid, invalid): valid numbers satisfy 1 <= n <= source_count.
    Each list is in first-seen order with no repeats.
    """
    raise NotImplementedError("Write check_citations")


def strip_invalid(answer: str, invalid: list[int]) -> str:
    """Remove every invalid [n] marker, then collapse doubled spaces and trim."""
    raise NotImplementedError("Write strip_invalid")
