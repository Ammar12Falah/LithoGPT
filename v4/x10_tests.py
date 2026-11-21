"""Tests for the v4 pipeline. Each test is first run with a planted error (it must FAIL),
then clean (it must PASS). A test that passes with its planted error is reported as broken.

  python -B x10_tests.py                    all tests
  python -B x10_tests.py --only bootstrap   one test
  python -B x10_tests.py --fast             skip the two slow tests (leakage, determinism)

Writes out/tests_<name>.json per test and prints a table.
"""
import sys

sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import os
import shutil
import time
import traceback
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4_common as vc  # noqa: E402
import v4_model as vm  # noqa: E402
import v4_scores as sc  # noqa: E402
import b04_baselines as bl  # noqa: E402
import g03_generate as g3  # noqa: E402
import s05_score as s5  # noqa: E402
import t02_train as t2  # noqa: E402

B = vc.BOUNDARY
TMP = vc.CACHE / "test_tmp"
SEED = vc.SEED


class Check(Exception):
    pass


def expect(cond, msg):
    if not cond:
        raise Check(msg)


_DATA = {}


def data():
    if "d" not in _DATA:
        _DATA["d"] = vc.load_data()
    return _DATA["d"]


def ngram_index():
    if "ng" not in _DATA:
        _DATA["ng"] = s5.build_ngram_index(data())
    return _DATA["ng"]


TESTS = []


def test(name, plants, slow=False):
    def deco(f):
        TESTS.append((name, f, plants, slow))
        return f
    return deco


def fresh_tmp(sub):
    p = TMP / sub
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True)
    return p


# ============================================================================ 1. self score
@test("self_score", plants=["off_by_one", "generated_kappa_ignores_boundaries"])
def t_self_score(plant=None):
    """A real well scored against itself: bias 0, W1 0, spread 1, structure score 0
    (also trend gap 0, copying gap 0, facies structure 0). Goes through the same
    file-based path as every generated well (s05_score.score_file)."""
    d = data()
    idx = ngram_index()
    tmp = fresh_tmp("self_score")
    pl = {"off_by_one": {"off_by_one": True},
          "generated_kappa_ignores_boundaries": {"ignore_segments": True}}.get(plant)
    details = {}
    for w in d.split["pilot"]:
        seq = d.seq[w]
        L = seq["tok"].size
        P = vc.prime_len(L)
        rec = dict(well=w, prime_n=P, L=L, gen_tok=seq["tok"][P:][None].astype(np.int16),
                   curves=d.curves_seq(w)[P:][None].astype(np.float32))
        f = tmp / f"{g3.safe(w)}.npz"
        np.savez_compressed(f, **rec)
        # the real side is float64 from the file; the self copy went through float32 like
        # every generated file, so compare against a float32 real copy
        real, m = s5.real_view(d, w, P, L)
        real["nphi"] = real["nphi"].astype(np.float32).astype(np.float64)
        gens = [dict(nphi=real["nphi"], tok=real["tok"], fac=real["fac"])]
        if pl:
            s = sc.score_well(real, gens, idx, plant=pl)
        else:
            _, s = s5.score_file(f, d, idx)
            s_fac = sc.score_well(real, gens, idx)
            s["facies_structure_true_labels_both_sides"] = s_fac["facies_structure"]
            s["structure_float32_real"] = s_fac["structure"]
            s["bias_abs_float32_real"] = s_fac["bias_abs"]
            s["w1_float32_real"] = s_fac["w1"]
        n_seg = int(np.unique(real["seg"]).size)
        details[w] = {k: s[k] for k in ("bias_abs", "bias_signed", "w1", "spread", "structure",
                                        "trend_gap", "copy10_gap", "copy20_gap", "copy50_gap") if k in s}
        details[w]["segments_in_scored_part"] = n_seg
        if not pl:
            details[w]["facies_structure"] = s["facies_structure_true_labels_both_sides"]
        tol = 1e-6       # float32 storage of NPHI (|x| < 1): rounding below 1e-7
        expect(abs(s["bias_abs"]) <= tol and abs(s["bias_signed"]) <= tol, f"{w}: bias {s['bias_signed']:.3g} != 0")
        expect(s["w1"] <= tol, f"{w}: W1 {s['w1']:.3g} != 0")
        expect(abs(s["spread"] - 1) <= tol, f"{w}: spread {s['spread']:.9f} != 1")
        expect(s["structure"] == 0.0, f"{w}: structure score {s['structure']:.3g} != 0")
        expect(abs(s["trend_gap"]) <= tol, f"{w}: trend gap {s['trend_gap']:.3g} != 0")
        for n in sc.NGRAM_NS:
            expect(s[f"copy{n}_gap"] == 0.0, f"{w}: copying gap n={n} {s[f'copy{n}_gap']} != 0")
        if not pl:
            expect(s["facies_structure_true_labels_both_sides"] == 0.0, f"{w}: facies structure != 0")
    return details


