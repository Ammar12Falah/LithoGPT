# Reading pilot: report

First step of the teacher and student system. Written 16 November 2026. Branch `claude/focused-hypatia-k9i62o`. All 5 test wells were finished. Freeze commit: `bcdd5c7`. Scored on 53 071 depth steps (8 067 m) of the five test wells. The headline number is the tolerant agreement with unread depth counted as wrong.

## First screen

### The three marks (main model only)

| mark | verdict | numbers (headline, percent) |
|---|---|---|
| 1. Room | **FAIL** | 70-well model 82.8; mean of the five ten-well draws 79.7 (range 78.5 to 80.8); gap 3.1 points, 5 needed. On the 23 curve wells. A few expert wells are already enough here. |
| 2. Teacher (combined reading) | **NOT DECIDED** | teacher 75.4; ten-well model 79.9 (teacher -4.5, ahead in 0 of 5 wells, ten-well model ahead in 5); all-shale line 60.3 (teacher +15.1); all-well model 85.1 (all-well model ahead). |
| 3. Picture idea (curve pictures) | **PASS** | curve picture 80.6; ten-well model 79.9; gap +0.7 points (-5 or better needed; ahead in 3 wells, behind in 2). Against the all-well model (85.1): -4.5, not decided (all-well model ahead in 5 of 5 wells). |

Would another score change a verdict?
- Mark 1: yes with the balanced agreement (gap 12.8 points, **pass**). No with the strict agreement (gap 3.8, fail).
- Mark 2: yes with the balanced agreement (teacher 64.9, ten-well model 46.2, all-well model 68.3: **strong pass**). No with the strict agreement (teacher 66.1, ten-well model 69.8, all-shale 60.3: not decided).
- Mark 3: no (balanced gap +24.8: pass; strict gap +6.8: pass).

### Headline number of every reader (pooled over the 5 test wells, percent)

| reader | headline: tolerant, unread = wrong | tolerant on read depth | coverage | strict | soft | balanced |
|---|---|---|---|---|---|---|
| text | 72.1 | 72.8 | 99.1 | 68.4 | 93.3 | 38.2 |
| log picture | 74.4 | 75.0 | 99.1 | 66.3 | 94.9 | 64.5 |
| combined (the teacher reading) | 75.4 | 76.1 | 99.1 | 66.1 | 95.3 | 64.9 |
| curve picture | 80.6 | 80.6 | 99.9 | 76.6 | 96.1 | 71.0 |
| ten-well model | 79.9 | 79.9 | 100.0 | 69.8 | 94.6 | 46.2 |
| all-well model | 85.1 | 85.1 | 100.0 | 77.4 | 96.7 | 68.3 |
| all-shale line | 60.3 | 60.3 | 100.0 | 60.3 | 91.7 | 14.3 |
| text (Sonnet) | 72.2 | 72.2 | 99.6 | 68.3 | 93.8 | 36.0 |
| log picture (Sonnet) | 68.7 | 69.3 | 99.1 | 63.5 | 92.4 | 39.9 |
| combined (Sonnet) | 70.7 | 70.8 | 99.9 | 63.9 | 93.7 | 41.2 |
| curve picture (Sonnet) | 67.6 | 67.6 | 100.0 | 65.2 | 92.3 | 51.3 |
| text (Haiku) | 71.7 | 72.9 | 97.3 | 67.9 | 92.9 | 35.6 |
| log picture (Haiku) | 63.6 | 64.1 | 99.1 | 61.5 | 91.3 | 39.0 |
| combined (Haiku) | 65.7 | 66.2 | 99.1 | 61.6 | 92.1 | 40.3 |
| curve picture (Haiku) | 48.7 | 48.7 | 99.9 | 46.6 | 87.5 | 28.3 |

Readers with (Sonnet) or (Haiku) are the cheaper readers of Part D. They do not count for the marks.

### Cheaper readers against the main model (Part D)

| reading | model | verdict | main | cheaper | gap (points) | wells cheaper ahead | wells main ahead |
|---|---|---|---|---|---|---|---|
| combined (the teacher reading) | Sonnet 5.5 | not decided | 75.4 | 70.7 | -4.7 | 0 | 4 |
| combined (the teacher reading) | Haiku 5.5 | behind the main model | 75.4 | 65.7 | -9.7 | 0 | 5 |
| curve picture | Sonnet 5.5 | behind the main model | 80.6 | 67.6 | -13.0 | 0 | 5 |
| curve picture | Haiku 5.5 | behind the main model | 80.6 | 48.7 | -31.9 | 0 | 5 |
| text | Sonnet 5.5 | not decided | 72.1 | 72.2 | +0.1 | 2 | 3 |
| text | Haiku 5.5 | not decided | 72.1 | 71.7 | -0.4 | 1 | 2 |
| log picture | Sonnet 5.5 | behind the main model | 74.4 | 68.7 | -5.7 | 0 | 4 |
| log picture | Haiku 5.5 | behind the main model | 74.4 | 63.6 | -10.8 | 0 | 5 |

### Three main findings

1. **The picture idea holds for the main model, and only for it.** Fact: reading the log curves
   as pictures, after 20 labelled example pictures, gave 80.6 percent. The plain model trained on
   the same ten example wells gave 79.9. The picture reader was more even over the rock classes
   (balanced 71.0 against 46.2) and better on strict agreement (76.6 against 69.8). The all-well
   model (93 wells) stayed above it in all five wells, by 4.5 points pooled. With cheaper readers
   the same method fell to 67.6 (Sonnet) and 48.7 (Haiku).
