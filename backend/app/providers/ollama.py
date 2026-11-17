"""Talks to a local Ollama server over HTTP. The only network calls in the app go to
the configured Ollama URL, which defaults to this machine."""

from __future__ import annotations

import httpx

from app.providers.base import ProviderUnavailable


class OllamaProvider:
    def __init__(
        self,
        base_url: str,
        embed_model: str,
        chat_model: str,
        timeout: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.embed_model = embed_model
        self.chat_model = chat_model
        self._client = client or httpx.Client(timeout=timeout)

    def _post(self, path: str, payload: dict) -> dict:
        try:
            response = self._client.post(f"{self.base_url}{path}", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:200]
            raise ProviderUnavailable(
                f"Ollama returned {exc.response.status_code} for {path}: {detail}"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderUnavailable(f"Cannot reach Ollama at {self.base_url}: {exc}") from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        data = self._post("/api/embed", {"model": self.embed_model, "input": texts})
        vectors = data.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(texts):
            raise ProviderUnavailable("Ollama returned an unexpected embedding response")
        return vectors

    def generate(self, prompt: str, *, system: str = "", json_mode: bool = False) -> str:
        payload: dict = {
            "model": self.chat_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        }
        if system:
            payload["system"] = system
        if json_mode:
            payload["format"] = "json"
        data = self._post("/api/generate", payload)
        return str(data.get("response", ""))

    def health(self) -> dict:
        try:
            response = self._client.get(f"{self.base_url}/api/tags", timeout=3.0)
            response.raise_for_status()
            installed = [m.get("name", "") for m in response.json().get("models", [])]
        except (httpx.HTTPError, ValueError) as exc:
            return {
                "ok": False,
                "detail": f"Ollama is not reachable at {self.base_url} ({exc.__class__.__name__}). "
                "Start it with `ollama serve`.",
            }

        def has(model: str) -> bool:
            return any(name == model or name.split(":")[0] == model for name in installed)

        missing = [m for m in (self.embed_model, self.chat_model) if not has(m)]
        if missing:
            return {
                "ok": False,
                "detail": "Missing models: " + ", ".join(missing) + ". Run `ollama pull <name>`.",
                "installed": installed,
            }
        return {"ok": True, "detail": "Ollama is running and both models are installed."}
