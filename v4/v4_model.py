"""Model, training windows, development loss, one-step-ahead scoring and generation for v4.

Copied and adapted from results_new/scripts/11_train_model.py (GPTBlock, LithoGPTv15,
build_batches), scripts/atce/atce_ablation_v3.py (build_batches_continuous, Arm C
decoding) and paper_atce/multiseed/ms_run.py (generate_batch, crash resume).

Changes from the pilot code, all required by PROTOCOL.md:
  - input vocabulary K + 1 (boundary token), output K tokens (discrete) or 4 features (Arm C)
  - optional dropout (embedding, attention, residual) and weight decay (section 6)
  - training windows never cross a boundary (section 4)
  - generation copies boundary positions from the real well and never lets the
    context reach back across a boundary (sections 4, 8)
With dropout 0 the block computes exactly what the pilot block computed.
"""
import sys

sys.dont_write_bytecode = True

import os

# must be set before the first cuBLAS call when deterministic algorithms are on (CUDA)
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import torch
import torch.nn as nn

from v4_common import BOUNDARY, CONTEXT, K, N_IN_VOCAB, B2_DEPTH_FEAT_DIM

D_MODEL = 256
N_LAYERS = 6
N_HEADS = 8
LR = 3e-4
BATCH_SIZE = 32
ARMS = ("A", "B2", "C")


def pick_device():
    dev = os.environ.get("V4_DEVICE")
    if dev:
        return dev
    return "cuda" if torch.cuda.is_available() else "cpu"


def set_determinism(seed, device):
    """Full seeding. Python, NumPy and torch (CPU and CUDA) generators are seeded and
    torch is asked for deterministic kernels."""
    import random
    if device.startswith("cuda"):
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.backends.cudnn.benchmark = False
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        # fused attention kernels on CUDA may have non-deterministic backward passes;
        # the plain math kernel is deterministic and supports dropout and masks
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        if hasattr(torch.backends.cuda, "enable_cudnn_sdp"):
            torch.backends.cuda.enable_cudnn_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)
    torch.use_deterministic_algorithms(True)
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    torch.manual_seed(seed)          # seeds CPU and every CUDA device


# ----------------------------------------------------------------------------- model
class GPTBlock(nn.Module):
    def __init__(self, d_model, n_heads, dropout=0.0):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.ln2 = nn.LayerNorm(d_model)
        self.mlp = nn.Sequential(nn.Linear(d_model, 4 * d_model), nn.GELU(), nn.Linear(4 * d_model, d_model))
        self.drop = nn.Dropout(dropout)

    def forward(self, x, causal_mask):
        h = self.ln1(x)
        a, _ = self.attn(h, h, h, attn_mask=causal_mask, need_weights=False)
        x = x + self.drop(a)
        x = x + self.drop(self.mlp(self.ln2(x)))
        return x


class LithoGPTv4(nn.Module):
    def __init__(self, arm, dropout=0.0, d_model=D_MODEL, n_layers=N_LAYERS, n_heads=N_HEADS,
                 context=CONTEXT):
        super().__init__()
        assert arm in ARMS
        self.arm = arm
        self.context = context
        self.tok_embed = nn.Embedding(N_IN_VOCAB, d_model)
        self.pos_embed = nn.Embedding(context, d_model)
        self.depth_feat_dim = B2_DEPTH_FEAT_DIM if arm == "B2" else 0
        self.use_depth_embed = self.depth_feat_dim > 0
        if self.use_depth_embed:
            self.depth_embed = nn.Linear(self.depth_feat_dim, d_model)
        self.drop = nn.Dropout(dropout)
        self.blocks = nn.ModuleList([GPTBlock(d_model, n_heads, dropout) for _ in range(n_layers)])
        self.ln_f = nn.LayerNorm(d_model)
        self.discrete = arm != "C"
        self.head = nn.Linear(d_model, K if self.discrete else 4)

    def n_params(self):
        return sum(p.numel() for p in self.parameters())

    def forward(self, tokens, depth_feat=None, last_only=False):
        B, T = tokens.shape
        pos = torch.arange(T, device=tokens.device).unsqueeze(0).expand(B, T)
        x = self.tok_embed(tokens) + self.pos_embed(pos)
        if self.use_depth_embed:
            assert depth_feat is not None
            x = x + self.depth_embed(depth_feat)
        x = self.drop(x)
        mask = torch.triu(torch.full((T, T), float("-inf"), device=tokens.device), diagonal=1)
        for block in self.blocks:
            x = block(x, mask)
        if last_only:
            x = x[:, -1:]
        x = self.ln_f(x)
        return self.head(x)


# ----------------------------------------------------------------------------- windows
def valid_window_starts(seg, context=CONTEXT):
    """Starts s of training windows seq[s : s+context+1] that stay inside one segment.
    seg carries the id of the segment each position belongs to (a boundary token has
    the id of the segment it opens), so equal ids at both ends mean the only boundary
    a window can hold is the one at its first position, which opens the segment."""
    L = seg.size
    if L < context + 1:
        return np.zeros(0, dtype=np.int64)
    return np.flatnonzero(seg[:L - context] == seg[context:]).astype(np.int64)


