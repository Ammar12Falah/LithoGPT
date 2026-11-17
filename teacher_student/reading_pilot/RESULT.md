# Reading pilot result: a frontier model reads pictures of well logs

Record written on 17 November 2026. The run finished on 16 November 2026.

## The result in short
Claude Fable 5.2 looked at 20 labelled example pictures of well-log curves from 10 wells of the public FORCE 2020 data. It then read unlabelled pictures of 5 other wells and named the rock at every depth. It named the same rock as the experts on 76.6% of the depth (8,067 m, 53,071 depth steps).

On the same 5 wells:

| Reader | Plain accuracy | Within 3 m | Balanced |
|---|---|---|---|
| Curve pictures, Claude Fable 5.2, 20 example pictures | 76.6 | 80.6 | 71.0 |
| Boosted trees, labels of all 93 other wells | 77.4 | 85.1 | 68.3 |
| Boosted trees, labels of the same 10 example wells | 69.8 | 79.9 | 46.2 |
| Documents (report text and completion log, combined), Claude Fable 5.2 | 66.1 | 75.4 | 64.9 |
| Always "Shale" | 60.3 | 60.3 | 14.3 |
| Curve pictures, Claude Sonnet 5.5 | 65.2 | 67.6 | 51.3 |
| Curve pictures, Claude Haiku 5.5 | 46.6 | 48.7 | 28.3 |

Plain accuracy is the "strict" column of the score files: the same class at the same depth step. Within 3 m is the "tolerant" column: the expert's class is found in the reading within 3 m. Balanced is the mean of the within-3-m score over the classes with at least 20 m, so rare rocks count as much as common ones.

## What the reader was given
- Pictures drawn from the digital curves, in paper-log style: gamma ray, caliper and bit size; resistivity; density, neutron and PEF; sonic; other curves; depth numbers; group and formation names as text. No well name. No rock labels on the pictures of the 5 wells.
- 20 example pictures from 10 other wells, with one more track that shows the expert rock class in colour.
- Written instructions: src/instructions/curve_picture_reader.md. They hold rules of thumb for each rock and allow the reader to use the group and formation names as context.
- The reader was a built-in subagent inside a Claude Code session. No scripted calls were made.

## How it was kept honest
- Wells were drawn at random with a fixed seed (draw.csv, seed 20261115).
- All readings were frozen in commit bcdd5c7 before any expert label of the 5 wells was opened. The reading rules were fixed earlier, in commit 9613929.
- The pass marks were fixed in the brief before the run. Their results are in scores/marks.csv.
- The advisor scored everything again with separate code (advisor_check/score_check.py). Every pooled score matches the run's own figure within 0.05 points. Depth-step classes rebuilt from the frozen reading files differ from the run's tables in 1 step of 53,071.
- The advisor trained a separate plain tree model with other features and settings (advisor_check/baseline_check.py). It gives 69.0 from the ten example wells and 77.4 from the 93 other wells. So the run's two tree models (69.8 and 77.4) are in the right range.

## What this result does not show
Read this before using the number.
1. Five wells and one reading per well. No repeat reading was made, so the spread between readings is not known. A larger test on 23 more wells with controls was planned and not run.
2. The pictures showed group and formation names. A reader that knows only the names and no curves scores 64.8 (names learned from 10 wells) to 66.7 (from 93 wells), see advisor_check/extra_check.py. The frontier model may also know North Sea geology from its training. How much of the 76.6 comes from the names has not been measured. A reading without the names track is the missing check.
3. FORCE 2020 has been public since 2020. Whether the model saw these wells during its training cannot be proven either way.
4. The pilot's headline was the within-3-m score. That score favours readers whose output changes class often. Plain accuracy is the fairer number and is the one quoted here.
5. The cheaper models did much worse (65.2 and 46.6). The result belongs to the strongest model only.
6. Usage was roughly 3 US dollars per well, a rough figure from logged tokens (readings/costs.csv).
7. The Sandstone/Shale class is hard for every reader: 14.0% plain accuracy for the curve-picture reader and 18.6% for the 93-well trees. It is 14% of the depth and about half of the errors of these two readers.
8. Where the experts marked their own label as medium confidence (657 m), the curve-picture reader drops from 78.6 to 53.1 and the 93-well trees from 78.8 to 60.7.

