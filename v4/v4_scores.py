"""Scores (protocol section 8) and the wells-and-seeds bootstrap (section 9).

Per well, on matched positions (generated positions that are not boundary positions),
per realization, then averaged over realizations; then averaged over wells with
equal weight.

  bias          signed: mean(gen NPHI) - mean(real NPHI); absolute: |signed|
  w1            Wasserstein-1 distance between gen and real NPHI values
  spread        std(gen NPHI) / std(real NPHI)
  trend share   share of NPHI variance carried by 100 m bin means (gen and real; gap = gen - real)
  structure     mean over lags 1,2,5,10,20,50,100,200 of |kappa_gen - kappa_real| on tokens
  facies struct the same on lithofacies (token -> most common training facies; real wells
                use their true labels where the file has them)
  copying       share of 10-, 20-, 50-token sequences found word for word in the training
                wells (gen and real; gap = gen - real)
  one step      NLL and top-1 at the matched positions, teacher forced (model arms and
                count models only)

Kappa at lag l, for one sequence: p_obs = share of pairs (i, i+l) inside one segment
that are equal; p_chance = sum of squared shares of the sequence's own values;
kappa = (p_obs - p_chance) / (1 - p_chance). This is the a23/a31 estimator applied to
one sequence (a31's within-segment pairs), as section 8 asks for per-well scores.
"""
import sys

sys.dont_write_bytecode = True

import numpy as np

from v4_common import BOUNDARY, SEED

LAGS = (1, 2, 5, 10, 20, 50, 100, 200)
NGRAM_NS = (10, 20, 50)
TREND_BIN_M = 100.0
N_BOOT = 10000


# ----------------------------------------------------------------------------- kappa
def kappa_lags(seq, seg, lags=LAGS, ignore_segments=False):
    a = np.asarray(seq)
    s = np.zeros_like(a) if ignore_segments else np.asarray(seg)
    out = {}
    if a.size == 0:
        return {l: np.nan for l in lags}
    _, cnt = np.unique(a, return_counts=True)
    p = cnt / cnt.sum()
    pe = float(np.sum(p ** 2))
    for l in lags:
        if a.size <= l or pe >= 1.0:
            out[l] = np.nan
            continue
        same = s[l:] == s[:-l]
        if not same.any():
            out[l] = np.nan
            continue
        po = float(np.mean((a[l:] == a[:-l])[same]))
        out[l] = (po - pe) / (1.0 - pe)
    return out


def structure_gap(gen_seq, real_seq, seg, lags=LAGS, plant_gen_ignores_segments=False):
    kg = kappa_lags(gen_seq, seg, lags, ignore_segments=plant_gen_ignores_segments)
    kr = kappa_lags(real_seq, seg, lags)
    gaps = [abs(kg[l] - kr[l]) for l in lags if np.isfinite(kg[l]) and np.isfinite(kr[l])]
    return (float(np.mean(gaps)) if gaps else np.nan), kg, kr


# ----------------------------------------------------------------------------- runs
def run_lengths(seq, seg):
    """Lengths of runs of equal values; a run never continues across a segment change."""
    a = np.asarray(seq); s = np.asarray(seg)
    if a.size == 0:
        return np.zeros(0, dtype=np.int64)
    brk = np.flatnonzero((a[1:] != a[:-1]) | (s[1:] != s[:-1])) + 1
    edges = np.concatenate(([0], brk, [a.size]))
    return np.diff(edges)


# ----------------------------------------------------------------------------- trend share
def trend_share(x, depth, bin_m=TREND_BIN_M):
    x = np.asarray(x, dtype=np.float64)
    v = np.var(x)
    if x.size < 2 or v <= 0:
        return np.nan
    b = np.floor(np.asarray(depth) / bin_m).astype(np.int64)
    _, inv = np.unique(b, return_inverse=True)
    bm = np.bincount(inv, weights=x) / np.bincount(inv)
    return float(np.var(bm[inv]) / v)


# ----------------------------------------------------------------------------- copying
def ngrams(seq, seg, n):
    """All n-grams that lie inside one segment, as bytes keys."""
    a = np.ascontiguousarray(np.asarray(seq, dtype=np.int16))
    s = np.asarray(seg)
    if a.size < n:
        return []
    ok = s[:a.size - n + 1] == s[n - 1:]
    win = np.lib.stride_tricks.sliding_window_view(a, n)[ok]
    win = np.ascontiguousarray(win)
    return [r.tobytes() for r in win]


class NgramIndex:
    """n-grams of the training wells (fitted on training wells only)."""

    def __init__(self, train_pairs, ns=NGRAM_NS):
        self.sets = {n: set() for n in ns}
        for tok, seg in train_pairs:
            m = tok != BOUNDARY
            for n in ns:
                self.sets[n].update(ngrams(tok[m], seg[m], n))

    def share(self, seq, seg, n):
        g = ngrams(seq, seg, n)
        if not g:
            return np.nan
        st = self.sets[n]
        return float(np.mean([k in st for k in g]))