# ============================================================================ 2. decode units
@test("decode_real_units", plants=["decode_skips_power_of_ten", "decode_skips_inverse_scaler"])
def t_decode(plant=None):
    """Decoded curves are in real units, for arms A and C: decode the tokens of every pilot
    well with the generator's own decoder and compare with the real curves. RDEP must come
    back in ohm-m."""
    d = data()
    tk = d.tk
    saved_fms = vc.from_model_space
    saved_dec = vc.Tokenizer.decode_std
    if plant == "decode_skips_power_of_ten":
        vc.from_model_space = lambda x: np.array(x, dtype=np.float64, copy=True)
    if plant == "decode_skips_inverse_scaler":
        vc.Tokenizer.decode_std = lambda self, z: vc.from_model_space(np.asarray(z, dtype=np.float64))
    details = {}
    try:
        for w in d.split["pilot"]:
            seq = d.seq[w]
            m = seq["tok"] != B
            real = d.curves_seq(w)
            # Arm A: tokens -> centroids -> real units
            cA = g3.decode_generated(tk, seq["tok"][None])[0]
            expect(np.all(np.isnan(cA[~m])) and np.all(np.isfinite(cA[m])), f"{w}: NaN layout wrong")
            a, r = cA[m], real[m]
            expect(np.all(a[:, vc.RDEP] > 0), f"{w} A: decoded RDEP has values <= 0, not ohm-m")
            lr = np.abs(np.log10(a[:, vc.RDEP] / r[:, vc.RDEP]))
            ratio = np.median(a[:, vc.RDEP]) / np.median(r[:, vc.RDEP])
            mae = np.abs(a - r).mean(0)
            details[w] = dict(A_mae_GR=mae[0], A_mae_NPHI=mae[2], A_mae_RHOB=mae[3],
                              A_mean_abs_log10_RDEP_ratio=float(lr.mean()), A_median_RDEP_ratio=float(ratio),
                              real_median_RDEP_ohmm=float(np.median(r[:, vc.RDEP])),
                              decoded_median_RDEP_ohmm=float(np.median(a[:, vc.RDEP])))
            expect(0.67 <= ratio <= 1.5, f"{w} A: median RDEP ratio {ratio:.3f} (decoded/real) outside 0.67-1.5")
            expect(lr.mean() < 0.2, f"{w} A: mean |log10 RDEP ratio| {lr.mean():.3f} >= 0.2")
            expect(mae[2] < 0.05, f"{w} A: NPHI mean error {mae[2]:.4f} >= 0.05 v/v")
            expect(mae[0] < 10, f"{w} A: GR mean error {mae[0]:.2f} >= 10 API")
            expect(mae[3] < 0.08, f"{w} A: RHOB mean error {mae[3]:.4f} >= 0.08 g/cc")
            # Arm C: regression rows (standardized GR, log10 RDEP, NPHI, RHOB) -> real units.
            # A perfect regression output (the real well's own standardized rows) must decode
            # to the real curves, and its fed-back token must be the tokenizer's token.
            z = d.std_seq(w)
            cC = g3.decode_generated(tk, seq["tok"][None], z[None])[0]
            expect(np.all(np.isnan(cC[~m])), f"{w} C: boundary rows not NaN")
            err = np.abs(cC[m] - r) / np.maximum(np.abs(r), 1e-9)
            details[w]["C_max_rel_error"] = float(err.max())
            expect(np.all(cC[m][:, vc.RDEP] > 0), f"{w} C: decoded RDEP has values <= 0, not ohm-m")
            expect(err.max() < 1e-9, f"{w} C: decoded curves differ from the real curves (max rel err {err.max():.3g})")
            same = float(np.mean(tk.nearest(z[m]) == seq["tok"][m]))
            details[w]["C_feedback_token_equals_tokenizer"] = same
            expect(same == 1.0, f"{w} C: fed-back token differs from tokenizer token on {1 - same:.4%}")
    finally:
        vc.from_model_space = saved_fms
        vc.Tokenizer.decode_std = saved_dec
    return details


