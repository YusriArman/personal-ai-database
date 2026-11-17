# Experiment: classifying notes by type

A supervised-learning exercise that sits beside the app. Nothing in the app uses it.

**Question.** Given only the text of a note, can a model tell whether it is a project,
meeting, journal or reference note?

**Setup.** 40 demo notes, 10 per class. The label comes from each note's `type:` frontmatter.
Features are TF-IDF over the note body only: frontmatter and folder name are excluded,
because the label is written there and using it would be label leakage. The model is
logistic regression. Scores come from 5-fold stratified cross-validation, so every note is
predicted by a model that never saw it.

```
make experiment        # writes RESULTS.md and results.json here
```

## Result

| System | Accuracy | Macro F1 |
|---|---|---|
| Majority class | 0.250 | 0.100 |
| Hand-written keyword rule | 0.875 | 0.875 |
| TF-IDF + logistic regression | 0.625 | 0.618 |
| Same, with dates removed from the text | 0.600 | 0.593 |

Full output, confusion matrix and misclassified notes: [RESULTS.md](RESULTS.md).

## What this shows

**The learned model loses to a five-minute rule.** It beats guessing (0.25) comfortably but
a few hand-written `if` statements score 0.875. With 32 training notes, the model sees about
8 examples per class, which is not enough to learn that "has an Attendees line" means
meeting; a person can simply write that down. More data is what makes learning win, not a
cleverer model.

**Where it fails is informative.** Meetings (9/10) and journals (8/10) are recognised:
meetings share fixed words (discussed, decisions, actions), journals share first-person past
tense (felt, went, today). Projects and references are confused with each other (only 3/10
projects correct) because both are topical prose about technical things; their vocabulary
is about the *subject*, not the *kind* of note.

**The strongest "meeting" feature is `2025`.** Meeting titles contain a date. That is a
property of how this vault was written, not of meetings. Removing dates costs one note
(0.625 → 0.600), so the model was leaning on it only slightly, but this is exactly the kind
of shortcut to look for before trusting a classifier.

**The estimate itself is shaky.** Each fold tests on 8 notes, so one note is 12.5 points of
fold accuracy. All five folds happening to score 0.625 is a coincidence of this seed, not a
sign of stability. Do not read anything into differences of a few points here.

**The rule is overfitted too.** It was written by someone who had read all 40 notes, and it
was never tested on notes it had not seen. Its 0.875 is an optimistic number.

## Things to try

1. Change `C`, `ngram_range` or `min_df` in `train.py` and watch how much the score moves
   from noise alone (change `SEED` too).
2. Add character n-grams (`analyzer="char_wb"`) and see whether style, not vocabulary, helps.
3. Label 40 of your own notes and run it on them. Does the keyword rule still win?
