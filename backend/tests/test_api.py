import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.config import Settings
from app.providers.base import ProviderUnavailable
from app.providers.fake import FakeProvider
from app.providers.ollama import OllamaProvider


def settings(tmp_path, vault, **over):
    base = dict(
        vault_path=vault, db_path=tmp_path / "t.db", provider="fake",
        ollama_url="http://127.0.0.1:9", embed_model="e", chat_model="c",
        profile="m4", abstain_threshold=0.1, top_k=5,
    )
    return Settings(**{**base, **over})


@pytest.fixture
def client(tmp_path, vault):
    return TestClient(create_app(settings(tmp_path, vault), FakeProvider()))


def test_full_flow(client):
    assert client.get("/api/status").json()["notes"] == 0
    report = client.post("/api/rescan").json()
    assert len(report["added"]) == 3

    status = client.get("/api/status").json()
    assert status["notes"] == 3 and status["chunks"] == status["chunks_embedded"]
    assert status["broken_links"] == 1 and status["model"]["ok"]

    for mode in ("keyword", "semantic", "hybrid"):
        results = client.get("/api/search", params={"q": "rockets kerosene", "mode": mode}).json()
        assert results["results"][0]["title"] == "Alpha", mode
    assert client.get("/api/search", params={"q": "x", "mode": "bad"}).status_code == 400

    notes = client.get("/api/notes").json()
    alpha = next(n for n in notes if n["title"] == "Alpha")
    detail = client.get(f"/api/notes/{alpha['id']}").json()
    assert [n["title"] for n in detail["outgoing"]] == ["Beta"]
    assert [b["target"] for b in detail["broken"]] == ["Missing Note"]
    assert len(detail["tasks"]) == 2 and detail["tags"] == ["space"]
    assert client.get("/api/notes/999").status_code == 404

    answer = client.post("/api/ask", json={"question": "What do rockets burn?"}).json()
    assert not answer["abstained"] and answer["cited"] == [1]
    assert client.post("/api/ask", json={"question": " "}).status_code == 400

    assert client.post("/api/tasks/propose").json()["new_proposals"] == 1
    pending = client.get("/api/tasks", params={"status": "pending"}).json()
    patched = client.patch(f"/api/tasks/{pending[0]['id']}", json={"status": "accepted"}).json()
    assert patched["status"] == "accepted"
    assert client.patch("/api/tasks/1", json={"status": "nope"}).status_code == 400
    assert client.patch("/api/tasks/999", json={"status": "accepted"}).status_code == 404
    assert "- [ ] I need to email Dana" in client.get("/api/tasks/export").text


def test_missing_vault_is_a_clear_error(tmp_path):
    app = create_app(settings(tmp_path, tmp_path / "nowhere"), FakeProvider())
    response = TestClient(app).post("/api/rescan")
    assert response.status_code == 400 and "Vault folder not found" in response.json()["detail"]


def test_ollama_down_degrades_to_keyword_search(tmp_path, vault):
    def refuse(request):
        raise httpx.ConnectError("refused")

    provider = OllamaProvider(
        "http://127.0.0.1:9", "e", "c", client=httpx.Client(transport=httpx.MockTransport(refuse))
    )
    client = TestClient(create_app(settings(tmp_path, vault, provider="ollama"), provider))
    report = client.post("/api/rescan").json()
    assert report["embedding_error"] and report["chunks_missing_embedding"] > 0
    status = client.get("/api/status").json()
    assert status["model"]["ok"] is False and "ollama serve" in status["model"]["detail"]
    ok = client.get("/api/search", params={"q": "rockets", "mode": "keyword"})
    assert ok.status_code == 200 and ok.json()["results"]
    # Nothing was embedded, so semantic features say so rather than pretending.
    hybrid = client.get("/api/search", params={"q": "rockets", "mode": "hybrid"})
    assert hybrid.status_code == 409 and "No embeddings" in hybrid.json()["detail"]
    assert client.post("/api/ask", json={"question": "rockets?"}).status_code == 409
    assert client.post("/api/tasks/propose").status_code == 503


def test_model_going_down_after_indexing_gives_503(tmp_path, vault):
    class Flaky(FakeProvider):
        down = False

        def embed(self, texts):
            if self.down:
                raise ProviderUnavailable("gone")
            return super().embed(texts)

    provider = Flaky()
    client = TestClient(create_app(settings(tmp_path, vault), provider))
    client.post("/api/rescan")
    provider.down = True
    response = client.get("/api/search", params={"q": "rockets", "mode": "semantic"})
    assert response.status_code == 503 and "Local model unavailable" in response.json()["detail"]
    assert client.post("/api/ask", json={"question": "rockets?"}).status_code == 503
    assert client.get("/api/search", params={"q": "rockets", "mode": "keyword"}).status_code == 200
