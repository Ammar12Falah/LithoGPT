#!/usr/bin/env python3
"""G3: T1-T3 tables (CSV + LaTeX booktabs) and the exact numeric data each of F1-F5
would plot. matplotlib is NOT installed on this Mac and section 0 forbids installs, so
no PNG/PDF is produced here (reported, not worked around) -- but every number each
figure needs is computed and saved so the image render is a pure plotting step once
matplotlib is available, not a re-analysis."""
import json
import csv
import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance

RAW_PATH = "/Users/ammar/LithoGPT_archive/atce_ablation_v3_raw_results_2026-07-26.json"
FORCE_CSV = "/Users/ammar/LithoGPT_archive/force2020_data/train.csv"
GR_IDX, RDEP_IDX, NPHI_IDX, RHOB_IDX = 0, 1, 2, 3
FEATURES = ["GR", "RDEP", "NPHI", "RHOB"]
ARMS = ["A", "B-linear", "B-abs", "B2", "C"]
CONTEXT, PRIME_FRAC, MAX_GEN_LEN = 512, 0.25, 20000
SEED = 20260715

with open(RAW_PATH) as f:
    raw = json.load(f)
WELLS = list(raw["A"].keys())

with open("analysis/FROZEN_RESULTS.json") as f:
    FR = json.load(f)


def autocorr(x, max_lag=20):
    x = np.asarray(x, dtype=np.float64); x = x - np.mean(x)
    n = len(x)
    if n < max_lag + 2:
        return np.full(max_lag, np.nan)
    var = np.var(x)
    if var < 1e-12:
        return np.zeros(max_lag)
    return np.array([np.mean(x[:n - lag] * x[lag:]) / var for lag in range(1, max_lag + 1)])


import os
os.makedirs("figs", exist_ok=True)

