"""A2 tables and chart: learning curve, Mark 1 and the power check.

Reads curve/learning_curve_runs.csv and curve/learning_curve_by_well.csv (made by a2_model.py curve).
Writes curve/learning_curve.csv, curve/learning_curve.png, curve/power_check.csv, curve/mark1.csv.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT  # noqa: E402

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#1a1a19", "#f0efec", "#c3c2b7", "#898781", "#2c2c2a", "#383835"
SERIES = [("tolerant_all", "Tolerant agreement (headline)", "#3987e5"), ("strict_all", "Strict agreement", "#d95926"),
          ("soft_all", "Soft agreement", "#199e70"), ("balanced_all", "Balanced agreement", "#c98500")]


def main():
    runs = pd.read_csv(ROOT / "curve" / "learning_curve_runs.csv")
    byw = pd.read_csv(ROOT / "curve" / "learning_curve_by_well.csv")
    plain = runs[runs.reader == "plain model"]
    rows = []
    for n, g in plain.groupby("n_wells"):
        r = {"n_wells": n, "draws": len(g)}
        for k, _, _ in SERIES:
            v = 100 * g[k]
            r[k.replace("_all", "") + "_mean"] = round(v.mean(), 1)
            r[k.replace("_all", "") + "_min"] = round(v.min(), 1)
            r[k.replace("_all", "") + "_max"] = round(v.max(), 1)
            r[k.replace("_all", "") + "_sd"] = round(v.std(ddof=1), 1) if len(g) > 1 else np.nan
        rows.append(r)
    lc = pd.DataFrame(rows)
    ten = runs[runs.reader.str.startswith("ten-well")].iloc[0]
    shale = runs[runs.reader == "all-shale line"].iloc[0]
    for name, s in [("ten-well model (the 10 example wells)", ten), ("all-shale line", shale)]:
        r = {"n_wells": name, "draws": 1}
        for k, _, _ in SERIES:
            r[k.replace("_all", "") + "_mean"] = round(100 * s[k], 1)
        lc = pd.concat([lc, pd.DataFrame([r])], ignore_index=True)
    lc.to_csv(ROOT / "curve" / "learning_curve.csv", index=False)
    print(lc.to_string(index=False))

    # ---- Mark 1: 70-well model against the mean of the five ten-well draws, headline number ----
    t70 = 100 * float(plain[plain.n_wells == 70].tolerant_all.iloc[0])
    t10 = 100 * plain[plain.n_wells == 10].tolerant_all
    gap = t70 - t10.mean()
    alt = {}
    for k in ("strict_all", "balanced_all", "soft_all"):
        alt[k] = 100 * float(plain[plain.n_wells == 70][k].iloc[0]) - 100 * plain[plain.n_wells == 10][k].mean()
    mark1 = pd.DataFrame([{
        "tolerant_70_wells_pct": round(t70, 1), "tolerant_10_wells_mean_of_5_draws_pct": round(t10.mean(), 1),
        "ten_well_draws_min_pct": round(t10.min(), 1), "ten_well_draws_max_pct": round(t10.max(), 1),
        "gap_points": round(gap, 1), "mark1": "pass" if gap >= 5 else "fail",
        "gap_strict_points": round(alt["strict_all"], 1), "gap_balanced_points": round(alt["balanced_all"], 1),
        "gap_soft_points": round(alt["soft_all"], 1),
        "mark1_if_strict": "pass" if alt["strict_all"] >= 5 else "fail",
        "mark1_if_balanced": "pass" if alt["balanced_all"] >= 5 else "fail"}])
    mark1.to_csv(ROOT / "curve" / "mark1.csv", index=False)
    print(mark1.T.to_string())

    # ---- power check: well-by-well gap between the 70-well model and the ten-well draws ----
    w70 = byw[(byw.reader == "plain model") & (byw.n_wells == 70)].set_index("well").tolerant_all * 100
    w10 = byw[(byw.reader == "plain model") & (byw.n_wells == 10)]
    per_draw = w10.pivot(index="well", columns="draw", values="tolerant_all") * 100
    gaps = per_draw.rsub(w70, axis=0)              # 70-well minus each ten-well draw, per well
    mean_gap = gaps.mean(axis=1)                    # per well, averaged over the five draws
    sd_wells = float(mean_gap.std(ddof=1))
    sd_single = float(np.mean([gaps[c].std(ddof=1) for c in gaps.columns]))
    rng = np.random.default_rng(20261115)
    # how often would 5 random curve wells show the true sign with a gap of at least 5 points and 4 of 5 wells ahead?
    wells = mean_gap.index.to_numpy()
    n_items = byw[(byw.reader == "plain model") & (byw.n_wells == 70)].set_index("well").n_items
    hits = 0
    pooled5 = []
    for _ in range(20000):
        pick = rng.choice(wells, size=5, replace=False)
        d = int(rng.choice(gaps.columns))
        g = gaps.loc[pick, d]
        w = n_items[pick]
        pooled = float(np.average(g, weights=w))
        pooled5.append(pooled)
        if pooled >= 5 and (g > 0).sum() >= 4:
            hits += 1
    pooled5 = np.array(pooled5)
    pc = pd.DataFrame([{
        "curve_wells": len(wells),
        "mean_well_gap_points": round(float(mean_gap.mean()), 1),
        "median_well_gap_points": round(float(mean_gap.median()), 1),
        "sd_of_well_gap_points_avg_over_draws": round(sd_wells, 1),
        "sd_of_well_gap_points_single_draw": round(sd_single, 1),
        "min_well_gap": round(float(mean_gap.min()), 1), "max_well_gap": round(float(mean_gap.max()), 1),
        "wells_with_70_ahead": int((mean_gap > 0).sum()),
        "standard_error_with_5_wells_points": round(sd_single / np.sqrt(5), 1),
        "smallest_gap_5_wells_can_show_points_2se": round(2 * sd_single / np.sqrt(5), 1),
        "five_random_curve_wells_pooled_gap_p05": round(float(np.percentile(pooled5, 5)), 1),
        "five_random_curve_wells_pooled_gap_p50": round(float(np.percentile(pooled5, 50)), 1),
        "five_random_curve_wells_pooled_gap_p95": round(float(np.percentile(pooled5, 95)), 1),
        "share_of_5_well_draws_that_call_70_ahead_pct": round(100 * hits / 20000, 1)}])
    pc.to_csv(ROOT / "curve" / "power_check.csv", index=False)
    gaps.round(1).assign(mean_over_draws=mean_gap.round(1)).to_csv(ROOT / "curve" / "power_check_by_well.csv")
    print(pc.T.to_string())

    # ---- chart (dark background) ----
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, ax = plt.subplots(figsize=(9.5, 5.6), dpi=130)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ns = sorted(plain.n_wells.unique())
    for k, label, col in SERIES:
        g = plain.groupby("n_wells")[k]
        mean, lo, hi = 100 * g.mean(), 100 * g.min(), 100 * g.max()
        ax.fill_between(ns, lo[ns], hi[ns], color=col, alpha=0.16, lw=0)
        ax.plot(ns, mean[ns], color=col, lw=2, marker="o", ms=6, mec=SURFACE, mew=1.5, label=label)
        ax.annotate(f"{mean[ns[-1]]:.1f}", (ns[-1], mean[ns[-1]]), xytext=(8, 0), textcoords="offset points",
                    color=INK, fontsize=9, va="center")
    ax.axhline(100 * shale.tolerant_all, color=MUTED, lw=1.2, ls=(0, (4, 3)))
    ax.text(1.02, 100 * shale.tolerant_all + 0.8, f"All-shale line, tolerant {100 * shale.tolerant_all:.1f}",
            color=INK2, fontsize=8.5, va="bottom")
    ax.scatter([10], [100 * ten.tolerant_all], marker="D", s=48, facecolor="none", edgecolor=INK, lw=1.4, zorder=5)
    ax.annotate(f"Ten-well model (the 10 example wells), tolerant {100 * ten.tolerant_all:.1f}",
                (10, 100 * ten.tolerant_all), xytext=(10, -16), textcoords="offset points", color=INK2, fontsize=8.5)
    ax.set_xscale("log")
    ax.set_xticks(ns)
    ax.set_xticklabels([str(n) for n in ns])
    ax.minorticks_off()
    ax.set_xlim(0.85, 110)
    ax.set_xlabel("Expert-labelled wells used for training (drawn from the pool of 70)", color=INK2)
    ax.set_ylabel("Agreement with expert labels on the 23 curve wells (%)", color=INK2)
    ax.tick_params(colors=MUTED, length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(AXIS)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    leg = ax.legend(loc="lower right", frameon=False, fontsize=9)
    for t in leg.get_texts():
        t.set_color(INK)
    ax.set_title("Learning curve of the plain log model: more expert wells, higher agreement",
                 color=INK, fontsize=12, loc="left", pad=14)
    fig.text(0.012, 0.012, "Line = mean of five random draws of wells (one model at 70). Band = lowest to highest draw. "
             "Unread items do not occur: the model gives a class at every depth step.", color=MUTED, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(ROOT / "curve" / "learning_curve.png", facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    main()
