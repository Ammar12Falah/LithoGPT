"""A2: the plain log model (gradient-boosted trees) and the learning curve.

Modes
  python -I src/a2_model.py cv        well-by-well check inside the extra wells only (chooses the setup)
  python -I src/a2_model.py curve     learning curve on the 23 curve wells (n = 1, 3, 10, 30, 70)
  python -I src/a2_model.py fixed     trains the ten-well model and the all-well model, saves them
The expert labels of the test wells are never read here.
"""
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (CLASSES, CODE_TO_IDX, CONF, CURVES, LAB, ROOT, SEED, SHALE,  # noqa: E402
                    item_scores, summarise)

RES_CURVES = ["RSHA", "RMED", "RDEP", "RMIC", "RXO"]
WIN_CURVES = ["GR", "RHOB", "NPHI", "DTC", "PEF", "RDEP", "RMED", "CALI", "SP", "DRHO"]
SHIFTS = [3, 7, 13, 33]          # depth steps: about 0.5, 1, 2 and 5 m above and below
ROLL = 33                        # half window of the rolling features: about 5 m

# ---- the fixed setup (chosen with `cv` inside the extra wells, then not changed) ----
SETUP = json.loads((ROOT / "src" / "model_setup.json").read_text()) if (ROOT / "src" / "model_setup.json").exists() else {
    "features": "S1", "rounds": 300,
}
PARAMS = {
    "objective": "multiclass", "num_class": len(CLASSES), "learning_rate": 0.1,
    "num_leaves": 63, "min_data_in_leaf": 40, "feature_fraction": 0.5,
    "bagging_fraction": 0.7, "bagging_freq": 1, "lambda_l2": 1.0, "max_bin": 127,
    "num_threads": 4, "verbose": -1, "seed": SEED, "deterministic": True, "force_row_wise": True,
}
TRAIN_EVERY = 2                  # train on every 2nd depth step (neighbours are near copies)


def load_logs() -> pd.DataFrame:
    df = pd.read_parquet(ROOT / "data" / "logs_all.parquet")
    return df.sort_values(["WELL", "DEPTH_MD"], kind="stable").reset_index(drop=True)


def build_features(df: pd.DataFrame, which: str) -> pd.DataFrame:
    """which = S0 (curves, depth, position, group, formation), S1 (+ 10 curves shifted by about
    0.5, 1, 2 and 5 m up and down), S1b (+ 5 curves shifted by about 1 and 3 m up and down),
    S2 (S1 + rolling mean / spread over about 10 m and well-normalised gamma ray)."""
    X = pd.DataFrame(index=df.index)
    for c in CURVES:
        v = df[c].astype("float32")
        if c in RES_CURVES:
            v = np.log10(v.clip(lower=1e-3))
        X[c] = v
    for c in ["DEPTH_MD", "X_LOC", "Y_LOC", "Z_LOC"]:
        X[c] = df[c].astype("float32")
    for c in ["GROUP", "FORMATION"]:
        cats = sorted(df[c].dropna().unique().tolist())
        X[c] = pd.Categorical(df[c], categories=cats).codes.astype("int32")
    if which in ("S1", "S2", "S1b"):
        g = X.groupby(df["WELL"], sort=False)
        new = {}
        for c in (WIN_CURVES if which != "S1b" else ["GR", "RHOB", "NPHI", "DTC", "RDEP"]):
            for s in (SHIFTS if which != "S1b" else [7, 20]):
                new[f"{c}_up{s}"] = g[c].shift(s)
                new[f"{c}_dn{s}"] = g[c].shift(-s)
        X = pd.concat([X, pd.DataFrame(new, index=X.index).astype("float32")], axis=1)
    if which == "S2":
        g = X.groupby(df["WELL"], sort=False)
        new = {}
        for c in ["GR", "RHOB", "NPHI", "DTC", "RDEP"]:
            r = g[c].rolling(2 * ROLL + 1, center=True, min_periods=5)
            new[f"{c}_rmean"] = r.mean().reset_index(level=0, drop=True)
            new[f"{c}_rstd"] = r.std().reset_index(level=0, drop=True)
        med = g["GR"].transform("median")
        q75 = g["GR"].transform(lambda s: s.quantile(0.75))
        q25 = g["GR"].transform(lambda s: s.quantile(0.25))
        new["GR_wellnorm"] = (X["GR"] - med) / (q75 - q25 + 1e-6)
        X = pd.concat([X, pd.DataFrame(new, index=X.index).astype("float32")], axis=1)
    return X


