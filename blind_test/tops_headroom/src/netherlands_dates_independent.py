"""Dutch dates for the date-rule test, read straight from the input table
with code that does not use the loader."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def _day(s):
    return pd.to_datetime(s).values.astype("datetime64[D]").astype("int64")


def dates():
    w = pd.read_csv(ROOT / "data" / "netherlands_wells.csv.gz", dtype=str,
                    usecols=["BOREHOLE_CODE", "START_DATE_DRILLING", "END_DATE_DRILLING"])
    start = pd.to_datetime(w["START_DATE_DRILLING"], errors="coerce")
    end = pd.to_datetime(w["END_DATE_DRILLING"], errors="coerce")
    lo, hi = pd.Timestamp("1900-01-01"), pd.Timestamp("2026-09-23")
    ok = (start >= lo) & (start <= hi) & (end >= lo) & (end <= hi) & (end >= start)
    start, end = start.where(ok), end.where(ok)
    fin_by_record = pd.Series(_day(end), index=w["BOREHOLE_CODE"].to_numpy())
    spud_by_hole = pd.Series(start.to_numpy(), index=w["BOREHOLE_CODE"].to_numpy())
    return fin_by_record, spud_by_hole, pd.DateOffset(years=5)
