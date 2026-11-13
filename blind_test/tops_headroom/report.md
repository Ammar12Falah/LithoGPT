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
| **Netherlands** | **Pass, narrowly.** Far items come from 371 development wells (need 300). The sealed period holds 342 far wells (need 300). | **Pass.** Best of the four on far items is kriging: median absolute error 122.4 m (95 % interval 108.0 to 141.8 m), on 1,891 items. Floor A is 4.19 m (7,139 pairs). Ratio 29.2 (interval 25.8 to 33.8, floor held fixed). | **PASS** |

"Far" means the nearest known well with that top is more than 1 km away. All scores are from the development period only. The sealed period was counted, never scored.

### Three main findings

1. **Both countries pass, but they are very different.** Kansas has a little room: the best simple method misses far tops by 4.36 m, against a floor of 1.83 m. The Netherlands has a lot: 122 m against a floor of 4.19 m.
2. **The miss grows steadily with distance.** Kriging in Kansas: 2.2 m under 1 km, 4.2 m at 1 to 5 km, 10.7 m at 5 to 20 km. Kriging in the Netherlands: 16 m, 78 m and 191 m. In Kansas 79 % of test items have a known well with the top within 1 km, and there the best method is at 1.2 times the floor. In the Netherlands only 27 % do, and even there the miss is 4 times the floor.
3. **Kriging with a local trend is the best of the four in both countries**, and its 80 % range is roughly honest (it holds the actual value 77.6 % of the time in Kansas, 74.2 % in the Netherlands). The thickness method as the brief defines it is worse than kriging. A stronger thickness variant that I added as a side result changes nothing (far miss 4.21 m in Kansas, 122.8 m in the Netherlands). Forecasts are biased: 0.8 m too deep in Kansas, 42 m too shallow on far items in the Netherlands.

### Three main doubts

1. **The Kansas margin is small and its floor is coarse.** Kansas depths are whole feet and floor A is exactly 6 ft. Mark (b) needs 3.66 m; the result is 4.36 m. Top by top the ratio runs from 1.44 (Stone Corral) to 5.46 (Kansas City). "Far" in Kansas is mostly 1 to 5 km (11,058 of 11,543 far items).
2. **Picks are not all made the same way, and I could not check when they were made.** In Kansas most test wells use short names ("Anhydrite", "Topeka", "Lansing-Kansas City") that I merged with the formal names; for some tops different sources disagree by metres. In the Netherlands 76 % of the top rows of holes finished before 1990 carry a source code with a later year in its name ("RGD1997", "ONSHORE2004" and the like). So a known well's pick may have been revised with knowledge of later wells, even of the test wells. That would make the simple methods look better than they were, not worse.
3. **The Dutch test is small and leans on deviated wells.** 535 development wells, 371 of them far; the sealed count of 342 is only just over 300 and had to use surface positions. 363 of the 535 development wells are deviated or horizontal. I forecast each top at the place where the test well actually crossed it, which a real forecast would know only roughly.

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

**Netherlands.** NLOG, the Dutch oil and gas portal. Downloaded 13 November 2026.

- `thematische_data_boringen.zip` from <https://www.nlog.nl/en/boreholes> ("Combined data selections by type"). Files inside are dated 23 September 2026. Used: `nlog_stratstelsel_20260923.csv`, the lithostratigraphy of all boreholes: 111,651 rows in 6,517 wellbores. Columns used: wellbore, borehole system, the borehole that drilled the interval, top and base along hole, true vertical depth of the top, unit code and name, anomaly code, position of the top (ED50 UTM zone 31), source of the interpretation.
- The borehole list: "All boreholes" from NLOG's page <https://www.nlog.nl/en/files-interactive-map>: 6,739 boreholes. Columns used: code, borehole or sidetrack, type, start and end date of drilling, shape (vertical, deviated, horizontal), on or offshore, reference level, its height and what it is relative to, position.

**A point about rule 4.** NLOG's page links the borehole list on another host, `www.gdngeoservices.nl`, the map server of the Geological Survey of the Netherlands. The list is not a file on `nlog.nl`. I stopped and asked. Ammar approved that host on 13 November 2026 and I downloaded that one file from it, nothing else. The borehole overview inside NLOG's "datacenter" web app was **not** used: it has no published file link.

