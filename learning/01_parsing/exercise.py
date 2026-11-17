"""Exercise 1 — pull tasks and links out of note text."""


def find_checkboxes(text: str) -> list[tuple[str, bool]]:
    """Return (task text, done) for every markdown checkbox line.

    "- [ ] Buy milk"  -> ("Buy milk", False)
    "- [x] Call Sam"  -> ("Call Sam", True)      (also "[X]", and "*" or "+" bullets)
    Lines inside a ``` fenced code block are ignored.
    """
    raise NotImplementedError("Write find_checkboxes")


def find_wikilinks(text: str) -> list[str]:
    """Return link targets in first-seen order, without duplicates.

    "[[A]]" -> "A";  "[[B|shown text]]" -> "B";  "[[C#Section]]" -> "C"
    """
    raise NotImplementedError("Write find_wikilinks")
