"""Forecast methods and helpers. Everything here works on plain numpy arrays.

Conventions
- Coordinates are projected metres. Inside the solvers they are re-centred on
  the test well and expressed in kilometres.
- Dates are integer day numbers (days since 1970-01-01).
- A "pool" is the set of holes that report one top (or one pair of tops),
  with the elevation (or thickness) and the day the hole was finished.
"""
import numpy as np
from scipy.spatial import cKDTree
from scipy.stats import t as student_t

BIG = 1.0e30


# --------------------------------------------------------------------------
# neighbour search under the date rule
# --------------------------------------------------------------------------
class Pool:
    """Holes that report one quantity: position, value, day finished."""

    def __init__(self, hole_idx, x, y, val, avail_day):
        self.hole_idx = np.asarray(hole_idx, dtype=np.int64)
        self.x = np.asarray(x, dtype=float)
        self.y = np.asarray(y, dtype=float)
        self.val = np.asarray(val, dtype=float)
        self.avail = np.asarray(avail_day, dtype=np.int64)
        self.n = len(self.hole_idx)
        self.tree = cKDTree(np.c_[self.x, self.y]) if self.n else None

    def known_neighbours(self, tx, ty, t_hole, cutoff_day, n_want):
        """Nearest n_want pool members that are known at each test well.

        A pool member is known for a test well if its finish day is on or
        before cutoff_day (already shifted by the waiting time) and it is not
        the test hole itself. Returns (idx, dist): shape (B, n_want), idx is a
        row number in the pool or -1, dist in metres (inf where idx is -1).
        Rows are ordered by distance, ties broken by pool row order.
        """
        B = len(tx)
        idx_out = np.full((B, n_want), -1, dtype=np.int64)
        dist_out = np.full((B, n_want), np.inf)
        if self.n == 0 or B == 0:
            return idx_out, dist_out
        todo = np.arange(B)
        k = min(self.n, max(2 * n_want, n_want + 8))
        pts = np.c_[tx, ty]
        while len(todo):
            d, i = self.tree.query(pts[todo], k=k)
            if k == 1:
                d = d[:, None]
                i = i[:, None]
            ok = i < self.n
            isafe = np.where(ok, i, 0)
            ok &= self.avail[isafe] <= cutoff_day[todo][:, None]
            ok &= self.hole_idx[isafe] != t_hole[todo][:, None]
            # stable order: distance, then pool row
            cnt = ok.sum(axis=1)
            done = (cnt >= n_want) | (k >= self.n)
            # compact the valid neighbours to the left, keeping distance order
            rank = np.cumsum(ok, axis=1) - 1
            for_rows = np.nonzero(done)[0]
            if len(for_rows):
                okd = ok[for_rows]
                rr, cc = np.nonzero(okd & (rank[for_rows] < n_want))
                dest = rank[for_rows][rr, cc]
                idx_out[todo[for_rows][rr], dest] = i[for_rows][rr, cc]
                dist_out[todo[for_rows][rr], dest] = d[for_rows][rr, cc]
            todo = todo[~done]
            k = min(self.n, k * 4)
        return idx_out, dist_out


# --------------------------------------------------------------------------
# method 2: local plane
# --------------------------------------------------------------------------
def _degenerate(xk, yk, w):
    """True where the valid points do not span a plane (fewer than 3 points,
    or all on one line / one spot)."""
    n = w.sum(axis=1)
    nn = np.maximum(n, 1)
    mx = (w * xk).sum(1) / nn
    my = (w * yk).sum(1) / nn
    dx = (xk - mx[:, None]) * w
    dy = (yk - my[:, None]) * w
    sxx = (dx * dx).sum(1)
    syy = (dy * dy).sum(1)
    sxy = (dx * dy).sum(1)
    tr = sxx + syy
    det = sxx * syy - sxy * sxy
    lam_min = tr / 2 - np.sqrt(np.maximum(tr * tr / 4 - det, 0))
    lam_max = tr / 2 + np.sqrt(np.maximum(tr * tr / 4 - det, 0))
    # smallest spread under 10 m RMS, or aspect ratio worse than 1:1000
    bad = (n < 3) | (lam_min / nn < 1e-4) | (lam_min < 1e-6 * np.maximum(lam_max, 1e-30))
    return bad


