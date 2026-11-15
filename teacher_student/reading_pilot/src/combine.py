"""Combined reading: joins the text reading and the log-picture reading into one class by depth.

The rule is written in reading_rules.md (section "Combined reading") and coded in `combine_arrays`.
Runs BEFORE the freeze. Uses no expert labels and no model output.

Usage: python -I src/combine.py <well> [<well> ...]     writes readings/<well>__combined.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CLASSES, ROOT, well_code  # noqa: E402
from readings import load_reading, rasterise  # noqa: E402

RULE = json.loads((ROOT / "src" / "combine_rule.json").read_text()) if (ROOT / "src" / "combine_rule.json").exists() \
    else {"text_max_len_m": 10.0}


def row_lengths(df):
    return (df["depth_to"] - df["depth_from"]).abs().to_numpy()


def combine_arrays(text_df, log_df, depths):
    """Rule: at each depth step
       1. if the text reading gives a class from a row no longer than text_max_len_m metres
          (a sample, core or sidewall-core description), take the text class;
       2. else if the log-picture reading gives a class, take it;
       3. else take the text class from a longer row, if any;
       4. else no class."""
    t_cls, t_row = rasterise(text_df, depths)
    l_cls, l_row = rasterise(log_df, depths)
    t_len = np.full(len(depths), np.inf)
    ok = t_row >= 0
    tl = row_lengths(text_df)
    t_len[ok] = tl[t_row[ok]]
    fine = (t_cls >= 0) & (t_len <= RULE["text_max_len_m"])
    out = np.where(fine, t_cls, np.where(l_cls >= 0, l_cls, t_cls))
    src = np.where(fine, "text", np.where(l_cls >= 0, "log_picture", np.where(t_cls >= 0, "text", "")))
    row = np.where(fine, t_row, np.where(l_cls >= 0, l_row, t_row))
    return out, src, row


def to_intervals(depths, cls, src, row):
    """Run-length encoding on the depth steps; boundaries at the midpoints between steps."""
    rows = []
    n = len(depths)
    if n == 0:
        return pd.DataFrame()
    mid = np.r_[depths[0] - 0.076, (depths[1:] + depths[:-1]) / 2, depths[-1] + 0.076]
    start = 0
    for i in range(1, n + 1):
        new = i == n or cls[i] != cls[start] or src[i] != src[start] or row[i] != row[start] \
            or depths[i] - depths[i - 1] > 0.5
        if new:
            if cls[start] >= 0:
                a = mid[start]
                b = mid[i] if (i == n or depths[i] - depths[i - 1] <= 0.5) else depths[i - 1] + 0.076
                rows.append({"depth_from": round(float(a), 3), "depth_to": round(float(b), 3),
                             "rock_class": CLASSES[int(cls[start])], "source_reading": src[start],
                             "source_row": int(row[start]) + 2})   # line number in the source CSV (header = line 1)
            start = i
    return pd.DataFrame(rows)


def main():
    logs = pd.read_parquet(ROOT / "data" / "logs_all.parquet", columns=["WELL", "DEPTH_MD"])
    for well in sys.argv[1:]:
        code = well_code(well)
        d = np.sort(logs[logs.WELL == well].DEPTH_MD.to_numpy())
        t = load_reading(ROOT / "readings" / f"{code}__text.csv")
        lg = load_reading(ROOT / "readings" / f"{code}__log_picture.csv")
        cls, src, row = combine_arrays(t, lg, d)
        out = to_intervals(d, cls, src, row)
        out.to_csv(ROOT / "readings" / f"{code}__combined.csv", index=False)
        cov = (cls >= 0).mean()
        print(well, "combined rows:", len(out), "coverage of depth steps:", round(float(cov), 3),
              "from text:", round(float((src == "text").mean()), 3))


if __name__ == "__main__":
    main()
