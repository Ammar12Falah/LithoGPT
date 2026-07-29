#!/usr/bin/env python3
"""DL Q3: pooled depth range, full precision, two masks, over the 8 FORCE test wells.
Read-only: no fitting, no figures. Cross-checked against the sealed v3 raw-results JSON
(scored window) and the raw FORCE CSV (full four-curve-valid window)."""
import json
import numpy as np
import pandas as pd

RAW_PATH = "/Users/ammar/LithoGPT_archive/atce_ablation_v3_raw_results_2026-07-26.json"
FORCE_CSV = "/Users/ammar/LithoGPT_archive/force2020_data/train.csv"
FEATURES = ["GR", "RDEP", "NPHI", "RHOB"]

with open(RAW_PATH) as f:
    raw = json.load(f)
WELLS = list(raw["A"].keys())

print("=" * 100)
print("Q3a. SCORED WINDOW pooled depth range, 8 test wells")
print("mask: rows of feats_real[prime_n:prime_n+gen_len] per well, i.e. the interval actually")
print("scored during generation (item P), read from depth_min_m/depth_max_m recorded per well")
print("in the sealed v3 raw-results JSON (identical across all 6 arms -- same test wells/window).")
print("=" * 100)
for arm in raw:
    mins = [raw[arm][w]["depth_min_m"] for w in raw[arm]]
    maxs = [raw[arm][w]["depth_max_m"] for w in raw[arm]]
    print(f"  arm {arm:10s} pooled min={min(mins):.10g}  pooled max={max(maxs):.10g}")
per_well_scored = {w: (raw["A"][w]["depth_min_m"], raw["A"][w]["depth_max_m"]) for w in WELLS}
scored_min = min(v[0] for v in per_well_scored.values())
scored_max = max(v[1] for v in per_well_scored.values())
print("\nper-well (arm A, representative -- identical for all arms):")
for w, (lo, hi) in per_well_scored.items():
    print(f"    {w:10s} {lo:.10g} .. {hi:.10g}")
print(f"\nPOOLED SCORED RANGE: min={scored_min:.10g} m  max={scored_max:.10g} m")
print(f"  claim on record: 1295.6 m to 3897.3 m -> {'MATCHES' if round(scored_min,1)==1295.6 and round(scored_max,1)==3897.3 else 'MISMATCH'}")

print("\n" + "=" * 100)
print("Q3b. FULL VALID FOUR-CURVE WINDOW pooled depth range, 8 test wells")
print("mask: np.isfinite(GR,RDEP,NPHI,RHOB).all(axis=1) per row, applied directly to the raw")
print("FORCE train.csv (';'-separated), independent of any generation/priming window.")
print("=" * 100)
df = pd.read_csv(FORCE_CSV, sep=";")
total = 0
mins2, maxs2 = [], []
for w in WELLS:
    sub = df[df["WELL"] == w]
    mask = np.isfinite(sub[FEATURES].to_numpy(dtype=np.float64)).all(axis=1)
    depths = sub["DEPTH_MD"].to_numpy(dtype=np.float64)[mask]
    total += int(mask.sum())
    mins2.append(float(depths.min())); maxs2.append(float(depths.max()))
    print(f"    {w:10s} n_valid={int(mask.sum()):6d}  {depths.min():.10g} .. {depths.max():.10g}")
full_min, full_max = min(mins2), max(maxs2)
print(f"\nTOTAL full-valid rows across 8 wells: {total}  (DK task1b expect 72064)")
print(f"POOLED FULL-VALID RANGE: min={full_min:.10g} m  max={full_max:.10g} m")
print(f"  claim on record: 760.9 m to 3897.3 m -> {'MATCHES' if round(full_min,1)==760.9 and round(full_max,1)==3897.3 else 'MISMATCH'}")

print("\n" + "=" * 100)
print("WHICH RANGE FOR 'the span of the 8 test wells'")
print("=" * 100)
print("""The full-valid range (760.9-3897.3 m) is the wells' actual data span (every sample where
all four modeled curves are present). The scored range (1295.6-3897.3 m) is narrower solely
because generation always starts after PRIME_FRAC=0.25 of each well is consumed as context
(scripts/atce/atce_ablation.py: prime_n = max(CONTEXT, int(n*PRIME_FRAC))) -- it is an artifact
of the generation protocol, not a property of the wells themselves. A document describing "the
span of the 8 test wells" should cite the FULL-VALID range, 760.9 m to 3897.3 m.""")
