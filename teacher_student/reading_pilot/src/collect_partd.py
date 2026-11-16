"""Part D: collects the readings of the cheaper readers (Sonnet 5.5, Haiku 5.5) into readings/,
checks their form, builds their combined readings with the same fixed rule, and writes the cost table.
Uses no expert labels.   Usage: python -I src/collect_partd.py
File names: readings/<well>__<reading>__<model>.csv
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
    draw = pd.read_csv(ROOT / "draw.csv")
    wells = draw[draw.role == "test"].well.tolist()
    pic = pd.read_csv(ROOT / "work" / "picture_codes.csv").set_index("well").code
    logs = pd.read_parquet(ROOT / "data" / "logs_all.parquet", columns=["WELL", "DEPTH_MD"])
    out = ROOT / "readings"
    rows_n = {}
    for model in ("sonnet", "haiku"):
        base = ROOT / "work" / "partd" / model
        for well in wells:
            code = well_code(well)
            d = np.sort(logs[logs.WELL == well].DEPTH_MD.to_numpy())
            got = {}
            for r, folder in [("curve_picture", f"curve_{pic[well]}"), ("log_picture", f"log_{code}"), ("text", f"text_{code}")]:
                src = base / folder
                parts = sorted(src.glob("reading_part*.csv"))
                files = parts + ([src / "reading.csv"] if (src / "reading.csv").exists() else [])
                if not files:
                    print(f"MISSING {model} {well} {r}")
                    continue
                dst = out / f"{code}__{r}__{model}.csv"
                note = ""
                try:
                    frames = [pd.read_csv(f, dtype=str, keep_default_na=False) for f in files]
                    cols = list(frames[0].columns)
                    same = all(list(fr.columns) == cols for fr in frames)
                    if len(files) == 1:
                        shutil.copy(files[0], dst)
                    elif same:
                        pd.concat(frames, ignore_index=True).to_csv(dst, index=False)
                    else:
                        # parts with different headers: keep the columns of the first part, fill what is missing
                        pd.concat([fr.reindex(columns=cols, fill_value="") for fr in frames], ignore_index=True).to_csv(dst, index=False)
                        note = " (parts had different headers; columns of the first part kept)"
                    df = load_reading(dst)
                except Exception as e:  # a file that cannot be parsed is recorded, not repaired
                    print(f"UNREADABLE {model} {well} {r}: {type(e).__name__}: {str(e)[:120]}")
                    if dst.exists():
                        dst.rename(out / "set_aside" / (dst.name + ".unreadable"))
                    continue
                if (src / "notes.txt").exists():
                    shutil.copy(src / "notes.txt", out / f"{code}__text_notes__{model}.txt")
                got[r] = df
                raw = pd.read_csv(dst, dtype=str, keep_default_na=False)
                bad = sorted(set(raw.rock_class[(raw.rock_class.str.strip() != "") & df.cls.isna().to_numpy()]))
                cls, _ = rasterise(df, d)
                rows_n[(model, well, r.replace("_", " "))] = len(df)
                print(f"{model} {well} {r}: rows {len(df)}, no-number depths {int(df.depth_from.isna().sum() + df.depth_to.isna().sum())}, "
                      f"class words not among the 12: {bad[:6]}, coverage {100 * (cls >= 0).mean():.1f}%{note}")
            if "text" in got and "log_picture" in got:
                cls, src_, row = combine_arrays(got["text"], got["log_picture"], d)
                to_intervals(d, cls, src_, row).to_csv(out / f"{code}__combined__{model}.csv", index=False)
    c = pd.read_csv(ROOT / "work" / "partd" / "costs_raw.csv")
    c["minutes"] = (c.seconds / 60).round(1)
    c["rows"] = [rows_n.get((m, w, r), 0) for m, w, r in zip(c.model, c.well, c.reading)]
    c[["model", "well", "reading", "minutes", "subagent_tokens", "pictures_looked_at", "pages_text_read", "rows", "note"]] \
        .to_csv(out / "costs_partd.csv", index=False)
    print("cost rows:", len(c))


if __name__ == "__main__":
    main()
