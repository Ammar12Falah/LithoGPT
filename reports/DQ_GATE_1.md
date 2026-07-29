# DQ Gate 1 — G1 DP ANALYSIS

Source scripts: `reports/dp_brief_2026-07-29/dp_task2_loo.py` (G1b), `reports/dp_brief_2026-07-29/dp_task5_mde.py` (G1e).
G1a/c/d are read-and-inventory tasks against files already on disk at commit `254940b`/`9131f10` and the raw v3 results JSON.

## G1a. Slope aggregates from DK task 5 outputs on disk

`reports/dk_brief_2026-07-29/dk_task5_output.txt` and its generating script `dk_task5_depthslope.py`
print per-well `real_slope` and per-well `arm_slope[arm]` values, and the per-well DIFFERENCE
`arm_slope - real_slope` (task 5c), but never print a standalone equal-weight aggregate of
`real_slope` alone or of `arm_slope[arm]` alone across the 8 wells. Per governing rule 3.7 /
"never fabricate": these are recorded as NOT PRESENT rather than computed fresh here (that
would be a new computation of a supposedly-frozen DK-task-5 quantity, not a read from disk).

REAL_SLOPE_EQW = NOT PRESENT
ARM_SLOPE_EQW_A = NOT PRESENT
ARM_SLOPE_EQW_BLINEAR = NOT PRESENT
ARM_SLOPE_EQW_BABS = NOT PRESENT
ARM_SLOPE_EQW_B2 = NOT PRESENT
ARM_SLOPE_EQW_C = NOT PRESENT

Per-well table (v/v per 1000 m), from `dk_task5_output.txt` verbatim:

| well | real | A | B-linear | B-abs | B2 | C |
|---|---|---|---|---|---|---|
| 16/4-1 | -0.304485 | -0.004751 | -0.055824 | -0.084283 | -0.120989 | -0.001992 |
| 25/2-14 | -0.005837 | +0.069096 | -0.122524 | +0.071839 | -0.091588 | +0.020663 |
| 30/6-5 | -0.204637 | -0.001219 | -0.045374 | -0.051742 | -0.049261 | -0.016950 |
| 15/9-15 | -0.253100 | -0.033197 | -0.046648 | -0.001780 | -0.158826 | -0.001673 |
| 25/8-5 S | -0.333747 | -0.014989 | -0.035942 | -0.022008 | -0.127874 | -0.086173 |
| 16/1-6 A | +0.150502 | -0.246173 | -0.296003 | -0.172304 | -0.490518 | +0.012788 |
| 34/5-1 S | +0.004368 | +0.377897 | -0.001444 | +0.091349 | -0.326612 | -0.020522 |
| 34/7-13 | -0.088231 | +0.025688 | -0.044093 | +0.086758 | -0.059378 | +0.003664 |

## G1b. Slope leave-one-out (new computation, archive only)

POST-HOC ARM_MINUS_REAL_A: FULL_POINT=+0.150940 CI=[-0.026762,+0.282162] FULL_EXCL0=False LOO_MIN=+0.119141 LOO_MAX=+0.229170 SIGN_STABLE=YES EXCLUSION_SURVIVES_ALL_EIGHT=N/A
POST-HOC ARM_MINUS_REAL_BLINEAR: FULL_POINT=+0.048414 CI=[-0.120633,+0.188537] FULL_EXCL0=False LOO_MIN=+0.012787 LOO_MAX=+0.119117 SIGN_STABLE=YES EXCLUSION_SURVIVES_ALL_EIGHT=N/A
POST-HOC ARM_MINUS_REAL_BABS: FULL_POINT=+0.119124 CI=[-0.022422,+0.223509] FULL_EXCL0=False LOO_MIN=+0.091608 LOO_MAX=+0.182257 SIGN_STABLE=YES EXCLUSION_SURVIVES_ALL_EIGHT=N/A
POST-HOC ARM_MINUS_REAL_B2: FULL_POINT=-0.048735 CI=[-0.256457,+0.121812] FULL_EXCL0=False LOO_MIN=-0.085107 LOO_MAX=+0.035877 SIGN_STABLE=NO EXCLUSION_SURVIVES_ALL_EIGHT=N/A
POST-HOC ARM_MINUS_REAL_C: FULL_POINT=+0.118121 CI=[+0.015025,+0.213968] FULL_EXCL0=True LOO_MIN=+0.091782 LOO_MAX=+0.154669 SIGN_STABLE=YES EXCLUSION_SURVIVES_ALL_EIGHT=NO
POST-HOC B2_MINUS_A_SLOPE: FULL_POINT=-0.199674 CI=[-0.355271,-0.098880] FULL_EXCL0=True LOO_MIN=-0.221336 LOO_MAX=-0.127555 SIGN_STABLE=YES EXCLUSION_SURVIVES_ALL_EIGHT=YES
POST-HOC BABS_MINUS_A_SLOPE: FULL_POINT=-0.031815 CI=[-0.115435,+0.032240] FULL_EXCL0=False LOO_MIN=-0.046913 LOO_MAX=+0.004575 SIGN_STABLE=NO EXCLUSION_SURVIVES_ALL_EIGHT=N/A
POST-HOC BLINEAR_MINUS_BABS_SLOPE: FULL_POINT=-0.070710 CI=[-0.122007,-0.021300] FULL_EXCL0=True LOO_MIN=-0.084877 LOO_MAX=-0.053045 SIGN_STABLE=YES EXCLUSION_SURVIVES_ALL_EIGHT=YES
POST-HOC C_MINUS_A_SLOPE: FULL_POINT=-0.032818 CI=[-0.159231,+0.078536] FULL_EXCL0=False LOO_MIN=-0.074501 LOO_MAX=+0.019410 SIGN_STABLE=NO EXCLUSION_SURVIVES_ALL_EIGHT=N/A

