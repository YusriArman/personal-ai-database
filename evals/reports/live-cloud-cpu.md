# Live-model evaluation report

- Date: 2026-11-17
- Machine: Linux-6.18.44-fc-v553-x86_64-with-glibc2.39 / x86_64 / x86_64
- Profile: `ryzen`
- Embedding model: `nomic-embed-text`
- Chat model: `llama3.2:3b` (temperature 0)
- Runs of each model-generated metric: 3
- Abstain threshold used: 0.35

> **Read this first.** The demo vault has 40 short fictional notes written by the same person who wrote the questions. Scores on it show that the pipeline works and let two configurations be compared; they do **not** predict performance on a real vault.

Model output can change between runs even at temperature 0, so generated metrics are reported as mean, standard deviation, minimum and maximum over the runs.

## Retrieval (one run; fixed for a given embedding model)

| Mode | Subset | n | recall@5 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| keyword | all | 36 | 0.819 | 0.736 | 0.772 |
| keyword | split=dev | 18 | 0.833 | 0.705 | 0.745 |
| keyword | split=heldout | 18 | 0.806 | 0.768 | 0.799 |
| keyword | kind=lexical | 22 | 0.977 | 0.970 | 0.965 |
| keyword | kind=paraphrase | 14 | 0.571 | 0.370 | 0.467 |
| semantic | all | 36 | 1.000 | 0.965 | 0.968 |
| semantic | split=dev | 18 | 1.000 | 0.931 | 0.940 |
| semantic | split=heldout | 18 | 1.000 | 1.000 | 0.996 |
| semantic | kind=lexical | 22 | 1.000 | 1.000 | 0.996 |
| semantic | kind=paraphrase | 14 | 1.000 | 0.911 | 0.922 |
| hybrid | all | 36 | 0.931 | 0.888 | 0.903 |
| hybrid | split=dev | 18 | 0.861 | 0.832 | 0.855 |
| hybrid | split=heldout | 18 | 1.000 | 0.944 | 0.951 |
| hybrid | kind=lexical | 22 | 1.000 | 1.000 | 0.990 |
| hybrid | kind=paraphrase | 14 | 0.821 | 0.713 | 0.767 |

Queries where **semantic** missed a relevant note in the top 5:

- none

Queries where **hybrid** missed a relevant note in the top 5:

- `r09` (paraphrase) "who looks after the society's money" — wanted ['meetings/Club Meeting 2025-02-03.md'], top result was ['meetings/Housemates Meeting 2025-01-05.md']
- `r15` (paraphrase) "which subject should I enrol in after this term" — wanted ['meetings/Advisor Meeting 2025-01-20.md'], top result was ['projects/Study Timer CLI.md']
- `r35` (paraphrase) "electrical interference made measurements jumpy" — wanted ['projects/Sensor Calibration Log.md', 'journal/2025-02-15.md'], top result was ['projects/Study Timer CLI.md']

## Abstain threshold calibration

Chosen on the dev split only: **0.66** (dev balanced accuracy 0.875, held-out 0.875). To use it, set `LNC_ABSTAIN_THRESHOLD` and run this report again; the Q&A numbers below used the threshold listed at the top.

## Implicit task proposals

| Metric | Mean | Std | Min | Max |
|---|---|---|---|---|
| precision | 0.244 | 0.000 | 0.244 | 0.244 |
| recall | 1.000 | 0.000 | 1.000 | 1.000 |
| f1 | 0.393 | 0.000 | 0.393 | 0.393 |

Keyword-rule baseline (deterministic): precision 0.667, recall 0.727, F1 0.696.

Errors from the last run:

False positives:

