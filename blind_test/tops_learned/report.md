# Tops learned test: report

Brief 2 of 13 November 2026: can a learned model beat mapping on layer depths?
Work done on 13 November 2026 in one Claude Code session, the same session that made the first run.
Branch: `claude/kind-mendel-aqkrot`. Folder: `blind_test/tops_learned/`. Nothing in `blind_test/tops_headroom/` was changed.

The question: on wells far from earlier wells, can a quick learned model beat the best simple method, after a fair correction for drift?

## First screen

### Pass or fail

The pass mark: on the far items of the scoring half, the learned model C must have a median absolute error at least 10 % below the best simple method, and the 95 % interval of that improvement must lie above zero.

| Country | Far items | Best simple method | Learned model C | Improvement | Verdict |
|---|---|---|---|---|---|
| **Kansas** | 5,700 items in 2,162 wells | Side method 4b: 3.87 m | 3.60 m | 7.1 % (95 % interval 3.9 to 9.5) | **FAIL.** The gain is real but under 10 %. |
| **Netherlands** | 938 items in 194 wells | Side method 4b: 109.4 m | 101.2 m | 7.5 % (95 % interval -5.7 to 21.9) | **FAIL.** Under 10 %, and the interval includes zero. |

How much of the gain the drift-only model D already gets: almost none. On far items D improves on the best simple method by 0.1 % in Kansas (interval -3.4 to 2.7) and by 0.4 % in the Netherlands (interval -13.1 to 18.5). That is 2 % and 5 % of C's gain.

"Far" means the nearest known well with that layer is more than 1 km away. The scoring half was scored once, with models frozen in commit `c7b367c6622aec5959c8c7dd20c0b33f2ea3c1df`.

### Three main findings

1. **Kansas: the learned model beats every simple method, but not by enough.** On far items it is 7.1 % better than the best simple method and 10.0 % better than kriging (interval 7.2 to 12.8). With shuffled targets the gain is gone (-3.0 %), so it is not an artefact. In metres it is small: 0.28 m on a miss of 3.87 m.
2. **The gain is not drift.** The drift-only model, which sees no depth value, gains nothing over the best simple method in either country. Drift-corrected kriging is not the best simple method in either country. The correction removes most of the bias (Kansas far items: from -1.03 m to -0.42 m; C reaches -0.10 m) but hardly moves the median miss. What helps C is depth information: in Kansas three quarters of the model's split gain sits in depth features, led by the routes through other layers.
3. **The Netherlands cannot be told apart from no gain.** The point estimate is like Kansas (7.5 %) but the interval runs from -5.7 % to +21.9 %. In Kansas the gain is larger near known wells (10.7 % at 30 m to 1 km) than far from them (6.4 % at 1 to 5 km, nothing measurable beyond 5 km). So the learned model does not help most where mapping is weakest.

### Three main doubts

1. **The Dutch result is mostly noise.** 938 far items in 194 wells. Two side models whose training sets differ by 129 of 11,307 items score 102.0 m and 109.9 m. The Dutch fail means "not shown", not "shown to be absent".
2. **This was a quick model.** One model family, a dozen settings tried per country (7 for C, 5 for D), features fixed beforehand, all built in under two hours. A more careful model might pass in Kansas, where the miss is 3 points (7.1 % against 10 %) and the top of the interval is 9.5 %. I cannot say from this run.
3. **The doubts of the first run still stand**, because the data are the same: picks in Kansas are named and made unevenly, Dutch picks may have been revised with later wells in view, and Dutch tops are forecast where the well actually crossed them. One new one: as the brief allows, the model trains on the whole tuning half, whose newest wells were not yet "known" for the first scoring wells. A side model without them scores the same (Kansas 3.57 m, Netherlands 102.0 m), so this did not drive the result.

---

## Details

Facts come first in each section. My own reading is marked **Judgment**.

### 1. Data and what was loaded

- Only the four cleaned input tables of the first run were read (`blind_test/tops_headroom/data/`). Nothing was downloaded. No FORCE 2020 file, no Norwegian data.
- The first run's code is imported, not copied and not changed: its loaders, its date rule, its four methods and side method 4b, and its settings (`results/<country>_settings.json` of the first run).
- **Sealed wells.** The first run's loaders read every row and dropped sealed depths afterwards. That is not allowed here. So this run reads the tables through a guard (`src/safe_load.py`): the depth columns of blocked rows are skipped while the file is read and are never parsed. Blocked are all rows of sealed wells, of their sidetracks and of their duplicate records, and, to be safe, every record dated on or after the start of the sealed period. Such records can never be a known well for a development well, so nothing usable is lost.
- **Scoring half.** During training the same guard also blocks every record dated on or after the start of the scoring half. The training stage cannot see a depth of the scoring half.
- The guard proves itself on every load: no sealed well, no sidetrack of one and (in training) no scoring-half well has a value in memory.
- Kansas depth columns guarded: top depth, and total depth of the well. Netherlands: depth along hole of top and base, true vertical depth of the top, and the position of the top (in a deviated hole it follows from the depth).

### 2. Split of the development period

Set from dates only, from the first run's split files, before any model was fitted. Committed first, in commit `01433f2`.

| Country | Development wells | Date between the halves | Tuning half | Scoring half |
|---|---|---|---|---|
| Kansas | 13,435 | 12 April 2006 | 6,716 wells, 3 Jan 2000 to 11 Apr 2006 | 6,719 wells, 12 Apr 2006 to 14 Jul 2010 |
| Netherlands | 535 | 2 September 1994 | 267 wells, 16 Jan 1990 to 13 Aug 1994 | 268 wells, 2 Sep 1994 to 27 Mar 2001 |

Files: `results/kansas_dev_split.csv`, `results/netherlands_dev_split.csv`, `results/dev_split_dates.txt`. The date is the one the first run ordered by: spud date in Kansas, end of drilling in the Netherlands.

### 3. Training targets

- **From before the test years.** Kansas: wells spudded 1970 to 1999. Netherlands: mother boreholes finished 1950 to 1989. Each is forecast at its own date, only from wells known then under the first run's date rule (finished at least 12 months before the spud date in Kansas, at least 5 years before the start of drilling in the Netherlands).
- **Plus the tuning half**, forecast the same way.
- Every choice was made by fitting on the targets from before the test years and looking at the tuning half. The final models were then fitted on both together with those choices.
- The start years 1970 and 1950 were set by me beforehand and not tuned.

