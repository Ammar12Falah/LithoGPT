#!/usr/bin/env python3
"""DP Task 5: minimum detectable effect for the four pre-specified signed-NPHI-bias
contrasts. Per-well nphi_bias reproduced EXACTLY via DK task1's own
well_metrics_signed reduction (mean over 5 realizations, per well, per arm) from the
raw v3 JSON already on disk -- deterministic, not a new bootstrap. SD of the 8 paired
per-well differences (sample SD, ddof=1), then MDE at 80% power, two-sided alpha=0.05,
paired t-test df=7: MDE = (t_{0.975,7} + t_{0.80,7}) * SD / sqrt(8)."""
import json
import numpy as np
from scipy.stats import t as tdist

RAW_PATH = "/Users/ammar/LithoGPT_archive/atce_ablation_v3_raw_results_2026-07-26.json"
NPHI_IDX = 2

with open(RAW_PATH) as f:
    raw = json.load(f)
WELLS = list(raw["A"].keys())


def well_nphi_bias(arm, well):
    d = raw[arm][well]
    real_nphi = np.array(d["real"], dtype=np.float64)[:, NPHI_IDX]
    gens = np.array(d["generated_realizations"], dtype=np.float64)
    return float(np.mean([g[:, NPHI_IDX].mean() - real_nphi.mean() for g in gens]))


nphi_bias = {arm: {w: well_nphi_bias(arm, w) for w in WELLS} for arm in ["A", "B-linear", "B-abs", "B2", "C"]}

# sanity check vs DK task1 arm-level equal-weight means (1c)
targets_1c = {"A": -0.04234970379, "B-linear": -0.0665919643, "B-abs": -0.03398159302,
              "B2": -0.04475730224, "C": 0.03318312565}
for arm, tgt in targets_1c.items():
    v = np.mean(list(nphi_bias[arm].values()))
    assert abs(v - tgt) < 1e-8, (arm, v, tgt)
print("Sanity check vs DK task1c equal-weight arm means: PASS\n")

CONTRASTS = [("A", "B2", "B2 minus A"), ("A", "B-abs", "B-abs minus A"),
             ("B-abs", "B-linear", "B-linear minus B-abs"), ("A", "C", "C minus A")]

n = 8
df = n - 1
t_crit = tdist.ppf(0.975, df)
t_power = tdist.ppf(0.80, df)
print(f"t_crit(0.975,df={df})={t_crit:.6f}  t_power(0.80,df={df})={t_power:.6f}\n")

for base, other, label in CONTRASTS:
    diffs = np.array([nphi_bias[other][w] - nphi_bias[base][w] for w in WELLS])
    sd = float(np.std(diffs, ddof=1))
    mde = (t_crit + t_power) * sd / np.sqrt(n)
    print(f"POST-HOC  {label:24s} SD_PAIRED={sd:.6f}  MDE={mde:.6f}")

print("\nDP_TASK5_MDE_COMPLETE")