- ['meetings/Club Meeting 2025-02-17.md', 'practice sessions move to wednesday evenings.']
- ['meetings/Club Meeting 2025-02-17.md', 'the competition venue is confirmed: lab 2 on 22 april.']
- ['meetings/Club Meeting 2025-03-03.md', 'the greenhouse demo is eleven days away and the enclosure is still not printed.']
- ['meetings/Group Project Sync 2025-02-10.md', 'nurul writes the sample data.']
- ['meetings/Housemates Meeting 2025-01-05.md', 'a weekly chores rota: bins on monday, bathroom on thursday, kitchen daily by whoever cooked.']
- ['meetings/Housemates Meeting 2025-01-05.md', 'the wifi bill is split three ways, rm30 each, paid to daniel by the 5th.']
- ['meetings/Internship Call with Kestrel Labs.md', 'phone call with priya, the recruiter, on 5 march.']
- ['meetings/Study Group 2025-02-12.md', 'meet every wednesday at 4 pm until the midterm.']
- ['projects/Internship Application Tracker.md', 'company, role, date applied, contact person, status and next step.']
- ['projects/Line Follower Robot.md', 'club entry for the campus robotics competition on 22 april.']
- ['projects/Portfolio Website.md', 'netlify rebuilds the site whenever i push to the main branch.']
- ['reference/Dynamic Programming Patterns.md', 'coin change: state is the amount.']
- ['reference/Dynamic Programming Patterns.md', 'define the state, write the recurrence, set the base cases, decide the order of filling.']
- ['reference/Dynamic Programming Patterns.md', 'longest increasing subsequence: state is the best length ending at each position.']
- ['reference/Dynamic Programming Patterns.md', 'memoization is top-down: write the recursion, then cache each result.']
- ['reference/Dynamic Programming Patterns.md', 'state is (item index, remaining capacity).']
- ['reference/Dynamic Programming Patterns.md', 'tabulation is bottom-up: fill a table from the smallest subproblem upward.']
- ['reference/Git Cheatsheet.md', '`git stash pop` brings them back.']
- ['reference/Git Cheatsheet.md', 'commands i keep forgetting.']
- ['reference/Interview Prep Notes.md', 'keep the situation short and spend most of the time on the action.']
- ['reference/Interview Prep Notes.md', 'talk through the approach before writing code.']
- ['reference/Linux Commands.md', 'try plain `kill` first.']
- ['reference/Markdown and Obsidian Tips.md', 'a link to a note that does not exist yet is shown faded.']
- ['reference/Markdown and Obsidian Tips.md', 'a task is a list item with a box.']
- ['reference/Markdown and Obsidian Tips.md', 'tags start with a hash, like #obsidian.']
- ['reference/PID Tuning Guide.md', 'raise kp until it wobbles, add kd until the wobble stops, then add a little ki.']
- ['reference/Raspberry Pi Pico Pinout.md', 'use a level shifter for 5 v sensors.']
- ['reference/SQL Joins Reference.md', 'put the filter in the on clause.']
- ['reference/Sourdough Baking Schedule.md', '3 pm: shape, then into the fridge overnight.']
- ['reference/Sourdough Baking Schedule.md', '9 am: mix flour and water, rest 30 minutes.']
- ['reference/Sourdough Baking Schedule.md', '9:30 am: add starter and salt.']
- ['reference/Sourdough Baking Schedule.md', 'wait at least one hour before cutting.']
- ['reference/Sourdough Starter Care.md', 'in the fridge, feed once a week.']
- ['reference/Sourdough Starter Care.md', 'pour it off and feed.']

False negatives:

- none

## Grounded Q&A

### Split: heldout

| Metric | Mean | Std | Min | Max |
|---|---|---|---|---|
| correct | 1.000 | 0.000 | 1.000 | 1.000 |
| cites_right_note | 1.000 | 0.000 | 1.000 | 1.000 |
| source_retrieved | 1.000 | 0.000 | 1.000 | 1.000 |
| wrongly_refused | 0.000 | 0.000 | 0.000 | 0.000 |
| correctly_refused | 1.000 | 0.000 | 1.000 | 1.000 |
| answers_with_invalid_citation | 0.000 | 0.000 | 0.000 | 0.000 |

### Split: dev

| Metric | Mean | Std | Min | Max |
|---|---|---|---|---|
| correct | 1.000 | 0.000 | 1.000 | 1.000 |
| cites_right_note | 1.000 | 0.000 | 1.000 | 1.000 |
| source_retrieved | 1.000 | 0.000 | 1.000 | 1.000 |
| wrongly_refused | 0.000 | 0.000 | 0.000 | 0.000 |
| correctly_refused | 1.000 | 0.000 | 1.000 | 1.000 |
| answers_with_invalid_citation | 0.000 | 0.000 | 0.000 | 0.000 |

### Split: all

| Metric | Mean | Std | Min | Max |
|---|---|---|---|---|
| correct | 1.000 | 0.000 | 1.000 | 1.000 |
| cites_right_note | 1.000 | 0.000 | 1.000 | 1.000 |
| source_retrieved | 1.000 | 0.000 | 1.000 | 1.000 |
| wrongly_refused | 0.000 | 0.000 | 0.000 | 0.000 |
| correctly_refused | 1.000 | 0.000 | 1.000 | 1.000 |
| answers_with_invalid_citation | 0.000 | 0.000 | 0.000 | 0.000 |

Failures from the last run:

- none

## Timing

- Q&A set: 78.202 s per pass (26 questions)
- Task proposals: 227.099 s per pass (40 notes)
