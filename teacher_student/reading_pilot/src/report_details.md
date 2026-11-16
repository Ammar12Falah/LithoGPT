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
