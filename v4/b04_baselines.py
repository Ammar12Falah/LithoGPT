"""Step 4, baselines (protocol sections 6 and 7).

  constant      the equal-weight mean of each curve over the 80 training wells
                (01_constant_baseline.py convention; RDEP averaged in log10)
  chain         first-order chain, Jelinek-Mercer mix of bigram and unigram
                (07_markov_interpolated.py / check3 tuned_chain), interpolation weight tuned
  trigram       interpolated absolute discounting, trigram -> bigram -> unigram
                (a32_higher_order_chain.py / check3 trigram_model), discount tuned
  block         real intervals of the training wells, block length tuned
  depthblock    the same, drawn from within 100 m of the target depth, widening to 250 m,
                then any depth; the block length tuned for 'block' is used (section 4 allows
                no other fitted setting)

Boundary handling (section 4): the boundary token is a start state. Counts from the
boundary to the first token of the next segment are kept; no count runs from one
segment into the next. Blocks lie inside one segment. In generation boundary
positions are copied from the real well and the state restarts at the boundary.

Tuning (section 6) is on development wells only, by the structure score of section 8,
with sampling seed 20260715 and 5 realizations. Scored runs use 12 sampling seeds
(20260715..20260726, paired by order with the training seeds), 5 realizations each.

  python -B b04_baselines.py tune                      writes out/b04_tuning.json
  python -B b04_baselines.py run --wells dev pilot      generates with the tuned settings
  python -B b04_baselines.py run --csv <file>           confirmatory wells

Side baselines (the author's ruling on Q18, CLARIFICATIONS.md of protocol/confirmatory-test):
  chain_nll     the chain with interpolation weight 0.02
  trigram_nll   the trigram with discount 0.75
These are the settings development likelihood picks (out/b04_tuning.json, dev NLL at the scored
positions; the run checks this). They run wherever the other baselines run and are reported as a
side result. They are not part of the four main comparisons.
"""
import sys

sys.dont_write_bytecode = True

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4_common as vc  # noqa: E402
import v4_scores as sc  # noqa: E402

K, B = vc.K, vc.BOUNDARY
LAMBDA_GRID = [0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005]      # 07_markov_interpolated.py
DISCOUNT_GRID = [0.1, 0.25, 0.5, 0.75, 0.9]                  # includes the pilot's 0.75
BLOCK_GRID = [8, 16, 32, 64, 128, 256, 512]                  # section 6
SAMPLING_SEEDS = list(range(20260715, 20260727))             # section 7
TUNE_SEED = SAMPLING_SEEDS[0]
DEPTH_WINDOWS_M = (100.0, 250.0)
MAIN_NAMES = ("constant", "chain", "trigram", "block", "depthblock")
SIDE = {"chain_nll": ("chain", 0.02), "trigram_nll": ("trigram", 0.75)}   # name: (model, fixed setting)
NAMES = MAIN_NAMES + tuple(SIDE)      # side baselines last, so they never delay the main ones


def kind(name):
    """The model a baseline name uses (a side baseline uses the chain or the trigram)."""
    return SIDE[name][0] if name in SIDE else name


def side_setting(name, tuning):
    """The fixed setting of a side baseline, checked against the development NLL in
    out/b04_tuning.json: it must be the grid value with the lowest NLL (a tie goes to the
    earlier grid value)."""
    k, val = SIDE[name]
    curve = tuning[k]["curve"]
    best = min(curve, key=lambda r: (r["dev_nll_scored_positions"], tuning[k]["grid"].index(r["value"])))
    if best["value"] != val:
        sys.exit(f"ABORT: side baseline {name} is fixed at {val}, but dev NLL picks {best['value']}")
    return val


def segments_with_start(seq):
    """Token runs of a sequence as the count models see them: each segment, preceded by
    its opening boundary when it has one. Nothing joins two segments."""
    tok, seg = seq["tok"], seq["seg"]
    brk = np.flatnonzero(np.diff(seg) != 0) + 1
    edges = np.concatenate(([0], brk, [tok.size]))
    return [tok[a:b] for a, b in zip(edges[:-1], edges[1:])]


