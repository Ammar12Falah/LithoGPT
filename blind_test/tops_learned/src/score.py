"""Stage 2: score the frozen models.

    .venv/bin/python -I src/score.py --final [kansas] [netherlands]   # the scoring half, once
    .venv/bin/python -I src/score.py [kansas] [netherlands]           # rehearsal on the tuning half

The rehearsal runs the same code on the tuning half (which the final models
were fitted on, so its numbers mean nothing) and writes to cache/rehearsal/.
It exists so that the scoring code could be tested before the scoring half
was touched.

Before anything is scored the script checks that every model file, the drift
table and the settings have the sha256 recorded in results/model_hashes.json.
"""
import hashlib
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import checks as CH          # noqa: E402
import features as FE        # noqa: E402
import safe_load as SL       # noqa: E402
import train as TR           # noqa: E402
from safe_load import pipeline as P  # noqa: E402

ROOT = SL.ROOT
SEED = 20261113
N_BOOT = 2000
FAR_M = 1000.0
BANDS = P.BANDS
SIMPLE = ["m1", "m2", "m3", "m4", "m4b", "B"]
NAMES = {"m1": "A1 nearest known well", "m2": "A2 local plane", "m3": "A3 kriging", "m4": "A4 thickness method",
         "m4b": "A side 4b best route", "B": "B drift-corrected kriging", "C": "C learned model",
         "D": "D drift-only model", "C_shuffled": "C trained on shuffled targets",
         "C_strict": "side: C, only targets known before the scoring half",
         "C_pre": "side: C, only targets from before the test years"}
ALL = ["m1", "m2", "m3", "m4", "m4b", "B", "C", "D", "C_shuffled", "C_strict", "C_pre"]


def verify_frozen(country):
    hashes = json.loads((ROOT / "results" / "model_hashes.json").read_text())
    n = 0
    for rel, h in hashes.items():
        if f"{country}_" in rel or rel.endswith("features.csv"):
            assert TR.sha256(ROOT / rel) == h, f"{rel} is not the frozen file"
            n += 1
    return n


def predict_all(country, items, X):
    S2 = json.loads((ROOT / "results" / f"{country}_settings_learned.json").read_text())
    feats = pd.read_csv(ROOT / "results" / "features.csv")
    cols_c = list(feats.loc[feats["in_model_C"], "feature"])
    cols_d = list(feats.loc[feats["in_drift_only_model_D"], "feature"])
    assert list(X.columns) == cols_c
    load = lambda name: lgb.Booster(model_file=str(ROOT / "models" / f"{country}_{name}.txt"))
    m3 = items["m3"].to_numpy()
    sc = np.maximum(items["sd3"].to_numpy(), 1e-3) if S2["model_C"]["target_scaled_by_kriging_sd"] else np.ones(len(items))
    out = pd.DataFrame({k: items[k].to_numpy() for k in ["m1", "m2", "m3", "m4", "m4b"]})
    out["B"] = TR.apply_drift(pd.read_csv(ROOT / "results" / f"{country}_drift_table.csv"), items)
    out["C"] = m3 + load("C").predict(X[cols_c]) * sc
    out["D"] = m3 + load("D").predict(X[cols_d])
    out["C_shuffled"] = m3 + load("C_shuffled").predict(X[cols_c]) * sc
    out["C_strict"] = m3 + load("C_strict").predict(X[cols_c]) * sc
    out["C_pre"] = m3 + load("C_fit_before_test_years_only").predict(X[cols_c]) * sc
    off = S2["range_offset_in_target_units"]
    out["C_lo"] = m3 + (load("C_q10").predict(X[cols_c]) - off) * sc
    out["C_hi"] = m3 + (load("C_q90").predict(X[cols_c]) + off) * sc
    return out, S2


