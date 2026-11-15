"""B1: score practice readings on the two practice wells (their expert labels may be seen).

Usage: python -I src/b1_practice.py <well> <reading.csv> <d_from> <d_to> [raw_column]
Prints the scores on the section, the table of expert class against reader class (metres), and,
if a raw column is named (rock_as_drawn or source_sentence), expert classes against the raw word.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CLASSES, CODE_TO_IDX, LAB, ROOT, STEP_M, item_scores, summarise  # noqa: E402
from readings import load_reading, rasterise  # noqa: E402


def truth_of(well, d0, d1):
    logs = pd.read_parquet(ROOT / "data" / "logs_all.parquet", columns=["row_id", "WELL", "DEPTH_MD"])
    lab = pd.read_parquet(ROOT / "data" / "labels_pool.parquet", columns=["row_id", LAB])
    s = logs[logs.WELL == well].merge(lab, on="row_id").sort_values("DEPTH_MD")
    s = s[(s.DEPTH_MD >= d0) & (s.DEPTH_MD < d1)]
    return s.DEPTH_MD.to_numpy(), s[LAB].map(CODE_TO_IDX).to_numpy().astype(int)


def main():
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_rows", 200)
    well, path, d0, d1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
    raw_col = sys.argv[5] if len(sys.argv) > 5 else None
    d, t = truth_of(well, d0, d1)
    rd = load_reading(path)
    p, row = rasterise(rd, d)
    it = item_scores(d, p, t)
    s = summarise(it, t)
    sh = summarise(item_scores(d, np.full(len(t), 2), t), t)
    print(f"{well} {d0:.0f}-{d1:.0f} m: rows {len(rd)}, coverage {s['coverage']:.3f}, strict {s['strict_all']:.3f}, "
          f"tolerant {s['tolerant_all']:.3f}, soft {s['soft_all']:.3f}, balanced {s['balanced_all']:.3f}  "
          f"| on read items: strict {s['strict_read']:.3f} tolerant {s['tolerant_read']:.3f} "
          f"| all-shale tolerant {sh['tolerant_all']:.3f}")
    conf = pd.crosstab(pd.Series([CLASSES[i] for i in t], name="expert"),
                       pd.Series([CLASSES[i] if i >= 0 else "(none)" for i in p], name="reader")) * STEP_M
    print(conf.round(0).astype(int))
    if raw_col and raw_col in rd.columns:
        raw = rd[raw_col].astype(str).str.lower().map(lambda x: re.split(r"[^a-z/ ]", x.strip())[0].strip()[:28])
        r = np.where(row >= 0, raw.to_numpy()[np.clip(row, 0, None)], "(none)")
        ct = pd.crosstab(pd.Series(r, name="raw word"), pd.Series([CLASSES[i] for i in t], name="expert")) * STEP_M
        ct["TOTAL"] = ct.sum(axis=1)
        print(ct.sort_values("TOTAL", ascending=False).round(0).astype(int).head(40))
    # length of the rows that were used, against correctness
    if "depth_from" in rd:
        ln = (rd.depth_to - rd.depth_from).abs().to_numpy()
        used = row >= 0
        L = ln[np.clip(row, 0, None)]
        for lo, hi in [(0, 1), (1, 5), (5, 10), (10, 30), (30, 100), (100, 1e9)]:
            m = used & (L >= lo) & (L < hi) & (p >= 0)
            if m.any():
                print(f"  rows of {lo}-{hi if hi < 1e8 else 'inf'} m: {m.sum() * STEP_M:7.0f} m read, strict {(p[m] == t[m]).mean():.3f}, "
                      f"tolerant {it.tolerant.to_numpy()[m].mean():.3f}")
        if "conf_rank" in rd:
            cr = rd.conf_rank.to_numpy()[np.clip(row, 0, None)]
            for k, name in [(3, "high"), (2, "medium"), (1, "low")]:
                m = used & (cr == k) & (p >= 0)
                if m.any():
                    print(f"  confidence {name}: {m.sum() * STEP_M:7.0f} m, strict {(p[m] == t[m]).mean():.3f}, tolerant {it.tolerant.to_numpy()[m].mean():.3f}")


if __name__ == "__main__":
    main()