### 4. What is compared

One test item is one chosen layer in one well of the scoring half. The 12 chosen layers per country are those of the first run.

**A. The four simple methods and side method 4b of the first run**, with the first run's settings: nearest known well, local plane, kriging with a local trend, thickness method, and the best-route variant 4b.

**B. Drift-corrected kriging.** Kriging plus one number per layer and distance band: the median of (actual minus kriging) over training targets. A cell with fewer than 30 targets uses the layer's median. Which years of targets to use was chosen on the tuning half among: all, the last 20, the last 10, the last 5 years. The final table uses that many years up to the start of the scoring half, so it includes the tuning half. Table: `results/<country>_drift_table.csv`.

**C. The learned model.** Gradient-boosted trees (LightGBM) that forecast the miss of kriging, actual minus kriging. The forecast is kriging plus the predicted miss. One model per country, all layers together, with the layer as a feature. Loss: absolute error. 160 features, listed with their group in `results/features.csv`:

- position: x and y of the forecast point, and the layer (3);
- dates: date of the test well, and how long before it each of the 8 nearest known wells was finished (12);
- distances: to the 8 nearest known wells with the layer, to the nearest known well with each other layer, to the nearest well that has both layers (34);
- counts: known wells within 0.5, 1, 2, 5, 10 and 20 km, and wells with both layers within 10 km (19);
- directions: east and north offset of the 8 nearest known wells, how one-sided they are (19);
- depth values (73): the outputs of the simple methods relative to kriging, the kriging spread, the values of the 8 nearest known wells relative to kriging, the local dip, the kriged elevation of each other chosen layer at the same spot, and "routes": kriging of another layer plus or minus a kriged thickness to the target layer, from above and from below.

No feature uses a pick of the test well, for any layer. Features for other layers are forecasts from known wells at the test well's position, not the test well's own values.

**D. The drift-only model.** The same trees, but only the 68 features of the groups position, dates, distances and counts. It sees no depth value and no output of a simple method. Its forecast is kriging plus its predicted miss.

**80 % range of C.** Two more tree models forecast the 10th and 90th percentile of the miss. One number, set on the tuning half, widens or narrows the range so that it held 80 % there.

**Choices made on the tuning half** (yardstick: median absolute error on its far items): whether the target is divided by the kriging spread (C only), whether far items weigh three times as much, tree size (four settings), and the number of trees. Every fit and its score is in `results/<country>_tuning_search.csv`; the choices are in `results/<country>_settings_learned.json` and in the tables below.

**Side models, not in the pass mark.**
- C trained on shuffled targets (the shuffle test).
- C trained only on targets from before the test years.
- C trained only on targets whose actual value was already known, under the date rule, before the first well of the scoring half was started. The brief lets the model train on the whole tuning half. But the newest tuning wells were not yet "known wells" for the first scoring wells. Because the model sees the position, it could carry their depths into forecasts nearby. This side model shows whether that matters.

### 5. Results

Scoring half, scored once. Kansas: 6,719 wells, 30,103 items. Netherlands: 268 wells, 1,323 items. Every well of the scoring half has at least one item.

**Kansas**

![Kansas: kriging, drift-corrected kriging and the learned model](results/kansas_learned_vs_kriging.png)

### Kansas: error by distance on the scoring half

Median absolute error in metres. In brackets: the mean absolute error.

| Distance to nearest known well with the layer | Items | Wells | A1 nearest | A2 plane | A3 kriging | A4 thickness | A side 4b | B drift-corrected kriging | C learned | D drift-only |
|---|---|---|---|---|---|---|---|---|---|---|
| all items | 30,103 | 6,719 | 2.74 (8.91) | 2.84 (8.21) | 2.39 (6.59) | 3.01 (10.99) | 2.33 (6.54) | 2.24 (6.48) | 2.11 (6.18) | 2.19 (6.44) |
| far (>1 km) | 5,700 | 2,162 | 5.49 (13.71) | 4.63 (11.79) | 4.00 (9.87) | 4.98 (15.00) | 3.87 (9.59) | 3.97 (9.83) | 3.60 (9.17) | 3.87 (9.78) |
| same site (<30 m) | 115 | 38 | 1.22 (3.39) | 2.75 (4.00) | 1.72 (2.94) | 2.13 (6.23) | 1.49 (2.99) | 1.61 (2.90) | 1.51 (2.65) | 1.54 (2.75) |
| 30 m-1 km | 24,288 | 5,701 | 2.44 (7.81) | 2.54 (7.39) | 2.15 (5.84) | 2.71 (10.07) | 2.10 (5.84) | 2.00 (5.71) | 1.88 (5.49) | 1.94 (5.67) |
| 1-5 km | 5,531 | 2,090 | 5.18 (12.54) | 4.55 (11.21) | 3.91 (9.34) | 4.87 (14.60) | 3.76 (9.06) | 3.87 (9.31) | 3.52 (8.68) | 3.78 (9.25) |
| 5-20 km | 166 | 128 | 22.71 (52.67) | 14.66 (27.97) | 11.53 (27.09) | 12.58 (28.09) | 10.68 (26.67) | 12.15 (26.97) | 11.38 (25.55) | 11.76 (27.11) |
| >20 km | 3 | 3 | 20.73 (20.22) | 37.57 (175.06) | 24.42 (26.61) | 24.42 (26.61) | 24.42 (26.61) | 24.08 (26.35) | 20.47 (18.75) | 24.22 (26.26) |

95 % interval of the median absolute error (resampling whole wells), far items and all items.

| Items | A1 nearest | A2 plane | A3 kriging | A4 thickness | A side 4b | B drift-corrected kriging | C learned | D drift-only |
|---|---|---|---|---|---|---|---|---|
| far (>1 km) | 5.18-5.79 | 4.40-4.87 | 3.83-4.20 | 4.70-5.28 | 3.69-4.04 | 3.82-4.15 | 3.44-3.78 | 3.69-4.08 |
| all items | 2.74-2.74 | 2.77-2.90 | 2.34-2.44 | 2.93-3.08 | 2.28-2.38 | 2.20-2.29 | 2.05-2.15 | 2.15-2.24 |

Median signed error in metres (forecast minus actual).

