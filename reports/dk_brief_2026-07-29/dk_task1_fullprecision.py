#!/usr/bin/env python3
"""DK Task 1: full-precision re-derivation. Round ONCE from full precision.
Estimator: metric per realization -> mean over 5 realizations within well ->
equal weight per well (or pooled where stated) -> paired well-level bootstrap,
10000 resamples, np.random.default_rng(20260715), percentile 2.5/97.5, shared
index draw, resampling over the 8 wells."""
import json
import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance

RAW_PATH = "/Users/ammar/LithoGPT_archive/atce_ablation_v3_raw_results_2026-07-26.json"
FORCE_CSV = "/Users/ammar/LithoGPT_archive/force2020_data/train.csv"
SEED = 20260715
N_BOOT = 10000
GR_IDX, RDEP_IDX, NPHI_IDX, RHOB_IDX = 0, 1, 2, 3
FEATURES = ["GR", "RDEP", "NPHI", "RHOB"]
ARMS = ["A", "B-linear", "B-abs", "B2", "C"]  # D withdrawn

with open(RAW_PATH) as f:
    raw = json.load(f)
WELLS = list(raw["A"].keys())


def autocorr(x, max_lag=20):
    x = np.asarray(x, dtype=np.float64)
    x = x - np.mean(x)
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

print("=" * 100)
print("1a. REAL NPHI MEAN")
print("=" * 100)
real_per_well = {}
all_real = []
for w in WELLS:
    real = np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX]
    real_per_well[w] = float(real.mean())
    all_real.append(real)
all_real = np.concatenate(all_real)
eqw = np.mean(list(real_per_well.values()))
pooled = all_real.mean()
print(f"equal-weight: {eqw:.10g}  (10sf)   {round(eqw,4):.4f} (4dp)   expect 0.328089")
print(f"pooled:       {pooled:.10g}  (10sf)   {round(pooled,4):.4f} (4dp)   expect 0.337309")

print("\n" + "=" * 100)
print("1b. SCORED COUNT / FULL VALID COUNT")
print("=" * 100)
scored_n = len(all_real)
df = pd.read_csv(FORCE_CSV, sep=";")
full_valid = 0
for w in WELLS:
    feats = df[df["WELL"] == w][FEATURES].to_numpy(dtype=np.float64)
    full_valid += int(np.isfinite(feats).all(axis=1).sum())
print(f"scored = {scored_n}  (expect 54051)")
print(f"full_valid = {full_valid}  (expect 72064)")

print("\n" + "=" * 100)
print("1c. FIVE HEADLINE NPHI BIASES")
print("=" * 100)
targets_1c = {"A": -0.0423, "B-linear": -0.0666, "B-abs": -0.0340, "B2": -0.0448, "C": +0.0332}
for arm in ARMS:
    v = np.mean([well_point[arm][w]["nphi_bias"] for w in WELLS])
    print(f"  {arm:10s} full={v:.10g}  4dp={round(v,4):+.4f}  target={targets_1c[arm]:+.4f}  "
          f"diff={abs(v-targets_1c[arm]):.2e}")

print("\n" + "=" * 100)
print("1d. FULL HEADLINE TABLE, 5 METRICS x 5 ARMS (equal-weight per well)")
print("=" * 100)
METRICS = ["nphi_bias", "nphi_w1", "nphi_ac_rmse", "gr_bias", "rhob_bias"]
header = f"{'arm':10s}" + "".join(f"{m:>18s}" for m in METRICS)
print(header)
headline_rows = []
for arm in ARMS:
    row = {"arm": arm}
    vals = []
    for m in METRICS:
        v = np.mean([well_point[arm][w][m] for w in WELLS])
        row[m] = v
        vals.append(v)
    headline_rows.append(row)
    print(f"{arm:10s}" + "".join(f"{v:+18.10g}" for v in vals))

print("\n" + "=" * 100)
print("1e. FOUR CONTRASTS, SIGNED NPHI BIAS, PAIRED BOOTSTRAP, SHARED INDEX DRAW")
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
contrast_rows = []
for base, other, label in CONTRASTS:
    va = {w: well_point[base][w]["nphi_bias"] for w in WELLS}
    vb = {w: well_point[other][w]["nphi_bias"] for w in WELLS}
    d = bootstrap_paired_diff(va, vb)
    contrast_rows.append(dict(label=label, base=base, other=other, **d))
    print(f"  {label:24s} operand_order=({other} minus {base})  "
          f"point_full={d['point']:.10g}  point_4dp={round(d['point'],4):+.4f}  "
          f"CI_full=[{d['ci_low']:.10g},{d['ci_high']:.10g}]  "
          f"CI_4dp=[{round(d['ci_low'],4):+.4f},{round(d['ci_high'],4):+.4f}]")

