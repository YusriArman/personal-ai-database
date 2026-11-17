# Semantic search: cosine similarity by brute force

An embedding model turns text into a list of numbers (a vector) so that texts with similar meaning point in similar directions. Cosine similarity measures the angle between two vectors: 1 means same direction, 0 means unrelated. To search, embed the query and rank every chunk by its cosine with the query. With a few thousand chunks, comparing against all of them is instant, which is why this app has no vector database.

## Exercise

Open `exercise.py` and fill in the functions. The docstrings say exactly what each must do.
Then, from the `backend/` folder:

```
uv run pytest ../learning/03_cosine_search
```

The tests fail with `NotImplementedError` until you write the code. Work until they pass.

## Hints

Open one at a time, and only when you have been stuck for ten minutes.

<details>
<summary>Hint 1</summary>

`np.linalg.norm(vectors, axis=1, keepdims=True)` gives one length per row in a shape that divides cleanly.

</details>

<details>
<summary>Hint 2</summary>

Once every row and the query have length 1, cosine similarity is just the dot product: `vectors @ query`.

</details>

<details>
<summary>Hint 3</summary>

`np.argsort(-similarities)` sorts from largest to smallest. Slice with `[:k]`, and convert NumPy numbers with `int()` and `float()`.

</details>

## Check yourself

- `solution.py` in this folder is one correct answer. Compare it with yours after your tests pass:
  `LEARNING_TARGET=solution uv run pytest ../learning/03_cosine_search`
- The version the app really uses is in `backend/app/retrieve/search.py (`semantic_search`) and backend/app/index/indexer.py (`to_blob`)`. Read it and find what it handles
  that the exercise left out.
