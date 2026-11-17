from app.connect import links
from app.index.indexer import rescan


def note_id(conn, title):
    return conn.execute("SELECT id FROM notes WHERE title = ?", (title,)).fetchone()[0]


def test_outgoing_backlinks_and_broken(indexed):
    alpha, beta = note_id(indexed, "Alpha"), note_id(indexed, "Beta")
    assert [n["title"] for n in links.outgoing(indexed, alpha)] == ["Beta"]
    assert [n["title"] for n in links.backlinks(indexed, beta)] == ["Alpha"]
    assert [b["target"] for b in links.broken(indexed, alpha)] == ["Missing Note"]
    assert links.broken(indexed, beta) == []


def test_adding_a_note_repairs_a_broken_link(indexed, vault, provider):
    (vault / "Missing Note.md").write_text("now I exist")
    rescan(indexed, vault, provider)
    assert links.broken(indexed) == []


def test_deleting_a_note_breaks_links_to_it(indexed, vault, provider):
    (vault / "Beta.md").unlink()
    rescan(indexed, vault, provider)
    assert sorted(b["target"] for b in links.broken(indexed)) == ["Beta", "Missing Note"]


def test_suggestions_exclude_self_and_linked_notes(indexed, provider):
    alpha, beta, gamma = (note_id(indexed, t) for t in ("Alpha", "Beta", "Gamma"))
    ids = [s["id"] for s in links.suggestions(indexed, alpha, provider.embed_model, 5, -1.0)]
    assert alpha not in ids and beta not in ids  # Beta is already linked from Alpha
    assert ids == [gamma]
    # A high bar removes weak suggestions entirely.
    assert links.suggestions(indexed, alpha, provider.embed_model, 5, 0.99) == []


def test_demo_vault_links(demo):
    monitor = note_id(demo, "Greenhouse Monitor")
    assert "Sensor Calibration Log" in [n["title"] for n in links.backlinks(demo, monitor)]
    assert [b["target"] for b in links.broken(demo)] == ["Motor Driver Datasheet"]