| Distance band | A1 nearest | A2 plane | A3 kriging | A4 thickness | A side 4b | B drift-corrected kriging | C learned | D drift-only |
|---|---|---|---|---|---|---|---|---|
| all items | -0.61 | -0.95 | -0.90 | -0.97 | -0.87 | -0.15 | -0.13 | -0.11 |
| far (>1 km) | -0.91 | -0.74 | -1.03 | -0.97 | -1.00 | -0.42 | -0.10 | -0.38 |
| same site (<30 m) | -0.30 | -1.84 | -0.68 | -0.94 | -0.66 | -0.57 | -0.15 | -0.06 |
| 30 m-1 km | -0.61 | -0.98 | -0.89 | -0.97 | -0.86 | -0.11 | -0.14 | -0.07 |
| 1-5 km | -0.91 | -0.73 | -1.04 | -0.96 | -0.99 | -0.42 | -0.07 | -0.38 |
| 5-20 km | -3.05 | -0.82 | 0.52 | -1.14 | -1.06 | 0.01 | -2.94 | -0.22 |
| >20 km | 20.73 | -37.57 | -24.42 | -24.42 | -24.42 | -24.08 | -20.47 | -24.22 |

### Kansas: the learned model C against each other method, same items

Relative improvement in median absolute error (positive: C is better), with the 95 % interval from resampling whole wells.

| C against | far (>1 km) | all items | same site (<30 m) | 30 m-1 km | 1-5 km | 5-20 km | >20 km |
|---|---|---|---|---|---|---|---|
| A1 nearest | 34.4 % (29.9 to 37.5) | 23.2 % (21.5 to 25.1) | -23.5 % (-47.2 to 16.4) | 23.0 % (21.0 to 24.8) | 32.0 % (28.9 to 37.2) | 49.9 % (32.9 to 65.2) | 1.2 % (-25.7 to 25.4) |
| A2 plane | 22.3 % (18.9 to 25.1) | 25.7 % (24.3 to 27.3) | 45.2 % (23.1 to 60.4) | 26.2 % (24.6 to 27.9) | 22.5 % (18.8 to 25.3) | 22.3 % (-1.9 to 44.8) | 45.5 % (45.5 to 94.4) |
| A3 kriging | 10.0 % (7.2 to 12.8) | 11.9 % (10.7 to 13.3) | 12.6 % (-21.7 to 28.0) | 12.9 % (11.4 to 14.3) | 9.9 % (7.1 to 12.8) | 1.2 % (-25.5 to 28.8) | 16.2 % (16.2 to 46.4) |
| A4 thickness | 27.7 % (24.3 to 31.0) | 30.0 % (28.5 to 31.7) | 29.2 % (-11.5 to 47.3) | 30.8 % (29.0 to 32.2) | 27.7 % (24.4 to 31.2) | 9.5 % (-18.2 to 35.9) | 16.2 % (16.2 to 46.4) |
| A side 4b | 7.1 % (3.9 to 9.5) | 9.5 % (8.3 to 11.1) | -1.1 % (-25.3 to 20.6) | 10.7 % (9.1 to 12.2) | 6.4 % (3.4 to 9.4) | -6.6 % (-39.0 to 23.4) | 16.2 % (16.2 to 46.4) |
| B drift-corrected kriging | 9.4 % (6.8 to 11.9) | 6.1 % (5.1 to 7.3) | 6.6 % (-12.9 to 25.3) | 6.0 % (4.8 to 7.3) | 9.0 % (6.7 to 11.8) | 6.3 % (-20.2 to 33.3) | 15.0 % (15.0 to 46.0) |
| D drift-only | 7.0 % (4.2 to 9.9) | 3.9 % (2.8 to 5.2) | 2.2 % (-19.2 to 20.3) | 3.4 % (2.0 to 4.8) | 6.7 % (4.2 to 9.7) | 3.2 % (-22.4 to 30.1) | 15.5 % (15.5 to 43.0) |

The other models against the best simple method and against kriging, far items.

| Model | Far median abs error, m | against best simple (A side 4b) | against kriging |
|---|---|---|---|
| C learned | 3.60 | 7.1 % (3.9 to 9.5) | 10.0 % (7.2 to 12.8) |
| D drift-only | 3.87 | 0.1 % (-3.4 to 2.7) | 3.2 % (0.9 to 5.0) |
| C on shuffled targets | 3.99 | -3.0 % (-6.2 to -0.2) | 0.2 % (-1.2 to 1.9) |
| C, targets known before scoring half | 3.57 | 7.8 % (4.6 to 10.2) | 10.7 % (8.1 to 13.4) |
| C, targets before test years | 3.64 | 6.1 % (3.4 to 8.8) | 9.0 % (6.7 to 11.9) |

### Kansas: by layer, scoring half

Median absolute error in metres (mean in brackets). In a well each layer is one item, so items and wells are the same number.

