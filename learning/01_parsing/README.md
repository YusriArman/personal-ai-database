# Reading a note: checkboxes and wikilinks

A note is just text. Before anything clever can happen, the app has to pull structure out of it: which lines are tasks, which notes it links to. This is done with regular expressions, line by line, with one trap: text inside a fenced code block (three backticks) is an example, not content.

## Exercise

Open `exercise.py` and fill in the functions. The docstrings say exactly what each must do.
Then, from the `backend/` folder:

```
uv run pytest ../learning/01_parsing
```

The tests fail with `NotImplementedError` until you write the code. Work until they pass.

## Hints

Open one at a time, and only when you have been stuck for ten minutes.

<details>
<summary>Hint 1</summary>

Work one line at a time with `text.split("\n")`. A checkbox line has optional spaces, a bullet (`-`, `*` or `+`), a space, `[`, one character, `]`, a space, then the task.

</details>

<details>
<summary>Hint 2</summary>

Keep a boolean `in_code` and flip it every time a line starts with three backticks. Skip lines while it is true.

</details>

<details>
<summary>Hint 3</summary>

For links, the target ends at the first `|`, `#` or `]`. In a regex character class that is `[^\]|#]+`. Use a list plus an `if target not in seen` check to keep order and drop duplicates.

</details>

## Check yourself

- `solution.py` in this folder is one correct answer. Compare it with yours after your tests pass:
  `LEARNING_TARGET=solution uv run pytest ../learning/01_parsing`
- The version the app really uses is in `backend/app/ingest/parser.py (`CHECKBOX_RE`, `WIKILINK_RE`, `parse_note`)`. Read it and find what it handles
  that the exercise left out.
