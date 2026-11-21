"""Shared code for the v4 confirmatory pipeline (paper_atce/v4).

The law for this code is PROTOCOL.md in this folder (SHA-256
58d8da3069398641d12a3f4cca5c717198ca163ce7d5f0b0d5ce77d5932d0926).
Section numbers below refer to it.

What is reused, and from where (copied, never edited in place):
  results_new/scripts/lib_common.py      split, well_curves() sort/mask logic, tokenizer recipe
  results_new/scripts/11_train_model.py  b2_depth_features() recipe
  paper_atce/multiseed/ms_run.py         train_only_athy() and load_athy_fitter()

What is new in v4 (protocol section 4):
  - validity mask: GR, RDEP, NPHI, RHOB finite and RDEP > 0 (section 3)
  - deep resistivity enters the tokenizer as log10(RDEP)
  - a boundary token (id K = 1000) marks every removed interval
  - the tokenizer is fitted once and saved with its SHA-256

Reads only train.csv and the split manifest. Writes only under paper_atce/v4/.
"""
import sys

sys.dont_write_bytecode = True

import hashlib
import json
import os
import re
import types
from pathlib import Path

import numpy as np

# The pod recreates the Mac paths (as the multiseed pod did); both can be overridden.
REPO = Path(os.environ.get("V4_REPO", "/Users/ammar/LithoGPT_archive/LithoGPT-2"))
V4 = REPO / "paper_atce" / "v4"
OUT = V4 / "out"
CACHE = V4 / "cache"
RN = REPO / "results_new"
FORCE_TRAIN_CSV = Path(os.environ.get("V4_TRAIN_CSV", "/Users/ammar/LithoGPT_archive/force2020_data/train.csv"))
SPLIT_MANIFEST = RN / "data" / "split_manifest_2026-07-31.json"
PROTOCOL_SHA256 = "58d8da3069398641d12a3f4cca5c717198ca163ce7d5f0b0d5ce77d5932d0926"

FEATURES = ["GR", "RDEP", "NPHI", "RHOB"]
GR, RDEP, NPHI, RHOB = 0, 1, 2, 3
LABEL_COL = "FORCE_2020_LITHOFACIES_LITHOLOGY"
K = 1000                 # real tokens 0..999
BOUNDARY = K             # boundary token id
N_IN_VOCAB = K + 1       # model input vocabulary (real tokens + boundary)
SEED = 20260715          # split, tokenizer, generation seed (pilot settings)
CONTEXT = 512
PRIME_FRAC = 0.25
N_REAL = 5
GAP_TOL = 1.5            # a depth step > GAP_TOL * the well's median step is a removed interval
TOKENIZER_PATH = CACHE / "tokenizer_v4.joblib"
TOKENIZER_SHA_PATH = CACHE / "tokenizer_v4.sha256"
SEQ_CACHE = CACHE / "sequences_v4.npz"
RECORDED_TRAINONLY_LAMBDA = 4375.8   # ms_run.py; analysis/FROZEN_RESULTS.json athy_trainonly_lambda_m

B2_WAVELENGTHS_M = np.logspace(np.log10(10.0), np.log10(5000.0), 5).tolist()   # 11_train_model.py
B2_DEPTH_FEAT_DIM = 1 + 1 + 2 * len(B2_WAVELENGTHS_M)                            # 12

OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------------- io helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_arrays(*arrays):
    h = hashlib.sha256()
    for a in arrays:
        a = np.ascontiguousarray(a)
        h.update(str(a.dtype).encode()); h.update(str(a.shape).encode()); h.update(a.tobytes())
    return h.hexdigest()


def save_json(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, default=_json_default))
    tmp.replace(path)
    return path


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def check_protocol():
    got = sha256_file(V4 / "PROTOCOL.md")
    if got != PROTOCOL_SHA256:
        sys.exit(f"ABORT: PROTOCOL.md SHA-256 {got} != {PROTOCOL_SHA256}")
    return got


# ----------------------------------------------------------------------------- split
def load_split():
    """The split from results_new/data/split_manifest_2026-07-31.json.
    'pilot' is the manifest's test8: the 8 held-out wells (protocol section 2)."""
    m = json.loads(SPLIT_MANIFEST.read_text())
    s = dict(pool98=list(m["pool98"]), train=list(m["train80"]), dev=list(m["dev10"]),
             pilot=list(m["test8"]))
    assert len(s["train"]) == 80 and len(s["dev"]) == 10 and len(s["pilot"]) == 8
    assert not (set(s["train"]) & set(s["dev"])) and not (set(s["train"]) & set(s["pilot"]))
    assert not (set(s["dev"]) & set(s["pilot"]))
    assert set(s["train"]) | set(s["dev"]) | set(s["pilot"]) == set(s["pool98"])
    return s


