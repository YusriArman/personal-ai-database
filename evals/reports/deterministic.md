# Deterministic evaluation report

No model is involved in anything on this page, so re-running gives identical numbers.

> **Read this first.** The demo vault has 40 short fictional notes written by the same person who wrote the questions. Scores on it show that the pipeline works and let two configurations be compared; they do **not** predict performance on a real vault.

## Retrieval — keyword search (SQLite FTS5, BM25)

This is the real keyword search the app uses.

| Mode | Subset | n | recall@5 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| keyword | all | 36 | 0.819 | 0.736 | 0.772 |
| keyword | split=dev | 18 | 0.833 | 0.705 | 0.745 |
| keyword | split=heldout | 18 | 0.806 | 0.768 | 0.799 |
| keyword | kind=lexical | 22 | 0.977 | 0.970 | 0.965 |
| keyword | kind=paraphrase | 14 | 0.571 | 0.370 | 0.467 |

Queries where **keyword** missed a relevant note in the top 5:

- `r06` (paraphrase) "what heat setting do I use to cook bread" — wanted ['reference/Sourdough Baking Schedule.md'], top result was ['reference/Interview Prep Notes.md']
- `r09` (paraphrase) "who looks after the society's money" — wanted ['meetings/Club Meeting 2025-02-03.md'], top result was ['reference/Interview Prep Notes.md']
- `r15` (paraphrase) "which subject should I enrol in after this term" — wanted ['meetings/Advisor Meeting 2025-01-20.md'], top result was ['journal/2025-02-22.md']
- `r16` (lexical) "library management system tables" — wanted ['meetings/Group Project Sync 2025-02-10.md', 'meetings/Group Project Sync 2025-02-24.md'], top result was ['meetings/Group Project Sync 2025-02-10.md']
- `r28` (paraphrase) "mobile application to record what I pay for things" — wanted ['projects/Budget Tracker App.md'], top result was ['journal/2025-03-08.md']
- `r34` (paraphrase) "what I read on my day off" — wanted ['journal/2025-03-22.md'], top result was ['projects/Reading Tracker Script.md']
- `r35` (paraphrase) "electrical interference made measurements jumpy" — wanted ['projects/Sensor Calibration Log.md', 'journal/2025-02-15.md'], top result was ['projects/Study Timer CLI.md']

## Retrieval — pipeline check with the fake embedder

These rows use `FakeProvider`, a hashed bag-of-words stand-in. It is **not** an embedding model and understands no meaning, so it is expected to fail paraphrase queries. The rows exist to prove the semantic and hybrid code paths run end to end. Real-model numbers are in the live report.

| Mode | Subset | n | recall@5 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| semantic | all | 36 | 0.708 | 0.599 | 0.620 |
| semantic | split=dev | 18 | 0.611 | 0.546 | 0.559 |
| semantic | split=heldout | 18 | 0.806 | 0.653 | 0.681 |
| semantic | kind=lexical | 22 | 0.955 | 0.886 | 0.886 |
| semantic | kind=paraphrase | 14 | 0.321 | 0.148 | 0.202 |
| hybrid | all | 36 | 0.806 | 0.717 | 0.751 |
| hybrid | split=dev | 18 | 0.722 | 0.646 | 0.686 |
| hybrid | split=heldout | 18 | 0.889 | 0.788 | 0.817 |
| hybrid | kind=lexical | 22 | 1.000 | 0.977 | 0.969 |
| hybrid | kind=paraphrase | 14 | 0.500 | 0.308 | 0.409 |

## Task extraction — checkboxes

| System | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Checkbox parser | 20 | 0 | 0 | 1.000 | 1.000 | 1.000 |

False positives:

- none

False negatives:

- none

## Task extraction — keyword-rule baseline for implicit tasks

A rule with no model: a sentence is a task if it contains *need to / must / should / have to / remember to*. This is the bar the local model has to clear. 0 predictions fell on sentences labelled ambiguous and were not scored.

| System | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Keyword rule | 8 | 4 | 3 | 0.667 | 0.727 | 0.696 |

False positives:

- ['projects/Recipe Scaler.md', 'it should be 15 ml.']
- ['reference/Git Cheatsheet.md', 'a commit message must say why, not what.']
- ['reference/Git Cheatsheet.md', 'you should commit small changes often.']
- ['reference/Markdown and Obsidian Tips.md', 'in a code block it is only an example and should not count:']

False negatives:

- ['journal/2025-01-06.md', 'tomorrow i will cook properly.']
- ['journal/2025-03-08.md', 'next week i am sending five more applications.']
- ['projects/Reading Tracker Script.md', 'fixing it is the next job once exams are over.']
