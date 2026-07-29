# DQ Gate 9 — G9 RENDER FIGURES

`analysis/render_figures.py`, run only via `~/lithogpt_plot/bin/python3` (the G8 venv). Reads
only `figs/F*_data.csv`, `figs/F2_*.npy`, and `analysis/FROZEN_RESULTS.json` (for the Athy
overlay constants and provenance) — recomputes no statistic. Light print-safe background
(`plt.rcParams` forced to white figure/axes/savefig facecolor). Vector PDF + 300dpi PNG for
every figure, written into `figs/`.

- `figs/F1_per_well_nphi_bias.{pdf,png}` — 8 wells × 5 arms, point + error bar (min/max across
  the 5 within-well realizations, captioned as descriptive only), zero line.
- `figs/F2_nphi_distribution.{pdf,png}` — 3 panels sharing x/y axes (A vs B2 vs real; B-linear
  vs B-abs vs real; A vs C vs real), step histograms, density-normalized.
- `figs/F3_nphi_vs_depth.{pdf,png}` — 20 depth-binned means, 5 arms + real, Athy overlay
  (phi0=0.6052, lambda=4068.0 m) computed directly from the FROZEN_RESULTS values, x-axis
  limited to the scored window (1295.6–3897.3 m), stated in both the axis label and title.
- `figs/F4_autocorrelation.{pdf,png}` — real vs A vs C, lags 1–20, mean over 8 wells.
- `figs/F5_per_well_depth_slope.{pdf,png}` — see branch decision below.

One rendering-only fix made and disclosed: Arm C's per-well F1 error bars are computed from 5
literally-identical realizations (Arm C is deterministic); floating-point rounding made
`point - real_min` or `real_max - point` a ~1e-17 negative value on one well, which
`matplotlib.errorbar` rejects (`yerr` must be non-negative). Clipped to 0 at render time only —
`figs/F1_data.csv` itself (the G3 data artifact) was not touched. A second fix: Arm A's plot
color was initially near-identical to "real"'s black, defeating the point of F3/F5 (both show A
and real as separate series); recolored Arm A to a dark red before final render, confirmed
visually distinguishable (see the rendered PNGs).

## F5 branch decision (3.4 applied here, per instruction)

Per `reports/DQ_GATE_1.md` §G1b, of the 9 leave-one-out-checked slope quantities:
- **B2 minus A** and **B-linear minus B-abs** (arm-vs-arm slope contrasts): full interval
  excludes zero, sign stable under all 8 omissions → satisfies 3.4's "render it" condition
  outright.
- **ARM_MINUS_REAL_C**: full interval excludes zero, sign IS stable under all 8 omissions
  (LOO range stays positive throughout), but its own leave-one-out bootstrap CI does not
  exclude zero for at least one omitted well (`EXCLUSION_SURVIVES_ALL_EIGHT=NO`). 3.4's fragile
  branch is defined by a **sign flip** under omission ("excludes zero but flips under any
  omission"); this quantity's sign never flips, so it does not fall into that branch either —
  it is simply a somewhat less robust instance of the first (render) branch, noted in the F5
  caption rather than silently treated as identical in strength to the two contrasts above.
- All other slope quantities (each arm's own slope minus real, B-abs minus A slope contrast, C
  minus A slope contrast): full interval crosses zero → descriptive only, per 3.4's third
  branch, never carrying interval language.

**Because at least one quantity satisfies 3.4's excludes-zero-and-sign-stable condition, F5 is
rendered as the main figure, not moved to a "fragile" appendix figure.** No quantity in this set
triggered the fragile/appendix branch (none excludes zero AND flips sign under any single
omission). The rendered figure's caption states explicitly which two contrasts carry
inferential weight and that all other series on the same plot are descriptive only — this
follows rule 3.5 ("any descriptive finding that flips sign under leave-one-out is reported with
its LOO range or not at all, never dropped silently") by keeping every series visible with its
support level stated, rather than selectively hiding the weaker ones.

Arm D appears in no figure (not in any `figs/F*_data.csv`/`.npy` file, never plotted).

G9 STATUS: COMPLETE. Continuing to G10.
