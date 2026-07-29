#!/usr/bin/env python3
"""G9: render F1-F5 from the data already saved in figs/ (analysis/build_tables_and_
figdata.py, DQ Gate 3). Runs ONLY inside the ~/lithogpt_plot venv (G8). No statistic is
recomputed here -- every number plotted is read from figs/*.csv, figs/*.npy, or
analysis/FROZEN_RESULTS.json. Light print-safe background, vector PDF + 300dpi PNG."""
import csv
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "axes.edgecolor": "#333333", "axes.labelcolor": "#111111", "text.color": "#111111",
    "xtick.color": "#333333", "ytick.color": "#333333", "font.size": 10,
})
ARM_COLORS = {"A": "#b23a48", "B-linear": "#3b6fb6", "B-abs": "#4fa37a",
              "B2": "#c9722a", "C": "#9a4fbf"}
REAL_COLOR = "#111111"
ARMS = ["A", "B-linear", "B-abs", "B2", "C"]

with open("analysis/FROZEN_RESULTS.json") as f:
    FR = json.load(f)


def save(fig, name):
    fig.savefig(f"figs/{name}.pdf")
    fig.savefig(f"figs/{name}.png", dpi=300)
    plt.close(fig)
    print(f"wrote figs/{name}.pdf and figs/{name}.png")


# ---------------- F1: per-well NPHI bias, 8 wells x 5 arms, with CI, zero line ----------------
rows = list(csv.DictReader(open("figs/F1_data.csv")))
wells = sorted(set(r["well"] for r in rows), key=lambda w: [r["well"] for r in rows].index(w))
wells = list(dict.fromkeys(r["well"] for r in rows))
fig, ax = plt.subplots(figsize=(10, 5))
n_arms = len(ARMS)
width = 0.15
x = np.arange(len(wells))
for i, arm in enumerate(ARMS):
    pts, lo, hi = [], [], []
    for w in wells:
        r = next(r for r in rows if r["well"] == w and r["arm"] == arm)
        p, rmin, rmax = float(r["point"]), float(r["real_min"]), float(r["real_max"])
        # Arm C is deterministic (5 identical realizations); min/max vs mean can differ
        # from p by a ~1e-17 floating-point rounding artifact, occasionally negative.
        # Clipped to 0 here (rendering only -- figs/F1_data.csv itself is untouched).
        pts.append(p); lo.append(max(0.0, p - rmin)); hi.append(max(0.0, rmax - p))
    ax.errorbar(x + (i - n_arms / 2) * width + width / 2, pts, yerr=[lo, hi], fmt="o",
                color=ARM_COLORS[arm], label=arm, capsize=2, markersize=4, elinewidth=1)
ax.axhline(0, color="#999999", linewidth=1, linestyle="--", zorder=0)
ax.set_xticks(x); ax.set_xticklabels(wells, rotation=30, ha="right")
ax.set_ylabel("NPHI bias (generated mean - real mean)")
ax.set_title("F1: per-well NPHI bias, 8 wells x 5 arms\n(error bars: min/max across 5 within-well realizations, descriptive only)")
ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.25), frameon=False)
fig.tight_layout()
save(fig, "F1_per_well_nphi_bias")

# ---------------- F2: three-panel distribution, sharing axes ----------------
real = np.load("figs/F2_real_nphi.npy")
gen = {arm: np.load(f"figs/F2_gen_nphi_{arm.replace('-', '')}.npy") for arm in ARMS}
panels = [("A", "B2", "A vs B2 vs real"), ("B-linear", "B-abs", "B-linear vs B-abs vs real"),
          ("A", "C", "A vs C vs real")]
fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharex=True, sharey=True)
bins = np.linspace(min(real.min(), *[g.min() for g in gen.values()]),
                    max(real.max(), *[g.max() for g in gen.values()]), 60)
for ax, (arm1, arm2, title) in zip(axes, panels):
    ax.hist(real, bins=bins, density=True, histtype="step", color="#111111", linewidth=1.6, label="real")
    ax.hist(gen[arm1], bins=bins, density=True, histtype="step", color=ARM_COLORS[arm1], linewidth=1.4, label=arm1)
    ax.hist(gen[arm2], bins=bins, density=True, histtype="step", color=ARM_COLORS[arm2], linewidth=1.4, label=arm2)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("NPHI")
    ax.legend(frameon=False, fontsize=8)
