"""A1 step 1: list the well names of train.csv and draw the order.

Reads ONLY the WELL column of train.csv (no label values are loaded).
Checks that no held-out well is in the file.
Shuffles the sorted well names once with seed 20261115 and writes draw.csv.

Usage: python -I src/a1_draw.py
"""
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261115

HELD_OUT = [
    "15/9-14", "15/9-23", "16/2-7", "16/7-6", "17/4-1", "25/10-10", "25/10-9",
    "25/11-24", "25/5-3", "29/3-1", "31/2-10", "31/2-21 S", "34/10-16 R",
    "34/3-2 S", "34/3-3 A", "34/6-1 S", "35/11-5", "35/6-2 S", "35/9-7", "35/9-8",
]


def norm(name: str) -> str:
    """Normalise a well name for comparison: upper case, no spaces."""
    return "".join(str(name).upper().split())


def main() -> None:
    zpath = ROOT / "raw" / "force" / "train.zip"
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
        print("files in train.zip:", names)
        member = [n for n in names if n.lower().endswith("train.csv")][0]
        with z.open(member) as f:
            header = f.readline().decode("utf-8").strip()
        cols = header.split(";")
        print("columns:", cols)
        with z.open(member) as f:
            wells = pd.read_csv(f, sep=";", usecols=["WELL"])["WELL"]
    counts = wells.value_counts()
    names_sorted = sorted(counts.index.tolist())
    print("number of wells:", len(names_sorted))
    print("number of rows:", int(counts.sum()))

    held = {norm(w) for w in HELD_OUT}
    clash = [w for w in names_sorted if norm(w) in held]
    if clash:
        print("STOP: held-out wells found in train.csv:", clash)
        sys.exit(2)
    print("held-out check: none of the 20 held-out wells is in train.csv")

    rng = np.random.default_rng(SEED)
    order = rng.permutation(len(names_sorted))
    drawn = [names_sorted[i] for i in order]
    out = pd.DataFrame({
        "draw_order": np.arange(1, len(drawn) + 1),
        "well": drawn,
        "n_rows": [int(counts[w]) for w in drawn],
    })
    out.to_csv(ROOT / "draw_order_only.csv", index=False)
    print("wrote draw_order_only.csv")


if __name__ == "__main__":
    main()