# ============================================================================ constant
class Constant:
    def __init__(self, data):
        tr = data.split["train"]
        vc.record_fit("constant", tr)
        means = np.array([vc.to_model_space(data_rows(data, w)["curves"]).mean(0) for w in tr])
        x = means.mean(0)                       # equal weight over wells, model space
        self.curve = vc.from_model_space(x[None])[0]
        self.token = int(data.tk.encode(self.curve[None])[0])

    def generate(self, seq, prime_n, n_real, seed):
        L = seq["tok"].size
        is_b = seq["tok"][prime_n:] == B
        tok = np.where(is_b, B, self.token)[None].repeat(1, 0)
        cur = np.where(is_b[:, None], np.nan, self.curve[None])[None]
        return tok, cur


def data_rows(data, w):
    """Rows of a training well (always from the training file, also in confirmatory mode)."""
    return data.train_rows[w]


# ============================================================================ chain
class Chain:
    """First-order chain over K real tokens plus the boundary start state (row K)."""

    def __init__(self, train_seqs, plant_cross_boundary=False):
        counts = np.zeros((K + 1, K))
        uni = np.zeros(K)
        for s in train_seqs:
            runs = [s["tok"]] if plant_cross_boundary else segments_with_start(s)
            for t in runs:
                t = t[t != B] if plant_cross_boundary else t
                if t.size >= 2:
                    np.add.at(counts, (t[:-1], t[1:]), 1.0)
                uni += np.bincount(t[t != B], minlength=K)
        self.counts = counts
        self.uni = uni / uni.sum()
        rs = counts.sum(1, keepdims=True)
        self.p_mle = np.where(rs > 0, counts / np.maximum(rs, 1), 0.0)
        self.has_row = rs[:, 0] > 0

    def set_lambda(self, lam):
        self.lam = lam
        tr = (1 - lam) * self.p_mle + lam * self.uni[None]
        tr[~self.has_row] = self.uni
        self.P = tr / tr.sum(1, keepdims=True)
        self.cum = np.cumsum(self.P, 1)
        self.cum[:, -1] = 1.0

    def generate(self, seq, prime_n, n_real, seed):
        tok = seq["tok"]
        L = tok.size
        rng = np.random.default_rng(seed)
        out = np.empty((n_real, L - prime_n), dtype=np.int64)
        state = np.full(n_real, int(tok[prime_n - 1]))
        for i, p in enumerate(range(prime_n, L)):
            if tok[p] == B:
                out[:, i] = B
                state[:] = B
                continue
            u = rng.random(n_real)
            nxt = (self.cum[state] <= u[:, None]).sum(1)
            nxt = np.minimum(nxt, K - 1)
            out[:, i] = nxt
            state = nxt
        return out, None

    def one_step(self, tok, positions):
        prev = tok[positions - 1]
        p = self.P[prev, tok[positions]]
        return np.log(np.maximum(p, 1e-300)), self.P[prev].argmax(1)


