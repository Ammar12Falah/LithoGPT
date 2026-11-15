"""Shared constants and the scoring functions of the reading pilot."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261115
LAB = "FORCE_2020_LITHOFACIES_LITHOLOGY"
CONF = "FORCE_2020_LITHOFACIES_CONFIDENCE"

# the 12 rock classes of the training file, in the order of the starter notebook
LITH_KEYS = {
    30000: "Sandstone", 65030: "Sandstone/Shale", 65000: "Shale", 80000: "Marl",
    74000: "Dolomite", 70000: "Limestone", 70032: "Chalk", 88000: "Halite",
    86000: "Anhydrite", 99000: "Tuff", 90000: "Coal", 93000: "Basement",
}
CLASSES = list(LITH_KEYS.values())
CODE_TO_IDX = {code: i for i, code in enumerate(LITH_KEYS)}
NAME_TO_IDX = {name: i for i, name in enumerate(CLASSES)}
SHALE = NAME_TO_IDX["Shale"]

# families of near classes for the soft score
FAMILY = {name: name for name in CLASSES}
for _n in ("Sandstone", "Sandstone/Shale", "Shale"):
    FAMILY[_n] = "clastic"
for _n in ("Limestone", "Chalk", "Marl"):
    FAMILY[_n] = "carbonate"
FAM_NAMES = sorted(set(FAMILY.values()))
FAM_OF_IDX = np.array([FAM_NAMES.index(FAMILY[c]) for c in CLASSES])

TOL_M = 3.0          # tolerance of the tolerant and soft agreement, in metres
STEP_M = 0.152       # nominal depth step of train.csv, used to turn item counts into metres
CURVES = ["CALI", "RSHA", "RMED", "RDEP", "RHOB", "GR", "SGR", "NPHI", "PEF", "DTC", "SP", "BS",
          "ROP", "DTS", "DCAL", "DRHO", "MUDWEIGHT", "RMIC", "ROPA", "RXO"]


def well_code(well: str) -> str:
    return well.replace("/", "_").replace(" ", "_")


def window_hits(depth: np.ndarray, pred: np.ndarray, target: np.ndarray, n_cat: int, tol: float = TOL_M):
    """For every item: does the reader give the item's target category at any depth step
    of the same well within +-tol metres?  depth must be sorted ascending.
    pred and target are integer category indices; pred < 0 means "no class given"."""
    n = len(depth)
    lo = np.searchsorted(depth, depth - tol - 1e-9, side="left")
    hi = np.searchsorted(depth, depth + tol + 1e-9, side="right")
    hit = np.zeros(n, dtype=bool)
    for c in range(n_cat):
        m = target == c
        if not m.any():
            continue
        cs = np.concatenate([[0], np.cumsum(pred == c)])
        hit[m] = (cs[hi[m]] - cs[lo[m]]) > 0
    return hit


def item_scores(depth, pred, truth):
    """Per-item results for one well. pred: class index or -1 (unread). truth: class index.
    Returns a DataFrame with read, strict, tolerant, soft (booleans)."""
    order = np.argsort(depth, kind="stable")
    inv = np.empty_like(order)
    inv[order] = np.arange(len(order))
    d, p, t = np.asarray(depth)[order], np.asarray(pred)[order], np.asarray(truth)[order]
    read = p >= 0
    strict = read & (p == t)
    tolerant = window_hits(d, p, t, len(CLASSES))
    pf = np.where(p >= 0, FAM_OF_IDX[np.clip(p, 0, None)], -1)
    tf = FAM_OF_IDX[t]
    soft = window_hits(d, pf, tf, len(FAM_NAMES))
    out = pd.DataFrame({"read": read, "strict": strict, "tolerant": tolerant, "soft": soft})
    return out.iloc[inv].reset_index(drop=True)


def summarise(items: pd.DataFrame, truth: np.ndarray, min_class_m: float = 20.0) -> dict:
    """Pooled numbers for a set of items (already scored). Each number twice:
    with unread items counted as wrong ("_all") and on read items only ("_read")."""
    n = len(items)
    r = items["read"].to_numpy()
    out = {"n_items": n, "metres": n * STEP_M, "coverage": r.mean() if n else np.nan,
           "read_metres": r.sum() * STEP_M}
    for k in ("strict", "tolerant", "soft"):
        v = items[k].to_numpy()
        out[f"{k}_all"] = v.mean() if n else np.nan
        out[f"{k}_read"] = v[r].mean() if r.any() else np.nan
        out[f"{k}_metres"] = v.sum() * STEP_M
    # balanced: tolerant agreement per class with at least min_class_m of expert label, then averaged
    per_all, per_read = [], []
    tol = items["tolerant"].to_numpy()
    for c in range(len(CLASSES)):
        m = truth == c
        if m.sum() * STEP_M >= min_class_m:
            per_all.append(tol[m].mean())
            if (m & r).any():
                per_read.append(tol[m & r].mean())
    out["balanced_all"] = float(np.mean(per_all)) if per_all else np.nan
    out["balanced_read"] = float(np.mean(per_read)) if per_read else np.nan
    out["n_classes_balanced"] = len(per_all)
    return out
