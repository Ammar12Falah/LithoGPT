This document supersedes v1.9 (not found on disk when v2.0 was first written; still not found
after the exhaustive G10 search — see section 2 below for what WAS found and used). Written
fresh from the DQ/DR briefs' frozen facts and this session's gate outputs.

````
LITHOGPT2_PLAN_HANDOFF_v2.0 (rewritten at the close of brief DR)
Supersedes: v1.9 (not found on disk)
Session: briefs DQ + DR, autonomous, local Mac only, $0 spend except one authorized
matplotlib venv install (G8), no pod, no GPU
Repo: /Users/ammar/LithoGPT_archive/LithoGPT-2, branch local-audit-env-pins-2026-07-29
Next brief letter: DS

================================================================================
1. RULED TITLE (use verbatim, this is the manuscript H1 -- unchanged)
================================================================================
Depth Conditioning Did Not Correct Mean Porosity Bias in Discrete Autoregressive
Well-Log Generation: A Single-Basin Ablation

================================================================================
2. THE EARLIER DRAFT: FOUND (this is new since v2.0's first write-up)
================================================================================
Brief DR's G10 ran an exhaustive search (all branches incl. remote-tracking, stashes,
dangling commits, the original LithoGPT repo if present, and the whole home directory
for .md/.tex/.docx/.odt/.pdf/.txt modified since 2026-06-01 mentioning the ablation).
FOUND: /Users/ammar/.codex/attachments/ea7dcacd-3e84-4bc0-81b0-48a94dafe5b9/pasted-text.txt
("Depth Conditioning Does Not Correct Porosity Bias..., Results-independent sections,
revision 2", dated 2026-07-29 13:35, from a parallel tool session under ~/.codex/, NOT
this repo). Contains full Introduction, Related Work, Data, Method, and Experimental
Protocol sections. Every checkable number in it matches FROZEN_RESULTS.json / the DQ
frozen facts exactly (spot-checked extensively, see reports/DQ_GATE_10.md) -- treated as
genuine, contemporaneous project output.
USED, with three corrections applied before use:
  (a) it uses "pre-specified" and "pre-registered" throughout (both banned) -- reworded
      to "fixed in advance" everywhere.
  (b) it frames the single-fit-per-arm limitation as "one training seed per arm" / "a
      single seed" -- THIS IS THE DRAFT error-list item 19 (below) was written to
      correct. No torch.manual_seed call exists anywhere in the training code (DK task
      4), so nothing was controlled by a seed at weight initialisation. Reworded to
      "one realized fit per arm" throughout, matching the DQ section 4 required form.
  (c) it cites 15 references; only 2 are in audit/references_check.txt (Koeshidayatullah/
      Al-Fakih/Kaka 2024, and Bormann et al. 2020 for FORCE 2020). The other 13 were
      removed as formal citations (no network gate was open in G10 to resolve more) and,
      where the underlying point still stood, restated without a name/year attribution.
      Full removed-citation list in reports/DQ_GATE_10_sections.md.
The manuscript's Abstract, Results, Discussion, Conclusions, Limitations, corrections
note, and Code Availability (written fresh at rev4, brief DQ, before this draft was
found) are UNCHANGED -- the found draft's own versions of the overlapping sections
(its Limitations, Code/Data Availability, Acknowledgements, References) were read for
cross-checking only and are not used, to avoid duplicating already-audited content.

