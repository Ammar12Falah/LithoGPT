This document supersedes v1.9. **v1.9 itself was not found on disk anywhere on this Mac**
(searched the repo at all branches, `~/LithoGPT_archive`, `~/Documents/Codex`) — this v2.0 is
written fresh from the DQ brief's section 1 frozen facts and this session's gate outputs, not by
editing a located v1.9 file. Flagged here rather than silently claimed as an edit of a real
predecessor. Likewise, "Plan's error list" items 1-16, which item 3 below is meant to extend,
were not located on disk; items 17-19 are recorded here with the exact numbers the brief
specified, as a pointer for whoever holds the actual list to reconcile, not as a fabricated
full list.

````
LITHOGPT2_PLAN_HANDOFF_v2.0
Supersedes: v1.9 (not found on disk -- see note above)
Session: brief DQ, autonomous run, local Mac only, $0 spend, no pod, no GPU
Repo: /Users/ammar/LithoGPT_archive/LithoGPT-2, branch local-audit-env-pins-2026-07-29
Next brief letter: DR

================================================================================
1. RULED TITLE (use verbatim, this is the manuscript H1)
================================================================================
Depth Conditioning Did Not Correct Mean Porosity Bias in Discrete Autoregressive
Well-Log Generation: A Single-Basin Ablation

================================================================================
2. FROZEN FACTS (section 1 of brief DQ, carried forward verbatim -- do not re-derive)
================================================================================
Real NPHI mean, 8 test wells: 0.328089 eqw (primary), 0.337309 pooled.
Counts: scored 54,051; full valid 72,064.
Depth: scored window 1295.6256 to 3897.346 m; full valid 760.8896 to 3897.346 m.
Headline signed NPHI bias, eqw: A -0.0423, B-linear -0.0666, B-abs -0.0340,
  B2 -0.0448, C +0.0332. Arm A full precision -0.0423497038.
Four comparisons, signed NPHI bias, 10,000 resamples, default_rng(20260715), wells:
  B2 minus A            -0.0024 [-0.0188, +0.0140]   includes zero
  B-abs minus A         +0.0084 [-0.0064, +0.0223]   includes zero
  B-linear minus B-abs  -0.0326 [-0.0470, -0.0184]   excludes zero
  C minus A             +0.0755 [+0.0214, +0.1312]   excludes zero
Magnitude version of B-linear minus B-abs: +0.0178 [-0.0006, +0.0357], includes zero.
Guards: signed convention 5 rows exclude zero (B2 minus A GR, B2 minus A RHOB,
  B-abs minus A RHOB, B-linear minus B-abs GR, C minus A RHOB); magnitude convention
  1 row (B-linear minus B-abs RHOB).
Dispersion: real pooled std 0.160875. Arms 0.090579 A, 0.088272 B-linear,
  0.078311 B-abs, 0.103124 B2, 0.086985 C. Understatement 35.9 to 51.3 percent pooled.
Slope, v/v per 1000 m, arm minus real: A +0.150940 [-0.026762,+0.282162];
  B-linear +0.048414 [-0.120633,+0.188537]; B-abs +0.119124 [-0.022422,+0.223509];
  B2 -0.048735 [-0.256457,+0.121812]; C +0.118121 [+0.015025,+0.213968].
Slope contrasts: B2 minus A -0.199674 [-0.355271,-0.098880];
  B-abs minus A -0.031815 [-0.115435,+0.032240];
  B-linear minus B-abs -0.070710 [-0.122007,-0.021300];
  C minus A -0.032818 [-0.159231,+0.078536].
Third estimator convention (absolute before realization reduction), row 26 of
  ATCE_V1_5_PAIRED_CONTRASTS.csv: B-linear minus B-abs, point 0.016942285207397677,
  CI [0.0015034300876249668, 0.03326014400310464]. It exists. It is post-hoc.
Estimator provenance: the original script used 1,000 resamples pooling 40 realization
  values as independent. The paired well-level 10,000-resample estimator was first
  committed 2026-07-27 20:35:28 UTC, after the first result commit ef8883e at
  2026-07-27 03:29:42 UTC. Every interval printed inside the v3 run log is the
  superseded estimator and is NOT citable. Only atce_v3_recompute.py intervals are.
Seed: no torch.manual_seed exists. seed=20260715 governs the split and tokenizer only.
Final training losses: A 1.4262, B-linear 1.4213, B-abs 1.4331, B2 1.3520.
  C is MSE 0.0292 and not comparable. No arm plateaued. No checkpoint selection.
Params: A 5,383,144; B-linear 5,383,656; B-abs 5,383,656; B2 5,386,472; C 5,127,172.
Wall time: A 276.4s, B-linear 276.8s, B-abs 276.0s, B2 323.0s, C 313.2s, total 3757.1s.
Tokenizer sealed: 1000/1000 clusters, entropy 9.800, RMSE GR 3.928, RDEP 9.309,
  NPHI 0.0136, RHOB 0.0254. Refit in a DIFFERENT library environment gave 9.786 and
  0.0134. The refit under archived pins could not run: no interpreter on this Mac
  supports scikit-learn 1.9.0. Reconstruction bias +0.000487 eqw.
Athy frozen fit: phi0 0.6052, lambda 4068.0 m. Train-only 0.5776 / 4375.8 m,
  shift +307.8 m, max feature shift 0.0267 in feature units.
Arm D is WITHDRAWN: it subtracts the Athy trend from targets and never adds it back
  before scoring. Appendix only. Never supporting evidence. Never in any table.