| Layer (shallow to deep) | Items | n | A1 nearest | A2 plane | A3 kriging | A4 thickness | A side 4b | B drift-corrected kriging | C learned | D drift-only |
|---|---|---|---|---|---|---|---|---|---|---|
| Stone Corral Formation | all items | 3,492 | 1.83 (8.24) | 1.98 (8.20) | 1.62 (5.89) | 1.62 (5.89) | 1.62 (5.89) | 1.52 (5.87) | 1.47 (5.63) | 1.54 (5.87) |
| Stone Corral Formation | far (>1 km) | 484 | 3.35 (11.61) | 3.33 (12.67) | 2.73 (9.81) | 2.73 (9.81) | 2.73 (9.81) | 2.71 (9.81) | 2.66 (9.32) | 2.72 (9.78) |
| Topeka Limestone Formation | all items | 2,678 | 3.05 (11.94) | 3.47 (11.22) | 2.69 (8.63) | 2.97 (9.58) | 2.64 (8.38) | 2.62 (8.62) | 2.35 (7.90) | 2.63 (8.62) |
| Topeka Limestone Formation | far (>1 km) | 533 | 4.88 (18.72) | 5.80 (18.50) | 4.71 (14.13) | 4.60 (14.91) | 4.36 (13.47) | 4.78 (14.08) | 3.91 (12.62) | 4.80 (14.08) |
| Heebner Shale Member | all items | 5,522 | 2.13 (8.16) | 2.15 (7.22) | 1.82 (5.77) | 2.38 (10.22) | 1.80 (5.72) | 1.69 (5.67) | 1.62 (5.55) | 1.61 (5.61) |
| Heebner Shale Member | far (>1 km) | 818 | 3.96 (12.80) | 3.16 (10.39) | 2.85 (9.28) | 3.67 (12.03) | 2.83 (9.24) | 2.75 (9.23) | 2.67 (9.02) | 2.75 (9.18) |
| Toronto Limestone Member | all items | 2,445 | 2.13 (7.77) | 2.32 (6.05) | 1.95 (4.54) | 2.38 (8.64) | 1.87 (4.36) | 1.73 (4.40) | 1.59 (4.11) | 1.71 (4.35) |
| Toronto Limestone Member | far (>1 km) | 492 | 4.57 (11.44) | 3.45 (8.19) | 2.72 (6.36) | 3.61 (15.40) | 2.44 (5.91) | 2.75 (6.37) | 2.29 (5.75) | 2.68 (6.32) |
| Lansing Group | all items | 5,560 | 2.44 (7.28) | 2.40 (6.89) | 2.06 (5.76) | 2.67 (9.81) | 1.99 (5.69) | 1.89 (5.60) | 1.82 (5.46) | 1.83 (5.56) |
| Lansing Group | far (>1 km) | 785 | 4.27 (10.13) | 3.65 (8.95) | 3.22 (8.45) | 3.84 (11.40) | 3.29 (8.44) | 3.11 (8.31) | 2.94 (8.07) | 3.11 (8.31) |
| Kansas City Group | all items | 511 | 4.27 (20.84) | 7.61 (20.79) | 4.49 (15.19) | 13.63 (31.19) | 4.70 (18.89) | 4.38 (15.15) | 5.07 (15.73) | 4.49 (15.18) |
| Kansas City Group | far (>1 km) | 160 | 8.84 (29.89) | 12.91 (30.52) | 10.68 (23.94) | 15.49 (30.07) | 10.29 (24.14) | 10.57 (23.94) | 11.73 (23.53) | 11.17 (24.10) |
| Marmaton Group | all items | 1,703 | 4.11 (8.89) | 4.01 (8.51) | 3.65 (7.27) | 4.33 (10.22) | 3.39 (6.70) | 3.35 (7.15) | 3.18 (6.50) | 3.44 (7.16) |
| Marmaton Group | far (>1 km) | 597 | 6.40 (12.46) | 5.30 (11.58) | 4.84 (9.37) | 5.67 (15.09) | 4.19 (8.53) | 4.82 (9.20) | 4.34 (8.22) | 4.79 (9.29) |
| Fort Scott Limestone Formation | all items | 1,460 | 3.66 (7.95) | 3.63 (7.70) | 3.21 (6.63) | 3.59 (7.79) | 3.12 (6.42) | 3.11 (6.59) | 2.75 (6.05) | 2.98 (6.54) |
| Fort Scott Limestone Formation | far (>1 km) | 375 | 7.01 (11.55) | 5.66 (10.30) | 5.61 (9.23) | 6.10 (11.55) | 5.09 (8.67) | 5.78 (9.24) | 4.72 (8.09) | 5.36 (9.25) |
| Cherokee Group | all items | 1,463 | 4.27 (10.76) | 3.76 (8.51) | 3.40 (7.30) | 4.59 (16.65) | 3.25 (7.03) | 3.37 (7.28) | 3.05 (6.80) | 3.35 (7.27) |
| Cherokee Group | far (>1 km) | 442 | 7.01 (16.66) | 5.28 (9.41) | 4.57 (8.60) | 6.41 (18.66) | 4.64 (8.28) | 4.58 (8.52) | 4.19 (7.99) | 4.54 (8.56) |
| Mississippian System | all items | 2,732 | 4.57 (8.90) | 4.33 (7.71) | 3.89 (6.72) | 6.32 (15.76) | 3.83 (6.73) | 3.78 (6.73) | 3.52 (6.44) | 3.62 (6.60) |
| Mississippian System | far (>1 km) | 635 | 7.62 (12.68) | 7.11 (10.60) | 5.90 (8.75) | 7.38 (13.40) | 5.56 (8.42) | 6.41 (9.00) | 5.13 (8.24) | 5.63 (8.63) |
| Simpson Group | all items | 369 | 4.57 (8.83) | 4.24 (9.41) | 3.31 (6.05) | 15.01 (37.89) | 3.40 (6.76) | 3.41 (6.07) | 3.12 (5.61) | 3.14 (5.95) |
| Simpson Group | far (>1 km) | 117 | 7.92 (15.09) | 5.35 (12.02) | 4.20 (8.80) | 32.65 (46.76) | 4.20 (10.75) | 4.75 (8.99) | 4.41 (8.29) | 4.07 (8.81) |
| Arbuckle Group | all items | 2,168 | 4.57 (10.29) | 5.11 (10.17) | 4.40 (8.60) | 5.04 (12.19) | 4.03 (8.43) | 3.58 (8.00) | 3.40 (7.59) | 3.64 (8.00) |
| Arbuckle Group | far (>1 km) | 262 | 10.06 (18.25) | 7.65 (14.04) | 6.96 (12.71) | 10.11 (23.07) | 6.64 (12.04) | 6.81 (12.41) | 6.29 (11.75) | 6.42 (12.33) |

### Kansas: how often the actual value is inside the 80 % range

| Distance band | Items | Wells | Learned model C | Kriging | Median width C, m | Median width kriging, m |
|---|---|---|---|---|---|---|
| all items | 30,103 | 6,719 | 82.2 % | 78.1 % | 9.5 | 9.6 |
| far (>1 km) | 5,700 | 2,162 | 79.3 % | 78.7 % | 15.5 | 16.2 |
| same site (<30 m) | 115 | 38 | 73.9 % | 64.3 % | 6.6 | 5.2 |
| 30 m-1 km | 24,288 | 5,701 | 82.9 % | 78.0 % | 8.5 | 8.5 |
| 1-5 km | 5,531 | 2,090 | 79.5 % | 78.7 % | 15.1 | 15.9 |
| 5-20 km | 166 | 128 | 73.5 % | 77.7 % | 37.1 | 51.7 |
| >20 km | 3 | 3 | 66.7 % | 66.7 % | 62.8 | 54.6 |

### Kansas: choices made on the tuning half

| Model | Target divided by kriging spread | Weight of far items | Leaves | Min items per leaf | Trees | Features |
|---|---|---|---|---|---|---|
| C learned | yes | 3.0 | 63 | 200 | 50 | 160 |
| D drift-only | no | 1.0 | 63 | 200 | 25 | 68 |