# ----------------------------------------------------------------------------- data
_DF = {}


def load_df(path=FORCE_TRAIN_CSV):
    """Only the columns the pipeline needs. Default path is the FORCE training file."""
    import pandas as pd
    key = str(path)
    if key not in _DF:
        head = pd.read_csv(path, sep=";", nrows=0).columns
        cols = ["WELL", "DEPTH_MD"] + FEATURES + ([LABEL_COL] if LABEL_COL in head else [])
        _DF[key] = pd.read_csv(path, sep=";", usecols=cols)
    return _DF[key]


def validity_mask(depth, raw):
    """Protocol section 3: GR, RDEP, NPHI, RHOB all finite and RDEP above zero.
    A row without a finite depth cannot be placed and is also removed."""
    return np.isfinite(raw).all(axis=1) & (raw[:, RDEP] > 0) & np.isfinite(depth)


def well_rows(df, wid):
    """Valid rows of one well, sorted by depth, with segment ids.

    Sorting follows lib_common.well_curves (sort by DEPTH_MD); a stable sort is
    used so ties keep file order. A new segment starts wherever one or more
    rows were removed by the validity mask, or where the depth step between
    two kept rows is larger than GAP_TOL times the well's median step (a gap
    in the file itself). Both are 'removed intervals' (protocol section 4)."""
    w = df[df.WELL == wid].sort_values("DEPTH_MD", kind="mergesort")
    depth_all = w["DEPTH_MD"].to_numpy(dtype=np.float64)
    raw = w[FEATURES].to_numpy(dtype=np.float64)
    keep = validity_mask(depth_all, raw)
    idx = np.flatnonzero(keep)
    depth = depth_all[idx]
    fin = depth_all[np.isfinite(depth_all)]
    med_dz = float(np.median(np.diff(fin))) if fin.size > 1 else float("nan")
    if idx.size:
        removed_between = np.diff(idx) > 1
        big_step = np.diff(depth) > GAP_TOL * med_dz
        brk = removed_between | big_step
        seg = np.concatenate(([0], np.cumsum(brk))).astype(np.int64)
    else:
        seg = np.zeros(0, dtype=np.int64)
    if LABEL_COL in w.columns:
        lab = w[LABEL_COL].to_numpy(dtype=np.float64)[idx]
    else:
        lab = np.full(idx.size, np.nan)
    return dict(depth=depth, curves=raw[idx], labels=lab, seg=seg, median_dz=med_dz,
                n_file_rows=int(len(w)), n_valid=int(idx.size))


# ----------------------------------------------------------------------------- tokenizer
def to_model_space(curves):
    """Real units -> tokenizer input: GR, log10(RDEP), NPHI, RHOB."""
    x = np.array(curves, dtype=np.float64, copy=True)
    x[:, RDEP] = np.log10(x[:, RDEP])
    return x


def from_model_space(x):
    """Inverse of to_model_space: back to real units, RDEP in ohm-m."""
    c = np.array(x, dtype=np.float64, copy=True)
    c[:, RDEP] = np.power(10.0, c[:, RDEP])
    return c


class Tokenizer:
    """StandardScaler + MiniBatchKMeans(1000), pilot recipe (lib_common.fit_tokenizer),
    on GR, log10 RDEP, NPHI, RHOB."""

    def __init__(self, scaler, kmeans):
        self.scaler = scaler
        self.kmeans = kmeans
        self.centers = kmeans.cluster_centers_.astype(np.float64)      # standardized units

    # curves (real units) -> standardized features
    def standardize(self, curves):
        return self.scaler.transform(to_model_space(curves))

    def encode(self, curves):
        return self.kmeans.predict(self.standardize(curves)).astype(np.int64)

    def nearest(self, z):
        """Nearest centroid for standardized rows (used by Arm C feedback)."""
        z = np.asarray(z, dtype=np.float64)
        d2 = ((z[:, None, :] - self.centers[None, :, :]) ** 2).sum(-1)
        return d2.argmin(1).astype(np.int64)

    # standardized features -> real units
    def decode_std(self, z):
        return from_model_space(self.scaler.inverse_transform(np.asarray(z, dtype=np.float64)))

    # tokens -> real units (boundary tokens give NaN rows)
    def decode_tokens(self, tok):
        tok = np.asarray(tok)
        out = np.full((tok.size, 4), np.nan)
        m = tok != BOUNDARY
        out[m] = self.decode_std(self.centers[tok[m]])
        return out

    def canonical_sha256(self):
        return sha256_arrays(self.scaler.mean_, self.scaler.scale_, self.centers)


FIT_LOG = []      # every fit records the wells it used; checked by the leakage test


def record_fit(what, wells):
    FIT_LOG.append((what, tuple(wells)))