# ----------------------------------------------------------------------------- one well
def score_well(real, gens, ngram_index=None, plant=None):
    """real: dict(nphi, tok, fac, seg, depth) on matched positions.
    gens: list of dicts (nphi, tok, fac) on the same matched positions, one per realization.
    Returns per-realization lists and their means."""
    plant = plant or {}
    r_nphi = np.asarray(real["nphi"], dtype=np.float64)
    seg = np.asarray(real["seg"])
    r_trend = trend_share(r_nphi, real["depth"])
    per = {k: [] for k in ("bias_signed", "bias_abs", "w1", "spread", "trend_share_gen", "trend_gap",
                           "structure", "facies_structure")}
    if ngram_index is not None:
        for n in NGRAM_NS:
            per[f"copy{n}_gen"] = []
            per[f"copy{n}_gap"] = []
        r_copy = {n: ngram_index.share(real["tok"], seg, n) for n in NGRAM_NS}
    from scipy.stats import wasserstein_distance
    for g in gens:
        g_nphi = np.asarray(g["nphi"], dtype=np.float64)
        r_use = r_nphi
        if plant.get("off_by_one"):           # planted error: misaligned positions
            g_nphi = np.r_[g_nphi[1:], g_nphi[-1]]
        b = float(np.mean(g_nphi) - np.mean(r_use))
        per["bias_signed"].append(b)
        per["bias_abs"].append(abs(b))
        per["w1"].append(float(wasserstein_distance(r_use, g_nphi)))
        sr = np.std(r_use)
        per["spread"].append(float(np.std(g_nphi) / sr) if sr > 0 else np.nan)
        tg = trend_share(g_nphi, real["depth"])
        per["trend_share_gen"].append(tg)
        per["trend_gap"].append(tg - r_trend)
        gt = np.asarray(g["tok"])
        if plant.get("off_by_one"):
            gt = np.r_[gt[1:], gt[-1]]
        per["structure"].append(structure_gap(gt, real["tok"], seg,
                                              plant_gen_ignores_segments=plant.get("ignore_segments", False))[0])
        per["facies_structure"].append(structure_gap(g["fac"], real["fac"], seg)[0])
        if ngram_index is not None:
            for n in NGRAM_NS:
                c = ngram_index.share(gt, seg, n)
                per[f"copy{n}_gen"].append(c)
                per[f"copy{n}_gap"].append(c - r_copy[n])
    out = {k: _nanmean(v) for k, v in per.items()}
    out["per_realization"] = per
    out["trend_share_real"] = r_trend
    out["n_matched"] = int(r_nphi.size)
    if ngram_index is not None:
        for n in NGRAM_NS:
            out[f"copy{n}_real"] = r_copy[n]
    return out


def _nanmean(v):
    v = np.asarray(v, dtype=np.float64)
    return float(np.nanmean(v)) if np.isfinite(v).any() else float("nan")


def mean_over_wells(per_well, key):
    """Equal weight over wells; wells where the score is not defined are left out and
    the number used is reported."""
    v = np.array([per_well[w][key] for w in per_well], dtype=np.float64)
    ok = np.isfinite(v)
    return dict(mean=(float(v[ok].mean()) if ok.any() else float("nan")), n_wells=int(ok.sum()))


# ----------------------------------------------------------------------------- bootstrap
def bootstrap_wells_seeds(M, n_boot=N_BOOT, seed=SEED, plant_wells_only=False, plant_percentiles=None):
    """Section 9. M[w, s] is a per-(well, seed) value, for example the difference between
    two sources paired by seed order. Each draw resamples wells and seeds together, both
    with replacement, and takes the mean over the resampled grid. Returns the estimate
    (equal-weight mean over wells and seeds) and the 2.5th and 97.5th percentiles."""
    M = np.asarray(M, dtype=np.float64)
    assert M.ndim == 2 and np.isfinite(M).all()
    W, S = M.shape
    rng = np.random.default_rng(seed)
    stats = np.empty(n_boot)
    for b in range(n_boot):
        wi = rng.integers(0, W, W)
        si = np.arange(S) if plant_wells_only else rng.integers(0, S, S)
        stats[b] = M[np.ix_(wi, si)].mean()
    lo_p, hi_p = plant_percentiles or (2.5, 97.5)
    return dict(estimate=float(M.mean()), lo=float(np.percentile(stats, lo_p)),
                hi=float(np.percentile(stats, hi_p)), n_boot=n_boot, n_wells=W, n_seeds=S, seed=seed)


MAIN_COMPARISONS = [
    # (name, source x, source y, score) : x minus y
    ("B2_minus_A_abs_bias", "B2", "A", "bias_abs"),
    ("A_minus_chain_abs_bias", "A", "chain", "bias_abs"),
    ("A_minus_trigram_structure", "A", "trigram", "structure"),
    ("A_minus_block_structure", "A", "block", "structure"),
]

# Side result (author's ruling on Q18): the same differences against the chain and the trigram
# at the settings development likelihood picks. Not part of the four main comparisons.
SIDE_COMPARISONS = [
    ("A_minus_chain_nll_abs_bias", "A", "chain_nll", "bias_abs"),
    ("A_minus_trigram_nll_structure", "A", "trigram_nll", "structure"),
]


def main_comparisons(table, wells, n_boot=N_BOOT, plant_pair_by_position=False, comps=None):
    """table[source][seed][well] = per-well score dict. Training seed i and sampling seed i
    carry the same number (20260715 + i), so pairing by order is pairing by seed value; only
    seeds present for both sides are used, and they are listed. Returns the four section 9
    results."""
    res = {}
    for name, x, y, key in (MAIN_COMPARISONS if comps is None else comps):
        if x not in table or y not in table:
            res[name] = dict(missing=[s for s in (x, y) if s not in table])
            continue
        seeds = sorted(set(table[x]) & set(table[y]))
        if plant_pair_by_position:          # planted error for the tests: pairs list positions
            sx, sy = sorted(table[x]), sorted(table[y])
            n = min(len(sx), len(sy))
            M = np.array([[table[x][sx[i]][w][key] - table[y][sy[i]][w][key] for i in range(n)] for w in wells])
        else:
            M = np.array([[table[x][s][w][key] - table[y][s][w][key] for s in seeds] for w in wells])
        res[name] = bootstrap_wells_seeds(M, n_boot=n_boot)
        res[name].update(score=key, x=x, y=y, seeds=seeds)
    return res
