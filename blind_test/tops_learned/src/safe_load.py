"""Load the cleaned input tables of the first run without the depths of
blocked wells, then run the first run's own loaders on them.

The first run's code (blind_test/tops_headroom/src) is imported, not copied
and not changed. Its loaders read the two tables of a country with
pandas.read_csv. Here that one call is replaced by a reader that never parses
the depth fields of blocked rows:

  pass 1  read every row, but only the columns that hold no depth
  pass 2  read the depth columns, skipping the lines of blocked rows

Blocked rows
  always        every row of a sealed well of the first run, and of its
                sidetracks or duplicate records
  stage "train" also every row of a well of the scoring half

To be safe the block is wider than the lists: every record dated on or after
the block date is blocked too (Kansas: spud date; Netherlands: end date of
drilling of the borehole that drilled the row). Such records can never be a
known well for a well before that date, so nothing the run may use is lost.
"""
import gzip
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                   # blind_test/tops_learned
RUN1 = ROOT.parent / "tops_headroom"                 # first run, read only
DATA = RUN1 / "data"
RES1 = RUN1 / "results"
sys.path.insert(0, str(RUN1 / "src"))

import kansas          # noqa: E402  (first-run loader, unchanged)
import netherlands     # noqa: E402
import pipeline        # noqa: E402
import methods         # noqa: E402
import run as run1     # noqa: E402  (first-run settings per country)

DEPTH_COLS = {
    "kansas_wells.csv.gz": ["DEPTH"],
    "kansas_tops.csv.gz": ["TOP"],
    "netherlands_wells.csv.gz": [],
    "netherlands_tops.csv.gz": ["TOP_AH", "BOTTOM_AH", "TV_TOP_NAP", "X_TOP_UTM31_ED50", "Y_TOP_UTM31_ED50"],
}


def first_run_lists(country):
    """Sealed wells, development wells and the cut date of the first run."""
    sp = pd.read_csv(RES1 / f"{country}_split.csv", parse_dates=["test_date"])
    sealed = pd.read_csv(RES1 / f"{country}_sealed_wells.csv", parse_dates=["test_date"])
    assert set(sealed["hole_id"]) == set(sp.loc[sp["period"] == "sealed", "hole_id"])
    dev = sp[sp["period"] == "development"].sort_values(["test_date", "hole_id"]).reset_index(drop=True)
    cut = sealed["test_date"].min()
    assert dev["test_date"].max() < cut
    return set(sealed["hole_id"]), dev[["hole_id", "test_date"]], cut


def _n_lines(path):
    n = 0
    with gzip.open(path, "rb") as f:
        for _ in f:
            n += 1
    return n


def _read_guarded(name, blocked_of):
    """Read one input table. blocked_of(frame without depth columns) -> bool
    mask of blocked rows. Depth fields of blocked rows are never parsed."""
    path = DATA / name
    dcols = DEPTH_COLS[name]
    header = list(pd.read_csv(path, nrows=0).columns)
    safe_cols = [c for c in header if c not in dcols]
    df = pd.read_csv(path, dtype=str, usecols=safe_cols)[safe_cols]
    assert _n_lines(path) == len(df) + 1, "a row spans more than one line; line skipping would be unsafe"
    blocked = np.asarray(blocked_of(df), dtype=bool)
    if dcols:
        key = safe_cols[0]
        skip = (np.nonzero(blocked)[0] + 1).tolist()          # +1: header line
        dep = pd.read_csv(path, dtype=str, usecols=[key] + dcols, skiprows=skip)
        assert len(dep) == int((~blocked).sum())
        assert (dep[key].to_numpy() == df.loc[~blocked, key].to_numpy()).all(), "row alignment lost"
        for c in dcols:
            col = np.full(len(df), np.nan, dtype=object)
            col[~blocked] = dep[c].to_numpy(dtype=object)
            df[c] = col
    return df[header], blocked