# ============================================================================ trigram
class Trigram:
    """Interpolated absolute discounting (a32 / check3), contexts never cross a boundary.
    The boundary can be a context symbol (it opens a segment), never a target."""

    def __init__(self, train_seqs, plant_cross_boundary=False):
        c3 = defaultdict(lambda: defaultdict(int))
        c2 = defaultdict(lambda: defaultdict(int))
        uni = np.zeros(K)
        for s in train_seqs:
            runs = [s["tok"][s["tok"] != B]] if plant_cross_boundary else segments_with_start(s)
            for t in runs:
                t = t.tolist()
                for i in range(1, len(t)):
                    c2[t[i - 1]][t[i]] += 1
                for i in range(2, len(t)):
                    c3[(t[i - 2], t[i - 1])][t[i]] += 1
                uni += np.bincount([x for x in t if x != B], minlength=K)
        self.c2, self.c3 = c2, c3
        self.uni = uni / uni.sum()
        self.uni_cum = np.cumsum(self.uni); self.uni_cum[-1] = 1.0

    def set_discount(self, D):
        self.D = D

        def pack(d):
            ks = np.fromiter(d.keys(), dtype=np.int64, count=len(d))
            vs = np.fromiter(d.values(), dtype=np.float64, count=len(d))
            N = vs.sum()
            disc = np.maximum(vs - D, 0.0) / N
            lam = D * len(d) / N
            cum = np.cumsum(disc / disc.sum()) if disc.sum() > 0 else None
            if cum is not None:
                cum[-1] = 1.0
            return ks, disc, lam, cum

        self.p2 = {k: pack(v) for k, v in self.c2.items()}
        self.p3 = {k: pack(v) for k, v in self.c3.items()}
        self.P2 = np.tile(self.uni, (K + 1, 1))            # dense P(t | v), v in 0..K
        for v, (ks, pr, lam, _) in self.p2.items():
            row = lam * self.uni
            row[ks] += pr
            self.P2[v] = row
        self.p3_map = {k: dict(zip(ks.tolist(), pr.tolist())) for k, (ks, pr, lam, _) in self.p3.items()}

    def _draw(self, u, v, rng):
        """Hierarchical draw, exactly equivalent to sampling the interpolated mixture (a32)."""
        e = self.p3.get((u, v))
        if e is not None:
            ks, pr, lam, cum = e
            if cum is not None and rng.random() > lam:
                return int(ks[np.searchsorted(cum, rng.random(), side="right")])
        e = self.p2.get(v)
        if e is not None:
            ks, pr, lam, cum = e
            if cum is not None and rng.random() > lam:
                return int(ks[np.searchsorted(cum, rng.random(), side="right")])
        return int(min(np.searchsorted(self.uni_cum, rng.random(), side="right"), K - 1))

    @staticmethod
    def start_state(tok, p):
        """(u, v) context for predicting position p, never crossing a boundary."""
        v = int(tok[p - 1])
        if v == B or p < 2:
            return -1, v
        u = int(tok[p - 2])
        return u, v                    # u may be the boundary that opens the segment

    def generate(self, seq, prime_n, n_real, seed):
        tok = seq["tok"]
        L = tok.size
        rng = np.random.default_rng(seed)
        out = np.empty((n_real, L - prime_n), dtype=np.int64)
        for r in range(n_real):
            u, v = self.start_state(tok, prime_n)
            for i, p in enumerate(range(prime_n, L)):
                if tok[p] == B:
                    out[r, i] = B
                    u, v = -1, B
                    continue
                t = self._draw(u, v, rng)
                out[r, i] = t
                u, v = v, t
        return out, None

    def prob(self, u, v, t):
        m = self.p3_map.get((u, v))
        if m is None:
            return self.P2[v][t]
        return m.get(t, 0.0) + self.p3[(u, v)][2] * self.P2[v][t]

    def dist(self, u, v):
        e = self.p3.get((u, v))
        if e is None:
            return self.P2[v]
        ks, pr, lam, _ = e
        d = lam * self.P2[v]
        d[ks] += pr
        return d

    def one_step(self, tok, positions):
        lp, top = np.empty(positions.size), np.empty(positions.size, dtype=np.int64)
        for j, p in enumerate(positions):
            u, v = self.start_state(tok, p)
            lp[j] = np.log(max(self.prob(u, v, int(tok[p])), 1e-300))
            top[j] = int(np.argmax(self.dist(u, v)))
        return lp, top


# ============================================================================ block resampling
class Blocks:
    """Real intervals of the training wells. A block lies inside one segment. Starts are
    drawn uniformly over all valid start rows pooled over the 80 training wells."""

    def __init__(self, data, depth_matched=False):
        vc.record_fit("blocks", data.split["train"])
        self.rows = [data_rows(data, w) for w in data.split["train"]]
        self.depth_matched = depth_matched
        # one table of every training row: well, row, depth, and 'room' = rows from it to the
        # end of its segment (inclusive). A block of length m may start at a row with room >= m.
        wi, st, dep, room = [], [], [], []
        for i, r in enumerate(self.rows):
            seg = r["seg"]
            n = seg.size
            last = np.r_[np.flatnonzero(np.diff(seg) != 0), n - 1]        # last row of each segment
            end = last[np.searchsorted(last, np.arange(n))]
            wi.append(np.full(n, i, dtype=np.int32)); st.append(np.arange(n, dtype=np.int32))
            dep.append(r["depth"]); room.append((end - np.arange(n) + 1).astype(np.int32))
        wi, st, dep, room = map(np.concatenate, (wi, st, dep, room))
        order = np.argsort(dep, kind="stable")
        self.wi, self.st, self.dep, self.room = wi[order], st[order], dep[order], room[order]
        self.by_room = np.argsort(-self.room, kind="stable")     # rows with room >= m form a prefix
        self.neg_room_sorted = -self.room[self.by_room]

    def candidates(self, m, target_depth):
        """Indices (into the depth-sorted table) of valid starts for a block of length m."""
        if not self.depth_matched:
            return self.by_room[:np.searchsorted(self.neg_room_sorted, -m, side="right")]
        for win in DEPTH_WINDOWS_M:
            a = np.searchsorted(self.dep, target_depth - win, side="left")
            b = np.searchsorted(self.dep, target_depth + win, side="right")
            c = a + np.flatnonzero(self.room[a:b] >= m)
            if c.size:
                return c
        return self.by_room[:np.searchsorted(self.neg_room_sorted, -m, side="right")]

    def draw(self, m, rng, target_depth=None):
        c = self.candidates(m, target_depth)
        j = int(c[rng.integers(0, c.size)])
        r = self.rows[self.wi[j]]
        s = int(self.st[j])
        return r["tok"][s:s + m], r["curves"][s:s + m]

    def set_length(self, Lb):
        self.Lb = Lb

    def generate(self, seq, prime_n, n_real, seed):
        tok = seq["tok"]
        L = tok.size
        rng = np.random.default_rng(seed)
        G = L - prime_n
        out = np.empty((n_real, G), dtype=np.int64)
        cur = np.full((n_real, G, 4), np.nan)
        is_b = tok[prime_n:] == B
        brk = np.flatnonzero(is_b)
        runs, a = [], 0
        for b in list(brk) + [G]:
            if b > a:
                runs.append((a, b))
            a = b + 1
        out[:, is_b] = B
        for r in range(n_real):
            for a, b in runs:
                p = a
                while p < b:
                    m = min(self.Lb, b - p)
                    t, c = self.draw(m, rng, seq["depth"][prime_n + p])
                    out[r, p:p + m] = t
                    cur[r, p:p + m] = c
                    p += m
        return out, cur