# ============================================================================ 3. boundaries
@test("no_boundary_crossing", plants=["windows_ignore_boundaries", "counts_cross_boundaries",
                                     "runs_ignore_boundaries", "lag_pairs_ignore_boundaries",
                                     "generation_context_crosses_boundaries"])
def t_boundaries(plant=None):
    """No training window, transition count, run or lag pair crosses a boundary token.
    Also: dev-loss chunks, n-grams and generation contexts stay inside one segment, and
    generated boundary positions are the real well's."""
    d = data()
    det = {}
    tr = [d.seq[w] for w in d.split["train"]]
    # --- training windows, all three arms
    for arm in ("A", "B2", "C"):
        if arm == "B2":
            d.ensure_athy(vc.load_df())
        seqs, dfeats, targets = t2.build_inputs(arm, d, d.split["train"])
        smp = vm.WindowSampler(seqs, SEED, dfeats=dfeats, targets=targets,
                               ignore_boundaries=(plant == "windows_ignore_boundaries"))
        bad, n, open_b = 0, 0, 0
        for _ in range(300 if arm == "A" else 60):
            xb, yb, db, meta = smp.next()
            for i, s in meta:
                seg = seqs[i]["seg"][s:s + vm.CONTEXT + 1]
                tok = seqs[i]["tok"][s:s + vm.CONTEXT + 1]
                n += 1
                if seg.min() != seg.max() or np.any(tok[1:] == B):
                    bad += 1
                open_b += int(tok[0] == B)
            if targets is not None:
                expect(torch.isfinite(yb).all(), f"{arm}: NaN target (a boundary) in a training window")
            if dfeats is not None:
                expect(db is not None and db.shape[-1] == vc.B2_DEPTH_FEAT_DIM, "B2 depth features missing")
        det[f"windows_{arm}"] = dict(n_windows=n, crossing=bad, opened_by_boundary=open_b)
        expect(bad == 0, f"{arm}: {bad} of {n} training windows cross a boundary")
    # --- dev chunks
    dv = [d.seq[w] for w in d.split["dev"]]
    badc = 0
    for wi, c, e in vm.dev_chunks(dv):
        seg, tok = dv[wi]["seg"][c:e + 1], dv[wi]["tok"][c:e + 1]
        badc += int(seg.min() != seg.max() or np.any(tok[1:] == B))
    det["dev_chunks_crossing"] = badc
    expect(badc == 0, f"{badc} dev-loss chunks cross a boundary")
    # --- transition counts: synthetic case where the crossing pairs are unique
    syn = dict(tok=np.array([1, 2, 3, B, 4, 5, 6]), seg=np.array([0, 0, 0, 1, 1, 1, 1]))
    pc = plant == "counts_cross_boundaries"
    ch = bl.Chain([syn], plant_cross_boundary=pc)
    expect(ch.counts[3, 4] == 0, "chain counts the pair (3, 4) that crosses the boundary")
    expect(ch.counts[B, 4] == 1 and ch.counts.sum() == 5, f"chain counts wrong: total {ch.counts.sum()}")
    tg = bl.Trigram([syn], plant_cross_boundary=pc)
    expect(tg.c2[3].get(4, 0) == 0 and tg.c3[(2, 3)].get(4, 0) == 0 and (3, B) not in tg.c3,
           "trigram counts a context that crosses the boundary")
    expect(tg.c3[(B, 4)].get(5, 0) == 1, "trigram misses the count opened by the boundary")
    # --- transition counts on the real training wells, against a plain row-by-row recount
    chain = bl.Chain(tr, plant_cross_boundary=pc)
    ref = np.zeros((vc.K + 1, vc.K))
    for w in d.split["train"]:
        r = d.rows[w]
        t, sg = r["tok"], r["seg"]
        same = sg[1:] == sg[:-1]
        np.add.at(ref, (t[:-1][same], t[1:][same]), 1.0)
        starts = np.flatnonzero(~same) + 1
        np.add.at(ref, (np.full(starts.size, B), t[starts]), 1.0)
    det["chain_counts_equal_row_recount"] = bool(np.array_equal(chain.counts, ref))
    expect(np.array_equal(chain.counts, ref), "chain counts on training wells differ from a within-segment recount")
    # --- runs
    rl_seg = np.zeros(4, dtype=int) if plant == "runs_ignore_boundaries" else np.array([0, 0, 1, 1])
    rl = sc.run_lengths(np.array([7, 7, 7, 7]), rl_seg)
    expect(rl.tolist() == [2, 2], f"run lengths {rl.tolist()} != [2, 2]: a run crosses a boundary")
    # --- lag pairs: synthetic and a real pilot well
    ign = plant == "lag_pairs_ignore_boundaries"
    k = sc.kappa_lags(np.array([1, 1, 1, 2, 2, 2]), np.array([0, 0, 0, 1, 1, 1]), lags=(1, 3), ignore_segments=ign)
    expect(abs(k[1] - 1.0) < 1e-12 and np.isnan(k[3]), f"synthetic kappa {k} != {{1: 1.0, 3: nan}}")
    w = max(d.split["pilot"], key=lambda x: int((d.seq[x]["tok"] == B).sum()))
    seq = d.seq[w]
    m = seq["tok"] != B
    a, s = seq["tok"][m], seq["seg"][m]
    kk = sc.kappa_lags(a, s, ignore_segments=ign)
    _, cnt = np.unique(a, return_counts=True)
    pe = float(np.sum((cnt / cnt.sum()) ** 2))
    maxdiff = 0.0
    for l in sc.LAGS:
        hits = tot = 0
        for i in range(a.size - l):
            if s[i] == s[i + l]:
                tot += 1
                hits += int(a[i] == a[i + l])
        ref_k = (hits / tot - pe) / (1 - pe)
        maxdiff = max(maxdiff, abs(ref_k - kk[l]))
    det["kappa_vs_pair_loop_max_diff"] = maxdiff
    det["kappa_well"] = w
    expect(maxdiff < 1e-12, f"{w}: kappa differs from a within-segment pair loop by {maxdiff:.3g}")
    # --- n-grams
    ng = sc.ngrams(np.array([1, 2, 3, 4]), np.array([0, 0, 1, 1]), 2)
    expect(len(ng) == 2, f"{len(ng)} 2-grams found, expected 2 (one would cross the boundary)")
    # --- generation contexts, with a stub model that records every context it is given
    saved = vm.context_start
    if plant == "generation_context_crosses_boundaries":
        vm.context_start = lambda tok, context=vm.CONTEXT: np.maximum(0, np.arange(tok.size) - context)

    class Stub(torch.nn.Module):
        discrete, use_depth_embed, context = True, False, vm.CONTEXT

        def __init__(self):
            super().__init__()
            self.seen = []

        def forward(self, x, d=None, last_only=False):
            self.seen.append(x[0].numpy().copy())
            return torch.zeros(x.shape[0], 1, vc.K)
    try:
        lens = [700, 300, 900]
        tok = np.concatenate([np.r_[([B] if j else []), np.random.default_rng(j).integers(0, vc.K, n)]
                              for j, n in enumerate(lens)]).astype(np.int64)
        stub = Stub()
        P = vc.prime_len(tok.size)
        gtok, _ = vm.generate(stub, tok, P, 2, SEED)
        crossing = sum(int(np.any(x[1:] == B)) for x in stub.seen)
        too_long = sum(int(x.size > vm.CONTEXT) for x in stub.seen)
        det["generation"] = dict(n_contexts=len(stub.seen), crossing=crossing, longer_than_512=too_long,
                                 boundary_positions_copied=bool(np.array_equal(gtok[:, tok[P:] == B] == B,
                                                                               np.ones_like(gtok[:, tok[P:] == B], bool))))
        expect(crossing == 0, f"{crossing} generation contexts reach back across a boundary")
        expect(too_long == 0, "a generation context is longer than 512")
        expect(np.all(gtok[:, tok[P:] == B] == B) and not np.any(gtok[:, tok[P:] != B] == B),
               "generated boundary positions differ from the real well's")
    finally:
        vm.context_start = saved
    return det


