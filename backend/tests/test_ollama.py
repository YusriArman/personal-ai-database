import json

import httpx
import pytest

from app.providers.base import ProviderUnavailable
from app.providers.ollama import OllamaProvider


def provider(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OllamaProvider("http://ollama.test", "embedder", "chatter:7b", client=client)


def test_embed_and_generate_send_the_expected_requests():
    seen = []

    def handler(request):
        body = json.loads(request.content)
        seen.append((request.url.path, body))
        if request.url.path == "/api/embed":
            return httpx.Response(200, json={"embeddings": [[1.0, 0.0]] * len(body["input"])})
        return httpx.Response(200, json={"response": "hello"})

    p = provider(handler)
    assert p.embed(["a", "b"]) == [[1.0, 0.0], [1.0, 0.0]]
    assert p.embed([]) == []
    assert p.generate("hi", system="sys", json_mode=True) == "hello"
    assert seen[0] == ("/api/embed", {"model": "embedder", "input": ["a", "b"]})
    path, body = seen[1]
    assert path == "/api/generate" and body["format"] == "json" and body["stream"] is False
    assert body["system"] == "sys" and body["options"]["temperature"] == 0


def test_errors_become_provider_unavailable():
    with pytest.raises(ProviderUnavailable, match="404"):
        provider(lambda r: httpx.Response(404, text="model not found")).generate("x")
    with pytest.raises(ProviderUnavailable, match="unexpected"):
        provider(lambda r: httpx.Response(200, json={"embeddings": []})).embed(["x"])


def test_health_reports_missing_models():
    tags = {"models": [{"name": "embedder:latest"}]}
    health = provider(lambda r: httpx.Response(200, json=tags)).health()
    assert health["ok"] is False and "chatter:7b" in health["detail"]
    tags["models"].append({"name": "chatter:7b"})
    assert provider(lambda r: httpx.Response(200, json=tags)).health()["ok"] is True
