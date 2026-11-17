"""The seam between the app and any model.

The app only ever talks to a ModelProvider. Real use plugs in OllamaProvider;
tests plug in FakeProvider, so the deterministic suite needs no model at all.
"""

from __future__ import annotations

from typing import Protocol


class ProviderUnavailable(RuntimeError):
    """The local model server could not be reached or returned an error."""


class ModelProvider(Protocol):
    embed_model: str
    chat_model: str

    def embed(self, texts: list[str]) -> list[list[float]]:
        """One embedding vector per input text."""
        ...

    def generate(self, prompt: str, *, system: str = "", json_mode: bool = False) -> str:
        """A completion for the prompt. With json_mode the reply must be JSON text."""
        ...

    def health(self) -> dict:
        """{'ok': bool, 'detail': str, ...} — never raises."""
        ...
