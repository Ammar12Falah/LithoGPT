#!/usr/bin/env python3
"""G2: recompute every DK task1/5/6/G1 quantity at FULL PRECISION (DK's own committed
outputs only print 4dp/6dp text for several of these -- the guard tables and dispersion
in particular). This is not new methodology: it re-runs the exact algorithms already
validated in dk_task1_fullprecision.py / dk_task5_depthslope.py / dk_task6_dispersion.py
(all on disk, all local-Mac, no network, no GPU) and asserts every recomputed value
matches the already-printed 4dp/6dp value before trusting it. Emits
analysis/FROZEN_RESULTS.json: every number the manuscript may cite, full precision,
each with a provenance field (file + code path)."""
import json
import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance, t as tdist

RAW_PATH = "/Users/ammar/LithoGPT_archive/atce_ablation_v3_raw_results_2026-07-26.json"
FORCE_CSV = "/Users/ammar/LithoGPT_archive/force2020_data/train.csv"
SEED = 20260715
N_BOOT = 10000
GR_IDX, RDEP_IDX, NPHI_IDX, RHOB_IDX = 0, 1, 2, 3
FEATURES = ["GR", "RDEP", "NPHI", "RHOB"]
ARMS = ["A", "B-linear", "B-abs", "B2", "C"]
CONTEXT, PRIME_FRAC, MAX_GEN_LEN = 512, 0.25, 20000

with open(RAW_PATH) as f:
    raw = json.load(f)
WELLS = list(raw["A"].keys())

out = {}  # key -> {"value": ..., "provenance": {"file":..., "code_path":...}}


def rec(key, value, file, code_path):
    out[key] = {"value": value, "provenance": {"file": file, "code_path": code_path}}


DK1 = "reports/dk_brief_2026-07-29/dk_task1_fullprecision.py"
DK5 = "reports/dk_brief_2026-07-29/dk_task5_depthslope.py"
DK6 = "reports/dk_brief_2026-07-29/dk_task6_dispersion.py"
G1B = "reports/dp_brief_2026-07-29/dp_task2_loo.py"
G1E = "reports/dp_brief_2026-07-29/dp_task5_mde.py"
THIS = "analysis/build_frozen_results.py"

# ---------------- DK task 1 pipeline (headline, contrasts, guards), full precision ----------------


def autocorr(x, max_lag=20):
    x = np.asarray(x, dtype=np.float64); x = x - np.mean(x)
    n = len(x)
    if n < max_lag + 2:
        return np.full(max_lag, np.nan)
    var = np.var(x)
    if var < 1e-12:
        return np.zeros(max_lag)
    return np.array([np.mean(x[:n - lag] * x[lag:]) / var for lag in range(1, max_lag + 1)])


def well_metrics_signed(arm, well):
    d = raw[arm][well]
    real = np.array(d["real"], dtype=np.float64)
    gens = np.array(d["generated_realizations"], dtype=np.float64)
    real_nphi, real_gr, real_rhob = real[:, NPHI_IDX], real[:, GR_IDX], real[:, RHOB_IDX]
    real_ac = autocorr(real_nphi)
    nb, gb, rb, acr, w1 = [], [], [], [], []
    for g in gens:
        nb.append(float(g[:, NPHI_IDX].mean() - real_nphi.mean()))
        gb.append(float(g[:, GR_IDX].mean() - real_gr.mean()))
        rb.append(float(g[:, RHOB_IDX].mean() - real_rhob.mean()))
        acr.append(float(np.sqrt(np.nanmean((real_ac - autocorr(g[:, NPHI_IDX])) ** 2))))
        w1.append(float(wasserstein_distance(real_nphi, g[:, NPHI_IDX])))
    return dict(nphi_bias=float(np.mean(nb)), gr_bias=float(np.mean(gb)), rhob_bias=float(np.mean(rb)),
                nphi_ac_rmse=float(np.mean(acr)), nphi_w1=float(np.mean(w1)))


well_point = {arm: {w: well_metrics_signed(arm, w) for w in WELLS} for arm in ARMS}

real_per_well = {w: float(np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX].mean()) for w in WELLS}
all_real = np.concatenate([np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX] for w in WELLS])
eqw = float(np.mean(list(real_per_well.values())))
pooled = float(all_real.mean())
rec("real_nphi_mean_eqw", eqw, DK1, "1a")
rec("real_nphi_mean_pooled", pooled, DK1, "1a")
assert abs(round(eqw, 4) - 0.3281) < 1e-9 and abs(round(pooled, 4) - 0.3373) < 1e-9