## Other facts worth keeping
- The curve-picture reader agrees with the 93-well trees on 85.8% of the depth.
- It changes rock class 6.5 times per 100 m. The experts change 23.2 times and the 93-well trees 18.6 times. So it draws thicker beds than the experts.
- Against the document reading: the two agree on 77.2% of the depth. Where they disagree (1,822 m), the curve-picture reader is right on 62.9% and the document reading on 19.7%.
- The whole pilot took 3 hours 50 minutes of session work time.

## Where things are (all inside teacher_student/reading_pilot)
- Frozen readings: readings/, one file per well and reader, for example readings/31_3-1__curve_picture.csv.
- Scores: scores/headline.csv, scores/by_well.csv, scores/by_class.csv, scores/by_expert_confidence.csv, scores/confusion_curve_picture.csv, and one table per well with every reader's class at every depth step (the files whose names start with scores/steps_).
- Full report: report.md. Reading rules: reading_rules.md. Well draw: draw.csv. File hashes: hashes.txt.
- Code: src/. The pictures are drawn by src/a3_pictures.py.
- The pictures themselves and the tables that hold expert labels are not in git. They can be drawn again from the public FORCE file.
- The five wells read: 31/3-1, 30/6-5, 35/11-13, 35/11-11, 25/6-2.

## How to check the scores again
Download the public FORCE 2020 train.zip (sha256 e996c8466f2d0dc7116daa71485cc90c31fcfac6345a5bb33165026478b642e9), unzip it, and from the repository root run:

    python3 teacher_student/reading_pilot/advisor_check/score_check.py teacher_student/reading_pilot TRAIN_CSV
    python3 teacher_student/reading_pilot/advisor_check/baseline_check.py teacher_student/reading_pilot TRAIN_CSV
    python3 teacher_student/reading_pilot/advisor_check/extra_check.py teacher_student/reading_pilot TRAIN_CSV

TRAIN_CSV is the path of train.csv. The logs of the check run are next to the scripts.

## Commits
- Branch: claude/focused-hypatia-k9i62o
- Reading rules fixed: 9613929
- Freeze of all readings: bcdd5c7
- Last commit of the pilot: 3a3cb40dcfb90be988e6c54e2ccab60f6d47d2bc

## Check run
- Date of the check run: 17 November 2026.
- Run on top of commit 3a3cb40dcfb90be988e6c54e2ccab60f6d47d2bc with Python 3.13.18, pandas 3.0.5, numpy 2.5.3, lightgbm 4.7.0.
- train.zip used, sha256: e996c8466f2d0dc7116daa71485cc90c31fcfac6345a5bb33165026478b642e9 (matches the expected value).

Checks:
- a. score_check.log: PASS. Largest gap between the check's figure and the run's figure: 0.05 points (limit 0.1). Curve picture row: strict 76.6, tolerant 80.6, balanced 71.0. Rebuilt depth-step classes: "text" differs in 1 step of 53,071, every other reader in 0 steps.
- b. baseline_check.log: PASS. Ten example wells -> 5 test wells: strict 69.0 (expected 69.0, within 1.5). All 93 other wells -> 5 test wells: strict 77.4 (expected 77.4, within 1.5).
- c. extra_check.log: PASS. Names-only reader: strict 64.8 (names from the 10 example wells) and 66.7 (from all 93 other wells). Where the curve-picture reader and the document reading disagree, curve picture is right on 62.9%. Changes of rock class per 100 m: expert 23.2, curve picture 6.5.

sha256 of the scripts and logs (all in advisor_check/):

    5c740af95018933d9780132fc0c88acfdc45af0fdc8cfb4997ab05ff48b3c10c  score_check.py
    62d571164219adba9594ed889d70330b28c2b86f3fbdf84b1bdc7d850caa6e59  baseline_check.py
    7f4142fe031f04b3f241067fb245eef680b135c6658c113d57210e8c3ce96230  extra_check.py
    4b71af269ca49fe702104e7441b737dfa52a99de6edc35e43a0de4967a368318  score_check.log
    b5f7be78d7b0f4f92f939840984887f008d9e99fafa7eed07c1b0828015dbda2  baseline_check.log
    03ea846dc7dd0c5366496978f7e0a6034f637fa13a2d3e2b4025b5cd258d4cc0  extra_check.log
