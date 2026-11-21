"""Step 5, scores (protocol section 8) and main comparisons (section 9).

  python -B s05_score.py score gens/<run>/best/pilot [more dirs ...]
      scores every <well>.npz in each directory against the real well; writes
      <dir>/scores.json (per well and the equal-weight mean over wells)
  python -B s05_score.py compare --wellset pilot --setting do0_wd0.01 --ckpt best
      collects per-(well, seed) scores and runs the four section 9 comparisons with the
      wells-and-seeds bootstrap (10,000 draws); writes out/compare_<wellset>_<ckpt>.json

The real side of every score is the real well on the same matched positions (generated
positions that are not boundary positions). Facies: real wells use their true labels where
the file has them; generated tokens use the token -> most common training facies map.
"""
import sys

sys.dont_write_bytecode = True

import argparse
import json
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4_common as vc  # noqa: E402
import v4_scores as sc  # noqa: E402

B = vc.BOUNDARY
SCORE_KEYS = ["bias_signed", "bias_abs", "w1", "spread", "trend_share_gen", "trend_share_real", "trend_gap",
              "structure", "facies_structure", "copy10_gen", "copy10_real", "copy10_gap", "copy20_gen",
              "copy20_real", "copy20_gap", "copy50_gen", "copy50_real", "copy50_gap", "osa_nll", "osa_top1",
              "osa_mse_std"]


def real_view(data, w, prime_n, L):
    seq = data.seq[w]
    sl = slice(prime_n, L)
    m = seq["tok"][sl] != B
    cur = data.curves_seq(w)[sl][m]
    return dict(nphi=cur[:, vc.NPHI], tok=seq["tok"][sl][m], fac=data.facies_seq(w)[sl][m],
                seg=seq["seg"][sl][m], depth=seq["depth"][sl][m]), m


def score_file(f, data, ngram_index, plant=None):
    z = np.load(f, allow_pickle=True)
    w = str(z["well"])
    prime_n, L = int(z["prime_n"]), int(z["L"])
    real, m = real_view(data, w, prime_n, L)
    gt = z["gen_tok"].astype(np.int64)
    # boundary positions must be exactly the real well's
    assert np.array_equal(gt[:, ~m], np.full((gt.shape[0], int((~m).sum())), B)), f"{f}: boundary mismatch"
    assert not np.any(gt[:, m] == B), f"{f}: boundary token at a matched position"
    gens = []
    for r in range(gt.shape[0]):
        t = gt[r][m]
        gens.append(dict(nphi=z["curves"][r][m][:, vc.NPHI].astype(np.float64), tok=t, fac=data.tok2fac[t]))
    s = sc.score_well(real, gens, ngram_index, plant=plant)
    if "osa_positions" in z.files:
        pos = z["osa_positions"]
        true = data.seq[w]["tok"][pos]
        s["osa_top1"] = float(np.mean(z["osa_top1"].astype(np.int64) == true))
        if "osa_logp_true" in z.files:
            s["osa_nll"] = float(-np.mean(z["osa_logp_true"]))
        if "osa_pred_std" in z.files:
            tgt = data.std_seq(w)[pos]
            s["osa_mse_std"] = float(np.mean((z["osa_pred_std"].astype(np.float64) - tgt) ** 2))
    s["n_real"] = int(gt.shape[0])
    s["n_generated"] = int(L - prime_n)
    return w, s


def train_seqs(data):
    return [data.train_seq[w] for w in data.split["train"]]


def build_ngram_index(data):
    vc.record_fit("ngram_index", data.split["train"])
    return sc.NgramIndex([(s["tok"], s["seg"]) for s in train_seqs(data)])


def summarize(per_well):
    return {k: sc.mean_over_wells(per_well, k) for k in SCORE_KEYS
            if any(k in v for v in per_well.values()) and all(k in v for v in per_well.values())}


