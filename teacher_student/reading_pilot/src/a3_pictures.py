"""A3: draw the curve pictures (paper style) from the logs file only.

 unlabelled pictures : tracks for gamma ray / caliper / bit size, resistivity (log scale),
                       density / neutron / PEF, sonic, other curves; depth numbers; group and
                       formation names. No well name, no rock labels.
 labelled pictures   : the same plus one extra track with the expert rock class in colour
                       (example wells only; labels come from labels_pool, never from test wells).

Usage:
  python -I src/a3_pictures.py <length_m> <out_dir> unlabelled|labelled <well> [<well> ...] [--range d0 d1]
File names carry a code (work/picture_codes.csv), not the well name.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CLASSES, CODE_TO_IDX, LAB, ROOT, SEED  # noqa: E402

LITH_COLOURS = {
    "Sandstone": "#ffe14d", "Sandstone/Shale": "#b5c334", "Shale": "#8a9a8a", "Marl": "#7fd6c2",
    "Dolomite": "#a678d6", "Limestone": "#3f8fe0", "Chalk": "#a8e0ff", "Halite": "#ff9ecb",
    "Anhydrite": "#d62d7f", "Tuff": "#ff8c1a", "Coal": "#111111", "Basement": "#8b3a1a",
}
LITH_SHORT = {"Sandstone": "SS", "Sandstone/Shale": "SS/SH", "Shale": "SH", "Marl": "MRL", "Dolomite": "DOL",
              "Limestone": "LST", "Chalk": "CHK", "Halite": "HAL", "Anhydrite": "ANH", "Tuff": "TUF",
              "Coal": "COAL", "Basement": "BSMT"}


def codes() -> dict:
    """A fixed random code for every well (seeded), so that file names do not show the well."""
    p = ROOT / "work" / "picture_codes.csv"
    if p.exists():
        d = pd.read_csv(p)
        return dict(zip(d.well, d.code))
    wells = pd.read_csv(ROOT / "draw.csv").well.tolist()
    rng = np.random.default_rng(SEED + 1)
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    out, used = {}, set()
    for w in wells:
        while True:
            c = "".join(rng.choice(list(letters), size=4))
            if c not in used:
                used.add(c)
                break
        out[w] = c
    p.parent.mkdir(exist_ok=True)
    pd.DataFrame({"well": list(out), "code": list(out.values())}).to_csv(p, index=False)
    return out


def step_runs(depth, values):
    """Runs of equal values along depth -> list of (top, base, value)."""
    runs = []
    if len(depth) == 0:
        return runs
    half = 0.076
    start = 0
    for i in range(1, len(depth) + 1):
        if i == len(depth) or values[i] != values[start] or depth[i] - depth[i - 1] > 0.5:
            runs.append((depth[start] - half, depth[i - 1] + half, values[start]))
            start = i
    return runs


def draw_picture(s: pd.DataFrame, d0: float, d1: float, out: Path, sp_range, lith=None):
    """s: rows of one well inside [d0, d1). lith: class index per row (labelled pictures) or None."""
    length = d1 - d0
    labelled = lith is not None
    widths = [0.55, 1.5, 1.5, 1.5, 1.1, 1.1, 1.55] + ([0.75] if labelled else [])
    fig_w = 8.6 if not labelled else 9.2
    fig, axes = plt.subplots(1, len(widths), figsize=(fig_w, 13.2), dpi=100, sharey=True,
                             gridspec_kw={"width_ratios": widths, "wspace": 0.0})
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.01, right=0.995, top=0.925, bottom=0.045 if labelled else 0.012)
    dep = s["DEPTH_MD"].to_numpy()
    major = 10 if length > 60 else 5
    minor = 2 if length > 60 else 1

    def base(ax, title_lines):
        ax.set_ylim(d1, d0)
        ax.set_yticks(np.arange(np.ceil(d0 / major) * major, d1 + 1e-6, major))
        ax.set_yticks(np.arange(np.ceil(d0 / minor) * minor, d1 + 1e-6, minor), minor=True)
        ax.grid(axis="y", which="major", color="#777777", lw=0.6)
        ax.grid(axis="y", which="minor", color="#cccccc", lw=0.3)
        ax.tick_params(axis="y", which="both", length=0, labelleft=False)
        ax.tick_params(axis="x", which="both", length=0, labelbottom=False)
        ax.set_facecolor("white")
        for sp in ax.spines.values():
            sp.set_linewidth(0.8)
        y = 1.005
        for txt, col in title_lines[::-1]:
            ax.text(0.5, y, txt, transform=ax.transAxes, ha="center", va="bottom", fontsize=6.0, color=col,
                    fontweight="bold")
            y += 0.0125

    def curve(ax, name, lo, hi, colour, ls="-", lw=0.9, log=False):
        if name not in s or s[name].notna().sum() == 0:
            return False
        v = s[name].to_numpy(dtype=float)
        if log:
            x = (np.log10(np.clip(v, lo, hi)) - np.log10(lo)) / (np.log10(hi) - np.log10(lo))
        else:
            x = (np.clip(v, min(lo, hi), max(lo, hi)) - lo) / (hi - lo)
        x = np.where(np.isnan(v), np.nan, x)
        # break the line over depth gaps
        gap = np.r_[False, np.diff(dep) > 0.5]
        x = np.where(gap, np.nan, x)
        ax.plot(x, dep, color=colour, ls=ls, lw=lw)
        return True

    # depth track
    ax = axes[0]
    base(ax, [("DEPTH", "black"), ("m", "black")])
    for t in np.arange(np.ceil(d0 / major) * major, d1 + 1e-6, major):
        ax.text(0.5, t, f"{t:.0f}", ha="center", va="center", fontsize=8.5, fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="none", pad=0.6))
    ax.set_xlim(0, 1)

    # track 1: gamma ray, caliper, bit size
    ax = axes[1]
    t = []
    if curve(ax, "GR", 0, 200, "#0a7a0a", lw=1.0):
        t.append(("GR 0-200 API", "#0a7a0a"))
    if curve(ax, "CALI", 6, 26, "#b0006a", ls="--", lw=0.7):
        t.append(("CALI 6-26 in (dashed)", "#b0006a"))
    if curve(ax, "BS", 6, 26, "black", ls=":", lw=0.8):
        t.append(("BS 6-26 in (dotted)", "black"))
    base(ax, t or [("no GR / CALI", "#999999")])
    ax.set_xlim(0, 1)
    ax.set_xticks(np.linspace(0, 1, 5))
    ax.grid(axis="x", color="#cccccc", lw=0.3)

    # track 2: resistivity, log scale 0.2 - 2000
    ax = axes[2]
    t = []
    for name, col, ls, lw in [("RDEP", "#d00000", "-", 1.0), ("RMED", "#0044cc", "--", 0.8),
                              ("RSHA", "black", ":", 0.8), ("RXO", "#888800", "-.", 0.6),
                              ("RMIC", "#cc7700", ":", 0.6)]:
        if curve(ax, name, 0.2, 2000, col, ls=ls, lw=lw, log=True):
            style = {"-": "=solid", "--": "=dash", ":": "=dot", "-.": "=dashdot"}[ls]
            t.append((name + style, col))
    base(ax, [("RES 0.2-2000 ohm.m (log)", "black")] + ([(" ".join(n for n, _ in t[:2]), "black"), (" ".join(n for n, _ in t[2:]), "black")] if t else [("none", "#999999")]))
    ax.set_xlim(0, 1)
    ax.set_xticks(np.linspace(0, 1, 5))
    ax.grid(axis="x", color="#bbbbbb", lw=0.4)

    # track 3: density, neutron, PEF
    ax = axes[3]
    t = []
    if curve(ax, "RHOB", 1.95, 2.95, "#d00000", lw=1.0):
        t.append(("RHOB 1.95-2.95 g/cc", "#d00000"))
    if curve(ax, "NPHI", 0.45, -0.15, "#0044cc", ls="--", lw=0.8):
        t.append(("NPHI 0.45 to -0.15 (dashed)", "#0044cc"))
    if curve(ax, "PEF", 0, 10, "black", ls=":", lw=0.8):
        t.append(("PEF 0-10 (dotted)", "black"))
    base(ax, t or [("no density / neutron", "#999999")])
    ax.set_xlim(0, 1)
    ax.set_xticks(np.linspace(0, 1, 5))
    ax.grid(axis="x", color="#cccccc", lw=0.3)

    # track 4: sonic
    ax = axes[4]
    t = []
    if curve(ax, "DTC", 240, 40, "#7a00b0", lw=1.0):
        t.append(("DTC 240-40 us/ft", "#7a00b0"))
    if curve(ax, "DTS", 440, 40, "#008888", ls="--", lw=0.7):
        t.append(("DTS 440-40 (dash)", "#008888"))
    base(ax, t or [("no sonic", "#999999")])
    ax.set_xlim(0, 1)
    ax.set_xticks(np.linspace(0, 1, 5))
    ax.grid(axis="x", color="#cccccc", lw=0.3)

    # track 5: other curves
    ax = axes[5]
    t = []
    if sp_range is not None and curve(ax, "SP", sp_range[0], sp_range[1], "#444444", lw=0.8):
        t.append((f"SP {sp_range[0]:.0f} to {sp_range[1]:.0f} mV", "#444444"))
    if curve(ax, "ROP", 0, 80, "#cc5500", ls="--", lw=0.6):
        t.append(("ROP 0-80 (dash)", "#cc5500"))
    if curve(ax, "DRHO", -0.25, 0.25, "#0088cc", ls=":", lw=0.7):
        t.append(("DRHO +-0.25 (dot)", "#0088cc"))
    base(ax, t or [("no other curves", "#999999")])
    ax.set_xlim(0, 1)
    ax.set_xticks(np.linspace(0, 1, 5))
    ax.grid(axis="x", color="#cccccc", lw=0.3)

    # track 6: group and formation names
    ax = axes[6]
    base(ax, [("GROUP", "black"), ("FORMATION (italic)", "black")])
    ax.grid(False)
    ax.set_xlim(0, 1)
    for col, x, style in [("GROUP", 0.03, "normal"), ("FORMATION", 0.03, "italic")]:
        vals = s[col].fillna("(not given)").to_numpy()
        for top, bot, v in step_runs(dep, vals):
            top, bot = max(top, d0), min(bot, d1)
            if col == "GROUP":
                ax.axhline(top, color="black", lw=1.0)
                ypos = top + 0.012 * length
                ax.text(x, ypos, str(v), fontsize=7.2, fontweight="bold", va="top", ha="left", clip_on=True)
            else:
                ax.plot([0, 1], [top, top], color="#555555", lw=0.6, ls="--")
                ypos = top + 0.030 * length
                if bot - top > 0.02 * length:
                    ax.text(x, ypos, str(v), fontsize=6.8, style=style, va="top", ha="left", clip_on=True)

    # extra track: expert rock class in colour (labelled pictures only)
    if labelled:
        ax = axes[7]
        base(ax, [("ROCK CLASS", "black"), ("(expert label)", "black")])
        ax.grid(False)
        ax.set_xlim(0, 1)
        for top, bot, v in step_runs(dep, lith):
            if v < 0:
                continue
            top, bot = max(top, d0), min(bot, d1)
            name = CLASSES[int(v)]
            ax.add_patch(Rectangle((0, top), 1, bot - top, facecolor=LITH_COLOURS[name], edgecolor="none"))
            if bot - top >= 0.028 * length:
                ax.text(0.5, (top + bot) / 2, LITH_SHORT[name], ha="center", va="center", fontsize=6.5,
                        color="white" if name in ("Coal", "Basement", "Anhydrite") else "black")
        handles = [Patch(facecolor=LITH_COLOURS[c], edgecolor="black", lw=0.4, label=f"{c} ({LITH_SHORT[c]})")
                   for c in CLASSES]
        fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=6.6, frameon=False,
                   handlelength=1.4, columnspacing=0.9, bbox_to_anchor=(0.5, 0.0))
    fig.savefig(out, facecolor="white")
    plt.close(fig)


def make(length, out_dir, mode, wells, d_range=None):
    logs = pd.read_parquet(ROOT / "data" / "logs_all.parquet")
    lab = None
    if mode == "labelled":
        test = set(pd.read_csv(ROOT / "draw.csv").query("role == 'test'").well)
        assert not (set(wells) & test), "labelled pictures are never made for test wells"
        lab = pd.read_parquet(ROOT / "data" / "labels_pool.parquet")
    cd = codes()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for w in wells:
        s = logs[logs.WELL == w].sort_values("DEPTH_MD")
        if lab is not None:
            s = s.merge(lab[["row_id", LAB]], on="row_id", how="left")
            s["lith"] = s[LAB].map(CODE_TO_IDX).fillna(-1).astype(int)
        sp = s["SP"].dropna()
        sp_range = None
        if len(sp) > 50:
            lo, hi = np.percentile(sp, [1, 99])
            pad = max(5.0, 0.1 * (hi - lo))
            sp_range = (np.floor((lo - pad) / 10) * 10, np.ceil((hi + pad) / 10) * 10)
        dmin, dmax = s.DEPTH_MD.min(), s.DEPTH_MD.max()
        if d_range:
            dmin, dmax = max(dmin, d_range[0]), min(dmax, d_range[1])
        start = np.floor(dmin / length) * length
        k = 0
        while start < dmax:
            d0, d1 = start, start + length
            part = s[(s.DEPTH_MD >= d0) & (s.DEPTH_MD < d1)]
            if len(part) > 5:
                k += 1
                fn = f"{cd[w]}_{k:03d}_{int(d0):04d}-{int(d1):04d}m.png"
                draw_picture(part, d0, d1, out_dir / fn, sp_range,
                             lith=part["lith"].to_numpy() if lab is not None else None)
                rows.append({"well": w, "code": cd[w], "file": fn, "top": d0, "base": d1, "n_rows": len(part)})
            start += length
    idx = pd.DataFrame(rows)
    idx.to_csv(out_dir / "_index.csv", index=False)
    print(len(idx), "pictures in", out_dir)


if __name__ == "__main__":
    a = sys.argv[1:]
    rng = None
    if "--range" in a:
        i = a.index("--range")
        rng = (float(a[i + 1]), float(a[i + 2]))
        a = a[:i]
    make(float(a[0]), a[1], a[2], a[3:], rng)
