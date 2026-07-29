#!/usr/bin/env python3
"""DK Task 3: independent reproduction of the third convention found in
ATCE_V1_5_PAIRED_CONTRASTS.csv ("mean_realization_absolute_bias" -- abs()
applied INSIDE the per-realization loop, before averaging over realizations,
per ATCE_V1_5_CPU_AUDIT_RECOMPUTE.py line 129/144-145), for the flagged
row 26 (B-linear minus B-abs, NPHI)."""
import json
import numpy as np

RAW_PATH = "/Users/ammar/LithoGPT_archive/atce_ablation_v3_raw_results_2026-07-26.json"
NPHI_IDX = 2
SEED = 20260715
N_BOOT = 10000

with open(RAW_PATH) as f:
    raw = json.load(f)
WELLS = list(raw["A"].keys())


def mean_realization_abs_bias(arm, well):
    """abs() INSIDE the per-realization loop (audit script line 129), then
    mean over the 5 realizations (line 144-145) -- this is the third,
    absolute-BEFORE-realization-reduction convention."""
    d = raw[arm][well]
    real = np.array(d["real"], dtype=np.float64)
    gens = np.array(d["generated_realizations"], dtype=np.float64)
    real_nphi = real[:, NPHI_IDX]
    per_real_abs = [abs(float(g[:, NPHI_IDX].mean() - real_nphi.mean())) for g in gens]
    return float(np.mean(per_real_abs))


vals_babs = {w: mean_realization_abs_bias("B-abs", w) for w in WELLS}
vals_blin = {w: mean_realization_abs_bias("B-linear", w) for w in WELLS}

rng = np.random.default_rng(SEED)
wells = list(vals_babs.keys())
a = np.array([vals_babs[w] for w in wells])
b = np.array([vals_blin[w] for w in wells])
n = len(a)
diffs = np.empty(N_BOOT)
for i in range(N_BOOT):
    idx = rng.integers(0, n, size=n)
    diffs[i] = b[idx].mean() - a[idx].mean()
point = float(b.mean() - a.mean())
lo, hi = float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))
print("INDEPENDENT REPRODUCTION of ATCE_V1_5_PAIRED_CONTRASTS.csv row 26")
print("(B-linear minus B-abs, nphi_mean_realization_absolute_bias):")
print(f"  point={point:.16g}  CI=[{lo:.16g},{hi:.16g}]")
print("  CSV row 26 says: point=0.016942285207397677  "
      "CI=[0.0015034300876249668,0.03326014400310464]")
print(f"  MATCH (1e-9): point={abs(point-0.016942285207397677)<1e-9}  "
      f"lo={abs(lo-0.0015034300876249668)<1e-9}  hi={abs(hi-0.03326014400310464)<1e-9}")
print(f"  EXCLUDES ZERO: {(lo > 0) or (hi < 0)}")
print("\nTASK3_THIRDCONVENTION_COMPLETE")
