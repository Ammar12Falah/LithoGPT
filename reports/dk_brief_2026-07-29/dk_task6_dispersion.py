#!/usr/bin/env python3
"""DK Task 6: dispersion / std understatement, pooled and equal-weight."""
import json
import numpy as np

RAW_PATH = "/Users/ammar/LithoGPT_archive/atce_ablation_v3_raw_results_2026-07-26.json"
NPHI_IDX = 2
with open(RAW_PATH) as f:
    raw = json.load(f)
WELLS = list(raw["A"].keys())
ARMS = ["A", "B-linear", "B-abs", "B2", "C"]

real_pooled = np.concatenate([np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX] for w in WELLS])
real_pooled_std = float(real_pooled.std())
print(f"REAL pooled std = {real_pooled_std:.6f}  (expect ~0.161)")

print("\nPOOLED per arm:")
arm_pooled_std = {}
for arm in ARMS:
    gen_pooled = np.concatenate([np.array(raw[arm][w]["generated_realizations"], dtype=np.float64)[:, :, NPHI_IDX].ravel() for w in WELLS])
    s = float(gen_pooled.std())
    arm_pooled_std[arm] = s
    understate = (1 - s / real_pooled_std) * 100
    print(f"  {arm:10s} std={s:.6f}  understatement={understate:.2f}%")

print("\nEQUAL-WEIGHT PER WELL (per-well std, then average across 8 wells):")
real_perwell_std = {w: float(np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX].std()) for w in WELLS}
real_eqw_std = float(np.mean(list(real_perwell_std.values())))
print(f"  REAL equal-weight mean per-well std = {real_eqw_std:.6f}")
for arm in ARMS:
    perwell = {w: float(np.array(raw[arm][w]["generated_realizations"], dtype=np.float64)[:, :, NPHI_IDX].ravel().std()) for w in WELLS}
    eqw = float(np.mean(list(perwell.values())))
    understate = (1 - eqw / real_eqw_std) * 100
    print(f"  {arm:10s} eqw_std={eqw:.6f}  understatement={understate:.2f}%")

print("\nPER-WELL C GENERATED STD (investigating the pooled-vs-eqw divergence for C):")
for w in WELLS:
    gen = np.array(raw["C"][w]["generated_realizations"], dtype=np.float64)[:, :, NPHI_IDX]
    std_per_well = gen.ravel().std()
    real_std = np.array(raw["A"][w]["real"], dtype=np.float64)[:, NPHI_IDX].std()
    print(f"  {w:12s} C_gen_std={std_per_well:.6f}  real_std={real_std:.6f}")

print("\nRANGE OF UNDERSTATEMENT ACROSS ARMS:")
pooled_vals = [(1 - arm_pooled_std[a] / real_pooled_std) * 100 for a in ARMS]
print(f"  pooled basis: {min(pooled_vals):.1f}% to {max(pooled_vals):.1f}%")
print(f"  v1.9 claimed bracket 40-50%: correct on pooled basis = "
      f"{40 <= min(pooled_vals) and max(pooled_vals) <= 50}")

print("\nTASK6_DISPERSION_COMPLETE")
