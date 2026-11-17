"""Turn the text of one Obsidian markdown note into structured data.

Pure functions only: no file or database access, so every piece is easy to test.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
# [[Target]], [[Target|alias]], [[Target#Heading]], and embeds ![[Target]]
WIKILINK_RE = re.compile(r"!?\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
# A tag is # followed by a letter, not preceded by a word character (so "C#" or a URL
# fragment does not count) and never a markdown heading ("# Title" has a space).
TAG_RE = re.compile(r"(?<![\w/#])#([A-Za-z][\w/-]*)")
CHECKBOX_RE = re.compile(r"^\s*[-*+]\s+\[( |x|X)\]\s+(.*\S)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


@dataclass(frozen=True)
class CheckboxTask:
    text: str
    done: bool
    line: int  # 1-based line number in the original file


@dataclass
class ParsedNote:
    title: str
    body: str  # note text without frontmatter
    frontmatter: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)  # link targets, in first-seen order
    tasks: list[CheckboxTask] = field(default_factory=list)
    body_start_line: int = 1  # line of the file where body begins


def split_frontmatter(text: str) -> tuple[dict, str, int]:
    """Return (frontmatter dict, body, 1-based line where the body starts)."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text, 1
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        # Broken YAML should not lose the note: treat the whole file as body.
        return {}, text, 1
    if not isinstance(data, dict):
        return {}, text, 1
    body = text[match.end() :]
    return data, body, text[: match.end()].count("\n") + 1


def _lines_outside_code(body: str) -> list[tuple[int, str]]:
    """(index, line) for lines that are not inside a fenced code block."""
    kept: list[tuple[int, str]] = []
    in_fence = False
    for i, line in enumerate(body.split("\n")):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            kept.append((i, line))
    return kept


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _frontmatter_tags(frontmatter: dict) -> list[str]:
    raw = frontmatter.get("tags", [])
    if isinstance(raw, str):
        raw = re.split(r"[,\s]+", raw)
    if not isinstance(raw, list):
        return []
    return [str(t).lstrip("#") for t in raw if str(t).strip()]


def parse_note(text: str, fallback_title: str) -> ParsedNote:
    """Parse a note. `fallback_title` is normally the file name without `.md`."""
    frontmatter, body, body_start = split_frontmatter(text)
    lines = _lines_outside_code(body)

    title = fallback_title
    if isinstance(frontmatter.get("title"), str) and frontmatter["title"].strip():
        title = frontmatter["title"].strip()

    tags = _frontmatter_tags(frontmatter)
    links: list[str] = []
    tasks: list[CheckboxTask] = []
    for index, line in lines:
        # Inline code spans can contain things that look like tags or links.
        visible = re.sub(r"`[^`]*`", "", line)
        links.extend(m.group(1).strip() for m in WIKILINK_RE.finditer(visible))
        if not HEADING_RE.match(visible):
            without_links = WIKILINK_RE.sub("", visible)
            tags.extend(TAG_RE.findall(without_links))
        box = CHECKBOX_RE.match(line)
        if box:
            tasks.append(
                CheckboxTask(
                    text=box.group(2), done=box.group(1) != " ", line=body_start + index
                )
            )

    return ParsedNote(
        title=title,
        body=body,
        frontmatter=frontmatter,
        tags=_dedupe(tags),
        links=_dedupe(links),
        tasks=tasks,
        body_start_line=body_start,
    )
