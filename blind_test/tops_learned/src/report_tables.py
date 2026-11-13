"""Markdown tables for report.md, built from the result files so that no
number in a table is typed by hand. Also refreshes hashes.txt.

    .venv/bin/python -I src/report_tables.py
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results"
BANDS = ["same site (<30 m)", "30 m-1 km", "1-5 km", "5-20 km", ">20 km"]
CELLS = ["all items", "far (>1 km)"] + BANDS
MAIN = ["m1", "m2", "m3", "m4", "m4b", "B", "C", "D"]
HEAD = {"m1": "A1 nearest", "m2": "A2 plane", "m3": "A3 kriging", "m4": "A4 thickness", "m4b": "A side 4b",
        "B": "B drift-corrected kriging", "C": "C learned", "D": "D drift-only",
        "C_shuffled": "C on shuffled targets", "C_strict": "C, targets known before scoring half",
        "C_pre": "C, targets before test years"}


def md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def f(x, nd=2):
    return "" if pd.isna(x) else f"{x:.{nd}f}"


def country_tables(c):
    s = json.loads((R / f"{c}_summary.json").read_text())
    S2 = json.loads((R / f"{c}_settings_learned.json").read_text())
    nd = 2 if s["far_median_abs_error_m"]["m3"] < 20 else 1
    b = pd.read_csv(R / f"{c}_scores_by_distance.csv")
    out = [f"### {s['country']}: error by distance on the scoring half\n",
           "Median absolute error in metres. In brackets: the mean absolute error.\n"]
    rows = []
    for cell in CELLS:
        g = b[b["cell"] == cell].set_index("key")
        if len(g) == 0:
            continue
        r = {"Distance to nearest known well with the layer": cell, "Items": f"{int(g['n_items'].iloc[0]):,}",
             "Wells": f"{int(g['n_wells'].iloc[0]):,}"}
        for m in MAIN:
            r[HEAD[m]] = f"{f(g.loc[m, 'median_abs_error_m'], nd)} ({f(g.loc[m, 'mean_abs_error_m'], nd)})"
        rows.append(r)
    out.append(md(pd.DataFrame(rows)))
    out.append("\n95 % interval of the median absolute error (resampling whole wells), far items and all items.\n")
    rows = []
    for cell in ["far (>1 km)", "all items"]:
        g = b[b["cell"] == cell].set_index("key")
        r = {"Items": cell}
        for m in MAIN:
            r[HEAD[m]] = f"{f(g.loc[m, 'median_ci_lo_m'], nd)}-{f(g.loc[m, 'median_ci_hi_m'], nd)}"
        rows.append(r)
    out.append(md(pd.DataFrame(rows)))
    out.append("\nMedian signed error in metres (forecast minus actual).\n")
    rows = []
    for cell in CELLS:
        g = b[b["cell"] == cell].set_index("key")
        if len(g) == 0:
            continue
        r = {"Distance band": cell}
        for m in MAIN:
            r[HEAD[m]] = f(g.loc[m, "median_signed_error_m"], nd)
        rows.append(r)
    out.append(md(pd.DataFrame(rows)))

    v = pd.read_csv(R / f"{c}_learned_vs_others.csv")
    out.append(f"\n### {s['country']}: the learned model C against each other method, same items\n")
    out.append("Relative improvement in median absolute error (positive: C is better), with the 95 % interval from resampling whole wells.\n")
    rows = []
    for m in ["m1", "m2", "m3", "m4", "m4b", "B", "D"]:
        r = {"C against": HEAD[m]}
        for cell in ["far (>1 km)", "all items"] + BANDS:
            g = v[(v["model_key"] == "C") & (v["against_key"] == m) & (v["cell"] == cell)]
            r[cell] = "" if len(g) == 0 else f"{f(g['improvement_pct'].iloc[0], 1)} % ({f(g['ci_lo_pct'].iloc[0], 1)} to {f(g['ci_hi_pct'].iloc[0], 1)})"
        rows.append(r)
    out.append(md(pd.DataFrame(rows)))
    out.append("\nThe other models against the best simple method and against kriging, far items.\n")
    rows = []
    best = s["best_simple_method"]
    for who in ["C", "D", "C_shuffled", "C_strict", "C_pre"]:
        r = {"Model": HEAD[who], "Far median abs error, m": f(s["far_median_abs_error_m"][who], nd)}
        for m, lab in [(best, f"against best simple ({HEAD[best]})"), ("m3", "against kriging")]:
            g = v[(v["model_key"] == who) & (v["against_key"] == m) & (v["cell"] == "far (>1 km)")]
            r[lab] = "" if len(g) == 0 else f"{f(g['improvement_pct'].iloc[0], 1)} % ({f(g['ci_lo_pct'].iloc[0], 1)} to {f(g['ci_hi_pct'].iloc[0], 1)})"
        rows.append(r)
    out.append(md(pd.DataFrame(rows)))

    bl = pd.read_csv(R / f"{c}_scores_by_layer.csv")
    out.append(f"\n### {s['country']}: by layer, scoring half\n")
    out.append("Median absolute error in metres (mean in brackets). In a well each layer is one item, so items and wells are the same number.\n")
    rows = []
    for layer in list(dict.fromkeys(bl["layer"])):
        for cell in ["all items", "far (>1 km)"]:
            g = bl[(bl["layer"] == layer) & (bl["cell"] == cell)].set_index("key")
            if len(g) == 0:
                continue
            r = {"Layer (shallow to deep)": layer, "Items": cell, "n": f"{int(g['n_items'].iloc[0]):,}"}
            for m in MAIN:
                r[HEAD[m]] = f"{f(g.loc[m, 'median_abs_error_m'], nd)} ({f(g.loc[m, 'mean_abs_error_m'], nd)})"
            rows.append(r)
    out.append(md(pd.DataFrame(rows)))

    cv = pd.read_csv(R / f"{c}_range_coverage.csv")
    out.append(f"\n### {s['country']}: how often the actual value is inside the 80 % range\n")
    out.append(md(pd.DataFrame({
        "Distance band": cv["cell"], "Items": cv["n_items"].map("{:,}".format), "Wells": cv["n_wells"].map("{:,}".format),
        "Learned model C": (cv["learned_model_share_inside"] * 100).map("{:.1f} %".format),
        "Kriging": (cv["kriging_share_inside"] * 100).map("{:.1f} %".format),
        "Median width C, m": cv["learned_model_median_width_m"].map(lambda x: f(x, 1)),
        "Median width kriging, m": cv["kriging_median_width_m"].map(lambda x: f(x, 1))})))

    out.append(f"\n### {s['country']}: choices made on the tuning half\n")
    mc, mdd = S2["model_C"], S2["model_D"]
    pv = S2["tuning_half_preview_models_fit_before_test_years"]
    tk = S2["tuning_half_kriging"]
    out.append(md(pd.DataFrame([
        {"Model": "C learned", "Target divided by kriging spread": "yes" if mc["target_scaled_by_kriging_sd"] else "no",
         "Weight of far items": mc["far_weight"], "Leaves": mc["num_leaves"], "Min items per leaf": mc["min_data_in_leaf"],
         "Trees": mc["best_rounds"], "Features": S2["features_C"]},
        {"Model": "D drift-only", "Target divided by kriging spread": "yes" if mdd["target_scaled_by_kriging_sd"] else "no",
         "Weight of far items": mdd["far_weight"], "Leaves": mdd["num_leaves"], "Min items per leaf": mdd["min_data_in_leaf"],
         "Trees": mdd["best_rounds"], "Features": S2["features_D"]}])))
    win = S2["drift_window_years"]
    out.append(f"\nTraining targets from before the test years: {S2['n_training_items_before_test_years']:,} items in "
               f"{S2['n_training_wells_before_test_years']:,} wells (dated from {S2['load']['train_from']}). "
               f"Tuning half: {S2['n_tuning_items']:,} items in {S2['n_tuning_wells']:,} wells, {S2['n_tuning_far_items']:,} far items. "
               f"Drift table of method B: targets of the last {win if win else 'all'} years before the scoring half "
               f"({S2['drift_table_targets']:,} items). "
               f"Side model 'targets known before the scoring half': {S2['strict_side_model_training_items']:,} items, "
               f"actual values finished on or before {S2['load']['strict_known_date']}.")
    out.append(f"\nWhat the tuning half showed (far items; models fitted only on targets from before the test years, but with "
               f"settings picked on this same half, so these numbers flatter the models): kriging {f(tk['mae_far'], nd)} m, "
               f"C {f(pv['C']['mae_far'], nd)} m, D {f(pv['D']['mae_far'], nd)} m.")
    return "\n".join(out)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def main():
    for c in ["kansas", "netherlands"]:
        if (R / f"{c}_summary.json").exists():
            (R / f"{c}_tables.md").write_text(country_tables(c) + "\n")
    lines = [f"{sha256(p)}  results/{p.name}" for p in sorted(R.glob("*")) if p.is_file()]
    (ROOT / "hashes.txt").write_text("\n".join(lines) + "\n")
    print("tables and hashes.txt written;", len(lines), "result files")


if __name__ == "__main__":
    sys.exit(main())