def plane_fit(xk, yk, z, valid):
    """Least-squares plane through the valid neighbours, read at (0, 0).

    xk, yk: (B, N) km relative to the test well. Falls back to the plain mean
    of the neighbours where they do not span a plane. Returns (pred, resid)
    with resid the (B, N) residuals of the neighbours (0 where not valid).
    """
    w = valid.astype(float)
    n = w.sum(1)
    deg = _degenerate(xk, yk, w)
    zz = np.where(valid, z, 0.0)
    F = np.stack([np.ones_like(xk), xk, yk], axis=2)  # B,N,3
    Fw = F * w[:, :, None]
    A = np.einsum("bni,bnj->bij", Fw, F)
    b = np.einsum("bni,bn->bi", Fw, zz)
    # make degenerate rows solvable; they are overwritten below
    A[deg] = np.eye(3)
    coef = np.linalg.solve(A, b[:, :, None])[:, :, 0]
    mean = zz.sum(1) / np.maximum(n, 1)
    coef[deg] = 0.0
    coef[deg, 0] = mean[deg]
    pred = coef[:, 0].copy()
    pred[n == 0] = np.nan
    resid = (zz - np.einsum("bni,bi->bn", F, coef)) * w
    return pred, resid


def screen_outliers(xk, yk, z, valid, k_mad, min_tol):
    """Drop neighbours that sit far off the local plane of their neighbours.

    One pass: fit the plane, measure residuals, mark as not valid any
    neighbour whose residual is more than max(k_mad * 1.4826 * MAD, min_tol)
    from the median residual. Uses only the known wells of that test well.
    """
    _, resid = plane_fit(xk, yk, z, valid)
    r = np.where(valid, resid, np.nan)
    with np.errstate(all="ignore"):
        med = np.nanmedian(r, axis=1)
        mad = np.nanmedian(np.abs(r - med[:, None]), axis=1)
    tol = np.maximum(k_mad * 1.4826 * mad, min_tol)
    keep = valid & ~(np.abs(r - med[:, None]) > tol[:, None])
    # never screen when there are too few points to judge
    few = valid.sum(1) < 6
    keep[few] = valid[few]
    return keep


