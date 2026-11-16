"""Check sheets for the advisor and conflict sheets for Ammar.

  python -I src/sheets.py check       20 random rows of each of the three readings (no labels needed)
  python -I src/sheets.py conflicts   AFTER THE FREEZE: intervals of at least 3 m where the teacher reading
                                      names a rock of another family than the expert label; at most 40, drawn
                                      at random with the seed; one sheet each.
Committed: check_sheet/*.csv and conflicts/conflicts.csv (references and extracted rows, no expert class).
Not committed (third-party pictures, FORCE logs and labels): the picture sheets in work/sheets_for_ammar/.
"""
import json
import shutil
import sys
from pathlib import Path

import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from combine import combine_arrays  # noqa: E402
from common import CLASSES, CODE_TO_IDX, FAM_OF_IDX, LAB, ROOT, SEED, well_code  # noqa: E402
from readings import load_reading, rasterise  # noqa: E402

SURFACE, INK, INK2, MUTED, GRID = "#1a1a19", "#f0efec", "#c3c2b7", "#898781", "#2c2c2a"
LITH_COL = {"Sandstone": "#e6c229", "Sandstone/Shale": "#a8b545", "Shale": "#7d8f7d", "Marl": "#5fc7b0",
            "Dolomite": "#9c6fd0", "Limestone": "#3987e5", "Chalk": "#8fd0f5", "Halite": "#f08fc0",
            "Anhydrite": "#d62d7f", "Tuff": "#e8791a", "Coal": "#dddddd", "Basement": "#a04a22"}


def test_wells():
    d = pd.read_csv(ROOT / "draw.csv")
    return d[d.role == "test"].well.tolist()


def log_cfg():
    return json.loads((ROOT / "src" / "log_tiles.json").read_text())


def doc_address(well, pdf_rel):
    src = pd.read_csv(ROOT / "src" / "sources.csv")
    hit = src[src.path == pdf_rel]
    return hit.url.iloc[0] if len(hit) else ""


def mode_check():
    rng = np.random.default_rng(SEED + 10)
    out = ROOT / "check_sheet"
    out.mkdir(exist_ok=True)
    img_root = ROOT / "work" / "sheets_for_ammar" / "check_sheet"
    if img_root.exists():
        shutil.rmtree(img_root)
    codes = pd.read_csv(ROOT / "work" / "picture_codes.csv").set_index("well").code
    for reading in ("curve_picture", "log_picture", "text"):
        pool = []
        for w in test_wells():
            p = ROOT / "readings" / f"{well_code(w)}__{reading}.csv"
            if not p.exists():
                continue
            df = pd.read_csv(p, dtype=str, keep_default_na=False)
            df.insert(0, "csv_line", np.arange(len(df)) + 2)
            df.insert(0, "well", w)
            pool.append(df[df.rock_class.str.strip() != ""])
        if not pool:
            continue
        pool = pd.concat(pool, ignore_index=True)
        pick = pool.iloc[np.sort(rng.choice(len(pool), size=min(20, len(pool)), replace=False))].copy()
        refs = []
        (img_root / reading).mkdir(parents=True, exist_ok=True)
        for k, (_, r) in enumerate(pick.iterrows(), 1):
            code = well_code(r.well)
            if reading == "curve_picture":
                idx = pd.read_csv(ROOT / "work" / "curve_read" / f"read_{codes[r.well]}" / "pictures_index.csv")
                a = float(r.depth_from)
                hit = idx[(idx.top <= a) & (idx.base > a)]
                fn = hit.file.iloc[0] if len(hit) else ""
                refs.append(f"curve picture {fn} (re-made from train.csv by src/a3_pictures.py)")
                src_img = ROOT / "work" / "curve_read" / f"read_{codes[r.well]}" / "pictures" / fn
            elif reading == "log_picture":
                cfg = log_cfg()[r.well]
                refs.append(f"{doc_address(r.well, cfg['pdf'])} page {cfg['page']}, picture {r.picture_file}")
                src_img = ROOT / "work" / "log_read" / code / "pictures" / r.picture_file
            else:
                refs.append(f"{r.document_address} page {r.page}")
                docs = pd.read_csv(ROOT / "work" / "text_read" / code / "documents.csv")
                folder = docs[docs.document_address == r.document_address].document_folder
                src_img = (ROOT / "work" / "text_read" / code / folder.iloc[0] / f"p{int(float(r.page)):04d}.png") \
                    if len(folder) and str(r.page).strip() else Path("/nonexistent")
            if src_img.exists() and src_img.is_file():
                shutil.copy(src_img, img_root / reading / f"{k:02d}_{code}_line{r.csv_line}{src_img.suffix}")
        pick.insert(2, "picture_or_page_reference", refs)
        pick.to_csv(out / f"check_sheet_{reading}.csv", index=False)
        print(reading, len(pick), "rows")


