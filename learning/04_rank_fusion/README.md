# Hybrid search: reciprocal rank fusion

Keyword search and semantic search each miss things the other finds. Their scores cannot be added together because they are on unrelated scales (BM25 is unbounded, cosine is between -1 and 1). Reciprocal rank fusion ignores the scores and uses only the positions: each list gives an item 1 / (k + rank), and the totals decide the final order. An item ranked well by both lists beats an item ranked first by only one.

## Exercise

Open `exercise.py` and fill in the functions. The docstrings say exactly what each must do.
Then, from the `backend/` folder:

```
uv run pytest ../learning/04_rank_fusion
```

The tests fail with `NotImplementedError` until you write the code. Work until they pass.

## Hints

Open one at a time, and only when you have been stuck for ten minutes.

<details>
<summary>Hint 1</summary>

Use a dictionary from id to running total, and `enumerate(ranking, start=1)` so ranks start at 1.

</details>

<details>
<summary>Hint 2</summary>

`scores.get(item, 0.0)` reads the current total, or 0 the first time you meet an id.

</details>

<details>
<summary>Hint 3</summary>

Sort with a key that returns a tuple: `(-score, id)` puts the highest score first and breaks ties alphabetically.

</details>

## Check yourself

- `solution.py` in this folder is one correct answer. Compare it with yours after your tests pass:
  `LEARNING_TARGET=solution uv run pytest ../learning/04_rank_fusion`
- The version the app really uses is in `backend/app/retrieve/search.py (`reciprocal_rank_fusion`, `hybrid_search`)`. Read it and find what it handles
  that the exercise left out.