def own_pick_perturbation(country, ctx, cfg, S, wells, items, X, n_sample):
    """Change every pick of a test well (and of the sidetracks of its hole
    system) by a large amount and build its features again. No feature and
    no simple-method forecast may move. As a control, the same change is then
    made to the nearest known well instead: there the features must move."""
    rng = np.random.default_rng(SEED + 11)
    sample = np.sort(rng.choice(wells, size=min(n_sample, len(wells)), replace=False))
    pools = list(ctx._pools.values()) + list(ctx._pairs.values())
    hole_of_item = items["hole"].to_numpy()
    fcols = ["m1", "m2", "m3", "m4", "m4b", "hw3", "sd3", "d1"]

    def shake(holes_):
        """Add 137 m to every value these holes supply. Returns what is needed to put the exact old values back."""
        saved = []
        for p in pools:
            rows = np.nonzero(np.isin(p.hole_idx, holes_))[0]
            if len(rows):
                saved.append((p, rows, p.val[rows].copy()))
                p.val[rows] += 137.0
        return saved

    def restore(saved):
        for p, rows, old in saved:
            p.val[rows] = old
    changed_own = changed_control = n_items = 0
    for w in sample:
        base_rows = np.nonzero(hole_of_item == w)[0]
        own = np.nonzero(ctx.system == ctx.system[w])[0]
        saved = shake(own)
        it2, X2 = FE.build(ctx, cfg, S, np.array([w]))
        restore(saved)
        a = np.c_[X.iloc[base_rows].to_numpy(float), items.iloc[base_rows][fcols].to_numpy(float)]
        b = np.c_[X2.to_numpy(float), it2[fcols].to_numpy(float)]
        same = (a.shape == b.shape) and bool(np.array_equal(a, b, equal_nan=True))
        changed_own += 0 if same else 1
        n_items += len(base_rows)
        # control: the nearest known well of the first item's layer
        j = int(items["top"].iloc[base_rows[0]])
        pool = ctx.pool(j)
        r0 = base_rows[0]
        idx, _ = pool.known_neighbours(np.array([items["x"].iloc[r0]]), np.array([items["y"].iloc[r0]]), np.array([w]),
                                       np.array([items["cut_day"].iloc[r0]]), 1)
        nb = np.array([pool.hole_idx[idx[0, 0]]])
        saved = shake(nb)
        it3, X3 = FE.build(ctx, cfg, S, np.array([w]))
        restore(saved)
        c = np.c_[X3.to_numpy(float), it3[fcols].to_numpy(float)]
        changed_control += 0 if np.array_equal(a, c, equal_nan=True) else 1
    return dict(wells_tested=int(len(sample)), items_tested=int(n_items), wells_where_a_feature_moved=int(changed_own),
                control_wells_where_features_moved=int(changed_control),
                passed=bool(changed_own == 0 and changed_control == len(sample)))


def score_tables(country, items, pred, tops, outdir, tag=""):
    rng = np.random.default_rng(SEED + 1)
    actual = items["actual"].to_numpy()
    wells, wcode = np.unique(items["hole"].to_numpy(), return_inverse=True)
    counts = rng.multinomial(len(wells), np.full(len(wells), 1.0 / len(wells)), size=N_BOOT).astype(np.int32)
    err = np.column_stack([pred[m].to_numpy() - actual for m in ALL])
    ae = np.abs(err)
    d1 = items["d1"].to_numpy()
    band = P.band_of(d1)
    far = d1 > FAR_M
    cells = [("all items", np.ones(len(items), bool)), ("far (>1 km)", far)] + [(BANDS[i][2], band == i) for i in range(len(BANDS))]
    rows, boots = [], {}
    for name, mk in cells:
        if mk.sum() == 0:
            continue
        med, _, cim, _, bm = P.boot_stats(ae[mk], wcode[mk], counts)
        boots[name] = bm
        for k_, m in enumerate(ALL):
            rows.append(dict(cell=name, method=NAMES[m], key=m, n_items=int(mk.sum()), n_wells=int(len(np.unique(wcode[mk]))),
                             median_abs_error_m=med[k_], median_ci_lo_m=cim[0, k_], median_ci_hi_m=cim[1, k_],
                             mean_abs_error_m=float(ae[mk][:, k_].mean()), median_signed_error_m=float(np.median(err[mk][:, k_]))))
    by_band = pd.DataFrame(rows)
    rows = []
    t = items["top"].to_numpy()
    for j, top in enumerate(tops):
        for name, mk in [("all items", t == j), ("far (>1 km)", (t == j) & far)]:
            if mk.sum() == 0:
                continue
            for k_, m in enumerate(ALL):
                rows.append(dict(layer=top, cell=name, method=NAMES[m], key=m, n_items=int(mk.sum()),
                                 n_wells=int(len(np.unique(wcode[mk]))), median_abs_error_m=float(np.median(ae[mk][:, k_])),
                                 mean_abs_error_m=float(ae[mk][:, k_].mean())))
    by_layer = pd.DataFrame(rows)
    # ---- the learned model against every other method, on the same items ----
    rows = []
    for who in ("C", "D", "C_shuffled", "C_strict", "C_pre"):
        kw = ALL.index(who)
        for name, mk in cells:
            if name not in boots:
                continue
            bm = boots[name]
            med = np.median(ae[mk], axis=0)
            for k_, m in enumerate(ALL):
                if m == who or (who != "C" and m not in SIMPLE + ["C"]):
                    continue
                with np.errstate(all="ignore"):
                    imp = 1.0 - med[kw] / med[k_]
                    bi = 1.0 - bm[:, kw] / bm[:, k_]
                rows.append(dict(model=NAMES[who], model_key=who, against=NAMES[m], against_key=m, cell=name,
                                 n_items=int(mk.sum()), n_wells=int(len(np.unique(wcode[mk]))),
                                 median_abs_error_model_m=med[kw], median_abs_error_other_m=med[k_],
                                 improvement_pct=100 * imp, ci_lo_pct=100 * float(np.nanpercentile(bi, 2.5)),
                                 ci_hi_pct=100 * float(np.nanpercentile(bi, 97.5))))
    versus = pd.DataFrame(rows)
    # ---- 80 % ranges ----------------------------------------------------------
    in_c = (actual >= pred["C_lo"].to_numpy()) & (actual <= pred["C_hi"].to_numpy())
    in_k = np.abs(items["m3"].to_numpy() - actual) <= items["hw3"].to_numpy()
    rows = []
    for name, mk in cells:
        if mk.sum() == 0:
            continue
        rows.append(dict(cell=name, n_items=int(mk.sum()), n_wells=int(len(np.unique(wcode[mk]))),
                         learned_model_share_inside=float(in_c[mk].mean()), kriging_share_inside=float(in_k[mk].mean()),
                         learned_model_median_width_m=float(np.median((pred["C_hi"] - pred["C_lo"]).to_numpy()[mk])),
                         kriging_median_width_m=float(np.median(2 * items["hw3"].to_numpy()[mk]))))
    cover = pd.DataFrame(rows)
    by_band.to_csv(outdir / f"{country}_scores_by_distance{tag}.csv", index=False)
    by_layer.to_csv(outdir / f"{country}_scores_by_layer{tag}.csv", index=False)
    versus.to_csv(outdir / f"{country}_learned_vs_others{tag}.csv", index=False)
    cover.to_csv(outdir / f"{country}_range_coverage{tag}.csv", index=False)
    return by_band, by_layer, versus, cover


