"""Step 3, generation (protocol section 8) for a trained run, plus one-step-ahead scores.

Adapted from paper_atce/multiseed/ms_regen.py: the generated tokens AND the decoded
curves are saved, one file per well, so nothing has to be regenerated to rescore.
Boundary positions are copied from the real well. Prime: the first quarter of the
well's sequence, at least 512 tokens. The rest of the well is generated, no cap.
Discrete arms: 5 realizations, temperature 1, generation seed 20260715 for every run
(pilot convention). Arm C: one deterministic realization.

  python -B g03_generate.py --run_dir runs/A_seed20260715_do0_wd0.01 --ckpt best --wells pilot
  python -B g03_generate.py ... --csv /path/confirmatory.csv           (confirmatory wells)
  python -B g03_generate.py ... --well "16/4-1" --n_real 1             (smoke test)

Writes <outroot>/<run>/<ckpt>/<well>.npz with gen_tok [R, L-prime], curves [R, L-prime, 4]
in real units (RDEP in ohm-m, NaN at boundary positions) and one-step-ahead arrays.
"""
import sys

sys.dont_write_bytecode = True

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4_common as vc  # noqa: E402
import v4_model as vm  # noqa: E402

GEN_SEED = vc.SEED
MIN_VALID = 2000          # section 3: a well is eligible with at least 2,000 valid samples


def safe(w):
    return w.replace("/", "_").replace(" ", "")


def load_run_model(run_dir, ckpt_tag, device):
    ck = torch.load(Path(run_dir) / f"{ckpt_tag}.pt", map_location=device, weights_only=False)
    model = vm.LithoGPTv4(ck["arm"], dropout=ck["dropout"]).to(device)
    model.load_state_dict(ck["model_state"])
    model.eval()
    return model, ck


def eligible_wells(data, wells):
    return [w for w in wells if data.rows[w]["n_valid"] >= MIN_VALID]


def decode_generated(tk, gen_tok, gen_rows=None):
    """Generated output -> curves in real units (GR API, RDEP ohm-m, NPHI v/v, RHOB g/cc),
    NaN at boundary positions. Discrete arms (gen_rows None): token centroids. Arm C:
    the regression rows, which are standardized GR, log10 RDEP, NPHI, RHOB."""
    R = gen_tok.shape[0]
    if gen_rows is None:
        return np.stack([tk.decode_tokens(gen_tok[r]) for r in range(R)])
    curves = np.full(gen_rows.shape, np.nan)
    for r in range(R):
        m = gen_tok[r] != vc.BOUNDARY
        curves[r, m] = tk.decode_std(gen_rows[r, m])
    return curves


