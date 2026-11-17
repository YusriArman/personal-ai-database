import math

import pytest

from app.evaluate import metrics, runners


def test_recall_at_k():
    assert metrics.recall_at_k(["a", "x", "b"], {"a", "b"}, 2) == 0.5
    assert metrics.recall_at_k(["a", "x", "b"], {"a", "b"}, 3) == 1.0
    with pytest.raises(ValueError):
        metrics.recall_at_k(["a"], set(), 1)


def test_reciprocal_rank():
    assert metrics.reciprocal_rank(["x", "y", "a"], {"a"}) == pytest.approx(1 / 3)
    assert metrics.reciprocal_rank(["x"], {"a"}) == 0.0


def test_ndcg_hand_worked():
    # Relevant at ranks 2 and 3; ideal would be ranks 1 and 2.
    dcg = 1 / math.log2(3) + 1 / math.log2(4)
    ideal = 1 / math.log2(2) + 1 / math.log2(3)
    assert metrics.ndcg_at_k(["x", "a", "b"], {"a", "b"}, 10) == pytest.approx(dcg / ideal)
    assert metrics.ndcg_at_k(["a", "b"], {"a", "b"}, 10) == pytest.approx(1.0)
    assert metrics.ndcg_at_k(["x"], {"a"}, 10) == 0.0


def test_precision_recall_f1_and_ignored_items():
    r = metrics.precision_recall_f1({"a", "b", "maybe"}, {"a", "c"}, ignore={"maybe"})
    assert (r["tp"], r["fp"], r["fn"]) == (1, 1, 1)
    assert r["precision"] == 0.5 and r["recall"] == 0.5 and r["f1"] == 0.5
    empty = metrics.precision_recall_f1(set(), {"a"})
    assert empty["precision"] == 0.0 and empty["f1"] == 0.0


def test_facts_present_handles_alternatives_and_case():
    facts = [["2 June", "June 2"], "1500"]
    assert metrics.facts_present("It starts on June 2 and pays RM1500.", facts)
    assert not metrics.facts_present("It pays RM1500.", facts)
    assert metrics.facts_present("OPERATING systems", ["Operating Systems"])


def test_mean_and_spread():
    s = metrics.mean_and_spread([0.5, 1.0])
    assert s == {"mean": 0.75, "std": 0.25, "min": 0.5, "max": 1.0, "runs": 2}
    assert metrics.mean_and_spread([0.4])["std"] == 0.0


def test_gold_data_is_consistent_with_the_demo_vault(demo):
    assert runners.check_gold_sentences_exist() == []
    paths = {r["path"] for r in demo.execute("SELECT path FROM notes")}
    for query in runners.load("retrieval")["queries"]:
        assert set(query["relevant"]) <= paths, query["id"]
    for question in runners.load("qa")["questions"]:
        if not question.get("unanswerable"):
            assert question["source"] in paths, question["id"]
            body = demo.execute(
                "SELECT body FROM notes WHERE path = ?", (question["source"],)
            ).fetchone()[0]
            # The expected facts really are in the note the gold data points to.
            assert metrics.facts_present(body, question["facts"]), question["id"]
    splits = [q["split"] for q in runners.load("qa")["questions"]]
    assert splits.count("dev") == splits.count("heldout")


def test_checkbox_parser_matches_gold_exactly():
    result = runners.eval_checkbox_parsing()
    assert result["f1"] == 1.0, result


def test_threshold_is_chosen_on_dev_only():
    rows = [
        {"split": "dev", "unanswerable": False, "similarity": 0.8},
        {"split": "dev", "unanswerable": True, "similarity": 0.3},
        # Held-out rows that would favour a different threshold must not influence it.
        {"split": "heldout", "unanswerable": False, "similarity": 0.2},
        {"split": "heldout", "unanswerable": True, "similarity": 0.9},
    ]
    result = runners.calibrate_threshold(rows)
    assert 0.3 < result["threshold"] <= 0.8
    assert result["dev_balanced_accuracy"] == 1.0
    assert result["heldout_balanced_accuracy"] == 0.0


def test_qa_eval_runs_end_to_end_with_fake_provider(demo, provider):
    result = runners.eval_qa(demo, provider, top_k=5, abstain_threshold=0.2)
    summary = result["summary"]["all"]
    assert summary["answerable_n"] == 18 and summary["unanswerable_n"] == 8
    assert 0.0 <= summary["correct"] <= 1.0
