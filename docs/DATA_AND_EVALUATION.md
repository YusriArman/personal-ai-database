# Data and evaluation

## The demo vault

`demo_vault/` holds 40 short fictional notes about an invented student: 10 projects,
10 meetings, 10 journal entries, 10 reference notes. It contains no real personal data.
It was written with awkward cases on purpose:

- a link to a note that does not exist (`[[Motor Driver Datasheet]]`)
- a checkbox and a tag inside a code block, which must be ignored
- `C#`, which is not a tag
- two near-duplicate topics (sourdough starter care vs. baking schedule)
- tasks phrased without any cue word ("Next week I am sending five more applications.")
- non-tasks that contain a cue word ("It should be 15 ml.")

## Gold data (`evals/data/`)

| File | Contents |
|---|---|
| `retrieval.json` | 36 queries with the notes that answer them. 22 *lexical* (share words with the note), 14 *paraphrase* (deliberately avoid them). |
| `qa.json` | 18 answerable questions with required facts and the source note; 8 unanswerable questions, several near-misses. |
| `tasks.json` | all 20 checkbox tasks; 11 prose sentences that are tasks; 11 *ambiguous* sentences excluded from scoring. |

Each file is split half **dev**, half **held-out**. Dev may be used to tune things (the
abstain threshold is); held-out must not be. A test (`tests/test_metrics.py`) checks that
every gold label still matches the vault, so editing a note cannot silently break the data.

## Two kinds of result, never mixed

**Deterministic** (`make eval` → `evals/reports/deterministic.md`): no model involved,
identical every run. Keyword retrieval, checkbox parsing, and the keyword-rule baseline for
prose tasks.

**Live** (`make eval-live` → `evals/reports/live-<profile>.md`): needs Ollama. Retrieval with
the real embedding model, task proposals and Q&A. Anything a model generates is run 3 times
and reported as mean, standard deviation, minimum and maximum, with the model names and
machine recorded. The two reports are separate files and their numbers are never averaged.

## Metrics

| Metric | Question it answers |
|---|---|
| recall@5 | Of the notes that should be found, what fraction is in the top 5? |
| MRR | How high is the first correct note? (1 = first, 0.5 = second, …) |
| nDCG@10 | Are all the correct notes near the top, weighted by position? |
| precision / recall / F1 | Of the tasks proposed, how many are real? Of the real ones, how many were found? |
| correct | Does the answer contain every required fact? |
| cites right note | Does the answer cite the note that actually holds the fact? |
| wrongly refused / correctly refused | Refusals on answerable / unanswerable questions |
| answers with invalid citation | How often the model cited a source it was never given |

All are a few lines each in `backend/app/evaluate/metrics.py` and are unit-tested against
hand-worked examples.

## Deterministic results at the time of writing

Keyword search (BM25), 36 queries:

| Subset | recall@5 | MRR | nDCG@10 |
|---|---|---|---|
| all | 0.819 | 0.736 | 0.772 |
| lexical (22) | 0.977 | 0.970 | 0.965 |
| paraphrase (14) | 0.571 | 0.370 | 0.467 |

Keyword search is close to perfect when the query shares words with the note and poor when
it does not. That gap is the reason meaning search exists; whether the real embedding model
closes it is what the live report measures.

Tasks: the checkbox parser scores F1 1.000 (20/20, and the code-block trap is ignored).
The keyword-rule baseline for prose tasks scores precision 0.667, recall 0.727, F1 0.696.
The local model has to beat that to justify its cost.

## Live results so far

Only one machine has been measured: the cloud container the project was built in (4 CPU
cores, no GPU, Linux), with `nomic-embed-text` and `llama3.2:3b`, 3 runs. **Nothing has been
measured on the Mac M4 or the Ryzen machine yet**, and `qwen2.5:7b` has not been run at all.
Full report: `evals/reports/live-cloud-cpu.md`.

Retrieval, recall@5 (36 queries):

| Mode | all | lexical (22) | paraphrase (14) |
|---|---|---|---|
| Exact words (BM25) | 0.819 | 0.977 | 0.571 |
| Meaning (`nomic-embed-text`) | 1.000 | 1.000 | 1.000 |
| Both (RRF) | 0.931 | 1.000 | 0.821 |

On this vault, meaning search alone beat the hybrid: fusing in the keyword ranking pulled
three paraphrase queries down. Hybrid is still the default because exact words matter for
names, codes and rare terms that a real vault has and this one mostly does not, but that is
a judgement, not something this data shows. Measure on your own notes before trusting it.

Grounded Q&A (18 answerable, 8 unanswerable), identical in all 3 runs: 18/18 correct, 18/18
citing the right note, 0 wrongly refused, 8/8 correctly refused, 0 invalid citations.
About 62–107 s per pass of 26 questions on this CPU.

Prose task proposals, identical in all 3 runs: 11 true positives, 34 false positives,
0 missed. Precision 0.244, recall 1.000, F1 0.393, about 225 s per pass.

| System | Precision | Recall | F1 |
|---|---|---|---|
| Keyword rule (no model) | 0.667 | 0.727 | 0.696 |
| `llama3.2:3b`, one sentence at a time | 0.244 | 1.000 | 0.393 |

**The model does not beat the baseline on F1.** It finds every real task, including the
three with no cue word that the rule misses, but three of every four things it proposes are
wrong. In a review queue, a missed task is invisible while a wrong proposal costs one click,
so high recall is the more useful failure; that is the argument for keeping it, and it is an
argument, not a win.

## What changed after the first live run, and why it matters

The first live run (`evals/reports/live-cloud-cpu-before-fixes.md`, kept on purpose) found
two faults that no test with the fake model could have found:

| | Before | After |
|---|---|---|
| Task proposals F1 | 0.087 (precision 0.047: nearly every sentence proposed) | 0.393 |
| Q&A correct | 0.667 (6 of 18 answers were only "[1]") | 1.000 |

Fixes: tasks are now judged one sentence at a time instead of as a list per note; the answer
prompt asks for a full sentence, and a reply that is only a citation marker is no longer
shown as an answer; sentence splitting no longer breaks after "Dr." or inside code.

**The "after" numbers are optimistic.** The prompts were changed after looking at failures
on this same data, including held-out questions, and the task labels have no held-out split
at all. So these scores are fitted to the fixture. A perfect Q&A score on 26 easy questions
written by the note author mostly says the fixture is too easy to separate a good system
from an adequate one. The trustworthy numbers will be the ones from questions written
after this point, on notes the prompts were never tuned against.

## What these numbers do not tell you

- **The vault is tiny and tidy.** 40 short notes by one author. A real vault is messier,
  longer and more repetitive; expect lower scores.
- **The same person wrote the notes and the questions.** Real questions will be vaguer.
- **Small counts mean large jumps.** With 14 paraphrase queries, one query moving changes
  recall by 7 points. With 8 unanswerable questions, one changes refusal rate by 12.5.
  Differences of that size between two runs are noise.
- **"Correct" is substring matching.** An answer that mentions the right number in a wrong
  sentence still passes. Read the failure list in the report, not only the averages.
- **Checkbox F1 of 1.0 is a regression test, not an achievement.** Parsing `- [ ]` is easy;
  the score exists to notice if it ever breaks.
- **The fake embedder rows are not a result.** They prove the code path runs.

## Evaluating on your own vault

The honest test is your own notes. Write 15–20 questions you actually want answered, note
which file holds each answer, copy the structure of `evals/data/qa.json` and
`retrieval.json`, and point `LNC_VAULT` at your vault. Keep that file out of git.