# ============================================================================ 4. leakage
def _perturb(df, wells):
    df = df.copy()
    m = df.WELL.isin(wells).to_numpy()
    df.loc[m, "GR"] = df.loc[m, "GR"] + 37.0
    df.loc[m, "RDEP"] = df.loc[m, "RDEP"] * 5.0
    df.loc[m, "NPHI"] = df.loc[m, "NPHI"] * 0.7 + 0.05
    df.loc[m, "RHOB"] = df.loc[m, "RHOB"] - 0.2
    df.loc[m, "DEPTH_MD"] = df.loc[m, "DEPTH_MD"] + 333.0
    df.loc[m, vc.LABEL_COL] = 99000
    idx = np.flatnonzero(m)
    df.loc[df.index[idx[::50]], "NPHI"] = np.nan          # new removed intervals
    return df


def _h(*arrays):
    return vc.sha256_arrays(*[np.asarray(a) for a in arrays])


def _fingerprint(df, plant, tmpdir):
    split = vc.load_split()
    vc.FIT_LOG.clear()
    tok_wells = split["train"] + (split["dev"] if plant == "tokenizer_fitted_with_dev_wells" else [])
    tk, _ = vc.fit_tokenizer(tok_wells, df)
    d = vc.Data(split, df, tk)
    athy = vc.train_only_athy(split["train"], df)
    fp = dict(tokenizer=tk.canonical_sha256(), depth_standardizer=[d.depth_mean, d.depth_std],
              facies_map=_h(d.tok2fac, d.fac_classes), athy=list(athy))
    fp["constant"] = _h(bl.build("constant", d).curve)
    if plant == "chain_counts_include_dev_wells":
        vc.record_fit("chain", split["train"] + split["dev"])
        ch = bl.Chain([d.seq[w] for w in split["train"] + split["dev"]])
    else:
        ch = bl.build("chain", d)
    fp["chain"] = _h(ch.counts)
    tg = bl.build("trigram", d)
    fp["trigram"] = hashlib.sha256(json.dumps(sorted((list(k), sorted(v.items())) for k, v in tg.c3.items())).encode()).hexdigest()
    blk = bl.build("block", d)
    fp["blocks"] = _h(blk.wi, blk.st, blk.dep, blk.room)
    ng = s5.build_ngram_index(d)
    fp["ngrams"] = {n: hashlib.sha256(b"".join(sorted(ng.sets[n]))).hexdigest() for n in sc.NGRAM_NS}
    s = t2.train("A", SEED, 0.0, 0.01, tmpdir, n_steps=4, ckpt_every=2, data=d, keep_step_ckpts=False,
                 device="cpu", log=lambda m: None)
    st = torch.load(Path(tmpdir) / t2.run_name("A", SEED, 0.0, 0.01) / "final.pt", weights_only=False)["model_state"]
    fp["weights_after_4_steps"] = _h(*[v.numpy() for v in st.values()])
    fp["dev_loss_after_4_steps_differs_is_allowed"] = s["final_dev_loss"]
    used = sorted({w for _, ws in vc.FIT_LOG for w in ws})
    return fp, used


