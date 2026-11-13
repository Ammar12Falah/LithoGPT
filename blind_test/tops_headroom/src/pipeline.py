"""Country-independent pipeline: chosen tops, split, tuning, forecasts,
floors, scoring, checks. Inputs are the `holes` and `picks` tables made by a
country loader (kansas.py, netherlands.py).

holes: hole_id, x, y (metres), test_date, rule_date, eligible, pre_test,
       loc_precise, flag_elev, flag_loc
picks: hole_id, record_id, top, elev_m, avail (finish date of the record
       that supplied the pick)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

import methods as M

SEED = 20261113
BANDS = [(0, 30, "same site (<30 m)"), (30, 1000, "30 m-1 km"), (1000, 5000, "1-5 km"),
         (5000, 20000, "5-20 km"), (20000, np.inf, ">20 km")]
METHODS = ["m1_nearest", "m2_plane", "m3_kriging", "m4_thickness"]
METHOD_LABEL = {"m1_nearest": "1 Nearest known well", "m2_plane": "2 Local plane",
                "m3_kriging": "3 Kriging with local trend", "m4_thickness": "4 Thickness method"}
NAT_DAY = np.iinfo(np.int64).min
FAR_M = 1000.0
N_BOOT = 1000


def to_day(s):
    d = pd.to_datetime(s).values.astype("datetime64[D]").astype("int64")
    return d


def band_of(d):
    out = np.full(len(d), -1)
    for i, (lo, hi, _) in enumerate(BANDS):
        out[(d >= lo) & (d < hi)] = i
    return out


class Ctx:
    """Arrays for one country. Pools hold only holes that are not sealed."""

    def __init__(self, cfg, holes, picks_known, tops):
        self.cfg = cfg
        self.holes = holes.reset_index(drop=True)
        self.hid = {h: i for i, h in enumerate(self.holes["hole_id"])}
        self.x = self.holes["x"].to_numpy(float)
        self.y = self.holes["y"].to_numpy(float)
        self.tops = list(tops)
        self.T = len(tops)
        pk = picks_known[picks_known["top"].isin(tops)].copy()
        pk["h"] = pk["hole_id"].map(self.hid).astype(np.int64)
        pk["t"] = pk["top"].map({t: i for i, t in enumerate(tops)}).astype(int)
        pk["day"] = to_day(pk["avail"])
        self.pk = pk
        H = len(self.holes)
        self.elev = np.full((H, self.T), np.nan)       # value of every known pick
        self.avail = np.full((H, self.T), NAT_DAY, dtype=np.int64)
        self.elev[pk["h"], pk["t"]] = pk["elev_m"].to_numpy()
        self.avail[pk["h"], pk["t"]] = pk["day"].to_numpy()
        self.rec = np.full((H, self.T), "", dtype=object)
        self.rec[pk["h"], pk["t"]] = pk["record_id"].to_numpy()
        self._pools = {}
        self._pairs = {}

    def pool(self, j, mask=None):
        key = (j, None if mask is None else id(mask))
        if key not in self._pools:
            ok = np.isfinite(self.elev[:, j]) & (self.avail[:, j] != NAT_DAY)
            if mask is not None:
                ok &= mask
            h = np.nonzero(ok)[0]
            self._pools[key] = M.Pool(h, self.x[h], self.y[h], self.elev[h, j], self.avail[h, j])
        return self._pools[key]

    def pair_pool(self, a, b, mask=None):
        """Holes that report both tops a (upper) and b (lower): thickness."""
        key = (a, b, None if mask is None else id(mask))
        if key not in self._pairs:
            th = self.elev[:, a] - self.elev[:, b]
            ok = np.isfinite(th) & (th > 0) & (self.avail[:, a] != NAT_DAY) & (self.avail[:, b] != NAT_DAY)
            if mask is not None:
                ok &= mask
            h = np.nonzero(ok)[0]
            self._pairs[key] = M.Pool(h, self.x[h], self.y[h], th[h], np.maximum(self.avail[h, a], self.avail[h, b]))
        return self._pairs[key]


def cutoff_days(rule_date, wait):
    """Latest finish day a known well may have. wait is a pandas DateOffset,
    or None for the no-waiting-time side run (finished before the spud day)."""
    rd = pd.to_datetime(pd.Series(rule_date))
    if wait is None:
        return to_day(rd) - 1
    return to_day(rd - wait)


# --------------------------------------------------------------------------
# forecasts for a set of wells
# --------------------------------------------------------------------------
def forecast_wells(ctx, widx, cutoff, S, mask=None, keep_audit=False, do_m4=True):
    """All four methods at wells `widx` for every chosen top.

    Returns dict of (W, T) arrays: m1..m4, d1 (distance to the nearest known
    well with that top), hw3 (half width of the 80 % range of method 3),
    anchor, chain (bit mask of the tops in the thickness chain).
    """
    W, T = len(widx), ctx.T
    tx, ty = ctx.x[widx], ctx.y[widx]
    out = {k: np.full((W, T), np.nan) for k in ["m1", "m2", "m3", "m4", "d1", "hw3"]}
    out["anchor"] = np.full((W, T), -1)
    out["chain"] = np.zeros((W, T), dtype=np.int64)
    sup_top = np.zeros((T, W), dtype=bool)
    audit = {"top_idx": {}, "link_idx": {}} if keep_audit else None
    m_sup, R = S["support_min_wells"], S["support_radius_m"]
    for j in range(T):
        pool = ctx.pool(j, mask)
        cfg3 = S["m3"][ctx.tops[j]]
        nmax = max(S["m2_n"], cfg3["n"], m_sup)
        idx, dist = pool.known_neighbours(tx, ty, widx, cutoff, nmax)
        xk, yk, z, valid = M.gather(pool, idx, tx, ty)
        has = valid[:, 0]
        out["m1"][:, j] = np.where(has, z[:, 0], np.nan)
        out["d1"][:, j] = dist[:, 0]
        # method 2
        n2 = S["m2_n"]
        v2 = valid[:, :n2]
        if S["screen"]:
            v2 = M.screen_outliers(xk[:, :n2], yk[:, :n2], z[:, :n2], v2, S["screen_k"], S["screen_min_m"])
        out["m2"][:, j], _ = M.plane_fit(xk[:, :n2], yk[:, :n2], z[:, :n2], v2)
        # method 3
        n3 = cfg3["n"]
        v3 = valid[:, :n3]
        if S["screen"]:
            v3 = M.screen_outliers(xk[:, :n3], yk[:, :n3], z[:, :n3], v3, S["screen_k"], S["screen_min_m"])
        p3, uv, s2, dof = M.krige(xk[:, :n3], yk[:, :n3], z[:, :n3], v3, cfg3["alpha"], cfg3["r"])
        out["m3"][:, j] = p3
        out["hw3"][:, j] = M.interval_halfwidth(uv, s2, dof, cfg3["s2_fallback"], S["interval_calib"])
        sup_top[j] = dist[:, m_sup - 1] <= R
        if keep_audit:
            audit["top_idx"][j] = (pool.hole_idx, idx.astype(np.int32), dist.astype(np.float32), z.astype(np.float32))
    if not do_m4:
        return out, audit
    # ---- method 4: shallowest supported top by kriging, then thicknesses --
    th = np.full((T, T, W), np.nan)
    sup_link = np.zeros((T, T, W), dtype=bool)
    nt = S["th_n"]
    for a in range(T):
        for b in range(a + 1, T):
            pool = ctx.pair_pool(a, b, mask)
            idx, dist = pool.known_neighbours(tx, ty, widx, cutoff, max(nt, m_sup))
            sup = dist[:, m_sup - 1] <= R
            sup_link[a, b] = sup
            if sup.any():
                rows = np.nonzero(sup)[0]
                xk, yk, z, valid = M.gather(pool, idx[rows, :nt], tx[rows], ty[rows])
                if S["screen"]:
                    valid = M.screen_outliers(xk, yk, z, valid, S["screen_k"], S["screen_min_m"])
                p, _, _, _ = M.krige(xk, yk, z, valid, S["th_alpha"], S["th_r"], drift_linear=S["th_linear"])
                th[a, b, rows] = p
            if keep_audit:
                audit["link_idx"][(a, b)] = (pool.hole_idx, idx[:, :nt].astype(np.int32), dist[:, :nt].astype(np.float32))
    ar = np.arange(W)
    for k in range(T):
        done = np.zeros(W, dtype=bool)
        for a in range(k):
            ok = sup_top[a] & np.isfinite(out["m3"][:, a]) & ~done
            if not ok.any():
                continue
            cur = np.full(W, a)
            total = np.zeros(W)
            chain = np.full(W, 1 << a, dtype=np.int64)
            for b in range(a + 1, k + 1):
                s = sup_link[cur, b, ar] & np.isfinite(th[cur, b, ar])
                total = np.where(s, total + th[cur, b, ar], total)
                chain = np.where(s, chain | (1 << b), chain)
                cur = np.where(s, b, cur)
            ok &= cur == k
            out["m4"][ok, k] = out["m3"][ok, a] - total[ok]
            out["anchor"][ok, k] = a
            out["chain"][ok, k] = chain[ok]
            done |= ok
        rest = ~done
        out["m4"][rest, k] = out["m3"][rest, k]
        out["anchor"][rest, k] = k
        out["chain"][rest, k] = 1 << k
    return out, audit


# --------------------------------------------------------------------------
# settings from wells drilled before the test years
# --------------------------------------------------------------------------
def tune(ctx, cfg, outdir):
    rng = np.random.default_rng(SEED)
    h = ctx.holes
    c = cfg["code"]
    start_day = to_day(pd.Series([cfg["test_start"]]))[0]
    pt = h.index[(h["pre_test"]) & (h["test_date"] >= cfg["tune_start"]) & h["rule_date"].notna()].to_numpy()
    cut_all = cutoff_days(h["rule_date"].to_numpy()[pt], cfg["wait"])
    pos = {w: i for i, w in enumerate(pt)}
    rows = []
    S = dict(screen_k=6.0, screen_min_m=cfg.get("screen_min_m", 3.0), support_min_wells=5)
    n_grid3 = cfg.get("n_grid3", [12, 24])
    alphas = [0.5, 1.0, 1.5]
    rs = [0.01, 0.03, 0.1, 0.3, 1.0, 3.0]
    n_grid2 = [3, 4, 6, 8, 12, 16, 24]
    per_top = {}
    m2_err = {}
    for j, top in enumerate(ctx.tops):
        ok = np.isfinite(ctx.elev[pt, j]) & (ctx.avail[pt, j] != NAT_DAY) & (ctx.avail[pt, j] < start_day)
        cand = pt[ok]
        if len(cand) > cfg["tune_sample"]:
            cand = np.sort(rng.choice(cand, cfg["tune_sample"], replace=False))
        cut = cut_all[[pos[w] for w in cand]]
        pool = ctx.pool(j)
        tx, ty = ctx.x[cand], ctx.y[cand]
        idx, dist = pool.known_neighbours(tx, ty, cand, cut, max(n_grid3 + n_grid2))
        xk, yk, z, valid = M.gather(pool, idx, tx, ty)
        truth = ctx.elev[cand, j]
        have = valid[:, 0]
        res = {}
        for screen in (False, True):
            for n in n_grid2:
                v = valid[:, :n]
                if screen:
                    v = M.screen_outliers(xk[:, :n], yk[:, :n], z[:, :n], v, S["screen_k"], S["screen_min_m"])
                p, _ = M.plane_fit(xk[:, :n], yk[:, :n], z[:, :n], v)
                m2_err[(screen, n, j)] = np.abs(p - truth)[have]
            for n in n_grid3:
                v = valid[:, :n]
                if screen:
                    v = M.screen_outliers(xk[:, :n], yk[:, :n], z[:, :n], v, S["screen_k"], S["screen_min_m"])
                for al in alphas:
                    for r in rs:
                        p, uv, s2, dof = M.krige(xk[:, :n], yk[:, :n], z[:, :n], v, al, r)
                        e = np.abs(p - truth)[have]
                        res[(screen, n, al, r)] = (e, uv[have], s2[have], dof[have])
                        rows.append(dict(part="method 3", top=top, screen=screen, n=n, alpha=al, r=r,
                                         n_items=int(have.sum()), mae_m=float(np.median(e)), p90_m=float(np.percentile(e, 90))))
        per_top[j] = res
    # screening on or off: pooled median error of method 3 with each top's best shape
    best = {}
    pooled = {}
    for screen in (False, True):
        errs = []
        for j in range(ctx.T):
            keys = [k for k in per_top[j] if k[0] == screen]
            kbest = min(keys, key=lambda k: (np.median(per_top[j][k][0]), k[1], k[2], k[3]))
            best[(screen, j)] = kbest
            errs.append(per_top[j][kbest][0])
        pooled[screen] = float(np.median(np.concatenate(errs)))
    screen = bool(pooled[True] < pooled[False])
    S["screen"] = screen
    S["m3"] = {}
    ratios = []
    for j, top in enumerate(ctx.tops):
        _, n, al, r = best[(screen, j)]
        e, uv, s2, dof = per_top[j][best[(screen, j)]]
        good = (dof >= 3) & np.isfinite(s2) & (s2 > 0)
        s2fb = float(np.median(s2[good])) if good.any() else 1.0
        S["m3"][top] = dict(n=int(n), alpha=float(al), r=float(r), s2_fallback=s2fb)
        hw = M.interval_halfwidth(uv, s2, dof, s2fb, 1.0)
        ratios.append(e / hw)
    ratios = np.concatenate(ratios)
    S["interval_calib"] = float(np.quantile(ratios[np.isfinite(ratios)], 0.80))
    S["interval_cover_before_calib"] = float(np.mean(ratios[np.isfinite(ratios)] <= 1.0))
    # method 2: number of wells in the plane
    m2 = {n: float(np.median(np.concatenate([m2_err[(screen, n, j)] for j in range(ctx.T)]))) for n in n_grid2}
    for n in n_grid2:
        rows.append(dict(part="method 2", top="all chosen tops pooled", screen=screen, n=n, n_items=int(sum(len(m2_err[(screen, n, j)]) for j in range(ctx.T))), mae_m=m2[n]))
    S["m2_n"] = int(min(n_grid2, key=lambda n: (m2[n], n)))
    for s in (False, True):
        rows.append(dict(part="screening choice (method 3, best shape per top, pooled)", top="all chosen tops pooled", screen=s, mae_m=pooled[s]))
    # ---- thickness kriging settings: consecutive layers ------------------
    th_res = {}
    for j in range(ctx.T - 1):
        a, b = j, j + 1
        both = np.isfinite(ctx.elev[pt, a]) & np.isfinite(ctx.elev[pt, b]) & (ctx.avail[pt, a] < start_day) & \
            (ctx.avail[pt, b] < start_day) & (ctx.avail[pt, a] != NAT_DAY) & (ctx.avail[pt, b] != NAT_DAY)
        cand = pt[both]
        if len(cand) > cfg["tune_sample"] // 2:
            cand = np.sort(rng.choice(cand, cfg["tune_sample"] // 2, replace=False))
        if len(cand) == 0:
            continue
        cut = cut_all[[pos[w] for w in cand]]
        pool = ctx.pair_pool(a, b)
        tx, ty = ctx.x[cand], ctx.y[cand]
        idx, dist = pool.known_neighbours(tx, ty, cand, cut, 16)
        xk, yk, z, valid = M.gather(pool, idx, tx, ty)
        truth = ctx.elev[cand, a] - ctx.elev[cand, b]
        have = valid[:, 0]
        for n in (8, 16):
            v = valid[:, :n]
            if screen:
                v = M.screen_outliers(xk[:, :n], yk[:, :n], z[:, :n], v, S["screen_k"], S["screen_min_m"])
            for lin in (False, True):
                for al in alphas:
                    for r in (0.03, 0.3, 3.0):
                        p, _, _, _ = M.krige(xk[:, :n], yk[:, :n], z[:, :n], v, al, r, drift_linear=lin)
                        th_res.setdefault((n, lin, al, r), []).append(np.abs(p - truth)[have])
    th_mae = {k: float(np.median(np.concatenate(v))) for k, v in th_res.items()}
    for k, v in th_mae.items():
        rows.append(dict(part="thickness kriging (consecutive layers pooled)", top="all layers pooled", screen=screen,
                         n=k[0], linear_drift=k[1], alpha=k[2], r=k[3], mae_m=v))
    kb = min(th_mae, key=lambda k: (th_mae[k], k))
    S["th_n"], S["th_linear"], S["th_alpha"], S["th_r"] = int(kb[0]), bool(kb[1]), float(kb[2]), float(kb[3])
    # ---- support radius of the thickness chain ---------------------------
    samp = pt if len(pt) <= cfg["tune_wells_m4"] else np.sort(rng.choice(pt, cfg["tune_wells_m4"], replace=False))
    cut = cut_all[[pos[w] for w in samp]]
    truth = ctx.elev[samp].copy()
    late = ~((ctx.avail[samp] < start_day) & (ctx.avail[samp] != NAT_DAY))
    truth[late] = np.nan
    r_res = {}
    for R in cfg.get("radius_grid_m", [10000.0, 30000.0]):
        S["support_radius_m"] = float(R)
        f, _ = forecast_wells(ctx, samp, cut, S)
        okk = np.isfinite(truth) & np.isfinite(f["m4"])
        r_res[R] = float(np.median(np.abs(f["m4"] - truth)[okk]))
        rows.append(dict(part="method 4 support radius", top="all chosen tops pooled", screen=screen, radius_m=R,
                         n_items=int(okk.sum()), mae_m=r_res[R]))
    S["support_radius_m"] = float(min(r_res, key=lambda R: (r_res[R], R)))
    f, _ = forecast_wells(ctx, samp, cut, S)
    okk = np.isfinite(truth) & np.isfinite(f["m3"])
    pre = {}
    for mth, key in zip(METHODS, ["m1", "m2", "m3", "m4"]):
        e = np.abs(f[key] - truth)[okk]
        far = (f["d1"] > FAR_M)[okk]
        pre[mth] = dict(n_items=int(okk.sum()), mae_m=float(np.median(e)), p90_m=float(np.percentile(e, 90)),
                        n_far=int(far.sum()), mae_far_m=float(np.median(e[far])) if far.any() else None)
    cov = (np.abs(f["m3"] - truth) <= f["hw3"])[okk]
    S["pre_test_year_check"] = dict(wells=int(len(samp)), by_method=pre, m3_cover80=float(cov.mean()),
                                    note="pseudo-test on wells drilled before the test years, same date rule")
    pd.DataFrame(rows).to_csv(outdir / f"{c}_tuning_grid.csv", index=False)
    return S


# --------------------------------------------------------------------------
# floors
# --------------------------------------------------------------------------
def floor_a(ctx, hole_ok, precise):
    """Same top in two different holes less than 150 m apart."""
    rows = []
    for j, top in enumerate(ctx.tops):
        ok = np.isfinite(ctx.elev[:, j]) & hole_ok
        h = np.nonzero(ok)[0]
        if len(h) < 2:
            continue
        tree = cKDTree(np.c_[ctx.x[h], ctx.y[h]])
        pr = tree.query_pairs(150.0, output_type="ndarray")
        if len(pr) == 0:
            continue
        a, b = h[pr[:, 0]], h[pr[:, 1]]
        d = np.hypot(ctx.x[a] - ctx.x[b], ctx.y[a] - ctx.y[b])
        keep = d < 150.0
        a, b, d = a[keep], b[keep], d[keep]
        rows.append(pd.DataFrame(dict(top=top, hole_a=a, hole_b=b, dist_m=d,
                                      abs_diff_m=np.abs(ctx.elev[a, j] - ctx.elev[b, j]),
                                      both_precise=precise[a] & precise[b])))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(
        columns=["top", "hole_a", "hole_b", "dist_m", "abs_diff_m", "both_precise"])


def summarise_floor(pairs, label):
    out = []
    def one(df, top):
        if len(df) == 0:
            return dict(floor=label, top=top, n_pairs=0, n_hole_pairs=0)
        hp = len(set(zip(df["hole_a"], df["hole_b"])))
        return dict(floor=label, top=top, n_pairs=len(df), n_hole_pairs=hp,
                    median_abs_diff_m=float(df["abs_diff_m"].median()),
                    p90_abs_diff_m=float(df["abs_diff_m"].quantile(0.9)),
                    share_zero=float((df["abs_diff_m"] == 0).mean()))
    out.append(one(pairs, "all chosen tops"))
    for top, g in pairs.groupby("top", sort=False):
        out.append(one(g, top))
    return out


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------
def boot_stats(abs_err, well, counts):
    """Median and 90th percentile with well-resampled 95 % intervals.
    abs_err: (n,) or (n, k); well: (n,) codes; counts: (B, W) draws."""
    e = np.asarray(abs_err, float)
    if e.ndim == 1:
        e = e[:, None]
    n = len(e)
    if n == 0:
        return None
    med = np.median(e, axis=0)
    p90 = np.percentile(e, 90, axis=0)
    bm = np.full((len(counts), e.shape[1]), np.nan)
    bp = np.full((len(counts), e.shape[1]), np.nan)
    for i in range(len(counts)):
        rep = counts[i][well]
        if rep.sum() == 0:
            continue
        ee = np.repeat(e, rep, axis=0)
        bm[i] = np.median(ee, axis=0)
        bp[i] = np.percentile(ee, 90, axis=0)
    return med, p90, np.nanpercentile(bm, [2.5, 97.5], axis=0), np.nanpercentile(bp, [2.5, 97.5], axis=0), bm


def score(items, ctx, outdir, c, tag, feet=False, n_boot=N_BOOT):
    """items: DataFrame with hole, top, actual, d1, m1..m4, hw3."""
    rng = np.random.default_rng(SEED + 1)
    wells, wcode = np.unique(items["hole"].to_numpy(), return_inverse=True)
    Wn = len(wells)
    counts = rng.multinomial(Wn, np.full(Wn, 1.0 / Wn), size=n_boot).astype(np.int32)
    err = np.column_stack([items[k].to_numpy() - items["actual"].to_numpy() for k in ["m1", "m2", "m3", "m4"]])
    ae = np.abs(err)
    band = band_of(items["d1"].to_numpy())
    far = items["d1"].to_numpy() > FAR_M
    cells = [("all items", np.ones(len(items), bool)), ("far (>1 km)", far)]
    cells += [(BANDS[i][2], band == i) for i in range(len(BANDS))]
    rows = []
    far_boot = None
    for name, mk in cells:
        if mk.sum() == 0:
            for k, mth in enumerate(METHODS):
                rows.append(dict(cell=name, method=mth, n_items=0, n_wells=0))
            continue
        r = boot_stats(ae[mk], wcode[mk], counts)
        med, p90, cim, cip, bm = r
        if name == "far (>1 km)":
            far_boot = bm
        for k, mth in enumerate(METHODS):
            rows.append(dict(cell=name, method=mth, n_items=int(mk.sum()), n_wells=int(len(np.unique(wcode[mk]))),
                             mae_m=med[k], mae_ci_lo_m=cim[0, k], mae_ci_hi_m=cim[1, k],
                             p90_m=p90[k], p90_ci_lo_m=cip[0, k], p90_ci_hi_m=cip[1, k],
                             median_signed_error_m=float(np.median(err[mk][:, k]))))
    by_band = pd.DataFrame(rows)
    rows = []
    tcode = items["top"].to_numpy()
    for j, top in enumerate(ctx.tops):
        for name, mk in [("all items", tcode == j), ("far (>1 km)", (tcode == j) & far)]:
            if mk.sum() == 0:
                continue
            med, p90, cim, cip, _ = boot_stats(ae[mk], wcode[mk], counts)
            for k, mth in enumerate(METHODS):
                rows.append(dict(top=top, cell=name, method=mth, n_items=int(mk.sum()), n_wells=int(len(np.unique(wcode[mk]))),
                                 mae_m=med[k], mae_ci_lo_m=cim[0, k], mae_ci_hi_m=cim[1, k],
                                 p90_m=p90[k], p90_ci_lo_m=cip[0, k], p90_ci_hi_m=cip[1, k]))
    by_top = pd.DataFrame(rows)
    # coverage of the 80 % range of method 3
    inside = np.abs(err[:, 2]) <= items["hw3"].to_numpy()
    rows = []
    for name, mk in cells:
        if mk.sum() == 0:
            rows.append(dict(cell=name, n_items=0))
            continue
        bc = []
        for i in range(n_boot):
            rep = counts[i][wcode[mk]]
            if rep.sum():
                bc.append(np.average(inside[mk], weights=rep))
        rows.append(dict(cell=name, n_items=int(mk.sum()), n_wells=int(len(np.unique(wcode[mk]))),
                         share_inside_80pct_range=float(inside[mk].mean()),
                         ci_lo=float(np.percentile(bc, 2.5)), ci_hi=float(np.percentile(bc, 97.5)),
                         median_half_width_m=float(np.median(items["hw3"].to_numpy()[mk]))))
    cover = pd.DataFrame(rows)
    if feet:
        for df in (by_band, by_top):
            for col in [x for x in df.columns if x.endswith("_m")]:
                df[col[:-2] + "_ft"] = df[col] / 0.3048
    by_band.to_csv(outdir / f"{c}_scores_by_distance{tag}.csv", index=False)
    by_top.to_csv(outdir / f"{c}_scores_by_top{tag}.csv", index=False)
    cover.to_csv(outdir / f"{c}_m3_range_coverage{tag}.csv", index=False)
    return by_band, by_top, cover, far_boot


def make_items(ctx, widx, f, truth):
    """Long table of test items: one chosen top in one test well."""
    wi, tj = np.nonzero(np.isfinite(truth))
    df = pd.DataFrame(dict(hole=widx[wi], top=tj, actual=truth[wi, tj], d1=f["d1"][wi, tj]))
    for k in ["m1", "m2", "m3", "m4", "hw3"]:
        df[k] = f[k][wi, tj]
    df["anchor"] = f["anchor"][wi, tj]
    df["chain"] = f["chain"][wi, tj]
    df["wi"] = wi
    return df


def chart(by_band, floorA, country, path, unit_note=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans"})
    # dark surface, ink and grid; four categorical hues in fixed order (blue,
    # orange, aqua, yellow), checked for colour-blind separation of adjacent
    # series. Marker shape and dash pattern repeat the identity.
    bg, fg, fg2, grid = "#1a1a19", "#f0efec", "#c3c2b7", "#2c2c2a"
    cols = {"m1_nearest": "#3987e5", "m2_plane": "#d95926", "m3_kriging": "#199e70", "m4_thickness": "#c98500"}
    marks = {"m1_nearest": "o", "m2_plane": "s", "m3_kriging": "^", "m4_thickness": "D"}
    dashes = {"m1_nearest": "-", "m2_plane": (0, (6, 2)), "m3_kriging": "-", "m4_thickness": (0, (2, 2))}
    fig, ax = plt.subplots(figsize=(9.5, 5.6), dpi=160)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    names = [b[2] for b in BANDS]
    xs = np.arange(len(names))
    ymax = 0
    for mth in METHODS:
        d = by_band[by_band["method"] == mth].set_index("cell").reindex(names)
        y = d["mae_m"].to_numpy(float)
        lo = d["mae_ci_lo_m"].to_numpy(float)
        hi = d["mae_ci_hi_m"].to_numpy(float)
        ax.plot(xs, y, color=cols[mth], marker=marks[mth], ls=dashes[mth], lw=2, ms=7, markeredgecolor=bg,
                markeredgewidth=1.2, label=METHOD_LABEL[mth], zorder=3)
        ax.fill_between(xs, lo, hi, color=cols[mth], alpha=0.14, lw=0, zorder=2)
        ymax = max(ymax, np.nanmax(hi))
    if floorA is not None and np.isfinite(floorA):
        ax.axhline(floorA, color=fg2, lw=1.4, ls=(0, (1, 2)), zorder=1, label=f"Floor A = {floorA:.2f} m")
    n_items = by_band[by_band["method"] == METHODS[0]].set_index("cell").reindex(names)["n_items"].fillna(0).astype(int)
    n_wells = by_band[by_band["method"] == METHODS[0]].set_index("cell").reindex(names)["n_wells"].fillna(0).astype(int)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{n}\n{n_items[n]:,} items\n{n_wells[n]:,} wells" for n in names], color=fg2, fontsize=9)
    ax.set_yscale("log")
    ax.set_ylabel("Median absolute error, metres (log scale)", color=fg2)
    ax.set_xlabel("Distance to the nearest known well that has the top", color=fg2)
    ax.set_title(f"{country}: miss of simple mapping methods against distance (development period)\n"
                 f"shaded: 95 % interval from resampling wells{unit_note}", color=fg, fontsize=11, loc="left")
    ax.tick_params(colors=fg2, which="both")
    for s in ax.spines.values():
        s.set_color(grid)
    ax.grid(True, which="major", color=grid, lw=0.8)
    ax.grid(True, which="minor", color=grid, lw=0.3)
    ax.set_axisbelow(True)
    from matplotlib.ticker import ScalarFormatter
    ax.yaxis.set_major_formatter(ScalarFormatter())
    leg = ax.legend(facecolor=bg, edgecolor=grid, labelcolor=fg, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, facecolor=bg)
    plt.close(fig)


# --------------------------------------------------------------------------
# main driver for one country
# --------------------------------------------------------------------------
def run_country(cfg, holes, picks, log, extra, outdir, cachedir):
    c = cfg["code"]
    outdir.mkdir(exist_ok=True)
    cachedir.mkdir(exist_ok=True)
    summary = {"country": cfg["name"]}
    holes = holes.reset_index(drop=True)

    # ---- chosen tops: the 12 most reported in holes drilled before the test years
    pre_ids = set(holes.loc[holes["pre_test"], "hole_id"])
    cnt = picks[picks["hole_id"].isin(pre_ids)].groupby("top")["hole_id"].nunique().sort_values(ascending=False)
    if cfg.get("top_filter") is not None:
        cnt = cnt[cnt.index.map(cfg["top_filter"])]
    cnt_df = cnt.head(30).rename("holes_before_test_years").reset_index()
    cnt_df["chosen"] = np.arange(len(cnt_df)) < 12
    chosen = list(cnt.index[:12])
    # stratigraphic order from holes drilled before the test years
    pv = picks[picks["hole_id"].isin(pre_ids) & picks["top"].isin(chosen)].pivot(index="hole_id", columns="top", values="elev_m")
    wins = {a: 0.0 for a in chosen}
    for a in chosen:
        for b in chosen:
            if a != b:
                d = (pv[a] - pv[b]).dropna()
                if len(d):
                    wins[a] += float((d > 0).mean())
                else:
                    wins[a] += 0.5
    chosen = sorted(chosen, key=lambda a: (-wins[a], a))
    cnt_df["order_top_down"] = cnt_df["top"].map({t: i + 1 for i, t in enumerate(chosen)})
    cnt_df.to_csv(outdir / f"{c}_chosen_tops.csv", index=False)
    summary["chosen_tops_top_down"] = chosen

    # ---- split, from counts only -----------------------------------------
    has_chosen = set(picks.loc[picks["top"].isin(chosen), "hole_id"])
    test = holes[holes["eligible"] & holes["hole_id"].isin(has_chosen) & holes["test_date"].notna()].copy()
    test = test.sort_values(["test_date", "hole_id"]).reset_index(drop=True)
    cut_date = test["test_date"].iloc[len(test) // 2]
    test["period"] = np.where(test["test_date"] < cut_date, "development", "sealed")
    sealed_ids = set(test.loc[test["period"] == "sealed", "hole_id"])
    dev_ids = list(test.loc[test["period"] == "development", "hole_id"])
    test[["hole_id", "test_date", "period"]].to_csv(outdir / f"{c}_split.csv", index=False)
    test.loc[test["period"] == "sealed", ["hole_id", "test_date"]].to_csv(outdir / f"{c}_sealed_wells.csv", index=False)
    (outdir / f"{c}_cut_date.txt").write_text(
        f"cut date: {cut_date.date()}\n"
        f"test wells: {len(test)}\ndevelopment (test date before the cut date): {len(dev_ids)}\n"
        f"sealed (test date on or after the cut date): {len(sealed_ids)}\n"
        f"test date = {cfg['test_date_meaning']}\n")
    summary.update(cut_date=str(cut_date.date()), n_test=len(test), n_dev=len(dev_ids), n_sealed=len(sealed_ids))

    # presence table (which hole reports which top, and when): counting only
    presence = picks.loc[picks["top"].isin(chosen), ["hole_id", "top", "avail"]].copy()
    # ---- from here on, no depth of a sealed well exists in memory ---------
    picks_known = picks[~picks["hole_id"].isin(sealed_ids)].copy()
    del picks
    ctx = Ctx(cfg, holes, picks_known, chosen)
    h = ctx.holes
    is_sealed = h["hole_id"].isin(sealed_ids).to_numpy()
    assert not np.isfinite(ctx.elev[is_sealed]).any()

    # ---- settings from wells drilled before the test years ----------------
    S = tune(ctx, cfg, outdir)
    (outdir / f"{c}_settings.json").write_text(json.dumps(S, indent=1, default=float))

    # ---- development forecasts -------------------------------------------
    widx = np.array([ctx.hid[i] for i in dev_ids], dtype=np.int64)
    truth = ctx.elev[widx].copy()
    rule = h["rule_date"].to_numpy()[widx]
    variants = {"": cfg["wait"], "_no_wait": None}
    results = {}
    for tag, wait in variants.items():
        cut = cutoff_days(rule, wait)
        f, audit = forecast_wells(ctx, widx, cut, S, keep_audit=True)
        items = make_items(ctx, widx, f, truth)
        n_all = len(items)
        items = items[np.isfinite(items["m1"])].reset_index(drop=True)
        results[tag] = dict(f=f, items=items, n_no_known=n_all - len(items), cut=cut, audit=audit)
        save_audit(cachedir / f"{c}_audit{tag}.npz", ctx, widx, cut, audit, items, S, tag)

    # ---- floors ------------------------------------------------------------
    precise = h["loc_precise"].to_numpy(bool)
    pairsA = floor_a(ctx, ~is_sealed, precise)
    fl = summarise_floor(pairsA[pairsA["both_precise"]], "A: two holes under 150 m apart, both positions precise (used in pass marks)")
    fl += summarise_floor(pairsA, "A-all: two holes under 150 m apart, any position quality")
    clean = (h["flag_elev"] == "").to_numpy()
    pc = pairsA[pairsA["both_precise"] & clean[pairsA["hole_a"].to_numpy(int)] & clean[pairsA["hole_b"].to_numpy(int)]] if len(pairsA) else pairsA
    fl += summarise_floor(pc, "A-clean: as A, both holes without an elevation flag")
    pb = extra.get("floor_b_pairs")
    if pb is not None:
        pb = pb[pb["top"].isin(chosen) & ~pb["hole_id"].isin(sealed_ids)]
        d = pb["abs_diff_m"]
        fl.append(dict(floor="B: two picks of one top in one hole from different sources", top="all chosen tops",
                       n_pairs=len(pb), n_hole_pairs=pb["hole_id"].nunique(),
                       median_abs_diff_m=float(d.median()) if len(pb) else np.nan,
                       p90_abs_diff_m=float(d.quantile(0.9)) if len(pb) else np.nan,
                       share_zero=float((d == 0).mean()) if len(pb) else np.nan,
                       median_abs_diff_nonzero_m=float(d[d > 0].median()) if (d > 0).any() else np.nan))
        for top, g in pb.groupby("top"):
            dd = g["abs_diff_m"]
            fl.append(dict(floor="B: two picks of one top in one hole from different sources", top=top, n_pairs=len(g),
                           n_hole_pairs=g["hole_id"].nunique(), median_abs_diff_m=float(dd.median()),
                           p90_abs_diff_m=float(dd.quantile(0.9)), share_zero=float((dd == 0).mean()),
                           median_abs_diff_nonzero_m=float(dd[dd > 0].median()) if (dd > 0).any() else np.nan))
    floors = pd.DataFrame(fl)
    if cfg.get("feet"):
        for col in [x for x in floors.columns if x.endswith("_m")]:
            floors[col[:-2] + "_ft"] = floors[col] / 0.3048
    floors.to_csv(outdir / f"{c}_floors.csv", index=False)
    fA = floors[(floors["floor"].str.startswith("A:")) & (floors["top"] == "all chosen tops")].iloc[0]
    floorA = float(fA.get("median_abs_diff_m", np.nan)) if fA["n_pairs"] else np.nan
    nA = int(fA["n_pairs"])
    summary.update(floor_a_m=floorA, floor_a_pairs=nA, floor_a_hole_pairs=int(fA["n_hole_pairs"]),
                   floor_a_reliable=bool(nA >= 50))
    fB = floors[floors["floor"].str.startswith("B:") & (floors["top"] == "all chosen tops")]
    if len(fB):
        summary.update(floor_b_m=float(fB.iloc[0]["median_abs_diff_m"]), floor_b_pairs=int(fB.iloc[0]["n_pairs"]),
                       floor_b_share_zero=float(fB.iloc[0]["share_zero"]))

    # ---- scoring (development period only) --------------------------------
    for tag in variants:
        items = results[tag]["items"]
        by_band, by_top, cover, far_boot = score(items, ctx, outdir, c, tag, feet=cfg.get("feet", False))
        results[tag].update(by_band=by_band, by_top=by_top, cover=cover, far_boot=far_boot)
        out = items.drop(columns=["wi"]).copy()
        out.insert(0, "hole_id", h["hole_id"].to_numpy()[out["hole"].to_numpy()])
        out["top"] = [chosen[j] for j in out["top"]]
        out["anchor"] = [chosen[j] for j in out["anchor"]]
        out["chain"] = [" > ".join(chosen[b] for b in range(ctx.T) if (m >> b) & 1) for m in out["chain"]]
        out = out.drop(columns=["hole"]).rename(columns={
            "actual": "actual_elev_m", "d1": "dist_nearest_known_m", "m1": "m1_nearest_m", "m2": "m2_plane_m",
            "m3": "m3_kriging_m", "m4": "m4_thickness_m", "hw3": "m3_half_width_80pct_m",
            "anchor": "m4_anchor_top", "chain": "m4_chain"})
        if cfg.get("feet"):
            out["actual_elev_ft"] = out["actual_elev_m"] / 0.3048
        out.round(3).to_csv(outdir / f"{c}_dev_items{tag}.csv.gz", index=False,
                            compression={"method": "gzip", "mtime": 0})
    main = results[""]
    chart(main["by_band"], floorA if nA else None, cfg["name"], outdir / f"{c}_error_vs_distance.png")

    # ---- sealed period: counts only ---------------------------------------
    sealed_far = count_far_sealed(ctx, cfg, presence, sorted(sealed_ids), chosen)
    sealed_far.to_csv(outdir / f"{c}_sealed_counts.csv", index=False)
    n_sealed_far = int(sealed_far.loc[sealed_far["what"] == "sealed wells with at least one far item", "count"].iloc[0])

    # ---- pass marks --------------------------------------------------------
    bb = main["by_band"]
    farrow = bb[bb["cell"] == "far (>1 km)"].set_index("method")
    best = farrow["mae_m"].astype(float).idxmin()
    best_mae = float(farrow.loc[best, "mae_m"])
    n_far_wells = int(farrow.loc[best, "n_wells"])
    a_ok = bool(n_far_wells >= 300 and n_sealed_far >= 300)
    ratio = best_mae / floorA if (nA and floorA > 0) else np.nan
    k = METHODS.index(best)
    rb = main["far_boot"][:, k] / floorA if (nA and floorA > 0) else np.array([np.nan])
    b_state = "not judged (floor A unreliable)" if nA < 50 else ("pass" if ratio >= 2 else "fail")
    summary.update(far_dev_wells=n_far_wells, far_dev_items=int(farrow.loc[best, "n_items"]), far_sealed_wells=n_sealed_far,
                   pass_a=a_ok, best_method_far=best, best_far_mae_m=best_mae,
                   best_far_mae_ci_m=[float(farrow.loc[best, "mae_ci_lo_m"]), float(farrow.loc[best, "mae_ci_hi_m"])],
                   far_mae_by_method_m={m: float(farrow.loc[m, "mae_m"]) for m in METHODS},
                   ratio_best_far_to_floor_a=float(ratio),
                   ratio_ci_wells_resampled_floor_fixed=[float(np.nanpercentile(rb, 2.5)), float(np.nanpercentile(rb, 97.5))],
                   pass_b=b_state,
                   verdict=("pass" if (a_ok and b_state == "pass") else
                            ("not judged" if (a_ok and b_state.startswith("not judged")) else "fail")),
                   items_dev=int(len(main["items"])), wells_dev_scored=int(main["items"]["hole"].nunique()),
                   items_dev_without_any_known_well=int(main["n_no_known"]),
                   no_wait_far_mae_m={m: float(results["_no_wait"]["by_band"].query("cell=='far (>1 km)'").set_index("method").loc[m, "mae_m"]) for m in METHODS},
                   no_wait_all_mae_m={m: float(results["_no_wait"]["by_band"].query("cell=='all items'").set_index("method").loc[m, "mae_m"]) for m in METHODS},
                   all_mae_m={m: float(bb.query("cell=='all items'").set_index("method").loc[m, "mae_m"]) for m in METHODS})

    # ---- side run: holes without flags only -------------------------------
    cleanmask = ((h["flag_elev"] == "") & h["loc_precise"]).to_numpy()
    if cfg.get("clean_side_run", True) and (~cleanmask).any():
        wc = widx[cleanmask[widx]]
        cut = cutoff_days(h["rule_date"].to_numpy()[wc], cfg["wait"])
        f, _ = forecast_wells(ctx, wc, cut, S, mask=cleanmask)
        it = make_items(ctx, wc, f, ctx.elev[wc])
        it = it[np.isfinite(it["m1"])].reset_index(drop=True)
        bbc, _, _, _ = score(it, ctx, outdir, c, "_unflagged_only", feet=cfg.get("feet", False), n_boot=200)
        fr = bbc[bbc["cell"] == "far (>1 km)"].set_index("method")
        fAc = floors[(floors["floor"].str.startswith("A-clean")) & (floors["top"] == "all chosen tops")].iloc[0]
        summary["unflagged_only"] = dict(
            far_mae_m={m: float(fr.loc[m, "mae_m"]) for m in METHODS}, far_wells=int(fr["n_wells"].iloc[0]),
            far_items=int(fr["n_items"].iloc[0]), floor_a_clean_m=float(fAc.get("median_abs_diff_m", np.nan)),
            floor_a_clean_pairs=int(fAc["n_pairs"]))

    # ---- spot-check sheet ---------------------------------------------------
    spot_check(ctx, main, widx, S, outdir / f"{c}_spot_check.csv", chosen, cfg)

    log.to_csv(outdir / f"{c}_cleaning_log.csv", index=False)
    for k_, name in [("name_map", "name_map"), ("variant_evidence", "name_map_evidence")]:
        if extra.get(k_) is not None:
            extra[k_].to_csv(outdir / f"{c}_{name}.csv", index=False)
    summary["settings"] = S
    (outdir / f"{c}_summary.json").write_text(json.dumps(summary, indent=1, default=float))
    return summary


def count_far_sealed(ctx, cfg, presence, sealed_ids, chosen):
    """Sealed wells with at least one far item. Uses positions, dates and
    which tops each hole reports. No depth is read."""
    h = ctx.holes
    pres = presence.copy()
    pres["h"] = pres["hole_id"].map(ctx.hid)
    pres["day"] = to_day(pres["avail"])
    sidx = np.array([ctx.hid[i] for i in sealed_ids], dtype=np.int64)
    spos = {w: i for i, w in enumerate(sidx)}
    cut = cutoff_days(h["rule_date"].to_numpy()[sidx], cfg["wait"])
    far_any = np.zeros(len(sidx), bool)
    n_items = n_far = n_none = 0
    band_counts = np.zeros(len(BANDS), int)
    for j, top in enumerate(chosen):
        p = pres[(pres["top"] == top)]
        pk = p[p["day"] != NAT_DAY]
        pool = M.Pool(pk["h"].to_numpy(), ctx.x[pk["h"]], ctx.y[pk["h"]], np.zeros(len(pk)), pk["day"].to_numpy())
        tw = np.array([w for w in p["h"].to_numpy() if w in spos], dtype=np.int64)
        if len(tw) == 0:
            continue
        rows = np.array([spos[w] for w in tw])
        _, dist = pool.known_neighbours(ctx.x[tw], ctx.y[tw], tw, cut[rows], 1)
        d = dist[:, 0]
        n_items += len(d)
        none = ~np.isfinite(d)
        n_none += int(none.sum())
        isfar = (d > FAR_M) & ~none
        n_far += int(isfar.sum())
        far_any[rows[isfar]] = True
        b = band_of(d[~none])
        for i in range(len(BANDS)):
            band_counts[i] += int((b == i).sum())
    rows = [dict(what="sealed wells", count=len(sidx)),
            dict(what="sealed items (chosen top reported in a sealed well)", count=n_items),
            dict(what="sealed far items (nearest known well with the top more than 1 km away)", count=n_far),
            dict(what="sealed items with no known well at all for the top", count=n_none),
            dict(what="sealed wells with at least one far item", count=int(far_any.sum()))]
    rows += [dict(what=f"sealed items, nearest known well {BANDS[i][2]}", count=int(band_counts[i])) for i in range(len(BANDS))]
    return pd.DataFrame(rows)


def save_audit(path, ctx, widx, cut, audit, items, S, tag):
    """Everything the date-rule test needs: for each forecast, the records of
    the known wells that were used."""
    T = ctx.T
    d = dict(widx=widx, cut=cut, test_rule_day=to_day(ctx.holes["rule_date"].to_numpy()[widx]),
             item_w=items["wi"].to_numpy(), item_top=items["top"].to_numpy(), item_chain=items["chain"].to_numpy(),
             item_anchor=items["anchor"].to_numpy(), T=T, n2=S["m2_n"], nt=S["th_n"],
             n3=np.array([S["m3"][t]["n"] for t in ctx.tops]))
    hole_ids = ctx.holes["hole_id"].to_numpy().astype(str)
    d["test_hole_id"] = hole_ids[widx]
    for j in range(T):
        ph, idx, dist, _ = audit["top_idx"][j]
        hh = np.where(idx >= 0, ph[np.where(idx >= 0, idx, 0)], -1)
        d[f"top{j}_hole"] = hh.astype(np.int32)
    for (a, b), (ph, idx, dist) in audit["link_idx"].items():
        hh = np.where(idx >= 0, ph[np.where(idx >= 0, idx, 0)], -1)
        d[f"link{a}_{b}_hole"] = hh.astype(np.int32)
    d["rec"] = ctx.rec.astype(str)
    d["avail"] = ctx.avail
    d["hole_ids"] = hole_ids
    np.savez_compressed(path, **d)


def spot_check(ctx, main, widx, S, path, chosen, cfg):
    rng = np.random.default_rng(SEED + 2)
    items = main["items"]
    audit = main["audit"]
    pick = np.sort(rng.choice(len(items), size=min(20, len(items)), replace=False))
    h = ctx.holes
    hid = h["hole_id"].to_numpy()
    rows = []
    epoch = np.datetime64("1970-01-01")
    def day(dn):
        return str(epoch + np.timedelta64(int(dn), "D"))
    for no, i in enumerate(pick, 1):
        it = items.iloc[i]
        w, j = int(it["wi"]), int(it["top"])
        hole = widx[w]
        base = dict(item=no, test_well=hid[hole], top=chosen[j], test_well_date=str(pd.Timestamp(h["rule_date"].iloc[hole]).date()),
                    latest_finish_date_allowed=day(main["cut"][w]),
                    actual_elev_m=round(float(it["actual"]), 2))
        fc = dict(m1_nearest=it["m1"], m2_plane=it["m2"], m3_kriging=it["m3"], m4_thickness=it["m4"])
        def emit(method, role, ph, idx, dist, n, val=None, quantity=None):
            for kk in range(n):
                p = idx[w, kk]
                if p < 0:
                    continue
                kh = ph[p]
                a, b = quantity
                if b is None:
                    rec = ctx.rec[kh, a]
                    fin = ctx.avail[kh, a]
                    v = ctx.elev[kh, a]
                else:
                    rec = f"{ctx.rec[kh, a]}|{ctx.rec[kh, b]}"
                    fin = max(ctx.avail[kh, a], ctx.avail[kh, b])
                    v = ctx.elev[kh, a] - ctx.elev[kh, b]
                rows.append(dict(base, method=method, forecast_elev_m=round(float(fc[method]), 2),
                                 error_m=round(float(fc[method] - it["actual"]), 2), role=role,
                                 known_well=hid[kh], known_record=rec, known_finish_date=day(fin),
                                 distance_m=round(float(dist[w, kk]), 1), known_value_m=round(float(v), 2)))
        ph, idx, dist, _ = audit["top_idx"][j]
        emit("m1_nearest", f"elevation of {chosen[j]}", ph, idx, dist, 1, quantity=(j, None))
        emit("m2_plane", f"elevation of {chosen[j]}", ph, idx, dist, S["m2_n"], quantity=(j, None))
        emit("m3_kriging", f"elevation of {chosen[j]}", ph, idx, dist, S["m3"][chosen[j]]["n"], quantity=(j, None))
        chain = [b for b in range(ctx.T) if (int(it["chain"]) >> b) & 1]
        a0 = chain[0]
        ph, idx, dist, _ = audit["top_idx"][a0]
        emit("m4_thickness", f"start of chain: elevation of {chosen[a0]} (kriging)", ph, idx, dist, S["m3"][chosen[a0]]["n"], quantity=(a0, None))
        for a, b in zip(chain[:-1], chain[1:]):
            ph, idx, dist = audit["link_idx"][(a, b)]
            emit("m4_thickness", f"thickness {chosen[a]} to {chosen[b]}", ph, idx, dist, S["th_n"], quantity=(a, b))
    pd.DataFrame(rows).to_csv(path, index=False)