Training targets from before the test years: 341,005 items in 72,056 wells (dated from 1970-01-01). Tuning half: 25,067 items in 6,714 wells, 5,837 far items. Drift table of method B: targets of the last 10 years before the scoring half (36,675 items). Side model 'targets known before the scoring half': 359,533 items, actual values finished on or before 2005-04-12.

What the tuning half showed (far items; models fitted only on targets from before the test years, but with settings picked on this same half, so these numbers flatter the models): kriging 4.69 m, C 4.35 m, D 4.60 m.

Where model C puts its weight (share of split gain, `results/kansas_feature_importance.csv`): depth 74 %, distance 10 %, position 6 %, date 5 %, direction 3 %, count 2 %. Largest single features: `route_median_rel` 13.8 %, `L2_route_rel` 9.2 %, `m4b_rel` 8.8 %, `L4_route_rel` 4.9 %, `route_nearest_rel` 3.9 %.

**Netherlands**

![Netherlands: kriging, drift-corrected kriging and the learned model](results/netherlands_learned_vs_kriging.png)

### Netherlands: error by distance on the scoring half

Median absolute error in metres. In brackets: the mean absolute error.

| Distance to nearest known well with the layer | Items | Wells | A1 nearest | A2 plane | A3 kriging | A4 thickness | A side 4b | B drift-corrected kriging | C learned | D drift-only |
|---|---|---|---|---|---|---|---|---|---|---|
| all items | 1,323 | 268 | 84.6 (178.3) | 94.5 (248.5) | 75.7 (143.4) | 92.7 (158.7) | 71.1 (143.3) | 76.9 (142.0) | 73.0 (134.0) | 74.5 (132.9) |
| far (>1 km) | 938 | 194 | 163.0 (230.1) | 152.1 (326.6) | 112.5 (183.8) | 117.3 (192.0) | 109.4 (183.8) | 114.2 (182.0) | 101.2 (170.4) | 109.0 (167.9) |
| 30 m-1 km | 385 | 124 | 22.7 (51.9) | 26.2 (58.2) | 19.1 (44.9) | 38.0 (77.6) | 19.2 (44.6) | 19.3 (44.6) | 21.9 (45.5) | 27.4 (47.6) |
| 1-5 km | 537 | 121 | 80.7 (152.6) | 104.1 (190.7) | 84.2 (132.0) | 94.6 (143.0) | 77.8 (132.5) | 84.1 (130.6) | 79.6 (129.1) | 83.4 (126.9) |
| 5-20 km | 377 | 104 | 298.5 (336.3) | 277.2 (525.7) | 198.0 (258.1) | 198.0 (262.8) | 198.4 (257.1) | 201.1 (256.0) | 166.8 (225.8) | 161.2 (226.8) |
| >20 km | 24 | 11 | 237.8 (297.6) | 211.2 (240.6) | 143.7 (177.7) | 143.7 (177.7) | 143.7 (177.7) | 129.8 (170.8) | 137.4 (224.7) | 168.4 (163.2) |

95 % interval of the median absolute error (resampling whole wells), far items and all items.

| Items | A1 nearest | A2 plane | A3 kriging | A4 thickness | A side 4b | B drift-corrected kriging | C learned | D drift-only |
|---|---|---|---|---|---|---|---|---|
| far (>1 km) | 115.7-195.8 | 120.8-187.3 | 92.9-140.5 | 101.2-147.2 | 91.8-140.1 | 95.8-135.4 | 87.5-123.3 | 92.1-126.0 |
| all items | 68.7-109.6 | 83.4-112.0 | 63.2-91.4 | 76.0-112.1 | 61.4-90.7 | 63.3-91.4 | 61.2-84.6 | 63.5-86.3 |

Median signed error in metres (forecast minus actual).

| Distance band | A1 nearest | A2 plane | A3 kriging | A4 thickness | A side 4b | B drift-corrected kriging | C learned | D drift-only |
|---|---|---|---|---|---|---|---|---|
| all items | 18.9 | 21.2 | 13.0 | 28.0 | 14.2 | 10.1 | -3.6 | -1.2 |
| far (>1 km) | 51.0 | 58.9 | 41.8 | 58.2 | 42.0 | 31.9 | -1.1 | 14.8 |
| 30 m-1 km | -4.2 | 2.6 | -1.9 | 0.0 | -1.9 | 0.2 | -4.6 | -7.7 |
| 1-5 km | 34.3 | 40.7 | 29.6 | 39.0 | 29.6 | 20.8 | 1.6 | 7.8 |
| 5-20 km | 171.1 | 93.6 | 94.1 | 101.2 | 97.8 | 64.2 | -2.1 | 57.0 |
| >20 km | 77.5 | -77.3 | 49.2 | 49.2 | 49.2 | 4.3 | -71.4 | -52.7 |

### Netherlands: the learned model C against each other method, same items

Relative improvement in median absolute error (positive: C is better), with the 95 % interval from resampling whole wells.

| C against | far (>1 km) | all items | same site (<30 m) | 30 m-1 km | 1-5 km | 5-20 km | >20 km |
|---|---|---|---|---|---|---|---|
| A1 nearest | 37.9 % (18.3 to 46.3) | 13.7 % (-1.0 to 28.3) |  | 3.4 % (-37.0 to 20.4) | 1.4 % (-16.3 to 19.7) | 44.1 % (34.0 to 53.2) | 42.2 % (-56.8 to 78.2) |
| A2 plane | 33.5 % (18.2 to 43.9) | 22.7 % (12.9 to 33.8) |  | 16.3 % (-9.6 to 33.4) | 23.5 % (9.3 to 39.2) | 39.8 % (18.8 to 54.8) | 35.0 % (-110.4 to 58.2) |
| A3 kriging | 10.1 % (-4.0 to 22.4) | 3.5 % (-8.4 to 14.3) |  | -14.7 % (-50.8 to 8.1) | 5.4 % (-10.1 to 15.3) | 15.8 % (-1.1 to 29.6) | 4.4 % (-161.6 to 47.8) |
| A4 thickness | 13.8 % (-0.3 to 27.1) | 21.3 % (8.6 to 33.4) |  | 42.2 % (7.5 to 59.6) | 15.8 % (-0.9 to 28.4) | 15.8 % (-2.3 to 29.5) | 4.4 % (-161.6 to 47.8) |
| A side 4b | 7.5 % (-5.7 to 21.9) | -2.6 % (-12.8 to 11.3) |  | -14.0 % (-50.2 to 12.7) | -2.4 % (-14.8 to 12.4) | 15.9 % (-0.8 to 29.5) | 4.4 % (-161.6 to 47.8) |
| B drift-corrected kriging | 11.4 % (-2.0 to 21.4) | 5.0 % (-6.2 to 15.2) |  | -13.4 % (-46.8 to 4.9) | 5.3 % (-10.1 to 15.4) | 17.1 % (0.6 to 30.8) | -5.8 % (-171.2 to 48.3) |
| D drift-only | 7.2 % (-7.6 to 17.6) | 2.0 % (-9.7 to 12.9) |  | 19.9 % (-1.0 to 32.4) | 4.6 % (-12.4 to 18.4) | -3.5 % (-16.6 to 14.4) | 18.4 % (-190.1 to 50.6) |

