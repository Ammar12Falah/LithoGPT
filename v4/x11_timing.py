"""Timing for the run plan, on whatever device is present (CPU here, the A40 on the pod).

Measures: one training step (arms A, B2, C; dropout 0 and 0.1), one development-loss pass,
generation cost per position (5 realizations for A, 1 for C, full 512 context), and
one-step-ahead cost per position. Also counts the positions the study will generate.

  python -B x11_timing.py [--threads 12]      writes out/x11_timing_<device>.json
"""
import sys

sys.dont_write_bytecode = True

import argparse
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4_common as vc  # noqa: E402
import v4_model as vm  # noqa: E402
import t02_train as t2  # noqa: E402


def sync(device):
    if device.startswith("cuda"):
        torch.cuda.synchronize()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--n_gen", type=int, default=300)
    args = ap.parse_args()
    if args.threads:
        torch.set_num_threads(args.threads)
    device = vm.pick_device()
    vm.set_determinism(vc.SEED, device)
    d = vc.load_data(with_athy=True)
    res = dict(device=device, torch=torch.__version__, threads=torch.get_num_threads(),
               gpu=(torch.cuda.get_device_name(0) if device.startswith("cuda") else None), train_step_s={})

    # ---- one training step
    for arm in ("A", "B2", "C"):
        seqs, dfeats, targets = t2.build_inputs(arm, d, d.split["train"])
        for do in (0.0, 0.1):
            torch.manual_seed(vc.SEED)
            model = vm.LithoGPTv4(arm, dropout=do).to(device)
            opt = torch.optim.AdamW(model.parameters(), lr=vm.LR, weight_decay=0.01)
            lf = torch.nn.CrossEntropyLoss() if model.discrete else torch.nn.MSELoss()
            smp = vm.WindowSampler(seqs, vc.SEED, dfeats=dfeats, targets=targets)
            ts = []
            for i in range(7):
                xb, yb, db, _ = smp.next()
                xb, yb = xb.to(device), yb.to(device)
                db = db.to(device) if db is not None else None
                sync(device)
                t0 = time.time()
                out = model(xb, depth_feat=db)
                loss = lf(out.reshape(-1, vc.K), yb.reshape(-1)) if model.discrete else lf(out, yb)
                opt.zero_grad(); loss.backward(); opt.step()
                sync(device)
                ts.append(time.time() - t0)
            res["train_step_s"][f"{arm}_dropout{do:g}"] = float(np.median(ts[2:]))
            print(f"train step {arm} dropout {do:g}: {np.median(ts[2:]):.3f}s", flush=True)

    # ---- development loss pass (arm A)
    model = vm.LithoGPTv4("A").to(device)
    dv = [d.seq[w] for w in d.split["dev"]]
    t0 = time.time()
    vm.dev_loss(model, dv, device=device)
    sync(device)
    res["dev_loss_pass_s"] = time.time() - t0
    print(f"dev loss pass: {res['dev_loss_pass_s']:.1f}s", flush=True)

    # ---- generation and one-step-ahead, per position, full context
    w = d.split["pilot"][0]
    tok = d.seq[w]["tok"]
    P = vc.prime_len(tok.size)
    centers = d.tk.centers
    for arm, R in (("A", 5), ("A", 1), ("C", 1)):
        m = vm.LithoGPTv4(arm).to(device).eval()
        t0 = time.time()
        vm.generate(m, tok[:P + args.n_gen], P, R, vc.SEED, centers_std=centers, device=device)
        sync(device)
        res[f"gen_s_per_position_{arm}_R{R}"] = (time.time() - t0) / args.n_gen
        print(f"generate {arm} R={R}: {1000 * res[f'gen_s_per_position_{arm}_R{R}']:.1f} ms/position", flush=True)
    m = vm.LithoGPTv4("A").to(device).eval()
    pos = P + np.arange(1000)
    t0 = time.time()
    vm.one_step_ahead(m, tok, pos, device=device, batch=(128 if device.startswith("cuda") else 64))
    sync(device)
    res["osa_s_per_position"] = (time.time() - t0) / pos.size
    print(f"one step ahead: {1000 * res['osa_s_per_position']:.2f} ms/position", flush=True)

    # ---- positions the study generates
    def gen_positions(wells):
        out = {}
        for w in wells:
            L = d.seq[w]["tok"].size
            P = vc.prime_len(L)
            out[w] = int(np.sum(d.seq[w]["tok"][P:] != vc.BOUNDARY))
        return out
    pil = gen_positions(d.split["pilot"])
    pool = gen_positions([w for w in d.split["pool98"] if d.rows[w]["n_valid"] >= 2000])
    res["pilot_generated_positions"] = pil
    res["pilot_generated_positions_total"] = int(sum(pil.values()))
    res["pool_eligible_wells"] = len(pool)
    res["pool_mean_generated_positions_per_eligible_well"] = float(np.mean(list(pool.values())))
    res["pool_max_generated_positions_per_eligible_well"] = int(max(pool.values()))
    vc.save_json(res, vc.OUT / f"x11_timing_{device.split(':')[0]}.json")
    print(f"pilot generated positions: {res['pilot_generated_positions_total']:,}; pool eligible wells "
          f"{len(pool)}, mean {res['pool_mean_generated_positions_per_eligible_well']:.0f} per well", flush=True)


if __name__ == "__main__":
    main()
