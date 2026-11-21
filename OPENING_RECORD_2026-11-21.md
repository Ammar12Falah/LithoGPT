# Opening record, 21 November 2026

Results opened at 2026-11-21 11:49:31 UTC, once, after the reading rules were made public
(READING_RULES_2026-11-21.md, commit 93a745e66eb057d1d4ee677927ba410c215ee302, pushed 11:49:03 UTC).
Before opening, the four comparison files, every other file in out/ and every gens/**/scores.json
(278 files) were hashed and found equal to the public list run_record/run_folder_2026-11-21.sha256
(commit e2acd0e1423d857b6efe97e2002e062eab345827). Nothing was rerun, refitted, re-scored or dropped.

Each difference is the first-named minus the second-named; lower is better for both scores, so a
negative difference favours the first-named. Intervals: 95%, bootstrap over wells and seeds together,
10,000 draws (protocol section 9, CLARIFICATIONS.md Q31). Selected setting: dropout 0.2, weight decay 0.1.

## Governing results: confirmatory wells, lowest-development-loss checkpoint

| Comparison | Estimate | 95% interval | Zero | Wells x seeds |
|---|---|---|---|---|
| 1. B2 minus A, absolute NPHI bias | -0.00819 | -0.01786 to +0.00111 | the interval included zero | 20 x 12 |
| 2. A minus tuned chain, absolute NPHI bias | -0.00187 | -0.01507 to +0.01127 | the interval included zero | 20 x 12 |
| 3. A minus trigram, structure score | -0.03022 | -0.03901 to -0.02133 | the interval excluded zero | 20 x 12 |
| 4. A minus block resampling, structure score | -0.00408 | -0.01177 to +0.00422 | the interval included zero | 20 x 12 |

## Secondary results

| Comparison | Confirmatory, step 3000 | Pilot, lowest-development-loss | Pilot, step 3000 |
|---|---|---|---|
| 1. B2 minus A, abs. NPHI bias | -0.01318 (-0.02229 to -0.00462), excluded zero, 20 x 12 | -0.01526 (-0.02721 to -0.00610), excluded zero, 8 x 12 | -0.00921 (-0.01867 to -0.00080), excluded zero, 8 x 12 |
| 2. A minus tuned chain, abs. NPHI bias | +0.00101 (-0.01037 to +0.01184), included zero, 20 x 12 | +0.01076 (-0.00725 to +0.02687), included zero, 8 x 12 | +0.00481 (-0.01657 to +0.02495), included zero, 8 x 12 |
| 3. A minus trigram, structure score | -0.02135 (-0.03698 to -0.00430), excluded zero, 20 x 12 | -0.01910 (-0.03261 to -0.00507), excluded zero, 8 x 12 | -0.01710 (-0.03383 to +0.00098), included zero, 8 x 12 |
| 4. A minus block resampling, structure score | +0.00479 (-0.01025 to +0.02139), included zero, 20 x 12 | +0.00240 (-0.00688 to +0.01150), included zero, 8 x 12 | +0.00440 (-0.01302 to +0.02167), included zero, 8 x 12 |

## Completeness
- Wells: all 20 eligible confirmatory wells and all 8 pilot wells in every comparison.
- Seeds: 12 (20260715 to 20260726) for A, B2, the tuned chain, the trigram and block resampling, in every comparison.
- Runs: 34 of 34 training runs complete. Output folders: A 12, B2 12, C 5 at both checkpoints on both well
  sets; every baseline at 12 seeds (the constant predictor at 1) on both well sets. No run is missing.
