"""Kansas loader: cleaned input tables -> holes, picks, name map, cleaning log.

Input: data/kansas_wells.csv.gz, data/kansas_tops.csv.gz (Kansas Geological
Survey statewide files of 9 October 2026, columns used only).
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Proj

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

FT = 0.3048
FILE_DATE = pd.Timestamp("2026-10-09")  # date printed on the KGS download page
TEST_START = pd.Timestamp("2000-01-01")
MIN_DATE = pd.Timestamp("1860-01-01")

# Lambert conformal conic on the NAD27 ellipsoid, centred on Kansas. The KGS
# coordinates are NAD27; no datum shift is applied, only a map projection.
PROJ = Proj("+proj=lcc +lat_1=37.5 +lat_2=39.5 +lat_0=38.5 +lon_0=-98.5 "
            "+x_0=0 +y_0=0 +ellps=clrk66 +units=m +no_defs")

DEVIATED_RE = re.compile(
    r"horizontal|directional|deviat|slant|side[- ]?track|whipstock|\bBHL\b|"
    r"bottom[- ]?hole loc|\bTVD\b", re.I)

# Spelling variants of the same top (short name or informal name -> KGS
# formal name). Only names that mean the same marker are merged. Evidence
# (wells that carry both names, and the depth difference) is written to the
# name-map file by build_name_map().
VARIANTS = {
    # short name used in recent completion and geological reports -> formal name
    "Lansing": "Lansing Group",
    "Lansing-Kansas City": "Lansing Group",            # top of the Lansing-Kansas City interval = top of the Lansing
    "Lansing - Kansas City Supergroup": "Lansing Group",
    "Heebner": "Heebner Shale Member",
    "Heebner Shale": "Heebner Shale Member",
    "Stone Corral": "Stone Corral Formation",
    "Stone Corral Anhydrite": "Stone Corral Formation",
    "Anhydrite": "Stone Corral Formation",              # the drillers' "Anhydrite" of Kansas reports (see evidence file)
    "Kansas City": "Kansas City Group",
    "Mississippian": "Mississippian System",
    "Mississippi": "Mississippian System",
    "Miss": "Mississippian System",
    "Arbuckle": "Arbuckle Group",
    "Toronto": "Toronto Limestone Member",
    "Toronto Limestone": "Toronto Limestone Member",
    "Topeka": "Topeka Limestone Formation",
    "Cherokee": "Cherokee Group",
    "Marmaton": "Marmaton Group",
    "Fort Scott": "Fort Scott Limestone Formation",
    "Simpson": "Simpson Group",
    "Winfield": "Winfield Limestone Formation",
    "Chase": "Chase Group",
    "Viola": "Viola Limestone Formation",
    "Krider": "Krider Limestone Member",
    "Herington": "Herington Limestone Member",
    "Pawnee": "Pawnee Limestone Formation",
}


def _dates(s):
    d = pd.to_datetime(s, format="%d-%b-%Y", errors="coerce")
    bad = d.notna() & ((d < MIN_DATE) | (d > FILE_DATE))
    return d.mask(bad), int(bad.sum())


def build_name_map(tops):
    """FORMATION -> canonical name. Returns (map_df, series canonical)."""
    raw = tops["FORMATION"].fillna("")
    norm = raw.str.replace(r"\s+", " ", regex=True).str.strip()
    key = norm.str.casefold()
    counts = pd.DataFrame({"key": key, "name": norm}).groupby(["key", "name"]).size().rename("n").reset_index()
    # most frequent spelling of each case/space-insensitive key
    best = counts.sort_values(["key", "n", "name"], ascending=[True, False, True]).drop_duplicates("key")
    key2best = dict(zip(best["key"], best["name"]))
    stage1 = key.map(key2best)
    var_cf = {k.casefold(): v for k, v in VARIANTS.items()}
    canon = stage1.str.casefold().map(var_cf).fillna(stage1)
    m = pd.DataFrame({"source_name": raw, "canonical_name": canon})
    mp = m.groupby(["source_name", "canonical_name"]).size().rename("n_top_rows").reset_index()
    def rule(r):
        if r.source_name == r.canonical_name:
            return "same"
        if r.source_name.casefold().strip() in var_cf or key2best.get(r.source_name.casefold().strip(), "").casefold() in var_cf:
            return "spelling variant of the same top (manual list)"
        return "upper/lower case or spacing variant"
    mp["rule"] = mp.apply(rule, axis=1)
    return mp.sort_values("n_top_rows", ascending=False).reset_index(drop=True), canon


def variant_evidence(tops, canon):
    """For each merged variant: records that carry both the variant and the
    canonical spelling, and the depth difference between them."""
    t = tops.assign(canon=canon, top=pd.to_numeric(tops["TOP"], errors="coerce")).dropna(subset=["top"])
    rows = []
    var_cf = {k.casefold(): v for k, v in VARIANTS.items()}
    names = t["FORMATION"].str.replace(r"\s+", " ", regex=True).str.strip()
    for src in sorted(set(names[names.str.casefold().isin(var_cf)])):
        tgt = var_cf[src.casefold()]
        a = t[names == src].groupby("KID")["top"].median()
        b = t[names == tgt].groupby("KID")["top"].median()
        j = pd.concat([a, b], axis=1, keys=["a", "b"]).dropna()
        d = (j["a"] - j["b"]).abs()
        rows.append(dict(source_name=src, canonical_name=tgt, records_with_variant=len(a),
                         records_with_both=len(j),
                         median_abs_depth_diff_ft=float(d.median()) if len(j) else np.nan,
                         share_identical=float((d == 0).mean()) if len(j) else np.nan,
                         share_within_10ft=float((d <= 10).mean()) if len(j) else np.nan))
    return pd.DataFrame(rows)


def load():
    log = []

    def note(step, recs, holes, detail=""):
        log.append(dict(step=step, well_records=int(recs), holes=int(holes), detail=detail))

    w = pd.read_csv(DATA / "kansas_wells.csv.gz", dtype=str)
    t = pd.read_csv(DATA / "kansas_tops.csv.gz", dtype=str)

    # ---- records -------------------------------------------------------
    api = w["API_NUM_NODASH"]
    w["hole_id"] = np.where(api.notna(), "API" + api.str[:10], "KID" + w["KID"])
    w["suffix"] = api.str[10:].fillna("")
    bad_dates = {}
    for c in ["SPUD", "COMPLETION", "PLUGGING"]:
        w[c.lower()], bad_dates[c] = _dates(w[c])
    w["elev_ft"] = pd.to_numeric(w["ELEVATION"], errors="coerce")
    w["td_ft"] = pd.to_numeric(w["DEPTH"], errors="coerce")
    w["lat"] = pd.to_numeric(w["LATITUDE"], errors="coerce")
    w["lon"] = pd.to_numeric(w["LONGITUDE"], errors="coerce")
    x, y = PROJ(w["lon"].to_numpy(), w["lat"].to_numpy())
    w["x"] = x
    w["y"] = y
    # finish date of a record: completion date; if the spud date is later
    # (a date error) the later one; if no completion date, the plugging date
    fin = w["completion"].copy()
    both = fin.notna() & w["spud"].notna() & (w["spud"] > fin)
    fin[both] = w.loc[both, "spud"]
    nofin = fin.isna() & w["plugging"].notna() & (w["spud"].isna() | (w["plugging"] >= w["spud"]))
    fin[nofin] = w.loc[nofin, "plugging"]
    w["finish"] = fin
    w["deviated_code"] = (w["suffix"].str[:2] != "00") & (w["suffix"] != "")
    w["deviated_text"] = w["COMMENTS"].fillna("").str.contains(DEVIATED_RE)
    w["loc_ok"] = w["LONG_LAT_SOURCE"].isin(["Calc. from footages", "From GPS", "Calc. from quarter calls"]) \
        & w["lat"].between(36.9, 40.1) & w["lon"].between(-102.1, -94.5)
    w["loc_precise"] = w["LONG_LAT_SOURCE"].isin(["Calc. from footages", "From GPS"])

    # ---- duplicate records of one hole filed under different numbers ----
    # Same position, same elevation, same total depth and same spud date
    # (all present): treated as one hole.
    k = w[w["td_ft"].notna() & w["elev_ft"].notna() & w["spud"].notna()].copy()
    k["dupkey"] = (k["lat"].round(6).astype(str) + "|" + k["lon"].round(6).astype(str) + "|" +
                   k["elev_ft"].astype(str) + "|" + k["td_ft"].astype(str) + "|" + k["spud"].astype(str))
    first = k.groupby("dupkey")["hole_id"].transform("min")
    differs = k["hole_id"] != first
    remap = dict(zip(k.loc[differs, "hole_id"], first[differs]))
    n_dup_holes = len(remap)
    w["hole_id"] = w["hole_id"].map(lambda h: remap.get(h, h))

    # ---- hole-level dates (from every record of the hole) --------------
    g = w.groupby("hole_id")
    drilled = ~w["STATUS"].isin(["INTENT", "LOC"])
    first_spud = g["spud"].min()
    min_other = pd.concat([g["completion"].min(), g["plugging"].min()], axis=1).min(axis=1)
    undated_drilled = (drilled & w["spud"].isna()).groupby(w["hole_id"]).any()
    eligible = (first_spud >= TEST_START) & ~(min_other < TEST_START) & ~undated_drilled
    pre_test = first_spud < TEST_START

    # ---- top rows ------------------------------------------------------
    n_rows0 = len(t)
    t = t.merge(w[["KID", "hole_id", "elev_ft", "ELEV_REF", "td_ft", "finish", "deviated_code",
                   "deviated_text", "loc_ok", "loc_precise", "LONG_LAT_SOURCE"]],
                on="KID", how="left", suffixes=("", "_w"))
    note("0. all records in the wells file", len(w), w["hole_id"].nunique(),
         f"{n_dup_holes} holes merged into another hole as duplicates (same position, elevation, depth, spud date)")
    note("1. records with at least one top row", t["KID"].nunique(), t["hole_id"].nunique(), f"{n_rows0} top rows")

    name_map, canon = build_name_map(t)
    evidence = variant_evidence(t, canon)
    t["top"] = canon
    t["depth_ft"] = pd.to_numeric(t["TOP"], errors="coerce")
    t["elev_t"] = pd.to_numeric(t["ELEVATION"], errors="coerce")
    t["ref_t"] = t["ELEV_REF"].fillna("")

    def keep(mask, step, detail=""):
        nonlocal t
        t = t[mask]
        note(step, t["KID"].nunique(), t["hole_id"].nunique(), f"{len(t)} top rows left. {detail}")

    keep(t["depth_ft"].notna() & (t["depth_ft"] > 0) & (t["depth_ft"] <= 12000),
         "2. top depth present, above 0 and not over 12,000 ft",
         "Rows with no top depth (base only), zero or negative depth, or a depth deeper than any Kansas well are dropped.")
    keep(~(t["td_ft"].notna() & (t["depth_ft"] > t["td_ft"] + 50)),
         "3. top not deeper than the well's total depth plus 50 ft",
         "A pick below the bottom of the hole is a data error.")
    mism = t["elev_t"].notna() & t["elev_ft"].notna() & ((t["elev_t"] != t["elev_ft"]) | (t["ref_t"] != t["ELEV_REF_w"].fillna("")))
    keep(t["elev_t"].notna() & (t["ref_t"] != "") & ~mism,
         "4. elevation and its reference present, and the same in the wells file and the tops file",
         f"{int(mism.sum())} top rows had a different elevation or reference in the two files.")
    keep(t["loc_ok"].fillna(False),
         "5. usable position",
         "Dropped: position given only as the centre of the section (up to about 1 km off), unknown source, or outside Kansas.")
    keep(~(t["deviated_code"] | t["deviated_text"]),
         "6. not horizontal or deviated",
         "Dropped: records whose API number carries a sidetrack code (digits 11-12 not 00, the KGS's own rule for its "
         "horizontal-well list) or whose comment mentions horizontal, directional, deviated, slant, sidetrack, whipstock, "
         "BHL or TVD. The file gives no true vertical depth or top position for them.")

    t["elev_top_ft"] = t["elev_t"] - t["depth_ft"]
    t["elev_m"] = t["elev_top_ft"] * FT
    t["flag_elev"] = np.where(t["ref_t"].isin(["KB", "DF"]), "",
                              np.where(t["ref_t"] == "GL", "GL: ground-level elevation, depth datum not stated",
                                       np.where(t["ref_t"] == "TOPO", "TOPO: elevation estimated from a digital model",
                                                "other reference")))

    # ---- one value per record and top (several sources may give picks) --
    pk_all = t[["hole_id", "top", "elev_m", "SOURCE"]].copy()
    rec = t.groupby(["hole_id", "KID", "top"], sort=False).agg(
        elev_m=("elev_m", "median"), lo=("elev_m", "min"), hi=("elev_m", "max"),
        n_picks=("elev_m", "size"), finish=("finish", "first"), flag_elev=("flag_elev", "first")).reset_index()
    wide = (rec["hi"] - rec["lo"]) > 100 * FT
    n_wide = int(wide.sum())
    rec = rec[~wide]
    # ---- one value per hole and top: the earliest finished record -------
    rec["fin_sort"] = rec["finish"].fillna(pd.Timestamp("2262-01-01"))
    rec = rec.sort_values(["hole_id", "top", "fin_sort", "KID"])
    multi = rec.duplicated(["hole_id", "top"], keep=False).sum()
    picks = rec.drop_duplicates(["hole_id", "top"], keep="first").drop(columns=["fin_sort", "lo", "hi"])
    picks = picks.rename(columns={"KID": "record_id", "finish": "avail"})
    note("7. one elevation per hole and top", picks["record_id"].nunique(), picks["hole_id"].nunique(),
         f"{len(picks)} hole-top values. Picks of one top in one record from several sources: the median. "
         f"{n_wide} record-top groups dropped because their picks disagree by more than 100 ft. "
         f"Records of one hole (re-entries, workovers; same first 10 digits of the API number): the earliest finished record "
         f"that reports the top is used ({int(multi)} record-top values were in holes with more than one record for that top).")

    # ---- holes table ---------------------------------------------------
    used = w[w["hole_id"].isin(picks["hole_id"])].copy()
    used["has_tops"] = used["KID"].isin(picks["record_id"])
    used = used.sort_values(["hole_id", "has_tops", "suffix", "KID"], ascending=[True, False, True, True])
    spread = used.groupby("hole_id").agg(xmin=("x", "min"), xmax=("x", "max"), ymin=("y", "min"), ymax=("y", "max"))
    moved = np.hypot(spread["xmax"] - spread["xmin"], spread["ymax"] - spread["ymin"]) > 30
    h = used.drop_duplicates("hole_id", keep="first")[["hole_id", "x", "y", "lat", "lon", "loc_precise", "LONG_LAT_SOURCE"]]
    h = h.set_index("hole_id")
    h["n_records"] = used.groupby("hole_id").size()
    h["first_spud"] = first_spud.reindex(h.index)
    h["eligible"] = eligible.reindex(h.index).fillna(False)
    h["pre_test"] = pre_test.reindex(h.index).fillna(False)
    h["test_date"] = h["first_spud"]
    h["rule_date"] = h["first_spud"]
    h["flag_records_moved"] = moved.reindex(h.index).fillna(False)
    fe = picks[picks["flag_elev"] != ""].groupby("hole_id")["flag_elev"].first()
    h["flag_elev"] = fe.reindex(h.index).fillna("")
    h["flag_loc"] = np.where(h["loc_precise"], "", "position from quarter calls (centre of the smallest quarter given)")
    h = h.reset_index()
    note("8. holes in the analysis", picks["record_id"].nunique(), len(h),
         f"{int((h['flag_elev'] != '').sum())} holes flagged for elevation (GL or TOPO), "
         f"{int((~h['loc_precise']).sum())} flagged for position from quarter calls, "
         f"{int(h['flag_records_moved'].sum())} holes whose records sit more than 30 m apart. Flagged holes are kept.")
    note("9. holes with a valid first spud date", 0, int(h["first_spud"].notna().sum()),
         f"spud before 2000: {int(h['pre_test'].sum())}; can be a test well (every drilled record spudded in 2000 or later, "
         f"no completion or plugging date before 2000): {int(h['eligible'].sum())}. "
         f"Dates outside 1860 to 9 Oct 2026 were treated as missing: {bad_dates}.")
    note("10. holes whose tops can serve as known wells (finish date present)", 0,
         int(picks.loc[picks['avail'].notna(), 'hole_id'].nunique()),
         "Finish date = completion date; the spud date if it is later; the plugging date if there is no completion date. "
         "Holes with none of these are never used as known wells.")

    # ---- floor B: two picks of one top in one hole from different sources -
    src = pk_all.groupby(["hole_id", "top", "SOURCE"], sort=False)["elev_m"].median().reset_index()
    src = src[src.duplicated(["hole_id", "top"], keep=False)]
    pb = src.merge(src, on=["hole_id", "top"], suffixes=("_a", "_b"))
    pb = pb[pb["SOURCE_a"] < pb["SOURCE_b"]].copy()
    pb["abs_diff_m"] = (pb["elev_m_a"] - pb["elev_m_b"]).abs()

    extra = dict(name_map=name_map, variant_evidence=evidence,
                 floor_b_pairs=pb[["hole_id", "top", "SOURCE_a", "SOURCE_b", "abs_diff_m"]])
    return h, picks, pd.DataFrame(log), extra
