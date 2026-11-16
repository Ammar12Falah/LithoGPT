# Notes of the reading pilot

Working notes, in the order things were done. Times are UTC on 15 November 2026.
Facts are marked as facts. My own judgments are marked "Judgment".

## Start

- 20:42 start. Remote confirmed: `Ammar12Falah/LithoGPT`. Earlier branch `claude/kind-mendel-aqkrot`
  merged into `claude/focused-hypatia-k9i62o` by fast-forward.
- Allowed hosts of the environment: factpages.sodir.no, raw.githubusercontent.com, the Kansas and
  NLOG hosts, the package index. No other host was used.

## A1. The draw

- `train.zip` holds one file, `train.csv`: 1 170 511 rows, 98 wells, 29 columns.
- Columns: WELL, DEPTH_MD, X_LOC, Y_LOC, Z_LOC, GROUP, FORMATION, CALI, RSHA, RMED, RDEP, RHOB, GR,
  SGR, NPHI, PEF, DTC, SP, BS, ROP, DTS, DCAL, DRHO, MUDWEIGHT, RMIC, ROPA, RXO,
  FORCE_2020_LITHOFACIES_LITHOLOGY, FORCE_2020_LITHOFACIES_CONFIDENCE.
- The starter notebook says the file has 83 wells. The file I downloaded has 98. I used the file.
- Rock classes (starter notebook): 30000 Sandstone, 65030 Sandstone/Shale, 65000 Shale, 80000 Marl,
  74000 Dolomite, 70000 Limestone, 70032 Chalk, 88000 Halite, 86000 Anhydrite, 99000 Tuff,
  90000 Coal, 93000 Basement.
- Confidence column (starter notebook): "confidence in lithology interpretation (1: high,
  2: medium, 3: low)". In the 93 wells that are not test wells: 966 328 rows with 1, 116 695 with 2,
  34 251 with 3, 53 237 empty.
- Every row of the 93 non-test wells has an expert label.
- Held-out check: none of the 20 held-out wells is in `train.csv`.
- Shuffle: the 98 well names sorted, then `numpy.random.default_rng(20261115).permutation`.
  The drawn order was committed (6ac79fd) before the documents table was opened.

### Documents table and name match

- Table: FactPages "wellbore_document", downloaded as CSV (10 569 rows, 1 994 wellbore names).
- Name match: exact match after upper-casing and removing spaces. 96 of 98 wells match.
  Two wells have no exact name in the table and were treated as having no documents:
  `16/11-1 ST3` (the table has "16/11-1 S") and `25/2-13 T4` (the table has "25/2-13").
- Document rule (fixed before any document was opened; `src/a1_roles.py`):
  completion log = document type "COMPOSITE LOG", or a name with COMPLETION_LOG, COMPOSITE_LOG,
  COMPOSITE_WELL_LOG, "..._REPORT_AND_LOG", or the old "WDSS_completion_log" sheet;
  report = a name with COMPLETION and REPORT, or FINAL_WELL_REPORT, END_OF_WELL_REPORT,
  FINAL_GEOLOGICAL_REPORT, GEOLOGICAL_REPORT.
- Fact found on opening the documents: the files of document type "COMPOSITE LOG" (made by the
  directorate) are plots of the curves with formation tops. They have no rock column. The old
  "WDSS completion log" sheets were downloaded but not used. The usable completion logs were all
  licensee documents. So my document rule counts some wells as "has a completion log" that have
  only a curve plot. This did not change the draw here: every test and practice well also has a
  licensee completion log. It matters for the Norway count in Part C.

### Roles

- Test wells (first 5 in the drawn order with both documents): 31/3-1, 30/6-5, 35/11-13, 35/11-11,
  25/6-2. Passed over: 36/7-3 (first in the drawn order; no report of the named kinds in the table).
- Example wells (next 10): 25/7-2, 17/11-1, 25/4-5, 16/5-3, 30/3-3, 16/1-2, 33/9-17, 32/2-1,
  34/12-1, 16/7-5. Practice wells: 25/7-2 and 25/4-5 (first two example wells with both documents).
- Curve wells: the next 23. Extra wells: the other 60. Pool = example + extra = 70 wells.
- No test well was replaced.

### Usability check of the documents (no extraction)

