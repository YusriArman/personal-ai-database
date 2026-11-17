"""Split a note body into chunks for retrieval.

Strategy: split on markdown headings first (a section is usually one idea), then
pack paragraphs of an over-long section into pieces of at most `max_chars`.
Each chunk remembers its heading trail so a search hit can show where it came from.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.ingest.parser import FENCE_RE, HEADING_RE


@dataclass(frozen=True)
class Chunk:
    position: int  # 0-based order within the note
    heading: str  # e.g. "Project Atlas > Risks" ("" for text before any heading)
    text: str


def _sections(body: str) -> list[tuple[str, str]]:
    """Return (heading trail, section text) pairs in document order."""
    sections: list[tuple[str, str]] = []
    trail: list[tuple[int, str]] = []
    current: list[str] = []
    in_fence = False

    def flush() -> None:
        text = "\n".join(current).strip()
        if text:
            sections.append((" > ".join(name for _, name in trail), text))
        current.clear()

    for line in body.split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
        heading = None if in_fence else HEADING_RE.match(line)
        if heading:
            flush()
            level = len(heading.group(1))
            while trail and trail[-1][0] >= level:
                trail.pop()
            trail.append((level, heading.group(2)))
        else:
            current.append(line)
    flush()
    return sections


def _pack(text: str, max_chars: int) -> list[str]:
    """Greedily pack paragraphs into pieces no longer than max_chars."""
    pieces: list[str] = []
    buffer = ""
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        # A single paragraph longer than the limit is hard-split on whitespace.
        while len(paragraph) > max_chars:
            cut = paragraph.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            if buffer:
                pieces.append(buffer)
                buffer = ""
            pieces.append(paragraph[:cut].strip())
            paragraph = paragraph[cut:].strip()
        if not buffer:
            buffer = paragraph
        elif len(buffer) + 2 + len(paragraph) <= max_chars:
            buffer = f"{buffer}\n\n{paragraph}"
        else:
            pieces.append(buffer)
            buffer = paragraph
    if buffer:
        pieces.append(buffer)
    return pieces


def chunk_note(body: str, max_chars: int = 1200) -> list[Chunk]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    chunks: list[Chunk] = []
    for heading, text in _sections(body):
        for piece in _pack(text, max_chars):
            chunks.append(Chunk(position=len(chunks), heading=heading, text=piece))
    return chunks