2. **The teacher from documents sits between the all-shale line and ten expert wells on the
   headline number, and above ten expert wells on rare rocks.** Fact: the combined reading gave
   75.4 percent, 15.1 points above the all-shale line and 4.5 below the ten-well model, which was
   ahead in all five wells. The teacher was much better on Tuff (75 against 19), Coal (89 against
   48), Limestone (58 against 40) and Marl (47 against 0). It almost never matched Sandstone/Shale
   (6 percent of 1 155 m). Judgment: the documents name the main rock well and the rare beds well,
   but they do not carry the experts' line between Shale, Sandstone/Shale and Sandstone.
3. **Cheaper readers read text as well as the main model, and pictures worse.** Fact: text
   reading gave 72.1 (main), 72.2 (Sonnet) and 71.7 (Haiku). Log pictures gave 74.4, 68.7 and 63.6.
   The combined teacher reading gave 75.4, 70.7 (not decided, 4.7 points lower and behind in 4 of 5
   wells) and 65.7 (behind). The cheaper readers wrote far fewer rows from pictures and took a sixth
   to a ninth of the time.

### Three main doubts

1. **Five wells are few.** Fact: on the curve wells the gap between two plain models changes
   from well to well with a spread of about 6 points, so five wells can show a gap of about
   5.5 points at best (power check, table T2). The gaps that decide Mark 2 (4.5 points) and the
   distance of the curve pictures to the all-well model (4.5 points) are inside that noise. One
   well, 30/6-5, holds 41 percent of the scored depth.
2. **Claude may already know these wells.** Fact: the FORCE 2020 files and the reports of these
   wells have been public for years, and the document readers saw the well names. I cannot check
   what the model has seen in training. The readers were told to use only what is on the page.
   Judgment: the readers' weak score on Sandstone/Shale, and the many places where they disagree
   with the experts, do not look like recall of the labels. This is not proof.
3. **The method was fitted on little data, by me, and for the main model only.** Fact: the word
   map and the combined rule were settled on two practice wells, the curve-picture method on three
   example wells, and nothing was tuned for Sonnet or Haiku. Two practice choices cut both ways on
   the test wells: sending siltstone to Shale, and sending tuffaceous claystone to Tuff (of the
   194 m of conflicts between teacher and experts, 128 m are teacher Tuff against expert Shale).
   I also had to repair my own picture cutting during the readings (30/6-5 was read twice; see
   "What went differently"). The experts' labels themselves differ in habit from well to well
   (the plain model scores between 35 and 93 percent strict on single curve wells).

### Cost of the main readings (per well)

| well | curve: minutes | curve: pictures | log: minutes | log: pictures | text: minutes | text: pictures | text: pages read |
|---|---|---|---|---|---|---|---|
| 31/3-1 | 18.0 | 41 | 14.1 | 23 | 33.1 | 32 | 110 |
| 30/6-5 | 17.7 | 54 | 10.4 | 36 | 33.6 | 32 | 118 |
| 35/11-13 | 7.0 | 24 | 1.9 | 6 | 9.2 | 13 | 49 |
| 35/11-11 | 18.3 | 41 | 17.6 | 22 | 11.2 | 13 | 63 |
| 25/6-2 | 6.4 | 25 | 4.5 | 7 | 6.5 | 12 | 52 |
| all five | 67.4 | 185 | 48.5 | 94 | 93.6 | 102 | 392 |

Curve pictures: 20 of the pictures per well are the labelled examples. Text "pictures" are page pictures that the reader opened; "pages read" are pages of page text. Tokens reported by the subagent tool, all five wells: curve picture 1,040,197, log picture 839,691, text 1,565,639. Not in the table: the set-aside readings of 30/6-5 (15.4 minutes), the method trial (9 readers, 91 minutes of reader time) and the practice (8 readers, 92 minutes), run side by side.

### Cost and quality by model (Part D table)

| reading | model | headline | coverage | balanced | minutes | tokens | pages | pictures |
|---|---|---|---|---|---|---|---|---|
| text | main model | 72.1 | 99.1 | 38.2 | 93.6 | 1,565,639 | 392 | 102 |
| text | Sonnet 5.5 | 72.2 | 99.6 | 36.0 | 36.9 | 1,101,190 | 307 | 65 |
| text | Haiku 5.5 | 71.7 | 97.3 | 35.6 | 51.2 | 1,611,011 | 271 | 59 |
| log picture | main model | 74.4 | 99.1 | 64.5 | 48.5 | 839,691 | 0 | 94 |
| log picture | Sonnet 5.5 | 68.7 | 99.1 | 39.9 | 8.5 | 559,758 | 0 | 94 |
| log picture | Haiku 5.5 | 63.6 | 99.1 | 39.0 | 8.2 | 603,638 | 0 | 94 |
| combined | main model | 75.4 | 99.1 | 64.9 | 142.1 | 2,405,330 | 392 | 196 |
| combined | Sonnet 5.5 | 70.7 | 99.9 | 41.2 | 45.4 | 1,660,948 | 307 | 159 |
| combined | Haiku 5.5 | 65.7 | 99.1 | 40.3 | 59.4 | 2,214,649 | 271 | 153 |
| curve picture | main model | 80.6 | 99.9 | 71.0 | 67.4 | 1,040,197 | 0 | 185 |
| curve picture | Sonnet 5.5 | 67.6 | 100.0 | 51.3 | 7.9 | 703,923 | 0 | 185 |
| curve picture | Haiku 5.5 | 48.7 | 99.9 | 28.3 | 7.0 | 733,414 | 0 | 185 |

