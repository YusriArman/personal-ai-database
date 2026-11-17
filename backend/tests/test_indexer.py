import numpy as np

from app.index.indexer import rescan
from app.providers.base import ProviderUnavailable
from app.providers.fake import FakeProvider
from app.retrieve.search import keyword_search


class DownProvider(FakeProvider):
    def embed(self, texts):
        raise ProviderUnavailable("down")


def count(conn, sql):
    return conn.execute(sql).fetchone()[0]


def test_first_scan_indexes_everything(conn, vault, provider):
    report = rescan(conn, vault, provider)
    assert sorted(report.added) == ["Alpha.md", "Beta.md", "Gamma.md"]
    assert report.chunks_missing_embedding == 0 and report.embedding_error is None
    assert count(conn, "SELECT COUNT(*) FROM chunks") == report.chunks_embedded
    assert count(conn, "SELECT COUNT(*) FROM chunks_fts") == report.chunks_embedded


def test_second_scan_does_nothing(indexed, vault, provider):
    report = rescan(indexed, vault, provider)
    assert report.unchanged == 3 and report.chunks_embedded == 0
    assert not (report.added or report.updated or report.deleted)


def test_edit_add_delete_are_picked_up(indexed, vault, provider):
    (vault / "Beta.md").write_text("# Beta\n\nNow about submarines.\n")
    (vault / "Delta.md").write_text("# Delta\n\nNew note about volcanoes.\n")
    (vault / "Gamma.md").unlink()
    report = rescan(indexed, vault, provider)
    assert (report.added, report.updated, report.deleted) == (
        ["Delta.md"], ["Beta.md"], ["Gamma.md"],
    )
    assert [h.title for h in keyword_search(indexed, "submarines", 5)] == ["Beta"]
    assert keyword_search(indexed, "orbit", 5) == []  # old Beta text is gone
    assert keyword_search(indexed, "sourdough", 5) == []  # deleted note is gone
    assert [h.title for h in keyword_search(indexed, "volcanoes", 5)] == ["Delta"]
    # No orphan rows left in the keyword index.
    assert count(indexed, "SELECT COUNT(*) FROM chunks_fts") == count(
        indexed, "SELECT COUNT(*) FROM chunks"
    )


def test_embeddings_are_stored_normalised(indexed):
    blob = indexed.execute("SELECT embedding FROM chunks LIMIT 1").fetchone()[0]
    assert abs(float(np.linalg.norm(np.frombuffer(blob, dtype=np.float32))) - 1.0) < 1e-5


def test_model_down_still_builds_keyword_index_then_recovers(conn, vault, provider):
    report = rescan(conn, vault, DownProvider())
    assert report.embedding_error == "down" and report.chunks_missing_embedding > 0
    assert keyword_search(conn, "rockets", 5)
    recovered = rescan(conn, vault, provider)
    assert recovered.unchanged == 3 and recovered.chunks_missing_embedding == 0
    assert recovered.chunks_embedded > 0


def test_changing_embedding_model_re_embeds(indexed, vault):
    other = FakeProvider()
    other.embed_model = "another-model"
    report = rescan(indexed, vault, other)
    assert report.chunks_embedded == count(indexed, "SELECT COUNT(*) FROM chunks")


def test_hidden_and_obsidian_folders_are_skipped(conn, vault, provider):
    (vault / ".obsidian").mkdir()
    (vault / ".obsidian" / "x.md").write_text("config")
    assert "x.md" not in " ".join(rescan(conn, vault, provider).added)
