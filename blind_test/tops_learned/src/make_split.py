"""Split the development period of the first run into a tuning half and a
scoring half, from dates only. No depth is read: only the first run's split
files (hole id and date) are used.

    .venv/bin/python -I src/make_split.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from safe_load import ROOT, first_run_lists  # noqa: E402

OUT = ROOT / "results"


def split(country):
    _, dev, sealed_cut = first_run_lists(country)          # sorted by date, then hole id
    cut2 = dev["test_date"].iloc[len(dev) // 2]
    dev = dev.copy()
    dev["half"] = ["tuning" if d < cut2 else "scoring" for d in dev["test_date"]]
    return dev, cut2, sealed_cut


def main():
    OUT.mkdir(exist_ok=True)
    lines = []
    for c in ["kansas", "netherlands"]:
        dev, cut2, sealed_cut = split(c)
        dev.to_csv(OUT / f"{c}_dev_split.csv", index=False)
        n_t, n_s = int((dev["half"] == "tuning").sum()), int((dev["half"] == "scoring").sum())
        lines += [f"{c}: development wells of the first run: {len(dev)}",
                  f"{c}: date that separates the halves: {cut2.date()} (tuning half: dated before it; scoring half: on or after it)",
                  f"{c}: tuning half {n_t} wells, {dev['test_date'].min().date()} to {dev.loc[dev['half'] == 'tuning', 'test_date'].max().date()}",
                  f"{c}: scoring half {n_s} wells, {cut2.date()} to {dev['test_date'].max().date()}",
                  f"{c}: sealed period of the first run starts {sealed_cut.date()} (never loaded)", ""]
    (OUT / "dev_split_dates.txt").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