@test("nothing_fitted_on_dev_or_pilot", plants=["tokenizer_fitted_with_dev_wells", "chain_counts_include_dev_wells"],
      slow=True)
def t_leakage(plant=None):
    """Nothing is fitted on development or pilot wells except the tuned settings. Every fitted
    object (tokenizer, depth standardizer, facies map, Athy constant, constant predictor, chain
    and trigram counts, block table, n-gram index, and the transformer weights after 4 steps)
    is fitted twice: on the real file and on a copy where every development and pilot well is
    changed (curves shifted, depth moved, labels replaced, rows removed). All must be identical,
    and the fit log must name training wells only."""
    split = vc.load_split()
    df = vc.load_df()
    dfp = _perturb(df, split["dev"] + split["pilot"])
    fp1, used1 = _fingerprint(df, plant, fresh_tmp("leak1"))
    fp2, used2 = _fingerprint(dfp, plant, fresh_tmp("leak2"))
    outside = sorted((set(used1) | set(used2)) - set(split["train"]))
    differ = [k for k in fp1 if k != "dev_loss_after_4_steps_differs_is_allowed" and fp1[k] != fp2[k]]
    det = dict(objects_compared=[k for k in fp1 if k != "dev_loss_after_4_steps_differs_is_allowed"],
               differ=differ, wells_in_fit_log_outside_training=outside,
               dev_loss_original=fp1["dev_loss_after_4_steps_differs_is_allowed"],
               dev_loss_perturbed=fp2["dev_loss_after_4_steps_differs_is_allowed"])
    expect(not outside and not differ,
           f"fit log names {len(outside)} non-training wells {outside[:3]}; "
           f"fitted objects that change when dev/pilot wells change: {differ}")
    return det


# ============================================================================ 5. determinism and resume
def _weights(path):
    st = torch.load(path, map_location="cpu", weights_only=False)["model_state"]
    return {k: v.clone() for k, v in st.items()}


def _same(a, b):
    return all(torch.equal(a[k], b[k]) for k in a) and a.keys() == b.keys()