================================================================================
3. FROZEN FACTS (unchanged from v1.9's supersession write-up -- do not re-derive)
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
Slope leave-one-out (brief DQ G1b): B2 minus A and B-linear minus B-abs both exclude
  zero with sign stable under all 8 well omissions -- this is what authorizes F5 as a
  main figure rather than an appendix-fragile one (3.4).
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
  supports scikit-learn 1.9.0. Reconstruction bias +0.000487 eqw (+0.001048 pooled,
  per the found draft, not independently re-verified this session).
Athy frozen fit: phi0 0.6052, lambda 4068.0 m. Train-only 0.5776 / 4375.8 m,
  shift +307.8 m, max feature shift 0.0267 in feature units.
Arm D is WITHDRAWN: it subtracts the Athy trend from targets and never adds it back
  before scoring. Appendix only (Limitations item, mentioned once). Never supporting
  evidence. Never in any table or figure.
References resolved (audit/references_check.txt): arXiv 2412.05681 =
  Koeshidayatullah/Al-Fakih/Kaka (confirmed); FORCE 2020 = dual licence, curves NLOD
  2.0 / lithofacies CC-BY-4.0, DOI 10.5281/zenodo.4351156 (confirmed from the primary
  Zenodo record); this study uses no lithofacies data. 13 further citations in the
  found draft remain UNRESOLVED and are not in the manuscript (see section 2c).

================================================================================
4. LANGUAGE RULES (section 4 of brief DQ, unchanged, verified 0 hits on full manuscript)
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
5. WHAT IS DONE (briefs DQ + DR, commits on local-audit-env-pins-2026-07-29)
================================================================================
G1 DP ANALYSIS: complete.
G2 TRACEABILITY: complete. analysis/FROZEN_RESULTS.json, 372 keys, full precision,
  each with provenance. analysis/fill.py template substitution.
G3 TABLES: complete. T1/T2/T3, CSV+LaTeX, both guard tables in full.
G4 MANUSCRIPT core sections: complete (Abstract, Results, Discussion, Conclusions,
  Limitations, corrections note, Code Availability).
G5 REFERENCES: complete. 2 of 2 "Known" references resolved.
G6 AUDIT: complete at the DQ close (0 mismatches on the then-current manuscript).
G7 HANDOFF v1 + summary: complete (this document supersedes that version).
G8 PLOTTING VENV: complete. ~/lithogpt_plot, matplotlib 3.9.4 + closure (pins in
  audit/lithogpt_plot_venv_pins.txt). Working environment confirmed byte-identical
  before/after (audit/env_before.txt == audit/env_after.txt).
G9 FIGURES RENDERED: complete. figs/F1-F5, vector PDF + 300dpi PNG, from saved data
  only (no recomputation). F5 rendered as a MAIN figure (not appendix-fragile): two
  slope contrasts (B2 minus A, B-linear minus B-abs) satisfy 3.4's exclude-zero +
  sign-stable test; caption states which series carry inferential weight. Arm D in no
  figure.
G10 EARLIER DRAFT: FOUND and used. See section 2 above. Introduction (748w),
  Related Work (475w), Protocol (645w), Experimental Family (1,654w) added to the
  manuscript.
G11 REAUDIT: complete, 0 mismatches. audit/verify_all.py extended with a citation-
  resolution check (new since the found draft added the manuscript's first real
  citations). Word count 6,515 (target 6,500, ceiling 6,800 -- 15 over target, one
  Protocol trim applied, remainder accepted rather than risk cutting load-bearing
  disclosures for a 15-word margin). Arm D exactly once. No superseded run-log
  interval cited.

================================================================================
6. WHAT REMAINS
================================================================================
(a) The manuscript is now essentially complete in structure (Introduction through Code
    Availability, all sections present, all figures rendered, all tables built). What
    remains is human/editorial: Ammar or Plan reading it end to end for scientific
    judgment calls no gate can make (e.g. does the Discussion's framing match what he
    wants to claim, is the Related Work's citation coverage acceptable at only 2 of 15
    original sources, does the SPE ATCE audience need more than this).
(b) Resolve the 13 citations dropped in G10 for lack of network access there, if the
    author wants Related Work restored to its original citation density -- would need
    a G5-style network-permitted pass.
(c) Decide whether/how to commit the BC-BW local-Mac-only analysis referenced in
    earlier session memory (still unrelated to this gate run, still open).
(d) Results-freeze date (5 Aug 2026 per earlier project record) -- re-check against
    how much of (a)/(b) still needs doing.
(e) The found draft (section 2) lives outside this repo, in another tool's local
    attachment store (~/.codex/); it is not committed anywhere and could be lost if
    that store is cleared. Worth Ammar copying it into the repo or archive if he wants
    it preserved as a citable source document.

================================================================================
7. PLAN'S ERROR LIST -- ITEMS 17-19 (items 1-16 not located; item 19 now resolved)
================================================================================
17. The third estimator convention (absolute value before the realization reduction)
    EXISTS on disk (44-row CSV, 12 rows under this convention, independently
    reproduced to 1e-9 for row 26) and was WRONGLY DENIED in an earlier pass -- correct
    this wherever the earlier denial was recorded.
18. Under-dispersion is 35.9 to 51.3 percent (pooled), NOT 40 to 50 percent as an
    earlier draft claimed.
19. RESOLVED this brief: the "earlier draft" this item warned about is now identified
    -- the found draft at ~/.codex/attachments/.../pasted-text.txt used "one training
    seed per arm" throughout. Corrected to "one realized fit per arm" everywhere it
    was used in the manuscript (see section 2b). No torch.manual_seed call exists in
    the training code; nothing was controlled by a seed at weight initialisation.

================================================================================
8. NEXT BRIEF LETTER: DS
================================================================================
````
