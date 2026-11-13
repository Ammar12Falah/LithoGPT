"""Netherlands: raw downloads -> cleaned input tables (only the columns the
run uses). All boreholes and all lithostratigraphy rows are kept.

Reads raw/netherlands/thematische_data_boringen.zip (from www.nlog.nl) and
raw/netherlands/NLOG_Boreholes_ED50UTM31N.json (the "All boreholes" file that
NLOG's page "Files interactive map" links to). Writes
data/netherlands_wells.csv.gz and data/netherlands_tops.csv.gz.
"""
import json
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw" / "netherlands"
DATA = ROOT / "data"

WELL_COLS = ["BOREHOLE_CODE", "NITG_NUMBER", "BOREHOLE_OR_SIDETRACK_CODE", "BOREHOLE_TYPE_CODE",
             "START_DATE_DRILLING", "END_DATE_DRILLING", "BOREHOLE_SHAPE", "ON_OFFSHORE_CODE",
             "REFERENCE_LEVEL", "REFERENCE_LEVEL_HEIGHT", "REFERENCE_LEVEL_RELATIVE_TO"]
TOP_COLS = ["WELLBORE", "STELSEL", "DATA_SOURCE", "TOP_AH", "BOTTOM_AH", "TV_TOP_NAP",
            "STRAT_UNIT_CD", "STRAT_UNIT_NM", "ANOMALY_CD", "X_TOP_UTM31_ED50", "Y_TOP_UTM31_ED50",
            "STRAT_SOURCE_CD"]


def main():
    DATA.mkdir(exist_ok=True)
    d = json.load(open(RAW / "NLOG_Boreholes_ED50UTM31N.json", encoding="utf-8"))
    rows = []
    for f in d["features"]:
        p = f["properties"]
        r = {c: p.get(c) for c in WELL_COLS}
        g = f.get("geometry") or {}
        xy = g.get("coordinates") or [None, None]
        r["X_UTM31_ED50"], r["Y_UTM31_ED50"] = xy[0], xy[1]
        rows.append(r)
    w = pd.DataFrame(rows).sort_values("BOREHOLE_CODE")
    with zipfile.ZipFile(RAW / "thematische_data_boringen.zip") as z:
        name = [n for n in z.namelist() if n.startswith("nlog_stratstelsel") and n.endswith(".csv")][0]
        with z.open(name) as f:
            t = pd.read_csv(f, sep=";", dtype=str, encoding="utf-8", usecols=TOP_COLS)
    t = t[TOP_COLS]
    for c in ["TOP_AH", "BOTTOM_AH", "TV_TOP_NAP", "X_TOP_UTM31_ED50", "Y_TOP_UTM31_ED50"]:
        t[c] = t[c].str.replace(",", ".", regex=False)   # decimal comma -> decimal point
    gz = {"method": "gzip", "mtime": 0, "compresslevel": 9}
    w.to_csv(DATA / "netherlands_wells.csv.gz", index=False, compression=gz)
    t.to_csv(DATA / "netherlands_tops.csv.gz", index=False, compression=gz)
    print("boreholes", len(w), "strat rows", len(t), "from", name)
    for f in ["netherlands_wells.csv.gz", "netherlands_tops.csv.gz"]:
        print(f, round((DATA / f).stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