def fit(X, y, rounds, valid=None, eval_at=None):
    ds = lgb.Dataset(X, label=y, categorical_feature=["GROUP", "FORMATION"], free_raw_data=False)
    if valid is None:
        return lgb.train(PARAMS, ds, num_boost_round=rounds), None
    booster = lgb.train(PARAMS, ds, num_boost_round=rounds)
    Xv, yv = valid
    acc = {}
    for k in eval_at:
        p = booster.predict(Xv, num_iteration=k).argmax(1)
        acc[k] = float((p == yv).mean())
    return booster, acc


def labels_pool(logs: pd.DataFrame) -> pd.DataFrame:
    lab = pd.read_parquet(ROOT / "data" / "labels_pool.parquet")
    m = logs[["row_id"]].merge(lab[["row_id", LAB, CONF]], on="row_id", how="left")
    y = m[LAB].map(CODE_TO_IDX)
    return pd.DataFrame({"y": y.to_numpy(), "conf": m[CONF].to_numpy()}, index=logs.index)


def train_rows(logs, lab, wells):
    m = logs["WELL"].isin(wells).to_numpy() & lab["y"].notna().to_numpy()
    idx = np.flatnonzero(m)
    return idx[::TRAIN_EVERY]


def score_wells(logs, lab, wells, pred_fn):
    """Scores a per-depth-step reader on a list of wells. pred_fn(index_array) -> class index."""
    per_well, items_all, truth_all = [], [], []
    for w in wells:
        idx = np.flatnonzero((logs["WELL"] == w).to_numpy() & lab["y"].notna().to_numpy())
        if len(idx) == 0:
            continue
        t = lab["y"].to_numpy()[idx].astype(int)
        p = pred_fn(idx)
        it = item_scores(logs["DEPTH_MD"].to_numpy()[idx], p, t)
        s = summarise(it, t)
        s["well"] = w
        per_well.append(s)
        items_all.append(it)
        truth_all.append(t)
    pooled = summarise(pd.concat(items_all, ignore_index=True), np.concatenate(truth_all))
    return pooled, pd.DataFrame(per_well)


def roles():
    d = pd.read_csv(ROOT / "draw.csv")
    return {r: d[d.role == r].well.tolist() for r in ["test", "example", "curve", "extra"]}


def mode_cv():
    R = roles()
    logs = load_logs()
    lab = labels_pool(logs)
    extra = R["extra"]
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(extra))
    folds = [[extra[i] for i in perm[k::3]] for k in range(3)]
    eval_at = [100, 200, 300, 400]
    out = []
    for which in ["S0", "S1", "S2"]:
        X = build_features(logs, which)
        for k, val_wells in enumerate(folds):
            tr_wells = [w for w in extra if w not in val_wells]
            tr = train_rows(logs, lab, tr_wells)
            va = np.flatnonzero(logs["WELL"].isin(val_wells).to_numpy() & lab["y"].notna().to_numpy())[::3]
            t0 = time.time()
            _, acc = fit(X.iloc[tr], lab["y"].to_numpy()[tr].astype(int), max(eval_at),
                         valid=(X.iloc[va], lab["y"].to_numpy()[va].astype(int)), eval_at=eval_at)
            for r, a in acc.items():
                out.append({"features": which, "fold": k, "rounds": r, "strict": a,
                            "n_train_rows": len(tr), "seconds": round(time.time() - t0)})
            print(which, "fold", k, acc, round(time.time() - t0), "s", flush=True)
        del X
    res = pd.DataFrame(out)
    (ROOT / "curve").mkdir(exist_ok=True)
    res.to_csv(ROOT / "curve" / "setup_check_extra_wells.csv", index=False)
    mean = res.groupby(["features", "rounds"]).strict.mean().reset_index()
    print(mean.to_string(index=False))
    best = mean.sort_values("strict", ascending=False).iloc[0]
    setup = {"features": str(best.features), "rounds": int(best.rounds)}
    (ROOT / "src" / "model_setup.json").write_text(json.dumps(setup))
    print("chosen setup:", setup)