def chart(by_band, country, path, half):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans"})
    # dark surface; three hues in fixed order (blue, orange, aqua) that stay apart for
    # colour-blind readers on this surface; marker and dash repeat the identity
    bg, fg, fg2, grid = "#1a1a19", "#f0efec", "#c3c2b7", "#2c2c2a"
    style = {"m3": ("#3987e5", "o", "-"), "B": ("#d95926", "s", (0, (6, 2))), "C": ("#199e70", "^", "-")}
    names = [b[2] for b in BANDS]
    xs = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(9.5, 5.6), dpi=160)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    for key, (col, mk, ls) in style.items():
        d = by_band[by_band["key"] == key].set_index("cell").reindex(names)
        ax.fill_between(xs, d["median_ci_lo_m"].to_numpy(float), d["median_ci_hi_m"].to_numpy(float), color=col, alpha=0.14, lw=0, zorder=2)
        ax.plot(xs, d["median_abs_error_m"].to_numpy(float), color=col, marker=mk, ls=ls, lw=2, ms=7, markeredgecolor=bg,
                markeredgewidth=1.2, label=NAMES[key][2:].strip().capitalize(), zorder=3)
    d = by_band[by_band["key"] == "m3"].set_index("cell").reindex(names)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{n}\n{int(d.loc[n, 'n_items']) if pd.notna(d.loc[n, 'n_items']) else 0:,} items\n"
                        f"{int(d.loc[n, 'n_wells']) if pd.notna(d.loc[n, 'n_wells']) else 0:,} wells" for n in names], color=fg2, fontsize=9)
    ax.set_yscale("log")
    ax.set_ylabel("Median absolute error, metres (log scale)", color=fg2)
    ax.set_xlabel("Distance to the nearest known well that has the layer", color=fg2)
    ax.set_title(f"{country}: kriging, drift-corrected kriging and the learned model ({half})\n"
                 f"shaded: 95 % interval from resampling wells", color=fg, fontsize=11, loc="left")
    ax.tick_params(colors=fg2, which="both")
    for s in ax.spines.values():
        s.set_color(grid)
    ax.grid(True, which="major", color=grid, lw=0.8)
    ax.grid(True, which="minor", color=grid, lw=0.3)
    ax.set_axisbelow(True)
    from matplotlib.ticker import ScalarFormatter
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.legend(facecolor=bg, edgecolor=grid, labelcolor=fg, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, facecolor=bg)
    plt.close(fig)