class _Shim:
    """Stands in for the name `pd` inside a first-run loader: read_csv hands
    out the guarded tables, everything else is plain pandas."""

    def __init__(self, tables):
        self._tables = tables

    def __getattr__(self, name):
        return getattr(pd, name)

    def read_csv(self, path, *args, **kwargs):
        return self._tables[Path(path).name].copy()


def load(country, stage, block_date=None):
    """Returns holes, picks, info. stage: "train" (scoring half blocked too,
    block_date = start of the scoring half) or "score"."""
    sealed, dev, cut = first_run_lists(country)
    if stage == "score":
        block_date = cut
    assert block_date is not None and block_date <= cut
    info = dict(country=country, stage=stage, block_date=str(pd.Timestamp(block_date).date()), sealed_wells=len(sealed))
    if country == "kansas":
        def blocked_wells(w):
            hid = np.where(w["API_NUM_NODASH"].notna(), "API" + w["API_NUM_NODASH"].str[:10], "KID" + w["KID"])
            spud = pd.to_datetime(w["SPUD"], format="%d-%b-%Y", errors="coerce")
            return pd.Series(hid).isin(sealed).to_numpy() | (spud >= block_date).to_numpy()
        wells, bw = _read_guarded("kansas_wells.csv.gz", blocked_wells)
        blocked_kid = set(wells.loc[bw, "KID"])
        tops, bt = _read_guarded("kansas_tops.csv.gz", lambda t: t["KID"].isin(blocked_kid))
        info.update(blocked_well_records=int(bw.sum()), blocked_top_rows=int(bt.sum()))
        mod = kansas
        tables = {"kansas_wells.csv.gz": wells, "kansas_tops.csv.gz": tops}
    else:
        wells, _ = _read_guarded("netherlands_wells.csv.gz", lambda w: np.zeros(len(w), bool))
        end = pd.to_datetime(wells.set_index("BOREHOLE_CODE")["END_DATE_DRILLING"], errors="coerce")
        late = set(end.index[end >= block_date])

        def blocked_tops(t):
            src = t["DATA_SOURCE"].str.split(" --> ").str[0].str.strip()
            return (t["STELSEL"].isin(sealed) | t["WELLBORE"].isin(sealed) | src.isin(sealed)
                    | src.isin(late) | t["WELLBORE"].isin(late) | t["STELSEL"].isin(late)).to_numpy()
        tops, bt = _read_guarded("netherlands_tops.csv.gz", blocked_tops)
        info.update(blocked_top_rows=int(bt.sum()))
        mod = netherlands
        tables = {"netherlands_wells.csv.gz": wells, "netherlands_tops.csv.gz": tops}
    real = mod.pd
    mod.pd = _Shim(tables)
    try:
        holes, picks, log, extra = mod.load()
    finally:
        mod.pd = real
    # ---- proofs that no blocked depth is in memory -------------------------
    assert not set(picks["hole_id"]) & sealed, "a sealed well has a pick in memory"
    if "system" in picks.columns:
        assert not set(picks["system"]) & sealed, "a sidetrack of a sealed well has a pick in memory"
    if stage == "train":
        # no well of the scoring half (development wells dated on or after the block date) has a pick
        scoring = set(dev.loc[dev["test_date"] >= block_date, "hole_id"])
        assert not set(picks["hole_id"]) & scoring, "a well of the scoring half has a pick in memory"
        if "system" in picks.columns:
            assert not set(picks["system"]) & scoring
    info.update(holes=len(holes), hole_top_values=len(picks))
    return holes, picks, info


def context(country, holes, picks):
    """First-run context (pools, date rule) with the first run's chosen tops
    and settings."""
    cfg = dict(run1.CONFIGS[country])
    ch = pd.read_csv(RES1 / f"{country}_chosen_tops.csv")
    ch = ch[ch["chosen"]].sort_values("order_top_down")
    tops = list(ch["top"])
    import json
    S = json.loads((RES1 / f"{country}_settings.json").read_text())
    ctx = pipeline.Ctx(cfg, holes, picks, tops)
    return ctx, cfg, S
