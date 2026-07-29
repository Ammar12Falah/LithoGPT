# DQ Gate 2 — G2 TRACEABILITY

`analysis/build_frozen_results.py` recomputes, at full precision, every quantity DK tasks
1/5/6 and G1b/G1e produced (DK's own committed outputs print only 4dp/6dp text for most of
these — full precision was never written to disk before this gate). Every recomputed value
is sanity-checked against the already-committed rounded value before being trusted (all
checks PASS, printed in the script's own stdout). 315 keys written to
`analysis/FROZEN_RESULTS.json`, each `{"value": <full precision>, "provenance": {"file":
..., "code_path": ...}}`.

Provenance breakdown:
- 264 keys freshly recomputed this gate from the raw v3 JSON / FORCE CSV (headline table,
  4 contrasts, both guard tables, per-well slopes, slope contrasts, LOO min/max/sign-stable,
  dispersion pooled+eqw, MDE) — code paths point at the DK/G1 script that defines the
  algorithm (`dk_task1_fullprecision.py`, `dk_task5_depthslope.py`, `dk_task6_dispersion.py`,
  `dp_task2_loo.py`, `dp_task5_mde.py`), since that is where each method was validated, not
  at `build_frozen_results.py` itself (a re-execution, not a new method).
- 51 keys are static frozen facts (counts, depth ranges, params, wall time, Athy fit,
  tokenizer-seal numbers, estimator-provenance dates) carried from Section 1 / earlier
  session artifacts already on disk (`dl_q3_depth_range.py`, `atce_ablation_v3/run_log.txt`,
  git log) or, where no on-disk artifact exists in this repo (Athy fit constants, sealed
  tokenizer entropy/RMSE — these were produced on the pod in an earlier session, per project
  memory, and are not reproducible here under "local Mac only, no pod, no GPU, no network"),
  explicitly tagged `"DQ brief section 1 (pre-existing project record, not re-derived this
  session)"` rather than silently presented as independently verified.

`analysis/fill.py` substitutes `{{key}}` / `{{key:FORMATSPEC}}` tokens in
`manuscript/manuscript.template.md` against `FROZEN_RESULTS.json`, rounding once at
substitution time via Python `format()`, and refuses to silently drop a missing key (writes
`{{MISSING:key}}` and exits nonzero) rather than ever having a hand-typed number in the
manuscript.

G2 STATUS: COMPLETE. 0 sanity-check failures. Continuing to G3.
