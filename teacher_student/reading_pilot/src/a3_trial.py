"""A3 method trial on example wells only, and the choice of labelled example pictures.

  python -I src/a3_trial.py setup            builds the trial folders for 100 m and 50 m pictures
  python -I src/a3_trial.py score            scores the trial readings against the example-well labels
  python -I src/a3_trial.py final <length>   builds the fixed example set from all 10 example wells
The test wells' labels are never touched here.
"""
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a3_pictures as pics  # noqa: E402
from common import CLASSES, CODE_TO_IDX, LAB, ROOT, SEED, STEP_M, item_scores, summarise  # noqa: E402
from readings import load_reading, rasterise  # noqa: E402

N_EXAMPLES = {100: 20, 50: 30}
TRIAL_SECTION_M = 1000


def example_wells():
    d = pd.read_csv(ROOT / "draw.csv")
    return d[d.role == "example"].well.tolist()


def class_thickness(index: pd.DataFrame) -> pd.DataFrame:
    """Metres of every class in every labelled picture."""
    logs = pd.read_parquet(ROOT / "data" / "logs_all.parquet", columns=["row_id", "WELL", "DEPTH_MD"])
    lab = pd.read_parquet(ROOT / "data" / "labels_pool.parquet", columns=["row_id", LAB])
    m = logs.merge(lab, on="row_id")
    m["cls"] = m[LAB].map(CODE_TO_IDX)
    rows = []
    for _, r in index.iterrows():
        s = m[(m.WELL == r.well) & (m.DEPTH_MD >= r.top) & (m.DEPTH_MD < r.base)]
        t = np.bincount(s.cls.astype(int), minlength=len(CLASSES)) * STEP_M
        rows.append(t)
    return pd.DataFrame(rows, columns=CLASSES, index=index.index)