The other models against the best simple method and against kriging, far items.

| Model | Far median abs error, m | against best simple (A side 4b) | against kriging |
|---|---|---|---|
| C learned | 101.2 | 7.5 % (-5.7 to 21.9) | 10.1 % (-4.0 to 22.4) |
| D drift-only | 109.0 | 0.4 % (-13.1 to 18.5) | 3.1 % (-9.8 to 18.4) |
| C on shuffled targets | 110.1 | -0.6 % (-9.7 to 7.6) | 2.2 % (-7.2 to 7.8) |
| C, targets known before scoring half | 102.0 | 6.8 % (-6.0 to 18.2) | 9.4 % (-4.3 to 18.6) |
| C, targets before test years | 109.9 | -0.5 % (-11.5 to 12.6) | 2.3 % (-8.8 to 12.7) |

### Netherlands: by layer, scoring half

Median absolute error in metres (mean in brackets). In a well each layer is one item, so items and wells are the same number.

| Layer (shallow to deep) | Items | n | A1 nearest | A2 plane | A3 kriging | A4 thickness | A side 4b | B drift-corrected kriging | C learned | D drift-only |
|---|---|---|---|---|---|---|---|---|---|---|
| NLLFC Landen Clay Member | all items | 80 | 62.5 (126.9) | 71.1 (172.7) | 45.4 (93.3) | 45.4 (93.3) | 45.4 (93.3) | 47.9 (94.4) | 40.9 (97.7) | 65.0 (99.1) |
| NLLFC Landen Clay Member | far (>1 km) | 61 | 119.6 (163.1) | 105.8 (219.3) | 101.1 (118.7) | 101.1 (118.7) | 101.1 (118.7) | 92.5 (119.8) | 102.6 (124.8) | 77.1 (119.5) |
| KNGLU Upper Holland Marl Member | all items | 136 | 98.5 (204.7) | 106.9 (264.9) | 77.2 (173.3) | 77.2 (173.9) | 77.2 (175.1) | 82.4 (170.6) | 81.6 (200.6) | 91.7 (166.2) |
| KNGLU Upper Holland Marl Member | far (>1 km) | 93 | 241.5 (281.0) | 171.2 (362.6) | 162.0 (236.4) | 151.9 (230.1) | 162.0 (239.1) | 154.5 (232.4) | 128.5 (276.4) | 159.3 (224.0) |
| KNGLM Middle Holland Claystone Member | all items | 131 | 101.5 (207.6) | 120.5 (403.6) | 85.6 (171.5) | 97.2 (176.5) | 90.8 (173.9) | 86.7 (168.0) | 80.8 (146.8) | 90.4 (161.5) |
| KNGLM Middle Holland Claystone Member | far (>1 km) | 89 | 233.9 (285.1) | 195.8 (566.8) | 150.2 (231.9) | 146.9 (230.7) | 151.4 (235.9) | 138.5 (226.8) | 130.3 (196.2) | 143.8 (216.4) |
| KNGLL Lower Holland Marl Member | all items | 136 | 101.8 (204.2) | 125.0 (400.6) | 79.4 (163.7) | 104.4 (191.6) | 89.8 (167.9) | 82.5 (161.3) | 79.8 (148.7) | 83.9 (158.4) |
| KNGLL Lower Holland Marl Member | far (>1 km) | 90 | 226.4 (286.3) | 201.2 (556.3) | 153.2 (226.5) | 170.4 (243.0) | 165.8 (232.0) | 150.6 (222.9) | 144.4 (202.7) | 167.8 (215.0) |
| RNRO1 Main Röt Evaporite Member | all items | 132 | 28.1 (124.0) | 38.1 (166.5) | 38.8 (105.4) | 33.5 (108.4) | 34.2 (106.1) | 43.6 (113.0) | 39.8 (96.5) | 48.1 (110.3) |
| RNRO1 Main Röt Evaporite Member | far (>1 km) | 58 | 209.0 (245.6) | 178.1 (341.8) | 156.0 (207.5) | 156.6 (212.9) | 156.4 (210.0) | 174.6 (224.9) | 109.2 (185.1) | 164.2 (209.8) |
| RNSOC Solling Claystone Member | all items | 107 | 55.7 (162.0) | 68.0 (145.1) | 56.6 (121.0) | 57.8 (127.2) | 57.8 (121.2) | 57.8 (124.3) | 68.4 (128.9) | 61.3 (121.8) |
| RNSOC Solling Claystone Member | far (>1 km) | 57 | 177.1 (262.5) | 169.8 (228.1) | 147.9 (191.6) | 144.2 (195.6) | 147.9 (193.4) | 134.5 (198.6) | 130.6 (201.0) | 126.1 (189.9) |
| ZEZ2H Z2 Salt Member | all items | 75 | 219.7 (356.2) | 269.0 (585.6) | 181.4 (333.5) | 181.4 (339.1) | 178.3 (333.5) | 172.0 (326.2) | 217.3 (293.8) | 174.6 (302.5) |
| ZEZ2H Z2 Salt Member | far (>1 km) | 60 | 255.1 (407.0) | 301.2 (688.2) | 225.4 (381.2) | 199.4 (376.3) | 218.9 (379.6) | 240.8 (372.2) | 255.1 (329.2) | 207.3 (341.7) |
| ZEZ2A Z2 Basal Anhydrite Member | all items | 107 | 84.5 (160.7) | 85.6 (219.7) | 80.0 (120.5) | 103.7 (147.6) | 79.8 (119.7) | 73.2 (115.4) | 71.8 (111.6) | 65.3 (101.5) |
| ZEZ2A Z2 Basal Anhydrite Member | far (>1 km) | 86 | 91.7 (166.9) | 102.9 (251.0) | 90.6 (125.4) | 102.7 (149.6) | 89.2 (124.7) | 94.9 (119.3) | 92.7 (117.2) | 75.1 (103.7) |
| ZEZ2C Z2 Carbonate Member | all items | 107 | 85.1 (148.3) | 89.7 (158.4) | 78.5 (108.7) | 104.0 (134.3) | 66.5 (106.7) | 77.4 (107.2) | 70.9 (98.7) | 64.9 (97.0) |
| ZEZ2C Z2 Carbonate Member | far (>1 km) | 86 | 96.6 (169.5) | 108.9 (184.0) | 93.4 (124.0) | 101.3 (132.7) | 87.2 (120.7) | 93.4 (122.2) | 79.5 (111.0) | 88.5 (109.8) |
| ZEZ1W Z1 Anhydrite Member | all items | 99 | 93.0 (163.0) | 88.6 (157.4) | 74.3 (120.8) | 104.0 (148.1) | 66.1 (121.0) | 80.2 (116.4) | 73.8 (104.6) | 69.2 (96.0) |
| ZEZ1W Z1 Anhydrite Member | far (>1 km) | 82 | 113.0 (182.7) | 116.6 (182.1) | 85.3 (135.6) | 108.1 (151.1) | 72.0 (136.1) | 88.4 (130.4) | 76.7 (117.0) | 82.7 (108.1) |
| ZEZ1C Z1 Carbonate Member | all items | 105 | 82.1 (158.7) | 88.2 (158.1) | 78.0 (117.5) | 98.2 (144.9) | 67.4 (113.3) | 79.0 (114.8) | 72.0 (99.8) | 72.6 (98.9) |
| ZEZ1C Z1 Carbonate Member | far (>1 km) | 88 | 112.4 (178.2) | 108.3 (178.1) | 91.8 (130.1) | 98.0 (145.9) | 79.3 (126.8) | 90.7 (127.5) | 79.1 (109.5) | 82.9 (109.7) |
| ZEZ1K Coppershale Member | all items | 108 | 73.8 (153.6) | 86.4 (162.0) | 78.2 (122.9) | 104.2 (151.0) | 70.0 (116.2) | 74.9 (121.7) | 63.3 (100.7) | 70.5 (103.9) |
| ZEZ1K Coppershale Member | far (>1 km) | 88 | 92.6 (175.3) | 109.3 (188.5) | 94.3 (140.1) | 104.2 (153.0) | 86.1 (132.0) | 95.5 (138.9) | 73.2 (113.7) | 89.4 (118.5) |