def run(country, final):
    outdir = ROOT / "results" if final else ROOT / "cache" / "rehearsal"
    outdir.mkdir(parents=True, exist_ok=True)
    half = "scoring" if final else "tuning"
    n_frozen = verify_frozen(country)
    sp, cut2 = TR.split_lists(country)
    if final:
        holes, picks, info = SL.load(country, "score")
    else:
        holes, picks, info = SL.load(country, "train", block_date=cut2)
    ctx, cfg, S = SL.context(country, holes, picks)
    ids = list(sp.loc[sp["half"] == half, "hole_id"])
    wells = np.array([ctx.hid[i] for i in ids if i in ctx.hid], dtype=np.int64)
    aud = FE.Audit()
    items, X = FE.build(ctx, cfg, S, wells, audit=aud)
    date_test = CH.check(country, ctx, aud)
    own_test = own_pick_perturbation(country, ctx, cfg, S, wells, items, X, 60)
    pred, S2 = predict_all(country, items, X)
    by_band, by_layer, versus, cover = score_tables(country, items, pred, ctx.tops, outdir)
    chart(by_band, cfg["name"], outdir / f"{country}_learned_vs_kriging.png", f"{half} half")
    # items with every forecast
    it = items[["hole_id", "top_name", "d1", "actual"]].rename(columns={"top_name": "layer", "d1": "dist_nearest_known_m", "actual": "actual_elev_m"})
    for m in ALL:
        it[f"{m}_elev_m"] = pred[m].to_numpy()
    it["C_range_lo_m"], it["C_range_hi_m"] = pred["C_lo"].to_numpy(), pred["C_hi"].to_numpy()
    it["kriging_half_width_80pct_m"] = items["hw3"].to_numpy()
    it.round(3).to_csv(outdir / f"{country}_{half}_items.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    # ---- pass mark -----------------------------------------------------------
    far = by_band[by_band["cell"] == "far (>1 km)"].set_index("key")
    best = far.loc[SIMPLE, "median_abs_error_m"].astype(float).idxmin()
    v = versus[(versus["cell"] == "far (>1 km)")].set_index(["model_key", "against_key"])
    c_best = v.loc[("C", best)]
    d_best = v.loc[("D", best)]
    passed = bool(c_best["improvement_pct"] >= 10.0 and c_best["ci_lo_pct"] > 0.0)
    gain_c = float(far.loc[best, "median_abs_error_m"] - far.loc["C", "median_abs_error_m"])
    gain_d = float(far.loc[best, "median_abs_error_m"] - far.loc["D", "median_abs_error_m"])
    summary = dict(
        country=cfg["name"], half=half, frozen_files_verified=n_frozen, load=info,
        wells_in_half=len(ids), wells_scored=int(items["hole"].nunique()), wells_without_item_here=int(len(ids) - items["hole"].nunique()),
        items=int(len(items)), far_items=int(far.loc["C", "n_items"]), far_wells=int(far.loc["C", "n_wells"]),
        far_median_abs_error_m={m: float(far.loc[m, "median_abs_error_m"]) for m in ALL},
        far_mean_abs_error_m={m: float(far.loc[m, "mean_abs_error_m"]) for m in ALL},
        all_median_abs_error_m={m: float(by_band[by_band["cell"] == "all items"].set_index("key").loc[m, "median_abs_error_m"]) for m in ALL},
        best_simple_method=best, best_simple_method_name=NAMES[best],
        C_improvement_over_best_simple_pct=float(c_best["improvement_pct"]),
        C_improvement_ci_pct=[float(c_best["ci_lo_pct"]), float(c_best["ci_hi_pct"])],
        D_improvement_over_best_simple_pct=float(d_best["improvement_pct"]),
        D_improvement_ci_pct=[float(d_best["ci_lo_pct"]), float(d_best["ci_hi_pct"])],
        C_gain_m=gain_c, D_gain_m=gain_d,
        share_of_C_gain_reached_by_D=(float(gain_d / gain_c) if gain_c > 0 else None),
        passed=passed,
        shuffle_test=dict(
            improvement_over_best_simple_pct=float(v.loc[("C_shuffled", best), "improvement_pct"]),
            ci_pct=[float(v.loc[("C_shuffled", best), "ci_lo_pct"]), float(v.loc[("C_shuffled", best), "ci_hi_pct"])],
            improvement_over_kriging_pct=float(v.loc[("C_shuffled", "m3"), "improvement_pct"]),
            ci_over_kriging_pct=[float(v.loc[("C_shuffled", "m3"), "ci_lo_pct"]), float(v.loc[("C_shuffled", "m3"), "ci_hi_pct"])],
            gain_vanished=bool(v.loc[("C_shuffled", best), "ci_lo_pct"] <= 0.0)),
        date_rule_test=date_test, own_pick_test=own_test,
        range_coverage={r["cell"]: dict(learned=r["learned_model_share_inside"], kriging=r["kriging_share_inside"])
                        for _, r in cover.iterrows()})
    (outdir / f"{country}_summary.json").write_text(json.dumps(summary, indent=1, default=float))
    print(json.dumps(summary, indent=1, default=float), flush=True)
    assert date_test["passed"], "date-rule test failed"
    assert own_test["passed"], "own-pick test failed"
    return summary


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    final = "--final" in argv
    for c in (args or ["kansas", "netherlands"]):
        run(c, final)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
