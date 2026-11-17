import pytest

from app.ingest.chunker import chunk_note


def test_sections_carry_their_heading_trail():
    body = "intro\n\n# A\ntext a\n\n## B\ntext b\n\n# C\ntext c"
    chunks = chunk_note(body)
    assert [(c.heading, c.text) for c in chunks] == [
        ("", "intro"),
        ("A", "text a"),
        ("A > B", "text b"),
        ("C", "text c"),
    ]
    assert [c.position for c in chunks] == [0, 1, 2, 3]


def test_long_sections_are_split_on_paragraphs_within_the_limit():
    body = "# S\n" + "\n\n".join(f"paragraph {i} " + "x" * 80 for i in range(10))
    chunks = chunk_note(body, max_chars=250)
    assert len(chunks) > 1
    assert all(len(c.text) <= 250 and c.heading == "S" for c in chunks)
    assert "paragraph 0" in chunks[0].text and "paragraph 9" in chunks[-1].text


def test_a_single_huge_paragraph_is_hard_split_without_losing_words():
    words = [f"w{i}" for i in range(300)]
    chunks = chunk_note(" ".join(words), max_chars=100)
    assert all(len(c.text) <= 100 for c in chunks)
    assert " ".join(c.text for c in chunks).split() == words


def test_heading_inside_code_fence_is_not_a_heading():
    chunks = chunk_note("# Real\n```\n# comment\n```\nafter")
    assert len(chunks) == 1 and chunks[0].heading == "Real"


def test_empty_body_and_bad_limit():
    assert chunk_note("") == []
    with pytest.raises(ValueError):
        chunk_note("x", max_chars=0)