References resolved this session (audit/references_check.txt): arXiv 2412.05681 =
  Koeshidayatullah/Al-Fakih/Kaka (confirmed); FORCE 2020 = dual licence, curves NLOD
  2.0 / lithofacies CC-BY-4.0, DOI 10.5281/zenodo.4351156 (confirmed from the primary
  Zenodo record); this study uses no lithofacies data.

================================================================================
3. LANGUAGE RULES (section 4 of brief DQ, unchanged, verified 0 hits this session)
================================================================================
Banned: em dash / en dash characters; "statistically significant"; "pre-specified" and
"pre-registered" anywhere; "pilot" as a name for this study (call it the ablation);
"regresses toward corpus-mean porosity"; "discrete outputs outperform continuous";
"MSE causes smoothing"; "the comparison isolates output representation"; "fair" applied
to the continuous baseline; "variance collapse"; "calibrated by construction";
"reserves"; "volumetric"; "proves"; "groundbreaking"; "unusable"; "clean null";
"robust to the leakage direction"; placeholder brackets and TODO markers.
Required forms: "the paired 95 percent bootstrap interval excluded zero"; "no
detectable correction at this precision" with the MDE beside it; an interval crossing
zero is never equivalence; B-linear is a feature-design mismatch, never a defect; "one
realized fit per arm"; every contrast row labelled "X minus Y".

================================================================================
4. WHAT IS DONE (this session, brief DQ, commit(s) on local-audit-env-pins-2026-07-29)
================================================================================
G1 DP ANALYSIS: complete. reports/DQ_GATE_1.md. Slope table, leave-one-out on 9
  quantities (2 qualify for Results per threshold 3.4: B2 minus A and B-linear minus
  B-abs slope contrasts), third-convention inventory (44-row CSV fully catalogued),
  relative-bias denominator confirmed correct (real per-well mean, already citable, no
  recompute needed), MDE for the 4 primary comparisons.
G2 TRACEABILITY: complete. analysis/FROZEN_RESULTS.json (337 keys, full precision,
  each with file+code-path provenance), analysis/fill.py (template substitution, round
  once, refuses silent missing keys).
G3 FIGURES/TABLES: PARTIAL. T1/T2/T3 tables complete (CSV+LaTeX, both guard tables
  produced in full). F1-F5 DATA complete (figs/F*_data.csv, figs/F2_*.npy) but NO
  IMAGE FILES exist -- matplotlib is not installed on this Mac and section 0 forbids
  installs. This is the single largest piece of remaining work.
G4 MANUSCRIPT: PARTIAL. manuscript/manuscript.md rev4 built via template+fill.py.
  Abstract, Results (confirmatory + descriptive subsections), Discussion (with future-
  work paragraph), Conclusions, Limitations (11 items), corrections-to-v1 paragraph,
  Code Availability: ALL DRAFTED, pass every banned-string/required-form/audit check.
  Introduction, Methods/Protocol, Related Work: NOT PRESENT -- no rev3 draft was found
  anywhere on this machine to edit/cut from, and nothing was invented in their place.
G5 REFERENCES: complete. audit/references_check.txt, both "Known" references resolved
  against primary sources (arXiv page directly; the dataset's own Zenodo deposit).
G6 AUDIT: complete, 0 mismatches. audit/verify_all.py: byte-identical template
  rebuild (proves every manuscript number traces to FROZEN_RESULTS.json, none
  hand-typed), 0 banned-string hits, word count 3,139 (well under the 6,500/6,800
  budget -- low because 3 of the planned sections are missing, not because content was
  cut), Arm D mentioned exactly once, no superseded run-log interval cited anywhere.

================================================================================
5. WHAT REMAINS
================================================================================
(a) Render figures F1-F5 as vector PDF + 300dpi PNG once matplotlib is available (or
    installs are authorized) -- all underlying numeric data is already in figs/, this
    is a pure plotting pass, not new analysis.
(b) Locate or (with Ammar's/Plan's authorization) draft Introduction, Methods/Protocol,
    and Related Work -- currently NOT PRESENT. If a real rev3 exists somewhere it was
    not found this session; worth Ammar/Plan confirming where it should live before
    the next brief drafts one from scratch.
(c) Locate the actual "Plan's error list" (items 1-16) so items 17-19 below can be
    appended to the real document instead of standing alone.
(d) Decide whether/how to commit the BC-BW local-Mac-only analysis referenced in
    earlier session memory (unrelated to this gate run, still an open decision per
    prior handoffs).
(e) Results-freeze date (5 Aug 2026 per earlier project record) should be re-checked
    against how much is still open in (a)-(c).

================================================================================
6. PLAN'S ERROR LIST -- ITEMS 17-19 (appended; items 1-16 not located this session)
================================================================================
17. The third estimator convention (absolute value before the realization reduction)
    EXISTS on disk (44-row CSV, 12 rows under this convention, independently
    reproduced to 1e-9 for row 26) and was WRONGLY DENIED in an earlier pass -- correct
    this wherever the earlier denial was recorded.
18. Under-dispersion is 35.9 to 51.3 percent (pooled), NOT 40 to 50 percent as an
    earlier draft claimed -- the 40-50 bracket does not hold on the pooled basis it was
    checked against (B2 and B-abs both fall outside it).
19. This study has ONE REALIZED FIT PER ARM, not one training seed per arm as an
    earlier draft implied -- weight initialisation is not explicitly seeded (no
    torch.manual_seed anywhere), so a re-run under the "same seed" would not reproduce
    the same weights; "one training seed per arm" overstates what was controlled.

================================================================================
7. NEXT BRIEF LETTER: DR
================================================================================
````