def mode_curve():
    R = roles()
    logs = load_logs()
    lab = labels_pool(logs)
    X = build_features(logs, SETUP["features"])
    pool = R["example"] + R["extra"]
    assert len(pool) == 70 and len(R["curve"]) == 23
    rng = np.random.default_rng(SEED)
    rows, wells_rows, draws = [], [], []
    yall = lab["y"].to_numpy()

    def run(tag, n, draw, wells):
        t0 = time.time()
        tr = train_rows(logs, lab, wells)
        booster, _ = fit(X.iloc[tr], yall[tr].astype(int), SETUP["rounds"])
        pooled, per_well = score_wells(logs, lab, R["curve"], lambda idx: booster.predict(X.iloc[idx]).argmax(1))
        pooled.update({"reader": tag, "n_wells": n, "draw": draw, "n_train_rows": len(tr)})
        per_well["reader"], per_well["n_wells"], per_well["draw"] = tag, n, draw
        rows.append(pooled)
        wells_rows.append(per_well)
        draws.append({"reader": tag, "n_wells": n, "draw": draw, "wells": " | ".join(wells)})
        print(tag, n, draw, f"tolerant={pooled['tolerant_all']:.4f} strict={pooled['strict_all']:.4f}",
              round(time.time() - t0), "s", flush=True)

    for n in [1, 3, 10, 30]:
        for d in range(5):
            wells = [pool[i] for i in rng.choice(len(pool), size=n, replace=False)]
            run("plain model", n, d + 1, wells)
    run("plain model", 70, 1, pool)
    run("ten-well model (the 10 example wells)", 10, 0, R["example"])
    pooled, per_well = score_wells(logs, lab, R["curve"], lambda idx: np.full(len(idx), SHALE))
    pooled.update({"reader": "all-shale line", "n_wells": 0, "draw": 0, "n_train_rows": 0})
    per_well["reader"], per_well["n_wells"], per_well["draw"] = "all-shale line", 0, 0
    rows.append(pooled)
    wells_rows.append(per_well)
    (ROOT / "curve").mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(ROOT / "curve" / "learning_curve_runs.csv", index=False)
    pd.concat(wells_rows, ignore_index=True).to_csv(ROOT / "curve" / "learning_curve_by_well.csv", index=False)
    pd.DataFrame(draws).to_csv(ROOT / "curve" / "learning_curve_draws.csv", index=False)


def mode_fixed():
    R = roles()
    logs = load_logs()
    lab = labels_pool(logs)
    X = build_features(logs, SETUP["features"])
    yall = lab["y"].to_numpy()
    (ROOT / "models").mkdir(exist_ok=True)
    allw = R["example"] + R["extra"] + R["curve"]
    assert len(allw) == 93 and not set(allw) & set(R["test"])
    for tag, wells in [("ten_well", R["example"]), ("all_well", allw)]:
        tr = train_rows(logs, lab, wells)
        booster, _ = fit(X.iloc[tr], yall[tr].astype(int), SETUP["rounds"])
        booster.save_model(str(ROOT / "models" / f"{tag}.txt"))
        print("saved", tag, "trained on", len(wells), "wells,", len(tr), "rows", flush=True)


if __name__ == "__main__":
    {"cv": mode_cv, "curve": mode_curve, "fixed": mode_fixed}[sys.argv[1]]()