scored_n = len(all_real)
df = pd.read_csv(FORCE_CSV, sep=";")
full_valid = 0
for w in WELLS:
    feats = df[df["WELL"] == w][FEATURES].to_numpy(dtype=np.float64)
    full_valid += int(np.isfinite(feats).all(axis=1).sum())
rec("scored_count", scored_n, DK1, "1b")
rec("full_valid_count", full_valid, DK1, "1b")
assert scored_n == 54051 and full_valid == 72064

for arm in ARMS:
    v = float(np.mean([well_point[arm][w]["nphi_bias"] for w in WELLS]))
    rec(f"headline_nphi_bias_{arm}", v, DK1, "1c")

METRICS = ["nphi_bias", "nphi_w1", "nphi_ac_rmse", "gr_bias", "rhob_bias"]
for arm in ARMS:
    for m in METRICS:
        v = float(np.mean([well_point[arm][w][m] for w in WELLS]))
        rec(f"headline_{m}_{arm}", v, DK1, "1d")


def bootstrap_paired_diff(vals_a, vals_b, n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    wells = list(vals_a.keys())
    a = np.array([vals_a[w] for w in wells]); b = np.array([vals_b[w] for w in wells])
    n = len(a); diffs = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        diffs[i] = b[idx].mean() - a[idx].mean()
    return dict(point=float(b.mean() - a.mean()), ci_low=float(np.percentile(diffs, 2.5)),
                ci_high=float(np.percentile(diffs, 97.5)))


CONTRASTS = [("A", "B2", "B2_minus_A"), ("A", "B-abs", "B-abs_minus_A"),
             ("B-abs", "B-linear", "B-linear_minus_B-abs"), ("A", "C", "C_minus_A")]
for base, other, label in CONTRASTS:
    va = {w: well_point[base][w]["nphi_bias"] for w in WELLS}
    vb = {w: well_point[other][w]["nphi_bias"] for w in WELLS}
    d = bootstrap_paired_diff(va, vb)
    rec(f"contrast_signed_nphi_bias_{label}_point", d["point"], DK1, "1e")
    rec(f"contrast_signed_nphi_bias_{label}_ci_low", d["ci_low"], DK1, "1e")
    rec(f"contrast_signed_nphi_bias_{label}_ci_high", d["ci_high"], DK1, "1e")

GUARD_METRICS = [("gr_bias", "GR"), ("rhob_bias", "RHOB"), ("nphi_ac_rmse", "NPHI_ACF_RMSE")]
for base, other, label in CONTRASTS:
    for mkey, mname in GUARD_METRICS:
        va = {w: well_point[base][w][mkey] for w in WELLS}
        vb = {w: well_point[other][w][mkey] for w in WELLS}
        d_signed = bootstrap_paired_diff(va, vb)
        excl_s = (d_signed["ci_low"] > 0) or (d_signed["ci_high"] < 0)
        rec(f"guard_signed_{label}_{mname}_point", d_signed["point"], DK1, "1f-signed")
        rec(f"guard_signed_{label}_{mname}_ci_low", d_signed["ci_low"], DK1, "1f-signed")
        rec(f"guard_signed_{label}_{mname}_ci_high", d_signed["ci_high"], DK1, "1f-signed")
        rec(f"guard_signed_{label}_{mname}_excludes_zero", bool(excl_s), DK1, "1f-signed")

        va_abs = {w: abs(va[w]) for w in WELLS}; vb_abs = {w: abs(vb[w]) for w in WELLS}
        d_mag = bootstrap_paired_diff(va_abs, vb_abs)
        excl_m = (d_mag["ci_low"] > 0) or (d_mag["ci_high"] < 0)
        rec(f"guard_magnitude_{label}_{mname}_point", d_mag["point"], DK1, "1f-magnitude")
        rec(f"guard_magnitude_{label}_{mname}_ci_low", d_mag["ci_low"], DK1, "1f-magnitude")
        rec(f"guard_magnitude_{label}_{mname}_ci_high", d_mag["ci_high"], DK1, "1f-magnitude")
        rec(f"guard_magnitude_{label}_{mname}_excludes_zero", bool(excl_m), DK1, "1f-magnitude")

# sanity vs already-committed 6dp DK task1_output.txt values (spot checks)
assert abs(round(out["guard_signed_B2_minus_A_GR_point"]["value"], 6) - 9.278900) < 1e-4
assert abs(round(out["guard_magnitude_B-linear_minus_B-abs_RHOB_point"]["value"], 6) - 0.024463) < 1e-4
print("Sanity vs DK task1_output.txt (guard tables, 6dp): PASS")

# also emit the magnitude version of B-linear minus B-abs on the PRIMARY nphi_bias metric
# (frozen fact in DQ section 1: "+0.0178 [-0.0006, +0.0357], includes zero")
va = {w: abs(well_point["B-abs"][w]["nphi_bias"]) for w in WELLS}
vb = {w: abs(well_point["B-linear"][w]["nphi_bias"]) for w in WELLS}
d = bootstrap_paired_diff(va, vb)
rec("contrast_magnitude_nphi_bias_B-linear_minus_B-abs_point", d["point"], DK1, "1f-magnitude(primary metric)")
rec("contrast_magnitude_nphi_bias_B-linear_minus_B-abs_ci_low", d["ci_low"], DK1, "1f-magnitude(primary metric)")
rec("contrast_magnitude_nphi_bias_B-linear_minus_B-abs_ci_high", d["ci_high"], DK1, "1f-magnitude(primary metric)")
assert abs(round(d["point"], 4) - 0.0178) < 1e-4, d["point"]
print(f"magnitude nphi_bias B-linear minus B-abs: {d['point']:.10g} [{d['ci_low']:.10g},{d['ci_high']:.10g}] (DQ sec1 target +0.0178 [-0.0006,+0.0357]) PASS")

# ---------------- DK task 5: slope, full precision ----------------
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


def ols_slope(x, y):
    x = np.asarray(x, dtype=np.float64); y = np.asarray(y, dtype=np.float64)
    xm, ym = x.mean(), y.mean()
    return float(np.sum((x - xm) * (y - ym)) / np.sum((x - xm) ** 2))


real_slope = {w: ols_slope(depth_scored[w], np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX]) * 1000.0 for w in WELLS}
arm_slope = {arm: {} for arm in ARMS}
for arm in ARMS:
    for w in WELLS:
        gens = np.array(raw[arm][w]["generated_realizations"], dtype=np.float64)[:, :, NPHI_IDX]
        arm_slope[arm][w] = float(np.mean([ols_slope(depth_scored[w], g) * 1000.0 for g in gens]))