Minutes, tokens, pages and pictures are sums over the five wells. The combined reading costs what its text and log-picture readings cost. Tokens are counts of tokens, not money: a token of a cheaper model costs less.

## Details

Facts are stated plainly. Where I give my own view, the sentence starts with "Judgment".
The working record, with times, is in `notes.md`.

### 1. What was done

1. Drew the 98 training wells with seed 20261115, before anything else (commit 6ac79fd).
2. Matched wells to the FactPages documents table and gave roles: 5 test, 10 example (2 of them
   practice), 23 curve, 60 extra wells. No test well had to be replaced. Details in `draw.csv`.
3. Chose one plain-model setup inside the 60 extra wells, ran the learning curve, trained the
   ten-well model and the all-well model.
4. Settled the curve-picture method on three example wells, and the document rules on the two
   practice wells. Fixed `reading_rules.md` (commit 9613929).
5. Read the five test wells, one after the other: three fresh readers per well.
6. Part D: read the five wells again with Sonnet 5.5 and with Haiku 5.5 as readers.
7. Froze all readings (commit bcdd5c7). Only then opened the test wells' expert labels and scored.

### 2. Room (Mark 1)

- Plain model: gradient-boosted trees (LightGBM), 12 classes. Inputs: the 20 curves, depth,
  position, group and formation as categories, the same curves 0.5 to 5 m above and below, rolling
  mean and spread over about 10 m, gamma ray normalised by well. 31 leaves, learning rate 0.05,
  100 rounds, trained on every second depth step. Chosen by a three-fold well-by-well check inside
  the extra wells (table in `notes.md`, files in `curve/`). All candidates landed between 71 and
  74 percent strict there. Then not changed.
- Learning curve on the 23 curve wells (table T1): the headline number rises from 63.6 percent
  with 1 well to 72.6 (3 wells), 79.7 (10), 81.2 (30) and 82.8 (70). The all-shale line is 60.1.
  The balanced agreement keeps rising: 20, 26, 36, 44, 49. More wells mainly help the rare rocks.
- The brief says the best competition teams reached about 80 percent strict. My 70-well model
  reaches 76.0 percent strict on the curve wells. I looked for a mistake and found none: the label
  join is checked by the scores themselves, all setups give the same level, and 18 of the 23 curve
  wells score between 72 and 93 percent strict. Three wells pull the pooled number down (34/10-35 at
  35 percent strict with 98 percent soft, 16/8-1 at 50, 16/11-1 ST3 at 55). Without 34/10-35 alone
  the model reaches 79.3. Judgment: this is a difference in labelling habit between wells, not a
  weak model. The model uses 70 wells and simple features; the competition models used all wells.
- Power check (table T2): the well-by-well gap between the 70-well model and a ten-well draw has
  a mean of 3.9 points and a spread of 6.2 points (one draw) over the 23 curve wells. With five
  wells the standard error is 2.8 points. Five wells can show a gap of about 5.5 points, not less.
  Only 23 percent of random sets of five curve wells would have called the 70-well model "ahead"
  by the rule of the brief, although it is ahead in 19 of the 23 wells.

### 3. Picture idea (Mark 3)

- Pictures: 860 x 1320 pixels, 100 m per picture, drawn from the logs file only. No well name, no
  labels. The reader saw 20 labelled example pictures from the 10 example wells (11 of the 12
  classes; no Basement), then all pictures of one test well in depth order.
- Method trial on three example wells with hidden labels: 100 m pictures 78.9 percent, 50 m
  pictures 78.6 percent at twice the effort, a second version of the instructions 78.5 percent.
  So the trial numbers (about 79) were close to what the test wells gave (80.6).
- By class (table T6): the picture reader is good on Shale (95), Sandstone (91), Tuff (91) and Coal
  (93), middling on Marl (64) and Limestone (47), weak on Sandstone/Shale (17). The readers said
  themselves that they call Tuff from the formation name (Balder) and an example picture, not from
  the curves.
- Against the all-well model the picture reader is 4.5 points lower and behind in all five wells.
  By the rule of the brief this is "not decided", because the gap is under 5 points.

### 4. Teacher from documents (Mark 2)

- Text reading: pages found by local text search and OCR, then read closely by a fresh reader.
  Two wells have cuttings sample lists (31/3-1: 728 rows; 30/6-5: 826 rows). The other three have
  only core or sidewall-core descriptions and formation summaries (62, 59 and 77 rows).
- Log-picture reading: the completion log cut into pictures of about 110 m with 10 m overlap,
  showing the rock column, its depth numbers and the written descriptions. Header and legend given.
- Combined reading (fixed rule): core and sidewall-core text first, then the log picture, then
  other text. On the test wells 4 to 12 percent of the depth came from text, the rest from the log
  picture. The combined reading was named as the teacher before any test well was read.
