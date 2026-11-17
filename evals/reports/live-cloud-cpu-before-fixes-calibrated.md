# Live-model evaluation report

- Date: 2026-11-17
- Machine: Linux-6.18.44-fc-v553-x86_64-with-glibc2.39 / x86_64 / x86_64
- Profile: `ryzen`
- Embedding model: `nomic-embed-text`
- Chat model: `llama3.2:3b` (temperature 0)
- Runs of each model-generated metric: 3
- Abstain threshold used: 0.66

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
| precision | 0.046 | 0.000 | 0.046 | 0.046 |
| recall | 0.636 | 0.000 | 0.636 | 0.636 |
| f1 | 0.085 | 0.000 | 0.085 | 0.085 |

Keyword-rule baseline (deterministic): precision 0.667, recall 0.727, F1 0.696.

Errors from the last run:

False positives:

- ['journal/2025-01-06.md', 'first day back after the break and i already feel tired.']
- ['journal/2025-01-06.md', 'the timetable has three 8 am classes, which is cruel.']
- ['journal/2025-01-06.md', 'we will see how long that lasts.']
- ['journal/2025-01-19.md', 'my knees hurt on the way down and i was slow on the rocky part.']
- ['journal/2025-02-01.md', 'that helped more than the studying.']
- ['journal/2025-02-09.md', 'hana said the rice needed more coconut milk and she is probably right.']
- ['journal/2025-02-09.md', 'it felt good to make something with my hands that was not a circuit or a program.']
- ['journal/2025-02-15.md', 'i am also very tired and i am going to bed at nine.']
- ['journal/2025-02-22.md', 'long call with mum tonight.']
- ['journal/2025-03-01.md', 'i was sure we would miss it and let the whole team down.']
- ['journal/2025-03-08.md', 'one rejection out of twelve applications is not a verdict on me.']
- ['journal/2025-03-15.md', 'demo day was yesterday and it went well.']
- ['journal/2025-03-22.md', 'a proper rest day.']
- ['meetings/Advisor Meeting 2025-01-20.md', 'final-year project ideas.']
- ['meetings/Advisor Meeting 2025-01-20.md', 'lim for the start-of-semester check.']
- ['meetings/Advisor Meeting 2025-01-20.md', 'my grades from last semester and the plan for the next two.']
- ['meetings/Advisor Meeting 2025-01-20.md', 'she liked anything involving cheap sensors.']
- ['meetings/Advisor Meeting 2025-03-10.md', 'second meeting with dr.']
- ['meetings/Advisor Meeting 2025-03-10.md', 'she has two spare particulate sensors i can borrow.']
- ['meetings/Club Meeting 2025-02-03.md', 'aisha manages the club budget this semester and approves purchases.']
- ['meetings/Club Meeting 2025-02-17.md', 'practice sessions move to wednesday evenings.']
- ['meetings/Club Meeting 2025-03-03.md', 'aisha approved rm40 for a second roll of filament.']
- ['meetings/Club Meeting 2025-03-03.md', 'jun proposed a club t-shirt.']
- ['meetings/Club Meeting 2025-03-03.md', 'nobody objected, nobody volunteered.']
- ['meetings/Club Meeting 2025-03-03.md', 'the greenhouse demo is eleven days away and the enclosure is still not printed.']
- ['meetings/Group Project Sync 2025-02-10.md', 'databases course project: a library management system.']
- ['meetings/Group Project Sync 2025-02-10.md', 'nurul writes the sample data.']
- ['meetings/Group Project Sync 2025-02-10.md', 'we chose a separate copies table.']
- ['meetings/Group Project Sync 2025-02-10.md', 'wei draws the er diagram.']
- ['meetings/Group Project Sync 2025-02-10.md', 'whether a book with several copies is one row or many.']
- ['meetings/Group Project Sync 2025-02-24.md', 'fines are rm0.50 per day, capped at rm20 per book.']
- ['meetings/Group Project Sync 2025-02-24.md', 'the overdue loans query returned duplicates because of a missing join condition.']
- ['meetings/Group Project Sync 2025-02-24.md', 'the report is due on 21 march and nurul will assemble it.']
- ['meetings/Housemates Meeting 2025-01-05.md', 'a weekly chores rota: bins on monday, bathroom on thursday, kitchen daily by whoever cooked.']
- ['meetings/Housemates Meeting 2025-01-05.md', 'the internet bill went up.']
- ['meetings/Housemates Meeting 2025-01-05.md', 'the kitchen was a mess over the break.']
- ['meetings/Housemates Meeting 2025-01-05.md', 'the wifi bill is split three ways, rm30 each, paid to daniel by the 5th.']
- ['meetings/Internship Call with Kestrel Labs.md', 'phone call with priya, the recruiter, on 5 march.']
- ['meetings/Internship Call with Kestrel Labs.md', 'there is a take-home test, about three hours, sent by email next week.']
- ['meetings/Study Group 2025-02-12.md', 'algorithms study group in the library.']
- ['meetings/Study Group 2025-02-12.md', 'attendees: jun, wei and me.']
- ['meetings/Study Group 2025-02-12.md', 'coin change took us forty minutes.']
- ['meetings/Study Group 2025-02-12.md', 'jun explained why greedy fails on coin change with unusual denominations.']
- ['meetings/Study Group 2025-02-12.md', 'meet every wednesday at 4 pm until the midterm.']
- ['meetings/Study Group 2025-02-12.md', 'notes on the patterns are in [[dynamic programming patterns]].']
- ['meetings/Study Group 2025-02-12.md', 'worked through four dynamic programming problems.']
- ['projects/Campus Map Dataset.md', 'a csv of gps coordinates for campus buildings, collected by walking around with my phone.']
- ['projects/Greenhouse Monitor.md', 'a small box that watches the herb trays in the club greenhouse and warns us before the soil dries out.']
- ['projects/Greenhouse Monitor.md', 'it runs on a raspberry pi pico w and posts readings every ten minutes.']
- ['projects/Greenhouse Monitor.md', 'readings were noisy until i redid the calibration, see [[sensor calibration log]].']
- ['projects/Greenhouse Monitor.md', 'the capacitive soil probes were the expensive part at rm22 each.']
- ['projects/Greenhouse Monitor.md', 'the demo is on 14 march in front of the faculty panel.']
- ['projects/Greenhouse Monitor.md', 'wiring follows [[raspberry pi pico pinout]].']
- ['projects/Internship Application Tracker.md', 'a spreadsheet of every internship i have applied to.']
- ['projects/Internship Application Tracker.md', 'applications sent on a monday morning got replies faster, but three replies is too few to conclude anything.']
- ['projects/Internship Application Tracker.md', 'colour coding: yellow means waiting, green means interview, grey means rejected.']
- ['projects/Internship Application Tracker.md', 'company, role, date applied, contact person, status and next step.']
- ['projects/Internship Application Tracker.md', 'preparation material lives in [[interview prep notes]] and the kestrel call is written up in [[internship call with kestrel labs]].']
- ['projects/Internship Application Tracker.md', 'so far 12 applications, 3 replies and 1 interview scheduled.']
- ['projects/Line Follower Robot.md', 'background on tuning is in [[pid tuning guide]].']
- ['projects/Line Follower Robot.md', 'club entry for the campus robotics competition on 22 april.']
- ['projects/Line Follower Robot.md', 'i could not find its limits in [[motor driver datasheet]] so we are adding a heat sink anyway.']
- ['projects/Line Follower Robot.md', 'the motor driver overheats after about six minutes.']
- ['projects/Line Follower Robot.md', 'the robot steers with a pid loop.']
- ['projects/Line Follower Robot.md', 'the values that finally stopped the wobble on the practice track were kp 0.42, ki 0.01 and kd 0.18.']
- ['projects/Line Follower Robot.md', 'two dc motors, five infrared reflectance sensors across the front, and an arduino nano.']
- ['projects/Reading Tracker Script.md', 'that bug is still there.']
- ['projects/Recipe Scaler.md', 'a one-page web tool: paste a recipe, choose how many servings, and it rescales every quantity.']
- ['projects/Recipe Scaler.md', 'it should be 15 ml.']
- ['projects/Recipe Scaler.md', 'plain javascript, no framework.']
- ['projects/Recipe Scaler.md', 'rounding to sensible kitchen amounts, for example 1/3 cup instead of 0.31 cup.']
- ['projects/Recipe Scaler.md', 'small recipes come out fine but a scaled-up curry was far too salty.']
- ['projects/Recipe Scaler.md', 'tablespoons are converted to millilitres using 20 ml, which is the australian tablespoon.']
- ['projects/Sensor Calibration Log.md', 'anything under 35 percent means the basil needs watering.']
- ['projects/Sensor Calibration Log.md', 'keeping them 5 cm apart fixed it.']
- ['projects/Sensor Calibration Log.md', 'raw numbers for the [[greenhouse monitor]] probes.']
- ['projects/Sensor Calibration Log.md', 'readings drift when the probe cable runs next to the pump wire.']
- ['projects/Sensor Calibration Log.md', 'the capacitive probe reads about 520 in dry air and about 260 in a glass of water.']
- ['projects/Sensor Calibration Log.md', 'the dht22 reads 0.8 °c higher than the lab thermometer, so the firmware subtracts 0.8 before logging.']
- ['projects/Study Timer CLI.md', 'a terminal pomodoro timer written in rust as a way to learn the language.']
- ['projects/Study Timer CLI.md', 'it runs 25 minutes of work followed by a 5 minute break, with a longer 20 minute break after four rounds.']
- ['projects/Study Timer CLI.md', 'ownership made sense once i stopped fighting the borrow checker and passed references instead of cloning everything.']
- ['projects/Study Timer CLI.md', 'the clap crate handles the command line arguments.']
- ['reference/Dynamic Programming Patterns.md', 'define the state, write the recurrence, set the base cases, decide the order of filling.']
- ['reference/Dynamic Programming Patterns.md', 'greedy fails when denominations are irregular.']
- ['reference/Git Cheatsheet.md', '`git rebase main` replays the current branch on top of main.']
- ['reference/Git Cheatsheet.md', '`git reset --soft head~1` undoes the last commit and keeps the changes staged.']
- ['reference/Git Cheatsheet.md', '`git restore <file>` discards changes in the working tree.']
- ['reference/Git Cheatsheet.md', '`git revert <commit>` creates a new commit that reverses an old one.']
- ['reference/Git Cheatsheet.md', '`git stash pop` brings them back.']
- ['reference/Git Cheatsheet.md', '`git stash` saves uncommitted changes and cleans the working tree.']
- ['reference/Git Cheatsheet.md', 'a commit message must say why, not what.']
- ['reference/Git Cheatsheet.md', 'commands i keep forgetting.']
- ['reference/Git Cheatsheet.md', 'never rebase commits that have already been pushed and shared.']
- ['reference/Git Cheatsheet.md', 'you should commit small changes often.']
- ['reference/Interview Prep Notes.md', 'describe a time you disagreed with a teammate.']
- ['reference/Interview Prep Notes.md', 'keep the situation short and spend most of the time on the action.']
- ['reference/Interview Prep Notes.md', 'state the time and space complexity without being asked.']
- ['reference/Interview Prep Notes.md', 'talk through the approach before writing code.']
- ['reference/Interview Prep Notes.md', 'tell me about a project you are proud of.']
- ['reference/Interview Prep Notes.md', 'test with an empty input.']
- ['reference/Interview Prep Notes.md', 'use the star method: situation, task, action, result.']
- ['reference/Interview Prep Notes.md', 'what does a typical week look like for an intern, and who would i learn from?']
- ['reference/Interview Prep Notes.md', 'what would you do differently?']
- ['reference/Linux Commands.md', '-name "*.log" -mtime +7` lists log files older than a week.']
- ['reference/Linux Commands.md', '`chmod +x script.sh` makes a script executable.']
- ['reference/Linux Commands.md', '`chown user:group file` changes the owner.']
- ['reference/Linux Commands.md', '`df -h` shows free space per disk.']
- ['reference/Linux Commands.md', '`du -sh *` shows the size of each item in the current folder.']
- ['reference/Linux Commands.md', '`grep -rn "text" .` searches file contents recursively and shows line numbers.']
- ['reference/Linux Commands.md', '`kill -9 <pid>` forces it to stop.']
- ['reference/Linux Commands.md', '`ps aux | grep name` finds a running process.']
- ['reference/Linux Commands.md', 'try plain `kill` first.']
- ['reference/PID Tuning Guide.md', 'raise kp until it wobbles, add kd until the wobble stops, then add a little ki.']
- ['reference/PID Tuning Guide.md', 'raise kp until the output oscillates steadily; that gain is ku and the period is tu.']
- ['reference/PID Tuning Guide.md', 'set ki and kd to zero.']
- ['reference/PID Tuning Guide.md', 'then use kp = 0.6 ku, ki = 1.2 ku / tu and kd = 0.075 ku tu.']
- ['reference/Raspberry Pi Pico Pinout.md', '3v3 out supplies up to about 300 ma to sensors.']
- ['reference/Raspberry Pi Pico Pinout.md', 'the default i2c bus uses gp4 for sda and gp5 for scl.']
- ['reference/Raspberry Pi Pico Pinout.md', 'the gpio pins are not 5 v tolerant.']
- ['reference/Raspberry Pi Pico Pinout.md', 'the pins i actually use.']
- ['reference/Raspberry Pi Pico Pinout.md', 'there are three adc inputs: gp26, gp27 and gp28.']
- ['reference/Raspberry Pi Pico Pinout.md', 'they read 0 to 3.3 v with 12-bit resolution.']
- ['reference/Raspberry Pi Pico Pinout.md', 'use a level shifter for 5 v sensors.']
- ['reference/Raspberry Pi Pico Pinout.md', 'vsys accepts 1.8 to 5.5 v.']
- ['reference/SQL Joins Reference.md', 'filtering the right table in where turns a left join into an inner join.']
- ['reference/SQL Joins Reference.md', 'forgetting a join condition multiplies rows and produces duplicates.']
- ['reference/SQL Joins Reference.md', 'put the filter in the on clause.']
- ['reference/SQL Joins Reference.md', 'row_number, rank and lag compute values across related rows without collapsing them the way group by does.']
- ['reference/Sourdough Baking Schedule.md', '3 pm: shape, then into the fridge overnight.']
- ['reference/Sourdough Baking Schedule.md', '9 am: mix flour and water, rest 30 minutes.']
- ['reference/Sourdough Baking Schedule.md', '9:30 am: add starter and salt.']
- ['reference/Sourdough Baking Schedule.md', 'bake 20 minutes with the lid on, then 25 minutes with the lid off.']
- ['reference/Sourdough Baking Schedule.md', 'bulk fermentation takes about 5 hours at 26 °c, with a fold every 45 minutes for the first two hours.']
- ['reference/Sourdough Baking Schedule.md', 'heat the oven and the pot to 230 °c.']
- ['reference/Sourdough Baking Schedule.md', 'wait at least one hour before cutting.']
- ['reference/Sourdough Starter Care.md', 'a grey liquid on top means it is hungry.']
- ['reference/Sourdough Starter Care.md', 'at room temperature feed every 24 hours.']
- ['reference/Sourdough Starter Care.md', 'feed at a ratio of 1:1:1 by weight: one part starter, one part flour, one part water.']
- ['reference/Sourdough Starter Care.md', 'how to keep the starter alive.']
- ['reference/Sourdough Starter Care.md', 'in the fridge, feed once a week.']
- ['reference/Sourdough Starter Care.md', 'pink or orange streaks mean it has gone bad.']
- ['reference/Sourdough Starter Care.md', 'pour it off and feed.']
- ['reference/Sourdough Starter Care.md', 'ready to use when it has doubled and a spoonful floats in water.']
- ['reference/Sourdough Starter Care.md', 'throw it away.']
- ['reference/Sourdough Starter Care.md', 'wholemeal flour makes it rise faster than white flour.']

