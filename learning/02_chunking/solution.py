"""Reference solution for exercise 2."""
import re


def pack_paragraphs(text: str, max_chars: int) -> list[str]:
    chunks = []
    current = ""
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if not current:
            current = paragraph
        elif len(current) + 2 + len(paragraph) <= max_chars:
            current = current + "\n\n" + paragraph
        else:
            chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks
