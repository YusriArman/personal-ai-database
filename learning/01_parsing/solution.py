"""Reference solution for exercise 1."""
import re

CHECKBOX = re.compile(r"^\s*[-*+]\s+\[( |x|X)\]\s+(.*\S)\s*$")
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


def find_checkboxes(text: str) -> list[tuple[str, bool]]:
    tasks = []
    in_code = False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        match = None if in_code else CHECKBOX.match(line)
        if match:
            tasks.append((match.group(2), match.group(1) != " "))
    return tasks


def find_wikilinks(text: str) -> list[str]:
    seen = []
    for match in WIKILINK.finditer(text):
        target = match.group(1).strip()
        if target not in seen:
            seen.append(target)
    return seen
