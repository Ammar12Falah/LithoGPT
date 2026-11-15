"""Scoring of all readers on the test wells.  RUN ONLY AFTER THE FREEZE COMMIT.

This is the only script that opens data/labels_test_SEALED.parquet.
It refuses to run unless the file FREEZE (holding the freeze commit hash) exists,
or `--wells practice` is given (then it scores the practice wells from labels_pool, for testing).

Outputs (scores/):
  headline.csv            one row per reader, pooled over the wells scored
  by_well.csv, by_class.csv, by_expert_confidence.csv
  confusion_<reader>.csv  expert class (rows) against reader class (columns), in metres
  comparisons.csv         pairs of readers: pooled gap and wells ahead
  text_vs_log_picture.csv agreement of the two document readings with each other
  second_class_side.csv   side numbers when the second class of a reading also counts
  marks.csv               the three pass marks
  steps_<well>.csv        class from every reader for every depth step (no expert class)
"""
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a2_model as m  # noqa: E402
from combine import combine_arrays  # noqa: E402
from common import (CLASSES, CODE_TO_IDX, CONF, FAM_OF_IDX, FAMILY, LAB, ROOT, SHALE, STEP_M,  # noqa: E402
                    item_scores, summarise, well_code, window_hits)
from readings import load_reading, rasterise  # noqa: E402

READERS = ["text", "log picture", "combined", "curve picture", "ten-well model", "all-well model", "all-shale line"]
FILE_OF = {"text": "text", "log picture": "log_picture", "curve picture": "curve_picture"}


