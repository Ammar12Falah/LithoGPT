# Tops headroom test: report

First step of the blind drilling test. Brief of 13 November 2026, version 2.
Work done on 13 November 2026 in one Claude Code session.
Branch: `claude/kind-mendel-aqkrot` (the environment only allows pushes to this branch; the brief's name `blind-test-tops-headroom` was not used).

The question: when simple mapping methods forecast the depth of rock layer tops in a new well from earlier wells, how big is the miss, and how does it grow with distance from the nearest earlier well?

## First screen

### Pass or fail

| Country | Mark (a): enough hard wells | Mark (b): best simple method misses by at least 2 x floor A on far items | Verdict |
|---|---|---|---|
| **Kansas** | **Pass.** Far items come from 4,735 development wells (need 300). The sealed period holds 4,517 far wells (need 300). | **Pass.** Best of the four on far items is kriging: median absolute error 4.36 m (95 % interval 4.21 to 4.49 m), on 11,543 items. Floor A is 1.83 m (35,782 pairs). Ratio 2.38 (interval 2.30 to 2.45, floor held fixed). | **PASS** |
| **Netherlands** | Not started yet. | Not started yet. | Not done |

"Far" means the nearest known well with that top is more than 1 km away. All scores are from the development period only. The sealed period was counted, never scored.

### Three main findings

1. **Kansas has room, but not a lot.** On far items the best simple method misses by 4.36 m (14.3 ft). No method can beat about 1.83 m (6 ft). The gap is about 2.5 m.
2. **The miss grows steadily with distance.** Kriging misses by 2.22 m under 1 km, 4.22 m at 1 to 5 km, 10.68 m at 5 to 20 km. But 79 % of Kansas test items (43,651 of 55,194) have a known well with the top within 1 km. There the best method is already at 1.2 times the floor.
3. **Kriging with a local trend is the best of the four** at every distance beyond the same site. Its 80 % range holds the actual value 77.6 % of the time. The thickness method as the brief defines it is worse than kriging. A stronger variant I added as a side result gains only 0.15 m on far items (4.21 m) and does not change the verdict.

### Three main doubts

1. **The floor is coarse.** Kansas depths are whole feet, and floor A is exactly 6 ft. It mixes pick noise, elevation errors and real relief over 150 m. Mark (b) needs 3.66 m and the result is 4.36 m, so the pass is clear but the margin is under 1 m.
2. **Names of tops are not used the same way by everyone.** Most test wells report short names ("Anhydrite", "Topeka", "Lansing-Kansas City"). I merged them with the formal names. For Topeka, Kansas City, Marmaton, Fort Scott and Cherokee the picks of different sources often disagree by several metres. Part of the far miss on those tops is naming noise, not geology. Top by top the ratio runs from 1.44 (Stone Corral) to 5.46 (Kansas City).
3. **"Far" in Kansas is mostly 1 to 5 km.** Of 11,543 far items, 11,058 are at 1 to 5 km and only 485 are beyond 5 km. The pass rests on mid-range step-outs, not on true wildcats.

---

## Details

Facts come first in each section. My own reading is marked **Judgment**.

### 1. Data

**Kansas.** Kansas Geological Survey (KGS), statewide bulk files, both marked "October 9, 2026" on the download page <https://www.kgs.ku.edu/PRS/petroDB.html>. Downloaded 13 November 2026.

- `ks_wells.zip`: 519,691 well records. Used: KID, API number, latitude, longitude and their source, elevation and its reference, total depth, spud, completion and plugging dates, status, comments.
- `ks_tops.zip`: 2,135,525 top rows in 196,743 well records. Used: KID, elevation and reference, formation name, top depth, source of the pick.

What the KGS says about reuse (terms of use page <https://www.kgs.ku.edu/General/copyright.html>, "Updated July 2002"):

> "Information presented on this website has been developed for public use and may be distributed or copied."
> "The user is granted the right, without any fee or cost, to access, link to and use, publish, distribute, disseminate, transfer, or in any manner alter, modify, revise, copy, edit, or digitize this information."

It asks for this citation: "The source of this material is the Kansas Geological Survey website at http://www.kgs.ku.edu/. All Rights Reserved." The download page adds: "Tops are derived from various sources and are not necessarily confirmed by the KGS."

These terms clearly allow reuse. The cleaned input tables are committed: `data/kansas_wells.csv.gz` (15.8 MB) and `data/kansas_tops.csv.gz` (13.1 MB). They hold every row of the two files, with only the columns listed above.

No FORCE 2020 file was opened. No Norwegian data was used. Only KGS hosts were contacted for Kansas (`www.kgs.ku.edu`, `kgs.ku.edu`, `chasm.kgs.ku.edu`), plus the Python package index for installs. Every downloaded file is in `manifest.csv` with its source, date, size and sha256.

### 2. Cleaning (Kansas)

Elevations are in metres relative to sea level: elevation of the top = well elevation minus top depth, times 0.3048. Feet are kept as a second column in the result tables.

Choices, each with the count of wells left, are in the cleaning table below. The main ones:

- **What depths are measured from.** The file does not say what each top depth is measured from. I took it as the elevation reference listed for the well (KB kelly bushing, DF derrick floor, GL ground level, TOPO estimate). The elevation and reference in the tops file and in the wells file agree for every row. Wells with a GL or TOPO elevation are **flagged, not dropped**: 22,940 holes. For GL the depth may in fact be from a kelly bushing a few feet higher; I cannot correct this. TOPO elevations are estimates from a digital model.
- **Position.** Coordinates are NAD27, mostly worked out by the KGS from the legal description. Projected to metres with a Lambert conformal conic map projection, no datum change. Wells placed only at the centre of their section were dropped. Wells placed from quarter calls are kept and flagged (10,207 holes).
- **Deviated wells.** The file has no direction field. I dropped records whose API number has a sidetrack code (digits 11 and 12 not "00"). This is the rule the KGS itself uses for its horizontal-well list. I also dropped records whose comment mentions horizontal, directional, deviated, slant, sidetrack, whipstock, BHL or TVD. This removed 730 well records with tops. No true vertical depth is given for them.
- **Same hole.** Records with the same first 10 digits of the API number are one hole (re-entries, workovers). A re-entry is never a new well. 356 more holes were merged because another record had the same position, elevation, total depth and spud date.
- **Several picks of one top.** Within one record: the median. If they disagree by more than 100 ft the top is dropped for that record (8,153 cases). Across records of one hole: the earliest finished record that reports the top.
- **Dates.** A hole can be a test well only if every drilled record of it was spudded in 2000 or later and it has no completion or plugging date before 2000. A record's finish date is its completion date (the KGS defines this column as "Date of drilling finish"); the spud date if that is later; the plugging date if there is no completion date. Tops from a record with no finish date are never used as known wells.

**Names of tops.** The KGS column FORMATION has 6,203 different spellings. 393 differ only in upper or lower case or spacing and were merged. 53 more were merged by hand as spelling variants of the same top, such as "Heebner" with "Heebner Shale Member". Full map: `results/kansas_name_map.csv`. Evidence for each hand merge (wells that carry both names, and the depth difference): `results/kansas_name_map_evidence.csv`.

Names that mean another marker were **not** merged: "Lansing B" and other zones, "Cherokee Shale", "Mississippian Chert", "Simpson Sand", "Base Kansas City" and the like.

Three merges deserve a warning:

- "Anhydrite" (13,799 records, mostly after 2000) was merged with "Stone Corral Formation". This is a synonym, not a spelling. In the 105 records that carry both, the median depth difference is 4 ft and 65 % agree within 10 ft.
- "Lansing-Kansas City" was merged with "Lansing Group", because the top of that interval is the top of the Lansing. 41 records carry both; median difference 3 ft.
- "Topeka", "Fort Scott", "Marmaton" and "Cherokee" short names agree poorly with the formal names where both exist (median differences 51, 36.5, 15 and 16 ft). They are the same names, so I merged them, but these tops are picked inconsistently. Floor B shows the same thing for Topeka and Cherokee.

### 3. Split (Kansas)

Set from counts only, in the same run and before any scoring.

- Test wells: holes spudded in 2000 or later with at least one chosen top after cleaning: **26,877**.
- Ordered by spud date. Cut date **15 July 2010**. Development period: 13,435 wells spudded from 3 January 2000 up to the cut date. Sealed period: 13,442 wells spudded from the cut date to 27 July 2026.
- Files: `results/kansas_cut_date.txt`, `results/kansas_split.csv`, `results/kansas_sealed_wells.csv`.
- After the split the code removes every sealed well's depths from memory. Only the positions, dates and list of tops of sealed wells are kept, for counting.
- Known wells for a test well: finish date at least 12 months before the test well's spud date. Side run: no waiting time.

### 4. Methods

All four use only the known wells of each test well. All settings were chosen on wells spudded before 2000: pseudo-test wells spudded 1990 to 1999, known wells finished at least 12 months earlier. The setting with the lowest median absolute error won. The search grid and every score are in `results/kansas_tuning_grid.csv`, the chosen settings in `results/kansas_settings.json`.

1. **Nearest known well.** The elevation of the top in the nearest known well that has that top.
2. **Local plane.** A least-squares plane through the 8 nearest known wells with the top, read at the test well. If the wells do not span a plane, their mean.
3. **Kriging with a local trend.** Universal kriging with a linear trend in x and y, in a moving neighbourhood of the 24 nearest known wells. Variogram: nugget plus a power of distance, g(h) = r + h^a, with the shape (a and r) set per top on pre-2000 wells. The size of the variogram is estimated from the same 24 wells each time. The 80 % range is the kriging forecast plus or minus a Student-t quantile times the kriging standard deviation, times one multiplier set on pre-2000 wells (0.998, so almost nothing).
4. **Thickness method, exactly as run.** For a target top in a test well:
   - Take the chosen tops in order from shallow to deep.
   - Find the shallowest chosen top above the target that is "supported": at least 5 known wells with that top within 10 km. Forecast its elevation with method 3.
   - Go down to the target in as few steps as possible. A step from top A to a deeper top B is allowed if at least 5 known wells within 10 km report both. The thickness A to B is kriged (ordinary kriging, 16 nearest known wells that report both tops, wells with zero or negative thickness left out). Subtract it.
   - If the target cannot be reached from that start, try the next deeper start. If none works, use method 3 directly.
   - "As few steps as possible" was chosen on pre-2000 wells over "step through every chosen top in between" (median error 3.47 m against 4.82 m).

For methods 2, 3 and 4 a neighbour is left out if it lies more than max(6 x 1.4826 x MAD, 3 m) off the plane through its fellow neighbours. This was switched on because it lowered the error on pre-2000 wells (2.78 m against 3.03 m).

**Side method 4b (not one of the four, not in the pass marks).** The brief's method 4 always starts from the shallowest top. That is a weak choice when the target is well controlled. So I also ran a stronger variant: for each item take either direct kriging, or kriging of one overlying chosen top plus one kriged thickness, whichever has the smaller predicted error variance. It is reported next to the four so the reader can see that a better thickness method does not change the picture.

### 5. The floor (Kansas)

- **Floor A** (used in the pass marks): the same chosen top in two different holes less than 150 m apart, both with a precise position (from footages or GPS). No sealed wells. Median absolute difference **1.83 m** (6 ft), from 35,782 pairs in 12,915 different pairs of holes. This is far more than the 50 pairs needed, so the floor is reliable in the sense of the brief.
- With any position quality: 1.83 m (38,571 pairs). Without flagged elevations: 1.83 m (32,162 pairs).
- **Floor B**: two picks of the same top in the same hole from different sources. Median absolute difference **0.30 m** (1 ft), from 55,738 pairs. 42.1 % of the pairs are exactly equal, which suggests that many "different sources" are copies of one pick. Among pairs that differ, the median is 2.74 m.
- By top, floor A runs from 1.22 m (Heebner, Toronto) to 2.74 m (Simpson). See `results/kansas_floors.csv`.

**Judgment.** Floor A is the right one for the pass marks, as the brief says. It still contains some real geology (two holes 150 m apart are not the same place) and the GL and TOPO elevation noise. So it is, if anything, a little high, which makes mark (b) harder to pass.

### 6. Results (Kansas, development period)

![Kansas: median absolute error against distance](results/kansas_error_vs_distance.png)

One test item is one chosen top in one test well. 55,194 items in 13,435 wells. Every item had at least one known well with the top.

<!-- TABLES:kansas -->

Other facts from these tables:

- **Forecasts are too deep by about 0.8 m on the median** (kriging: -0.82 m). New wells come in slightly higher than the map from older wells says.
- **No waiting time** changes little: kriging goes from 2.53 m to 2.32 m on all items and stays at 4.37 m on far items. With no waiting time fewer items are far (8,752 against 11,543).
- **Without flagged wells** (no GL or TOPO elevation, no quarter-call position) the far miss of kriging is 4.22 m and floor A is 1.83 m: the same picture.
- **Sealed period, counts only:** 13,442 wells, 64,634 items, 14,479 far items in 4,517 wells.

**Judgment.** The steady bias is what one would expect if operators drill where they hope the layer is high. A method that knew this could gain a few tenths of a metre. The pass in Kansas is real but narrow in metres: a new method has to beat 4.36 m on far items and cannot go below about 1.83 m.

### 7. Checks

- **Date-rule test** (`src/check_date_rule.py`, run by the one command). It reads the dates again from the input tables with separate code and checks every known well behind every forecast. Kansas: 551,940 forecasts checked (main run and no-waiting-time run; five forecasts per item, the four methods and side method 4b), 11,296,020 uses of a known well checked, **0 violations**. Output: `results/date_rule_check.txt`.
- **Spot-check sheet:** `results/kansas_spot_check.csv`. 20 random test items. For each: the test well, its spud date, the latest finish date allowed, every known well used by each method with its finish date, distance and value, each forecast and the actual value. For methods 2 to 4 the sheet lists all neighbours taken; a few of them may have been left out by the outlier screen.
- **Rerun:** `./run.sh` goes from `data/` to `results/` in about 5 minutes. I ran it twice; every result file had the same sha256 both times (`hashes.txt`).

### 8. What I could not do or verify

- I could not check what each top depth is measured from. The file does not say. See section 2.
- I could not check deviation beyond the API code and the comments. Some deviated wells without that code may remain. Kansas wells are mostly vertical.
- I did not check any pick against a log. A wrong pick in a test well counts as a miss of the method.
- "Known" is decided by the finish date of the well, as the brief says. I did not check when each pick was made or released. Some picks on old wells were made later by KGS projects. They are treated as known from the well's finish date.
- The sealed period was not scored. I cannot say whether its errors look like the development period.
- The 95 % intervals resample wells. They do not include the uncertainty of the floor or of the settings.
- Wells in one field are not independent. The well-resampled intervals are probably too narrow.

### 9. How to rerun

```
cd blind_test/tops_headroom
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh                      # data/ -> results/, date-rule test, hashes.txt   (about 5 min per country)
.venv/bin/python -I src/build_report.py     # report_src.md + result tables -> report.md
```

To rebuild `data/` from the source: `./download_kansas.sh`, then `.venv/bin/python -I src/prepare_kansas.py` and `.venv/bin/python -I src/make_manifest.py`. The KGS files change over time; `manifest.csv` holds the hashes of the files used here.

Files: `src/` code; `data/` cleaned input tables; `results/` tables, chart, name maps, split, spot-check sheet; `manifest.csv` downloads; `hashes.txt` sha256 of every download, input table and result file.