# ============================================================================ helpers
def build(name, data, plant_cross_boundary=False):
    tr = [data.train_seq[w] for w in data.split["train"]]
    vc.record_fit(name, data.split["train"])
    name = kind(name)
    if name == "constant":
        return Constant(data)
    if name == "chain":
        return Chain(tr, plant_cross_boundary)
    if name == "trigram":
        return Trigram(tr, plant_cross_boundary)
    if name == "block":
        return Blocks(data)
    if name == "depthblock":
        return Blocks(data, depth_matched=True)
    raise ValueError(name)


def set_param(model, name, val):
    name = kind(name)
    if name == "chain":
        model.set_lambda(val)
    elif name == "trigram":
        model.set_discount(val)
    elif name in ("block", "depthblock"):
        model.set_length(val)


def gen_record(model, name, data, w, n_real, seed):
    seq = data.seq[w]
    L = seq["tok"].size
    prime_n = vc.prime_len(L)
    R = 1 if name == "constant" else n_real
    t0 = time.time()
    gen_tok, cur = model.generate(seq, prime_n, R, seed)
    if cur is None:
        cur = np.stack([data.tk.decode_tokens(gen_tok[r]) for r in range(R)])
    rec = dict(well=w, prime_n=prime_n, L=L, L_full=L, gen_tok=gen_tok.astype(np.int16),
               curves=cur.astype(np.float32), n_generated=int(L - prime_n), n_real=R, seed=seed,
               seconds_gen=time.time() - t0, source=name)
    if kind(name) in ("chain", "trigram"):
        pos = prime_n + np.flatnonzero(seq["tok"][prime_n:] != B)
        lp, top = model.one_step(seq["tok"], pos)
        rec.update(osa_positions=pos, osa_logp_true=lp, osa_top1=top.astype(np.int16))
    return rec


def real_view(data, w, prime_n):
    seq = data.seq[w]
    m = seq["tok"][prime_n:] != B
    cur = data.curves_seq(w)[prime_n:][m]
    return dict(nphi=cur[:, vc.NPHI], tok=seq["tok"][prime_n:][m], fac=data.facies_seq(w)[prime_n:][m],
                seg=seq["seg"][prime_n:][m], depth=seq["depth"][prime_n:][m])


def gen_view(data, rec, r, matched):
    t = rec["gen_tok"][r].astype(np.int64)[matched]
    return dict(nphi=rec["curves"][r][matched][:, vc.NPHI].astype(np.float64), tok=t, fac=data.tok2fac[t])


