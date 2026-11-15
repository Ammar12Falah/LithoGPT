"""Collects the three readings of one test well into readings/, checks their form, makes the
combined reading and records the cost. Uses no expert labels.

Usage: python -I src/collect_well.py <well> <curve_min> <curve_tokens> <curve_pictures> \
                                          <log_min> <log_tokens> <log_pictures> \
                                          <text_min> <text_tokens> <text_pages_text> <text_page_pictures>
"""
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from combine import combine_arrays, to_intervals  # noqa: E402
from common import CLASSES, ROOT, well_code  # noqa: E402
from readings import load_reading, rasterise  # noqa: E402


def main():
    well = sys.argv[1]
    a = sys.argv[2:]
    code = well_code(well)
    pic_code = pd.read_csv(ROOT / "work" / "picture_codes.csv").set_index("well").code[well]
    out = ROOT / "readings"
    out.mkdir(exist_ok=True)
    # curve picture and log picture: one file each
    shutil.copy(ROOT / "work" / "curve_read" / f"read_{pic_code}" / "reading.csv", out / f"{code}__curve_picture.csv")
    shutil.copy(ROOT / "work" / "log_read" / code / "reading.csv", out / f"{code}__log_picture.csv")
    # text: one file, or parts joined in file-name order
    tdir = ROOT / "work" / "text_read" / f"{code}_out"
    parts = sorted(tdir.glob("reading_part*.csv"))
    if (tdir / "reading.csv").exists() and not parts:
        shutil.copy(tdir / "reading.csv", out / f"{code}__text.csv")
    else:
        files = parts + ([tdir / "reading.csv"] if (tdir / "reading.csv").exists() else [])
        frames = [pd.read_csv(f, dtype=str, keep_default_na=False) for f in files]
        cols = list(frames[0].columns)
        for f, fr in zip(files, frames):
            assert list(fr.columns) == cols, f"header differs in {f.name}"
        pd.concat(frames, ignore_index=True).to_csv(out / f"{code}__text.csv", index=False)
        print("text reading joined from", [f.name for f in files])
    if (tdir / "notes.txt").exists():
        shutil.copy(tdir / "notes.txt", out / f"{code}__text_notes.txt")

    logs = pd.read_parquet(ROOT / "data" / "logs_all.parquet", columns=["WELL", "DEPTH_MD"])
    d = np.sort(logs[logs.WELL == well].DEPTH_MD.to_numpy())
    rd = {}
    for r in ("curve_picture", "log_picture", "text"):
        df = load_reading(out / f"{code}__{r}.csv")
        rd[r] = df
        raw = pd.read_csv(out / f"{code}__{r}.csv", dtype=str, keep_default_na=False)
        bad_cls = sorted(set(raw.rock_class[(raw.rock_class.str.strip() != "") & df.cls.isna().to_numpy()]))
        cls, _ = rasterise(df, d)
        used = pd.Series([CLASSES[i] for i in cls[cls >= 0]]).value_counts()
        print(f"{well} {r}: rows {len(df)}, rows without number depths {int(df.depth_from.isna().sum() + df.depth_to.isna().sum())}, "
              f"class words not among the 12: {bad_cls}, depth {df.depth_from.min()} to {df.depth_to.max()}, "
              f"coverage of depth steps {100 * (cls >= 0).mean():.1f}%")
        print("    metres by class:", {k: round(v * 0.152) for k, v in used.items()})
    cls, src, row = combine_arrays(rd["text"], rd["log_picture"], d)
    to_intervals(d, cls, src, row).to_csv(out / f"{code}__combined.csv", index=False)
    print(f"{well} combined: coverage {100 * (cls >= 0).mean():.1f}%, from text {100 * (src == 'text').mean():.1f}%, "
          f"from log picture {100 * (src == 'log_picture').mean():.1f}%")
    # cost table
    cost = out / "costs.csv"
    rows = pd.read_csv(cost) if cost.exists() else pd.DataFrame()
    rows = rows[rows.well != well] if len(rows) else rows
    new = pd.DataFrame([
        {"well": well, "reading": "curve picture", "minutes": float(a[0]), "subagent_tokens": int(a[1]),
         "pictures_looked_at": int(a[2]), "pages_text_read": 0, "rows": len(rd["curve_picture"])},
        {"well": well, "reading": "log picture", "minutes": float(a[3]), "subagent_tokens": int(a[4]),
         "pictures_looked_at": int(a[5]), "pages_text_read": 0, "rows": len(rd["log_picture"])},
        {"well": well, "reading": "text", "minutes": float(a[6]), "subagent_tokens": int(a[7]),
         "pictures_looked_at": int(a[9]), "pages_text_read": int(a[8]), "rows": len(rd["text"])},
    ])
    pd.concat([rows, new], ignore_index=True).to_csv(cost, index=False)


if __name__ == "__main__":
    main()
