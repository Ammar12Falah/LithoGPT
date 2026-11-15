"""Reading files -> one class per depth step.

A reading file is a CSV with at least: depth_from, depth_to, rock_class (metres, measured depth
from the rotary table, as in train.csv). Optional: second_class, confidence.
Rules (fixed in reading_rules.md):
 - a row with an empty rock_class, or a class that is not one of the 12, gives no class;
 - depth_from / depth_to must both be numbers, else the row is dropped;
 - where rows overlap, the shortest interval wins; ties go to the higher confidence, then to the later row;
 - a depth step d gets the class of the winning row with depth_from <= d < depth_to
   (a row with depth_from == depth_to, a point description, covers d within +-0.25 m).
"""
import numpy as np
import pandas as pd

from common import CLASSES, NAME_TO_IDX

CONF_RANK = {"high": 3, "medium": 2, "low": 1}
ALIASES = {c.lower(): c for c in CLASSES}
ALIASES.update({"sandstone / shale": "Sandstone/Shale", "sandstone-shale": "Sandstone/Shale",
                "shaly sandstone": "Sandstone/Shale"})
POINT_HALF_M = 0.25


def clean_class(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    s = str(v).strip().lower()
    return ALIASES.get(s)


def load_reading(path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [c.strip().lower() for c in df.columns]
    for c in ("depth_from", "depth_to"):
        df[c] = pd.to_numeric(df[c].str.replace(",", ".", regex=False).str.strip(), errors="coerce")
    df["cls"] = df["rock_class"].map(clean_class)
    df["cls2"] = df["second_class"].map(clean_class) if "second_class" in df else None
    df["conf_rank"] = df["confidence"].str.strip().str.lower().map(CONF_RANK).fillna(0) if "confidence" in df else 0
    df["row"] = np.arange(len(df))
    return df


def rasterise(df: pd.DataFrame, depths: np.ndarray, col: str = "cls"):
    """Class index for every depth (or -1), and the winning row number (or -1)."""
    out = np.full(len(depths), -1, dtype=int)
    row = np.full(len(depths), -1, dtype=int)
    ok = df[df["depth_from"].notna() & df["depth_to"].notna()].copy()
    a = ok[["depth_from", "depth_to"]].min(axis=1)
    b = ok[["depth_from", "depth_to"]].max(axis=1)
    point = (b - a) < 1e-9
    a = np.where(point, a - POINT_HALF_M, a)
    b = np.where(point, b + POINT_HALF_M, b)
    ok["a"], ok["b"], ok["len"] = a, b, b - a
    # longest first, so that shorter intervals overwrite; within equal length lower confidence first, earlier row first
    ok = ok.sort_values(["len", "conf_rank", "row"], ascending=[False, True, True])
    for _, r in ok.iterrows():
        m = (depths >= r["a"]) & (depths < r["b"])
        if not m.any():
            continue
        c = r[col]
        cmain = r["cls"]
        if cmain is None or (isinstance(cmain, float) and np.isnan(cmain)):
            # a row without a main class (e.g. "no class, curves missing") wipes what longer rows said
            out[m] = -1
            row[m] = r["row"]
            continue
        out[m] = NAME_TO_IDX[c] if isinstance(c, str) else -1
        row[m] = r["row"]
    return out, row