class WindowSampler:
    """Training batches. Pilot scheme (pick a well uniformly, then a window start
    uniformly) restricted to windows inside one segment. State can be saved and
    restored exactly, so a resumed run sees the same batches."""

    def __init__(self, seqs, seed, context=CONTEXT, batch_size=BATCH_SIZE, dfeats=None, targets=None,
                 ignore_boundaries=False):
        self.seqs, self.dfeats, self.targets = seqs, dfeats, targets
        self.context, self.batch_size = context, batch_size
        self.starts = []
        for s in seqs:
            if ignore_boundaries:     # only used by the tests, to plant an error
                st = np.arange(max(0, s["tok"].size - context - 1), dtype=np.int64)
            else:
                st = valid_window_starts(s["seg"], context)
            self.starts.append(st)
        self.wells = [i for i, st in enumerate(self.starts) if st.size > 0]
        self.rng = np.random.default_rng(seed)

    def get_state(self):
        return self.rng.bit_generator.state

    def set_state(self, st):
        self.rng.bit_generator.state = st

    def next_meta(self):
        widx = self.rng.choice(self.wells, size=self.batch_size)
        return [(int(i), int(self.starts[i][self.rng.integers(0, self.starts[i].size)])) for i in widx]

    def next(self):
        meta = self.next_meta()
        c = self.context
        xb = np.stack([self.seqs[i]["tok"][s:s + c] for i, s in meta])
        if self.targets is None:
            yb = torch.from_numpy(np.stack([self.seqs[i]["tok"][s + 1:s + c + 1] for i, s in meta]))
        else:
            yb = torch.from_numpy(np.stack([self.targets[i][s + 1:s + c + 1] for i, s in meta]).astype(np.float32))
        db = None
        if self.dfeats is not None:
            db = torch.from_numpy(np.stack([self.dfeats[i][s:s + c] for i, s in meta]).astype(np.float32))
        return torch.from_numpy(xb), yb, db, meta


# ----------------------------------------------------------------------------- dev loss
def segment_runs(seg):
    """[a, b) position ranges of each segment in a sequence."""
    brk = np.flatnonzero(np.diff(seg) != 0) + 1
    edges = np.concatenate(([0], brk, [seg.size]))
    return list(zip(edges[:-1].tolist(), edges[1:].tolist()))


def dev_chunks(seqs, context=CONTEXT):
    """Fixed teacher-forced chunks covering every token that has a predecessor in its
    segment (or the boundary that opens it), each target counted once. Chunks never
    cross a boundary. Same layout as 11b (non-overlapping windows), per segment."""
    chunks = []
    for wi, s in enumerate(seqs):
        for a, b in segment_runs(s["seg"]):
            for c in range(a, b - 1, context):
                e = min(c + context, b - 1)
                chunks.append((wi, c, e))          # inputs c..e-1, targets c+1..e
    return chunks


@torch.no_grad()
def dev_loss(model, seqs, dfeats=None, targets=None, device="cpu", batch=32):
    """Mean next-token cross entropy (nats) for discrete arms, mean squared error
    (standardized units) for Arm C, over the fixed dev chunks."""
    was_training = model.training
    model.eval()
    chunks = dev_chunks(seqs, model.context)
    by_len = {}
    for ch in chunks:
        by_len.setdefault(ch[2] - ch[1], []).append(ch)
    tot, n = 0.0, 0
    for T, group in sorted(by_len.items()):
        for i in range(0, len(group), batch):
            g = group[i:i + batch]
            x = torch.from_numpy(np.stack([seqs[w]["tok"][c:e] for w, c, e in g])).to(device)
            d = None
            if model.use_depth_embed:
                d = torch.from_numpy(np.stack([dfeats[w][c:e] for w, c, e in g]).astype(np.float32)).to(device)
            out = model(x, d).double()
            if model.discrete:
                y = torch.from_numpy(np.stack([seqs[w]["tok"][c + 1:e + 1] for w, c, e in g])).to(device)
                tot += float(nn.functional.cross_entropy(out.reshape(-1, K), y.reshape(-1), reduction="sum"))
                n += y.numel()
            else:
                y = torch.from_numpy(np.stack([targets[w][c + 1:e + 1] for w, c, e in g])).to(device).double()
                tot += float(((out - y) ** 2).sum())
                n += y.numel()
    if was_training:
        model.train()
    return tot / n, n


# ----------------------------------------------------------------------------- one step ahead
def context_start(seq_tok, context=CONTEXT):
    """For every position p, the first position its context may use: the boundary that
    opens p's segment (or 0), and never more than `context` positions back."""
    L = seq_tok.size
    is_b = seq_tok == BOUNDARY
    last_b = np.maximum.accumulate(np.where(is_b, np.arange(L), 0))
    return np.maximum(last_b, np.arange(L) - context)


