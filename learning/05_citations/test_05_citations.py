"""Run with:  uv run pytest ../learning/05_citations   (from backend/)"""
def test_check_citations(target):
    assert target.check_citations("A [1]. B [3][1]. C [9] D [0].", 3) == ([1, 3], [9, 0])
    assert target.check_citations("No markers, [not a number].", 3) == ([], [])


def test_strip_invalid(target):
    assert target.strip_invalid("Rain [1] falls [7] mainly.", [7]) == "Rain [1] falls mainly."
    assert target.strip_invalid("Only [12] here", [12]) == "Only here"
    assert target.strip_invalid("Keep [1] and [10].", [1]) == "Keep and [10]."
