"""Keyword, semantic and hybrid search over chunks.

- keyword:  SQLite FTS5 with BM25 ranking.
- semantic: cosine similarity between the query embedding and every chunk embedding,
            computed by brute force in NumPy. At personal-vault scale (thousands of
            chunks) this is milliseconds and needs no vector database.
- hybrid:   reciprocal rank fusion (RRF) of the two ranked lists.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

import numpy as np

from app.index.indexer import to_blob
from app.providers.base import ModelProvider

MODES = ("keyword", "semantic", "hybrid")
RRF_K = 60  # the constant from the original RRF paper; larger = flatter weighting
WORD_RE = re.compile(r"\w+", re.UNICODE)


@dataclass
class Hit:
    chunk_id: int
    note_id: int
    path: str
    title: str
    heading: str
    text: str
    score: float  # meaning depends on mode: -bm25, cosine, or RRF sum
    snippet: str = ""
    # Cosine similarity when the semantic ranker saw this chunk, else None.
    similarity: float | None = None


def fts_query(query: str) -> str:
    """Turn free text into a safe FTS5 query: each word quoted, joined with OR.

    Quoting stops user text such as `AND`, `-` or `"` being read as FTS5 syntax.
    """
    words = WORD_RE.findall(query)
    return " OR ".join(f'"{w}"' for w in words)


def keyword_search(conn: sqlite3.Connection, query: str, limit: int) -> list[Hit]:
    match = fts_query(query)
    if not match:
        return []
    rows = conn.execute(
        """
        SELECT c.id AS chunk_id, n.id AS note_id, n.path, n.title, c.heading, c.text,
               bm25(chunks_fts, 3.0, 2.0, 1.0) AS rank,
               snippet(chunks_fts, 2, '<mark>', '</mark>', ' … ', 24) AS snippet
        FROM chunks_fts
        JOIN chunks c ON c.id = chunks_fts.rowid
        JOIN notes n ON n.id = c.note_id
        WHERE chunks_fts MATCH ?
        ORDER BY rank, c.id
        LIMIT ?
        """,
        (match, limit),
    ).fetchall()
    # bm25() is lower-is-better; negate so a higher score is always a better hit.
    return [
        Hit(
            chunk_id=r["chunk_id"],
            note_id=r["note_id"],
            path=r["path"],
            title=r["title"],
            heading=r["heading"],
            text=r["text"],
            score=-r["rank"],
            snippet=r["snippet"],
        )
        for r in rows
    ]


NO_EMBEDDINGS = (
    "No embeddings in the index yet. Start the local model and run a rescan; "
    "keyword search works in the meantime."
)


def has_embeddings(conn: sqlite3.Connection, embed_model: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM chunks WHERE embedding IS NOT NULL AND embed_model = ? LIMIT 1",
        (embed_model,),
    ).fetchone()
    return row is not None


def load_embeddings(conn: sqlite3.Connection, embed_model: str) -> tuple[list[int], np.ndarray]:
    """All chunk ids and an (n, dim) matrix of their normalised vectors."""
    rows = conn.execute(
        "SELECT id, embedding FROM chunks WHERE embedding IS NOT NULL AND embed_model = ? "
        "ORDER BY id",
        (embed_model,),
    ).fetchall()
    if not rows:
        return [], np.zeros((0, 0), dtype=np.float32)
    matrix = np.vstack([np.frombuffer(r["embedding"], dtype=np.float32) for r in rows])
    return [r["id"] for r in rows], matrix


def semantic_search(
    conn: sqlite3.Connection, provider: ModelProvider, query: str, limit: int
) -> list[Hit]:
    if not query.strip():
        return []
    ids, matrix = load_embeddings(conn, provider.embed_model)
    if not ids:
        return []
    query_vec = np.frombuffer(to_blob(provider.embed([query])[0]), dtype=np.float32)
    if query_vec.shape[0] != matrix.shape[1]:
        raise ValueError("Query embedding size does not match the index; run a rescan.")
    sims = matrix @ query_vec  # vectors are normalised, so the dot product is the cosine
    order = np.argsort(-sims, kind="stable")[:limit]
    hits: list[Hit] = []
    for i in order:
        row = conn.execute(
            "SELECT c.id AS chunk_id, n.id AS note_id, n.path, n.title, c.heading, c.text "
            "FROM chunks c JOIN notes n ON n.id = c.note_id WHERE c.id = ?",
            (ids[int(i)],),
        ).fetchone()
        sim = float(sims[int(i)])
        hits.append(
            Hit(
                chunk_id=row["chunk_id"],
                note_id=row["note_id"],
                path=row["path"],
                title=row["title"],
                heading=row["heading"],
                text=row["text"],
                score=sim,
                snippet=row["text"][:240],
                similarity=sim,
            )
        )
    return hits


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = RRF_K) -> list[tuple[int, float]]:
    """Fuse ranked id lists. Each list adds 1 / (k + rank) to an id's score (rank from 1).

    RRF only uses ranks, so it can combine BM25 scores and cosine similarities even
    though those numbers are on unrelated scales.
    """
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))


def hybrid_search(
    conn: sqlite3.Connection, provider: ModelProvider, query: str, limit: int
) -> list[Hit]:
    pool = max(limit * 4, 20)  # fuse deeper lists than we finally return
    keyword = keyword_search(conn, query, pool)
    semantic = semantic_search(conn, provider, query, pool)
    by_id: dict[int, Hit] = {h.chunk_id: h for h in semantic}
    for hit in keyword:
        if hit.chunk_id in by_id:
            # Keep the keyword snippet (it highlights matches) and the similarity.
            hit.similarity = by_id[hit.chunk_id].similarity
        by_id[hit.chunk_id] = hit
    fused = reciprocal_rank_fusion(
        [[h.chunk_id for h in keyword], [h.chunk_id for h in semantic]]
    )
    hits: list[Hit] = []
    for chunk_id, score in fused[:limit]:
        hit = by_id[chunk_id]
        hit.score = score
        hits.append(hit)
    return hits


def search(
    conn: sqlite3.Connection, provider: ModelProvider | None, query: str, mode: str, limit: int
) -> list[Hit]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if mode == "keyword":
        return keyword_search(conn, query, limit)
    if provider is None:
        raise ValueError("semantic and hybrid search need a model provider")
    if not has_embeddings(conn, provider.embed_model):
        # Say so instead of silently returning keyword-only results labelled "hybrid".
        raise ValueError(NO_EMBEDDINGS)
    if mode == "semantic":
        return semantic_search(conn, provider, query, limit)
    return hybrid_search(conn, provider, query, limit)


def group_by_note(hits: list[Hit]) -> list[Hit]:
    """Keep only the best-ranked chunk for each note, preserving order."""
    seen: set[int] = set()
    out: list[Hit] = []
    for hit in hits:
        if hit.note_id not in seen:
            seen.add(hit.note_id)
            out.append(hit)
    return out


def search_notes(
    conn: sqlite3.Connection, provider: ModelProvider | None, query: str, mode: str, limit: int
) -> list[Hit]:
    """Note-level results: search more chunks than needed, then one hit per note."""
    return group_by_note(search(conn, provider, query, mode, limit * 4))[:limit]