print("\n" + "=" * 100)
print("1f. GUARD TABLES -- SIGNED and MAGNITUDE (abs per well AFTER realization reduction, "
      "BEFORE averaging across wells)")
print("=" * 100)
GUARD_METRICS = [("gr_bias", "GR"), ("rhob_bias", "RHOB"), ("nphi_ac_rmse", "NPHI ACF RMSE")]

signed_rows, magnitude_rows = [], []
for base, other, label in CONTRASTS:
    for mkey, mname in GUARD_METRICS:
        va = {w: well_point[base][w][mkey] for w in WELLS}
        vb = {w: well_point[other][w][mkey] for w in WELLS}
        d_signed = bootstrap_paired_diff(va, vb)
        excl_s = (d_signed["ci_low"] > 0) or (d_signed["ci_high"] < 0)
        signed_rows.append(dict(label=label, metric=mname, **d_signed, excludes_zero=excl_s))

        va_abs = {w: abs(va[w]) for w in WELLS}
        vb_abs = {w: abs(vb[w]) for w in WELLS}
        d_mag = bootstrap_paired_diff(va_abs, vb_abs)
        excl_m = (d_mag["ci_low"] > 0) or (d_mag["ci_high"] < 0)
        magnitude_rows.append(dict(label=label, metric=mname, **d_mag, excludes_zero=excl_m))

print("\n-- SIGNED --")
for r in signed_rows:
    print(f"  {r['label']:24s} {r['metric']:14s} point={r['point']:+.6f} CI=[{r['ci_low']:+.6f},{r['ci_high']:+.6f}] excl0={r['excludes_zero']}")
print("\n-- MAGNITUDE --")
for r in magnitude_rows:
    print(f"  {r['label']:24s} {r['metric']:14s} point={r['point']:+.6f} CI=[{r['ci_low']:+.6f},{r['ci_high']:+.6f}] excl0={r['excludes_zero']}")

# ---- CSV emission: every quantity at full precision + single-rounded 4dp, flagged vs v1.9 targets ----
csv_rows = []
v19_targets = {
    ("1a_real_nphi_eqw", None): 0.328089, ("1a_real_nphi_pooled", None): 0.337309,
    ("1c_A", None): -0.0423, ("1c_B-linear", None): -0.0666, ("1c_B-abs", None): -0.0340,
    ("1c_B2", None): -0.0448, ("1c_C", None): +0.0332,
    ("1e_B2 minus A_point", None): -0.0024, ("1e_B2 minus A_lo", None): -0.0188, ("1e_B2 minus A_hi", None): +0.0140,
    ("1e_B-abs minus A_point", None): +0.0084, ("1e_B-abs minus A_lo", None): -0.0064, ("1e_B-abs minus A_hi", None): +0.0223,
    ("1e_B-linear minus B-abs_point", None): -0.0326, ("1e_B-linear minus B-abs_lo", None): -0.0470, ("1e_B-linear minus B-abs_hi", None): -0.0184,
    ("1e_C minus A_point", None): +0.0755, ("1e_C minus A_lo", None): +0.0214, ("1e_C minus A_hi", None): +0.1312,
}
full_values = {
    ("1a_real_nphi_eqw", None): eqw, ("1a_real_nphi_pooled", None): pooled,
    ("1c_A", None): headline_rows[0]["nphi_bias"], ("1c_B-linear", None): headline_rows[1]["nphi_bias"],
    ("1c_B-abs", None): headline_rows[2]["nphi_bias"], ("1c_B2", None): headline_rows[3]["nphi_bias"],
    ("1c_C", None): headline_rows[4]["nphi_bias"],
}
for r in contrast_rows:
    full_values[(f"1e_{r['label']}_point", None)] = r["point"]
    full_values[(f"1e_{r['label']}_lo", None)] = r["ci_low"]
    full_values[(f"1e_{r['label']}_hi", None)] = r["ci_high"]

print("\n" + "=" * 100)
print("CSV: full precision vs single-rounded 4dp vs v1.9 target, flagged")
print("=" * 100)
out_csv = []
for key, target in v19_targets.items():
    name = key[0]
    full = full_values[key]
    rounded = round(full, 4)
    flag = abs(rounded - target) > 5e-5  # differs at the 4dp display level
    out_csv.append(dict(quantity=name, full_precision=full, single_rounded_4dp=rounded,
                         v19_target=target, flagged_mismatch=flag))
    print(f"  {name:34s} full={full:.10g}  rounded={rounded:+.4f}  target={target:+.4f}  flagged={flag}")

pd.DataFrame(out_csv).to_csv("/Users/ammar/LithoGPT_archive/dk_task1_fullprecision.csv", index=False)
print("\nwritten dk_task1_fullprecision.csv")
print("\nTASK1_FULLPRECISION_COMPLETE")
