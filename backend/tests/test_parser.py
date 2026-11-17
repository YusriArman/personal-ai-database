from app.ingest.parser import parse_note, split_frontmatter


def test_frontmatter_is_split_and_body_line_tracked():
    fm, body, start = split_frontmatter("---\ntitle: Hi\ntags: [a, b]\n---\nBody\n")
    assert fm == {"title": "Hi", "tags": ["a", "b"]}
    assert body == "Body\n"
    assert start == 5


def test_broken_frontmatter_keeps_the_whole_note():
    text = "---\ntitle: [unclosed\n---\nBody"
    fm, body, start = split_frontmatter(text)
    assert fm == {} and body == text and start == 1


def test_title_falls_back_to_file_name():
    assert parse_note("just text", "My Note").title == "My Note"
    assert parse_note("---\ntitle: Real\n---\ntext", "file").title == "Real"


def test_wikilinks_with_alias_heading_and_embed():
    note = parse_note("[[A]] [[B|alias]] [[C#Part]] ![[D]] [[a]]", "n")
    assert note.links == ["A", "B", "C", "D"]  # deduplicated case-insensitively


def test_tags_from_frontmatter_and_body():
    note = parse_note("---\ntags: [one]\n---\n# Heading\nText #two and C# and #two\n", "n")
    assert note.tags == ["one", "two"]


def test_string_frontmatter_tags():
    assert parse_note("---\ntags: a, b c\n---\n", "n").tags == ["a", "b", "c"]


def test_checkboxes_with_line_numbers_and_done_state():
    note = parse_note("---\nx: 1\n---\n- [ ] first\ntext\n  * [X] second\n- [] not a box\n", "n")
    assert [(t.text, t.done, t.line) for t in note.tasks] == [
        ("first", False, 4),
        ("second", True, 6),
    ]


def test_code_blocks_are_ignored():
    text = "real #tag\n```\n- [ ] fake task\n#faketag [[FakeLink]]\n```\n`[[inline]]` done"
    note = parse_note(text, "n")
    assert note.tags == ["tag"] and note.links == [] and note.tasks == []