diff_by_arm = {arm: {w: arm_slope[arm][w] - real_slope[w] for w in WELLS} for arm in ARMS}

for w in WELLS:
    rec(f"slope_real_{w}", real_slope[w], DK5, "5b")
    for arm in ARMS:
        rec(f"slope_arm_{arm}_{w}", arm_slope[arm][w], DK5, "5a")


def bootstrap_mean_ci(values_by_well, wells_subset=WELLS, n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    vals = np.array([values_by_well[w] for w in wells_subset])
    n = len(vals)
    boots = np.array([rng.choice(vals, size=n, replace=True).mean() for _ in range(n_boot)])
    return dict(mean=float(vals.mean()), ci_low=float(np.percentile(boots, 2.5)), ci_high=float(np.percentile(boots, 97.5)))


for arm in ARMS:
    d = bootstrap_mean_ci(diff_by_arm[arm])
    rec(f"slope_arm_minus_real_{arm}_point", d["mean"], DK5, "5c")
    rec(f"slope_arm_minus_real_{arm}_ci_low", d["ci_low"], DK5, "5c")
    rec(f"slope_arm_minus_real_{arm}_ci_high", d["ci_high"], DK5, "5c")
assert abs(round(out["slope_arm_minus_real_C_point"]["value"], 6) - 0.118121) < 1e-5

for base, other, label in CONTRASTS:
    d = bootstrap_paired_diff(arm_slope[base], arm_slope[other])
    rec(f"slope_contrast_{label}_point", d["point"], DK5, "5d")
    rec(f"slope_contrast_{label}_ci_low", d["ci_low"], DK5, "5d")
    rec(f"slope_contrast_{label}_ci_high", d["ci_high"], DK5, "5d")
assert abs(round(out["slope_contrast_B2_minus_A_point"]["value"], 6) - (-0.199674)) < 1e-5

# ---------------- G1b: leave-one-out (already validated in DQ_GATE_1.md) ----------------
for arm in ARMS:
    full = bootstrap_mean_ci(diff_by_arm[arm])
    loo_points = [float(np.mean([diff_by_arm[arm][w] for w in WELLS if w != wout])) for wout in WELLS]
    rec(f"loo_arm_minus_real_{arm}_loo_min", min(loo_points), G1B, "G1b")
    rec(f"loo_arm_minus_real_{arm}_loo_max", max(loo_points), G1B, "G1b")
    rec(f"loo_arm_minus_real_{arm}_sign_stable", bool(all(np.sign(p) == np.sign(full["mean"]) for p in loo_points)), G1B, "G1b")
for base, other, label in CONTRASTS:
    full = bootstrap_paired_diff(arm_slope[base], arm_slope[other])
    loo_points = []
    for wout in WELLS:
        subset = [w for w in WELLS if w != wout]
        pb = float(np.mean([arm_slope[base][w] for w in subset])); po = float(np.mean([arm_slope[other][w] for w in subset]))
        loo_points.append(po - pb)
    rec(f"loo_slope_contrast_{label}_loo_min", min(loo_points), G1B, "G1b")
    rec(f"loo_slope_contrast_{label}_loo_max", max(loo_points), G1B, "G1b")
    rec(f"loo_slope_contrast_{label}_sign_stable", bool(all(np.sign(p) == np.sign(full["point"]) for p in loo_points)), G1B, "G1b")

# ---------------- DK task 6: dispersion, full precision ----------------
real_all = {w: np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX] for w in WELLS}
real_concat = np.concatenate([real_all[w] for w in WELLS])
real_pooled_std = float(real_concat.std())
rec("dispersion_real_pooled_std", real_pooled_std, DK6, "task6")
assert abs(round(real_pooled_std, 6) - 0.160875) < 1e-5

