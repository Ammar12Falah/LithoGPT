"""Kansas: raw downloads -> cleaned input tables (only the columns the run uses).

Run after download_kansas.sh. Reads raw/kansas/*.zip (not in git) and writes
data/kansas_wells.csv.gz and data/kansas_tops.csv.gz. All rows are kept; no
well or top is removed here. Every later cleaning choice is made in run.py so
it is repeated by the one-command rerun.
"""
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw" / "kansas"
DATA = ROOT / "data"

WELL_COLS = [
    "KID", "API_NUM_NODASH", "LATITUDE", "LONGITUDE", "LONG_LAT_SOURCE",
    "ELEVATION", "ELEV_REF", "DEPTH", "PERMIT", "SPUD", "COMPLETION",
    "PLUGGING", "STATUS", "COMMENTS",
]
TOP_COLS = ["KID", "ELEVATION", "ELEV_REF", "FORMATION", "TOP", "SOURCE"]


def read_zip(zname, member, cols):
    with zipfile.ZipFile(RAW / zname) as z:
        with z.open(member) as f:
            df = pd.read_csv(f, dtype=str, encoding="latin-1", usecols=cols)
    for c in df.columns:
        df[c] = df[c].str.strip()
    return df[cols]


def main():
    DATA.mkdir(exist_ok=True)
    w = read_zip("ks_wells.zip", "ks_wells.txt", WELL_COLS)
    # free-text comments are only used to spot deviated holes: keep the text
    # but collapse line breaks so the CSV stays one row per record
    w["COMMENTS"] = w["COMMENTS"].str.replace(r"\s+", " ", regex=True)
    t = read_zip("ks_tops.zip", "ks_tops.txt", TOP_COLS)
    gz = {"method": "gzip", "mtime": 0, "compresslevel": 9}
    w.to_csv(DATA / "kansas_wells.csv.gz", index=False, compression=gz)
    t.to_csv(DATA / "kansas_tops.csv.gz", index=False, compression=gz)
    print("wells rows", len(w), "tops rows", len(t))
    for f in ["kansas_wells.csv.gz", "kansas_tops.csv.gz"]:
        print(f, round((DATA / f).stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    sys.exit(main())