@torch.no_grad()
def one_step_ahead(model, seq_tok, positions, dfeat=None, std_targets=None, centers_std=None,
                   device="cpu", batch=64):
    """Teacher-forced prediction at each position in `positions` (none a boundary),
    with exactly the context generation would use: the previous tokens back to the
    opening boundary, at most 512. Returns dict of per-position arrays:
      discrete: logp_true, top1 (argmax token)
      Arm C:    pred_std (4 features), top1 (nearest centroid of the prediction)"""
    model.eval()
    positions = np.asarray(positions, dtype=np.int64)
    assert np.all(seq_tok[positions] != BOUNDARY)
    cs = context_start(seq_tok, model.context)
    res_key = "logp_true" if model.discrete else "pred_std"
    out_val = np.zeros(positions.size) if model.discrete else np.zeros((positions.size, 4))
    out_top = np.zeros(positions.size, dtype=np.int64)
    # positions whose context starts at their opening boundary (or 0) and is shorter than
    # `context`: one forward from that start gives all of them exactly
    short = (positions - cs[positions]) < model.context
    groups = {}
    for j in np.flatnonzero(short):
        groups.setdefault(int(cs[positions[j]]), []).append(j)
    jobs = [("short", a, js) for a, js in groups.items()]
    full = np.flatnonzero(~short)
    for i in range(0, full.size, batch):
        jobs.append(("full", None, full[i:i + batch]))

    def _emit(js, vals):
        if model.discrete:
            logp = torch.log_softmax(vals.double(), dim=-1)
            t = torch.from_numpy(seq_tok[positions[js]]).to(logp.device)
            out_val[js] = logp.gather(1, t[:, None])[:, 0].cpu().numpy()
            out_top[js] = logp.argmax(-1).cpu().numpy()
        else:
            v = vals.double().cpu().numpy()
            out_val[js] = v
            d2 = ((v[:, None, :] - centers_std[None]) ** 2).sum(-1)
            out_top[js] = d2.argmin(1)

    for kind, a, js in jobs:
        js = np.asarray(js)
        if kind == "short":
            e = int(positions[js].max())
            x = torch.from_numpy(seq_tok[a:e][None]).to(device)
            d = torch.from_numpy(dfeat[a:e][None].astype(np.float32)).to(device) if model.use_depth_embed else None
            o = model(x, d)[0]                       # o[t] predicts position a + t + 1
            _emit(js, o[positions[js] - a - 1])
        else:
            P = positions[js]
            x = torch.from_numpy(np.stack([seq_tok[p - model.context:p] for p in P])).to(device)
            d = None
            if model.use_depth_embed:
                d = torch.from_numpy(np.stack([dfeat[p - model.context:p] for p in P]).astype(np.float32)).to(device)
            _emit(js, model(x, d, last_only=True)[:, -1])
    return {res_key: out_val, "top1": out_top}


# ----------------------------------------------------------------------------- generation
@torch.no_grad()
def generate(model, seq_tok, prime_n, n_real, seed, dfeat=None, centers_std=None, temperature=1.0,
             device="cpu", progress=None):
    """Adapted from ms_run.generate_batch. The real well's first prime_n positions are
    the prime. Every later position is generated, except boundary positions, which are
    copied from the real well. The context never reaches back past the boundary that
    opens the current segment and is at most 512 tokens.

    Discrete arms: temperature sampling, one NumPy generator per well seeded with `seed`
    (pilot convention). Arm C: deterministic; the regression output is the generated
    row and its nearest centroid is fed back as the next input token.
    Returns tokens [n_real, L - prime_n] and, for Arm C, standardized rows."""
    model.eval()
    L = seq_tok.size
    is_b = seq_tok == BOUNDARY
    cs = context_start(seq_tok, model.context)
    B = n_real
    toks = np.full((B, L), -1, dtype=np.int64)
    toks[:, :prime_n] = seq_tok[:prime_n]
    rows = None if model.discrete else np.full((B, L, 4), np.nan)
    rng = np.random.default_rng(seed)
    dfeat_t = torch.from_numpy(dfeat.astype(np.float32)).to(device) if model.use_depth_embed else None
    for p in range(prime_n, L):
        if is_b[p]:
            toks[:, p] = BOUNDARY
            continue
        a = int(cs[p])
        x = torch.from_numpy(toks[:, a:p]).to(device)
        d = dfeat_t[a:p].unsqueeze(0).expand(B, -1, -1) if model.use_depth_embed else None
        out = model(x, d, last_only=True)[:, -1]
        if model.discrete:
            probs = torch.softmax(out.double() / temperature, dim=-1).cpu().numpy()
            for b in range(B):
                pb = probs[b] / probs[b].sum()
                toks[b, p] = int(rng.choice(K, p=pb))
        else:
            z = out.double().cpu().numpy()
            rows[:, p] = z
            d2 = ((z[:, None, :] - centers_std[None]) ** 2).sum(-1)
            toks[:, p] = d2.argmin(1)
        if progress and (p - prime_n) % 2000 == 0:
            progress(p - prime_n, L - prime_n)
    gen_tok = toks[:, prime_n:]
    gen_rows = None if rows is None else rows[:, prime_n:]
    return gen_tok, gen_rows