def fit_tokenizer(train_wells, df):
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.preprocessing import StandardScaler
    record_fit("tokenizer", train_wells)
    X = np.concatenate([to_model_space(well_rows(df, w)["curves"]) for w in train_wells], axis=0)
    scaler = StandardScaler().fit(X)
    kmeans = MiniBatchKMeans(n_clusters=K, random_state=SEED, n_init=3, batch_size=4096)
    kmeans.fit(scaler.transform(X))
    return Tokenizer(scaler, kmeans), int(X.shape[0])


def load_tokenizer(check=True):
    import joblib
    if check:
        want = TOKENIZER_SHA_PATH.read_text().split()[0]
        got = sha256_file(TOKENIZER_PATH)
        if got != want:
            sys.exit(f"ABORT: tokenizer SHA-256 {got} != saved {want}")
    d = joblib.load(TOKENIZER_PATH)
    tk = Tokenizer(d["scaler"], d["kmeans"])
    if check and tk.canonical_sha256() != d["canonical_sha256"]:
        sys.exit("ABORT: tokenizer arrays do not match their recorded canonical SHA-256")
    return tk


# ----------------------------------------------------------------------------- sequences
def build_sequence(rows, tok):
    """Insert a boundary token before every segment except the first.

    Returns arrays over sequence positions:
      tok   token id (BOUNDARY at boundary positions)
      row   index into the well's valid rows (-1 at boundary positions)
      seg   segment id (a boundary carries the id of the segment it opens)
      depth measured depth (a boundary carries the depth of the row after it)
    """
    seg = rows["seg"]
    n = seg.size
    starts = np.flatnonzero(np.diff(seg) != 0) + 1          # first row of each later segment
    L = n + starts.size
    out_tok = np.empty(L, dtype=np.int64)
    out_row = np.empty(L, dtype=np.int64)
    # position of row i in the sequence = i + number of boundaries inserted at or before it
    shift = np.searchsorted(starts, np.arange(n), side="right")
    pos = np.arange(n) + shift
    out_tok[pos] = tok
    out_row[pos] = np.arange(n)
    bpos = starts + np.arange(starts.size)                  # boundary just before row starts[j]
    out_tok[bpos] = BOUNDARY
    out_row[bpos] = -1
    nxt = np.where(out_row >= 0, out_row, np.r_[out_row[1:], -1])
    out_seg = seg[nxt]
    out_depth = rows["depth"][nxt]
    return dict(tok=out_tok, row=out_row, seg=out_seg, depth=out_depth)


def prime_len(L):
    """Protocol section 8: prime with the first quarter, at least 512 tokens."""
    return max(CONTEXT, int(L * PRIME_FRAC))


# ----------------------------------------------------------------------------- Athy, depth features
def load_athy_fitter():
    """Copied from paper_atce/multiseed/ms_run.py: the project's Huber fitter,
    loaded from source without its unused package imports."""
    src = (REPO / "src" / "lithogpt2" / "pipeline" / "trend.py").read_text()
    stripped = re.sub(r"^from \.\.?[\w.]+ import .*$", "", src, flags=re.M)
    mod = types.ModuleType("trend_standalone_v4")
    mod.__file__ = str(REPO / "src" / "lithogpt2" / "pipeline" / "trend.py")
    sys.modules["trend_standalone_v4"] = mod        # dataclasses look the module up here
    exec(compile(stripped, mod.__file__, "exec"), mod.__dict__)
    return mod.fit_athy_trend


def train_only_athy(train_wells, df):
    """Copied from ms_run.py: the Athy decay constant fitted on the 80 training
    wells only (rows with finite DEPTH_MD and NPHI), asserted against the
    recorded train-only value."""
    record_fit("athy", train_wells)
    fit = load_athy_fitter()
    z, p = [], []
    for w in train_wells:
        sub = df[df.WELL == w].sort_values("DEPTH_MD", kind="mergesort")
        d = sub["DEPTH_MD"].to_numpy(dtype=np.float64)
        n = sub["NPHI"].to_numpy(dtype=np.float64)
        m = np.isfinite(d) & np.isfinite(n)
        z.append(d[m]); p.append(n[m])
    z, p = np.concatenate(z), np.concatenate(p)
    tr = fit(z, p, basin_group="train80")
    if abs(tr.lambda_m - RECORDED_TRAINONLY_LAMBDA) > 0.1:
        sys.exit(f"ABORT: train-only lambda {tr.lambda_m:.3f} != recorded {RECORDED_TRAINONLY_LAMBDA}")
    return float(tr.phi0), float(tr.lambda_m), int(z.size)