What NLOG says about reuse (disclaimer page <https://www.nlog.nl/en/disclaimer>):

> "NLOG.NL does not claim any rights (except domain names, trademark rights, patents and other intellectual property rights) in respect of information provided on or through this website. Users are permitted to copy, to download and to disclose in any way, to distribute or to simplify the information provided on this website without the prior written permission of NLOG.NL or the lawful consent of the entitled party. Users are also permitted to copy, duplicate, process or edit the information and/or layout, provided NLOG.NL is quoted as the source."

Its data page adds: "Well logs, cuttings, cores and the accompanying reports are available after a statutory five-year confidentiality period. Administrative data are available to the public immediately."

These terms clearly allow reuse with NLOG named as the source. The cleaned input tables are committed: `data/netherlands_wells.csv.gz` (0.15 MB) and `data/netherlands_tops.csv.gz` (1.74 MB). **Judgment:** the borehole list is offered "through" the NLOG website, so I read the same terms as covering it; I did not look for separate terms on the map server.

All four committed input tables together are 30.8 MB, under the 50 MB limit.

No FORCE 2020 file was opened. No Norwegian data was used. Hosts contacted: `www.kgs.ku.edu`, `kgs.ku.edu`, `chasm.kgs.ku.edu`, `www.nlog.nl`, `www.gdngeoservices.nl` (one file, approved), and the Python package index for installs. Every downloaded file is in `manifest.csv` with its source, date, size and sha256.

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

### 2b. Cleaning (Netherlands)

Counts after each step are in the cleaning table in section 6b.

- **Vertical reference.** The file gives the true vertical depth of each top below NAP (onshore) or mean sea level (offshore). The NLOG description of the file says so. Elevation = minus that depth, in metres. Nothing had to be converted. I did not correct for the small difference between NAP and mean sea level.
- **Check of the reference.** Where a wellbore's first interval starts at 0 m along hole, its vertical depth should be minus the reference height in the borehole list. It agrees within 0.05 m in 66.1 % of 6,308 wellbores and within 1 m in 97.5 %. Holes off by more than 1 m are flagged, not dropped (118 holes in the analysis). The source marks no elevation as an estimate.
- **Deviated wells are kept.** The file gives the true vertical depth and the position of every top, which is the brief's condition for keeping them. Holes in the analysis: 2,109 vertical, 3,084 deviated, 278 horizontal. No hole was removed for being deviated. Distances are measured between the positions of the tops, not between wellheads.
- **Which rows are tops.** A row is used only if it is a named member, formation, subgroup or group; the true vertical depth and position are present; the interval directly above it in the same wellbore is an interpreted unit (so the top is a drilled boundary, not the surface, a gap, a fault row or the edge of a "NOT INTERPRETED" stretch); and its upper boundary is not marked as a kick-off point, a fault or uncertain. Tops that are unconformities are kept.
- **Same hole.** NLOG lists a sidetrack as its own borehole, and repeats the picks above the kick-off point in the table of the mother borehole and of each sidetrack. I removed the 13,907 copies. A hole in this test is a borehole or sidetrack with the tops it drilled itself. A sidetrack is never a test well. Its own picks count as known data once it is finished. A borehole and its sidetracks are never paired for the floor. Sidetracks of sealed wells are sealed with them.
- **One level of the naming scheme.** Counted after cleaning, the member level has the most data (60,342 hole-top values, against 45,717 at formation level and 22,740 at group level, with members rolled up). So the chosen tops are members. The file uses the codes of the Dutch nomenclature, so there are no spelling variants to merge; the name map (`results/netherlands_name_map.csv`) lists the 209 member codes with their names.
- **A tie at place 12.** Z2 Salt Member and Grey Salt Clay Member are both reported in 843 holes finished before 1990. I took the first in code order, Z2 Salt Member.
- **Dates.** Test wells are mother boreholes (not sidetracks) whose drilling ended in 1990 or later. Known wells for a test well: drilling ended at least 5 years before the test well's start date of drilling. Side run: no waiting time.

### 3. Split (Kansas)

Set from counts only, in the same run and before any scoring.

- Test wells: holes spudded in 2000 or later with at least one chosen top after cleaning: **26,877**.
- Ordered by spud date. Cut date **15 July 2010**. Development period: 13,435 wells spudded from 3 January 2000 up to the cut date. Sealed period: 13,442 wells spudded from the cut date to 27 July 2026.
- Files: `results/kansas_cut_date.txt`, `results/kansas_split.csv`, `results/kansas_sealed_wells.csv`.
- After the split the code removes every sealed well's depths from memory. Only the positions, dates and list of tops of sealed wells are kept, for counting.
- Known wells for a test well: finish date at least 12 months before the test well's spud date. Side run: no waiting time.

### 3b. Split (Netherlands)

- Test wells: 1,251 mother boreholes finished in 1990 or later have tops; **1,070** of them have at least one chosen top.
- Ordered by end date of drilling. Cut date **30 March 2001**. Development period: 535 wells finished from 16 January 1990 up to the cut date (172 vertical, 324 deviated, 39 horizontal; 288 onshore, 247 offshore). Sealed period: 535 wells finished from the cut date to 16 October 2025.
- Files: `results/netherlands_cut_date.txt`, `results/netherlands_split.csv`, `results/netherlands_sealed_wells.csv`.
- As in Kansas, sealed depths are removed from memory right after the split. For counting far wells in the sealed period I used the surface position of each sealed borehole, not the position of its tops, because the position of a top in a deviated hole depends on its depth.

### 4. Methods

All four use only the known wells of each test well. All settings were chosen on wells drilled before the test years, with the same date rule. Kansas: pseudo-test wells spudded 1990 to 1999. Netherlands: pseudo-test wells finished 1975 to 1989. The setting with the lowest median absolute error won. The search grids and every score are in `results/<country>_tuning_grid.csv`, the chosen settings in `results/<country>_settings.json` and in the settings tables below. The numbers quoted in this section are the Kansas ones.

In the Netherlands every forecast is made at the position of the top in the test well. For the thickness method, a known hole gives a thickness only if its two tops lie within 250 m of each other in plan; the thickness is placed at the lower top.

1. **Nearest known well.** The elevation of the top in the nearest known well that has that top.
2. **Local plane.** A least-squares plane through the 8 nearest known wells with the top, read at the test well. If the wells do not span a plane, their mean.
3. **Kriging with a local trend.** Universal kriging with a linear trend in x and y, in a moving neighbourhood of the 24 nearest known wells. Variogram: nugget plus a power of distance, g(h) = r + h^a, with the shape (a and r) set per top on pre-2000 wells. The size of the variogram is estimated from the same 24 wells each time. The 80 % range is the kriging forecast plus or minus a Student-t quantile times the kriging standard deviation, times one multiplier set on pre-2000 wells (0.998, so almost nothing).
4. **Thickness method, exactly as run.** For a target top in a test well:
   - Take the chosen tops in order from shallow to deep.
   - Find the shallowest chosen top above the target that is "supported": at least 5 known wells with that top within 10 km. Forecast its elevation with method 3.
   - Go down to the target in as few steps as possible. A step from top A to a deeper top B is allowed if at least 5 known wells within 10 km report both. The thickness A to B is kriged (ordinary kriging, 16 nearest known wells that report both tops, wells with zero or negative thickness left out). Subtract it.
   - If the target cannot be reached from that start, try the next deeper start. If none works, use method 3 directly.
   - "As few steps as possible" was chosen on pre-2000 wells over "step through every chosen top in between" (median error 3.47 m against 4.82 m).

For methods 2, 3 and 4 a neighbour is left out if it lies more than max(6 x 1.4826 x MAD, 3 m) off the plane through its fellow neighbours. In Kansas this was switched on because it lowered the error on pre-2000 wells (2.78 m against 3.03 m). In the Netherlands the same search left it off, and chose 4 wells for the plane, 12 or 24 wells for kriging and 8 wells for thickness kriging (see the settings tables).

**Side method 4b (not one of the four, not in the pass marks).** The brief's method 4 always starts from the shallowest top. That is a weak choice when the target is well controlled. So I also ran a stronger variant: for each item take either direct kriging, or kriging of one overlying chosen top plus one kriged thickness, whichever has the smaller predicted error variance. It is reported next to the four so the reader can see that a better thickness method does not change the picture.

### 5. The floor

**Kansas.**

- **Floor A** (used in the pass marks): the same chosen top in two different holes less than 150 m apart, both with a precise position (from footages or GPS). No sealed wells. Median absolute difference **1.83 m** (6 ft), from 35,782 pairs in 12,915 different pairs of holes. This is far more than the 50 pairs needed, so the floor is reliable in the sense of the brief.
- With any position quality: 1.83 m (38,571 pairs). Without flagged elevations: 1.83 m (32,162 pairs).
- **Floor B**: two picks of the same top in the same hole from different sources. Median absolute difference **0.30 m** (1 ft), from 55,738 pairs. 42.1 % of the pairs are exactly equal, which suggests that many "different sources" are copies of one pick. Among pairs that differ, the median is 2.74 m.
- By top, floor A runs from 1.22 m (Heebner, Toronto) to 2.74 m (Simpson). See `results/kansas_floors.csv`.

**Netherlands.**

- **Floor A**: the same chosen top in two different hole systems, picks less than 150 m apart. Median absolute difference **4.19 m**, from 7,139 pairs in 2,470 different pairs of holes. Reliable in the sense of the brief (more than 50 pairs).
- Vertical holes only: 2.88 m (2,063 pairs).
- By top it runs from 2.48 m (Coppershale, Z2 Carbonate) to 15.45 m (Z2 Salt). See `results/netherlands_floors.csv`.
- **Floor B is not available.** The file holds one interpretation per borehole. No hole has the same top from two sources.

**Judgment.** Floor A is the right one for the pass marks, as the brief says. It still contains some real geology (two holes 150 m apart are not the same place) and, in Kansas, the GL and TOPO elevation noise. So it is, if anything, a little high, which makes mark (b) harder to pass. In the Netherlands the floor does not matter for the verdict: the far miss is 29 times larger.

### 6. Results (Kansas, development period)

![Kansas: median absolute error against distance](results/kansas_error_vs_distance.png)

One test item is one chosen top in one test well. 55,194 items in 13,435 wells. Every item had at least one known well with the top.

### Kansas: error by distance, development period

Median absolute error in metres, with the 95 % interval from resampling whole wells in brackets.

| Distance to nearest known well with the top | Items | Wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route |
|---|---|---|---|---|---|---|---|
| all items | 55,194 | 13,435 | 3.05 (3.05-3.05) | 2.98 (2.93-3.03) | 2.53 (2.48-2.56) | 3.24 (3.19-3.31) | 2.46 (2.42-2.51) |
| far (>1 km) | 11,543 | 4,735 | 6.10 (5.79-6.40) | 5.03 (4.85-5.22) | 4.36 (4.21-4.49) | 5.41 (5.18-5.64) | 4.21 (4.07-4.34) |
| same site (<30 m) | 207 | 79 | 1.52 (1.22-2.13) | 2.73 (2.16-3.12) | 1.74 (1.36-2.25) | 2.39 (1.84-3.01) | 1.66 (1.26-2.28) |
| 30 m-1 km | 43,444 | 10,824 | 2.44 (2.44-2.74) | 2.65 (2.59-2.69) | 2.22 (2.18-2.26) | 2.87 (2.81-2.93) | 2.17 (2.14-2.21) |
| 1-5 km | 11,058 | 4,558 | 5.79 (5.49-6.10) | 4.86 (4.70-5.05) | 4.22 (4.09-4.36) | 5.28 (5.07-5.50) | 4.09 (3.97-4.22) |
| 5-20 km | 474 | 364 | 18.90 (16.46-22.25) | 13.88 (12.64-15.95) | 10.68 (9.34-12.32) | 10.89 (9.54-12.76) | 9.80 (8.47-11.49) |
| >20 km | 11 | 11 | 55.47 (20.73-92.96) | 37.57 (24.73-96.06) | 36.27 (18.18-75.98) | 36.27 (18.18-75.98) | 36.27 (18.18-75.98) |

The same medians in feet.

| Distance to nearest known well with the top | Items | Wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route |
|---|---|---|---|---|---|---|---|
| all items | 55,194 | 13,435 | 10.0 | 9.8 | 8.3 | 10.6 | 8.1 |
| far (>1 km) | 11,543 | 4,735 | 20.0 | 16.5 | 14.3 | 17.7 | 13.8 |
| same site (<30 m) | 207 | 79 | 5.0 | 9.0 | 5.7 | 7.8 | 5.4 |
| 30 m-1 km | 43,444 | 10,824 | 8.0 | 8.7 | 7.3 | 9.4 | 7.1 |
| 1-5 km | 11,058 | 4,558 | 19.0 | 16.0 | 13.8 | 17.3 | 13.4 |
| 5-20 km | 474 | 364 | 62.0 | 45.5 | 35.0 | 35.7 | 32.1 |
| >20 km | 11 | 11 | 182.0 | 123.3 | 119.0 | 119.0 | 119.0 |

90th percentile of the absolute error in metres (95 % interval).

| Distance to nearest known well with the top | Items | Wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route |
|---|---|---|---|---|---|---|---|
| all items | 55,194 | 13,435 | 15.2 (14.6-15.5) | 14.3 (13.9-14.6) | 11.0 (10.8-11.3) | 21.2 (20.2-22.1) | 10.7 (10.4-10.9) |
| far (>1 km) | 11,543 | 4,735 | 25.6 (24.4-26.8) | 24.2 (22.8-25.7) | 18.4 (17.5-19.4) | 28.8 (26.7-30.8) | 17.4 (16.6-18.2) |
| same site (<30 m) | 207 | 79 | 9.7 (8.2-14.5) | 9.1 (6.7-11.6) | 8.6 (6.6-11.0) | 14.8 (8.7-24.0) | 8.7 (7.0-11.2) |
| 30 m-1 km | 43,444 | 10,824 | 11.9 (11.3-12.2) | 11.7 (11.3-12.0) | 8.9 (8.7-9.1) | 18.7 (17.7-19.8) | 8.7 (8.5-8.9) |
| 1-5 km | 11,058 | 4,558 | 23.5 (22.3-24.4) | 22.4 (21.2-23.8) | 17.0 (16.3-17.8) | 27.3 (25.5-29.5) | 16.2 (15.6-16.9) |
| 5-20 km | 474 | 364 | 87.1 (64.7-100.6) | 66.3 (52.0-91.0) | 50.7 (39.0-63.3) | 51.7 (42.0-63.3) | 51.1 (39.9-63.3) |
| >20 km | 11 | 11 | 96.3 (63.9-97.5) | 97.9 (42.7-462.1) | 79.6 (37.2-81.3) | 79.6 (37.2-81.3) | 79.6 (37.2-81.3) |

Median signed error in metres (forecast minus actual; negative means the forecast was too deep).

| Distance to nearest known well with the top | Items | Wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route |
|---|---|---|---|---|---|---|---|
| all items | 55,194 | 13,435 | -0.61 | -0.92 | -0.82 | -0.93 | -0.80 |
| far (>1 km) | 11,543 | 4,735 | -0.61 | -0.55 | -0.70 | -0.78 | -0.75 |
| same site (<30 m) | 207 | 79 | 0.00 | -1.32 | -0.49 | -0.73 | -0.40 |
| 30 m-1 km | 43,444 | 10,824 | -0.30 | -0.96 | -0.84 | -0.95 | -0.82 |
| 1-5 km | 11,058 | 4,558 | -0.61 | -0.56 | -0.74 | -0.80 | -0.77 |
| 5-20 km | 474 | 364 | -4.11 | -0.40 | 0.89 | 0.53 | 0.51 |
| >20 km | 11 | 11 | 23.47 | -24.73 | -18.18 | -18.18 | -18.18 |

### Kansas: how often the actual value is inside the 80 % range of method 3

| Distance band | Items | Wells | Actual inside the 80 % range | 95 % interval | Median half width, m |
|---|---|---|---|---|---|
| all items | 55,194 | 13,435 | 77.6 % | 77.1-78.1 % | 5.0 |
| far (>1 km) | 11,543 | 4,735 | 78.4 % | 77.5-79.4 % | 9.1 |
| same site (<30 m) | 207 | 79 | 64.7 % | 56.6-72.7 % | 2.6 |
| 30 m-1 km | 43,444 | 10,824 | 77.4 % | 76.9-78.0 % | 4.4 |
| 1-5 km | 11,058 | 4,558 | 78.3 % | 77.4-79.3 % | 8.8 |
| 5-20 km | 474 | 364 | 81.9 % | 78.2-85.2 % | 25.6 |
| >20 km | 11 | 11 | 63.6 % | 33.3-91.7 % | 64.2 |

### Kansas: median absolute error by top, metres

In a test well each top is one item, so items and wells are the same number here.

| Top (shallow to deep) | Items | n items | n wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route | Floor A, m (pairs) | Best of four / floor A |
|---|---|---|---|---|---|---|---|---|---|---|
| Stone Corral Formation | all items | 5,722 | 5,722 | 1.83 | 1.93 | 1.56 | 1.56 | 1.56 |  |  |
| Stone Corral Formation | far (>1 km) | 744 | 744 | 3.05 | 3.28 | 2.63 | 2.63 | 2.63 | 1.83 (3,560) | 1.44 |
| Topeka Limestone Formation | all items | 4,538 | 4,538 | 3.05 | 3.55 | 2.83 | 3.10 | 2.80 |  |  |
| Topeka Limestone Formation | far (>1 km) | 881 | 881 | 5.49 | 6.39 | 5.27 | 4.98 | 4.66 | 2.13 (1,955) | 2.34 |
| Heebner Shale Member | all items | 9,666 | 9,666 | 2.13 | 2.18 | 1.86 | 2.51 | 1.85 |  |  |
| Heebner Shale Member | far (>1 km) | 1,468 | 1,468 | 4.57 | 3.24 | 2.99 | 3.80 | 2.96 | 1.22 (5,402) | 2.45 |
| Toronto Limestone Member | all items | 4,120 | 4,120 | 2.44 | 2.42 | 2.03 | 2.48 | 1.95 |  |  |
| Toronto Limestone Member | far (>1 km) | 809 | 809 | 4.57 | 3.79 | 3.11 | 3.71 | 2.73 | 1.22 (1,930) | 2.55 |
| Lansing Group | all items | 9,977 | 9,977 | 2.44 | 2.51 | 2.16 | 2.84 | 2.10 |  |  |
| Lansing Group | far (>1 km) | 1,484 | 1,484 | 4.88 | 4.00 | 3.50 | 4.29 | 3.45 | 1.83 (8,032) | 1.91 |
| Kansas City Group | all items | 1,102 | 1,102 | 5.49 | 8.35 | 5.26 | 13.62 | 5.53 |  |  |
| Kansas City Group | far (>1 km) | 415 | 415 | 13.72 | 14.13 | 11.65 | 14.30 | 10.51 | 2.13 (2,038) | 5.46 |
| Marmaton Group | all items | 3,440 | 3,440 | 4.57 | 4.09 | 3.72 | 4.47 | 3.49 |  |  |
| Marmaton Group | far (>1 km) | 1,213 | 1,213 | 7.01 | 5.50 | 5.01 | 5.82 | 4.49 | 2.13 (759) | 2.35 |
| Fort Scott Limestone Formation | all items | 3,115 | 3,115 | 4.27 | 4.07 | 3.56 | 4.38 | 3.54 |  |  |
| Fort Scott Limestone Formation | far (>1 km) | 1,074 | 1,074 | 7.01 | 6.12 | 5.53 | 6.55 | 5.17 | 2.13 (1,689) | 2.59 |
| Cherokee Group | all items | 3,269 | 3,269 | 4.57 | 3.85 | 3.59 | 4.96 | 3.49 |  |  |
| Cherokee Group | far (>1 km) | 1,008 | 1,008 | 7.32 | 5.50 | 4.86 | 6.72 | 5.07 | 2.44 (1,147) | 1.99 |
| Mississippian System | all items | 5,929 | 5,929 | 4.88 | 4.47 | 3.85 | 6.53 | 3.88 |  |  |
| Mississippian System | far (>1 km) | 1,798 | 1,798 | 7.62 | 6.81 | 5.43 | 7.27 | 5.38 | 2.44 (2,828) | 2.23 |
| Simpson Group | all items | 597 | 597 | 5.18 | 4.83 | 3.70 | 13.54 | 3.70 |  |  |
| Simpson Group | far (>1 km) | 182 | 182 | 9.52 | 8.08 | 5.78 | 27.75 | 5.80 | 2.74 (975) | 2.11 |
| Arbuckle Group | all items | 3,719 | 3,719 | 4.57 | 5.16 | 4.48 | 5.05 | 4.08 |  |  |
| Arbuckle Group | far (>1 km) | 467 | 467 | 10.97 | 8.68 | 7.45 | 11.19 | 6.91 | 2.44 (5,467) | 3.05 |

### Kansas: the floor

| Floor | Pairs | Different hole pairs / holes | Median absolute difference, m | 90th percentile, m | Share exactly zero |
|---|---|---|---|---|---|
| A: two holes under 150 m apart, both positions precise (used in pass marks) | 35,782 | 12,915 | 1.83 | 9.45 | 5.5 % |
| A-all: two holes under 150 m apart, any position quality | 38,571 | 14,416 | 1.83 | 9.75 | 5.7 % |
| A-clean: as A, both holes in the unflagged side set | 32,162 | 10,626 | 1.83 | 9.14 | 5.6 % |
| B: two picks of one top in one hole from different sources | 55,738 | 13,837 | 0.30 | 14.02 | 42.1 % |

### Kansas: side results

No waiting time (known wells = finished before the test well was spudded). Median absolute error, metres (95 % interval).

| Distance to nearest known well with the top | Items | Wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route |
|---|---|---|---|---|---|---|---|
| all items | 55,194 | 13,435 | 2.74 (2.74-2.74) | 2.79 (2.75-2.84) | 2.32 (2.29-2.35) | 3.06 (3.00-3.12) | 2.27 (2.23-2.30) |
| far (>1 km) | 8,752 | 3,761 | 6.10 (5.79-6.40) | 5.04 (4.81-5.24) | 4.37 (4.19-4.53) | 5.43 (5.16-5.66) | 4.21 (4.06-4.37) |
| same site (<30 m) | 233 | 91 | 1.52 (1.22-2.13) | 2.67 (2.14-3.04) | 1.66 (1.29-2.21) | 2.38 (1.72-3.01) | 1.55 (1.16-2.17) |
| 30 m-1 km | 46,209 | 11,535 | 2.44 (2.44-2.44) | 2.54 (2.51-2.59) | 2.10 (2.07-2.13) | 2.77 (2.71-2.83) | 2.06 (2.02-2.09) |
| 1-5 km | 8,389 | 3,624 | 5.79 (5.49-6.10) | 4.86 (4.65-5.08) | 4.24 (4.07-4.41) | 5.30 (5.08-5.56) | 4.09 (3.94-4.24) |
| 5-20 km | 354 | 260 | 19.81 (16.15-22.56) | 13.41 (11.27-14.93) | 10.44 (9.10-12.34) | 10.50 (8.90-12.76) | 9.76 (8.44-11.70) |
| >20 km | 9 | 9 | 55.47 (17.98-131.06) | 34.85 (15.95-100.08) | 24.28 (9.56-80.33) | 24.28 (9.56-80.33) | 24.28 (9.56-80.33) |

Side set: holes without an elevation flag (no GL or TOPO) and with a precise position, as test wells and as known wells (200 resamples). Median absolute error, metres (95 % interval).

| Distance to nearest known well with the top | Items | Wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route |
|---|---|---|---|---|---|---|---|
| all items | 51,397 | 11,554 | 2.74 (2.74-3.05) | 2.89 (2.85-2.95) | 2.44 (2.40-2.49) | 3.15 (3.08-3.21) | 2.38 (2.34-2.42) |
| far (>1 km) | 10,232 | 3,799 | 5.79 (5.78-6.10) | 4.88 (4.70-5.12) | 4.22 (4.09-4.38) | 5.30 (5.09-5.55) | 4.06 (3.92-4.21) |
| same site (<30 m) | 184 | 64 | 1.52 (0.91-2.13) | 2.47 (1.96-2.97) | 1.66 (1.10-2.22) | 2.22 (1.59-2.76) | 1.51 (1.10-2.07) |
| 30 m-1 km | 40,981 | 9,702 | 2.44 (2.44-2.44) | 2.59 (2.54-2.63) | 2.17 (2.13-2.21) | 2.80 (2.72-2.86) | 2.12 (2.08-2.16) |
| 1-5 km | 9,721 | 3,591 | 5.49 (5.49-5.79) | 4.65 (4.49-4.85) | 4.09 (3.93-4.21) | 5.12 (4.96-5.40) | 3.92 (3.77-4.06) |
| 5-20 km | 476 | 322 | 21.79 (18.27-24.38) | 15.10 (12.47-16.39) | 9.56 (8.56-11.13) | 9.86 (8.58-11.24) | 9.18 (8.26-10.57) |
| >20 km | 35 | 33 | 51.21 (30.02-58.85) | 37.57 (20.16-52.80) | 33.82 (15.55-47.64) | 33.82 (15.55-47.64) | 33.82 (15.55-47.64) |

### Kansas: sealed period, counts only

| Count of | Number |
|---|---|
| sealed wells | 13442 |
| sealed items (chosen top reported in a sealed well) | 64634 |
| sealed far items (nearest known well with the top more than 1 km away) | 14479 |
| sealed items with no known well at all for the top | 0 |
| sealed wells with at least one far item | 4517 |
| sealed items, nearest known well same site (<30 m) | 261 |
| sealed items, nearest known well 30 m-1 km | 49894 |
| sealed items, nearest known well 1-5 km | 14075 |
| sealed items, nearest known well 5-20 km | 400 |
| sealed items, nearest known well >20 km | 4 |

### Kansas: chosen tops

| Order (top down) | Top | Holes drilled before the test years that report it |
|---|---|---|
| 1 | Stone Corral Formation | 68,311 |
| 2 | Topeka Limestone Formation | 43,290 |
| 3 | Heebner Shale Member | 92,941 |
| 4 | Toronto Limestone Member | 50,085 |
| 5 | Lansing Group | 109,294 |
| 6 | Kansas City Group | 48,548 |
| 7 | Marmaton Group | 27,797 |
| 8 | Fort Scott Limestone Formation | 24,994 |
| 9 | Cherokee Group | 33,711 |
| 10 | Mississippian System | 56,548 |
| 11 | Simpson Group | 22,841 |
| 12 | Arbuckle Group | 54,403 |

Next three, not chosen: Winfield Limestone Formation (21,124); Chase Group (20,352); Viola Limestone Formation (19,529).

### Kansas: cleaning steps and wells left

| Step | Well records left | Holes left | Detail |
|---|---|---|---|
| 0. all records in the wells file | 519,691 | 474,876 | 356 holes merged into another hole as duplicates (same position, elevation, depth, spud date) |
| 1. records with at least one top row | 196,743 | 194,621 | 2135525 top rows |
| 2. top depth present, above 0 and not over 12,000 ft | 195,530 | 193,453 | 2052549 top rows left. Rows with no top depth (base only), zero or negative depth, or a depth deeper than any Kansas well are dropped. |
| 3. top not deeper than the well's total depth plus 50 ft | 195,003 | 192,950 | 2035617 top rows left. A pick below the bottom of the hole is a data error. |
| 4. elevation and its reference present, and the same in the wells file and the tops file | 194,989 | 192,936 | 2035512 top rows left. 0 top rows had a different elevation or reference in the two files. |
| 5. usable position | 194,802 | 192,752 | 2034482 top rows left. Dropped: position given only as the centre of the section (up to about 1 km off), unknown source, or outside Kansas. |
| 6. not horizontal or deviated | 194,072 | 192,061 | 2030207 top rows left. Dropped: records whose API number carries a sidetrack code (digits 11-12 not 00, the KGS's own rule for its horizontal-well list) or whose comment mentions horizontal, directional, deviated, slant, sidetrack, whipstock, BHL or TVD. The file gives no true vertical depth or top position for them. |
| 7. one elevation per hole and top | 193,417 | 192,045 | 1824531 hole-top values. Picks of one top in one record from several sources: the median. 8153 record-top groups dropped because their picks disagree by more than 100 ft. Records of one hole (re-entries, workovers; same first 10 digits of the API number): the earliest finished record that reports the top is used (14120 record-top values were in holes with more than one record for that top). |
| 8. holes in the analysis | 193,417 | 192,045 | 22940 holes flagged for elevation (GL or TOPO), 10207 flagged for position from quarter calls, 3555 holes whose records sit more than 30 m apart. Flagged holes are kept. |
| 9. holes with a valid first spud date |  | 189,252 | spud before 2000: 158325; can be a test well (every drilled record spudded in 2000 or later, no completion or plugging date before 2000): 30258. Dates outside 1860 to 9 Oct 2026 were treated as missing: {'SPUD': 5, 'COMPLETION': 9, 'PLUGGING': 20}. |
| 10. holes whose tops can serve as known wells (finish date present) |  | 190,931 | Finish date = completion date; the spud date if it is later; the plugging date if there is no completion date. Holes with none of these are never used as known wells. |

### Kansas: settings (all set on wells drilled before the test years)

| Top | Wells used | Variogram power | Nugget ratio r |
|---|---|---|---|
| Stone Corral Formation | 24 | 1.5 | 0.3 |
| Topeka Limestone Formation | 24 | 1.5 | 0.1 |
| Heebner Shale Member | 24 | 1.0 | 0.03 |
| Toronto Limestone Member | 24 | 0.5 | 0.03 |
| Lansing Group | 24 | 1.0 | 0.1 |
| Kansas City Group | 24 | 1.0 | 0.1 |
| Marmaton Group | 24 | 1.0 | 0.01 |
| Fort Scott Limestone Formation | 24 | 1.0 | 0.1 |
| Cherokee Group | 24 | 1.0 | 0.03 |
| Mississippian System | 24 | 0.5 | 0.3 |
| Simpson Group | 24 | 1.0 | 0.1 |
| Arbuckle Group | 24 | 1.0 | 0.1 |

Method 2 uses the 8 nearest known wells. Outlier screening of neighbours: on (drop a neighbour more than max(6 x 1.4826 x MAD, 3 m) off the local plane). Thickness kriging: 16 nearest wells, power 0.5, nugget ratio 0.03, constant local mean. Thickness chain: fewest layers, support = at least 5 known wells within 10 km. Multiplier on the 80 % range: 0.998 (coverage before the multiplier on the pre-test-year check: 80.1 %).

Check on wells drilled before the test years (4,000 sampled wells, same date rule; 80 % range of method 3 held the actual value 79.7 % of the time):

| Method | Items | Median abs error, m | 90th percentile, m | Far items | Median abs error far, m |
|---|---|---|---|---|---|
| 1 Nearest | 17,131 | 3.35 | 14.9 | 4,143 | 6.10 |
| 2 Plane | 17,131 | 3.22 | 14.3 | 4,143 | 4.71 |
| 3 Kriging | 17,131 | 2.63 | 11.2 | 4,143 | 4.29 |
| 4 Thickness | 17,131 | 3.47 | 18.5 | 4,143 | 5.06 |
| (side) 4b best route | 17,131 | 2.57 | 10.7 | 4,143 | 4.11 |

Other facts from these tables:

- **Forecasts are too deep by about 0.8 m on the median** (kriging: -0.82 m). New wells come in slightly higher than the map from older wells says.
- **No waiting time** changes little: kriging goes from 2.53 m to 2.32 m on all items and stays at 4.37 m on far items. With no waiting time fewer items are far (8,752 against 11,543).
- **Without flagged wells** (no GL or TOPO elevation, no quarter-call position) the far miss of kriging is 4.22 m and floor A is 1.83 m: the same picture.
- **Sealed period, counts only:** 13,442 wells, 64,634 items, 14,479 far items in 4,517 wells.

**Judgment.** The steady bias is what one would expect if operators drill where they hope the layer is high. A method that knew this could gain a few tenths of a metre. The pass in Kansas is real but narrow in metres: a new method has to beat 4.36 m on far items and cannot go below about 1.83 m.

### 6b. Results (Netherlands, development period)

![Netherlands: median absolute error against distance](results/netherlands_error_vs_distance.png)

2,587 items in 535 wells. Every item had at least one known well with the top.

### Netherlands: error by distance, development period

Median absolute error in metres, with the 95 % interval from resampling whole wells in brackets.

| Distance to nearest known well with the top | Items | Wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route |
|---|---|---|---|---|---|---|---|
| all items | 2,587 | 535 | 89.26 (76.80-106.55) | 101.00 (87.20-116.06) | 78.72 (67.98-91.79) | 98.89 (84.02-111.72) | 76.50 (66.16-90.72) |
| far (>1 km) | 1,891 | 371 | 148.97 (131.51-174.46) | 158.91 (139.50-188.80) | 122.39 (107.95-141.77) | 133.06 (117.27-151.24) | 122.84 (107.78-142.33) |
| same site (<30 m) | 10 | 6 | 3.29 (2.08-9.97) | 10.44 (2.07-36.38) | 6.63 (1.70-13.46) | 19.92 (1.74-42.77) | 6.63 (1.74-16.40) |
| 30 m-1 km | 686 | 229 | 15.95 (12.47-22.71) | 21.48 (17.32-27.25) | 16.35 (13.20-20.36) | 23.97 (18.96-31.65) | 16.16 (13.09-20.31) |
| 1-5 km | 847 | 192 | 86.20 (72.81-101.94) | 95.72 (84.99-116.84) | 78.49 (64.15-91.83) | 93.22 (76.71-104.17) | 75.63 (63.83-91.66) |
| 5-20 km | 972 | 223 | 220.02 (192.95-274.12) | 268.03 (214.73-326.01) | 190.70 (161.81-213.93) | 191.60 (168.04-214.82) | 189.22 (160.64-211.25) |
| >20 km | 72 | 28 | 254.16 (205.16-408.53) | 236.56 (117.12-328.78) | 217.28 (129.94-307.07) | 217.28 (129.94-307.07) | 217.28 (129.94-307.07) |

90th percentile of the absolute error in metres (95 % interval).

| Distance to nearest known well with the top | Items | Wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route |
|---|---|---|---|---|---|---|---|
| all items | 2,587 | 535 | 457.4 (417.9-528.1) | 626.5 (535.7-735.5) | 395.6 (356.9-439.0) | 419.8 (377.7-461.3) | 393.4 (355.7-437.5) |
| far (>1 km) | 1,891 | 371 | 543.7 (477.9-613.7) | 776.7 (662.4-887.1) | 463.3 (418.3-513.6) | 474.3 (428.5-524.7) | 463.3 (416.7-506.2) |
| same site (<30 m) | 10 | 6 | 18.5 (2.7-46.4) | 44.4 (5.1-70.2) | 19.5 (5.8-35.9) | 45.4 (24.8-53.0) | 20.4 (6.1-44.6) |
| 30 m-1 km | 686 | 229 | 95.6 (74.0-134.5) | 125.0 (106.8-142.8) | 92.6 (74.3-117.0) | 161.0 (134.3-211.7) | 92.1 (70.5-123.4) |
| 1-5 km | 847 | 192 | 331.5 (300.3-420.9) | 389.6 (349.6-468.3) | 286.5 (247.7-339.9) | 323.4 (272.6-379.9) | 290.2 (253.1-351.7) |
| 5-20 km | 972 | 223 | 645.0 (567.0-792.9) | 1011.9 (842.7-1291.3) | 558.2 (499.1-638.3) | 571.8 (503.0-639.9) | 557.4 (497.5-638.3) |
| >20 km | 72 | 28 | 658.5 (451.4-769.9) | 1030.9 (525.1-2780.8) | 554.3 (341.8-683.1) | 554.3 (341.8-683.1) | 554.3 (341.8-683.1) |

Median signed error in metres (forecast minus actual; negative means the forecast was too deep).

| Distance to nearest known well with the top | Items | Wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route |
|---|---|---|---|---|---|---|---|
| all items | 2,587 | 535 | 20.90 | 14.42 | 10.60 | 21.29 | 11.62 |
| far (>1 km) | 1,891 | 371 | 62.37 | 47.62 | 42.51 | 56.81 | 43.73 |
| same site (<30 m) | 10 | 6 | -2.35 | -2.32 | -2.90 | -19.92 | -3.54 |
| 30 m-1 km | 686 | 229 | -1.06 | 0.77 | -2.08 | -1.41 | -2.05 |
| 1-5 km | 847 | 192 | 35.80 | 36.30 | 23.75 | 34.86 | 23.66 |
| 5-20 km | 972 | 223 | 119.81 | 76.65 | 93.75 | 96.04 | 96.96 |
| >20 km | 72 | 28 | 100.45 | -1.47 | 29.14 | 29.14 | 29.14 |

### Netherlands: how often the actual value is inside the 80 % range of method 3

| Distance band | Items | Wells | Actual inside the 80 % range | 95 % interval | Median half width, m |
|---|---|---|---|---|---|
| all items | 2,587 | 535 | 74.2 % | 71.2-77.1 % | 164.2 |
| far (>1 km) | 1,891 | 371 | 72.4 % | 68.7-76.1 % | 220.3 |
| same site (<30 m) | 10 | 6 | 100.0 % | 100.0-100.0 % | 39.1 |
| 30 m-1 km | 686 | 229 | 78.6 % | 73.9-82.3 % | 55.4 |
| 1-5 km | 847 | 192 | 70.1 % | 64.7-75.7 % | 143.6 |
| 5-20 km | 972 | 223 | 72.9 % | 67.6-77.9 % | 317.1 |
| >20 km | 72 | 28 | 93.1 % | 83.9-98.5 % | 608.3 |

### Netherlands: median absolute error by top, metres

In a test well each top is one item, so items and wells are the same number here.

| Top (shallow to deep) | Items | n items | n wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route | Floor A, m (pairs) | Best of four / floor A |
|---|---|---|---|---|---|---|---|---|---|---|
| NLLFC Landen Clay Member | all items | 170 | 170 | 55.42 | 56.13 | 43.73 | 43.73 | 43.73 |  |  |
| NLLFC Landen Clay Member | far (>1 km) | 136 | 136 | 86.16 | 77.27 | 66.06 | 66.06 | 66.06 | 4.08 (325) | 16.19 |
| KNGLU Upper Holland Marl Member | all items | 292 | 292 | 103.34 | 111.83 | 91.24 | 91.70 | 90.77 |  |  |
| KNGLU Upper Holland Marl Member | far (>1 km) | 209 | 209 | 193.41 | 218.12 | 169.97 | 166.00 | 169.97 | 7.83 (710) | 21.19 |
| KNGLM Middle Holland Claystone Member | all items | 273 | 273 | 108.33 | 134.04 | 93.20 | 107.24 | 96.22 |  |  |
| KNGLM Middle Holland Claystone Member | far (>1 km) | 196 | 196 | 195.70 | 232.89 | 158.89 | 180.79 | 177.76 | 6.31 (938) | 25.20 |
| KNGLL Lower Holland Marl Member | all items | 278 | 278 | 106.64 | 146.88 | 86.63 | 129.11 | 91.37 |  |  |
| KNGLL Lower Holland Marl Member | far (>1 km) | 200 | 200 | 190.16 | 237.91 | 161.23 | 186.55 | 165.84 | 5.64 (845) | 28.59 |
| RNRO1 Main Röt Evaporite Member | all items | 229 | 229 | 19.45 | 30.53 | 25.80 | 26.20 | 25.68 |  |  |
| RNRO1 Main Röt Evaporite Member | far (>1 km) | 97 | 97 | 240.94 | 207.40 | 172.48 | 169.79 | 172.48 | 2.77 (503) | 61.30 |
| RNSOC Solling Claystone Member | all items | 198 | 198 | 52.35 | 77.11 | 50.87 | 59.53 | 53.81 |  |  |
| RNSOC Solling Claystone Member | far (>1 km) | 104 | 104 | 238.70 | 206.50 | 179.47 | 173.28 | 173.28 | 3.00 (367) | 57.76 |
| ZEZ2H Z2 Salt Member | all items | 149 | 149 | 179.47 | 248.95 | 138.59 | 146.96 | 137.53 |  |  |
| ZEZ2H Z2 Salt Member | far (>1 km) | 119 | 119 | 218.04 | 289.00 | 187.49 | 178.27 | 167.66 | 15.45 (573) | 11.54 |
| ZEZ2A Z2 Basal Anhydrite Member | all items | 200 | 200 | 92.59 | 97.07 | 89.86 | 113.87 | 89.19 |  |  |
| ZEZ2A Z2 Basal Anhydrite Member | far (>1 km) | 167 | 167 | 119.67 | 118.99 | 105.49 | 115.77 | 105.49 | 2.83 (579) | 37.28 |
| ZEZ2C Z2 Carbonate Member | all items | 207 | 207 | 91.47 | 104.11 | 86.91 | 109.66 | 80.81 |  |  |
| ZEZ2C Z2 Carbonate Member | far (>1 km) | 171 | 171 | 118.94 | 125.41 | 105.44 | 115.69 | 101.53 | 2.48 (579) | 42.52 |
| ZEZ1W Z1 Anhydrite Member | all items | 180 | 180 | 96.56 | 111.74 | 85.33 | 119.20 | 71.96 |  |  |
| ZEZ1W Z1 Anhydrite Member | far (>1 km) | 149 | 149 | 121.51 | 134.03 | 107.28 | 125.39 | 107.37 | 2.53 (573) | 42.40 |
| ZEZ1C Z1 Carbonate Member | all items | 202 | 202 | 93.16 | 104.54 | 85.24 | 106.64 | 76.64 |  |  |
| ZEZ1C Z1 Carbonate Member | far (>1 km) | 170 | 170 | 123.42 | 124.20 | 99.17 | 112.76 | 94.49 | 2.93 (577) | 33.85 |
| ZEZ1K Coppershale Member | all items | 209 | 209 | 83.48 | 95.41 | 82.86 | 106.52 | 76.23 |  |  |
| ZEZ1K Coppershale Member | far (>1 km) | 173 | 173 | 109.52 | 114.02 | 101.15 | 115.44 | 99.13 | 2.48 (570) | 40.79 |

### Netherlands: the floor

| Floor | Pairs | Different hole pairs / holes | Median absolute difference, m | 90th percentile, m | Share exactly zero |
|---|---|---|---|---|---|
| A: two holes under 150 m apart, both positions precise (used in pass marks) | 7,139 | 2,470 | 4.19 | 20.76 | 0.1 % |
| A-all: two holes under 150 m apart, any position quality | 7,139 | 2,470 | 4.19 | 20.76 | 0.1 % |
| A-clean: as A, both holes in the unflagged side set | 2,063 | 678 | 2.88 | 14.85 | 0.0 % |

### Netherlands: side results

No waiting time (known wells = finished before the test well was spudded). Median absolute error, metres (95 % interval).

| Distance to nearest known well with the top | Items | Wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route |
|---|---|---|---|---|---|---|---|
| all items | 2,587 | 535 | 60.44 (49.62-69.76) | 65.44 (57.45-76.58) | 54.57 (47.78-63.16) | 74.21 (64.00-82.22) | 54.57 (47.22-62.14) |
| far (>1 km) | 1,652 | 323 | 115.72 (99.96-132.99) | 120.28 (104.55-135.82) | 94.07 (83.73-104.74) | 104.63 (91.07-117.56) | 93.90 (83.58-103.93) |
| same site (<30 m) | 18 | 12 | 2.49 (0.87-3.85) | 2.03 (1.20-3.65) | 2.79 (0.88-5.79) | 3.09 (0.88-34.96) | 2.33 (0.65-5.79) |
| 30 m-1 km | 917 | 271 | 16.15 (13.11-21.00) | 18.75 (14.58-23.46) | 14.69 (11.63-18.10) | 26.64 (20.98-33.49) | 14.09 (11.60-17.46) |
| 1-5 km | 1,048 | 225 | 88.65 (74.98-100.41) | 97.23 (84.99-116.84) | 76.21 (68.28-88.86) | 88.82 (77.51-104.45) | 79.13 (68.51-91.19) |
| 5-20 km | 571 | 147 | 180.50 (151.16-221.81) | 172.52 (139.60-202.64) | 136.46 (114.26-165.03) | 134.82 (113.56-160.56) | 132.90 (113.42-159.08) |
| >20 km | 33 | 11 | 237.36 (132.93-574.96) | 207.40 (70.27-445.80) | 97.19 (32.32-237.27) | 97.19 (32.32-237.27) | 97.19 (32.32-237.27) |

Side set: vertical holes only, without a reference-height flag, as test wells and as known wells (200 resamples). Median absolute error, metres (95 % interval).

| Distance to nearest known well with the top | Items | Wells | 1 Nearest | 2 Plane | 3 Kriging | 4 Thickness | (side) 4b best route |
|---|---|---|---|---|---|---|---|
| all items | 563 | 172 | 91.85 (68.66-130.37) | 132.23 (71.02-191.60) | 93.28 (60.10-133.93) | 98.44 (58.42-136.57) | 93.28 (60.10-133.93) |
| far (>1 km) | 402 | 89 | 195.15 (156.09-243.49) | 250.89 (204.27-278.57) | 192.84 (141.97-230.37) | 193.50 (137.05-235.77) | 192.84 (142.13-230.40) |
| same site (<30 m) | 0 | 0 |  |  |  |  |  |
| 30 m-1 km | 161 | 99 | 6.55 (5.46-7.61) | 4.68 (3.18-6.13) | 4.51 (3.93-5.51) | 4.27 (3.74-5.83) | 4.02 (3.40-5.26) |
| 1-5 km | 75 | 17 | 77.97 (60.11-109.91) | 88.01 (43.65-129.29) | 60.66 (52.44-98.44) | 55.01 (34.15-113.31) | 60.66 (52.44-98.44) |
| 5-20 km | 259 | 70 | 237.09 (201.42-287.80) | 274.23 (229.63-291.29) | 203.63 (167.43-248.56) | 203.91 (173.55-250.76) | 203.63 (167.43-248.54) |
| >20 km | 68 | 21 | 187.68 (95.53-370.33) | 354.99 (222.62-553.31) | 308.00 (152.63-361.61) | 308.00 (152.63-361.61) | 308.00 (152.63-361.61) |

### Netherlands: sealed period, counts only

| Count of | Number |
|---|---|
| sealed wells | 535 |
| sealed items (chosen top reported in a sealed well) | 2229 |
| sealed far items (nearest known well with the top more than 1 km away) | 1158 |
| sealed items with no known well at all for the top | 0 |
| sealed wells with at least one far item | 342 |
| sealed items, nearest known well same site (<30 m) | 243 |
| sealed items, nearest known well 30 m-1 km | 828 |
| sealed items, nearest known well 1-5 km | 830 |
| sealed items, nearest known well 5-20 km | 317 |
| sealed items, nearest known well >20 km | 11 |

### Netherlands: chosen tops

| Order (top down) | Top | Holes drilled before the test years that report it |
|---|---|---|
| 1 | NLLFC Landen Clay Member | 860 |
| 2 | KNGLU Upper Holland Marl Member | 1,670 |
| 3 | KNGLM Middle Holland Claystone Member | 1,685 |
| 4 | KNGLL Lower Holland Marl Member | 1,306 |
| 5 | RNRO1 Main Röt Evaporite Member | 864 |
| 6 | RNSOC Solling Claystone Member | 844 |
| 7 | ZEZ2H Z2 Salt Member | 843 |
| 8 | ZEZ2A Z2 Basal Anhydrite Member | 1,022 |
| 9 | ZEZ2C Z2 Carbonate Member | 1,049 |
| 10 | ZEZ1W Z1 Anhydrite Member | 980 |
| 11 | ZEZ1C Z1 Carbonate Member | 1,009 |
| 12 | ZEZ1K Coppershale Member | 1,123 |

Next three, not chosen: ZEZ3G Grey Salt Clay Member (843); RNMUL Lower Muschelkalk Member (836); ZEZ3C Z3 Carbonate Member (829).

### Netherlands: which level of the naming scheme has the most data

| Level | Hole-top values | In holes finished before the test years | Different units | Chosen |
|---|---|---|---|---|
| member | 60,342 | 39,880 | 209 | yes |
| formation | 45,717 | 29,690 | 93 |  |
| group | 22,740 | 14,683 | 18 |  |

### Netherlands: cleaning steps and wells left

| Step | Well records left | Holes left | Detail |
|---|---|---|---|
| 0. all boreholes in the NLOG list | 6,739 | 6,739 | 1631 of them are sidetracks. Shape: {'Deviated': 3591, 'Vertical': 2749, 'Horizontal': 387}. |
| 1. wellbores with lithostratigraphy rows | 6,517 | 6,517 | 111651 rows |
| 2. row is a named member, formation, subgroup or group | 6,410 | 6,267 | 103643 rows left. Dropped: 'NOT INTERPRETED', fault rows, the North Sea Supergroup and informal units (Zechstein salt, caprock, igneous rock). |
| 3. true vertical depth and position of the top present | 6,396 | 6,251 | 103496 rows left.  |
| 4. the top is a drilled boundary under an interpreted interval | 6,304 | 6,125 | 98143 rows left. Dropped: the first interval of each wellbore (its top is the surface or the start of the description), and tops under a 'NOT INTERPRETED' interval, a fault row or a gap. |
| 5. top not at a kick-off point, not a fault, not marked uncertain | 6,293 | 6,097 | 97156 rows left. Dropped: anomaly codes UKO, UF and U on the upper boundary. Tops that are unconformities (UU) are kept. |
| 6. each pick once | 6,095 | 6,097 | 83249 rows left. 13907 copies removed: a pick above a kick-off point appears in the table of the mother borehole and of each sidetrack. |
| 7. borehole found in the borehole list | 6,092 | 6,092 | 83193 rows left. The borehole that drilled the top, and the mother borehole of its system, must be in the list. |
| 8. one level of the naming scheme: member | 5,471 | 5,471 | 60342 hole-top values. Hole-top values per level (all / finished before 1990): member 60342 / 39880; formation 45717 / 29690; group 22740 / 14683. The level with the most values in holes finished before 1990 is used. 407 hole-unit pairs had the unit more than once in one hole (fault repeats and the like): the shallowest is used. |
| 9. holes in the analysis (a hole = a borehole or sidetrack with tops it drilled itself) | 5,471 | 5,471 | 2109 vertical, 3084 deviated, 278 horizontal. Deviated and horizontal holes are kept, because the file gives the true vertical depth and the position of every top. 118 holes flagged because the reference height differs by more than 1 m between the two files (flagged, kept). Check of the vertical reference: in 6308 wellbores the first interval starts at 0 m along hole; there the vertical depth should be minus the reference height of the borehole list. It agrees within 0.05 m in 66.1 % and within 1 m in 97.5 %. |
| 10. holes with valid drilling dates |  | 5,469 | finished before 1990: 3682; can be a test well (mother borehole, not a sidetrack, finished in 1990 or later): 1251. 94 boreholes in the list had dates outside 1900 to 23 Sep 2026 or an end before the start; their dates were treated as missing. |

### Netherlands: settings (all set on wells drilled before the test years)

| Top | Wells used | Variogram power | Nugget ratio r |
|---|---|---|---|
| NLLFC Landen Clay Member | 24 | 1.0 | 0.1 |
| KNGLU Upper Holland Marl Member | 12 | 1.5 | 0.1 |
| KNGLM Middle Holland Claystone Member | 12 | 1.5 | 0.3 |
| KNGLL Lower Holland Marl Member | 12 | 1.5 | 0.3 |
| RNRO1 Main Röt Evaporite Member | 24 | 0.5 | 0.01 |
| RNSOC Solling Claystone Member | 24 | 1.0 | 0.3 |
| ZEZ2H Z2 Salt Member | 12 | 1.0 | 0.03 |
| ZEZ2A Z2 Basal Anhydrite Member | 24 | 1.5 | 3.0 |
| ZEZ2C Z2 Carbonate Member | 12 | 1.5 | 0.1 |
| ZEZ1W Z1 Anhydrite Member | 24 | 1.0 | 0.01 |
| ZEZ1C Z1 Carbonate Member | 12 | 1.5 | 1.0 |
| ZEZ1K Coppershale Member | 12 | 1.5 | 0.3 |

Method 2 uses the 4 nearest known wells. Outlier screening of neighbours: off (drop a neighbour more than max(6 x 1.4826 x MAD, 3 m) off the local plane). Thickness kriging: 8 nearest wells, power 0.5, nugget ratio 0.03, constant local mean. Thickness chain: fewest layers, support = at least 5 known wells within 10 km. Multiplier on the 80 % range: 1.028 (coverage before the multiplier on the pre-test-year check: 79.0 %).

Check on wells drilled before the test years (1,835 sampled wells, same date rule; 80 % range of method 3 held the actual value 80.0 % of the time):

| Method | Items | Median abs error, m | 90th percentile, m | Far items | Median abs error far, m |
|---|---|---|---|---|---|
| 1 Nearest | 7,103 | 78.43 | 467.2 | 5,372 | 129.85 |
| 2 Plane | 7,103 | 86.96 | 567.4 | 5,372 | 134.54 |
| 3 Kriging | 7,103 | 64.02 | 385.7 | 5,372 | 102.80 |
| 4 Thickness | 7,103 | 75.60 | 395.5 | 5,372 | 113.30 |
| (side) 4b best route | 7,103 | 63.05 | 382.7 | 5,372 | 100.79 |

Other facts from these tables:

- **Forecasts are too shallow on far items**: the median signed error of kriging is +42.5 m there (forecast higher than the actual top). Within 1 km there is no clear bias (-2.1 m).
- **No waiting time** helps more than in Kansas: kriging goes from 78.7 m to 54.6 m on all items and from 122.4 m to 94.1 m on far items.
- **Vertical holes only** (89 far wells): the far miss of kriging is 192.8 m and floor A is 2.88 m. The vertical test wells are mostly far step-outs.
- **Sealed period, counts only:** 535 wells, 2,229 items, 1,158 far items in 342 wells (by surface position).

**Judgment.** The Dutch far miss is large because the geology is rough (salt, faults, inverted basins) and wells are far apart: over half of the far items are more than 5 km from the nearest known well with the top. The bias suggests that old wells sit on highs and later wells step off them. The pass on mark (b) is beyond doubt. The pass on mark (a) is thin: 371 and 342 against a need of 300.

### 7. Checks

- **Date-rule test** (`src/check_date_rule.py`, run by the one command). It reads the dates again from the input tables with separate code and checks every known well behind every forecast (main run and no-waiting-time run; five forecasts per item: the four methods and side method 4b). Output: `results/date_rule_check.txt`.
  - Kansas: 551,940 forecasts checked, 11,296,020 uses of a known well checked, **0 violations**.
  - Netherlands: 25,870 forecasts checked, 329,706 uses of a known well checked, **0 violations**.
- **Spot-check sheets:** `results/kansas_spot_check.csv` and `results/netherlands_spot_check.csv`. 20 random test items each. For each: the test well, its spud date, the latest finish date allowed, every known well used by each method with its finish date, distance and value, each forecast and the actual value. For methods 2 to 4 the sheet lists all neighbours taken; in Kansas a few of them may have been left out by the outlier screen.
- **Rerun:** `./run.sh` goes from `data/` to `results/` in about 6 minutes for both countries. I ran each country twice; every result file had the same sha256 both times (`hashes.txt`). After the code was extended for the Netherlands I ran Kansas again: every Kansas number was unchanged.

### 8. What I could not do or verify

- I could not check what each top depth is measured from. The file does not say. See section 2.
- I could not check deviation beyond the API code and the comments. Some deviated wells without that code may remain. Kansas wells are mostly vertical.
- I did not check any pick against a log. A wrong pick in a test well counts as a miss of the method.
- "Known" is decided by the finish date of the well, as the brief says. I did not check when each pick was made or released. Some picks on old wells were made later by KGS projects. They are treated as known from the well's finish date.
- The sealed period was not scored. I cannot say whether its errors look like the development period.
- Netherlands: I could not check when each interpretation was made. The file gives a source code per row (the largest are EINDSLIP, RGD1997, ONSHORE2004, GE-KRT2018V3). The NLOG description does not explain the codes. Going only by the year in the code's name, 60 % of all rows, and 76 % of the rows of holes finished before 1990, were interpreted more than 5 years after the hole was finished. Such picks may have been made with later wells in view, including test wells. The date rule in this test goes by when the hole was finished, as the brief says, so it does not catch this.
- Netherlands: each top is forecast at the place where the test well crossed it. Before drilling only the planned path is known. For a deviated well the true crossing point depends on the depth being forecast. I did not measure this effect.
- Netherlands: the sealed far-well count (342) uses surface positions. With top positions it could be somewhat different. I did not compute that, so as not to touch sealed depths.
- Netherlands: I used the brief's 5-year rule. I did not check each well's real release date.
- The 95 % intervals resample wells. They do not include the uncertainty of the floor or of the settings.
- Wells in one field are not independent. The well-resampled intervals are probably too narrow.

### 9. Where the work was blocked

- **Branch.** This environment only lets me push to `claude/kind-mendel-aqkrot`. The brief's branch name was not used. Nothing was committed to `main`. No force-push, no rewritten history.
- **Push.** The first push was refused (403: the Claude GitHub App had no write access to the repository). I stopped, sent Ammar a git bundle as a backup and asked. He fixed the access and the push then worked.
- **Dutch borehole list.** See section 1: the file sits on `www.gdngeoservices.nl`. I stopped and asked; Ammar approved that host.
- **Order of work.** Kansas was finished and pushed (commit `bfc76a0`) before any Dutch file was downloaded.
- Nothing else blocked the work. No rule was worked around.

### 10. How to rerun

```
cd blind_test/tops_headroom
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh                      # data/ -> results/, date-rule test, hashes.txt   (about 6 min; "./run.sh kansas" for one country)
.venv/bin/python -I src/build_report.py     # report_src.md + result tables -> report.md
```

To rebuild `data/` from the sources: `./download_kansas.sh` and `./download_netherlands.sh`, then `.venv/bin/python -I src/prepare_kansas.py`, `.venv/bin/python -I src/prepare_netherlands.py` and `.venv/bin/python -I src/make_manifest.py`. The source files change over time; `manifest.csv` holds the hashes of the files used here.

Files: `src/` code; `data/` cleaned input tables; `results/` tables, chart, name maps, split, spot-check sheet; `manifest.csv` downloads; `hashes.txt` sha256 of every download, input table and result file.
