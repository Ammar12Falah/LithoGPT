"""Writes report.md from the result tables. Every number in the tables is read from a CSV file.
Usage: python -I src/make_report.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
S, C = ROOT / "scores", ROOT / "curve"
MAIN = ["text", "log picture", "combined", "curve picture", "ten-well model", "all-well model", "all-shale line"]
NAMES = {"combined": "combined (the teacher reading)"}


def md(df, floatfmt="{:.1f}"):
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                cells.append("" if pd.isna(v) else floatfmt.format(v))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main():
    H = pd.read_csv(S / "headline.csv").set_index("reader")
    W = pd.read_csv(S / "by_well.csv")
    M = pd.read_csv(S / "marks.csv").set_index("metric")
    CMP = pd.read_csv(S / "comparisons.csv")
    PD_ = pd.read_csv(S / "partd.csv")
    PV = pd.read_csv(S / "partd_vs_main.csv")
    m1 = pd.read_csv(C / "mark1.csv").iloc[0]
    pc = pd.read_csv(C / "power_check.csv").iloc[0]
    lc = pd.read_csv(C / "learning_curve.csv")
    cost = pd.read_csv(ROOT / "readings" / "costs.csv")
    freeze = (ROOT / "FREEZE").read_text().split()[2][:7]
    t = M.loc["tolerant_all_pct"]
    b = M.loc["balanced_all_pct"]
    s = M.loc["strict_all_pct"]

    def cmp(a, bb, metric="tolerant_all_pct"):
        r = CMP[(CMP.metric == metric) & (((CMP.reader_a == a) & (CMP.reader_b == bb)) | ((CMP.reader_a == bb) & (CMP.reader_b == a)))].iloc[0]
        ahead_a = r.wells_a_ahead if r.reader_a == a else r.wells_b_ahead
        ahead_b = r.wells_b_ahead if r.reader_a == a else r.wells_a_ahead
        return int(ahead_a), int(ahead_b), r.verdict

    ta, tb, _ = cmp("combined", "ten-well model")
    ca, cb, _ = cmp("curve picture", "ten-well model")
    ka, kb, _ = cmp("curve picture", "all-well model")
    aa, ab, _ = cmp("combined", "all-well model")

    L = []
    A = L.append
    A("# Reading pilot: report\n")
    A("First step of the teacher and student system. Written 16 November 2026. Branch "
      "`claude/focused-hypatia-k9i62o`. All 5 test wells were finished. Freeze commit: `" + freeze + "`. "
      "Scored on 53 071 depth steps (8 067 m) of the five test wells. "
      "The headline number is the tolerant agreement with unread depth counted as wrong.\n")
    A("## First screen\n")
    A("### The three marks (main model only)\n")
    marks = pd.DataFrame([
        {"mark": "1. Room", "verdict": f"**{m1.mark1.upper()}**",
         "numbers (headline, percent)": f"70-well model {m1.tolerant_70_wells_pct:.1f}; mean of the five ten-well draws "
         f"{m1.tolerant_10_wells_mean_of_5_draws_pct:.1f} (range {m1.ten_well_draws_min_pct:.1f} to {m1.ten_well_draws_max_pct:.1f}); "
         f"gap {m1.gap_points:.1f} points, 5 needed. On the 23 curve wells. A few expert wells are already enough here."},
        {"mark": "2. Teacher (combined reading)", "verdict": f"**{t.mark2.upper()}**",
         "numbers (headline, percent)": f"teacher {t.teacher_pct:.1f}; ten-well model {t.ten_well_pct:.1f} (teacher {t.teacher_pct - t.ten_well_pct:+.1f}, "
         f"ahead in {ta} of 5 wells, ten-well model ahead in {tb}); all-shale line {t.all_shale_pct:.1f} (teacher {t.teacher_minus_all_shale:+.1f}); "
         f"all-well model {t.all_well_pct:.1f} ({t.teacher_vs_all_well})."},
        {"mark": "3. Picture idea (curve pictures)", "verdict": f"**{t.mark3.upper()}**",
         "numbers (headline, percent)": f"curve picture {t.curve_picture_pct:.1f}; ten-well model {t.ten_well_pct:.1f}; gap {t.curve_picture_minus_ten_well:+.1f} points "
         f"(-5 or better needed; ahead in {ca} wells, behind in {cb}). Against the all-well model ({t.all_well_pct:.1f}): {t.curve_picture_minus_all_well:+.1f}, "
         f"{t.curve_picture_vs_all_well} (all-well model ahead in {kb} of 5 wells)."}])
    A(md(marks) + "\n")
    A("Would another score change a verdict?\n"
      f"- Mark 1: yes with the balanced agreement (gap {m1.gap_balanced_points:.1f} points, **{m1.mark1_if_balanced}**). No with the strict agreement (gap {m1.gap_strict_points:.1f}, {m1.mark1_if_strict}).\n"
      f"- Mark 2: yes with the balanced agreement (teacher {b.teacher_pct:.1f}, ten-well model {b.ten_well_pct:.1f}, all-well model {b.all_well_pct:.1f}: **{b.mark2}**). "
      f"No with the strict agreement (teacher {s.teacher_pct:.1f}, ten-well model {s.ten_well_pct:.1f}, all-shale {s.all_shale_pct:.1f}: {s.mark2}).\n"
      f"- Mark 3: no (balanced gap {b.curve_picture_minus_ten_well:+.1f}: {b.mark3}; strict gap {s.curve_picture_minus_ten_well:+.1f}: {s.mark3}).\n")

    A("### Headline number of every reader (pooled over the 5 test wells, percent)\n")
    rows = []
    for r in H.index:
        h = H.loc[r]
        rows.append({"reader": NAMES.get(r, r), "headline: tolerant, unread = wrong": h.tolerant_all_pct, "tolerant on read depth": h.tolerant_read_pct,
                     "coverage": h.coverage_pct, "strict": h.strict_all_pct, "soft": h.soft_all_pct, "balanced": h.balanced_all_pct})
    A(md(pd.DataFrame(rows)) + "\n")
    A("Readers with (Sonnet) or (Haiku) are the cheaper readers of Part D. They do not count for the marks.\n")

    A("### Cheaper readers against the main model (Part D)\n")
    pv = PV[PV.metric == "tolerant_all_pct"]
    rows = []
    for k in ["combined", "curve picture", "text", "log picture"]:
        for mname in ["Sonnet 5.5", "Haiku 5.5"]:
            r = pv[(pv.kind_of_reading == k) & (pv.model == mname)].iloc[0]
            rows.append({"reading": NAMES.get(k, k), "model": mname, "verdict": r.verdict, "main": r.main_pct, "cheaper": r.cheaper_pct,
                         "gap (points)": f"{r.gap_points_cheaper_minus_main:+.1f}", "wells cheaper ahead": int(r.wells_cheaper_ahead),
                         "wells main ahead": int(r.wells_main_ahead)})
    A(md(pd.DataFrame(rows)) + "\n")

    A((ROOT / "src" / "report_first_screen.md").read_text(encoding="utf-8").rstrip() + "\n")

    A("### Cost of the main readings (per well)\n")
    c = cost[~cost.reading.str.contains("set aside")]
    rows = []
    for w in c.well.unique():
        r = {"well": w}
        for k, short in [("curve picture", "curve"), ("log picture", "log"), ("text", "text")]:
            x = c[(c.well == w) & (c.reading == k)].iloc[0]
            r[f"{short}: minutes"] = x.minutes
            r[f"{short}: pictures"] = int(x.pictures_looked_at)
            if k == "text":
                r["text: pages read"] = int(x.pages_text_read)
        rows.append(r)
    tot = {"well": "all five"}
    for k, short in [("curve picture", "curve"), ("log picture", "log"), ("text", "text")]:
        x = c[c.reading == k]
        tot[f"{short}: minutes"] = round(float(x.minutes.sum()), 1)
        tot[f"{short}: pictures"] = int(x.pictures_looked_at.sum())
        if k == "text":
            tot["text: pages read"] = int(x.pages_text_read.sum())
    rows.append(tot)
    A(md(pd.DataFrame(rows)) + "\n")
    tk = c.groupby("reading").subagent_tokens.sum()
    A(f"Curve pictures: 20 of the pictures per well are the labelled examples. Text \"pictures\" are page pictures that the reader opened; "
      f"\"pages read\" are pages of page text. Tokens reported by the subagent tool, all five wells: curve picture {tk['curve picture']:,}, "
      f"log picture {tk['log picture']:,}, text {tk['text']:,}. Not in the table: the set-aside readings of 30/6-5 (15.4 minutes), "
      "the method trial (9 readers, 91 minutes of reader time) and the practice (8 readers, 92 minutes), run side by side.\n")

    A("### Cost and quality by model (Part D table)\n")
    p = PD_.rename(columns={"kind_of_reading": "reading", "headline_tolerant_all_pct": "headline", "coverage_pct": "coverage",
                            "balanced_all_pct": "balanced", "subagent_tokens": "tokens", "pages_text_read": "pages",
                            "pictures_looked_at": "pictures"})[["reading", "model", "headline", "coverage", "balanced", "minutes", "tokens", "pages", "pictures"]]
    p["tokens"] = p.tokens.map(lambda v: f"{v:,}")
    A(md(p) + "\n")
    A("Minutes, tokens, pages and pictures are sums over the five wells. The combined reading costs what its text and log-picture readings cost. "
      "Tokens are counts of tokens, not money: a token of a cheaper model costs less.\n")

    A((ROOT / "src" / "report_details.md").read_text(encoding="utf-8").rstrip() + "\n")

    # ---------------- detail tables ----------------
    A("## Tables\n")
    A("### T1. Learning curve of the plain model on the 23 curve wells (percent)\n")
    A(md(lc[["n_wells", "draws", "tolerant_mean", "tolerant_min", "tolerant_max", "strict_mean", "soft_mean", "balanced_mean"]]) + "\n")
    A("Chart: `curve/learning_curve.png`. Draws: `curve/learning_curve_draws.csv`.\n")
    A("### T2. Power check on the 23 curve wells (70-well model minus ten-well draws, headline, points)\n")
    A(md(pd.DataFrame([{"what": k.replace("_", " "), "value": v} for k, v in pc.items()])) + "\n")
    A("### T3. Headline number by well (percent)\n")
    A(md(W.pivot(index="reader", columns="well", values="tolerant_all_pct").reindex(list(H.index)).reset_index()) + "\n")
    A("### T4. Strict agreement by well (percent)\n")
    A(md(W.pivot(index="reader", columns="well", values="strict_all_pct").reindex(list(H.index)).reset_index()) + "\n")
    A("### T5. Coverage by well, document and picture readers of the main model (percent)\n")
    A(md(W.pivot(index="reader", columns="well", values="coverage_pct").reindex(MAIN[:4]).reset_index()) + "\n")
    B = pd.read_csv(S / "by_class.csv")
    p = B[B.reader.isin(MAIN[:6])].pivot(index="expert_class", columns="reader", values="tolerant_all_pct")[MAIN[:6]]
    p.insert(0, "metres of expert label", B[B.reader == "combined"].set_index("expert_class").metres)
    A("### T6. Headline number by expert rock class (percent)\n")
    A(md(p.sort_values("metres of expert label", ascending=False).reset_index()) + "\n")
    A("Classes with less than 20 m (Dolomite) do not enter the balanced agreement. Halite, Anhydrite, Chalk and Basement do not occur in the test wells.\n")
    E = pd.read_csv(S / "by_expert_confidence.csv")
    q = E[E.reader.isin(MAIN)].pivot(index="expert_confidence", columns="reader", values="tolerant_all_pct")[MAIN]
    q.insert(0, "metres", E[E.reader == "combined"].set_index("expert_confidence").metres)
    A("### T7. Headline number by the experts' confidence level (percent)\n")
    A(md(q.reset_index()) + "\n")
    A("### T8. Which classes get mixed up: the teacher reading (metres; rows = expert class, columns = teacher class)\n")
    A(md(pd.read_csv(S / "confusion_combined.csv")) + "\n")
    A("### T9. Which classes get mixed up: the curve-picture reading (metres)\n")
    A(md(pd.read_csv(S / "confusion_curve_picture.csv")) + "\n")
    A("The same tables for every other reader are in `scores/confusion_*.csv`.\n")
    A("### T10. Pairs of main readers (headline; ahead needs 5 points and 4 of 5 wells)\n")
    c2 = CMP[(CMP.metric == "tolerant_all_pct") & CMP.reader_a.isin(MAIN) & CMP.reader_b.isin(MAIN)]
    A(md(c2[["reader_a", "reader_b", "a_pct", "b_pct", "gap_points_a_minus_b", "wells_a_ahead", "wells_b_ahead", "verdict"]]) + "\n")
    A("All pairs and the same for strict and balanced agreement: `scores/comparisons.csv`.\n")
    A("### T11. Where text and log picture agree with each other\n")
    ag = pd.read_csv(S / "text_vs_log_picture.csv")
    A(md(ag[["well", "share_same_class_of_all_pct", "share_same_family_of_both_read_pct", "strict_where_same_pct", "tolerant_where_same_pct",
             "differ_metres", "strict_text_where_differ_pct", "strict_log_where_differ_pct"]]) + "\n")
    A("### T12. Side numbers: tolerant agreement if the second class of a document reading also counts (not used for any mark)\n")
    sc = pd.read_csv(S / "second_class_side.csv")
    A(md(sc[sc.well == "POOLED"][["reader", "tolerant_main_only", "tolerant_with_second_class"]]) + "\n")
    A("### T13. The set-aside first log-picture reading of 30/6-5, scored once after the freeze (that well only)\n")
    A(md(pd.read_csv(S / "side_set_aside_30_6-5_log_picture.csv")) + "\n")
    A("### T14. Cheaper readers against the main reader of the same kind, all three scores\n")
    A(md(PV[["metric", "kind_of_reading", "model", "main_pct", "cheaper_pct", "gap_points_cheaper_minus_main", "wells_cheaper_ahead",
             "wells_main_ahead", "verdict"]]) + "\n")
    A("### T15. Conflicts: teacher class of another family than the expert label, intervals of 3 m or more\n")
    A(md(pd.read_csv(ROOT / "conflicts" / "conflicts_all_summary_by_teacher_class.csv")) + "\n")
    (ROOT / "report.md").write_text("\n".join(L), encoding="utf-8")
    print("report.md written:", sum(len(x) for x in L), "characters")


if __name__ == "__main__":
    main()