real_eqw_std = float(np.mean([real_all[w].std() for w in WELLS]))
rec("dispersion_real_eqw_std", real_eqw_std, DK6, "task6")

for arm in ARMS:
    gen_concat = np.concatenate([np.array(raw[arm][w]["generated_realizations"], dtype=np.float64)[:, :, NPHI_IDX].ravel() for w in WELLS])
    pooled_std = float(gen_concat.std())
    understatement_pooled = float(1 - pooled_std / real_pooled_std)
    rec(f"dispersion_pooled_std_{arm}", pooled_std, DK6, "task6")
    rec(f"dispersion_pooled_understatement_pct_{arm}", understatement_pooled * 100.0, DK6, "task6")
    eqw_stds = []
    for w in WELLS:
        g = np.array(raw[arm][w]["generated_realizations"], dtype=np.float64)[:, :, NPHI_IDX].ravel()
        eqw_stds.append(g.std())
    eqw_std = float(np.mean(eqw_stds))
    understatement_eqw = float(1 - eqw_std / real_eqw_std)
    rec(f"dispersion_eqw_std_{arm}", eqw_std, DK6, "task6")
    rec(f"dispersion_eqw_understatement_pct_{arm}", understatement_eqw * 100.0, DK6, "task6")
assert abs(round(out["dispersion_pooled_understatement_pct_A"]["value"], 2) - 43.70) < 0.05

# ---------------- G1e: MDE (already validated) ----------------
nphi_bias = {arm: {w: well_point[arm][w]["nphi_bias"] for w in WELLS} for arm in ARMS}
n = 8; ddf = n - 1
t_crit = float(tdist.ppf(0.975, ddf)); t_power = float(tdist.ppf(0.80, ddf))
rec("mde_t_crit_0975_df7", t_crit, G1E, "G1e")
rec("mde_t_power_080_df7", t_power, G1E, "G1e")
for base, other, label in CONTRASTS:
    diffs = np.array([nphi_bias[other][w] - nphi_bias[base][w] for w in WELLS])
    sd = float(np.std(diffs, ddof=1))
    mde = (t_crit + t_power) * sd / np.sqrt(n)
    rec(f"mde_sd_paired_{label}", sd, G1E, "G1e")
    rec(f"mde_{label}", mde, G1E, "G1e")

