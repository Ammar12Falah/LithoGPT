#!/usr/bin/env python3
"""DK Task 5: post-hoc depth-slope analysis. Scored window only, per-well depth
arrays from the FORCE CSV (oracle-supplied, element-aligned to the stored real
arrays). OLS slope of NPHI on depth, per realization -> mean over 5
realizations to well level (same reduction order as the governing estimator)
-> equal-weight per well -> paired bootstrap over the 8 wells, same machinery
as task 1e. Units: v/v per 1000 m. Every row labelled POST-HOC."""
import json
import numpy as np
import pandas as pd

RAW_PATH = "/Users/ammar/LithoGPT_archive/atce_ablation_v3_raw_results_2026-07-26.json"
FORCE_CSV = "/Users/ammar/LithoGPT_archive/force2020_data/train.csv"
SEED = 20260715
N_BOOT = 10000
NPHI_IDX = 2
FEATURES = ["GR", "RDEP", "NPHI", "RHOB"]
CONTEXT, PRIME_FRAC, MAX_GEN_LEN = 512, 0.25, 20000
ARMS = ["A", "B-linear", "B-abs", "B2", "C"]

with open(RAW_PATH) as f:
    raw = json.load(f)
WELLS = list(raw["A"].keys())

df = pd.read_csv(FORCE_CSV, sep=";")
depth_scored = {}
for w in WELLS:
    wdf = df[df["WELL"] == w].sort_values("DEPTH_MD")
    depth = wdf["DEPTH_MD"].to_numpy(dtype=np.float64)
    feats = wdf[FEATURES].to_numpy(dtype=np.float64)
    valid = np.isfinite(feats).all(axis=1)
    depth_v, feats_v = depth[valid], feats[valid]
    n = len(depth_v)
    prime_n = max(CONTEXT, int(n * PRIME_FRAC))
    gen_len = min(n - prime_n, MAX_GEN_LEN)
    depth_scored[w] = depth_v[prime_n:prime_n + gen_len]
    real_stored = np.array(raw["A"][w]["real"], dtype=np.float64)
    assert np.allclose(feats_v[prime_n:prime_n + gen_len], real_stored, atol=1e-6), f"depth alignment failed for {w}"
print("Depth arrays validated element-aligned to stored real arrays for all 8 wells.\n")


def ols_slope(x, y):
    """slope in y-units per x-unit; x in metres here, converted to per-1000m after."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    xm, ym = x.mean(), y.mean()
    return float(np.sum((x - xm) * (y - ym)) / np.sum((x - xm) ** 2))


print("=" * 100)
print("POST-HOC 5b/5e. PER-WELL REAL NPHI-vs-DEPTH SLOPE (v/v per 1000 m)")
print("=" * 100)
real_slope = {}
for w in WELLS:
    real_nphi = np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX]
    d = depth_scored[w]
    s = ols_slope(d, real_nphi) * 1000.0
    real_slope[w] = s
    print(f"  POST-HOC  {w:12s} real slope = {s:+.6f}")

print("\n" + "=" * 100)
print("POST-HOC 5a/5e. PER-WELL, PER-ARM SLOPE (mean of 5 realization slopes)")
print("=" * 100)
arm_slope = {arm: {} for arm in ARMS}
for arm in ARMS:
    for w in WELLS:
        gens = np.array(raw[arm][w]["generated_realizations"], dtype=np.float64)[:, :, NPHI_IDX]
        d = depth_scored[w]
        real_slopes = [ols_slope(d, g) * 1000.0 for g in gens]
        arm_slope[arm][w] = float(np.mean(real_slopes))
    print(f"\n  Arm {arm}:")
    for w in WELLS:
        print(f"    POST-HOC  {w:12s} arm slope = {arm_slope[arm][w]:+.6f}  real slope = {real_slope[w]:+.6f}  "
              f"diff = {arm_slope[arm][w]-real_slope[w]:+.6f}")

print("\n" + "=" * 100)
print("POST-HOC 5c. PER-WELL DIFFERENCE (arm minus real), equal-weight mean + paired bootstrap over wells")
print("=" * 100)


def bootstrap_ci_single(values_by_well, n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    wells = list(values_by_well.keys())
    vals = np.array([values_by_well[w] for w in wells])
    n = len(vals)
    boots = np.array([rng.choice(vals, size=n, replace=True).mean() for _ in range(n_boot)])
    return dict(mean=float(vals.mean()), ci_low=float(np.percentile(boots, 2.5)),
                ci_high=float(np.percentile(boots, 97.5)))


diff_by_arm = {}
for arm in ARMS:
    diffs = {w: arm_slope[arm][w] - real_slope[w] for w in WELLS}
    diff_by_arm[arm] = diffs
    ci = bootstrap_ci_single(diffs)
    print(f"  POST-HOC  {arm:10s} mean(arm-real) = {ci['mean']:+.6f}  CI=[{ci['ci_low']:+.6f},{ci['ci_high']:+.6f}]")

print("\n" + "=" * 100)
print("POST-HOC 5d. FOUR CONTRASTS APPLIED TO SLOPE (arm-vs-arm on the SLOPE quantity itself)")
print("=" * 100)


def bootstrap_paired_diff(vals_a, vals_b, n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    wells = list(vals_a.keys())
    a = np.array([vals_a[w] for w in wells])
    b = np.array([vals_b[w] for w in wells])
    n = len(a)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        diffs[i] = b[idx].mean() - a[idx].mean()
    return dict(point=float(b.mean() - a.mean()), ci_low=float(np.percentile(diffs, 2.5)),
                ci_high=float(np.percentile(diffs, 97.5)))


CONTRASTS = [("A", "B2", "B2 minus A"), ("A", "B-abs", "B-abs minus A"),
             ("B-abs", "B-linear", "B-linear minus B-abs"), ("A", "C", "C minus A")]
for base, other, label in CONTRASTS:
    d = bootstrap_paired_diff(arm_slope[base], arm_slope[other])
    print(f"  POST-HOC  {label:24s} operand_order=({other} minus {base})  slope_point={d['point']:+.6f} v/v-per-1000m  "
          f"CI=[{d['ci_low']:+.6f},{d['ci_high']:+.6f}]")

print("\nTASK5_DEPTHSLOPE_COMPLETE")
