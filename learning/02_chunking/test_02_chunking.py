"""Run with:  uv run pytest ../learning/02_chunking   (from backend/)"""
def test_small_text_is_one_chunk(target):
    assert target.pack_paragraphs("one\n\ntwo", 100) == ["one\n\ntwo"]


def test_packing_respects_the_limit_and_order(target):
    text = "aaaa\n\nbbbb\n\ncccc\n\ndddd"
    assert target.pack_paragraphs(text, 10) == ["aaaa\n\nbbbb", "cccc\n\ndddd"]
    assert target.pack_paragraphs(text, 9) == ["aaaa", "bbbb", "cccc", "dddd"]


def test_blank_runs_and_empty_input(target):
    assert target.pack_paragraphs("a\n\n\n\n  \n\nb", 100) == ["a\n\nb"]
    assert target.pack_paragraphs("", 100) == []
