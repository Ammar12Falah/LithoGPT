# DQ Gate 3 — G3 FIGURES AND TABLES

## Blocker: matplotlib is not installed on this Mac

```
$ python3 -c "import matplotlib; print(matplotlib.__version__)"
ModuleNotFoundError: No module named 'matplotlib'
```
No other Python interpreter exists on this machine (`which -a python3` → only `/usr/bin/python3`;
confirmed in DK task 7 already: no Homebrew, no python3.10+). Section 0 says "No installs." This
is treated the same as the GPU rule in section 0 ("if a step seems to need GPU, skip it and log
it as out of scope") and the sklearn-1.9.0 blocker in DK task 7: reported verbatim, not worked
around by installing anything or by substituting a non-matplotlib plotting method (the brief
specifies "Matplotlib only," so hand-rolling SVG/other output would not satisfy G3 either — it
would just be a different fabrication).

**Consequence: no PDF/PNG image exists for F1-F5.** This is a genuine gate shortfall, carried
into `reports/DQ_SUMMARY.md` and the handoff doc as the single largest piece of remaining work,
not silently absorbed.

## What WAS produced: every number each figure needs, in `figs/`

To make the eventual plotting step a pure rendering pass (no re-analysis needed once matplotlib
is available), `analysis/build_tables_and_figdata.py` computed and saved:

- `figs/F1_data.csv` — 40 rows (5 arms × 8 wells): per-well NPHI bias point estimate, plus
  min/max across the 5 within-well realizations (a descriptive spread band, explicitly NOT the
  well-level paired bootstrap used for the four inferential comparisons — caption must say so).
- `figs/F2_real_nphi.npy` + `figs/F2_gen_nphi_{A,B2,Blinear,Babs,C}.npy` — pooled NPHI arrays
  (all realizations, all 8 wells) for the three-panel distribution comparison (A/B2/real,
  B-linear/B-abs/real, A/C/real).
- `figs/F3_data.csv` — 20 depth-binned means (real + 5 arms) over the SCORED window only
  (1295.6256–3897.346 m), plus the Athy overlay parameters (phi0=0.6052, lambda=4068.0 m,
  phi(z)=phi0·exp(−z/lambda)) — caption must state the x-axis is the scored window, not the
  full-valid window.
- `figs/F4_data.csv` — mean autocorrelation (lags 1–20, averaged over 8 wells) for real, Arm A,
  Arm C.
- `figs/F5_data.csv` — per-well depth slope, real + 5 arms (v/v per 1000 m). **Authorized**: per
  `reports/DQ_GATE_1.md` §G1b, threshold 3.4 is satisfied (B2 minus A and B-linear minus B-abs
  slope contrasts both exclude zero with sign stable under all 8 leave-one-out omissions), so F5
  is not skipped.

## T1–T3: produced in full (no matplotlib dependency)

- `figs/T1_headline.csv` / `.tex` — 5 metrics × 5 arms, equal-weight. LaTeX file's leading
  comment states the W1 call signature: `scipy.stats.wasserstein_distance(real_nphi, gen_nphi)`
  per realization, mean over 5 realizations then equal-weight mean over 8 wells.
- `figs/T2_guard_signed.csv` / `.tex` — all 12 rows (4 contrasts × 3 metrics), signed convention,
  exclude-zero verdict per row.
- `figs/T3_guard_magnitude.csv` / `.tex` — all 12 rows, magnitude convention (abs per well AFTER
  realization reduction), exclude-zero verdict per row.

Both guard tables are produced in full; neither is suppressed, per instruction.

G3 STATUS: **PARTIAL.** T1–T3 complete. F1–F5 data complete; F1–F5 **images NOT produced**
(matplotlib unavailable, installs forbidden). Continuing to G4.
