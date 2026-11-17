# Chunking: cutting a note into retrievable pieces

Search works on chunks, not whole notes: a long note about five things would otherwise match everything weakly. A chunk should be small enough to be about one thing and large enough to make sense alone. The simplest good rule is to pack whole paragraphs together until a size limit is reached.

## Exercise

Open `exercise.py` and fill in the functions. The docstrings say exactly what each must do.
Then, from the `backend/` folder:

```
uv run pytest ../learning/02_chunking
```

The tests fail with `NotImplementedError` until you write the code. Work until they pass.

## Hints

Open one at a time, and only when you have been stuck for ten minutes.

<details>
<summary>Hint 1</summary>

Split with `re.split(r"\n\s*\n", text)` so a line containing only spaces also counts as a blank line.

</details>

<details>
<summary>Hint 2</summary>

Keep one string `current`. For each paragraph decide: start a chunk, extend it, or close it and start a new one.

</details>

<details>
<summary>Hint 3</summary>

The joined length is `len(current) + 2 + len(paragraph)` because the separator is two characters. Do not forget to append the last `current` after the loop.

</details>

## Check yourself

- `solution.py` in this folder is one correct answer. Compare it with yours after your tests pass:
  `LEARNING_TARGET=solution uv run pytest ../learning/02_chunking`
- The version the app really uses is in `backend/app/ingest/chunker.py (`_pack`, `chunk_note`)`. Read it and find what it handles
  that the exercise left out.