def generate_well(model, ck, data, w, n_real, device, max_gen=None, log=print):
    tk = data.tk
    seq = data.seq[w]
    tok = seq["tok"]
    L_full = tok.size
    prime_n = vc.prime_len(L_full)
    L = L_full if not max_gen else min(L_full, prime_n + max_gen)
    tok = tok[:L]
    dfeat = data.dfeat_b2(w)[:L] if model.use_depth_embed else None
    R = n_real if model.discrete else 1
    t0 = time.time()
    gen_tok, gen_rows = vm.generate(model, tok, prime_n, R, GEN_SEED, dfeat=dfeat, centers_std=tk.centers,
                                    device=device,
                                    progress=lambda i, n: log(f"    {w}: {i}/{n} positions ({time.time() - t0:.0f}s)"))
    t_gen = time.time() - t0
    curves = decode_generated(tk, gen_tok, gen_rows)
    pos = prime_n + np.flatnonzero(tok[prime_n:] != vc.BOUNDARY)
    t1 = time.time()
    osa = vm.one_step_ahead(model, tok, pos, dfeat=dfeat, centers_std=tk.centers, device=device,
                            batch=(128 if device.startswith("cuda") else 64))
    t_osa = time.time() - t1
    rec = dict(well=w, prime_n=prime_n, L=L, L_full=L_full, gen_tok=gen_tok.astype(np.int16),
               curves=curves.astype(np.float32), osa_positions=pos.astype(np.int64),
               osa_top1=osa["top1"].astype(np.int16), seconds_gen=t_gen, seconds_osa=t_osa,
               n_generated=int(L - prime_n), n_real=R, gen_seed=GEN_SEED, ckpt_step=int(ck["step"]),
               arm=ck["arm"], seed=int(ck["seed"]), tokenizer_sha256=ck["tokenizer_sha256"])
    if model.discrete:
        rec["osa_logp_true"] = osa["logp_true"]
    else:
        rec["osa_pred_std"] = osa["pred_std"].astype(np.float32)
        rec["gen_std"] = gen_rows.astype(np.float32)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--ckpt", default="best", choices=["best", "final"])
    ap.add_argument("--wells", default="pilot", choices=["pilot", "dev", "csv"])
    ap.add_argument("--csv", default=None, help="confirmatory wells file (same columns as train.csv)")
    ap.add_argument("--well", action="append", default=None, help="restrict to these wells")
    ap.add_argument("--n_real", type=int, default=vc.N_REAL)
    ap.add_argument("--outroot", default=str(vc.V4 / "gens"))
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--max_gen", type=int, default=0, help="SMOKE ONLY: cap generated positions")
    args = ap.parse_args()
    vc.check_protocol()
    if args.threads:
        torch.set_num_threads(args.threads)
    device = vm.pick_device()
    vm.set_determinism(GEN_SEED, device)

    split = vc.load_split()
    fit_df = vc.load_df(vc.FORCE_TRAIN_CSV)
    tk = vc.load_tokenizer()
    if args.wells == "csv":
        df = vc.load_df(Path(args.csv))
        wells = sorted(df.WELL.astype(str).unique())
        overlap = set(wells) & set(split["pool98"])
        if overlap:
            sys.exit(f"ABORT: {len(overlap)} wells of {args.csv} are pool wells: {sorted(overlap)[:5]}")
    else:
        df, wells = fit_df, list(split[args.wells])
    if args.well:
        wells = [w for w in wells if w in set(args.well)]
    data = vc.Data(split, df, tk, wells=wells, fit_df=fit_df)
    model, ck = load_run_model(args.run_dir, args.ckpt, device)
    if ck["tokenizer_sha256"] != tk.canonical_sha256():
        sys.exit("ABORT: run was trained with a different tokenizer")
    if model.use_depth_embed:
        data.ensure_athy(fit_df)
        if tuple(data.athy) != tuple(ck["athy"]) or data.depth_mean != ck["depth_mean"]:
            sys.exit("ABORT: depth features differ from the ones the run was trained with")
    elig = eligible_wells(data, wells)
    skipped = [w for w in wells if w not in elig]
    tag = args.ckpt + (f"_SMOKE_maxgen{args.max_gen}" if args.max_gen else "")
    out = Path(args.outroot) / Path(args.run_dir).name / tag / ("csv" if args.wells == "csv" else args.wells)
    out.mkdir(parents=True, exist_ok=True)
    print(f"=== generate {Path(args.run_dir).name} [{args.ckpt}, step {ck['step']}] on {device}: "
          f"{len(elig)} eligible wells, skipped {skipped} ===", flush=True)
    meta = dict(run=Path(args.run_dir).name, ckpt=args.ckpt, ckpt_step=int(ck["step"]), device=device,
                wells=elig, skipped_lt_2000_valid=skipped, n_real=args.n_real, gen_seed=GEN_SEED,
                max_gen=args.max_gen, torch=torch.__version__, threads=torch.get_num_threads(), per_well={})
    for w in elig:
        f = out / f"{safe(w)}.npz"
        if f.exists():
            print(f"  {w}: exists, skipping", flush=True)
            continue
        rec = generate_well(model, ck, data, w, args.n_real, device, max_gen=args.max_gen,
                            log=lambda m: print(m, flush=True))
        tmp = f.with_suffix(".tmp.npz")
        np.savez_compressed(tmp, **rec)
        tmp.replace(f)
        meta["per_well"][w] = dict(n_generated=rec["n_generated"], seconds_gen=rec["seconds_gen"],
                                   seconds_osa=rec["seconds_osa"], n_real=rec["n_real"])
        print(f"  {w}: {rec['n_generated']} positions x {rec['n_real']} in {rec['seconds_gen']:.0f}s, "
              f"one-step-ahead {rec['seconds_osa']:.0f}s", flush=True)
    prev = out / "meta.json"
    if prev.exists():
        old = json.loads(prev.read_text())
        old.get("per_well", {}).update(meta["per_well"])
        meta["per_well"] = old.get("per_well", meta["per_well"])
    vc.save_json(meta, prev)


if __name__ == "__main__":
    main()
