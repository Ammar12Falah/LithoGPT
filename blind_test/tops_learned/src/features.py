"""Features for the learned model. One item = one chosen layer in one well,
forecast at that well's own date.

Everything is built from
  - the known wells of the test well under the first run's date rule
    (through first-run code: pipeline.forecast_wells and Pool.known_neighbours,
    both of which take the cut-off day of each row),
  - the outputs of the first run's simple methods,
  - the test well's own position and date, and the layer.
The test well's own picks are used for one thing only: the target (actual
elevation), which is kept apart from the feature table.

Feature groups (column `group` in the feature list):
  position   x, y of the forecast point; layer
  date       date of the test well; ages of the nearest known wells
  distance   distances to known wells of this layer, of other layers, and of
             wells that report this layer together with another one
  count      how many known wells are near
  direction  where the nearest known wells lie (east/north offsets, gap)
  depth      anything computed from depth values of known wells: outputs of
             the simple methods, values of neighbours, other layers, routes
The drift-only model D uses position, date, distance and count only.
"""
import numpy as np
import pandas as pd

import safe_load as SL
from safe_load import methods as M, pipeline as P

KN = 32          # known wells of the item's own layer that are looked at
K8 = 8           # of which the nearest 8 are given one by one
RADII = [500.0, 1000.0, 2000.0, 5000.0, 10000.0, 20000.0]


class Audit:
    """Every known well behind every feature, for the date-rule test and the
    own-pick test. A block is (rows, hole matrix, top columns): each hole in
    the matrix supplied a value of each of those tops to the item or row."""

    def __init__(self):
        self.blocks = []

    def add(self, name, test_hole, cut, holes, tops):
        self.blocks.append(dict(name=name, test_hole=np.asarray(test_hole), cut=np.asarray(cut),
                                holes=np.asarray(holes, dtype=np.int64), tops=tuple(tops)))


def _holes_of(pool, idx):
    return np.where(idx >= 0, pool.hole_idx[np.where(idx >= 0, idx, 0)], -1)