- Results: text 72.1, log picture 74.4, combined 75.4. None of the three is "ahead" of another
  by the rule. All three are ahead of the all-shale line (60.3). The ten-well model (79.9) is
  ahead of the text and of the log picture, and 4.5 points above the combined reading.
- The practice wells had promised more: 75.8 percent for the combined reading on two sections.
  The test wells gave 75.4. Judgment: the practice numbers were not too rosy after all for the
  combined reading, but the text reading did better on the test wells (72.1) than on the practice
  wells (67.6), mostly thanks to the two wells with cuttings lists.
- Where text and log picture agree (table T11): they name the same class on 78 percent of the
  depth and the same family on 93 percent of the depth both read. Where they agree, they are right
  75 percent of the time (strict). Where they differ (1 687 m), the text is right 46 percent and the
  log picture 36 percent of the time. Judgment: agreement between the two is not a strong sign of
  being right here, because both miss Sandstone/Shale in the same way.
- By class (table T6): the teacher gets Shale 90, Sandstone 89, Coal 89, Tuff 75, Limestone 58,
  Marl 47, Sandstone/Shale 6. The text reading alone is weak on thin rare beds (Limestone 6,
  Coal 22, Tuff 24); the rock column on the log carries them.
- By expert confidence (table T7): all readers do worse where the experts were less sure. Where
  the experts gave "medium" (657 m), the teacher scores 57 percent and the all-well model 75.
- If the second class of a row also counted, the teacher would score 86.6 instead of 75.4
  (table T12). This is a side number. It shows that many misses are beds the documents name as the
  second rock of an interval.
- Conflicts: 19 intervals of at least 3 m where the teacher names a rock of another family than
  the experts, 194 m in all (2.4 percent of the depth): 9 with teacher Tuff and expert Shale
  (128 m), 5 with teacher Shale and expert Tuff (38 m), and 5 between Shale and Marl or Limestone
  (29 m). All 19 have a sheet (fewer than the 40 allowed, so none was drawn at random).

### 5. Cheaper readers (Part D)

- Same picture files, pages, instructions, example pictures and task messages; a fresh memory for
  each reading; no tuning. Model set with the subagent tool ("sonnet", "haiku"). The tool does
  not report the served model version back, and I could not check whether the cheaper models see
  pictures at lower detail.
- Text: no real difference between the three models (72.1, 72.2, 71.7). The cheaper readers wrote
  about as many rows (1 752, 1 699, 1 693). Haiku left 9.7 percent of 31/3-1 unread.
- Log picture: Sonnet 5.7 points lower and behind in 4 of 5 wells, Haiku 10.8 lower and behind in
  all 5. They wrote 352 and 201 rows against 809: they merged thin beds. Their balanced agreement
  is 40 and 39 against 64.5.
- Curve picture: Sonnet 13.0 points lower, Haiku 31.9 lower (below the all-shale line of 60.3).
- Speed: a cheaper reader needed about 1 to 4 minutes for a picture reading where the main model
  needed 2 to 18, and 2 to 24 minutes for a text reading where the main model needed 7 to 34.
- Three cheaper readers each made one tool call outside their task (see `notes.md`). None of it
  touched data or readings.
- Judgment: for the full project, text reading could go to a cheaper model at little loss. Picture
  reading cannot, with this method as it stands. The method was built for the main model, so a
  method tuned for a cheaper model might close part of the gap. This pilot did not test that.

### 6. What went differently from the brief

- **Picture cutting fault, repaired before the freeze.** The long scanned sheets are not straight.
  My first cut clipped the rock column of 30/6-5 in places. The first reader said so and left
  232 m without a class. I added a drift correction, cut 30/6-5 and 35/11-11 again, and had a
  fresh reader read 30/6-5 again in full. The first reading was set aside. No label had been seen.
  Scored after the freeze, on that well: kept reading 76.3, faulty first reading 70.6, first
  reading with a patch of the lower part 76.1 (table T13). The pooled result does not hang on it.
- **Pause.** I stopped once to wait for a reader and the session went idle for 6.7 hours. Nothing
  was lost. Idle time is not counted.
- **Readers side by side.** The three readings of a well ran at the same time, wells in the drawn
  order. In Part D up to 20 readers ran at once.
- **Trial on sections.** To keep the method trial inside one hour, each hidden example well was
  read on one 1 000 m section. The practice log pictures used 1 200 m sections.
- **Task messages.** The text reader's task message allowed writing the file in parts and asked
  for one row per sample. The log readers of wells 4 and 5 were told in one sentence where the
  depth numbers stand on that sheet. All three models got the same messages.
- **Conflict sheets.** There were only 19 conflicts, so all were drawn.
- **Kept out of git** (terms of reuse unclear, rule 11): the pictures drawn from the FORCE logs,
  the page and log pictures from FactPages, the conflict sheets with expert labels and log plots,
  and every table with expert labels. The step tables in `scores/` hold no expert class. The
  conflict list in git holds no expert class. The pictures were sent to Ammar as one zip file.

### 7. What I could not do or verify

- The licence of the FORCE files: the three files I was allowed to open say nothing about it.
- Whether Claude has seen these wells, their reports or their labels in training.
- The exact model version behind "sonnet" and "haiku", and the picture detail they get.
- Whether every reader kept to its rules. I rely on the readers' own reports; three cheaper
  readers reported one stray tool call each.
