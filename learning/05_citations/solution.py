"""Reference solution for exercise 5."""
import re


def check_citations(answer: str, source_count: int) -> tuple[list[int], list[int]]:
    valid: list[int] = []
    invalid: list[int] = []
    for match in re.finditer(r"\[(\d+)\]", answer):
        number = int(match.group(1))
        bucket = valid if 1 <= number <= source_count else invalid
        if number not in bucket:
            bucket.append(number)
    return valid, invalid


def strip_invalid(answer: str, invalid: list[int]) -> str:
    for number in invalid:
        answer = answer.replace(f"[{number}]", "")
    return re.sub(r" {2,}", " ", answer).strip()
