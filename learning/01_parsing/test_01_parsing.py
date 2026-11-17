"""Run with:  uv run pytest ../learning/01_parsing   (from backend/)"""
def test_checkboxes(target):
    text = "- [ ] Buy milk\n* [x] Call Sam\n  + [X] Indented\n- [] broken\n- plain item"
    assert target.find_checkboxes(text) == [
        ("Buy milk", False), ("Call Sam", True), ("Indented", True),
    ]


def test_checkboxes_in_code_blocks_do_not_count(target):
    text = "- [ ] real\n```\n- [ ] example only\n```\n- [ ] also real"
    assert target.find_checkboxes(text) == [("real", False), ("also real", False)]


def test_wikilinks(target):
    text = "See [[A]], [[B|shown text]], [[C#Section]] and [[A]] again."
    assert target.find_wikilinks(text) == ["A", "B", "C"]
    assert target.find_wikilinks("no links [here]") == []