def tune(data, log=print):
    """Section 6: interpolation weight, discount and block length on development wells,
    chosen by the structure score (lower is better)."""
    res = {}
    wells = [w for w in data.split["dev"] if data.rows[w]["n_valid"] >= 2000]
    grids = dict(chain=LAMBDA_GRID, trigram=DISCOUNT_GRID, block=BLOCK_GRID)
    for name, grid in grids.items():
        model = build(name, data)
        curve = []
        for val in grid:
            set_param(model, name, val)
            t0 = time.time()
            per_well = {}
            dev_ll = []
            for w in wells:
                rec = gen_record(model, name, data, w, vc.N_REAL, TUNE_SEED)
                matched = rec["gen_tok"][0] != B
                real = real_view(data, w, rec["prime_n"])
                gens = [gen_view(data, rec, r, matched) for r in range(rec["n_real"])]
                per_well[w] = sc.score_well(real, gens)["structure"]
                if "osa_logp_true" in rec:
                    dev_ll.append(rec["osa_logp_true"])
            row = dict(value=val, structure=float(np.mean(list(per_well.values()))), per_well=per_well,
                       seconds=time.time() - t0)
            if dev_ll:
                row["dev_nll_scored_positions"] = float(-np.mean(np.concatenate(dev_ll)))
            curve.append(row)
            log(f"  tune {name} {val}: structure {row['structure']:.5f}"
                + (f"  dev NLL {row['dev_nll_scored_positions']:.4f}" if dev_ll else "")
                + f"  ({row['seconds']:.0f}s)")
        best = min(curve, key=lambda r: (r["structure"], grid.index(r["value"])))
        res[name] = dict(grid=grid, chosen=best["value"], curve=curve, criterion="structure score, dev wells",
                         sampling_seed=TUNE_SEED, n_realizations=vc.N_REAL, wells=wells)
        log(f"CHOSEN {name}: {best['value']}")
    res["depthblock"] = dict(chosen=res["block"]["chosen"], note="block length tuned for 'block'")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["tune", "run"])
    ap.add_argument("--wells", nargs="+", default=["dev", "pilot"])
    ap.add_argument("--csv", default=None)
    ap.add_argument("--names", nargs="+", default=list(NAMES))
    ap.add_argument("--seeds", nargs="+", type=int, default=SAMPLING_SEEDS)
    ap.add_argument("--outroot", default=str(vc.V4 / "gens"))
    args = ap.parse_args()
    vc.check_protocol()
    log = lambda m: print(m, flush=True)  # noqa: E731
    split = vc.load_split()
    fit_df = vc.load_df(vc.FORCE_TRAIN_CSV)
    tk = vc.load_tokenizer()

    if args.cmd == "tune":
        data = vc.Data(split, fit_df, tk)
        t0 = time.time()
        res = tune(data, log)
        res["seconds"] = time.time() - t0
        vc.save_json(res, vc.OUT / "b04_tuning.json")
        return

    tuning = json.loads((vc.OUT / "b04_tuning.json").read_text())
    if args.csv:
        df = vc.load_df(Path(args.csv))
        cw = sorted(df.WELL.astype(str).unique())
        if set(cw) & set(split["pool98"]):
            sys.exit("ABORT: confirmatory file holds pool wells")
        data = vc.Data(split, df, tk, wells=cw, fit_df=fit_df)
        sets = {"csv": [w for w in cw if data.rows[w]["n_valid"] >= 2000]}
    else:
        data = vc.Data(split, fit_df, tk)
        sets = {s: [w for w in split[s] if data.rows[w]["n_valid"] >= 2000] for s in args.wells}
    for name in args.names:
        model = build(name, data)
        setting = side_setting(name, tuning) if name in SIDE else tuning.get(name, {}).get("chosen")
        if name != "constant":
            set_param(model, name, setting)
        seeds = [args.seeds[0]] if name == "constant" else args.seeds
        for seed in seeds:
            for setname, wells in sets.items():
                out = Path(args.outroot) / f"baseline_{name}" / f"seed{seed}" / setname
                out.mkdir(parents=True, exist_ok=True)
                t0 = time.time()
                for w in wells:
                    f = out / f"{w.replace('/', '_').replace(' ', '')}.npz"
                    if f.exists():
                        continue
                    rec = gen_record(model, name, data, w, vc.N_REAL, seed)
                    tmp = f.with_suffix(".tmp.npz")
                    np.savez_compressed(tmp, **rec)
                    tmp.replace(f)
                vc.save_json(dict(source=name, seed=seed, wells=wells, setting=setting, side=name in SIDE,
                                  seconds=time.time() - t0), out / "meta.json")
                log(f"  {name} seed {seed} {setname}: {len(wells)} wells in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
