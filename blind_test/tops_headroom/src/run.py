"""One command: cleaned input tables -> every result file.

    .venv/bin/python -I src/run.py            # all countries with input tables
    .venv/bin/python -I src/run.py kansas     # one country

Reads data/*.csv.gz only. Writes results/, then runs the date-rule test and
refreshes hashes.txt.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parent

import pipeline  # noqa: E402

CONFIGS = {
    "kansas": dict(
        code="kansas", name="Kansas", feet=True,
        test_start=pd.Timestamp("2000-01-01"), tune_start=pd.Timestamp("1990-01-01"),
        wait=pd.DateOffset(months=12),
        test_date_meaning="earliest spud date of the hole",
        side_label="holes without an elevation flag (no GL or TOPO) and with a precise position",
        tune_sample=3000, tune_wells_m4=4000),
    "netherlands": dict(
        code="netherlands", name="Netherlands", feet=False, per_top_position=True,
        test_start=pd.Timestamp("1990-01-01"), tune_start=pd.Timestamp("1975-01-01"),
        wait=pd.DateOffset(years=5),
        test_date_meaning="end date of drilling of the borehole (the 5-year rule uses its start date of drilling)",
        side_label="vertical holes only, without a reference-height flag",
        radius_grid_m=[10000.0, 30000.0], pair_max_offset_m=250.0,
        tune_sample=3000, tune_wells_m4=4000),
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def write_hashes():
    lines = []
    man = ROOT / "manifest.csv"
    if man.exists():
        m = pd.read_csv(man)
        for _, r in m.iterrows():
            lines.append(f"{r['sha256']}  download: {r['file']}")
    for d in ["data", "results"]:
        for p in sorted((ROOT / d).glob("*")):
            if p.is_file():
                lines.append(f"{sha256(p)}  {d}/{p.name}")
    (ROOT / "hashes.txt").write_text("\n".join(lines) + "\n")


def main(argv):
    want = argv[1:] or [c for c in CONFIGS if (ROOT / "data" / f"{c}_wells.csv.gz").exists()]
    out = ROOT / "results"
    cache = ROOT / "cache"
    for c in want:
        t0 = time.time()
        mod = __import__(c)
        holes, picks, log, extra = mod.load()
        print(f"[{c}] loaded: {len(holes)} holes, {len(picks)} hole-top values ({time.time() - t0:.0f} s)", flush=True)
        s = pipeline.run_country(CONFIGS[c], holes, picks, log, extra, out, cache)
        print(json.dumps({k: v for k, v in s.items() if k != "settings"}, indent=1, default=float), flush=True)
        import io
        from contextlib import redirect_stdout
        import report_tables
        buf = io.StringIO()
        with redirect_stdout(buf):
            report_tables.main(c)
        (out / f"{c}_tables.md").write_text(buf.getvalue())
        print(f"[{c}] done in {time.time() - t0:.0f} s", flush=True)
    import check_date_rule
    ok = check_date_rule.main(["check_date_rule.py"] + want)
    write_hashes()
    return 0 if ok == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