| well | completion log | report |
|---|---|---|
| 31/3-1 | 1:500 sheet with rock column, depth marks, written descriptions (report PDF p211) | lithology summaries, cuttings sample list, core and sidewall-core descriptions |
| 30/6-5 | 1:500 sheet with rock column and descriptions (report PDF p185); a mud log with a rock column is on p187 (not used) | lithology summaries, sample descriptions |
| 35/11-13 | 1:500 colour sheet from 2005, rock column and descriptions | lithology by depth interval, core descriptions |
| 35/11-11 | 1:500 sheet, rock column against depth with descriptions; black-and-white scan of a colour sheet, the fill of the column is partly lost | lithology by formation with depths |
| 25/6-2 | 1:500 composite well log with rock column and descriptions (report PDF p115) | sidewall-core descriptions by depth, lithostratigraphic summary; no cuttings sample list |
| 25/7-2 (practice) | composite well log with rock column (report PDF p263) | formation summaries, sidewall cores, cores |
| 25/4-5 (practice) | composite log 1:500 with rock column | lithology by interval, cores, sidewall cores |

Judgment: I kept 35/11-11 and 25/6-2 although their documents are weaker (lost fill; no cuttings
list). Both meet the test in the brief: a rock column against depth, and a report that describes
rock by depth. Dropping weak documents would have made the teacher look better than it is.

### Split

`src/a1_split.py` wrote three files and printed no rows: logs of all wells without the two label
columns; labels of the 93 non-test wells; labels of the 5 test wells (`labels_test_SEALED.parquet`,
53 071 rows). The last file was not opened before the freeze.

Depth range of the test wells in `train.csv` (from the logs file):
31/3-1 350 to 2362 m; 30/6-5 257 to 3548 m; 35/11-13 2902 to 3271 m; 35/11-11 1245 to 3215 m;
25/6-2 1925 to 2369 m. Depth step 0.152 m.

## Reuse terms of the sources

- FactPages (factpages.sodir.no, home page, read 15 November 2026): "The content on the FactPages
  may be used in accordance with Norwegian Licence for Open Government Data (NLOD). In this context
  we emphasize that there may be limitations with respect to the use of information subject to
  third party rights, such as reports, core images and logs etc."
  So the listing table is clearly reusable. For reports and logs the terms are not clear.
  Page pictures and log pictures are kept out of git. Short source sentences with their page and
  address are in the reading files.
- FORCE files: `train.zip`, `penalty_matrix.npy` and `starter_notebook.ipynb` say nothing about a
  licence. The rules of this pilot did not let me open other files of that repository, so I could
  not read its licence text. Terms unclear from what I was allowed to read. So no table with
  expert labels, no picture drawn from the logs, and no conflict sheet with expert labels is in git.
  (From memory, not checked here: the FORCE 2020 data are said to be under NLOD 2.0 for the logs
  and CC-BY-4.0 for the labels. If Ammar confirms this, these files can be committed later.)

## A2. Plain model: the setup check inside the 60 extra wells

- Three folds of extra wells (40 train, 20 check), `src/a2_search.py`. Trained on every 4th depth
  step, checked on every 3rd. Strict agreement, mean of the three folds:

| features | trees | 100 rounds | 200 | 400 | 600 |
|---|---|---|---|---|---|
| S0: curves, depth, position, group, formation (no windows) | 63 leaves, lr 0.1 | 72.6 | 72.4 | 72.1 | 72.0 |
| S0 | 31 leaves, lr 0.05, strong smoothing (B) | 74.3 | 73.5 | 72.9 | 72.7 |
| S0 | 15 leaves (C) | 73.3 | 73.6 | 73.3 | 73.0 |
| S0 | 31 leaves, extra-random splits (D) | 73.2 | 73.1 | 72.8 | 72.1 |
| S1: + 10 curves shifted 0.5, 1, 2, 5 m up and down | A | 72.2 | 72.2 | 72.2 | 72.1 |
| S1 | B | 72.4 | 72.4 | 72.3 | 72.1 |
| S1 | C | 72.0 | 72.2 | 72.1 | 71.9 |
| S1 | D | 71.6 | 71.4 | 71.3 | 71.2 |
| S1b: + 5 curves shifted 1 and 3 m | B | 72.7 | 72.6 | 72.6 | 72.5 |
| S1b | C | 72.9 | 72.9 | 72.5 | 72.5 |
| S2: S1 + rolling mean and spread over about 10 m + gamma ray normalised by well | B | **74.2** | 74.0 | 73.7 | 73.6 |
| S2 | C | 73.9 | 73.9 | 73.6 | 73.4 |

- Fixed setup: features S2, trees B (31 leaves, learning rate 0.05, at least 300 rows per leaf,
  40 percent of the features per tree, 70 percent of the rows per round, L2 5, smoothing of the
  category splits), 100 rounds, trained on every 2nd depth step. No class weights.
- Facts: all candidates lie between 71 and 74 percent. More rounds never helped. The plain shifted
  curves alone (S1) were a little worse than no windows; with rolling means and the well-normalised
  gamma ray (S2) the window model equals the best no-window model (74.2 against 74.3).
