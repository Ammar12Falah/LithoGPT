"""Markdown tables for report.md, built from the result files so that no
number is typed by hand.

    .venv/bin/python -I src/report_tables.py kansas > results/kansas_tables.md
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results"
BANDS = ["same site (<30 m)", "30 m-1 km", "1-5 km", "5-20 km", ">20 km"]
CELLS = ["all items", "far (>1 km)"] + BANDS
M = ["m1_nearest", "m2_plane", "m3_kriging", "m4_thickness", "side_4b_best_route"]
MH = ["1 Nearest", "2 Plane", "3 Kriging", "4 Thickness", "(side) 4b best route"]


def md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def f(x, nd=2):
    return "" if pd.isna(x) else f"{x:.{nd}f}"


def band_table(c, tag, ft=False, what="mae"):
    b = pd.read_csv(R / f"{c}_scores_by_distance{tag}.csv")
    rows = []
    for cell in CELLS:
        g = b[b["cell"] == cell].set_index("method")
        if len(g) == 0 or g["n_items"].iloc[0] == 0:
            rows.append({"Distance to nearest known well with the top": cell, "Items": 0, "Wells": 0})
            continue
        r = {"Distance to nearest known well with the top": cell, "Items": f"{int(g['n_items'].iloc[0]):,}",
             "Wells": f"{int(g['n_wells'].iloc[0]):,}"}
        for m, h in zip(M, MH):
            if m not in g.index:
                continue
            if what == "mae":
                r[h] = f"{f(g.loc[m, 'mae_m'])} ({f(g.loc[m, 'mae_ci_lo_m'])}-{f(g.loc[m, 'mae_ci_hi_m'])})"
            elif what == "p90":
                r[h] = f"{f(g.loc[m, 'p90_m'], 1)} ({f(g.loc[m, 'p90_ci_lo_m'], 1)}-{f(g.loc[m, 'p90_ci_hi_m'], 1)})"
            elif what == "mae_ft":
                r[h] = f"{f(g.loc[m, 'mae_ft'], 1)}"
            elif what == "bias":
                r[h] = f"{f(g.loc[m, 'median_signed_error_m'])}"
        rows.append(r)
    return md(pd.DataFrame(rows).fillna(""))


def main(c):
    s = json.loads((R / f"{c}_summary.json").read_text())
    S = s["settings"]
    feet = (R / f"{c}_scores_by_distance.csv").read_text().splitlines()[0].count("_ft") > 0
    out = []
    out.append(f"### {s['country']}: error by distance, development period\n")
    out.append("Median absolute error in metres, with the 95 % interval from resampling whole wells in brackets.\n")
    out.append(band_table(c, "", what="mae"))
    if feet:
        out.append("\nThe same medians in feet.\n")
        out.append(band_table(c, "", what="mae_ft"))
    out.append("\n90th percentile of the absolute error in metres (95 % interval).\n")
    out.append(band_table(c, "", what="p90"))
    out.append("\nMedian signed error in metres (forecast minus actual; negative means the forecast was too deep).\n")
    out.append(band_table(c, "", what="bias"))

    cov = pd.read_csv(R / f"{c}_m3_range_coverage.csv")
    cov = cov[cov["n_items"] > 0]
    cv = pd.DataFrame({"Distance band": cov["cell"], "Items": cov["n_items"].map("{:,}".format),
                       "Wells": cov["n_wells"].astype(int).map("{:,}".format),
                       "Actual inside the 80 % range": (cov["share_inside_80pct_range"] * 100).map("{:.1f} %".format),
                       "95 % interval": (cov["ci_lo"] * 100).map("{:.1f}".format) + "-" + (cov["ci_hi"] * 100).map("{:.1f} %".format),
                       "Median half width, m": cov["median_half_width_m"].map("{:.1f}".format)})
    out.append(f"\n### {s['country']}: how often the actual value is inside the 80 % range of method 3\n")
    out.append(md(cv))

    bt = pd.read_csv(R / f"{c}_scores_by_top.csv")
    fv = pd.read_csv(R / f"{c}_far_vs_floor_by_top.csv").set_index("top")
    rows = []
    for top in s["chosen_tops_top_down"]:
        for cell in ["all items", "far (>1 km)"]:
            g = bt[(bt["top"] == top) & (bt["cell"] == cell)].set_index("method")
            if len(g) == 0:
                continue
            r = {"Top (shallow to deep)": top, "Items": cell, "n items": f"{int(g['n_items'].iloc[0]):,}",
                 "n wells": f"{int(g['n_wells'].iloc[0]):,}"}
            for m, h in zip(M, MH):
                r[h] = f(g.loc[m, "mae_m"])
            if cell.startswith("far") and top in fv.index:
                r["Floor A, m (pairs)"] = f"{f(fv.loc[top, 'floor_a_m'])} ({int(fv.loc[top, 'floor_a_pairs']):,})"
                r["Best of four / floor A"] = f(fv.loc[top, "ratio"])
            rows.append(r)
    out.append(f"\n### {s['country']}: median absolute error by top, metres\n")
    out.append("In a test well each top is one item, so items and wells are the same number here.\n")
    out.append(md(pd.DataFrame(rows).fillna("")))

    fl = pd.read_csv(R / f"{c}_floors.csv")
    g = fl[fl["top"] == "all chosen tops"]
    ft = pd.DataFrame({"Floor": g["floor"], "Pairs": g["n_pairs"].map("{:,}".format),
                       "Different hole pairs / holes": g["n_hole_pairs"].map("{:,}".format),
                       "Median absolute difference, m": g["median_abs_diff_m"].map(f),
                       "90th percentile, m": g["p90_abs_diff_m"].map(f),
                       "Share exactly zero": (g["share_zero"] * 100).map("{:.1f} %".format)})
    out.append(f"\n### {s['country']}: the floor\n")
    out.append(md(ft))

    out.append(f"\n### {s['country']}: side results\n")
    out.append("No waiting time (known wells = finished before the test well was spudded). Median absolute error, metres (95 % interval).\n")
    out.append(band_table(c, "_no_wait", what="mae"))
    if (R / f"{c}_scores_by_distance_unflagged_only.csv").exists():
        out.append("\nOnly holes without an elevation flag and with a precise position, as test wells and as known wells "
                   "(200 resamples). Median absolute error, metres (95 % interval).\n")
        out.append(band_table(c, "_unflagged_only", what="mae"))

    sc = pd.read_csv(R / f"{c}_sealed_counts.csv")
    out.append(f"\n### {s['country']}: sealed period, counts only\n")
    out.append(md(sc.rename(columns={"what": "Count of", "count": "Number"})))

    ch = pd.read_csv(R / f"{c}_chosen_tops.csv")
    ch = ch[ch["chosen"]].sort_values("order_top_down")
    out.append(f"\n### {s['country']}: chosen tops\n")
    out.append(md(pd.DataFrame({"Order (top down)": ch["order_top_down"].astype(int), "Top": ch["top"],
                                "Holes drilled before the test years that report it": ch["holes_before_test_years"].map("{:,}".format)})))
    nxt = pd.read_csv(R / f"{c}_chosen_tops.csv")
    nxt = nxt[~nxt["chosen"]].head(3)
    out.append("\nNext three, not chosen: " + "; ".join(f"{r.top} ({r.holes_before_test_years:,})" for r in nxt.itertuples()) + ".")

    cl = pd.read_csv(R / f"{c}_cleaning_log.csv").fillna("")
    out.append(f"\n### {s['country']}: cleaning steps and wells left\n")
    cl2 = pd.DataFrame({"Step": cl["step"], "Well records left": cl["well_records"].map(lambda v: "" if v == 0 else f"{int(v):,}"),
                        "Holes left": cl["holes"].map("{:,}".format), "Detail": cl["detail"]})
    out.append(md(cl2))

    out.append(f"\n### {s['country']}: settings (all set on wells drilled before the test years)\n")
    m3 = pd.DataFrame([dict(Top=t, **{"Wells used": v["n"], "Variogram power": v["alpha"], "Nugget ratio r": v["r"]})
                       for t, v in S["m3"].items()])
    out.append(md(m3))
    pre = S["pre_test_year_check"]
    out.append(f"\nMethod 2 uses the {S['m2_n']} nearest known wells. Outlier screening of neighbours: {'on' if S['screen'] else 'off'} "
               f"(drop a neighbour more than max({S['screen_k']:.0f} x 1.4826 x MAD, {S['screen_min_m']:.0f} m) off the local plane). "
               f"Thickness kriging: {S['th_n']} nearest wells, power {S['th_alpha']}, nugget ratio {S['th_r']}, "
               f"{'linear' if S['th_linear'] else 'constant'} local mean. Thickness chain: {S['m4_chain'].replace('_', ' ')}, "
               f"support = at least {S['support_min_wells']} known wells within {S['support_radius_m'] / 1000:.0f} km. "
               f"Multiplier on the 80 % range: {S['interval_calib']:.3f} (coverage before the multiplier on the pre-test-year check: "
               f"{S['interval_cover_before_calib'] * 100:.1f} %).")
    pr = pd.DataFrame([dict(Method=h, **{"Items": f"{pre['by_method'][m]['n_items']:,}",
                                         "Median abs error, m": f(pre["by_method"][m]["mae_m"]),
                                         "90th percentile, m": f(pre["by_method"][m]["p90_m"], 1),
                                         "Far items": f"{pre['by_method'][m]['n_far']:,}",
                                         "Median abs error far, m": f(pre["by_method"][m]["mae_far_m"])})
                       for m, h in zip(M, MH) if m in pre["by_method"]])
    out.append(f"\nCheck on wells drilled before the test years ({pre['wells']:,} sampled wells, same date rule; "
               f"80 % range of method 3 held the actual value {pre['m3_cover80'] * 100:.1f} % of the time):\n")
    out.append(md(pr))
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1])