axes[0].set_ylabel("density")
fig.suptitle("F2: NPHI distribution, pooled across all realizations and 8 test wells")
fig.tight_layout()
save(fig, "F2_nphi_distribution")

# ---------------- F3: NPHI vs depth, binned means, 5 arms + real, Athy overlay ----------------
rows = list(csv.DictReader(open("figs/F3_data.csv")))
depth = np.array([float(r["bin_center_m"]) for r in rows])
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(depth, [float(r["real_mean"]) for r in rows], color="#111111", linewidth=2, marker="o", markersize=3, label="real")
for arm in ARMS:
    ax.plot(depth, [float(r[f"{arm}_mean"]) for r in rows], color=ARM_COLORS[arm], linewidth=1.4, marker="o", markersize=2.5, label=arm)
phi0, lam = FR["athy_frozen_phi0"]["value"], FR["athy_frozen_lambda_m"]["value"]
z = np.linspace(depth.min(), depth.max(), 200)
ax.plot(z, phi0 * np.exp(-z / lam), color="#999999", linewidth=1.5, linestyle="--", label=f"Athy (phi0={phi0}, lambda={lam}m)")
ax.set_xlim(FR["depth_scored_min_m"]["value"], FR["depth_scored_max_m"]["value"])
ax.set_xlabel("depth (m) -- scored window only")
ax.set_ylabel("NPHI, binned mean")
ax.set_title("F3: NPHI vs depth, binned means, scored window only")
ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.18), frameon=False, fontsize=8)
fig.tight_layout()
save(fig, "F3_nphi_vs_depth")

# ---------------- F4: autocorrelation, lags 1-20, real vs A vs C ----------------
rows = list(csv.DictReader(open("figs/F4_data.csv")))
fig, ax = plt.subplots(figsize=(7, 4.5))
for series, color in [("real", "#111111"), ("A", ARM_COLORS["A"]), ("C", ARM_COLORS["C"])]:
    srows = [r for r in rows if r["series"] == series]
    lags = [int(r["lag"]) for r in srows]
    acf = [float(r["acf"]) for r in srows]
    style = "-" if series == "real" else "--"
    ax.plot(lags, acf, style, color=color, marker="o", markersize=3, label=series)
ax.axhline(0, color="#cccccc", linewidth=1)
ax.set_xlabel("lag"); ax.set_ylabel("mean autocorrelation (8 wells)")
ax.set_title("F4: NPHI autocorrelation, lags 1-20")
ax.legend(frameon=False)
fig.tight_layout()
save(fig, "F4_autocorrelation")

# ---------------- F5: per-well depth slope, arms vs real ----------------
b2a_excl0 = FR["loo_slope_contrast_B2_minus_A_loo_min"]  # presence check only
main_branch = True  # per DQ_GATE_1 G1b: B2-A and B-linear-B-abs slope contrasts both
                     # exclude zero with sign stable under all 8 LOO omissions -> the
                     # "render it" branch of 3.4 fires; no quantity here fell into the
                     # "excludes zero but sign flips" fragile branch (ARM_MINUS_REAL_C
                     # excludes zero with SIGN_STABLE=YES, so it doesn't trigger fragile
                     # either) -- see reports/DQ_GATE_9.md for the full branch statement.
rows = list(csv.DictReader(open("figs/F5_data.csv")))
wells = [r["well"] for r in rows]
fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(wells))
ax.plot(x, [float(r["real"]) for r in rows], color="#111111", marker="o", markersize=6, linewidth=0, label="real", zorder=5)
for arm in ARMS:
    ax.plot(x, [float(r[arm]) for r in rows], color=ARM_COLORS[arm], marker="s", markersize=5, linewidth=0, label=arm)
ax.axhline(0, color="#cccccc", linewidth=1)
ax.set_xticks(x); ax.set_xticklabels(wells, rotation=30, ha="right")
ax.set_ylabel("NPHI-depth OLS slope (v/v per 1000 m)")
ax.set_title("F5: per-well depth slope, arms vs real\n"
              "(inferential support: B2 minus A and B-linear minus B-abs slope contrasts exclude zero,\n"
              "sign-stable under all 8 leave-one-out omissions; all other slope quantities descriptive only)")
ax.legend(ncol=6, loc="upper center", bbox_to_anchor=(0.5, -0.30), frameon=False, fontsize=8)
fig.tight_layout()
save(fig, "F5_per_well_depth_slope")

print("\nRENDER_FIGURES_COMPLETE")