# ---------------- T1: headline table, 5 metrics x 5 arms ----------------
METRICS = ["nphi_bias", "nphi_w1", "nphi_ac_rmse", "gr_bias", "rhob_bias"]
with open("figs/T1_headline.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["arm"] + METRICS)
    for arm in ARMS:
        row = [arm] + [f"{FR[f'headline_{m}_{arm}']['value']:.10g}" for m in METRICS]
        w.writerow(row)
with open("figs/T1_headline.tex", "w") as f:
    f.write("% W1 call signature: scipy.stats.wasserstein_distance(real_nphi, gen_nphi), per realization, mean over 5 reals then over 8 wells (equal-weight)\n")
    f.write("\\begin{tabular}{lrrrrr}\n\\toprule\n")
    f.write("Arm & NPHI bias & NPHI $W_1$ & NPHI ACF RMSE & GR bias & RHOB bias \\\\\n\\midrule\n")
    for arm in ARMS:
        vals = [FR[f'headline_{m}_{arm}']['value'] for m in METRICS]
        f.write(f"{arm} & {vals[0]:+.4f} & {vals[1]:.4f} & {vals[2]:.4f} & {vals[3]:+.3f} & {vals[4]:+.4f} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# ---------------- T2 / T3: guard tables, signed and magnitude ----------------
CONTRASTS = [("A", "B2", "B2_minus_A", "B2 minus A"), ("A", "B-abs", "B-abs_minus_A", "B-abs minus A"),
             ("B-abs", "B-linear", "B-linear_minus_B-abs", "B-linear minus B-abs"), ("A", "C", "C_minus_A", "C minus A")]
GUARDS = [("GR", "GR"), ("RHOB", "RHOB"), ("NPHI_ACF_RMSE", "NPHI ACF RMSE")]

for convention, fname_csv, fname_tex in [("signed", "figs/T2_guard_signed.csv", "figs/T2_guard_signed.tex"),
                                          ("magnitude", "figs/T3_guard_magnitude.csv", "figs/T3_guard_magnitude.tex")]:
    with open(fname_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["contrast", "metric", "point", "ci_low", "ci_high", "excludes_zero"])
        for _, _, label, disp in CONTRASTS:
            for mkey, mdisp in GUARDS:
                k = f"guard_{convention}_{label}_{mkey}"
                w.writerow([disp, mdisp, f"{FR[k+'_point']['value']:.10g}", f"{FR[k+'_ci_low']['value']:.10g}",
                            f"{FR[k+'_ci_high']['value']:.10g}", FR[k+'_excludes_zero']['value']])
    with open(fname_tex, "w") as f:
        f.write("\\begin{tabular}{llrrrl}\n\\toprule\n")
        f.write("Contrast & Metric & Point & CI low & CI high & Excludes zero \\\\\n\\midrule\n")
        for _, _, label, disp in CONTRASTS:
            for mkey, mdisp in GUARDS:
                k = f"guard_{convention}_{label}_{mkey}"
                p, lo, hi, ex = FR[k+'_point']['value'], FR[k+'_ci_low']['value'], FR[k+'_ci_high']['value'], FR[k+'_excludes_zero']['value']
                f.write(f"{disp} & {mdisp} & {p:+.4f} & {lo:+.4f} & {hi:+.4f} & {'YES' if ex else 'no'} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n")
print("T1/T2/T3 written.")

# ---------------- F1 data: per-well NPHI bias, 8 wells x 5 arms, with within-well realization CI ----------------
f1_rows = []
for arm in ARMS:
    for w in WELLS:
        d = raw[arm][w]
        real_nphi = np.array(d["real"], dtype=np.float64)[:, NPHI_IDX]
        gens = np.array(d["generated_realizations"], dtype=np.float64)
        per_real_bias = [float(g[:, NPHI_IDX].mean() - real_nphi.mean()) for g in gens]
        point = float(np.mean(per_real_bias))
        lo, hi = float(np.min(per_real_bias)), float(np.max(per_real_bias))
        f1_rows.append(dict(arm=arm, well=w, point=point, real_min=lo, real_max=hi))
with open("figs/F1_data.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["arm", "well", "point", "real_min", "real_max"])
    w.writeheader(); w.writerows(f1_rows)
print("F1 data written (caption note: error band = min/max across the 5 within-well realizations, descriptive only, NOT the well-level paired bootstrap used for inference).")

# ---------------- F2 data: pooled NPHI values for A, B2, B-linear, B-abs, C, real ----------------
for arm in ["A", "B2", "B-linear", "B-abs", "C"]:
    vals = np.concatenate([np.array(raw[arm][w]["generated_realizations"], dtype=np.float64)[:, :, NPHI_IDX].ravel() for w in WELLS])
    np.save(f"figs/F2_gen_nphi_{arm.replace('-','')}.npy", vals)
real_vals = np.concatenate([np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX] for w in WELLS])
np.save("figs/F2_real_nphi.npy", real_vals)
print("F2 data written (3 panels: A/B2/real, B-linear/B-abs/real, A/C/real).")

# ---------------- F3 data: NPHI vs depth, binned means, 5 arms + real, Athy curve params ----------------
df = pd.read_csv(FORCE_CSV, sep=";")
depth_all, real_all, arm_all = [], [], {arm: [] for arm in ARMS}
for w in WELLS:
    wdf = df[df["WELL"] == w].sort_values("DEPTH_MD")
    depth = wdf["DEPTH_MD"].to_numpy(dtype=np.float64)
    feats = wdf[FEATURES].to_numpy(dtype=np.float64)
    valid = np.isfinite(feats).all(axis=1)
    depth_v = depth[valid]
    n = len(depth_v)
    prime_n = max(CONTEXT, int(n * PRIME_FRAC))
    gen_len = min(n - prime_n, MAX_GEN_LEN)
    dscored = depth_v[prime_n:prime_n + gen_len]
    depth_all.append(dscored)
    real_all.append(np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX])
    for arm in ARMS:
        gens = np.array(raw[arm][w]["generated_realizations"], dtype=np.float64)[:, :, NPHI_IDX]
        arm_all[arm].append(gens.mean(axis=0))
depth_all = np.concatenate(depth_all)
real_all = np.concatenate(real_all)
bins = np.linspace(FR["depth_scored_min_m"]["value"], FR["depth_scored_max_m"]["value"], 21)
bin_idx = np.digitize(depth_all, bins) - 1
bin_centers = (bins[:-1] + bins[1:]) / 2
f3_rows = []
for bi in range(len(bins) - 1):
    mask = bin_idx == bi
    if mask.sum() == 0:
        continue
    row = dict(bin_center_m=float(bin_centers[bi]), n=int(mask.sum()), real_mean=float(real_all[mask].mean()))
    for arm in ARMS:
        arm_concat = np.concatenate(arm_all[arm])
        row[f"{arm}_mean"] = float(arm_concat[mask].mean())
    f3_rows.append(row)
with open("figs/F3_data.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(f3_rows[0].keys()))
    w.writeheader(); w.writerows(f3_rows)
print(f"F3 data written, {len(f3_rows)} depth bins over [{bins[0]:.1f},{bins[-1]:.1f}] m (scored window). "
      f"Athy overlay: phi0={FR['athy_frozen_phi0']['value']}, lambda={FR['athy_frozen_lambda_m']['value']}m, "
      f"formula phi(z)=phi0*exp(-z/lambda) -- caption must state x-axis is the SCORED window only.")

# ---------------- F4 data: autocorrelation, lags 1-20, real vs A vs C ----------------
f4_rows = []
for arm_label, arm_key in [("real", None), ("A", "A"), ("C", "C")]:
    acs = []
    for w in WELLS:
        if arm_key is None:
            x = np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX]
            acs.append(autocorr(x))
        else:
            gens = np.array(raw[arm_key][w]["generated_realizations"], dtype=np.float64)[:, :, NPHI_IDX]
            acs.append(np.mean([autocorr(g) for g in gens], axis=0))
    mean_ac = np.nanmean(np.array(acs), axis=0)
    for lag in range(1, 21):
        f4_rows.append(dict(series=arm_label, lag=lag, acf=float(mean_ac[lag - 1])))
with open("figs/F4_data.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["series", "lag", "acf"])
    w.writeheader(); w.writerows(f4_rows)
print("F4 data written (real vs A vs C, lags 1-20, mean over 8 wells).")

# ---------------- F5 data: per-well depth slope, arms vs real (authorized per DQ_GATE_1 threshold 3.4) ----------------
f5_rows = []
for w in WELLS:
    row = {"well": w, "real": FR.get(f"slope_real_{w}", {}).get("value")}
    for arm in ARMS:
        row[arm] = FR.get(f"slope_arm_{arm}_{w}", {}).get("value")
    f5_rows.append(row)
with open("figs/F5_data.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["well", "real"] + ARMS)
    w.writeheader(); w.writerows(f5_rows)
print("F5 data written (authorized by DQ_GATE_1 threshold-3.4 check: B2 minus A and B-linear minus B-abs slope "
      "contrasts both exclude zero with sign stable under all 8 leave-one-out omissions).")

print("\nBUILD_TABLES_AND_FIGDATA_COMPLETE")
