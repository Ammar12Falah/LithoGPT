"""Date-rule test. Fails (exit code 1) if any known well used for any forecast
was finished too late for that test well.

The dates are read again from the cleaned input tables with separate code,
not taken from the pipeline. For every forecast of every method the script
looks up the records of the known wells that were used and checks

    finish date of the known record  <=  spud date of the test well - waiting time

(main run: 12 months in Kansas, 5 years in the Netherlands; side run with no
waiting time: finished before the spud day).

    .venv/bin/python -I src/check_date_rule.py [kansas] [netherlands]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
NAT = np.iinfo(np.int64).min


def _day(s):
    return pd.to_datetime(s).values.astype("datetime64[D]").astype("int64")


def kansas_dates():
    w = pd.read_csv(ROOT / "data" / "kansas_wells.csv.gz", dtype=str,
                    usecols=["KID", "API_NUM_NODASH", "SPUD", "COMPLETION", "PLUGGING"])
    lo, hi = pd.Timestamp("1860-01-01"), pd.Timestamp("2026-10-09")
    d = {}
    for c in ["SPUD", "COMPLETION", "PLUGGING"]:
        x = pd.to_datetime(w[c], format="%d-%b-%Y", errors="coerce")
        d[c] = x.where((x >= lo) & (x <= hi))
    fin = d["COMPLETION"].where(~(d["SPUD"] > d["COMPLETION"]), d["SPUD"])
    plug_ok = d["PLUGGING"].where(d["SPUD"].isna() | (d["PLUGGING"] >= d["SPUD"]))
    fin = fin.fillna(plug_ok)
    fin_by_record = pd.Series(_day(fin), index=w["KID"].to_numpy())
    api10 = w["API_NUM_NODASH"].str[:10]
    spud_api = d["SPUD"].groupby("API" + api10).min()
    spud_kid = pd.Series(d["SPUD"].to_numpy(), index="KID" + w["KID"])
    spud_by_hole = pd.concat([spud_api, spud_kid])
    return fin_by_record, spud_by_hole, pd.DateOffset(months=12)


def netherlands_dates():
    import netherlands_dates_independent as ndi
    return ndi.dates()


def check(country):
    fin_by_record, spud_by_hole, wait = {"kansas": kansas_dates, "netherlands": netherlands_dates}[country]()
    total_forecasts = 0
    total_uses = 0
    bad = 0
    report = []
    for tag, w8 in [("", wait), ("_no_wait", None)]:
        a = np.load(ROOT / "cache" / f"{country}_audit{tag}.npz", allow_pickle=False)
        T = int(a["T"])
        rec = a["rec"]
        H = rec.shape[0]
        # independent finish day of the record behind every (hole, top) value
        flat = pd.Series(rec.ravel())
        fin = flat.map(fin_by_record).to_numpy()
        fin = np.where(flat.to_numpy() == "", NAT, np.where(pd.isna(fin), NAT, fin)).astype(np.int64).reshape(H, T)
        # the pipeline's own dates must agree with the independent ones
        used_any = np.zeros((H, T), bool)
        spud = pd.to_datetime(pd.Series(a["test_hole_id"]).map(spud_by_hole))
        assert spud.notna().all(), "test well without an independent spud date"
        if w8 is None:
            cut_ind = _day(spud) - 1
        else:
            cut_ind = _day(spud - w8)
        cut = np.minimum(cut_ind, a["cut"])
        item_w, item_top, item_chain = a["item_w"], a["item_top"], a["item_chain"]
        n2, nt, n3 = int(a["n2"]), int(a["nt"]), a["n3"]
        nf = 0
        nu = 0
        nbad = 0

        def test_block(holes, w_rows, tops):
            """holes: (n, k) known hole index or -1; tops: list of top columns
            whose records must all be early enough."""
            nonlocal nu, nbad
            ok = holes >= 0
            hs = np.where(ok, holes, 0)
            for tcol in tops:
                f = fin[hs, tcol]
                viol = ok & ((f == NAT) | (f > cut[w_rows][:, None]))
                nbad += int(viol.sum())
                used_any[hs[ok], tcol] = True
            nu += int(ok.sum())

        for j in range(T):
            m = item_top == j
            if not m.any():
                continue
            w = item_w[m]
            hj = a[f"top{j}_hole"]
            test_block(hj[w, :1], w, [j]);            nf += int(m.sum())   # method 1
            test_block(hj[w, :n2], w, [j]);           nf += int(m.sum())   # method 2
            test_block(hj[w, :int(n3[j])], w, [j]);   nf += int(m.sum())   # method 3
        # method 4: start of chain (kriging of the anchor top) and every thickness link
        for chain in np.unique(item_chain):
            m = item_chain == chain
            w = item_w[m]
            tops = [b for b in range(T) if (int(chain) >> b) & 1]
            a0 = tops[0]
            test_block(a[f"top{a0}_hole"][w, :int(n3[a0])], w, [a0])
            for x, y in zip(tops[:-1], tops[1:]):
                test_block(a[f"link{x}_{y}_hole"][w, :nt], w, [x, y])
            nf += int(m.sum())
        # side method 4b: direct kriging, or one overlying top plus one thickness
        route = a["item_route4b"]
        for j in range(T):
            for r in np.unique(route[item_top == j]):
                m = (item_top == j) & (route == r)
                w = item_w[m]
                r = int(r)
                test_block(a[f"top{r}_hole"][w, :int(n3[r])], w, [r])
                if r != j:
                    test_block(a[f"link{r}_{j}_hole"][w, :nt], w, [r, j])
                nf += int(m.sum())
        # pipeline dates equal the independent dates wherever a value was used
        mism = int((a["avail"][used_any] != fin[used_any]).sum())
        loose = int((a["cut"] > cut_ind).sum())
        name = "main run" if tag == "" else "no waiting time"
        report.append(f"{country}, {name}: {nf} forecasts checked, {nu} uses of a known well checked, "
                      f"{nbad} violations, {mism} date mismatches between pipeline and input table, "
                      f"{loose} test wells with a cut-off later than the independent one")
        total_forecasts += nf
        total_uses += nu
        bad += nbad + mism + loose
    return total_forecasts, total_uses, bad, report


def main(argv):
    countries = argv[1:] or ["kansas"]
    lines = []
    bad_all = 0
    for c in countries:
        nf, nu, bad, rep = check(c)
        lines += rep
        lines.append(f"{c}: total {nf} forecasts and {nu} known-well uses checked; {'PASS' if bad == 0 else 'FAIL'}")
        bad_all += bad
    out = ROOT / "results" / "date_rule_check.txt"
    keep = []
    if out.exists():
        keep = [ln for ln in out.read_text().splitlines() if ln and not any(ln.startswith(c) for c in countries)]
    out.write_text("\n".join(keep + lines) + "\n")
    print("\n".join(lines))
    return 0 if bad_all == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