# --------------------------------------------------------------------------
# method 3: kriging with a local (linear) trend
# --------------------------------------------------------------------------
def krige(xk, yk, z, valid, alpha, r, drift_linear=True, chunk=20000):
    """Universal kriging in a moving neighbourhood with variogram
    g(h) = r + h**alpha (h in km; r is the nugget, in the same unit-slope
    scale). The slope of the variogram is estimated locally from the same
    neighbours, so only the shape (alpha, r) is a fixed setting.

    Drift: [1, x, y] where at least 5 valid neighbours span a plane,
    otherwise [1] (ordinary kriging).

    Returns pred, unit_var, s2_local, dof:
      pred      forecast at the test well
      unit_var  kriging variance for a new hole at the test well, for unit
                slope (includes the nugget r)
      s2_local  local slope estimate  q / dof, q = z' P z
      dof       valid neighbours minus drift terms
    """
    B, N = xk.shape
    pred = np.full(B, np.nan)
    unit_var = np.full(B, np.nan)
    s2 = np.full(B, np.nan)
    dof = np.zeros(B, dtype=int)
    for s in range(0, B, chunk):
        e = min(B, s + chunk)
        x = xk[s:e]
        y = yk[s:e]
        v = valid[s:e]
        zz = np.where(v, z[s:e], 0.0)
        w = v.astype(float)
        b = e - s
        n = v.sum(1)
        lin = (n >= 5) & ~_degenerate(x, y, w)
        if not drift_linear:
            lin[:] = False
        dx = x[:, :, None] - x[:, None, :]
        dy = y[:, :, None] - y[:, None, :]
        h = np.sqrt(dx * dx + dy * dy)
        G = r + h ** alpha
        ii = np.arange(N)
        G[:, ii, ii] = 0.0
        vv = v[:, :, None] & v[:, None, :]
        G = np.where(vv, G, 0.0)
        # rows of invalid points become identity rows: weight exactly zero
        inval = ~v
        bi, ni = np.nonzero(inval)
        G[bi, ni, ni] = 1.0
        h0 = np.sqrt(x * x + y * y)
        g0 = np.where(v, r + h0 ** alpha, 0.0)
        F = np.zeros((b, N, 3))
        F[:, :, 0] = w
        F[:, :, 1] = x * w * lin[:, None]
        F[:, :, 2] = y * w * lin[:, None]
        A = np.zeros((b, N + 3, N + 3))
        A[:, :N, :N] = G
        A[:, :N, N:] = F
        A[:, N:, :N] = np.transpose(F, (0, 2, 1))
        # switched-off drift terms: identity rows so their multiplier is 0
        off = ~lin
        A[off, N + 1, N + 1] = 1.0
        A[off, N + 2, N + 2] = 1.0
        rhs = np.zeros((b, N + 3, 2))
        rhs[:, :N, 0] = g0
        rhs[:, N, 0] = 1.0
        rhs[:, :N, 1] = zz
        empty = n == 0
        A[empty] = np.eye(N + 3)
        try:
            sol = np.linalg.solve(A, rhs)
        except np.linalg.LinAlgError:
            sol = np.empty_like(rhs)
            for j in range(b):
                sol[j] = np.linalg.lstsq(A[j], rhs[j], rcond=None)[0]
        lam = sol[:, :N, 0]
        mu0 = sol[:, N, 0]
        a = sol[:, :N, 1]
        p = np.where(lin, 3, 1)
        d = n - p
        q = -(zz * a).sum(1)
        pr = (lam * zz).sum(1)
        uv = (lam * g0).sum(1) + mu0
        pr[empty] = np.nan
        uv[empty] = np.nan
        pred[s:e] = pr
        unit_var[s:e] = uv
        with np.errstate(all="ignore"):
            s2[s:e] = np.where(d > 0, q / np.maximum(d, 1), np.nan)
        dof[s:e] = d
    return pred, unit_var, s2, dof


def interval_halfwidth(unit_var, s2_local, dof, s2_fallback, calib, level=0.80, min_dof=3):
    """Half width of the central `level` range of the kriging forecast.

    Student-t with the local degrees of freedom. Where fewer than min_dof
    degrees of freedom are left, the pre-test-year fallback slope is used
    with a normal quantile.
    """
    use_local = (dof >= min_dof) & np.isfinite(s2_local) & (s2_local > 0)
    s2 = np.where(use_local, s2_local, s2_fallback)
    with np.errstate(all="ignore"):
        tq = np.where(use_local, student_t.ppf(0.5 + level / 2, np.maximum(dof, 1)), 1.2815515655446004)
        sd = np.sqrt(np.maximum(unit_var, 0) * s2)
    return calib * tq * sd


def gather(pool, idx, tx, ty):
    """Neighbour arrays for the solvers: coords in km relative to the test
    well, values, valid mask."""
    valid = idx >= 0
    safe = np.where(valid, idx, 0)
    xk = (pool.x[safe] - tx[:, None]) / 1000.0
    yk = (pool.y[safe] - ty[:, None]) / 1000.0
    z = pool.val[safe]
    xk = np.where(valid, xk, 0.0)
    yk = np.where(valid, yk, 0.0)
    z = np.where(valid, z, 0.0)
    return xk, yk, z, valid