def select_examples(index: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """Covers every class present (at least 1 m in some picture), then fills up to n pictures,
    taking wells in turn and preferring pictures that hold two or more classes."""
    th = class_thickness(index)
    chosen = []
    present = [c for c in CLASSES if th[c].max() >= 1.0]
    # rare classes first
    for c in sorted(present, key=lambda c: th[c].sum()):
        if any(th.loc[i, c] >= 3.0 for i in chosen):
            continue
        cand = th[c].drop(index=chosen).sort_values(ascending=False)
        if len(cand) and cand.iloc[0] >= 1.0:
            chosen.append(cand.index[0])
    rng = np.random.default_rng(seed)
    n_cls = (th >= 2.0).sum(axis=1)
    rest = index.drop(index=chosen).copy()
    rest["n_cls"] = n_cls
    rest["rnd"] = rng.random(len(rest))
    wells = list(rng.permutation(index.well.unique()))
    while len(chosen) < n and len(rest):
        for w in wells:
            sub = rest[rest.well == w].sort_values(["n_cls", "rnd"], ascending=[False, False])
            if len(sub) and len(chosen) < n:
                chosen.append(sub.index[0])
                rest = rest.drop(index=sub.index[0])
    out = index.loc[chosen].copy()
    out["classes_m"] = [", ".join(f"{c} {th.loc[i, c]:.0f}" for c in CLASSES if th.loc[i, c] >= 1.0) for i in chosen]
    return out


def setup():
    ex = example_wells()
    rng = np.random.default_rng(SEED + 2)
    hidden = [ex[i] for i in sorted(rng.choice(len(ex), size=3, replace=False))]
    shown = [w for w in ex if w not in hidden]
    logs = pd.read_parquet(ROOT / "data" / "logs_all.parquet", columns=["WELL", "DEPTH_MD"])
    sections = {}
    for w in hidden:
        d = logs[logs.WELL == w].DEPTH_MD
        lo, hi = np.ceil(d.min() / 100) * 100, np.floor(d.max() / 100) * 100
        if hi - lo <= TRIAL_SECTION_M:
            sections[w] = (lo, hi)
        else:
            start = lo + 100 * rng.integers(0, int((hi - lo - TRIAL_SECTION_M) / 100) + 1)
            sections[w] = (start, start + TRIAL_SECTION_M)
    base = ROOT / "work" / "curve_trial"
    if base.exists():
        shutil.rmtree(base)
    plan = []
    for L in (100, 50):
        lab_dir = base / f"L{L}" / "_labelled_all"
        pics.make(L, lab_dir, "labelled", shown)
        idx = pd.read_csv(lab_dir / "_index.csv")
        sel = select_examples(idx, N_EXAMPLES[L], SEED + L)
        ex_dir = base / f"L{L}" / "examples"
        ex_dir.mkdir(parents=True)
        for i, (_, r) in enumerate(sel.iterrows(), 1):
            shutil.copy(lab_dir / r.file, ex_dir / f"example_{i:02d}_{r.file}")
        sel.to_csv(base / f"L{L}" / "examples_chosen.csv", index=False)
        for w in hidden:
            wd = base / f"L{L}" / f"read_{pics.codes()[w]}"
            pics.make(L, wd / "pictures", "unlabelled", [w], sections[w])
            (wd / "pictures" / "_index.csv").unlink()
            plan.append({"length": L, "well": w, "code": pics.codes()[w], "from": sections[w][0], "to": sections[w][1],
                         "folder": str(wd.relative_to(ROOT))})
    pd.DataFrame(plan).to_csv(base / "plan.csv", index=False)
    print("hidden wells:", hidden, "sections:", sections)
    print(pd.DataFrame(plan).to_string(index=False))


def score_reading(well, path, d0=None, d1=None):
    logs = pd.read_parquet(ROOT / "data" / "logs_all.parquet", columns=["row_id", "WELL", "DEPTH_MD"])
    lab = pd.read_parquet(ROOT / "data" / "labels_pool.parquet", columns=["row_id", LAB])
    s = logs[logs.WELL == well].merge(lab, on="row_id").sort_values("DEPTH_MD")
    if d0 is not None:
        s = s[(s.DEPTH_MD >= d0) & (s.DEPTH_MD < d1)]
    truth = s[LAB].map(CODE_TO_IDX).to_numpy().astype(int)
    pred, _ = rasterise(load_reading(path), s.DEPTH_MD.to_numpy())
    it = item_scores(s.DEPTH_MD.to_numpy(), pred, truth)
    return it, truth, pred


def score():
    base = ROOT / "work" / "curve_trial"
    plan = pd.read_csv(base / "plan.csv")
    rows = []
    for L, g in plan.groupby("length"):
        items, truths = [], []
        for _, r in g.iterrows():
            f = ROOT / r.folder / "reading.csv"
            if not f.exists():
                print("missing", f)
                continue
            it, truth, pred = score_reading(r.well, f, r["from"], r["to"])
            s = summarise(it, truth)
            s.update({"length": L, "well": r.well})
            rows.append(s)
            items.append(it)
            truths.append(truth)
            conf = pd.crosstab(pd.Series([CLASSES[t] for t in truth], name="expert"),
                               pd.Series([CLASSES[p] if p >= 0 else "(none)" for p in pred], name="reader"))
            print(f"--- L={L} {r.well}\n{conf}")
            # all-shale line on the same items, for reference
            sh = summarise(item_scores(np.arange(len(truth)) * STEP_M, np.full(len(truth), 2), truth), truth)
            rows.append({**sh, "length": L, "well": r.well + " (all-shale)"})
        if items:
            s = summarise(pd.concat(items, ignore_index=True), np.concatenate(truths))
            s.update({"length": L, "well": "POOLED"})
            rows.append(s)
    out = pd.DataFrame(rows)
    cols = ["length", "well", "metres", "coverage", "strict_all", "tolerant_all", "soft_all", "balanced_all"]
    print(out[cols].round(3).to_string(index=False))
    out.to_csv(base / "trial_scores.csv", index=False)


def final(L: int):
    ex = example_wells()
    base = ROOT / "work" / "curve_read"
    lab_dir = base / "_labelled_all"
    if lab_dir.exists():
        shutil.rmtree(lab_dir)
    pics.make(L, lab_dir, "labelled", ex)
    idx = pd.read_csv(lab_dir / "_index.csv")
    sel = select_examples(idx, N_EXAMPLES[L], SEED + L)
    ex_dir = base / "examples"
    if ex_dir.exists():
        shutil.rmtree(ex_dir)
    ex_dir.mkdir(parents=True)
    for i, (_, r) in enumerate(sel.iterrows(), 1):
        shutil.copy(lab_dir / r.file, ex_dir / f"example_{i:02d}_{r.file}")
    sel.drop(columns=["well"]).to_csv(base / "examples_chosen.csv", index=False)
    print(sel[["code", "file", "classes_m"]].to_string(index=False))


if __name__ == "__main__":
    if sys.argv[1] == "setup":
        setup()
    elif sys.argv[1] == "score":
        score()
    else:
        final(int(sys.argv[2]))
