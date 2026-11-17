# Evaluation: measuring retrieval and extraction honestly

Without numbers, 'it seems to work' is all you can say. Recall@k asks: of the notes that should have been found, how many were in the top k? Reciprocal rank asks how far down the first good result was. Precision and recall pull against each other in extraction: proposing everything gets perfect recall and terrible precision. F1 is high only when both are. A number is only meaningful next to a baseline and a description of the data it was measured on.

## Exercise

Open `exercise.py` and fill in the functions. The docstrings say exactly what each must do.
Then, from the `backend/` folder:

```
uv run pytest ../learning/06_metrics
```

The tests fail with `NotImplementedError` until you write the code. Work until they pass.

## Hints

Open one at a time, and only when you have been stuck for ten minutes.

<details>
<summary>Hint 1</summary>

Sets do the counting for you: `set(ranked[:k]) & relevant` is the relevant items found in the top k.

</details>

<details>
<summary>Hint 2</summary>

For reciprocal rank, loop with `enumerate(ranked, start=1)` and return as soon as you meet a relevant item.

</details>

<details>
<summary>Hint 3</summary>

Write each division as `x / y if y else 0.0`. For F1 the thing that can be zero is `precision + recall`.

</details>

## Check yourself

- `solution.py` in this folder is one correct answer. Compare it with yours after your tests pass:
  `LEARNING_TARGET=solution uv run pytest ../learning/06_metrics`
- The version the app really uses is in `backend/app/evaluate/metrics.py; gold data in evals/data/; reports in evals/reports/`. Read it and find what it handles
  that the exercise left out.
