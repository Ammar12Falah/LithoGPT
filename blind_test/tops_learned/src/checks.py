"""Date-rule test and own-pick test on the known wells behind every feature.

The dates are read again from the input tables with the first run's
independent code (check_date_rule.kansas_dates, netherlands_dates_independent),
not taken from the pipeline. For every block of the audit:

  date rule   finish date of the record that supplied the known value
              <=  start date of the test well - waiting time
  own picks   the known well is never the test well itself, nor (Netherlands)
              a sidetrack of its hole system
"""
import numpy as np
import pandas as pd

import safe_load as SL

NAT = np.iinfo(np.int64).min
_cache = {}


def _day(s):
    return pd.to_datetime(s).values.astype("datetime64[D]").astype("int64")


def independent_dates(country):
    if country not in _cache:
        if country == "kansas":
            import check_date_rule
            _cache[country] = check_date_rule.kansas_dates()
        else:
            import netherlands_dates_independent
            _cache[country] = netherlands_dates_independent.dates()
    return _cache[country]


def check(country, ctx, audit):
    """Returns dict with the numbers checked and the violations found."""
    fin_by_record, spud_by_hole, wait = independent_dates(country)
    H, T = ctx.rec.shape
    flat = pd.Series(ctx.rec.ravel().astype(str))
    fin = flat.map(fin_by_record).to_numpy()
    fin = np.where((flat.to_numpy() == "") | pd.isna(fin), NAT, fin).astype(np.int64).reshape(H, T)
    hole_ids = ctx.holes["hole_id"].to_numpy()
    res = dict(known_well_uses=0, rows=0, date_violations=0, date_mismatch=0, loose_cutoff=0, own_pick=0, own_system=0)
    for b in audit.blocks:
        th = b["test_hole"]
        spud = pd.to_datetime(pd.Series(hole_ids[th]).map(spud_by_hole))
        assert spud.notna().all(), "test well without an independent start date"
        cut_ind = _day(spud - wait)
        res["loose_cutoff"] += int((b["cut"] > cut_ind).sum())
        cut = np.minimum(cut_ind, b["cut"])
        holes = b["holes"]
        ok = holes >= 0
        hs = np.where(ok, holes, 0)
        for tcol in b["tops"]:
            f = fin[hs, tcol]
            res["date_violations"] += int((ok & ((f == NAT) | (f > cut[:, None]))).sum())
            res["date_mismatch"] += int((ok & (ctx.avail[hs, tcol] != f)).sum())
        res["own_pick"] += int((ok & (holes == th[:, None])).sum())
        res["own_system"] += int((ok & (ctx.system[hs] == ctx.system[th][:, None])).sum())
        res["known_well_uses"] += int(ok.sum())
        res["rows"] += len(th)
    res["passed"] = all(res[k] == 0 for k in ["date_violations", "date_mismatch", "loose_cutoff", "own_pick", "own_system"])
    return res
