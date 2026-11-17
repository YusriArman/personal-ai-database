"""Grounded question answering.

The model is only allowed to answer from retrieved chunks, must cite them as [n], and
the code — not the model — checks that every citation points at a chunk that was
actually retrieved. There are two ways to refuse:

1. Before calling the model: the best chunk is not similar enough to the question.
2. The model itself replies NOT_IN_NOTES.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field

from app.providers.base import ModelProvider
from app.retrieve.search import Hit, hybrid_search

REFUSAL_TOKEN = "NOT_IN_NOTES"
REFUSAL_TEXT = "I could not find this in your notes."
CITATION_RE = re.compile(r"\[(\d+)\]")

SYSTEM_PROMPT = (
    "You answer questions using only the numbered sources from the user's own notes. "
    "Cite every claim with the source number in square brackets, like [1]. "
    f"If the sources do not contain the answer, reply with exactly {REFUSAL_TOKEN} and "
    "nothing else. Never use outside knowledge. Be concise."
)


@dataclass
class Answer:
    question: str
    text: str
    abstained: bool
    reason: str  # "answered", "no_sources", "low_similarity", "model_declined"
    sources: list[Hit] = field(default_factory=list)  # sources[i] is citation [i + 1]
    cited: list[int] = field(default_factory=list)  # valid citation numbers, in order
    invalid_citations: list[int] = field(default_factory=list)
    # False when an answer was given but nothing in it is backed by a valid citation.
    grounded: bool = False
    top_similarity: float | None = None


def build_prompt(question: str, sources: list[Hit]) -> str:
    blocks = []
    for number, hit in enumerate(sources, start=1):
        where = hit.title if not hit.heading else f"{hit.title} — {hit.heading}"
        blocks.append(f"[{number}] {where}\n{hit.text}")
    return "Sources:\n\n" + "\n\n".join(blocks) + f"\n\nQuestion: {question}\nAnswer:"


def check_citations(text: str, source_count: int) -> tuple[list[int], list[int]]:
    """Split the [n] markers in an answer into (valid, invalid) citation numbers."""
    valid: list[int] = []
    invalid: list[int] = []
    for match in CITATION_RE.finditer(text):
        number = int(match.group(1))
        bucket = valid if 1 <= number <= source_count else invalid
        if number not in bucket:
            bucket.append(number)
    return valid, invalid


def answer_question(
    conn: sqlite3.Connection,
    provider: ModelProvider,
    question: str,
    top_k: int = 5,
    abstain_threshold: float = 0.35,
) -> Answer:
    sources = hybrid_search(conn, provider, question, top_k)
    similarities = [h.similarity for h in sources if h.similarity is not None]
    top = max(similarities) if similarities else None

    if not sources:
        return Answer(question, REFUSAL_TEXT, True, "no_sources", top_similarity=top)
    if top is None or top < abstain_threshold:
        return Answer(question, REFUSAL_TEXT, True, "low_similarity", sources, top_similarity=top)

    reply = provider.generate(build_prompt(question, sources), system=SYSTEM_PROMPT).strip()
    if not reply or REFUSAL_TOKEN in reply:
        return Answer(question, REFUSAL_TEXT, True, "model_declined", sources, top_similarity=top)

    valid, invalid = check_citations(reply, len(sources))
    # Remove citation markers that point at nothing, so the UI never shows a dead reference.
    for number in invalid:
        reply = reply.replace(f"[{number}]", "")
    reply = re.sub(r"[ \t]{2,}", " ", reply).strip()
    return Answer(
        question=question,
        text=reply,
        abstained=False,
        reason="answered",
        sources=sources,
        cited=valid,
        invalid_citations=invalid,
        grounded=bool(valid),
        top_similarity=top,
    )
