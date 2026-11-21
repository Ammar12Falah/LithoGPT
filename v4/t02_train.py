"""Step 2, training for arms A, B2 and C (protocol sections 5 and 6).

Adapted from results_new/scripts/11_train_model.py and paper_atce/multiseed/ms_run.py.
  - dropout and weight decay options (section 6 grid: dropout 0, 0.1, 0.2; weight decay 0.01, 0.1)
  - full seeding (Python, NumPy, torch CPU and CUDA, deterministic kernels)
  - every 100 steps: development loss, a weights checkpoint, and a resume checkpoint
    holding the optimizer, the batch sampler state and every RNG state
  - resume after a crash gives the same weights as an uninterrupted run (tested)
  - best.pt is the checkpoint with the lowest development loss (section 6)

  python -B t02_train.py --arm A --seed 20260715 --dropout 0.1 --wd 0.01 --outdir runs
  python -B t02_train.py ... --n_steps 300                       (smoke test)
  python -B t02_train.py ... --stop_after 30 --ckpt_every 10      (crash simulation, tests only)
"""
import sys

sys.dont_write_bytecode = True

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4_common as vc  # noqa: E402
import v4_model as vm  # noqa: E402

N_STEPS = 3000
CKPT_EVERY = 100


def run_name(arm, seed, dropout, wd):
    return f"{arm}_seed{seed}_do{dropout:g}_wd{wd:g}"


def build_inputs(arm, data, wells):
    seqs = [data.seq[w] for w in wells]
    dfeats = [data.dfeat_b2(w) for w in wells] if arm == "B2" else None
    targets = [data.std_seq(w) for w in wells] if arm == "C" else None
    return seqs, dfeats, targets


