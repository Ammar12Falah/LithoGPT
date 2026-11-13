"""Netherlands loader: cleaned input tables -> holes, picks, name map, log.

Input: data/netherlands_wells.csv.gz (NLOG "All boreholes" list) and
data/netherlands_tops.csv.gz (NLOG lithostratigraphy of all boreholes, file
of 23 September 2026), columns used only.

A "hole" here is one wellbore (a borehole or a sidetrack) with the picks it
drilled itself. A sidetrack is never a test well: it is part of the hole
system of its mother borehole. Its own picks can serve as known data once it
is finished.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

TEST_START = pd.Timestamp("1990-01-01")
FILE_DATE = pd.Timestamp("2026-09-23")
MIN_DATE = pd.Timestamp("1900-01-01")
LEVELS = {"member": None, "formation": 4, "group": 2}
BAD_TOP = {"UKO", "UF", "U"}          # upper boundary is a kick-off point, a fault, or uncertain


def _anomaly_codes(a):
    """Codes that apply to the top of the interval. Where an interval runs
    from one borehole into a sidetrack the file lists the codes of both
    pieces, separated by a comma; the first piece holds the top."""
    if not isinstance(a, str) or not a:
        return set()
    return set(a.split(",")[0].strip().split("_"))


def _rank(code, name):
    last = name.str.lower().str.replace(r"\s*\(inf\.\)$", "", regex=True).str.split().str[-1]
    r = last.map({"member": "member", "mb": "member", "formation": "formation", "group": "group", "groep": "group",
                  "subgroup": "subgroup", "subgroep": "subgroup", "supergroup": "supergroup"}).fillna("other unit")
    r = r.mask(code.eq("NN"), "not interpreted")
    r = r.mask(code.isin(["FAULT", "FLT_N", "FLT_R"]), "fault")
    return r


def load():
    log = []

    def note(step, recs, holes, detail=""):
        log.append(dict(step=step, well_records=int(recs), holes=int(holes), detail=detail))

    w = pd.read_csv(DATA / "netherlands_wells.csv.gz", dtype=str)
    t = pd.read_csv(DATA / "netherlands_tops.csv.gz", dtype=str)
    for c in ["TOP_AH", "BOTTOM_AH", "TV_TOP_NAP", "X_TOP_UTM31_ED50", "Y_TOP_UTM31_ED50"]:
        t[c] = pd.to_numeric(t[c], errors="coerce")
    w["start"] = pd.to_datetime(w["START_DATE_DRILLING"], errors="coerce")
    w["end"] = pd.to_datetime(w["END_DATE_DRILLING"], errors="coerce")
    bad = (w["end"] < MIN_DATE) | (w["end"] > FILE_DATE) | (w["start"] < MIN_DATE) | (w["start"] > FILE_DATE) | (w["end"] < w["start"])
    n_bad_dates = int(bad.sum())
    w.loc[bad, ["start", "end"]] = pd.NaT
    w["x"] = pd.to_numeric(w["X_UTM31_ED50"], errors="coerce")
    w["y"] = pd.to_numeric(w["Y_UTM31_ED50"], errors="coerce")
    w["ref_h"] = pd.to_numeric(w["REFERENCE_LEVEL_HEIGHT"], errors="coerce")
    wi = w.set_index("BOREHOLE_CODE")

    note("0. all boreholes in the NLOG list", len(w), len(w),
         f"{int((w['BOREHOLE_OR_SIDETRACK_CODE'] == 'STR').sum())} of them are sidetracks. "
         f"Shape: {w['BOREHOLE_SHAPE'].value_counts().to_dict()}.")
    note("1. wellbores with lithostratigraphy rows", t["WELLBORE"].nunique(), t["WELLBORE"].nunique(), f"{len(t)} rows")

    # ---- the borehole that drilled the top of each interval --------------
    t["src"] = t["DATA_SOURCE"].str.split(" --> ").str[0].str.strip()
    t = t.sort_values(["WELLBORE", "TOP_AH", "BOTTOM_AH"]).reset_index(drop=True)
    # the interval directly above, in the same wellbore table
    prev_same = t["WELLBORE"].eq(t["WELLBORE"].shift())
    t["above_cd"] = t["STRAT_UNIT_CD"].shift().where(prev_same)
    t["above_nm"] = t["STRAT_UNIT_NM"].shift().where(prev_same)
    t["above_bottom"] = t["BOTTOM_AH"].shift().where(prev_same)
    t["rank"] = _rank(t["STRAT_UNIT_CD"], t["STRAT_UNIT_NM"])
    above_rank = t["rank"].shift().where(prev_same)
    codes = t["ANOMALY_CD"].map(_anomaly_codes)
    t["m_unit"] = t["rank"].isin(["member", "formation", "subgroup", "group"])
    t["m_xyz"] = t["TV_TOP_NAP"].notna() & t["X_TOP_UTM31_ED50"].notna() & t["Y_TOP_UTM31_ED50"].notna()
    t["m_above"] = prev_same & above_rank.notna() & ~above_rank.isin(["not interpreted", "fault"]) & \
        ((t["above_bottom"] - t["TOP_AH"]).abs() <= 0.01)
    t["m_top_ok"] = ~codes.map(lambda s: bool(s & BAD_TOP))
    # check of the vertical reference: first interval at 0 m along hole
    first = t[~prev_same & (t["TOP_AH"] == 0)].copy()
    first["ref_h"] = first["WELLBORE"].map(wi["ref_h"])
    dref = (first["TV_TOP_NAP"] + first["ref_h"]).abs()
    ref_mismatch = set(first.loc[dref > 1.0, "WELLBORE"])
    ref_note = (f"Check of the vertical reference: in {len(first)} wellbores the first interval starts at 0 m along hole; there the "
                f"vertical depth should be minus the reference height of the borehole list. It agrees within 0.05 m in "
                f"{float((dref <= 0.05).mean()) * 100:.1f} % and within 1 m in {float((dref <= 1.0).mean()) * 100:.1f} %.")

    def keep(col, step, detail=""):
        nonlocal t
        t = t[t[col]]
        note(step, t["WELLBORE"].nunique(), t["src"].nunique(), f"{len(t)} rows left. {detail}")

    keep("m_unit", "2. row is a named member, formation, subgroup or group",
         "Dropped: 'NOT INTERPRETED', fault rows, the North Sea Supergroup and informal units (Zechstein salt, caprock, igneous rock).")
    keep("m_xyz", "3. true vertical depth and position of the top present")
    keep("m_above", "4. the top is a drilled boundary under an interpreted interval",
         "Dropped: the first interval of each wellbore (its top is the surface or the start of the description), "
         "and tops under a 'NOT INTERPRETED' interval, a fault row or a gap.")
    keep("m_top_ok", "5. top not at a kick-off point, not a fault, not marked uncertain",
         "Dropped: anomaly codes UKO, UF and U on the upper boundary. Tops that are unconformities (UU) are kept.")
    # the same pick is listed in the table of the mother borehole and of every sidetrack that passes it
    t["own"] = t["WELLBORE"] == t["src"]
    t = t.sort_values(["STELSEL", "src", "STRAT_UNIT_CD", "TOP_AH", "own"], ascending=[True, True, True, True, False])
    n_before = len(t)
    t = t.drop_duplicates(["STELSEL", "src", "STRAT_UNIT_CD", "TOP_AH"], keep="first")
    note("6. each pick once", t["WELLBORE"].nunique(), t["src"].nunique(),
         f"{len(t)} rows left. {n_before - len(t)} copies removed: a pick above a kick-off point appears in the table of the "
         f"mother borehole and of each sidetrack.")
    t["m_listed"] = t["src"].isin(wi.index) & t["STELSEL"].isin(wi.index)
    keep("m_listed", "7. borehole found in the borehole list",
         "The borehole that drilled the top, and the mother borehole of its system, must be in the list.")
    t["elev_m"] = -t["TV_TOP_NAP"]          # NAP (onshore) or mean sea level (offshore), positive up

    # ---- one level of the naming scheme ----------------------------------
    t["end"] = t["src"].map(wi["end"])
    cd = t["STRAT_UNIT_CD"]
    form_codes = set(cd[t["rank"] == "formation"])
    group_codes = set(cd[t["rank"] == "group"])
    lvl = {}
    lvl["member"] = t[t["rank"] == "member"].assign(top=cd)
    lvl["formation"] = t[t["rank"].isin(["member", "formation"]) & cd.str[:4].isin(form_codes)].assign(top=cd.str[:4])
    lvl["group"] = t[cd.str[:2].isin(group_codes)].assign(top=cd.str[:2])
    level_rows = []
    picks_lvl = {}
    for name, df in lvl.items():
        df = df.sort_values(["src", "top", "TOP_AH"])
        if name != "member":
            # rolled up: the top of a formation or group is the top of its first interval;
            # it is a top only if the interval above belongs to another unit of that level
            n = LEVELS[name]
            df = df[df["above_cd"].str[:n] != df["top"]]
        rep = df.duplicated(["src", "top"], keep=False)
        p = df.drop_duplicates(["src", "top"], keep="first")
        picks_lvl[name] = (p, int(df.loc[rep, ["src", "top"]].drop_duplicates().shape[0]))
        pre = p[p["end"] < TEST_START]
        level_rows.append(dict(level=name, hole_top_values=len(p), hole_top_values_finished_before_1990=len(pre),
                               units=p["top"].nunique(), holes=p["src"].nunique()))
    levels = pd.DataFrame(level_rows)
    best = levels.sort_values("hole_top_values_finished_before_1990", ascending=False)["level"].iloc[0]
    levels["chosen"] = levels["level"] == best
    p, n_rep = picks_lvl[best]
    note(f"8. one level of the naming scheme: {best}", p["WELLBORE"].nunique(), p["src"].nunique(),
         f"{len(p)} hole-top values. Hole-top values per level (all / finished before 1990): "
         + "; ".join(f"{r.level} {r.hole_top_values} / {r.hole_top_values_finished_before_1990}" for r in levels.itertuples())
         + f". The level with the most values in holes finished before 1990 is used. "
         f"{n_rep} hole-unit pairs had the unit more than once in one hole (fault repeats and the like): the shallowest is used.")

    names = t.drop_duplicates("STRAT_UNIT_CD").set_index("STRAT_UNIT_CD")["STRAT_UNIT_NM"]
    n = LEVELS[best]
    if best == "member":
        name_map = pd.DataFrame({"source_code": p["top"].unique()})
        name_map["canonical_code"] = name_map["source_code"]
    else:
        name_map = t[["STRAT_UNIT_CD"]].drop_duplicates().rename(columns={"STRAT_UNIT_CD": "source_code"})
        name_map["canonical_code"] = name_map["source_code"].str[:n]
    name_map["source_name"] = name_map["source_code"].map(names)
    name_map["canonical_name"] = name_map["canonical_code"].map(names)
    name_map["rule"] = np.where(name_map["source_code"] == name_map["canonical_code"], "same",
                                f"rolled up to its {best} (first {n} letters of the code)")
    label = (p["top"] + " " + p["top"].map(names).fillna("")).str.strip()

    picks = pd.DataFrame({
        "hole_id": p["src"].to_numpy(), "record_id": p["src"].to_numpy(), "top": label.to_numpy(),
        "elev_m": p["elev_m"].to_numpy(), "avail": p["end"].to_numpy(),
        "px": p["X_TOP_UTM31_ED50"].to_numpy(), "py": p["Y_TOP_UTM31_ED50"].to_numpy(),
        "system": p["STELSEL"].to_numpy()})

    # ---- holes ------------------------------------------------------------
    sysmap = picks.drop_duplicates("hole_id").set_index("hole_id")["system"]
    h = wi.loc[sysmap.index, ["x", "y", "start", "end", "BOREHOLE_SHAPE", "BOREHOLE_OR_SIDETRACK_CODE",
                              "REFERENCE_LEVEL", "REFERENCE_LEVEL_RELATIVE_TO", "ON_OFFSHORE_CODE"]].copy()
    h.index.name = "hole_id"
    h["system"] = sysmap
    mother = (h.index == h["system"]) & (h["BOREHOLE_OR_SIDETRACK_CODE"] != "STR")
    h["test_date"] = h["end"]
    h["rule_date"] = h["start"]
    h["eligible"] = mother & (h["end"] >= TEST_START) & h["start"].notna()
    h["pre_test"] = h["end"] < TEST_START
    h["loc_precise"] = True
    h["flag_elev"] = np.where(h.index.isin(ref_mismatch),
                              "reference height in the borehole list and in the lithostratigraphy file differ by more than 1 m", "")
    h["flag_loc"] = np.where(h["BOREHOLE_SHAPE"] == "Vertical", "", "not vertical: " + h["BOREHOLE_SHAPE"].fillna("shape unknown"))
    h["side_clean"] = (h["BOREHOLE_SHAPE"] == "Vertical") & (h["flag_elev"] == "")
    h = h.reset_index()
    note("9. holes in the analysis (a hole = a borehole or sidetrack with tops it drilled itself)", len(h), len(h),
         f"{int((h['BOREHOLE_SHAPE'] == 'Vertical').sum())} vertical, {int((h['BOREHOLE_SHAPE'] == 'Deviated').sum())} deviated, "
         f"{int((h['BOREHOLE_SHAPE'] == 'Horizontal').sum())} horizontal. Deviated and horizontal holes are kept, because the file gives "
         f"the true vertical depth and the position of every top. {int((h['flag_elev'] != '').sum())} holes flagged because the reference "
         f"height differs by more than 1 m between the two files (flagged, kept). " + ref_note)
    note("10. holes with valid drilling dates", 0, int(h["end"].notna().sum()),
         f"finished before 1990: {int(h['pre_test'].sum())}; can be a test well (mother borehole, not a sidetrack, finished in 1990 or later): "
         f"{int(h['eligible'].sum())}. {n_bad_dates} boreholes in the list had dates outside 1900 to 23 Sep 2026 or an end before the start; "
         f"their dates were treated as missing.")

    extra = dict(name_map=name_map, variant_evidence=None, floor_b_pairs=None, levels=levels)
    return h, picks, pd.DataFrame(log), extra