def pct(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(100 * x, 1)


def load_truth(wells, practice):
    logs = m.load_logs()
    logs = logs[logs.WELL.isin(wells)]
    if practice:
        lab = pd.read_parquet(ROOT / "data" / "labels_pool.parquet")
    else:
        assert (ROOT / "FREEZE").exists(), "no FREEZE file: the readings are not frozen yet"
        lab = pd.read_parquet(ROOT / "data" / "labels_test_SEALED.parquet")
    df = logs.merge(lab[["row_id", LAB, CONF]], on="row_id", how="inner")
    df = df[df[LAB].notna()].copy()
    df["truth"] = df[LAB].map(CODE_TO_IDX).astype(int)
    return df.sort_values(["WELL", "DEPTH_MD"], kind="stable").reset_index(drop=True)


def model_preds(wells):
    """Class per depth step from the two saved plain models (no labels involved)."""
    logs = m.load_logs()
    X = m.build_features(logs, m.SETUP["features"])
    out = {}
    for tag, name in [("ten-well model", "ten_well"), ("all-well model", "all_well")]:
        b = lgb.Booster(model_file=str(ROOT / "models" / f"{name}.txt"))
        idx = np.flatnonzero(logs.WELL.isin(wells).to_numpy())
        p = b.predict(X.iloc[idx]).argmax(1)
        out[tag] = pd.Series(p, index=logs["row_id"].to_numpy()[idx])
    return out


def reader_arrays(well, df_w, mp, readings_dir):
    """All readers on the depth steps of one well -> dict reader -> class index (-1 = no class)."""
    code = well_code(well)
    d = df_w.DEPTH_MD.to_numpy()
    out, second, extra = {}, {}, {}
    rd = {}
    for r, f in FILE_OF.items():
        p = readings_dir / f"{code}__{f}.csv"
        if p.exists():
            rd[r] = load_reading(p)
            out[r], row = rasterise(rd[r], d)
            extra[r + "_row"] = row
            if "second_class" in rd[r].columns:
                second[r], _ = rasterise(rd[r], d, col="cls2")
        else:
            out[r] = None
    if out.get("text") is not None and out.get("log picture") is not None:
        cls, src, row = combine_arrays(rd["text"], rd["log picture"], d)
        out["combined"] = cls
        extra["combined_src"], extra["combined_row"] = src, row
        s2 = np.where(src == "text", second.get("text", np.full(len(d), -1)),
                      second.get("log picture", np.full(len(d), -1)))
        second["combined"] = np.where(cls >= 0, s2, -1)
    else:
        out["combined"] = None
    for tag in ("ten-well model", "all-well model"):
        out[tag] = mp[tag].reindex(df_w.row_id.to_numpy()).to_numpy().astype(int) if mp else None
    out["all-shale line"] = np.full(len(d), SHALE)
    return out, second, extra, rd


def conf_name(v):
    return {1.0: "1 high", 2.0: "2 medium", 3.0: "3 low"}.get(v, "not given")


def main():
    practice = "--wells" in sys.argv and sys.argv[sys.argv.index("--wells") + 1] == "practice"
    draw = pd.read_csv(ROOT / "draw.csv")
    wells = draw[draw.practice_well].well.tolist() if practice else draw[draw.role == "test"].well.tolist()
    readings_dir = ROOT / ("work/practice_readings" if practice else "readings")
    out_dir = ROOT / ("work/practice_scores" if practice else "scores")
    out_dir.mkdir(parents=True, exist_ok=True)
    df = load_truth(wells, practice)
    mp = model_preds(wells) if (ROOT / "models" / "ten_well.txt").exists() and not practice else None

    items = {r: [] for r in READERS}      # per reader: list of per-well frames
    done_wells = {r: [] for r in READERS}
    side_rows, agree_rows = [], []
    for well in wells:
        dw = df[df.WELL == well].reset_index(drop=True)
        if len(dw) == 0:
            continue
        d, t = dw.DEPTH_MD.to_numpy(), dw.truth.to_numpy()
        preds, second, extra, rd = reader_arrays(well, dw, mp, readings_dir)
        steps = pd.DataFrame({"depth_md": d})
        for r in READERS:
            p = preds.get(r)
            if p is None:
                continue
            it = item_scores(d, p, t)
            it["well"], it["truth"], it["pred"], it["conf"] = well, t, p, dw[CONF].map(conf_name).to_numpy()
            it["depth"] = d
            items[r].append(it)
            done_wells[r].append(well)
            steps[r] = [CLASSES[i] if i >= 0 else "" for i in p]
            # side number: the second class of a reading also counts in the tolerant agreement
            if r in second:
                h2 = window_hits(d, second[r], t, len(CLASSES))
                side_rows.append({"reader": r, "well": well, "n_items": len(t),
                                  "tolerant_main_only": it.tolerant.mean(),
                                  "tolerant_with_second_class": (it.tolerant | h2).mean()})
        if "combined_src" in extra:
            steps["combined_source"] = extra["combined_src"]
        steps.to_csv(out_dir / f"steps_{well_code(well)}.csv", index=False)
        # agreement of text and log picture with each other
        if preds.get("text") is not None and preds.get("log picture") is not None:
            a, b = preds["text"], preds["log picture"]
            both = (a >= 0) & (b >= 0)
            same = both & (a == b)
            samefam = both & (FAM_OF_IDX[np.clip(a, 0, None)] == FAM_OF_IDX[np.clip(b, 0, None)])
            agree_rows.append({"well": well, "n_items": len(t), "both_read": both.sum(), "same_class": same.sum(),
                               "same_family": samefam.sum(),
                               "strict_where_same": (a[same] == t[same]).sum(),
                               "tolerant_where_same": item_scores(d, np.where(same, a, -1), t).tolerant[same].sum(),
                               "strict_text_where_differ": (a[both & ~same] == t[both & ~same]).sum(),
                               "strict_log_where_differ": (b[both & ~same] == t[both & ~same]).sum(),
                               "differ": (both & ~same).sum()})

    # ---------- tables ----------
    head, bywell, bycls, byconf = [], [], [], []
    for r in READERS:
        if not items[r]:
            continue
        allit = pd.concat(items[r], ignore_index=True)
        s = summarise(allit, allit.truth.to_numpy())
        s.update({"reader": r, "wells_scored": len(done_wells[r])})
        head.append(s)
        for w, g in allit.groupby("well", sort=False):
            sw = summarise(g, g.truth.to_numpy())
            sw.update({"reader": r, "well": w})
            bywell.append(sw)
        for c in range(len(CLASSES)):
            g = allit[allit.truth == c]
            if len(g):
                sc = summarise(g, g.truth.to_numpy(), min_class_m=0)
                sc.update({"reader": r, "expert_class": CLASSES[c]})
                bycls.append(sc)
        for cf, g in allit.groupby("conf"):
            sc = summarise(g, g.truth.to_numpy())
            sc.update({"reader": r, "expert_confidence": cf})
            byconf.append(sc)
        conf = pd.crosstab(allit.truth.map(lambda i: CLASSES[i]),
                           allit.pred.map(lambda i: CLASSES[i] if i >= 0 else "(no class)")) * STEP_M
        conf = conf.reindex(index=[c for c in CLASSES if c in conf.index],
                            columns=[c for c in CLASSES + ["(no class)"] if c in conf.columns]).round(1)
        conf.index.name = "expert class \\ reader class (metres)"
        conf.to_csv(out_dir / f"confusion_{r.replace(' ', '_').replace('-', '_')}.csv")

    def tidy(rows, first):
        t = pd.DataFrame(rows)
        num = [c for c in t.columns if c.endswith(("_all", "_read")) or c == "coverage"]
        for c in num:
            t[c + "_pct"] = (100 * t[c]).round(1)
        keep = first + ["n_items", "metres", "coverage_pct", "read_metres"]
        for k in ("strict", "tolerant", "soft", "balanced"):
            keep += [f"{k}_all_pct", f"{k}_read_pct"] + ([f"{k}_metres"] if f"{k}_metres" in t else [])
        t["metres"] = t["metres"].round(1)
        for c in t.columns:
            if c.endswith("metres"):
                t[c] = t[c].round(1)
        return t[[c for c in keep if c in t.columns] + (["n_classes_balanced"] if "n_classes_balanced" in t else [])]

    H = tidy(head, ["reader", "wells_scored"])
    H.to_csv(out_dir / "headline.csv", index=False)
    W = tidy(bywell, ["reader", "well"])
    W.to_csv(out_dir / "by_well.csv", index=False)
    tidy(bycls, ["reader", "expert_class"]).drop(columns=["balanced_all_pct", "balanced_read_pct", "n_classes_balanced"],
                                                 errors="ignore").to_csv(out_dir / "by_class.csv", index=False)
    tidy(byconf, ["reader", "expert_confidence"]).to_csv(out_dir / "by_expert_confidence.csv", index=False)

    if side_rows:
        S = pd.DataFrame(side_rows)
        pooled = S.groupby("reader").apply(lambda g: pd.Series({
            "well": "POOLED", "n_items": g.n_items.sum(),
            "tolerant_main_only": np.average(g.tolerant_main_only, weights=g.n_items),
            "tolerant_with_second_class": np.average(g.tolerant_with_second_class, weights=g.n_items)}),
            include_groups=False).reset_index()
        S = pd.concat([S, pooled], ignore_index=True)
        for c in ("tolerant_main_only", "tolerant_with_second_class"):
            S[c] = (100 * S[c]).round(1)
        S.to_csv(out_dir / "second_class_side.csv", index=False)
    if agree_rows:
        A = pd.DataFrame(agree_rows)
        tot = A.drop(columns="well").sum()
        tot["well"] = "POOLED"
        A = pd.concat([A, tot.to_frame().T], ignore_index=True)
        A["share_both_read_pct"] = (100 * A.both_read / A.n_items).astype(float).round(1)
        A["share_same_class_of_all_pct"] = (100 * A.same_class / A.n_items).astype(float).round(1)
        A["share_same_class_of_both_read_pct"] = (100 * A.same_class / A.both_read.replace(0, np.nan)).astype(float).round(1)
        A["share_same_family_of_both_read_pct"] = (100 * A.same_family / A.both_read.replace(0, np.nan)).astype(float).round(1)
        A["strict_where_same_pct"] = (100 * A.strict_where_same / A.same_class.replace(0, np.nan)).astype(float).round(1)
        A["tolerant_where_same_pct"] = (100 * A.tolerant_where_same / A.same_class.replace(0, np.nan)).astype(float).round(1)
        A["strict_text_where_differ_pct"] = (100 * A.strict_text_where_differ / A.differ.replace(0, np.nan)).astype(float).round(1)
        A["strict_log_where_differ_pct"] = (100 * A.strict_log_where_differ / A.differ.replace(0, np.nan)).astype(float).round(1)
        for c in ("both_read", "same_class", "same_family", "differ"):
            A[c + "_metres"] = (A[c].astype(float) * STEP_M).round(1)
        A.to_csv(out_dir / "text_vs_log_picture.csv", index=False)

    # ---------- comparisons of two readers ----------
    comp = []
    n_wells = len(wells)
    need = n_wells - 1 if n_wells < 5 else 4
    for metric in ("tolerant_all_pct", "strict_all_pct", "balanced_all_pct"):
        for i, a in enumerate(READERS):
            for b in READERS[i + 1:]:
                if a not in set(H.reader) or b not in set(H.reader):
                    continue
                ga = float(H.loc[H.reader == a, metric].iloc[0])
                gb = float(H.loc[H.reader == b, metric].iloc[0])
                wa = W[W.reader == a].set_index("well")[metric]
                wb = W[W.reader == b].set_index("well")[metric]
                common = wa.index.intersection(wb.index)
                a_ahead = int((wa[common] > wb[common]).sum())
                b_ahead = int((wb[common] > wa[common]).sum())
                gap = round(ga - gb, 1)
                if gap >= 5 and a_ahead >= need:
                    verdict = f"{a} ahead"
                elif gap <= -5 and b_ahead >= need:
                    verdict = f"{b} ahead"
                else:
                    verdict = "not decided"
                comp.append({"metric": metric, "reader_a": a, "reader_b": b, "a_pct": ga, "b_pct": gb,
                             "gap_points_a_minus_b": gap, "wells_a_ahead": a_ahead, "wells_b_ahead": b_ahead,
                             "wells_compared": len(common), "verdict": verdict})
    C = pd.DataFrame(comp)
    C.to_csv(out_dir / "comparisons.csv", index=False)

    # ---------- the pass marks (Marks 2 and 3; Mark 1 comes from the learning curve) ----------
    if not practice:
        rules = json.loads((ROOT / "src" / "teacher.json").read_text())
        teacher = rules["teacher_reading"]

        def verdict_of(metric):
            def get(r):
                return float(H.loc[H.reader == r, metric].iloc[0])

            def cmp(a, b):
                row = C[(C.metric == metric) & (((C.reader_a == a) & (C.reader_b == b)) | ((C.reader_a == b) & (C.reader_b == a)))].iloc[0]
                return row.verdict
            t, ten, allw, sh, cp = get(teacher), get("ten-well model"), get("all-well model"), get("all-shale line"), get("curve picture")
            v_t10 = cmp(teacher, "ten-well model")
            v_tall = cmp(teacher, "all-well model")
            if v_t10 == f"{teacher} ahead" and t - sh >= 10:
                m2 = "pass"
            elif v_t10 == "ten-well model ahead" or t - sh < 5:
                m2 = "fail"
            else:
                m2 = "not decided"
            if m2 == "pass" and v_tall != "all-well model ahead":
                m2 = "strong pass"
            gap3 = cp - ten
            m3 = "pass" if gap3 >= -5 else ("fail" if gap3 <= -15 else "not decided")
            return {"metric": metric, "teacher_reading": teacher, "teacher_pct": t, "ten_well_pct": ten,
                    "all_well_pct": allw, "all_shale_pct": sh, "curve_picture_pct": cp,
                    "teacher_vs_ten_well": v_t10, "teacher_vs_all_well": v_tall,
                    "teacher_minus_all_shale": round(t - sh, 1), "mark2": m2,
                    "curve_picture_minus_ten_well": round(gap3, 1), "mark3": m3,
                    "curve_picture_minus_all_well": round(cp - allw, 1),
                    "curve_picture_vs_all_well": cmp("curve picture", "all-well model")}
        M = pd.DataFrame([verdict_of(k) for k in ("tolerant_all_pct", "balanced_all_pct", "strict_all_pct")])
        M.to_csv(out_dir / "marks.csv", index=False)
        print(M.T.to_string())
    pd.set_option("display.width", 250)
    print(H.to_string(index=False))
    print(W[["reader", "well", "coverage_pct", "strict_all_pct", "tolerant_all_pct", "soft_all_pct"]].to_string(index=False))
    # per-item frame kept on disk (not in git: it holds expert labels) for the conflict sheets
    allf = []
    for r in READERS:
        for it in items[r]:
            f = it[["well", "depth", "truth", "pred", "conf"]].copy()
            f["reader"] = r
            allf.append(f)
    (ROOT / "data").mkdir(exist_ok=True)
    pd.concat(allf, ignore_index=True).to_parquet(ROOT / "data" / ("items_practice.parquet" if practice else "items_test.parquet"))


if __name__ == "__main__":
    main()