### Netherlands: how often the actual value is inside the 80 % range

| Distance band | Items | Wells | Learned model C | Kriging | Median width C, m | Median width kriging, m |
|---|---|---|---|---|---|---|
| all items | 1,323 | 268 | 78.4 % | 72.9 % | 307.4 | 298.1 |
| far (>1 km) | 938 | 194 | 75.8 % | 70.3 % | 431.8 | 403.0 |
| 30 m-1 km | 385 | 124 | 84.7 % | 79.2 % | 140.8 | 130.1 |
| 1-5 km | 537 | 121 | 74.1 % | 68.7 % | 295.6 | 296.0 |
| 5-20 km | 377 | 104 | 76.7 % | 71.1 % | 659.9 | 675.6 |
| >20 km | 24 | 11 | 100.0 % | 91.7 % | 1259.8 | 1349.8 |

### Netherlands: choices made on the tuning half

| Model | Target divided by kriging spread | Weight of far items | Leaves | Min items per leaf | Trees | Features |
|---|---|---|---|---|---|---|
| C learned | yes | 3.0 | 31 | 20 | 525 | 160 |
| D drift-only | no | 1.0 | 15 | 15 | 300 | 68 |

Training targets from before the test years: 11,307 items in 2,539 wells (dated from 1950-01-01). Tuning half: 1,264 items in 267 wells, 953 far items. Drift table of method B: targets of the last 20 years before the scoring half (7,182 items). Side model 'targets known before the scoring half': 11,178 items, actual values finished on or before 1989-08-09.

What the tuning half showed (far items; models fitted only on targets from before the test years, but with settings picked on this same half, so these numbers flatter the models): kriging 130.7 m, C 118.0 m, D 119.9 m.

Where model C puts its weight (share of split gain, `results/netherlands_feature_importance.csv`): depth 57 %, distance 16 %, direction 14 %, date 8 %, position 3 %, count 2 %. Largest single features: `L0_m1_rel` 1.5 %, `nb1_dx_km` 1.4 %, `L0_route_rel` 1.3 %, `L0_sd3` 1.3 %, `route_median_rel` 1.3 %.

**Facts drawn from the tables**