@test("same_seed_same_weights", plants=["model_init_not_seeded", "resume_without_rng_restore"], slow=True)
def t_determinism(plant=None):
    """The same seed twice gives the same weights after 50 CPU steps, for arms A, B2 and C,
    with dropout 0.1 so the dropout random stream is exercised. Also: a run stopped at step 30
    and resumed gives the same weights at step 50 as an uninterrupted run."""
    d = data()
    det = {}
    arms = ["A"] if plant else ["A", "B2", "C"]
    dev = os.environ.get("V4_TEST_DEVICE", "cpu")       # the pod reruns this test on cuda
    det["device"] = dev
    kw = dict(n_steps=50, ckpt_every=10, data=d, keep_step_ckpts=False, device=dev, log=lambda m: None)
    if plant != "resume_without_rng_restore":
        for arm in arms:
            p1, p2 = fresh_tmp(f"det1_{arm}"), fresh_tmp(f"det2_{arm}")
            t2.train(arm, SEED, 0.1, 0.01, p1, **kw)
            t2.train(arm, SEED, 0.1, 0.01, p2, plant_unseeded=(plant == "model_init_not_seeded"), **kw)
            n = t2.run_name(arm, SEED, 0.1, 0.01)
            same = _same(_weights(p1 / n / "final.pt"), _weights(p2 / n / "final.pt"))
            det[f"{arm}_identical_after_50_steps"] = same
            expect(same, f"arm {arm}: two runs with seed {SEED} give different weights after 50 steps")
    if plant in (None, "resume_without_rng_restore"):
        n = t2.run_name("A", SEED, 0.1, 0.01)
        ref = TMP / "det1_A" / n / "final.pt"
        if not ref.exists():
            p1 = fresh_tmp("det1_A")
            t2.train("A", SEED, 0.1, 0.01, p1, **kw)
        p3 = fresh_tmp("resume_A")
        t2.train("A", SEED, 0.1, 0.01, p3, stop_after=30, **kw)
        expect(not (p3 / n / "final.pt").exists(), "crash simulation did not stop the run")
        s = t2.train("A", SEED, 0.1, 0.01, p3, plant_no_rng_restore=(plant == "resume_without_rng_restore"), **kw)
        same = _same(_weights(ref), _weights(p3 / n / "final.pt"))
        det["resume_at_30_identical_at_50"] = same
        det["resumed_flag"] = s.get("resumed")
        expect(s.get("resumed"), "second call did not resume")
        expect(same, "resumed run differs from the uninterrupted run")
    return det


# ============================================================================ 6. bootstrap
def _exact_quantiles(values, probs, q=(0.025, 0.975)):
    order = np.argsort(values)
    v, p = np.asarray(values)[order], np.asarray(probs)[order]
    c = np.cumsum(p)
    return tuple(float(v[np.searchsorted(c, qq - 1e-12)]) for qq in q)