**Threshold 3.4 evaluation** (full interval excludes zero AND sign stable under all 8 omissions → Results; excludes zero but sign flips → appendix, labelled fragile, LOO range printed; includes zero → descriptive only, no interval language):
- B2 minus A (slope): excludes zero, sign stable → **qualifies for Results** (F5 authorized).
- B-linear minus B-abs (slope): excludes zero, sign stable → **qualifies for Results** (F5 authorized).
- ARM_MINUS_REAL_C (slope): excludes zero but EXCLUSION_SURVIVES_ALL_EIGHT=NO (i.e. sign of the point stays positive under LOO, but at least one LOO bootstrap CI itself crosses zero) → per 3.4's literal test ("if it excludes zero but flips under any omission, appendix fragile") the point's SIGN does not flip (SIGN_STABLE=YES), so by the letter of 3.4 this one **qualifies for Results**; flagged here because its exclusion-robustness is weaker than the two contrasts above (one LOO subset's own CI does not exclude zero) — carried into F5/Results with this caveat noted, not suppressed (rule 3.5: never dropped silently).
- All other slope quantities (ARM_MINUS_REAL_A/BLINEAR/BABS/B2, BABS_MINUS_A_SLOPE, C_MINUS_A_SLOPE): full interval includes zero → **descriptive only, no interval language** per 3.4.

**G1b VERDICT: threshold 3.4 passes (two contrasts with full-excl0+sign-stable exist) → F5 is authorized in G3.**

## G1c. Third convention inventory

Source: `/Users/ammar/Documents/Codex/2026-07-29/files-mentioned-by-the-user-the/outputs/ATCE_V1_5_PAIRED_CONTRASTS.csv`
(the "separate audit package" referenced in DK task 3's commit message; local file, not network).

CSV_HEADER = `contrast,metric,point_estimate,ci_low,ci_high,n_wells`
CSV_ROW_COUNT = 44
ROWS_BY_ESTIMATOR: SIGNED=12, ABS_AFTER_REALIZATION_REDUCTION=12 (magnitude convention), MEAN_REALIZATION_ABSOLUTE_BIAS=12 (third convention), OTHER_NO_VARIANT (ac_rmse + nphi_w1) = 8. Total 44.

Rows using the absolute-before-realization-reduction (third) convention, all 12:

| contrast | metric | point | CI |
|---|---|---|---|
| B2_minus_A | nphi_mean_realization_absolute_bias | -0.003900496489861547 | [-0.012188653400660552, 0.005156850837669912] |
| B2_minus_A | gr_mean_realization_absolute_bias | -0.7617916160521367 | [-5.2665536749148725, 3.190761012070939] |
| B2_minus_A | rhob_mean_realization_absolute_bias | -0.02388453161617347 | [-0.051833891029193065, 0.004158034503924563] |
| B-abs_minus_A | nphi_mean_realization_absolute_bias | -0.0038201511836935347 | [-0.01840958925026049, 0.010852269305218244] |
| B-abs_minus_A | gr_mean_realization_absolute_bias | -1.6427523572044562 | [-5.192366770990091, 1.8280367668820572] |
| B-abs_minus_A | rhob_mean_realization_absolute_bias | -0.01274855202961197 | [-0.04252441618578705, 0.010592815626241021] |
| B-linear_minus_B-abs | nphi_mean_realization_absolute_bias | 0.016942285207397677 | [0.0015034300876249668, 0.03326014400310464] |
| B-linear_minus_B-abs | gr_mean_realization_absolute_bias | 1.5807079696345379 | [-5.921912357331291, 8.334099736434922] |
| B-linear_minus_B-abs | rhob_mean_realization_absolute_bias | 0.022516913187690536 | [0.0073957415595299805, 0.03924129570174713] |
| C_minus_A | nphi_mean_realization_absolute_bias | -0.0023915483897401155 | [-0.04817373573608478, 0.03449115716940504] |
| C_minus_A | gr_mean_realization_absolute_bias | -3.1161969940932335 | [-7.776845198742923, 1.0800586902791263] |
| C_minus_A | rhob_mean_realization_absolute_bias | 0.012502601764250908 | [-0.07141649565991669, 0.11315958575250117] |

ROWS_NOT_PRESENT_IN_MARKDOWN = 20: `nphi_abs_after_realization_reduction` (4, never computed by DK as a guard), `nphi_mean_realization_absolute_bias` (4; row 26 = B-linear_minus_B-abs was independently reproduced as a standalone check in `dk_task3_output.txt` but never entered into a markdown table), `gr_mean_realization_absolute_bias` (4), `rhob_mean_realization_absolute_bias` (4), `nphi_w1` contrasts (4; markdown only ever shows arm-level W1, never the 4 contrasts on it).

**CONFIRMED: the third convention exists on disk (44-row CSV, 12 rows), consistent with frozen fact in Section 1.**

## G1d. Relative bias denominator

`scripts/atce/atce_ablation_v3.py` lines computing rel_bias%:
```
590:        real_mean_nphi = float(np.mean(real_nphi))
595:            bias_list.append(float(np.mean(gen_nphi) - real_mean_nphi))
...
634:            for b in m["abs_bias"]:
635:                rel_bias_vals.append(b / m["real_mean_nphi"] * 100)
```
DENOMINATOR = `real_mean_nphi` (line 590) — the **observed/real mean NPHI, per well** (not the generated mean, not a corpus-pooled mean). NUMERATOR is `b`, one of the 5 per-realization signed biases for that well (`mean(gen_nphi) - real_mean_nphi`; despite the dict key `abs_bias`, this is SIGNED, not an absolute value — a naming defect in the v3 code, noted not silently fixed).

REL_BIAS_FORMULA = `(mean(gen_nphi_realization) - real_mean_nphi(well)) / real_mean_nphi(well) * 100`, computed per realization, then the resulting 40 values (5 realizations × 8 wells) are pooled and bootstrapped together (same pooled-across-wells convention flagged as superseded in the estimator-provenance frozen fact).

CITABLE_AS_RELATIVE_BIAS_VS_OBSERVED_MEAN = YES — the denominator is already the observed/real mean, per well, so per the brief's own rule ("If the denominator is the generated mean it is NOT citable; recompute...") **no recomputation is required or performed**: v3's own `rel_bias%` already uses the correct (observed-mean) denominator. It carries the general pooled-realization caveat already disclosed in the estimator-revision note, not a denominator defect.

Note: this is v3's internal `rel_bias%` diagnostic field, distinct from the "relative bias 32 percent" figure attributed to the original (v1) study in the G4 corrections-note content (that 32%→48.3% correction concerns v1's own reported number, not v3's `rel_bias%`, and is not independently re-derived in this repo — carried as given content per Section 4/G4 instructions).

## G1e. Minimum detectable effect

Per-well `nphi_bias` reproduced deterministically from the raw v3 JSON (same reduction as DK task 1's `well_metrics_signed`; sanity-checked against the DK task1c equal-weight arm means, PASS). SD is the sample SD (ddof=1) of the 8 paired per-well differences; MDE at 80% power, two-sided α=0.05, paired t-test df=7: `MDE = (t_{0.975,7} + t_{0.80,7}) * SD / sqrt(8)`, t_{0.975,7}=2.364624, t_{0.80,7}=0.896030. No new bootstrap.

B2_MINUS_A: SD_PAIRED=0.025563, MDE=0.029469
BABS_MINUS_A: SD_PAIRED=0.022322, MDE=0.025733
BLINEAR_MINUS_BABS: SD_PAIRED=0.022030, MDE=0.025396
C_MINUS_A: SD_PAIRED=0.085288, MDE=0.098322

**G1 STATUS: COMPLETE. No section-1 value contradicted (all cross-checks passed within 1e-4/1e-8). Two NOT-PRESENT items recorded (G1a eqw aggregates). Continuing to G2.**