- **Pass mark, Kansas.** Best simple method on far items: side method 4b, 3.87 m. C: 3.60 m. Improvement 7.1 % (3.9 to 9.5). Fail: under 10 %.
- **Pass mark, Netherlands.** Best simple method on far items: side method 4b, 109.4 m. C: 101.2 m. Improvement 7.5 % (-5.7 to 21.9). Fail: under 10 % and the interval includes zero.
- **If side method 4b is left out** (it was my addition in the first run, not one of the brief's four): the best simple method is drift-corrected kriging in Kansas (3.97 m; C is 9.4 % better, interval 6.8 to 11.9) and plain kriging in the Netherlands (112.5 m; C is 10.1 % better, interval -4.0 to 22.4). Both would still fail.
- **Drift.** Against the best simple method D gains 0.1 % (Kansas) and 0.4 % (Netherlands) on far items. Against plain kriging D gains 3.2 % in Kansas (0.9 to 5.0) and 3.1 % in the Netherlands (-9.8 to 18.4), about a third of what C gains against kriging. Drift-corrected kriging B gains 0.7 % over kriging in Kansas and loses 1.5 % in the Netherlands.
- **Bias on far items** (median of forecast minus actual). Kansas: kriging -1.03 m, B -0.42 m, D -0.38 m, C -0.10 m. Netherlands: kriging +41.8 m, B +31.9 m, D +14.8 m, C -1.1 m.
- **All items.** Kansas: C 2.11 m, best simple there is B with 2.24 m (C 6.1 % better, 5.1 to 7.3). Netherlands: C 73.0 m, 4b 71.1 m (C 2.6 % worse, -12.8 to 11.3).
- **Mean absolute error, far items.** Kansas: 4b 9.59 m, C 9.17 m (4.3 % lower). Netherlands: 4b 183.8 m, C 170.4 m, D 167.9 m.
- **80 % range.** C's range holds the actual value 82.2 % of the time in Kansas (kriging 78.1 %) and 78.4 % in the Netherlands (kriging 72.9 %). On far items: 79.3 % against 78.7 % in Kansas, 75.8 % against 70.3 % in the Netherlands. The ranges are about as wide as kriging's.
- **Where C puts its weight.** Share of split gain in depth features: 74 % in Kansas, 57 % in the Netherlands. In Kansas the three largest features are routes through other layers (the median of all routes 13.8 %, the route through the Heebner 9.2 %, side method 4b 8.8 %). In the Netherlands no single feature has more than 1.5 %. Feature names: `L<n>` is the n-th chosen layer counted from the top, starting at 0.
- **Side models.** Trained only on targets already known before the scoring half: Kansas 3.57 m, Netherlands 102.0 m. Trained only on targets from before the test years: Kansas 3.64 m, Netherlands 109.9 m.

**Judgment.** In Kansas there is a real edge for a learned model, about 7 % on far items and about 10 % near wells, and it comes mainly from using the other layers at the same spot, not from knowing that new wells run high. It is too small to pass, and in metres it is a quarter of a metre. In the Netherlands the test is too small to see an effect of this size: an honest reading is "no evidence either way". If the aim is to beat mapping where it is weakest, far from wells, this run gives no support: the edge shrinks with distance in Kansas.

### 6. Checks

All four checks passed.

- **Date-rule test, extended to every known well behind every feature** (`src/checks.py`). Each feature is built from stored lists of known wells; the test reads the dates again from the input tables with the first run's independent code and checks each known well against each test well's start date. It also checks that the pipeline's own dates agree.
  - Scoring half: Kansas 15,291,760 uses of a known well, Netherlands 1,127,196. **0 violations.**
  - Training targets and tuning half: Kansas 182,271,584 uses, Netherlands 10,047,299. **0 violations.**
- **Own-pick test.** Two parts.
  - On every item above: the known wells behind a feature never include the test well itself, nor (Netherlands) a sidetrack of its hole system. 0 cases.
  - On 60 random scoring wells per country (280 items in Kansas, 273 in the Netherlands): every pick of the test well was shifted by 137 m and its features were built again. No feature and no simple-method forecast moved, in any well. As a control the same shift was given to the nearest known well instead: the features moved in all 60 wells, so the test can fail.
  - In the rehearsal on the tuning half this test first reported 2 Kansas wells. The cause was the test itself: it put values back by subtracting 137, which does not always restore the last digit. It now restores saved copies. This was fixed before the frozen commit.
- **Shuffle test.** C trained with the same settings on shuffled targets, scored on the far items of the scoring half. Kansas: 3.99 m, that is -3.0 % against the best simple method (-6.2 to -0.2) and +0.2 % against kriging (-1.2 to 1.9). Netherlands: 110.1 m, -0.6 % against the best simple method (-9.7 to 7.6) and +2.2 % against kriging (-7.2 to 7.8). The gain vanishes.
- **Frozen models.** Before scoring, the script checked the sha256 of 10 files per country (models, drift table, settings, feature list) against `results/model_hashes.json` of commit `c7b367c`.
- **Rerun with one command.** After scoring, `./run.sh` was run again in full (22 minutes). It rebuilt all 14 model files, the drift tables and the feature list with the same sha256 as in the frozen commit. Every table, per-item file and chart of the scoring half came out byte for byte the same. The only differences were the run-time fields ("seconds") in the two settings files and the two tuning-search files; I kept the committed versions of those four files. Seeds are fixed in the code.

Two more facts about agreement with the first run:

- The guard changes nothing it should not. Netherlands: the 1,323 scoring items are exactly the first run's, with the same actual values and the same kriging forecasts. Kansas: 30,103 of the first run's 30,115 scoring-half items. The 12 missing ones took their actual value from a record dated on or after the sealed period's start (a later re-entry of a development hole), which the guard blocks. In the tuning half 12 of 25,079 items and 2 wells are missing for the same reason.
- In Kansas the simple-method forecasts differ from the first run by more than 2 mm in 31 (kriging) to 44 (nearest well) of 30,103 items. These are ties between equally distant known wells; which one is taken depends on which wells are in memory. The Netherlands has one such item.

### 7. What I could not do or verify

- I could not make the Dutch test larger. 194 far wells is what the scoring half holds.
- I did not try other model families, more settings, feature selection or averaging over seeds. The brief asked for a quick model. A failed quick model does not prove that no model passes.
- The 95 % intervals resample wells of the scoring half. They do not include the luck of the model fit (bagging seed), which the Dutch side models show to be several percent, nor the choice of the best simple method, which is made on the same items.
- The settings were picked on the far items of the tuning half, so the tuning-half numbers flatter the models. The scoring half is the only clean number.
- I did not check any pick against a log, in either run.
- LightGBM gives the same model on this machine with 4 threads. I did not test other machines or thread counts.
- In the Dutch chart some axis labels are in powers of ten. I left the chart code as frozen.

### 8. Where the work was blocked

- No rule blocked the work and none was worked around.
- The first-run loaders read sealed depths before dropping them. To keep rule 4 I did not copy or change them; the new guard hands them tables in which those depths were never read. See section 1.
- The container restarted once during the final rerun. Nothing was lost; the rerun was started again.
- Commits: split `01433f2`; frozen code, settings and model hashes `c7b367c`; scoring results `cbd45e9`. Nothing was committed to `main`. No force-push, no rewritten history.
- One code file changed after the frozen commit: `src/report_tables.py`, to add the feature-importance table. No code that builds features, trains or scores was changed after it.

### 9. How to rerun

```
cd blind_test/tops_learned
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh        # split, training, scoring, tables, hashes.txt, report.md
```

`run.sh` reads only `blind_test/tops_headroom/data` and `results`. Seeds are fixed. LightGBM runs with 4 threads and its results depend on the thread count, so the count is fixed in the code. Model files are not committed (they are rebuilt by `run.sh`); their sha256 is in `results/model_hashes.json`.

Files: `src/` code; `results/` tables, charts, split, feature list, settings, model hashes; `hashes.txt` sha256 of every result file.