False negatives:

- ['journal/2025-03-08.md', 'next week i am sending five more applications.']
- ['projects/Budget Tracker App.md', 'i need to add csv export before showing it to farid.']
- ['projects/Portfolio Website.md', 'i must remember to compress the images first because the home page is slow on mobile data.']
- ['projects/Reading Tracker Script.md', 'fixing it is the next job once exams are over.']

## Grounded Q&A

### Split: heldout

| Metric | Mean | Std | Min | Max |
|---|---|---|---|---|
| correct | 0.778 | 0.000 | 0.778 | 0.778 |
| cites_right_note | 1.000 | 0.000 | 1.000 | 1.000 |
| source_retrieved | 1.000 | 0.000 | 1.000 | 1.000 |
| wrongly_refused | 0.000 | 0.000 | 0.000 | 0.000 |
| correctly_refused | 1.000 | 0.000 | 1.000 | 1.000 |
| answers_with_invalid_citation | 0.000 | 0.000 | 0.000 | 0.000 |

### Split: dev

| Metric | Mean | Std | Min | Max |
|---|---|---|---|---|
| correct | 0.556 | 0.000 | 0.556 | 0.556 |
| cites_right_note | 1.000 | 0.000 | 1.000 | 1.000 |
| source_retrieved | 1.000 | 0.000 | 1.000 | 1.000 |
| wrongly_refused | 0.000 | 0.000 | 0.000 | 0.000 |
| correctly_refused | 1.000 | 0.000 | 1.000 | 1.000 |
| answers_with_invalid_citation | 0.000 | 0.000 | 0.000 | 0.000 |

### Split: all

| Metric | Mean | Std | Min | Max |
|---|---|---|---|---|
| correct | 0.667 | 0.000 | 0.667 | 0.667 |
| cites_right_note | 1.000 | 0.000 | 1.000 | 1.000 |
| source_retrieved | 1.000 | 0.000 | 1.000 | 1.000 |
| wrongly_refused | 0.000 | 0.000 | 0.000 | 0.000 |
| correctly_refused | 1.000 | 0.000 | 1.000 | 1.000 |
| answers_with_invalid_citation | 0.000 | 0.000 | 0.000 | 0.000 |

Failures from the last run:

- `q03` "When does the Kestrel Labs internship start?" → (answered) [1]
- `q05` "What does the soil probe read in dry air?" → (answered) [1]
- `q10` "When is my cousin Sara's wedding?" → (answered) [1]
- `q11` "When is the final-year project proposal due?" → (answered) [1]
- `q14` "Which course did Dr. Lim advise me to take next semester?" → (answered) [3]
- `q17` "By what date must the safety form be submitted?" → (answered) [1]

## Timing

- Q&A set: 34.048 s per pass (26 questions)
- Task proposals: 278.100 s per pass (40 notes)