def cmd_score(dirs, csv=None):
    split = vc.load_split()
    fit_df = vc.load_df(vc.FORCE_TRAIN_CSV)
    tk = vc.load_tokenizer()
    if csv:
        df = vc.load_df(Path(csv))
        data = vc.Data(split, df, tk, wells=sorted(df.WELL.astype(str).unique()), fit_df=fit_df)
    else:
        data = vc.Data(split, fit_df, tk)
    t0 = time.time()
    idx = build_ngram_index(data)
    print(f"n-gram index of the training wells built in {time.time() - t0:.0f}s", flush=True)
    for d in dirs:
        d = Path(d)
        files = sorted(p for p in d.glob("*.npz") if not p.name.endswith(".tmp.npz"))
        per_well = {}
        for f in files:
            w, s = score_file(f, data, idx)
            per_well[w] = s
        res = dict(dir=str(d), n_wells=len(per_well), mean_over_wells=summarize(per_well), per_well=per_well)
        vc.save_json(res, d / "scores.json")
        m = res["mean_over_wells"]
        print(f"{d}: {len(per_well)} wells | abs bias {m['bias_abs']['mean']:.4f} | W1 {m['w1']['mean']:.4f} | "
              f"spread {m['spread']['mean']:.3f} | structure {m['structure']['mean']:.4f} | facies structure "
              f"{m['facies_structure']['mean']:.4f}"
              + (f" | NLL {m['osa_nll']['mean']:.3f}" if "osa_nll" in m else "")
              + (f" | top-1 {m['osa_top1']['mean']:.3f}" if "osa_top1" in m else ""), flush=True)


def cmd_compare(wellset, setting, ckpt, gens_root, out_name=None, base_root=None):
    """Section 9 on the given well set. Model runs: gens/<arm>_seed<s>_<setting>/<ckpt>/<wellset>;
    baselines: gens/baseline_<name>/seed<s>/<wellset>. Seeds paired by order."""
    root = Path(gens_root)
    broot = Path(base_root) if base_root else root
    table, seeds_used = {}, {}
    arm_seeds = {"A": range(20260715, 20260727), "B2": range(20260715, 20260727)}
    for arm, seeds in arm_seeds.items():
        rows = []
        for s in seeds:
            p = root / f"{arm}_seed{s}_{setting}" / ckpt / wellset / "scores.json"
            if p.exists():
                rows.append((s, json.loads(p.read_text())["per_well"]))
        if rows:
            table[arm] = dict(rows)
            seeds_used[arm] = [s for s, _ in rows]
    for name in ("chain", "trigram", "block", "chain_nll", "trigram_nll"):
        rows = []
        for s in range(20260715, 20260727):
            p = broot / f"baseline_{name}" / f"seed{s}" / wellset / "scores.json"
            if p.exists():
                rows.append((s, json.loads(p.read_text())["per_well"]))
        if rows:
            table[name] = dict(rows)
            seeds_used[name] = [s for s, _ in rows]

    def common_wells(sources):
        wells = None
        for src in sources:
            for pw in table[src].values():
                wells = sorted(pw) if wells is None else sorted(set(wells) & set(pw))
        return wells or []

    # The four main comparisons use only their own sources, so the side baselines can never
    # change their wells or seeds. Paired by seed value (= by order); only seeds present for
    # both sides are used.
    main_src = [k for k in ("A", "B2", "chain", "trigram", "block") if k in table]
    wells = common_wells(main_src)
    res = dict(wellset=wellset, setting=setting, ckpt=ckpt, seeds_used=seeds_used, wells=wells)
    if wells:
        res["comparisons"] = sc.main_comparisons({k: table[k] for k in main_src}, wells)
    side_src = [k for k in ("A", "chain_nll", "trigram_nll") if k in table]
    side_wells = common_wells(side_src)
    if side_wells:
        res["side_comparisons"] = dict(
            note="side result, not part of the four main comparisons (ruling on Q18)", wells=side_wells,
            results=sc.main_comparisons({k: table[k] for k in side_src}, side_wells, comps=sc.SIDE_COMPARISONS))
    vc.save_json(res, vc.OUT / (out_name or f"compare_{wellset}_{ckpt}.json"))
    for k, v in list(res.get("comparisons", {}).items()) + [
            ("(side) " + k, v) for k, v in res.get("side_comparisons", {}).get("results", {}).items()]:
        if "estimate" in v:
            print(f"{k}: {v['estimate']:+.5f}  95% interval {v['lo']:+.5f} to {v['hi']:+.5f} "
                  f"({v['n_wells']} wells x {v['n_seeds']} seeds)")
        else:
            print(f"{k}: missing {v}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("score")
    a.add_argument("dirs", nargs="+")
    a.add_argument("--csv", default=None)
    b = sub.add_parser("compare")
    b.add_argument("--wellset", default="pilot")
    b.add_argument("--setting", required=True)
    b.add_argument("--ckpt", default="best")
    b.add_argument("--gens_root", default=str(vc.V4 / "gens"))
    b.add_argument("--base_root", default=None, help="baselines root if not gens_root")
    b.add_argument("--out_name", default=None)
    args = ap.parse_args()
    vc.check_protocol()
    if args.cmd == "score":
        cmd_score(args.dirs, args.csv)
    else:
        cmd_compare(args.wellset, args.setting, args.ckpt, args.gens_root, args.out_name, args.base_root)


if __name__ == "__main__":
    main()