- Judgment: the brief asks for window features, so I took the best setup that has them. It is as
  strong as the best setup without them in this check.

## A3. Curve pictures: the method trial on example wells (21:07 to 21:36)

- Hidden example wells (drawn with seed + 2): 17/11-1, 25/4-5, 16/1-2. To stay inside the one-hour
  cap, each was read on one section drawn with the seed: 17/11-1 1800 to 2800 m, 25/4-5 3300 to
  4300 m, 16/1-2 2700 to 2900 m (its whole range). Readers saw labelled pictures of the other
  7 example wells: 20 pictures of 100 m, or 30 pictures of 50 m.
- Rule written down before the trial was scored: take 100 m unless 50 m is at least 3 points
  better in pooled tolerant agreement; take the second version of the instructions only if it is
  at least 1 point better.

| pictures | instructions | 17/11-1 | 25/4-5 | 16/1-2 | pooled tolerant | pooled strict | pooled soft |
|---|---|---|---|---|---|---|---|
| 100 m | first | 80.9 | 78.0 | 74.0 | 78.9 | 74.2 | 94.0 |
| 50 m | first | 81.1 | 77.5 | 72.5 | 78.6 | 74.3 | 93.6 |
| 100 m | second | 80.6 | 77.9 | 71.6 | 78.5 | 73.2 | 93.6 |

  All-shale line on the same sections: 60.7, 37.4, 19.1 percent.
- Cost of one trial reader: 100 m pictures 5 to 13 minutes, 50 m pictures 8 to 17 minutes.
- Chosen: 100 m pictures, first version of the instructions, 20 example pictures.
- The readers' remarks: the examples of the trial held no Zechstein or Rotliegend sections (the
  final example set, from all 10 example wells, does). Sandstone/Shale is under-called: the readers
  wrote Shale for most depth that the experts call Sandstone/Shale. The second version of the
  instructions tried to mend this and did not.
- One reader said the group and formation text looked carried over. Checked: the picture shows what
  `train.csv` holds (for example "ZECHSTEIN GP." with formation "Smith Bank Fm." in 17/11-1).

## B1. Practice on the two practice wells (21:13 to 21:52)

- Log picture: a 1200 m section of each well, drawn with seed + 3 (25/7-2 1400 to 2600 m; 25/4-5
  1700 to 2900 m). Text: the whole depth range of the training file.
- Two rounds, each with fresh readers. Round 1 used the first draft of the word map (siltstone to
  Sandstone/Shale). Round 2 used the final instructions.

Tolerant agreement on the two practice sections (percent):

| reading | 25/7-2 | 25/4-5 | pooled |
|---|---|---|---|
| all-shale line | 70.5 | 32.0 | 51.2 |
| round 1 text | 78.5 | 45.1 | 61.8 |
| round 1 log picture | 69.6 | 61.0 | 65.3 |
| round 2 text | 83.0 | 52.3 | 67.6 |
| round 2 log picture | 82.5 | 66.3 | 74.4 |
| round 2 combined (the fixed rule) | 84.2 | 67.3 | 75.8 |

Text reading over the whole range of the well: round 1 68.0 and 54.6; round 2 65.2 and 56.8
(all-shale 53.2 and 38.8).

What the practice changed:
1. Siltstone goes to Shale (second class Sandstone/Shale). Round 1 sent it to Sandstone/Shale.
2. Claystone or siltstone called tuffaceous, or drawn with tuff marks all through, goes to Tuff.
3. Overlap rule: low-confidence rows count only where no better row gives a class.
4. Text reader: rows only from the places where geologists describe rock, not from drilling, mud,
   pressure or test chapters, and not from table labels. A new column `kind`.
5. The legend of the sheet must be complete in the header picture (it was cut off for 25/4-5 in
   round 1).
6. Text reader: a depth that looks like a misprint is left empty, not corrected (a round 2 reader
   had corrected four printed depths from context).

Caution (fact): rounds 1 and 2 were scored on the same two wells on which the changes were made.
The round 2 numbers are therefore too rosy as a forecast for the test wells.

Reading confidence is informative (round 1 log pictures): rows marked high were right far more
often (strict 71 to 79 percent) than rows marked low (19 to 48 percent).

Forecast against found depth (not extracted, as told): 25/7-2 report PDF p12 (Fig. 1.3.1 Well Data
Summary); 25/4-5 completion report p52.

Cost of one practice reader: log picture (1200 m) 5 to 11 minutes; text (whole well) 9 to 18 minutes.

## B2. A fault in my picture cutting, found while well 2 was being read (22:45 to 23:05)

