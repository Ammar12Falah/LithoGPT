"""Pick the transformer setting (protocol section 6): among the six Arm A runs with seed
20260715 (dropout 0, 0.1, 0.2 x weight decay 0.01, 0.1), the one whose lowest development
loss is lowest. A tie goes to the earlier grid entry. Writes out/selected_setting.json and
prints the setting tag (for example do0.1_wd0.01).

  python -B x12_select.py [--runs runs]
"""
import sys

sys.dont_write_bytecode = True

import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4_common as vc  # noqa: E402
import t02_train as t2  # noqa: E402

GRID = [(do, wd) for do in (0.0, 0.1, 0.2) for wd in (0.01, 0.1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(vc.V4 / "runs"))
    args = ap.parse_args()
    rows = []
    for i, (do, wd) in enumerate(GRID):
        p = Path(args.runs) / t2.run_name("A", vc.SEED, do, wd) / "run.json"
        if not p.exists():
            sys.exit(f"ABORT: tuning run missing: {p}")
        s = json.loads(p.read_text())
        if not s.get("complete") or s["n_steps"] != t2.N_STEPS or s["ckpt_every"] != t2.CKPT_EVERY:
            sys.exit(f"ABORT: tuning run incomplete or not 3000 steps / every 100: {p}")
        rows.append(dict(order=i, dropout=do, wd=wd, best_dev_loss=s["best_dev_loss"], best_step=s["best_step"]))
    best = min(rows, key=lambda r: (r["best_dev_loss"], r["order"]))
    tag = f"do{best['dropout']:g}_wd{best['wd']:g}"
    vc.save_json(dict(setting=tag, dropout=best["dropout"], wd=best["wd"], table=rows,
                      rule="lowest development loss over checkpoints, Arm A seed 20260715"),
                 vc.OUT / "selected_setting.json")
    print(tag)


if __name__ == "__main__":
    main()
