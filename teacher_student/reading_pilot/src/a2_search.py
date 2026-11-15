"""A2 setup search, inside the extra wells only (well-by-well check, 3 folds).
Compares a few fixed candidates of features and tree settings. Writes curve/setup_check_extra_wells.csv.
Usage: python -I src/a2_search.py <stage>
"""
import sys, time, json
from pathlib import Path
import numpy as np, pandas as pd, lightgbm as lgb
sys.path.insert(0, str(Path(__file__).resolve().parent))
import a2_model as m
from common import ROOT, SEED

CAND = {
 "A_leaves63": dict(num_leaves=63, min_data_in_leaf=40, feature_fraction=0.5, learning_rate=0.1, lambda_l2=1.0),
 "B_leaves31_reg": dict(num_leaves=31, min_data_in_leaf=300, feature_fraction=0.4, learning_rate=0.05, lambda_l2=5.0,
                        cat_l2=50.0, cat_smooth=50.0, min_data_per_group=300),
 "C_leaves15_reg": dict(num_leaves=15, min_data_in_leaf=600, feature_fraction=0.3, learning_rate=0.05, lambda_l2=10.0,
                        cat_l2=100.0, cat_smooth=100.0, min_data_per_group=500),
 "D_leaves31_extra": dict(num_leaves=31, min_data_in_leaf=300, feature_fraction=0.4, learning_rate=0.05, lambda_l2=5.0,
                          cat_l2=50.0, cat_smooth=50.0, min_data_per_group=300, extra_trees=True, path_smooth=20.0),
}
EVAL_AT = [100, 200, 400, 600]

def main():
    stage = sys.argv[1]
    feats = {"1": ["S0", "S1"], "2": ["S1", "S2"]}[stage]
    cands = sys.argv[2].split(",") if len(sys.argv) > 2 else list(CAND)
    R = m.roles(); logs = m.load_logs(); lab = m.labels_pool(logs)
    extra = R["extra"]
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(extra))
    folds = [[extra[i] for i in perm[k::3]] for k in range(3)]
    y = lab["y"].to_numpy()
    rows = []
    outp = ROOT / "curve" / f"setup_check_extra_wells_stage{stage}.csv"
    for which in feats:
        X = m.build_features(logs, which)
        for name in cands:
            P = dict(m.PARAMS); P.update(CAND[name])
            for k, val_wells in enumerate(folds):
                tr_w = [w for w in extra if w not in val_wells]
                tr = np.flatnonzero(logs["WELL"].isin(tr_w).to_numpy())[::4]
                va = np.flatnonzero(logs["WELL"].isin(val_wells).to_numpy())[::3]
                t0 = time.time()
                ds = lgb.Dataset(X.iloc[tr], label=y[tr].astype(int), categorical_feature=["GROUP", "FORMATION"])
                b = lgb.train(P, ds, num_boost_round=max(EVAL_AT))
                for r in EVAL_AT:
                    acc = float((b.predict(X.iloc[va], num_iteration=r).argmax(1) == y[va]).mean())
                    rows.append({"features": which, "trees": name, "fold": k, "rounds": r, "strict": acc})
                print(which, name, "fold", k, [round(x["strict"], 4) for x in rows[-len(EVAL_AT):]], round(time.time() - t0), "s", flush=True)
                pd.DataFrame(rows).to_csv(outp, index=False)
    res = pd.DataFrame(rows)
    print(res.groupby(["features", "trees", "rounds"]).strict.mean().unstack().round(4).to_string())

if __name__ == "__main__":
    main()