def mode_conflicts():
    assert (ROOT / "FREEZE").exists()
    teacher = json.loads((ROOT / "src" / "teacher.json").read_text())["teacher_reading"]
    items = pd.read_parquet(ROOT / "data" / "items_test.parquet")
    it = items[items.reader == teacher]
    logs = pd.read_parquet(ROOT / "data" / "logs_all.parquet")
    rows = []
    for w, g in it.groupby("well", sort=False):
        g = g.sort_values("depth").reset_index(drop=True)
        d, t, p = g.depth.to_numpy(), g.truth.to_numpy(), g.pred.to_numpy()
        code = well_code(w)
        text = load_reading(ROOT / "readings" / f"{code}__text.csv")
        lg = load_reading(ROOT / "readings" / f"{code}__log_picture.csv")
        if teacher == "combined":
            _, src, row = combine_arrays(text, lg, d)
        elif teacher == "text":
            _, row = rasterise(text, d)
            src = np.full(len(d), "text")
        else:
            _, row = rasterise(lg, d)
            src = np.full(len(d), "log_picture")
        bad = (p >= 0) & (FAM_OF_IDX[np.clip(p, 0, None)] != FAM_OF_IDX[t])
        start = None
        for i in range(len(d) + 1):
            same = i < len(d) and bad[i] and start is not None and p[i] == p[start] and t[i] == t[start] \
                and d[i] - d[i - 1] < 0.5
            if start is not None and not same:
                a, b = d[start], d[i - 1]
                if b - a >= 3.0:
                    rows.append({"well": w, "depth_from": round(a, 2), "depth_to": round(b, 2),
                                 "length_m": round(b - a, 1), "teacher_class": CLASSES[p[start]],
                                 "expert_class": CLASSES[t[start]], "source_reading": src[start],
                                 "source_row": int(row[start])})
                start = None
            if i < len(d) and bad[i] and start is None:
                start = i
    allc = pd.DataFrame(rows)
    rng = np.random.default_rng(SEED + 11)
    n_all = len(allc)
    pick = allc.iloc[np.sort(rng.choice(n_all, size=min(40, n_all), replace=False))].reset_index(drop=True) if n_all else allc
    out_dir = ROOT / "conflicts"
    out_dir.mkdir(exist_ok=True)
    img_dir = ROOT / "work" / "sheets_for_ammar" / "conflicts"
    if img_dir.exists():
        shutil.rmtree(img_dir)
    img_dir.mkdir(parents=True)
    lab = pd.read_parquet(ROOT / "data" / "labels_test_SEALED.parquet")
    recs = []
    for k, r in pick.iterrows():
        code = well_code(r.well)
        rd = pd.read_csv(ROOT / "readings" / f"{code}__{r.source_reading}.csv", dtype=str, keep_default_na=False)
        srow = rd.iloc[r.source_row]
        if r.source_reading == "text":
            ref = f"{srow.document_address} page {srow.page}"
            sentence = srow.source_sentence
        else:
            cfg = log_cfg()[r.well]
            ref = f"{doc_address(r.well, cfg['pdf'])} page {cfg['page']}, picture {srow.picture_file}"
            sentence = f"rock as drawn: {srow.rock_as_drawn}"
        recs.append({"sheet": k + 1, "well": r.well, "depth_from": r.depth_from, "depth_to": r.depth_to,
                     "length_m": r.length_m, "teacher_class": r.teacher_class, "source_reading": r.source_reading,
                     "source_csv_line": r.source_row + 2, "source_sentence_or_picture": sentence,
                     "document_address_and_page": ref})
        # ---- the sheet: logs around the interval, expert label, teacher label, source ----
        pad = max(15.0, 1.0 * r.length_m)
        s = logs[(logs.WELL == r.well) & (logs.DEPTH_MD >= r.depth_from - pad) & (logs.DEPTH_MD <= r.depth_to + pad)]
        s = s.sort_values("DEPTH_MD").merge(lab[["row_id", LAB]], on="row_id", how="left")
        g = it[(it.well == r.well)].set_index("depth").pred.reindex(s.DEPTH_MD.to_numpy())
        fig, axes = plt.subplots(1, 6, figsize=(11, 7.5), dpi=110, sharey=True,
                                 gridspec_kw={"width_ratios": [1.3, 1.3, 1.3, 1.1, 0.45, 0.45], "wspace": 0.08})
        fig.patch.set_facecolor(SURFACE)
        dep = s.DEPTH_MD.to_numpy()
        tracks = [("GR", "GR (API)", "#0ca30c", False), ("RDEP", "RDEP (ohm.m, log)", "#d95926", True),
                  ("RHOB", "RHOB (g/cc)", "#d55181", False), ("DTC", "DTC (us/ft)", "#9085e9", False)]
        for ax, (c, name, col, logx) in zip(axes[:4], tracks):
            ax.set_facecolor(SURFACE)
            if s[c].notna().any():
                ax.plot(s[c], dep, color=col, lw=1.3)
                if logx:
                    ax.set_xscale("log")
                    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            if c == "RHOB" and s["NPHI"].notna().any():
                ax2 = ax.twiny()
                ax2.plot(s["NPHI"], dep, color="#3987e5", lw=1.0, ls="--")
                ax2.invert_xaxis()
                ax2.tick_params(colors=MUTED, labelsize=7, length=0)
                ax2.set_xlabel("NPHI (dashed)", color=INK2, fontsize=8)
                for sp in ax2.spines.values():
                    sp.set_visible(False)
            ax.set_title(name, color=INK2, fontsize=9)
            ax.axhspan(r.depth_from, r.depth_to, color="#f0efec", alpha=0.08, lw=0)
            ax.tick_params(colors=MUTED, labelsize=7, length=0)
            ax.grid(color=GRID, lw=0.6)
            for sp in ax.spines.values():
                sp.set_color(GRID)
        for ax, vals, name in [(axes[4], s[LAB].map(CODE_TO_IDX).to_numpy(), "Expert"), (axes[5], g.to_numpy(), "Teacher")]:
            ax.set_facecolor(SURFACE)
            ax.set_title(name, color=INK2, fontsize=9)
            for j in range(len(dep)):
                v = vals[j]
                if v is not None and not (isinstance(v, float) and np.isnan(v)) and v >= 0:
                    ax.axhspan(dep[j] - 0.076, dep[j] + 0.076, color=LITH_COL[CLASSES[int(v)]], lw=0)
            ax.set_xticks([])
            for sp in ax.spines.values():
                sp.set_color(GRID)
        axes[0].set_ylim(dep.max(), dep.min())
        axes[0].set_ylabel("Depth (m MD)", color=INK2)
        used = sorted({CLASSES[int(v)] for v in np.r_[s[LAB].map(CODE_TO_IDX).dropna().to_numpy(), g.dropna().to_numpy()] if v >= 0},
                      key=CLASSES.index)
        handles = [plt.Rectangle((0, 0), 1, 1, color=LITH_COL[c]) for c in used]
        leg = fig.legend(handles, used, loc="lower center", ncol=min(6, len(used)), frameon=False, fontsize=8)
        for tx in leg.get_texts():
            tx.set_color(INK)
        head = (f"Conflict sheet {k + 1}: well {r.well}, {r.depth_from:.1f} - {r.depth_to:.1f} m ({r.length_m} m).  "
                f"Expert label: {r.expert_class}.  Teacher ({r.source_reading.replace('_', ' ')}): {r.teacher_class}.")
        fig.text(0.01, 0.975, head, color=INK, fontsize=10.5, va="top")
        body = f"Source: {sentence[:230]}\n{ref}"
        fig.text(0.01, 0.945, body, color=INK2, fontsize=7.8, va="top", wrap=True)
        fig.subplots_adjust(top=0.84, bottom=0.09, left=0.07, right=0.99)
        fig.savefig(img_dir / f"conflict_{k + 1:02d}_{code}_{int(r.depth_from)}m.png", facecolor=SURFACE)
        plt.close(fig)
        if r.source_reading == "log_picture":
            src_img = ROOT / "work" / "log_read" / code / "pictures" / srow.picture_file
            if src_img.exists():
                shutil.copy(src_img, img_dir / f"conflict_{k + 1:02d}_{code}_source_picture.png")
    pd.DataFrame(recs).to_csv(out_dir / "conflicts.csv", index=False)
    summ = allc.groupby(["teacher_class"]).agg(intervals=("length_m", "size"), metres=("length_m", "sum")).reset_index() if n_all else allc
    summ.to_csv(out_dir / "conflicts_all_summary_by_teacher_class.csv", index=False)
    full = allc.groupby(["expert_class", "teacher_class"]).agg(intervals=("length_m", "size"), metres=("length_m", "sum")).reset_index() if n_all else allc
    full.to_csv(ROOT / "work" / "sheets_for_ammar" / "conflicts_all_by_expert_and_teacher_class.csv", index=False)
    pick.to_csv(ROOT / "work" / "sheets_for_ammar" / "conflicts_with_expert_class.csv", index=False)
    print("conflict intervals of at least 3 m:", n_all, "| total metres:", round(allc.length_m.sum(), 1) if n_all else 0,
          "| sheets drawn:", len(pick))
    print(full.to_string(index=False) if n_all else "")


if __name__ == "__main__":
    {"check": mode_check, "conflicts": mode_conflicts}[sys.argv[1]]()
