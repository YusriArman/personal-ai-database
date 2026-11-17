"""HTTP API. Run with:  uv run uvicorn app.api.main:app --reload  (from backend/)."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from dataclasses import asdict

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.answer.qa import answer_question
from app.config import Settings, load_settings
from app.connect import links
from app.index.db import connect
from app.index.indexer import rescan
from app.providers.base import ModelProvider, ProviderUnavailable
from app.providers.fake import FakeProvider
from app.providers.ollama import OllamaProvider
from app.retrieve.search import MODES, NO_EMBEDDINGS, has_embeddings, search_notes
from app.tasks import review
from app.tasks.extract import propose_tasks


def make_provider(settings: Settings) -> ModelProvider:
    if settings.provider == "fake":
        return FakeProvider()
    if settings.provider == "ollama":
        return OllamaProvider(settings.ollama_url, settings.embed_model, settings.chat_model)
    raise ValueError(f"LNC_PROVIDER must be 'ollama' or 'fake', got {settings.provider!r}")


class AskBody(BaseModel):
    question: str


class TaskPatch(BaseModel):
    status: str | None = None
    text: str | None = None


def create_app(settings: Settings | None = None, provider: ModelProvider | None = None) -> FastAPI:
    settings = settings or load_settings()
    provider = provider or make_provider(settings)
    app = FastAPI(title="Local Notes Companion")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def db() -> Iterator[sqlite3.Connection]:
        conn = connect(settings.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def model_error(exc: ProviderUnavailable) -> HTTPException:
        return HTTPException(status_code=503, detail=f"Local model unavailable: {exc}")

    @app.get("/api/status")
    def status(conn: sqlite3.Connection = Depends(db)) -> dict:
        count = lambda sql, *p: conn.execute(sql, p).fetchone()[0]  # noqa: E731
        return {
            "vault": str(settings.vault_path),
            "vault_exists": settings.vault_path.is_dir(),
            "profile": settings.profile,
            "provider": settings.provider,
            "embed_model": provider.embed_model,
            "chat_model": provider.chat_model,
            "model": provider.health(),
            "notes": count("SELECT COUNT(*) FROM notes"),
            "chunks": count("SELECT COUNT(*) FROM chunks"),
            "chunks_embedded": count(
                "SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL AND embed_model = ?",
                provider.embed_model,
            ),
            "broken_links": count("SELECT COUNT(*) FROM links WHERE target_id IS NULL"),
            "tasks_pending": count("SELECT COUNT(*) FROM tasks WHERE status = 'pending'"),
            "notes_awaiting_task_proposals": count(
                "SELECT COUNT(*) FROM notes WHERE proposed_hash IS NOT content_hash"
            ),
        }

    @app.post("/api/rescan")
    def do_rescan(conn: sqlite3.Connection = Depends(db)) -> dict:
        try:
            return rescan(conn, settings.vault_path, provider).as_dict()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/search")
    def do_search(
        q: str,
        mode: str = "hybrid",
        k: int = Query(10, ge=1, le=50),
        conn: sqlite3.Connection = Depends(db),
    ) -> dict:
        if mode not in MODES:
            raise HTTPException(status_code=400, detail=f"mode must be one of {list(MODES)}")
        try:
            hits = search_notes(conn, provider, q, mode, k)
        except ProviderUnavailable as exc:
            raise model_error(exc) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"query": q, "mode": mode, "results": [asdict(h) for h in hits]}

    @app.get("/api/notes")
    def list_notes(conn: sqlite3.Connection = Depends(db)) -> list[dict]:
        rows = conn.execute("SELECT id, path, title, tags FROM notes ORDER BY title")
        return [
            {"id": r["id"], "path": r["path"], "title": r["title"], "tags": json.loads(r["tags"])}
            for r in rows
        ]

    @app.get("/api/notes/{note_id}")
    def get_note(note_id: int, conn: sqlite3.Connection = Depends(db)) -> dict:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Note not found")
        return {
            "id": row["id"],
            "path": row["path"],
            "title": row["title"],
            "body": row["body"],
            "tags": json.loads(row["tags"]),
            "outgoing": links.outgoing(conn, note_id),
            "backlinks": links.backlinks(conn, note_id),
            "broken": links.broken(conn, note_id),
            "suggestions": links.suggestions(conn, note_id, provider.embed_model),
            "tasks": review.list_tasks(conn, note_path=row["path"]),
        }

    @app.get("/api/links/broken")
    def broken_links(conn: sqlite3.Connection = Depends(db)) -> list[dict]:
        return links.broken(conn)

    @app.post("/api/ask")
    def ask(body: AskBody, conn: sqlite3.Connection = Depends(db)) -> dict:
        if not body.question.strip():
            raise HTTPException(status_code=400, detail="Question is empty")
        if not has_embeddings(conn, provider.embed_model):
            raise HTTPException(status_code=409, detail=NO_EMBEDDINGS)
        try:
            answer = answer_question(
                conn, provider, body.question, settings.top_k, settings.abstain_threshold
            )
        except ProviderUnavailable as exc:
            raise model_error(exc) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return asdict(answer)

    @app.get("/api/tasks")
    def tasks(status: str | None = None, conn: sqlite3.Connection = Depends(db)) -> list[dict]:
        try:
            return review.list_tasks(conn, status=status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/tasks/propose")
    def propose(conn: sqlite3.Connection = Depends(db)) -> dict:
        try:
            return propose_tasks(conn, provider)
        except ProviderUnavailable as exc:
            raise model_error(exc) from exc

    @app.get("/api/tasks/export", response_class=PlainTextResponse)
    def export(conn: sqlite3.Connection = Depends(db)) -> str:
        return review.export_markdown(conn)

    @app.patch("/api/tasks/{task_id}")
    def patch_task(
        task_id: int, body: TaskPatch, conn: sqlite3.Connection = Depends(db)
    ) -> dict:
        try:
            task = review.update_task(conn, task_id, status=body.status, text=body.text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    return app


app = create_app()
