"""A deterministic stand-in for a model, used by tests and offline demos.

Embeddings are a hashed bag of words: texts that share words get similar vectors.
That is a real (if crude) lexical similarity, not semantic understanding, so retrieval
numbers measured with FakeProvider say nothing about a real embedding model.

`generate` returns scripted replies, or a rule-based reply built from the prompt, so
the Q&A and task pipelines can be exercised end to end without a model.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Callable

DIM = 256
WORD_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    "a an and are as at be by for from has have i in is it its of on or that the this to was "
    "we were what when where which who why will with you your do does did how my me".split()
)


def tokenize(text: str) -> list[str]:
    return [w for w in WORD_RE.findall(text.lower()) if w not in STOPWORDS]


def _bucket(word: str) -> int:
    return int.from_bytes(hashlib.md5(word.encode()).digest()[:4], "big") % DIM


class FakeProvider:
    embed_model = "fake-hash-embed"
    chat_model = "fake-rules"

    def __init__(self, script: Callable[[str], str] | list[str] | None = None) -> None:
        self._script = script
        self.prompts: list[str] = []  # every prompt seen, for assertions in tests

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vec = [0.0] * DIM
            for word in tokenize(text):
                vec[_bucket(word)] += 1.0
            norm = math.sqrt(sum(v * v for v in vec))
            vectors.append([v / norm for v in vec] if norm else vec)
        return vectors

    def generate(self, prompt: str, *, system: str = "", json_mode: bool = False) -> str:
        self.prompts.append(prompt)
        if callable(self._script):
            return self._script(prompt)
        if isinstance(self._script, list):
            if not self._script:
                raise AssertionError("FakeProvider script ran out of replies")
            return self._script.pop(0)
        return _rule_based_reply(prompt, json_mode)

    def health(self) -> dict:
        return {"ok": True, "detail": "fake provider (no model running)"}


def _rule_based_reply(prompt: str, json_mode: bool) -> str:
    if json_mode:
        # Task extraction: propose lines that contain an obvious commitment phrase.
        tasks = []
        for line in prompt.split("\n"):
            numbered = re.match(r"^\[(\d+)\]\s+(.*)$", line)
            if numbered and re.search(
                r"\b(need to|must|should|have to|remember to|todo)\b", numbered.group(2), re.I
            ):
                tasks.append({"sentence": int(numbered.group(1)), "task": numbered.group(2)})
        return json.dumps({"tasks": tasks})
    # Q&A: quote the first source and cite it.
    source = re.search(r"^\[1\][^\n]*\n(.+)$", prompt, re.M)
    if not source:
        return "NOT_IN_NOTES"
    return f"{source.group(1).strip()[:200]} [1]"
