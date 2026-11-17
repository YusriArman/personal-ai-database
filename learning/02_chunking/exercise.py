"""Exercise 2 — pack paragraphs into chunks."""


def pack_paragraphs(text: str, max_chars: int) -> list[str]:
    """Split text into paragraphs (separated by a blank line) and join neighbours
    with "\n\n" into chunks no longer than max_chars.

    - Never split inside a paragraph (assume none is longer than max_chars).
    - Keep paragraphs in order; drop empty ones.
    - Be greedy: add the next paragraph to the current chunk whenever it still fits.
    """
    raise NotImplementedError("Write pack_paragraphs")