- Fact: the long scanned sheets are not straight. The sheet of 30/6-5 wanders sideways by up to
  21 mm and the sheet of 35/11-11 by up to 51 mm over its length. My first cut used fixed columns,
  measured at one place in the middle of each sheet.
- Fact: the first log-picture reader of 30/6-5 reported that the rock column was cut off in the
  pictures below about 3150 m, and it left 3316 to 3548 m without a class. A check with thin
  slices of the sheet (`src/drift_check.py`) showed the column was also clipped by 1 to 4 mm of its
  12 mm width in the top 700 m.
- What I did, before any expert label of a test well was opened:
  1. Added a sideways shift by depth to the cutting (`x_shift` in `src/log_tiles.json`), measured on
     the thin slices, and cut the sheets of 30/6-5 and 35/11-11 again. Spot checks of the new
     pictures show the rock column and its depth numbers inside every sampled picture.
  2. Set the first log-picture reading of 30/6-5 aside (kept in `work/`, not used) and had a fresh
     reader read the whole well again from the new pictures. A second fresh reader had already
     been started on a patch of the lower part only (3150 to 3548 m); that patch is also set aside.
  3. 35/11-11 had not been read yet. It is read once, from the new pictures.
  4. Checked the other sheets the same way: 31/3-1 wanders by 8 mm and its column stays inside the
     cut (first reading kept); 25/6-2 does not wander; 35/11-13 is a drawn PDF, not a scan.
- Judgment: this is a repair of my tool, not a second try at a reading. No label had been seen, so
  the choice could not be steered by results. The set-aside reading is scored after the freeze and
  shown next to the kept one, so that the size of the effect is in the open.

## The readings of the five test wells (15 November, 22:01 to 23:45)

- Each reading was done by a subagent with a fresh memory. Its task message named only its
  instruction file, the folder it may open, the depth range (document readers) and the output path.
- Wells were read in the drawn order, one after the other: 31/3-1, 30/6-5, 35/11-13, 35/11-11, 25/6-2.
- Text readers were allowed to write their file in parts (wells 1 and 2 have 728 and 826 rows).
- Rows without a usable depth (printed depths that look like misprints were left empty, as the
  instructions say): 31/3-1 text 8 cells, 30/6-5 text 6, 35/11-13 text 1, 25/6-2 text 2.
- 31/3-1 log picture: 349 to 420 m has no class (no rock column drawn above 358 m; "NO RETURN" to 420 m).
- 35/11-11 log picture: the claystone fill cannot be seen on this black-and-white scan. The reader
  took Shale from the written descriptions next to the column there and said so in every such row.
- Tables of forecast depth against found depth (noted, not extracted): 35/11-13 completion report
  p60 (site survey horizons); 35/11-11 completion report p36; 25/6-2 final well report p23
  (Figure 4.5). The readers found none for 31/3-1 and 30/6-5.
- Costs are in `readings/costs.csv`.

## Pause

- 15 November 23:45: I ended my turn to wait for the completion notice of the last reader. The
  session then sat idle. The container was suspended and started again on 16 November at 06:27,
  with all working files still on disk. Nothing was rebuilt. Idle time is not counted as work time.

## Part D. Cheaper readers (16 November, 06:29 to 06:55)

- The subagent tool has a model option. I set it to "sonnet" and to "haiku". The tool does not
  report back the exact model version that served a reader. This environment names the newest
  models of those two lines as Claude Sonnet 5.5 and Claude Haiku 5.5. I could not check the served
  version myself.
- Everything else was the same as for the main readings: the same picture files and pages (nothing
  was rebuilt), the same instruction files, the same 20 example pictures, the same task messages
  (only the output path differs), a fresh memory for each reading. For 30/6-5 the log pictures are
  the corrected ones that the kept main reading used. No tuning and no practice for these models.
- Before the cheaper readers started, I moved the main readers' output files out of the picture
  folders, so that no cheaper reader could come across them.
- All 30 readings (5 wells x 3 kinds x 2 models) were done. They ran several at a time; the tool
  allows at most 20 readers at once, so the two text readings of well 5 started a few minutes later.
- I could not find out whether the cheaper models see the pictures at lower detail. They were given
  the same files.
- Three cheaper readers broke the tool rules once each. None of it touched data or readings:
  Haiku, log picture of 25/6-2, tried to archive its own session (denied, nothing happened);
  Sonnet, log picture of 30/6-5, made one shell call "echo" (denied);
  Haiku, text of 31/3-1, ran one shell command to make its output folder.
- The cheaper readers wrote far fewer rows for the pictures (for example 54 and 45 rows for the
  log picture of 31/3-1, against 291 by the main reader) and were about five to ten times faster.
- Costs are in `readings/costs_partd.csv`. Their combined readings were built with the same rule.