def train(arm, seed, dropout, wd, outdir, n_steps=N_STEPS, ckpt_every=CKPT_EVERY, threads=None,
          device=None, stop_after=None, data=None, keep_step_ckpts=True, log=print,
          plant_unseeded=False, plant_no_rng_restore=False):
    """Train one (arm, seed, dropout, wd) run. Returns the run summary dict.
    plant_* flags exist only so the tests can show they catch the error."""
    device = device or vm.pick_device()
    if threads:
        torch.set_num_threads(threads)
    out = Path(outdir) / run_name(arm, seed, dropout, wd)
    (out / "ckpt").mkdir(parents=True, exist_ok=True)
    summary_path = out / "run.json"
    if summary_path.exists():
        s = json.loads(summary_path.read_text())
        if s.get("n_steps") == n_steps and s.get("complete"):
            log(f"SKIP {out.name}: complete")
            return s

    t_all = time.time()
    if data is None:
        data = vc.load_data(with_athy=(arm == "B2"))
    elif arm == "B2":
        data.ensure_athy(vc.load_df())
    split = data.split
    tr_seqs, tr_dfeats, tr_targets = build_inputs(arm, data, split["train"])
    dv_seqs, dv_dfeats, dv_targets = build_inputs(arm, data, split["dev"])

    vm.set_determinism(seed, device)
    if plant_unseeded:                      # planted error for the determinism test
        torch.manual_seed(int(time.time_ns() % (2 ** 31)))
    model = vm.LithoGPTv4(arm, dropout=dropout).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=vm.LR, weight_decay=wd)
    loss_fn = nn.CrossEntropyLoss() if model.discrete else nn.MSELoss()
    sampler = vm.WindowSampler(tr_seqs, seed, dfeats=tr_dfeats, targets=tr_targets)

    resume = out / "resume.pt"
    step0, losses, dev_hist, step_dt, resumed = 0, [], [], [], False
    if resume.exists():
        st = torch.load(resume, map_location=device, weights_only=False)
        model.load_state_dict(st["model_state"])
        opt.load_state_dict(st["opt_state"])
        sampler.set_state(st["sampler_state"])
        if not plant_no_rng_restore:
            # map_location=device puts every saved tensor on the device, RNG states included;
            # the setters take CPU ByteTensors (found on the pod 2026-11-19: TypeError on CUDA)
            torch.set_rng_state(st["torch_rng"].cpu())
            if device.startswith("cuda") and st.get("cuda_rng") is not None:
                torch.cuda.set_rng_state_all([s.cpu() for s in st["cuda_rng"]])
            np.random.set_state(st["numpy_rng"])
        step0, losses, dev_hist = int(st["step"]), list(st["losses"]), list(st["dev_hist"])
        resumed = True
        log(f"RESUME {out.name} at step {step0}")

    def save_resume(step):
        tmp = resume.with_suffix(".pt.tmp")
        torch.save(dict(model_state=model.state_dict(), opt_state=opt.state_dict(),
                        sampler_state=sampler.get_state(), torch_rng=torch.get_rng_state(),
                        cuda_rng=(torch.cuda.get_rng_state_all() if device.startswith("cuda") else None),
                        numpy_rng=np.random.get_state(), step=step, losses=losses, dev_hist=dev_hist,
                        arm=arm, seed=seed, dropout=dropout, wd=wd), tmp)
        tmp.replace(resume)

    def save_weights(path, step, dev):
        tmp = path.with_suffix(".pt.tmp")
        torch.save(dict(model_state=model.state_dict(), step=step, dev_loss=dev, arm=arm, seed=seed,
                        dropout=dropout, wd=wd, tokenizer_sha256=data.tk.canonical_sha256(),
                        athy=(data.athy if arm == "B2" else None),
                        depth_mean=data.depth_mean, depth_std=data.depth_std), tmp)
        tmp.replace(path)

    model.train()
    t0 = time.time()
    for step in range(step0, n_steps):
        ts = time.time()
        xb, yb, db, _ = sampler.next()
        xb, yb = xb.to(device), yb.to(device)
        db = db.to(device) if db is not None else None
        out_ = model(xb, depth_feat=db)
        loss = loss_fn(out_.reshape(-1, vc.K), yb.reshape(-1)) if model.discrete else loss_fn(out_, yb)
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
        if device.startswith("cuda"):
            torch.cuda.synchronize()
        step_dt.append(time.time() - ts)
        done = step + 1
        if done % ckpt_every == 0 or done == n_steps:
            dl, _ = vm.dev_loss(model, dv_seqs, dv_dfeats, dv_targets, device=device)
            dev_hist.append(dict(step=done, dev_loss=dl, train_loss_last100=float(np.mean(losses[-100:]))))
            if keep_step_ckpts:
                save_weights(out / "ckpt" / f"step_{done:05d}.pt", done, dl)
            best = min(dev_hist, key=lambda r: (r["dev_loss"], r["step"]))
            if best["step"] == done:
                save_weights(out / "best.pt", done, dl)
            if done == n_steps:
                save_weights(out / "final.pt", done, dl)
            save_resume(done)
            log(f"  [{out.name}] step {done}/{n_steps} train {np.mean(losses[-100:]):.4f} dev {dl:.4f} "
                f"median_step {np.median(step_dt):.3f}s elapsed {time.time() - t0:.0f}s")
        if stop_after is not None and done >= stop_after:
            log(f"  [{out.name}] stop_after {stop_after}: simulated crash")
            return dict(stopped_at=done)

    best = min(dev_hist, key=lambda r: (r["dev_loss"], r["step"]))
    summary = dict(run=out.name, arm=arm, seed=seed, dropout=dropout, wd=wd, n_steps=n_steps,
                   ckpt_every=ckpt_every, device=device, torch=torch.__version__,
                   threads=torch.get_num_threads(), n_params=model.n_params(),
                   best_step=best["step"], best_dev_loss=best["dev_loss"],
                   final_dev_loss=dev_hist[-1]["dev_loss"], dev_hist=dev_hist,
                   median_step_s=(float(np.median(step_dt)) if step_dt else None),
                   train_s=time.time() - t0, total_s=time.time() - t_all, resumed=resumed,
                   tokenizer_sha256=data.tk.canonical_sha256(), complete=True)
    vc.save_json(summary, summary_path)
    log(f"DONE {out.name}: best step {best['step']} dev {best['dev_loss']:.4f}")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=vm.ARMS)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--dropout", type=float, required=True)
    ap.add_argument("--wd", type=float, required=True)
    ap.add_argument("--outdir", default=str(vc.V4 / "runs"))
    ap.add_argument("--n_steps", type=int, default=N_STEPS)
    ap.add_argument("--ckpt_every", type=int, default=CKPT_EVERY)
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--stop_after", type=int, default=None)
    args = ap.parse_args()
    vc.check_protocol()
    train(args.arm, args.seed, args.dropout, args.wd, args.outdir, n_steps=args.n_steps,
          ckpt_every=args.ckpt_every, threads=args.threads, stop_after=args.stop_after,
          log=lambda m: print(m, flush=True))


if __name__ == "__main__":
    main()
