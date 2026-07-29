#!/usr/bin/env python3
"""DP Task 2: leave-one-out (over the 8 wells) on DK task 5's slope quantities.
Reproduces dk_task5_depthslope.py's per-well real_slope / arm_slope exactly
(same data, same OLS, same units v/v per 1000m), then for each of the 9
pre-specified slope quantities (5 arm-minus-real diffs, 4 arm-vs-arm slope
contrasts) recomputes the point estimate with each of the 8 wells dropped in
turn. Where the FULL 8-well 95% paired bootstrap CI (N_BOOT=10000, seed
20260715, matching DK task 5c/5d machinery exactly) excludes zero, an
additional LOO bootstrap (same N_BOOT/seed, n=7) is run per omitted well to
check whether the zero-exclusion survives; where the full CI already crosses
zero, EXCLUSION_SURVIVES_ALL_EIGHT is N/A by definition (per brief)."""
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
    assert np.allclose(feats_v[prime_n:prime_n + gen_len], real_stored, atol=1e-6)


def ols_slope(x, y):
    x = np.asarray(x, dtype=np.float64); y = np.asarray(y, dtype=np.float64)
    xm, ym = x.mean(), y.mean()
    return float(np.sum((x - xm) * (y - ym)) / np.sum((x - xm) ** 2))


real_slope = {}
for w in WELLS:
    real_nphi = np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX]
    real_slope[w] = ols_slope(depth_scored[w], real_nphi) * 1000.0

arm_slope = {arm: {} for arm in ARMS}
for arm in ARMS:
    for w in WELLS:
        gens = np.array(raw[arm][w]["generated_realizations"], dtype=np.float64)[:, :, NPHI_IDX]
        d = depth_scored[w]
        arm_slope[arm][w] = float(np.mean([ols_slope(d, g) * 1000.0 for g in gens]))

diff_by_arm = {arm: {w: arm_slope[arm][w] - real_slope[w] for w in WELLS} for arm in ARMS}

# sanity check against DK task5 printed values (spot check a few, atol 1e-5)
assert abs(real_slope["16/4-1"] - (-0.304485)) < 1e-4
assert abs(arm_slope["A"]["16/4-1"] - (-0.004751)) < 1e-4
assert abs(diff_by_arm["C"]["34/7-13"] - (0.003664 - (-0.088231))) < 1e-4
print("Sanity check vs DK task5 printed 6dp values: PASS\n")


def bootstrap_mean_ci(values_by_well, wells_subset, n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    vals = np.array([values_by_well[w] for w in wells_subset])
    n = len(vals)
    boots = np.array([rng.choice(vals, size=n, replace=True).mean() for _ in range(n_boot)])
    return dict(mean=float(vals.mean()), ci_low=float(np.percentile(boots, 2.5)),
                ci_high=float(np.percentile(boots, 97.5)))


def bootstrap_paired_diff_ci(vals_a, vals_b, wells_subset, n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    a = np.array([vals_a[w] for w in wells_subset])
    b = np.array([vals_b[w] for w in wells_subset])
    n = len(a)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        diffs[i] = b[idx].mean() - a[idx].mean()
    return dict(point=float(b.mean() - a.mean()), ci_low=float(np.percentile(diffs, 2.5)),
                ci_high=float(np.percentile(diffs, 97.5)))


CONTRASTS = [("A", "B2", "B2 minus A"), ("A", "B-abs", "B-abs minus A"),
             ("B-abs", "B-linear", "B-linear minus B-abs"), ("A", "C", "C minus A")]

print("=" * 100)
print("POST-HOC LOO -- 5 ARM MINUS REAL SLOPE DIFFERENCES")
print("=" * 100)
for arm in ARMS:
    full = bootstrap_mean_ci(diff_by_arm[arm], WELLS)
    full_excl = (full["ci_low"] > 0) or (full["ci_high"] < 0)
    loo_points = []
    for wout in WELLS:
        subset = [w for w in WELLS if w != wout]
        p = float(np.mean([diff_by_arm[arm][w] for w in subset]))
        loo_points.append(p)
    loo_min, loo_max = min(loo_points), max(loo_points)
    full_sign = np.sign(full["mean"])
    sign_stable = all(np.sign(p) == full_sign for p in loo_points)
    if not full_excl:
        excl_survives = "N/A"
    else:
        all_excl = True
        for wout in WELLS:
            subset = [w for w in WELLS if w != wout]
            loo_ci = bootstrap_mean_ci(diff_by_arm[arm], subset)
            loo_excl = (loo_ci["ci_low"] > 0) or (loo_ci["ci_high"] < 0)
            if not loo_excl:
                all_excl = False
        excl_survives = "YES" if all_excl else "NO"
    print(f"POST-HOC  ARM_MINUS_REAL_{arm:10s} FULL_POINT={full['mean']:+.6f}  "
          f"FULL_CI=[{full['ci_low']:+.6f},{full['ci_high']:+.6f}]  FULL_EXCL0={full_excl}  "
          f"LOO_MIN={loo_min:+.6f}  LOO_MAX={loo_max:+.6f}  SIGN_STABLE={'YES' if sign_stable else 'NO'}  "
          f"EXCLUSION_SURVIVES_ALL_EIGHT={excl_survives}")

print("\n" + "=" * 100)
print("POST-HOC LOO -- 4 ARM-VS-ARM SLOPE CONTRASTS")
print("=" * 100)
for base, other, label in CONTRASTS:
    full = bootstrap_paired_diff_ci(arm_slope[base], arm_slope[other], WELLS)
    full_excl = (full["ci_low"] > 0) or (full["ci_high"] < 0)
    loo_points = []
    for wout in WELLS:
        subset = [w for w in WELLS if w != wout]
        pb = float(np.mean([arm_slope[base][w] for w in subset]))
        po = float(np.mean([arm_slope[other][w] for w in subset]))
        loo_points.append(po - pb)
    loo_min, loo_max = min(loo_points), max(loo_points)
    full_sign = np.sign(full["point"])
    sign_stable = all(np.sign(p) == full_sign for p in loo_points)
    if not full_excl:
        excl_survives = "N/A"
    else:
        all_excl = True
        for wout in WELLS:
            subset = [w for w in WELLS if w != wout]
            loo_ci = bootstrap_paired_diff_ci(arm_slope[base], arm_slope[other], subset)
            loo_excl = (loo_ci["ci_low"] > 0) or (loo_ci["ci_high"] < 0)
            if not loo_excl:
                all_excl = False
        excl_survives = "YES" if all_excl else "NO"
    print(f"POST-HOC  {label:24s} FULL_POINT={full['point']:+.6f}  "
          f"FULL_CI=[{full['ci_low']:+.6f},{full['ci_high']:+.6f}]  FULL_EXCL0={full_excl}  "
          f"LOO_MIN={loo_min:+.6f}  LOO_MAX={loo_max:+.6f}  SIGN_STABLE={'YES' if sign_stable else 'NO'}  "
          f"EXCLUSION_SURVIVES_ALL_EIGHT={excl_survives}")

print("\nDP_TASK2_LOO_COMPLETE")
