"""Stage 1: everything that happens before the scoring half is looked at.

    .venv/bin/python -I src/train.py [kansas] [netherlands]

No depth of a sealed well or of a scoring-half well is loaded here (see
safe_load.py). Per country:

  1. training targets: wells from before the test years, each forecast at
     its own date from the wells known then; and the tuning half
  2. every choice is made by fitting on the targets from before the test
     years and looking at the tuning half
  3. the final models are fitted on both together, with those choices
  4. models, settings and the drift table are written, with their sha256
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import checks as CH          # noqa: E402
import features as FE        # noqa: E402
import safe_load as SL       # noqa: E402
from safe_load import pipeline as P  # noqa: E402

ROOT = SL.ROOT
OUT = ROOT / "results"
MODELS = ROOT / "models"
CACHE = ROOT / "cache"
SEED = 20261113
THREADS = 4                   # fixed: LightGBM results depend on the thread count
FAR_M = 1000.0
BANDS = P.BANDS

TRAIN_FROM = {"kansas": pd.Timestamp("1970-01-01"), "netherlands": pd.Timestamp("1950-01-01")}
CHUNK = 15000
LR = {"kansas": 0.1, "netherlands": 0.05}
BASE = dict(feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0,
            max_bin=255, seed=SEED, deterministic=True, force_row_wise=True, num_threads=THREADS, verbose=-1)
MAX_ROUNDS = {"kansas": 800, "netherlands": 600}
STEP = 25
LEAF_GRID = {"kansas": [(15, 200), (63, 200), (63, 50), (127, 100)],
             "netherlands": [(7, 40), (15, 40), (15, 15), (31, 20)]}
MIN_CELL = 30                 # items needed in a layer-and-band cell of the drift table


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def band_of(d):
    return P.band_of(np.asarray(d, float))


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def split_lists(country):
    sp = pd.read_csv(OUT / f"{country}_dev_split.csv", parse_dates=["test_date"])
    cut2 = sp.loc[sp["half"] == "scoring", "test_date"].min()
    assert sp.loc[sp["half"] == "tuning", "test_date"].max() < cut2
    return sp, cut2


def build_sets(country):
    """Features for the training targets from before the test years and for
    the tuning half. Runs the date-rule and own-pick tests on every chunk."""
    sp, cut2 = split_lists(country)
    holes, picks, info = SL.load(country, "train", block_date=cut2)
    ctx, cfg, S = SL.context(country, holes, picks)
    h = ctx.holes
    start_day = P.to_day(pd.Series([cfg["test_start"]]))[0]
    pre = h["pre_test"].to_numpy(bool) & (h["test_date"] >= TRAIN_FROM[country]).to_numpy() & h["rule_date"].notna().to_numpy()
    if "system" in h.columns:                      # Netherlands: mother boreholes only, like the test wells
        pre &= (h["hole_id"] == h["system"]).to_numpy() & (h["BOREHOLE_OR_SIDETRACK_CODE"] != "STR").to_numpy()
    pre_idx = np.nonzero(pre)[0]
    tun_ids = [i for i in sp.loc[sp["half"] == "tuning", "hole_id"] if i in ctx.hid]
    tun_idx = np.array([ctx.hid[i] for i in tun_ids], dtype=np.int64)
    chk = dict(known_well_uses=0, rows=0, date_violations=0, date_mismatch=0, loose_cutoff=0, own_pick=0, own_system=0)
    parts = []
    for name, idx in [("before test years", pre_idx), ("tuning half", tun_idx)]:
        for s in range(0, len(idx), CHUNK):
            aud = FE.Audit()
            it, X = FE.build(ctx, cfg, S, idx[s:s + CHUNK], audit=aud)
            r = CH.check(country, ctx, aud)
            for k_ in chk:
                chk[k_] += r[k_]
            it["set"] = name
            if name == "before test years":
                # the actual value must itself date from before the test years
                ok = (ctx.avail[it["hole"].to_numpy(), it["top"].to_numpy()] < start_day)
                it, X = it[ok].reset_index(drop=True), X[ok].reset_index(drop=True)
            parts.append((it, X))
            print(f"[{country}] features {name}: wells {min(s + CHUNK, len(idx))}/{len(idx)}", flush=True)
    items = pd.concat([p[0] for p in parts], ignore_index=True)
    X = pd.concat([p[1] for p in parts], ignore_index=True)
    chk["passed"] = all(chk[k_] == 0 for k_ in ["date_violations", "date_mismatch", "loose_cutoff", "own_pick", "own_system"])
    assert chk["passed"], chk
    # latest finish day a well may have to count as known for EVERY well of the scoring half
    # (start dates of the scoring-half wells come from the date columns only)
    _, spud_by_hole, wait = CH.independent_dates(country)
    sc_start = pd.to_datetime(sp.loc[sp["half"] == "scoring", "hole_id"].map(spud_by_hole))
    assert sc_start.notna().all()
    strict_day = int(P.cutoff_days(sc_start.to_numpy(), cfg["wait"]).min())
    info.update(cut2=str(cut2.date()), train_from=str(TRAIN_FROM[country].date()), checks_training_and_tuning=chk,
                strict_known_day=strict_day, strict_known_date=str(np.datetime64("1970-01-01") + np.timedelta64(strict_day, "D")))
    return items, X, info, ctx.tops


# --------------------------------------------------------------------------
# drift table (method B)
# --------------------------------------------------------------------------
def drift_table(items, n_tops):
    """Median of (actual - kriging) per layer and distance band, with
    fall-back to the layer and then to all items where a cell is thin."""
    y = (items["actual"] - items["m3"]).to_numpy()
    b = band_of(items["d1"])
    t = items["top"].to_numpy()
    glob = float(np.median(y)) if len(y) else 0.0
    rows = []
    for j in range(n_tops):
        mj = t == j
        lay = float(np.median(y[mj])) if mj.sum() >= MIN_CELL else glob
        for i in range(len(BANDS)):
            m = mj & (b == i)
            n = int(m.sum())
            rows.append(dict(top=j, band=i, n=n, shift_m=float(np.median(y[m])) if n >= MIN_CELL else lay,
                             source="cell" if n >= MIN_CELL else ("layer" if mj.sum() >= MIN_CELL else "all")))
    return pd.DataFrame(rows)


def apply_drift(table, items):
    key = table.set_index(["top", "band"])["shift_m"]
    idx = pd.MultiIndex.from_arrays([items["top"].to_numpy(), band_of(items["d1"])])
    return items["m3"].to_numpy() + key.reindex(idx).to_numpy()


# --------------------------------------------------------------------------
# gradient-boosted trees
# --------------------------------------------------------------------------
def target_and_scale(items, scaled):
    y = (items["actual"] - items["m3"]).to_numpy()
    s = np.maximum(items["sd3"].to_numpy(), 1e-3) if scaled else np.ones(len(items))
    return y / s, s


def dataset(X, cols, y, w=None):
    return lgb.Dataset(X[cols], label=y, weight=w, categorical_feature=["layer"], free_raw_data=False)


def far_weight(items, fw):
    return np.where(items["d1"].to_numpy() > FAR_M, fw, 1.0)


def fit(params, X, cols, y, w, rounds):
    return lgb.train(params, dataset(X, cols, y, w), num_boost_round=rounds)


def curve(booster, Xv, cols, items_v, scale_v, rounds):
    """Median absolute error of kriging + model on the validation items,
    all and far, every STEP rounds."""
    yv = (items_v["actual"] - items_v["m3"]).to_numpy()
    far = items_v["d1"].to_numpy() > FAR_M
    out = []
    for r in range(STEP, rounds + 1, STEP):
        p = booster.predict(Xv[cols], num_iteration=r) * scale_v
        e = np.abs(yv - p)
        out.append((r, float(np.median(e)), float(np.median(e[far])), float(np.mean(e)), float(np.mean(e[far]))))
    return pd.DataFrame(out, columns=["rounds", "mae_all", "mae_far", "mean_all", "mean_far"])


def search(country, items, X, cols, label, log, allow_scaled=True):
    """Choices for one model (C or D), made by fitting on the targets from
    before the test years and scoring the tuning half. The yardstick is the
    median absolute error on the far items of the tuning half."""
    tr = (items["set"] == "before test years").to_numpy()
    va = ~tr
    Xt, Xv, it, iv = X[tr], X[va], items[tr], items[va]
    best = None
    leaves0, minleaf0 = LEAF_GRID[country][1]
    tried = []
    plan = [(sc, fw, leaves0, minleaf0) for sc in ((False, True) if allow_scaled else (False,)) for fw in (1.0, 3.0)]
    for stage in (1, 2):
        for scaled, fw, leaves, minleaf in plan:
            if (scaled, fw, leaves, minleaf) in tried:
                continue
            tried.append((scaled, fw, leaves, minleaf))
            y, s = target_and_scale(it, scaled)
            _, sv = target_and_scale(iv, scaled)
            params = dict(BASE, learning_rate=LR[country], objective="regression_l1", num_leaves=leaves, min_data_in_leaf=minleaf)
            t0 = time.time()
            b = fit(params, Xt, cols, y, far_weight(it, fw), MAX_ROUNDS[country])
            cv = curve(b, Xv, cols, iv, sv, MAX_ROUNDS[country])
            k = cv["mae_far"].idxmin()
            rec = dict(country=country, model=label, target_scaled_by_kriging_sd=scaled, far_weight=fw, num_leaves=leaves,
                       min_data_in_leaf=minleaf, best_rounds=int(cv.loc[k, "rounds"]), tuning_mae_far=cv.loc[k, "mae_far"],
                       tuning_mae_all=cv.loc[k, "mae_all"], tuning_mean_far=cv.loc[k, "mean_far"], seconds=round(time.time() - t0, 1))
            log.append(rec)
            print(f"[{country}] {label} {rec}", flush=True)
            if best is None or rec["tuning_mae_far"] < best["tuning_mae_far"]:
                best = rec
        plan = [(best["target_scaled_by_kriging_sd"], best["far_weight"], lv, ml) for lv, ml in LEAF_GRID[country]]
    return best


def main(argv):
    OUT.mkdir(exist_ok=True)
    MODELS.mkdir(exist_ok=True)
    CACHE.mkdir(exist_ok=True)
    countries = argv[1:] or ["kansas", "netherlands"]
    hashes = {}
    if (OUT / "model_hashes.json").exists():
        hashes = json.loads((OUT / "model_hashes.json").read_text())
    feat_rows = None
    for c in countries:
        t0 = time.time()
        items, X, info, tops = build_sets(c)
        items.to_pickle(CACHE / f"{c}_train_items.pkl")
        X.to_pickle(CACHE / f"{c}_train_X.pkl")
        groups = FE.feature_groups(X.columns)
        cols_c = list(X.columns)
        cols_d = [f for f in X.columns if groups[f] in FE.DRIFT_GROUPS]
        feat_rows = pd.DataFrame({"feature": cols_c, "group": [groups[f] for f in cols_c],
                                  "in_model_C": True, "in_drift_only_model_D": [f in cols_d for f in cols_c]})
        tr = (items["set"] == "before test years").to_numpy()
        va = ~tr
        far_v = (items["d1"] > FAR_M).to_numpy() & va
        S2 = dict(country=c, seed=SEED, threads=THREADS, load=info,
                  n_training_items_before_test_years=int(tr.sum()), n_training_wells_before_test_years=int(items.loc[tr, "hole"].nunique()),
                  n_tuning_items=int(va.sum()), n_tuning_wells=int(items.loc[va, "hole"].nunique()),
                  n_tuning_far_items=int(far_v.sum()))
        log = []
        # ---- B: window of the drift table ---------------------------------
        yv = (items.loc[va, "actual"] - items.loc[va, "m3"]).to_numpy()
        farv = (items.loc[va, "d1"] > FAR_M).to_numpy()
        first_tun = items.loc[va, "test_day"].min()
        bres = {}
        for win in (None, 20, 10, 5):
            m = tr if win is None else tr & (items["test_day"].to_numpy() >= first_tun - int(win * 365.25))
            tab = drift_table(items[m], len(tops))
            e = np.abs(items.loc[va, "actual"].to_numpy() - apply_drift(tab, items[va]))
            bres[win] = float(np.median(e[farv]))
            log.append(dict(country=c, model="B drift-corrected kriging", window_years=win or "all", tuning_mae_far=bres[win],
                            tuning_mae_all=float(np.median(e)), n_targets=int(m.sum())))
        win = min(bres, key=lambda w_: (bres[w_], 0 if w_ is None else w_))
        S2["drift_window_years"] = win
        last = items["test_day"].max()
        mfin = np.ones(len(items), bool) if win is None else (items["test_day"].to_numpy() >= last - int(win * 365.25))
        tab = drift_table(items[mfin], len(tops))
        tab["top_name"] = [tops[j] for j in tab["top"]]
        tab["band_name"] = [BANDS[i][2] for i in tab["band"]]
        tab.to_csv(OUT / f"{c}_drift_table.csv", index=False)
        S2["drift_table_targets"] = int(mfin.sum())
        e0 = np.abs(yv)
        S2["tuning_half_kriging"] = dict(mae_far=float(np.median(e0[farv])), mae_all=float(np.median(e0)))
        # ---- C and D: search, then final fit ------------------------------
        final = {}
        for label, cols in (("C", cols_c), ("D", cols_d)):
            # D may not see depth values, so its target is not scaled by the kriging spread either
            best = search(c, items, X, cols, label, log, allow_scaled=(label == "C"))
            final[label] = best
        S2["model_C"], S2["model_D"] = final["C"], final["D"]
        pd.DataFrame(log).to_csv(OUT / f"{c}_tuning_search.csv", index=False)

        def params_of(best, objective="regression_l1", **kw):
            return dict(BASE, learning_rate=LR[c], objective=objective, num_leaves=best["num_leaves"],
                        min_data_in_leaf=best["min_data_in_leaf"], **kw)

        bc = final["C"]
        y_all, s_all = target_and_scale(items, bc["target_scaled_by_kriging_sd"])
        w_all = far_weight(items, bc["far_weight"])
        # 80 % range of C: quantile models on the targets from before the test years,
        # widened or narrowed by one number so that the tuning half is covered 80 % of the time
        q = {}
        for a in (0.1, 0.9):
            q[a] = fit(params_of(bc, "quantile", alpha=a), X[tr], cols_c, y_all[tr], w_all[tr], bc["best_rounds"])
        lo = q[0.1].predict(X.loc[va, cols_c]) * s_all[va]
        hi = q[0.9].predict(X.loc[va, cols_c]) * s_all[va]
        miss = np.maximum(lo - yv, yv - hi) / s_all[va]
        off = float(np.quantile(miss, 0.80))
        S2["range_offset_in_target_units"] = off
        S2["range_cover_tuning_before_offset"] = float(np.mean((yv >= lo) & (yv <= hi)))
        # preview on the tuning half with models that never saw it
        prev = {}
        for label, cols in (("C", cols_c), ("D", cols_d)):
            b_ = final[label]
            yy, ss = target_and_scale(items, b_["target_scaled_by_kriging_sd"])
            m_ = fit(params_of(b_), X[tr], cols, yy[tr], far_weight(items[tr], b_["far_weight"]), b_["best_rounds"])
            p_ = m_.predict(X.loc[va, cols]) * ss[va]
            e_ = np.abs(yv - p_)
            prev[label] = dict(mae_far=float(np.median(e_[farv])), mae_all=float(np.median(e_)),
                               mean_far=float(np.mean(e_[farv])), mean_all=float(np.mean(e_)))
            if label == "C":
                m_.save_model(str(MODELS / f"{c}_C_fit_before_test_years_only.txt"))
        S2["tuning_half_preview_models_fit_before_test_years"] = prev
        # final models: targets from before the test years plus the tuning half
        models = {}
        models["C"] = fit(params_of(bc), X, cols_c, y_all, w_all, bc["best_rounds"])
        bd = final["D"]
        y_d, s_d = target_and_scale(items, bd["target_scaled_by_kriging_sd"])
        models["D"] = fit(params_of(bd), X, cols_d, y_d, far_weight(items, bd["far_weight"]), bd["best_rounds"])
        models["C_q10"] = fit(params_of(bc, "quantile", alpha=0.1), X, cols_c, y_all, w_all, bc["best_rounds"])
        models["C_q90"] = fit(params_of(bc, "quantile", alpha=0.9), X, cols_c, y_all, w_all, bc["best_rounds"])
        rng = np.random.default_rng(SEED + 7)
        models["C_shuffled"] = fit(params_of(bc), X, cols_c, y_all[rng.permutation(len(y_all))], w_all, bc["best_rounds"])
        # side model: only targets whose actual value was already known, under the date rule,
        # when the first well of the scoring half was started
        strict = items["actual_day"].to_numpy() <= info["strict_known_day"]
        models["C_strict"] = fit(params_of(bc), X[strict], cols_c, y_all[strict], w_all[strict], bc["best_rounds"])
        S2["strict_side_model_training_items"] = int(strict.sum())
        for name, m_ in models.items():
            p_ = MODELS / f"{c}_{name}.txt"
            m_.save_model(str(p_))
            hashes[f"models/{p_.name}"] = sha256(p_)
        hashes[f"models/{c}_C_fit_before_test_years_only.txt"] = sha256(MODELS / f"{c}_C_fit_before_test_years_only.txt")
        hashes[f"results/{c}_drift_table.csv"] = sha256(OUT / f"{c}_drift_table.csv")
        S2["features_C"], S2["features_D"] = len(cols_c), len(cols_d)
        S2["seconds"] = round(time.time() - t0, 1)
        (OUT / f"{c}_settings_learned.json").write_text(json.dumps(S2, indent=1, default=str))
        hashes[f"results/{c}_settings_learned.json"] = sha256(OUT / f"{c}_settings_learned.json")
        print(json.dumps({k_: v for k_, v in S2.items() if k_ not in ("load",)}, indent=1, default=str), flush=True)
    if feat_rows is not None:
        feat_rows.to_csv(OUT / "features.csv", index=False)
        hashes["results/features.csv"] = sha256(OUT / "features.csv")
    (OUT / "model_hashes.json").write_text(json.dumps(dict(sorted(hashes.items())), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
