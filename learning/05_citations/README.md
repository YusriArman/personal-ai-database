# Grounding: never trust a citation you have not checked

A language model asked to cite its sources will usually do so, and will sometimes cite a source that was never given to it. The fix is not a better prompt; it is code. After the model answers, the program reads every [n] marker and checks that source n really exists. Anything else is removed, and an answer left with no valid citation is flagged as ungrounded.

## Exercise

Open `exercise.py` and fill in the functions. The docstrings say exactly what each must do.
Then, from the `backend/` folder:

```
uv run pytest ../learning/05_citations
```

The tests fail with `NotImplementedError` until you write the code. Work until they pass.

## Hints

Open one at a time, and only when you have been stuck for ten minutes.

<details>
<summary>Hint 1</summary>

`re.finditer(r"\[(\d+)\]", answer)` yields one match per marker; `int(match.group(1))` is the number.

</details>

<details>
<summary>Hint 2</summary>

Pick the list to append to first (`valid` or `invalid`), then append only if the number is not already in it.

</details>

<details>
<summary>Hint 3</summary>

Replace the exact text `f"[{number}]"`, not just the digits, so removing [1] does not damage [10].

</details>

## Check yourself

- `solution.py` in this folder is one correct answer. Compare it with yours after your tests pass:
  `LEARNING_TARGET=solution uv run pytest ../learning/05_citations`
- The version the app really uses is in `backend/app/answer/qa.py (`check_citations`, `answer_question`)`. Read it and find what it handles
  that the exercise left out.
