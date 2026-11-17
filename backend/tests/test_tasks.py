import json

import pytest

from app.index.indexer import rescan
from app.providers.fake import FakeProvider
from app.tasks import review
from app.tasks.extract import candidate_sentences, parse_proposals, propose_tasks


def test_checkbox_tasks_are_accepted_with_done_state(indexed):
    tasks = review.list_tasks(indexed, note_path="Alpha.md")
    assert [(t["text"], t["done"], t["status"], t["source"]) for t in tasks] == [
        ("Order the nozzle", False, "accepted", "checkbox"),
        ("Weld the tank", True, "accepted", "checkbox"),
    ]


def test_ticking_and_removing_a_checkbox_follows_the_file(indexed, vault, provider):
    (vault / "Alpha.md").write_text("# Alpha\n- [x] Order the nozzle\n")
    rescan(indexed, vault, provider)
    tasks = review.list_tasks(indexed, note_path="Alpha.md")
    assert [(t["text"], t["done"]) for t in tasks] == [("Order the nozzle", True)]


def test_candidate_sentences_skip_headings_code_and_checkboxes():
    body = "# Title\n- [ ] box\nI need to call Sam. It rained.\n```\nI must not appear.\n```\n"
    assert candidate_sentences(body) == ["I need to call Sam.", "It rained."]


def test_parse_proposals_rejects_anything_without_real_evidence():
    sentences = ["I need to call Sam.", "It rained."]
    reply = json.dumps({"tasks": [
        {"sentence": 1, "task": "Call Sam"},
        {"sentence": 9, "task": "Invented"},       # no such sentence
        {"sentence": "2", "task": "wrong type"},
        {"sentence": 1, "task": "duplicate"},
        {"sentence": 2, "task": "  "},
    ]})
    assert parse_proposals(reply, sentences) == [("Call Sam", "I need to call Sam.")]
    assert parse_proposals("not json", sentences) == []
    assert parse_proposals('{"tasks": "nope"}', sentences) == []
    assert parse_proposals("[1, 2]", sentences) == []


def test_model_proposals_are_pending_until_reviewed(indexed, provider):
    result = propose_tasks(indexed, provider)
    assert result == {"notes_analysed": 3, "new_proposals": 1}
    pending = review.list_tasks(indexed, status="pending")
    assert [t["evidence"] for t in pending] == ["I need to email Dana about the launch window."]
    assert pending[0]["source"] == "model"
    # Unchanged notes are not sent to the model again.
    assert propose_tasks(indexed, provider) == {"notes_analysed": 0, "new_proposals": 0}


def test_review_decision_survives_a_rescan_of_an_edited_note(indexed, vault, provider):
    propose_tasks(indexed, provider)
    task = review.list_tasks(indexed, status="pending")[0]
    review.update_task(indexed, task["id"], status="rejected")
    with (vault / "Beta.md").open("a") as f:
        f.write("\nMore text about moons.\n")
    rescan(indexed, vault, provider)
    propose_tasks(indexed, provider)
    again = review.get_task(indexed, task["id"])
    assert again["status"] == "rejected" and not again["orphaned"]
    assert review.list_tasks(indexed, status="pending") == []


def test_accepted_proposal_is_marked_orphaned_when_its_sentence_goes(indexed, vault, provider):
    propose_tasks(indexed, provider)
    task = review.list_tasks(indexed, status="pending")[0]
    review.update_task(indexed, task["id"], status="accepted", text="Email Dana")
    (vault / "Beta.md").write_text("# Beta\n\nNothing to do here.\n")
    rescan(indexed, vault, provider)
    propose_tasks(indexed, provider)
    kept = review.get_task(indexed, task["id"])
    assert kept["orphaned"] and kept["text"] == "Email Dana"


def test_unreviewed_proposal_disappears_with_its_note(indexed, vault, provider):
    propose_tasks(indexed, provider)
    (vault / "Beta.md").unlink()
    rescan(indexed, vault, provider)
    assert review.list_tasks(indexed, status="pending") == []


def test_update_validation_and_export(indexed):
    task = review.list_tasks(indexed)[0]
    with pytest.raises(ValueError):
        review.update_task(indexed, task["id"], status="maybe")
    with pytest.raises(ValueError):
        review.update_task(indexed, task["id"], text="   ")
    assert review.update_task(indexed, 99999, status="accepted") is None
    assert review.export_markdown(indexed) == (
        "# Tasks\n\n## Alpha\n- [ ] Order the nozzle\n- [x] Weld the tank\n"
    )


def test_malformed_model_output_creates_no_tasks(indexed):
    result = propose_tasks(indexed, FakeProvider(script=lambda prompt: "I refuse to give JSON"))
    assert result["new_proposals"] == 0
