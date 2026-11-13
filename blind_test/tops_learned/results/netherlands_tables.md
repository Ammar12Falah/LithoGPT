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
