import pytest

from app.retrieve.search import (
    fts_query,
    group_by_note,
    hybrid_search,
    keyword_search,
    reciprocal_rank_fusion,
    search,
    search_notes,
    semantic_search,
)


def test_fts_query_neutralises_operators():
    assert fts_query('rockets AND "fuel" -x') == '"rockets" OR "AND" OR "fuel" OR "x"'
    assert fts_query("  !!! ") == ""


def test_keyword_search_ranks_and_highlights(indexed):
    hits = keyword_search(indexed, "kerosene", 5)
    assert [h.title for h in hits] == ["Alpha"]
    assert "<mark>kerosene</mark>" in hits[0].snippet
    assert keyword_search(indexed, "", 5) == []
    assert keyword_search(indexed, '"unbalanced (', 5) == []  # no syntax error


def test_keyword_search_uses_stemming(indexed):
    assert [h.title for h in keyword_search(indexed, "orbits", 5)] == ["Beta"]


def test_semantic_search_orders_by_cosine(indexed, provider):
    hits = semantic_search(indexed, provider, "orbit around a planet", 3)
    assert hits[0].title == "Beta"
    sims = [h.similarity for h in hits]
    assert sims == sorted(sims, reverse=True) and all(-1.0001 <= s <= 1.0001 for s in sims)


def test_rrf_math():
    fused = reciprocal_rank_fusion([[1, 2, 3], [3, 1]], k=60)
    scores = dict(fused)
    assert scores[1] == pytest.approx(1 / 61 + 1 / 62)
    assert scores[3] == pytest.approx(1 / 63 + 1 / 61)
    assert scores[2] == pytest.approx(1 / 62)
    assert [i for i, _ in fused] == [1, 3, 2]
    assert reciprocal_rank_fusion([]) == []


def test_hybrid_puts_item_found_by_both_rankers_first(indexed, provider):
    hits = hybrid_search(indexed, provider, "rockets kerosene oxygen", 3)
    assert hits[0].title == "Alpha" and hits[0].similarity is not None


def test_mode_validation_and_note_grouping(indexed, provider):
    with pytest.raises(ValueError):
        search(indexed, provider, "x", "magic", 5)
    with pytest.raises(ValueError):
        search(indexed, None, "x", "semantic", 5)
    assert search(indexed, None, "rockets", "keyword", 5)


def test_semantic_modes_refuse_when_nothing_is_embedded(conn, vault, provider):
    from app.index.indexer import rescan

    rescan(conn, vault, None)  # keyword index only
    with pytest.raises(ValueError, match="No embeddings"):
        search(conn, provider, "rockets", "hybrid", 5)
    assert search(conn, provider, "rockets", "keyword", 5)


def test_note_grouping(indexed, provider):
    notes = search_notes(indexed, provider, "rockets", "hybrid", 5)
    assert len({h.note_id for h in notes}) == len(notes)
    assert group_by_note([]) == []