- Depth shifts between driller's depth, logger's depth and the logs of `train.csv`. No shift was
  applied to any reading. Core depths in the text readings are driller's depths.
- The well names `16/11-1 ST3` and `25/2-13 T4` could not be matched to the documents table.
- Money cost. I report minutes and tokens only.

### 8. Files, and how to run the number work again

- `draw.csv` (roles and reasons), `reading_rules.md` (fixed rules and the readers' instructions),
  `notes.md` (working record), `data_count.md` (Part C).
- `readings/`: one CSV per well and reading; `__sonnet` and `__haiku` for Part D; `costs.csv`,
  `costs_partd.csv`; `set_aside/` for the readings not used.
- `scores/`: headline, by well, by class, by expert confidence, confusion tables, comparisons,
  marks, Part D tables, and one table per test well with the class from every reader at every
  depth step (no expert class).
- `curve/`: learning curve tables and chart, setup check, power check, Mark 1.
- `conflicts/`, `check_sheet/`: lists with references and the extracted rows.
- `manifest.csv`, `hashes.txt`: every downloaded file and every result file with its sha256.
- One command: `sh run.sh`. It downloads the allowed files if they are missing, splits the
  training file, runs the learning curve, trains the two models, rebuilds the combined readings
  and scores everything from the saved readings. The readings themselves are not made again.

## Tables

### T1. Learning curve of the plain model on the 23 curve wells (percent)

| n_wells | draws | tolerant_mean | tolerant_min | tolerant_max | strict_mean | soft_mean | balanced_mean |
|---|---|---|---|---|---|---|---|
| 1 | 5 | 63.6 | 49.2 | 72.2 | 55.9 | 90.3 | 20.1 |
| 3 | 5 | 72.6 | 70.4 | 76.4 | 65.3 | 91.9 | 25.6 |
| 10 | 5 | 79.7 | 78.5 | 80.8 | 72.2 | 93.9 | 36.3 |
| 30 | 5 | 81.2 | 80.1 | 82.2 | 74.3 | 94.8 | 43.6 |
| 70 | 1 | 82.8 | 82.8 | 82.8 | 76.0 | 95.8 | 49.1 |
| ten-well model (the 10 example wells) | 1 | 79.2 |  |  | 73.4 | 95.0 | 44.1 |
| all-shale line | 1 | 60.1 |  |  | 60.1 | 87.5 | 9.1 |

Chart: `curve/learning_curve.png`. Draws: `curve/learning_curve_draws.csv`.

### T2. Power check on the 23 curve wells (70-well model minus ten-well draws, headline, points)

| what | value |
|---|---|
| curve wells | 23.0 |
| mean well gap points | 3.9 |
| median well gap points | 2.1 |
| sd of well gap points avg over draws | 4.8 |
| sd of well gap points single draw | 6.2 |
| min well gap | -2.5 |
| max well gap | 13.5 |
| wells with 70 ahead | 19.0 |
| standard error with 5 wells points | 2.8 |
| smallest gap 5 wells can show points 2se | 5.5 |
| five random curve wells pooled gap p05 | -0.9 |
| five random curve wells pooled gap p50 | 3.1 |
| five random curve wells pooled gap p95 | 8.3 |
| share of 5 well draws that call 70 ahead pct | 23.3 |

### T3. Headline number by well (percent)

| reader | 25/6-2 | 30/6-5 | 31/3-1 | 35/11-11 | 35/11-13 |
|---|---|---|---|---|---|
| text | 79.4 | 77.2 | 66.1 | 67.6 | 75.4 |
| log picture | 77.5 | 76.3 | 73.0 | 70.9 | 79.0 |
| combined | 81.2 | 77.0 | 75.8 | 70.2 | 79.0 |
| curve picture | 78.2 | 82.9 | 82.0 | 76.0 | 80.2 |
| ten-well model | 86.9 | 81.7 | 77.3 | 75.2 | 93.4 |
| all-well model | 80.7 | 85.3 | 89.2 | 81.9 | 82.8 |
| all-shale line | 71.2 | 68.3 | 48.5 | 58.5 | 50.3 |
| text (Sonnet) | 79.1 | 77.4 | 65.5 | 68.5 | 73.0 |
| log picture (Sonnet) | 75.8 | 70.9 | 63.4 | 66.8 | 79.0 |
| combined (Sonnet) | 80.9 | 72.3 | 67.6 | 67.5 | 79.0 |
| curve picture (Sonnet) | 73.9 | 68.2 | 68.5 | 62.4 | 75.9 |
| text (Haiku) | 79.4 | 77.2 | 64.3 | 68.2 | 73.0 |
| log picture (Haiku) | 73.6 | 61.1 | 62.6 | 64.6 | 74.9 |
| combined (Haiku) | 78.7 | 63.7 | 65.5 | 64.7 | 75.0 |
| curve picture (Haiku) | 31.9 | 48.1 | 56.5 | 43.2 | 60.7 |

### T4. Strict agreement by well (percent)

| reader | 25/6-2 | 30/6-5 | 31/3-1 | 35/11-11 | 35/11-13 |
|---|---|---|---|---|---|
| text | 71.9 | 73.7 | 60.3 | 66.2 | 74.0 |
| log picture | 72.4 | 66.4 | 64.4 | 65.2 | 75.1 |
| combined | 72.5 | 66.4 | 64.4 | 64.4 | 75.3 |
| curve picture | 73.2 | 80.1 | 78.2 | 70.7 | 72.6 |
| ten-well model | 82.6 | 71.6 | 65.5 | 67.4 | 74.4 |
| all-well model | 74.2 | 80.5 | 79.4 | 72.3 | 70.0 |
| all-shale line | 71.2 | 68.3 | 48.5 | 58.5 | 50.3 |
| text (Sonnet) | 71.5 | 73.3 | 60.3 | 66.9 | 71.9 |
| log picture (Sonnet) | 72.1 | 63.1 | 60.8 | 62.8 | 75.8 |
| combined (Sonnet) | 72.5 | 63.2 | 61.8 | 63.0 | 75.9 |
| curve picture (Sonnet) | 72.1 | 66.4 | 66.9 | 60.3 | 63.3 |
| text (Haiku) | 71.9 | 73.7 | 57.7 | 66.8 | 72.0 |
| log picture (Haiku) | 69.3 | 59.6 | 60.7 | 61.9 | 71.2 |
| combined (Haiku) | 69.7 | 60.0 | 60.8 | 61.6 | 71.3 |
| curve picture (Haiku) | 27.8 | 46.3 | 55.7 | 40.2 | 56.1 |

### T5. Coverage by well, document and picture readers of the main model (percent)

| reader | 25/6-2 | 30/6-5 | 31/3-1 | 35/11-11 | 35/11-13 |
|---|---|---|---|---|---|
| text | 100.0 | 100.0 | 96.5 | 99.9 | 100.0 |
| log picture | 100.0 | 100.0 | 96.5 | 100.0 | 100.0 |
| combined | 100.0 | 100.0 | 96.5 | 100.0 | 100.0 |
| curve picture | 99.9 | 100.0 | 99.9 | 100.0 | 99.9 |

### T6. Headline number by expert rock class (percent)

| expert_class | metres of expert label | text | log picture | combined | curve picture | ten-well model | all-well model |
|---|---|---|---|---|---|---|---|
| Shale | 4865.8 | 92.6 | 88.4 | 90.2 | 94.9 | 96.7 | 97.5 |
| Sandstone | 1375.9 | 84.6 | 89.2 | 88.8 | 90.6 | 92.4 | 95.2 |
| Sandstone/Shale | 1155.2 | 0.2 | 6.2 | 6.3 | 17.4 | 27.8 | 39.4 |
| Limestone | 249.6 | 6.2 | 61.1 | 58.4 | 46.5 | 39.6 | 52.7 |
| Marl | 220.7 | 38.6 | 42.4 | 46.5 | 63.6 | 0.0 | 19.1 |
| Tuff | 163.1 | 23.7 | 75.0 | 75.0 | 91.0 | 19.3 | 94.3 |
| Coal | 32.7 | 21.9 | 88.8 | 88.8 | 93.0 | 47.9 | 80.0 |
| Dolomite | 3.8 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

Classes with less than 20 m (Dolomite) do not enter the balanced agreement. Halite, Anhydrite, Chalk and Basement do not occur in the test wells.

### T7. Headline number by the experts' confidence level (percent)

| expert_confidence | metres | text | log picture | combined | curve picture | ten-well model | all-well model | all-shale line |
|---|---|---|---|---|---|---|---|---|
| 1 high | 7201.3 | 74.5 | 76.3 | 77.1 | 82.1 | 82.4 | 85.8 | 62.8 |
| 2 medium | 657.1 | 57.2 | 53.3 | 56.9 | 62.0 | 66.6 | 74.8 | 46.7 |
| 3 low | 206.4 | 36.3 | 73.4 | 73.4 | 87.8 | 34.9 | 94.3 | 17.7 |
| not given | 2.0 | 38.5 | 38.5 | 38.5 | 61.5 | 53.8 | 84.6 | 30.8 |

### T8. Which classes get mixed up: the teacher reading (metres; rows = expert class, columns = teacher class)

| expert class \ reader class (metres) | Sandstone | Sandstone/Shale | Shale | Marl | Dolomite | Limestone | Tuff | Coal | (no class) |
|---|---|---|---|---|---|---|---|---|---|
| Sandstone | 1108.7 | 53.5 | 124.8 | 0.0 | 0.0 | 41.0 | 0.0 | 1.1 | 46.8 |
| Sandstone/Shale | 401.1 | 45.4 | 681.0 | 0.0 | 0.0 | 18.4 | 4.4 | 1.1 | 3.8 |
| Shale | 644.2 | 57.6 | 3883.4 | 26.6 | 0.5 | 78.1 | 149.7 | 5.9 | 19.8 |
| Marl | 0.0 | 1.1 | 46.7 | 79.3 | 0.5 | 93.2 | 0.0 | 0.0 | 0.0 |
| Dolomite | 2.9 | 0.0 | 0.9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Limestone | 37.5 | 2.1 | 108.2 | 10.2 | 0.0 | 89.8 | 1.7 | 0.0 | 0.0 |
| Tuff | 0.0 | 0.0 | 47.0 | 0.0 | 0.0 | 0.9 | 115.2 | 0.0 | 0.0 |
| Coal | 5.5 | 2.7 | 11.4 | 0.0 | 0.0 | 0.0 | 0.0 | 13.1 | 0.0 |

### T9. Which classes get mixed up: the curve-picture reading (metres)

| expert class \ reader class (metres) | Sandstone | Sandstone/Shale | Shale | Marl | Limestone | Tuff | Coal | (no class) |
|---|---|---|---|---|---|---|---|---|
| Sandstone | 1186.5 | 63.8 | 108.8 | 0.0 | 14.7 | 0.0 | 0.8 | 1.2 |
| Sandstone/Shale | 207.3 | 162.2 | 765.8 | 3.5 | 14.3 | 0.0 | 1.7 | 0.5 |
| Shale | 112.6 | 91.4 | 4462.1 | 28.1 | 42.7 | 119.6 | 7.1 | 2.1 |
| Marl | 0.0 | 0.8 | 85.4 | 126.5 | 8.1 | 0.0 | 0.0 | 0.0 |
| Dolomite | 2.7 | 0.0 | 1.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Limestone | 38.9 | 8.5 | 78.3 | 33.3 | 86.3 | 4.0 | 0.0 | 0.3 |
| Tuff | 0.0 | 0.0 | 20.5 | 0.0 | 0.2 | 142.4 | 0.0 | 0.0 |
| Coal | 1.8 | 3.3 | 11.7 | 0.0 | 0.0 | 0.0 | 15.8 | 0.0 |

The same tables for every other reader are in `scores/confusion_*.csv`.

### T10. Pairs of main readers (headline; ahead needs 5 points and 4 of 5 wells)

| reader_a | reader_b | a_pct | b_pct | gap_points_a_minus_b | wells_a_ahead | wells_b_ahead | verdict |
|---|---|---|---|---|---|---|---|
| text | log picture | 72.1 | 74.4 | -2.3 | 2 | 3 | not decided |
| text | combined | 72.1 | 75.4 | -3.3 | 1 | 4 | not decided |
| text | curve picture | 72.1 | 80.6 | -8.5 | 1 | 4 | curve picture ahead |
| text | ten-well model | 72.1 | 79.9 | -7.8 | 0 | 5 | ten-well model ahead |
| text | all-well model | 72.1 | 85.1 | -13.0 | 0 | 5 | all-well model ahead |
| text | all-shale line | 72.1 | 60.3 | 11.8 | 5 | 0 | text ahead |
| log picture | combined | 74.4 | 75.4 | -1.0 | 1 | 3 | not decided |
| log picture | curve picture | 74.4 | 80.6 | -6.2 | 0 | 5 | curve picture ahead |
| log picture | ten-well model | 74.4 | 79.9 | -5.5 | 0 | 5 | ten-well model ahead |
| log picture | all-well model | 74.4 | 85.1 | -10.7 | 0 | 5 | all-well model ahead |
| log picture | all-shale line | 74.4 | 60.3 | 14.1 | 5 | 0 | log picture ahead |
| combined | curve picture | 75.4 | 80.6 | -5.2 | 1 | 4 | curve picture ahead |
| combined | ten-well model | 75.4 | 79.9 | -4.5 | 0 | 5 | not decided |
| combined | all-well model | 75.4 | 85.1 | -9.7 | 1 | 4 | all-well model ahead |
| combined | all-shale line | 75.4 | 60.3 | 15.1 | 5 | 0 | combined ahead |
| curve picture | ten-well model | 80.6 | 79.9 | 0.7 | 3 | 2 | not decided |
| curve picture | all-well model | 80.6 | 85.1 | -4.5 | 0 | 5 | not decided |
| curve picture | all-shale line | 80.6 | 60.3 | 20.3 | 5 | 0 | curve picture ahead |
| ten-well model | all-well model | 79.9 | 85.1 | -5.2 | 2 | 3 | not decided |
| ten-well model | all-shale line | 79.9 | 60.3 | 19.6 | 5 | 0 | ten-well model ahead |
| all-well model | all-shale line | 85.1 | 60.3 | 24.8 | 5 | 0 | all-well model ahead |

All pairs and the same for strict and balanced agreement: `scores/comparisons.csv`.

### T11. Where text and log picture agree with each other

| well | share_same_class_of_all_pct | share_same_family_of_both_read_pct | strict_where_same_pct | tolerant_where_same_pct | differ_metres | strict_text_where_differ_pct | strict_log_where_differ_pct |
|---|---|---|---|---|---|---|---|
| 31/3-1 | 68.4 | 86.0 | 75.0 | 75.2 | 565.7 | 31.9 | 46.8 |
| 30/6-5 | 76.2 | 96.2 | 78.7 | 79.3 | 781.9 | 57.6 | 26.8 |
| 35/11-13 | 92.9 | 98.9 | 77.1 | 77.7 | 26.1 | 33.7 | 48.8 |
| 35/11-11 | 87.1 | 92.5 | 69.3 | 69.8 | 249.1 | 45.6 | 36.3 |
| 25/6-2 | 85.6 | 95.9 | 76.6 | 78.0 | 64.0 | 43.9 | 47.5 |
| POOLED | 78.2 | 92.9 | 75.2 | 75.7 | 1686.9 | 46.3 | 36.0 |

### T12. Side numbers: tolerant agreement if the second class of a document reading also counts (not used for any mark)

| reader | tolerant_main_only | tolerant_with_second_class |
|---|---|---|
| combined | 75.4 | 86.6 |
| combined (Haiku) | 65.7 | 77.3 |
| combined (Sonnet) | 70.7 | 86.9 |
| log picture | 74.4 | 85.4 |
| log picture (Haiku) | 63.6 | 76.1 |
| log picture (Sonnet) | 68.7 | 84.8 |
| text | 72.1 | 83.2 |
| text (Haiku) | 71.7 | 81.5 |
| text (Sonnet) | 72.2 | 82.2 |

### T13. The set-aside first log-picture reading of 30/6-5, scored once after the freeze (that well only)

| log-picture reading of 30/6-5 | coverage_pct | tolerant_all_pct | tolerant_read_pct | strict_all_pct | soft_all_pct | balanced_all_pct |
|---|---|---|---|---|---|---|
| kept reading (corrected pictures, full re-read) | 100.0 | 76.3 | 76.3 | 66.4 | 96.5 | 52.4 |
| set aside: first cut | 93.0 | 70.6 | 75.9 | 61.2 | 88.8 | 40.5 |
| set aside: first cut down to 3150 m + patch below | 100.0 | 76.1 | 76.1 | 65.1 | 95.6 | 44.1 |

### T14. Cheaper readers against the main reader of the same kind, all three scores

| metric | kind_of_reading | model | main_pct | cheaper_pct | gap_points_cheaper_minus_main | wells_cheaper_ahead | wells_main_ahead | verdict |
|---|---|---|---|---|---|---|---|---|
| tolerant_all_pct | text | Sonnet 5.5 | 72.1 | 72.2 | 0.1 | 2 | 3 | not decided |
| strict_all_pct | text | Sonnet 5.5 | 68.4 | 68.3 | -0.1 | 1 | 3 | not decided |
| balanced_all_pct | text | Sonnet 5.5 | 38.2 | 36.0 | -2.2 | 2 | 3 | not decided |
| tolerant_all_pct | text | Haiku 5.5 | 72.1 | 71.7 | -0.4 | 1 | 2 | not decided |
| strict_all_pct | text | Haiku 5.5 | 68.4 | 67.9 | -0.5 | 1 | 2 | not decided |
| balanced_all_pct | text | Haiku 5.5 | 38.2 | 35.6 | -2.6 | 1 | 2 | not decided |
| tolerant_all_pct | log picture | Sonnet 5.5 | 74.4 | 68.7 | -5.7 | 0 | 4 | behind the main model |
| strict_all_pct | log picture | Sonnet 5.5 | 66.3 | 63.5 | -2.8 | 1 | 4 | not decided |
| balanced_all_pct | log picture | Sonnet 5.5 | 64.5 | 39.9 | -24.6 | 0 | 4 | behind the main model |
| tolerant_all_pct | log picture | Haiku 5.5 | 74.4 | 63.6 | -10.8 | 0 | 5 | behind the main model |
| strict_all_pct | log picture | Haiku 5.5 | 66.3 | 61.5 | -4.8 | 0 | 5 | not decided |
| balanced_all_pct | log picture | Haiku 5.5 | 64.5 | 39.0 | -25.5 | 1 | 4 | behind the main model |
| tolerant_all_pct | combined | Sonnet 5.5 | 75.4 | 70.7 | -4.7 | 0 | 4 | not decided |
| strict_all_pct | combined | Sonnet 5.5 | 66.1 | 63.9 | -2.2 | 1 | 3 | not decided |
| balanced_all_pct | combined | Sonnet 5.5 | 64.9 | 41.2 | -23.7 | 0 | 4 | behind the main model |
| tolerant_all_pct | combined | Haiku 5.5 | 75.4 | 65.7 | -9.7 | 0 | 5 | behind the main model |
| strict_all_pct | combined | Haiku 5.5 | 66.1 | 61.6 | -4.5 | 0 | 5 | not decided |
| balanced_all_pct | combined | Haiku 5.5 | 64.9 | 40.3 | -24.6 | 1 | 4 | behind the main model |
| tolerant_all_pct | curve picture | Sonnet 5.5 | 80.6 | 67.6 | -13.0 | 0 | 5 | behind the main model |
| strict_all_pct | curve picture | Sonnet 5.5 | 76.6 | 65.2 | -11.4 | 0 | 5 | behind the main model |
| balanced_all_pct | curve picture | Sonnet 5.5 | 71.0 | 51.3 | -19.7 | 1 | 4 | behind the main model |
| tolerant_all_pct | curve picture | Haiku 5.5 | 80.6 | 48.7 | -31.9 | 0 | 5 | behind the main model |
| strict_all_pct | curve picture | Haiku 5.5 | 76.6 | 46.6 | -30.0 | 0 | 5 | behind the main model |
| balanced_all_pct | curve picture | Haiku 5.5 | 71.0 | 28.3 | -42.7 | 0 | 5 | behind the main model |

### T15. Conflicts: teacher class of another family than the expert label, intervals of 3 m or more

| teacher_class | intervals | metres |
|---|---|---|
| Limestone | 1 | 3.3 |
| Marl | 2 | 10.8 |
| Shale | 7 | 52.8 |
| Tuff | 9 | 127.5 |
