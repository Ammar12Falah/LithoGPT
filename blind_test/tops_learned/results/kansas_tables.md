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