def b2_depth_features(depth_m, depth_abs_std, lambda_m):
    """Copied from 11_train_model.b2_depth_features, with the decay constant passed in."""
    feats = [depth_abs_std.astype(np.float32)]
    feats.append(np.exp(-depth_m / lambda_m).astype(np.float32))
    for wl in B2_WAVELENGTHS_M:
        feats.append(np.sin(2 * np.pi * depth_m / wl).astype(np.float32))
        feats.append(np.cos(2 * np.pi * depth_m / wl).astype(np.float32))
    return np.stack(feats, axis=-1)


def depth_standardizer(train_depths):
    pool = np.concatenate(train_depths)
    return float(pool.mean()), float(pool.std())


# ----------------------------------------------------------------------------- facies map
def facies_map(train_tokens, train_labels):
    """Protocol section 8: each token -> its most common lithofacies in the
    training wells. Returns (tok2fac over K tokens as class codes, classes)."""
    t = np.concatenate(train_tokens)
    lab = np.concatenate(train_labels)
    ok = np.isfinite(lab)
    t, lab = t[ok], lab[ok].astype(np.int64)
    classes = np.unique(lab)
    li = np.searchsorted(classes, lab)
    cnt = np.zeros((K, classes.size))
    np.add.at(cnt, (t, li), 1.0)
    mode = int(cnt.sum(0).argmax())
    best = cnt.argmax(1)
    best[cnt.sum(1) == 0] = mode
    return classes[best].astype(np.int64), classes


# ----------------------------------------------------------------------------- everything at once
class Data:
    """All wells of one CSV as boundary-token sequences, plus the fitted objects.
    Fitted objects use the training wells only (section 4)."""

    def __init__(self, split, df, tk, wells=None, fit_df=None):
        self.split = split
        self.tk = tk
        fit_df = df if fit_df is None else fit_df
        wells = list(split["pool98"]) if wells is None else list(wells)
        self.rows, self.seq = {}, {}
        for w in wells:
            r = well_rows(df, w)
            r["tok"] = tk.encode(r["curves"]) if r["n_valid"] else np.zeros(0, np.int64)
            self.rows[w] = r
            self.seq[w] = build_sequence(r, r["tok"])
        # fitted on training wells only
        tr_rows = {w: (self.rows[w] if w in self.rows else _rows_tok(fit_df, w, tk)) for w in split["train"]}
        # the training wells are always available, also when `wells` holds only confirmatory wells
        self.train_rows = tr_rows
        self.train_seq = {w: (self.seq[w] if w in self.seq else build_sequence(tr_rows[w], tr_rows[w]["tok"]))
                          for w in split["train"]}
        record_fit("depth_standardizer", split["train"])
        self.depth_mean, self.depth_std = depth_standardizer([tr_rows[w]["depth"] for w in split["train"]])
        record_fit("facies_map", split["train"])
        self.tok2fac, self.fac_classes = facies_map([tr_rows[w]["tok"] for w in split["train"]],
                                                    [tr_rows[w]["labels"] for w in split["train"]])
        self.athy = None

    def ensure_athy(self, df):
        if self.athy is None:
            self.athy = train_only_athy(self.split["train"], df)
        return self.athy

    def dfeat_b2(self, w):
        _, lam, _ = self.athy
        d = self.seq[w]["depth"]
        return b2_depth_features(d, (d - self.depth_mean) / self.depth_std, lam)

    def curves_seq(self, w):
        """Real curves aligned to sequence positions (NaN at boundaries)."""
        s = self.seq[w]
        out = np.full((s["tok"].size, 4), np.nan)
        m = s["row"] >= 0
        out[m] = self.rows[w]["curves"][s["row"][m]]
        return out

    def std_seq(self, w):
        """Standardized features aligned to sequence positions (NaN at boundaries)."""
        s = self.seq[w]
        out = np.full((s["tok"].size, 4), np.nan)
        m = s["row"] >= 0
        out[m] = self.tk.standardize(self.rows[w]["curves"][s["row"][m]])
        return out

    def facies_seq(self, w):
        """True lithofacies where the file has them, else the token's mapped facies.
        -1 at boundaries."""
        s = self.seq[w]
        out = np.full(s["tok"].size, -1, dtype=np.int64)
        m = s["row"] >= 0
        lab = self.rows[w]["labels"][s["row"][m]]
        mapped = self.tok2fac[s["tok"][m]]
        out[m] = np.where(np.isfinite(lab), np.nan_to_num(lab, nan=-1).astype(np.int64), mapped)
        return out


def _rows_tok(df, w, tk):
    r = well_rows(df, w)
    r["tok"] = tk.encode(r["curves"])
    return r


def load_data(wells=None, csv=FORCE_TRAIN_CSV, with_athy=False):
    split = load_split()
    df = load_df(csv)
    fit_df = load_df(FORCE_TRAIN_CSV)
    tk = load_tokenizer()
    d = Data(split, df, tk, wells=wells, fit_df=fit_df)
    if with_athy:
        d.ensure_athy(fit_df)
    return d