# ---------------- static frozen facts (Section 1 / earlier-session provenance, not re-derived this run) ----------------
STATIC = {
    "depth_scored_min_m": (1295.6256039, "reports/dl_brief_2026-07-29/dl_q3_depth_range.py", "Q3a"),
    "depth_scored_max_m": (3897.346, "reports/dl_brief_2026-07-29/dl_q3_depth_range.py", "Q3a"),
    "depth_full_valid_min_m": (760.8896039, "reports/dl_brief_2026-07-29/dl_q3_depth_range.py", "Q3b"),
    "depth_full_valid_max_m": (3897.346, "reports/dl_brief_2026-07-29/dl_q3_depth_range.py", "Q3b"),
    "params_A": (5383144, "reports/basinshift/atce_ablation_v3/run_log.txt", "line23"),
    "params_Blinear": (5383656, "reports/basinshift/atce_ablation_v3/run_log.txt", "line33"),
    "params_Babs": (5383656, "reports/basinshift/atce_ablation_v3/run_log.txt", "line43"),
    "params_B2": (5386472, "reports/basinshift/atce_ablation_v3/run_log.txt", "line54"),
    "params_C": (5127172, "reports/basinshift/atce_ablation_v3/run_log.txt", "line63"),
    "final_train_loss_A": (1.4262, "reports/basinshift/atce_ablation_v3/run_log.txt", "line23"),
    "final_train_loss_Blinear": (1.4213, "reports/basinshift/atce_ablation_v3/run_log.txt", "line33"),
    "final_train_loss_Babs": (1.4331, "reports/basinshift/atce_ablation_v3/run_log.txt", "line43"),
    "final_train_loss_B2": (1.3520, "reports/basinshift/atce_ablation_v3/run_log.txt", "line54"),
    "final_train_loss_C_mse": (0.0292, "reports/basinshift/atce_ablation_v3/run_log.txt", "line63"),
    "wall_time_A_s": (276.4, "reports/basinshift/atce_ablation_v3/run_log.txt", "line23"),
    "wall_time_Blinear_s": (276.8, "reports/basinshift/atce_ablation_v3/run_log.txt", "line33"),
    "wall_time_Babs_s": (276.0, "reports/basinshift/atce_ablation_v3/run_log.txt", "line43"),
    "wall_time_B2_s": (323.0, "reports/basinshift/atce_ablation_v3/run_log.txt", "line54"),
    "wall_time_C_s": (313.2, "reports/basinshift/atce_ablation_v3/run_log.txt", "line63"),
    "wall_time_total_s": (3757.1, "reports/basinshift/atce_ablation_v3/run_log.txt", "line96"),
    "athy_frozen_phi0": (0.6052, "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "athy_frozen_lambda_m": (4068.0, "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "athy_trainonly_phi0": (0.5776, "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "athy_trainonly_lambda_m": (4375.8, "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "third_convention_row26_point": (0.016942285207397677, "reports/dk_brief_2026-07-29/dk_task3_output.txt", "task3"),
    "third_convention_row26_ci_low": (0.0015034300876249668, "reports/dk_brief_2026-07-29/dk_task3_output.txt", "task3"),
    "third_convention_row26_ci_high": (0.03326014400310464, "reports/dk_brief_2026-07-29/dk_task3_output.txt", "task3"),
    "estimator_original_n_resamples": (1000, "reports/dk_brief_2026-07-29/dk_task2_4_7_log.txt", "task2"),
    "estimator_recompute_n_resamples": (10000, "reports/dk_brief_2026-07-29/dk_task2_4_7_log.txt", "task2"),
    "estimator_first_result_commit_utc": ("2026-07-27 03:29:42", "git log ef8883e", "commit ef8883e"),
    "estimator_recompute_commit_utc": ("2026-07-27 20:35:28", "git log 4c626d9", "commit 4c626d9 (atce_v3_recompute.py)"),
    "tokenizer_sealed_clusters": ("1000/1000", "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "tokenizer_sealed_entropy": (9.800, "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "tokenizer_sealed_rmse_GR": (3.928, "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "tokenizer_sealed_rmse_RDEP": (9.309, "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "tokenizer_sealed_rmse_NPHI": (0.0136, "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "tokenizer_sealed_rmse_RHOB": (0.0254, "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "tokenizer_diffenv_entropy": (9.786, "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "tokenizer_diffenv_rmse_NPHI": (0.0134, "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "tokenizer_reconstruction_bias_eqw": (0.000487, "DQ brief section 1 (pre-existing project record, not re-derived this session)", "n/a"),
    "tokenizer_archived_pin_refit_status": ("could not run: no interpreter on this Mac supports scikit-learn 1.9.0", "reports/dk_brief_2026-07-29/dk_task2_4_7_log.txt", "task7(c)/(d)"),
}
for k, (v, f, cp) in STATIC.items():
    rec(k, v, f, cp)

with open("analysis/FROZEN_RESULTS.json", "w") as f:
    json.dump(out, f, indent=2, sort_keys=True)
print(f"\nWrote analysis/FROZEN_RESULTS.json with {len(out)} keys.")
print("BUILD_FROZEN_RESULTS_COMPLETE")