def build(ctx, cfg, S, wells, audit=None):
    """Items and features for test wells `wells` (hole indices).

    Returns (items, X): items holds ids, the target and the simple-method
    forecasts; X holds the features, same row order.
    """
    h = ctx.holes
    T = ctx.T
    rh, rt, rx, ry = P.build_rows(ctx, wells)
    rule = h["rule_date"].to_numpy()[rh]
    cut = P.cutoff_days(rule, cfg["wait"])
    tday = P.to_day(pd.Series(rule))
    f, aud = P.forecast_wells(ctx, rh, cut, S, keep_audit=True, tx=rx, ty=ry)
    items = P.make_items(ctx, rh, f, ctx.elev[rh], rt)
    items = items[np.isfinite(items["m1"])].reset_index(drop=True)
    wi = items["wi"].to_numpy()
    k = items["top"].to_numpy()
    n = len(items)
    ih, icut, iday, ix, iy = rh[wi], cut[wi], tday[wi], rx[wi], ry[wi]
    m3 = items["m3"].to_numpy()
    if audit is not None:
        used = np.unique(wi)
        for j in range(T):
            ph, idx, _, _ = aud["top_idx"][j]
            audit.add(f"simple methods, layer {j}", rh[used], cut[used], _holes_of_ph(ph, idx[used]), [j])
        for (a, b), (ph, idx, _) in aud["link_idx"].items():
            audit.add(f"thickness {a}-{b} (first-run method 4)", rh[used], cut[used], _holes_of_ph(ph, idx[used]), [a, b])

    X = {}
    # ---- position, date, layer ---------------------------------------------
    X["layer"] = k.astype(float)
    X["x_km"] = ix / 1000.0
    X["y_km"] = iy / 1000.0
    X["year"] = 1970.0 + iday / 365.25
    # ---- outputs of the simple methods (relative to kriging) ---------------
    var3 = f["var3"][wi, k]
    sd3 = np.sqrt(np.maximum(var3, 0))
    X["m3_elev"] = m3
    X["sd3"] = sd3
    X["hw3"] = items["hw3"].to_numpy()
    X["m1_rel"] = items["m1"].to_numpy() - m3
    X["m2_rel"] = items["m2"].to_numpy() - m3
    X["m4_rel"] = items["m4"].to_numpy() - m3
    X["m4b_rel"] = items["m4b"].to_numpy() - m3
    X["log_d1"] = np.log10(items["d1"].to_numpy() + 1.0)
    # ---- known wells of the item's own layer --------------------------------
    nb = {name: np.full((n, K8), np.nan) for name in ["ld", "dx", "dy", "rel", "age"]}
    agg = {name: np.full(n, np.nan) for name in
           ["ld_last", "age_mean", "age_min", "age_max", "rel_mean", "rel_std", "rel_min", "rel_max",
            "grad_m_per_km", "grad_dir_x", "grad_dir_y", "centroid_km", "centroid_ratio", "max_gap_deg", "n_known"]}
    cnt = {r: np.full(n, np.nan) for r in RADII}
    for j in range(T):
        sel = np.nonzero(k == j)[0]
        if len(sel) == 0:
            continue
        pool = ctx.pool(j)
        idx, dist = pool.known_neighbours(ix[sel], iy[sel], ih[sel], icut[sel], KN)
        if audit is not None:
            audit.add(f"neighbours of own layer {j}", ih[sel], icut[sel], _holes_of(pool, idx), [j])
        valid = idx >= 0
        safe = np.where(valid, idx, 0)
        dxk = np.where(valid, (pool.x[safe] - ix[sel][:, None]) / 1000.0, np.nan)
        dyk = np.where(valid, (pool.y[safe] - iy[sel][:, None]) / 1000.0, np.nan)
        rel = np.where(valid, pool.val[safe] - m3[sel][:, None], np.nan)
        age = np.where(valid, (iday[sel][:, None] - pool.avail[safe]) / 365.25, np.nan)
        dm = np.where(valid, dist, np.nan)
        nb["ld"][sel] = np.log10(dm[:, :K8] + 1.0)
        nb["dx"][sel] = dxk[:, :K8]
        nb["dy"][sel] = dyk[:, :K8]
        nb["rel"][sel] = rel[:, :K8]
        nb["age"][sel] = age[:, :K8]
        for r in RADII:
            cnt[r][sel] = (dm <= r).sum(axis=1)
        with np.errstate(all="ignore"):
            agg["n_known"][sel] = valid.sum(1)
            agg["ld_last"][sel] = np.log10(np.nanmax(dm, axis=1) + 1.0)
            agg["age_mean"][sel] = np.nanmean(age[:, :K8], axis=1)
            agg["age_min"][sel] = np.nanmin(age[:, :K8], axis=1)
            agg["age_max"][sel] = np.nanmax(age[:, :K8], axis=1)
            agg["rel_mean"][sel] = np.nanmean(rel[:, :K8], axis=1)
            agg["rel_std"][sel] = np.nanstd(rel[:, :K8], axis=1)
            agg["rel_min"][sel] = np.nanmin(rel[:, :K8], axis=1)
            agg["rel_max"][sel] = np.nanmax(rel[:, :K8], axis=1)
            cx = np.nanmean(dxk[:, :K8], axis=1)
            cy = np.nanmean(dyk[:, :K8], axis=1)
            agg["centroid_km"][sel] = np.hypot(cx, cy)
            agg["centroid_ratio"][sel] = np.hypot(cx, cy) / np.maximum(np.nanmean(dm[:, :K8], axis=1) / 1000.0, 1e-6)
        # local dip from a plane through the nearest 8
        v8 = valid[:, :K8]
        w8 = v8.astype(float)
        F = np.stack([w8, np.nan_to_num(dxk[:, :K8]) * w8, np.nan_to_num(dyk[:, :K8]) * w8], axis=2)
        A = np.einsum("bni,bnj->bij", F, F) + 1e-9 * np.eye(3)
        bvec = np.einsum("bni,bn->bi", F, np.nan_to_num(rel[:, :K8]) * w8)
        coef = np.linalg.solve(A, bvec[:, :, None])[:, :, 0]
        ok = v8.sum(1) >= 3
        g = np.hypot(coef[:, 1], coef[:, 2])
        agg["grad_m_per_km"][sel] = np.where(ok, g, np.nan)
        agg["grad_dir_x"][sel] = np.where(ok & (g > 0), coef[:, 1] / np.maximum(g, 1e-12), np.nan)
        agg["grad_dir_y"][sel] = np.where(ok & (g > 0), coef[:, 2] / np.maximum(g, 1e-12), np.nan)
        # largest angle around the test well with no known well among the nearest 8
        ang = np.degrees(np.arctan2(np.nan_to_num(dyk[:, :K8]), np.nan_to_num(dxk[:, :K8])))
        ang = np.where(v8 & (dm[:, :K8] > 0), ang, np.nan)
        s_ang = np.sort(ang, axis=1)                       # NaN last
        m_ = np.isfinite(s_ang).sum(1)
        gaps = np.diff(s_ang, axis=1)
        with np.errstate(all="ignore"):
            gmax = np.nanmax(np.where(np.isfinite(gaps), gaps, np.nan), axis=1)
            first = s_ang[:, 0]
            last = np.take_along_axis(s_ang, np.maximum(m_ - 1, 0)[:, None], axis=1)[:, 0]
            wrap = 360.0 - (last - first)
            agg["max_gap_deg"][sel] = np.where(m_ >= 2, np.fmax(gmax, wrap), 360.0)
    for i in range(K8):
        X[f"nb{i + 1}_log_dist"] = nb["ld"][:, i]
        X[f"nb{i + 1}_age_yr"] = nb["age"][:, i]
        X[f"nb{i + 1}_dx_km"] = nb["dx"][:, i]
        X[f"nb{i + 1}_dy_km"] = nb["dy"][:, i]
        X[f"nb{i + 1}_rel"] = nb["rel"][:, i]
    for r in RADII:
        X[f"n_within_{int(r)}m"] = cnt[r]
    for name, v in agg.items():
        X[f"own_{name}"] = v
    # ---- other layers at the same spot (forecasts from known wells only) ----
    for j in range(T):
        other = k != j
        X[f"L{j}_m3_rel"] = np.where(other, f["m3"][wi, j] - m3, np.nan)
        X[f"L{j}_log_d1"] = np.where(other, np.log10(f["d1"][wi, j] + 1.0), np.nan)
        X[f"L{j}_sd3"] = np.where(other, np.sqrt(np.maximum(f["var3"][wi, j], 0)), np.nan)
        X[f"L{j}_m1_rel"] = np.where(other, f["m1"][wi, j] - f["m3"][wi, j], np.nan)
    # ---- routes: kriging of another layer plus or minus a kriged thickness ---
    route = np.full((n, T), np.nan)
    rdist = np.full((n, T), np.nan)
    rcnt = np.full((n, T), np.nan)
    nt = S["th_n"]
    for a in range(T):
        for b in range(a + 1, T):
            sel = np.nonzero((k == a) | (k == b))[0]
            if len(sel) == 0:
                continue
            pool = ctx.pair_pool(a, b)
            if pool.n == 0:
                continue
            idx, dist = pool.known_neighbours(ix[sel], iy[sel], ih[sel], icut[sel], nt)
            if audit is not None:
                audit.add(f"route thickness {a}-{b}", ih[sel], icut[sel], _holes_of(pool, idx), [a, b])
            have = idx[:, 0] >= 0
            if not have.any():
                continue
            xk, yk, z, valid = M.gather(pool, idx[have], ix[sel][have], iy[sel][have])
            if S["screen"]:
                valid = M.screen_outliers(xk, yk, z, valid, S["screen_k"], S["screen_min_m"])
            th, _, _, _ = M.krige(xk, yk, z, valid, S["th_alpha"], S["th_r"], drift_linear=S["th_linear"])
            rows = sel[have]
            via = np.where(k[rows] == a, b, a)              # the other layer of the pair
            base = f["m3"][wi[rows], via]
            fc = np.where(k[rows] == a, base + th, base - th)
            route[rows, via] = fc - m3[rows]
            rdist[rows, via] = np.log10(dist[have, 0] + 1.0)
            rcnt[rows, via] = (dist[have] <= 10000.0).sum(axis=1)
    for j in range(T):
        X[f"L{j}_route_rel"] = route[:, j]
        X[f"L{j}_pair_log_d1"] = rdist[:, j]
        X[f"L{j}_pair_n_10km"] = rcnt[:, j]
    with np.errstate(all="ignore"):
        X["route_median_rel"] = np.nanmedian(route, axis=1)
        X["route_n"] = np.isfinite(route).sum(axis=1).astype(float)
        X["route_nearest_rel"] = np.where(np.isfinite(rdist).any(1),
                                          np.take_along_axis(route, np.nanargmin(np.where(np.isfinite(rdist), rdist, np.inf), axis=1)[:, None], axis=1)[:, 0],
                                          np.nan)
    X = pd.DataFrame(X)

    out = pd.DataFrame(dict(
        hole=ih, hole_id=h["hole_id"].to_numpy()[ih], top=k, top_name=np.array(ctx.tops, dtype=object)[k],
        test_day=iday, cut_day=icut, x=ix, y=iy, actual=items["actual"].to_numpy(),
        actual_day=ctx.avail[ih, k],                  # day the record with the actual value was finished (not a feature)
        d1=items["d1"].to_numpy(),
        m1=items["m1"].to_numpy(), m2=items["m2"].to_numpy(), m3=m3, m4=items["m4"].to_numpy(),
        m4b=items["m4b"].to_numpy(), hw3=items["hw3"].to_numpy(), sd3=sd3))
    return out, X


def _holes_of_ph(ph, idx):
    return np.where(idx >= 0, ph[np.where(idx >= 0, idx, 0)], -1)


def feature_groups(columns):
    """Group of every feature; the drift-only model takes position, date,
    distance and count."""
    g = {}
    for c in columns:
        if c in ("layer", "x_km", "y_km"):
            g[c] = "position"
        elif c == "year" or c.endswith("_age_yr") or c in ("own_age_mean", "own_age_min", "own_age_max"):
            g[c] = "date"
        elif c == "log_d1" or c.endswith("_log_dist") or c.endswith("_log_d1") or c == "own_ld_last":
            g[c] = "distance"
        elif c.startswith("n_within_") or c.endswith("_pair_n_10km") or c in ("own_n_known",):
            g[c] = "count"
        elif c.endswith("_dx_km") or c.endswith("_dy_km") or c in ("own_centroid_km", "own_centroid_ratio", "own_max_gap_deg"):
            g[c] = "direction"
        else:
            g[c] = "depth"
    return g


DRIFT_GROUPS = ("position", "date", "distance", "count")