@test("bootstrap_known_interval", plants=["resamples_wells_only", "wrong_percentiles", "pairs_seeds_by_position"])
def t_bootstrap(plant=None):
    """The wells-and-seeds bootstrap returns a known interval on made-up data. With 0/1
    well effects the bootstrap mean is Binomial(W, 1/2)/W; with 0/1 seed effects it is
    Binomial(S, 1/2)/S; with both it is their sum, whose exact quantiles are computed by
    enumeration. The 10,000-draw percentile interval must match within one lattice step."""
    from scipy.stats import binom
    kw = {}
    if plant == "resamples_wells_only":
        kw["plant_wells_only"] = True
    if plant == "wrong_percentiles":
        kw["plant_percentiles"] = (5.0, 95.0)
    det = {}
    W, S = 100, 40
    a = np.r_[np.zeros(W // 2), np.ones(W // 2)]
    b = np.r_[np.zeros(S // 2), np.ones(S // 2)]
    cases = {
        "wells_only": (np.repeat(a[:, None], S, 1), np.arange(W + 1) / W, binom.pmf(np.arange(W + 1), W, 0.5), 1 / W),
        "seeds_only": (np.repeat(b[None], W, 0), np.arange(S + 1) / S, binom.pmf(np.arange(S + 1), S, 0.5), 1 / S),
    }
    x, y = np.meshgrid(np.arange(W + 1), np.arange(S + 1), indexing="ij")
    vals = (x / W + y / S).ravel()
    probs = (binom.pmf(x, W, 0.5) * binom.pmf(y, S, 0.5)).ravel()
    cases["wells_and_seeds"] = (a[:, None] + b[None], vals, probs, 1 / S)
    for name, (M, v, p, step) in cases.items():
        lo_ex, hi_ex = _exact_quantiles(v, p)
        r = sc.bootstrap_wells_seeds(M, **kw)
        det[name] = dict(exact=[lo_ex, hi_ex], bootstrap=[r["lo"], r["hi"]], estimate=r["estimate"],
                         mean=float(M.mean()), tolerance=step + 1e-9)
        expect(abs(r["estimate"] - M.mean()) < 1e-12, f"{name}: estimate is not the mean")
        expect(abs(r["lo"] - lo_ex) <= step + 1e-9 and abs(r["hi"] - hi_ex) <= step + 1e-9,
               f"{name}: interval {r['lo']:.4f} to {r['hi']:.4f}, exact {lo_ex:.4f} to {hi_ex:.4f}")
    c = sc.bootstrap_wells_seeds(np.full((7, 5), 0.3), **kw)
    expect(abs(c["lo"] - 0.3) < 1e-12 and abs(c["hi"] - 0.3) < 1e-12, "constant data must give [0.3, 0.3]")
    # pairing: Arm A has seeds 1, 2, 3; the chain has 1 and 3 (seed 2 missing). The pairs must be
    # (1, 1) and (3, 3), never by list position.
    wl = ["w1", "w2"]
    A = {1: {w: {"bias_abs": 1.0} for w in wl}, 2: {w: {"bias_abs": 5.0} for w in wl}, 3: {w: {"bias_abs": 3.0} for w in wl}}
    C = {1: {w: {"bias_abs": 0.5} for w in wl}, 3: {w: {"bias_abs": 2.0} for w in wl}}
    mc = sc.main_comparisons({"A": A, "chain": C}, wl, n_boot=200,
                             plant_pair_by_position=(plant == "pairs_seeds_by_position"))
    got = mc["A_minus_chain_abs_bias"]["estimate"]
    det["pairing_check"] = dict(estimate=got, expected=0.75)
    expect(abs(got - 0.75) < 1e-12, f"seed pairing wrong: estimate {got}, expected 0.75 (pairs (1,1) and (3,3))")
    det["n_boot"] = sc.N_BOOT
    return det


# ============================================================================ 7. confirmatory file builder
def _c06_fake_files(tmp, plant):
    """Fake open and blind test files made from four pilot wells under new names: the open
    features without labels plus a separate label file, the blind file with labels."""
    import pandas as pd
    pil = vc.load_split()["pilot"][:4]
    df = pd.read_csv(vc.FORCE_TRAIN_CSV, sep=";", dtype=str, keep_default_na=False, na_filter=False)
    df = df[df.WELL.isin(pil)]
    names = {pil[0]: "FAKE O-1", pil[1]: "FAKE O-2", pil[2]: "FAKE B-1", pil[3]: "FAKE B-2"}
    if plant == "pool_well_present":
        names[pil[3]] = pil[3]                      # one blind well keeps its pool name
    df = df.assign(WELL=df.WELL.map(names))
    op = df[df.WELL.str.startswith("FAKE O")]
    bl_ = df[~df.WELL.str.startswith("FAKE O")]
    feat = op.drop(columns=[vc.LABEL_COL, "FORCE_2020_LITHOFACIES_CONFIDENCE"], errors="ignore")
    targ = op[["WELL", "DEPTH_MD", vc.LABEL_COL]]
    if plant == "labels_misaligned":
        targ = pd.concat([targ.iloc[1:], targ.iloc[:1]])        # label rows shifted by one
    if plant == "missing_column":
        bl_ = bl_.drop(columns=["NPHI"])
    f = dict(open_features=tmp / "open_features.csv", open_target=tmp / "open_target.csv", blind=tmp / "blind.csv")
    feat.to_csv(f["open_features"], sep="," if plant == "wrong_separator" else ";", index=False)
    targ.to_csv(f["open_target"], sep=";", index=False)
    bl_.to_csv(f["blind"], sep=";", index=False)
    return f, op, bl_, names


@test("c06_confirmatory_file", plants=["wrong_separator", "missing_column", "pool_well_present", "labels_misaligned"])
def t_c06(plant=None):
    """c06_prepare_confirmatory.py build, on fake open and blind files made from pilot wells under
    new names: the CSV holds the values as exact text, the separate labels are joined to the right
    rows, the counts match the pipeline's own, and the printed output holds no data value. Planted
    errors in the input files must be refused."""
    import subprocess
    import pandas as pd
    tmp = fresh_tmp("c06")
    files, op, bl_, names = _c06_fake_files(tmp, plant)
    out_csv, man_path = tmp / "confirmatory_wells.csv", tmp / "manifest.json"
    cmd = [sys.executable, "-B", str(vc.V4 / "c06_prepare_confirmatory.py"), "build", "--any_count",
           "--out_csv", str(out_csv), "--manifest", str(man_path)] + \
          [x for k, v in files.items() for x in (f"--{k}", str(v))]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    text = r.stdout + r.stderr
    expect(r.returncode == 0, f"c06 refused or failed (exit {r.returncode}): {text.strip().splitlines()[-1:]}")
    # 1. values are exact text; labels sit on the right rows
    got = pd.read_csv(out_csv, sep=";", dtype=str, keep_default_na=False, na_filter=False)
    want = pd.concat([op, bl_])[["WELL", "DEPTH_MD"] + vc.FEATURES + [vc.LABEL_COL]].reset_index(drop=True)
    expect(list(got.columns) == list(want.columns), f"columns {list(got.columns)}")
    expect(got.equals(want), "the CSV differs from the text of the raw files (values or labels)")
    # 2. counts equal the pipeline's own on the original wells
    man = json.loads(man_path.read_text())
    tr = vc.load_df()
    for orig, fake in names.items():
        rr = vc.well_rows(tr, orig)
        m = man["wells"][fake]
        expect(m["n_rows"] == rr["n_file_rows"] and m["n_valid"] == rr["n_valid"],
               f"{fake}: counts {m['n_rows']}/{m['n_valid']} != {rr['n_file_rows']}/{rr['n_valid']}")
        expect(m["eligible"] == (rr["n_valid"] >= 2000), f"{fake}: eligibility wrong")
    expect(man["output_csv"]["sha256"] == vc.sha256_file(out_csv), "manifest SHA-256 of the CSV is wrong")
    # 3. nothing printed is a data value: no curve or label text of these wells appears in the output
    vals = set()
    for c in vc.FEATURES + [vc.LABEL_COL]:
        vals |= {v for v in want[c].unique().tolist() if len(v) >= 4 and "." in v}
    leaked = [v for v in list(vals)[:5000] if v in text]
    expect(not leaked, f"the output prints {len(leaked)} data value(s)")
    return dict(n_rows=len(got), wells=list(man["wells"]), n_eligible=man["n_eligible"],
                values_checked_not_printed=min(len(vals), 5000), label_join=man["label_join"])


# ============================================================================ runner
def run_one(name, f, plants):
    rec = dict(name=name, doc=(f.__doc__ or "").strip(), plants={}, clean=None)
    for p in plants:
        t0 = time.time()
        try:
            f(plant=p)
            rec["plants"][p] = dict(result="PASS (BROKEN: the planted error was not caught)", seconds=time.time() - t0)
        except Check as e:
            rec["plants"][p] = dict(result="FAIL", message=str(e), seconds=time.time() - t0)
        except Exception as e:  # noqa: BLE001
            rec["plants"][p] = dict(result="ERROR", message=f"{type(e).__name__}: {e}",
                                    trace=traceback.format_exc()[-1500:], seconds=time.time() - t0)
        print(f"  [{name}] planted '{p}': {rec['plants'][p]['result']}"
              + (f" -- {rec['plants'][p].get('message', '')}" if rec["plants"][p].get("message") else ""), flush=True)
    t0 = time.time()
    try:
        det = f(plant=None)
        rec["clean"] = dict(result="PASS", details=det, seconds=time.time() - t0)
    except Check as e:
        rec["clean"] = dict(result="FAIL", message=str(e), seconds=time.time() - t0)
    except Exception as e:  # noqa: BLE001
        rec["clean"] = dict(result="ERROR", message=f"{type(e).__name__}: {e}", trace=traceback.format_exc()[-1500:],
                            seconds=time.time() - t0)
    print(f"  [{name}] clean: {rec['clean']['result']}"
          + (f" -- {rec['clean'].get('message', '')}" if rec["clean"].get("message") else ""), flush=True)
    rec["ok"] = rec["clean"]["result"] == "PASS" and all(v["result"] == "FAIL" for v in rec["plants"].values())
    vc.save_json(rec, vc.OUT / f"tests_{name}.json")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", default=None)
    ap.add_argument("--fast", action="store_true")
    args = ap.parse_args()
    vc.check_protocol()
    torch.set_num_threads(12)
    torch.use_deterministic_algorithms(True)
    for name, f, plants, slow in TESTS:
        if args.only and name not in args.only:
            continue
        if args.fast and slow:
            continue
        print(f"=== {name} ===", flush=True)
        r = run_one(name, f, plants)
        print(f"  => {'OK' if r['ok'] else 'NOT OK'}", flush=True)


if __name__ == "__main__":
    main()
