This document supersedes v2.0. The manuscript and its supporting analysis are now published
(as a non-default branch, not merged to main) at the ORIGINAL repository,
github.com/Ammar12Falah/LithoGPT — a different destination from the audit work's home repo,
github.com/Ammar12Falah/LithoGPT-2 (still the source of truth for the branch this was built on,
`local-audit-env-pins-2026-07-29`).

````
LITHOGPT2_PLAN_HANDOFF_v2.1 (rewritten at the close of brief DV)
Supersedes: v2.0
Session: briefs DQ through DV, autonomous except the DV push (explicit live consent
required and given), local Mac + one HTTPS push, $0 spend except one authorized
matplotlib venv install (G8), no pod, no GPU
Source repo/branch: /Users/ammar/LithoGPT_archive/LithoGPT-2,
  branch local-audit-env-pins-2026-07-29 (unmodified by the publication branch work)
PUBLISHED repo/branch: github.com/Ammar12Falah/LithoGPT,
  branch atce-v1-5-audit-2026-07-29 (NOT main, NOT merged)
Final pushed commit: 2e033eca1ce61dba42069415497c4f8c9243fedf
  (verified via git fetch + git rev-parse against the remote, not just the local commit)
Next brief letter: DW

================================================================================
1. RULED TITLE (use verbatim, this is the manuscript H1 -- unchanged)
================================================================================
Depth Conditioning Did Not Correct Mean Porosity Bias in Discrete Autoregressive
Well-Log Generation: A Single-Basin Ablation

================================================================================
2. THE EARLIER DRAFT: FOUND AND FULLY INTEGRATED (unchanged since v2.0, references
   now also fully restored -- see section 3 below)
================================================================================
Found at brief DR's G10: /Users/ammar/.codex/attachments/ea7dcacd-3e84-4bc0-81b0-48a94dafe5b9/
pasted-text.txt ("Depth Conditioning Does Not Correct Porosity Bias..., Results-independent
sections, revision 2", dated 2026-07-29 13:35, a parallel tool session's output, NOT in this
repo). Contains Introduction, Related Work, Data, Method, and Experimental Protocol. Every
checkable number matched FROZEN_RESULTS.json / the DQ frozen facts exactly. Used, with three
corrections: banned "pre-specified"/"pre-registered" language reworded; a "one training seed
per arm" framing corrected to "one realized fit per arm" (this was Plan's error-list item 19,
now resolved -- see section 7); and, at brief DR, its 15 citations were unresolved so 13 were
described generically. **All 13 have since been resolved (brief DS/DT G14) and restored as
real citations, plus a References section added** -- see section 3.
This document still lives only under ~/.codex/ on this Mac, not committed anywhere. It is
worth Ammar copying it into the repo or archive if he wants it preserved as a citable source.

================================================================================
3. REFERENCES: 15 OF 15 RESOLVED (complete since brief DT; NEW since v2.0)
================================================================================
Every one fetched directly from a primary source (DOI resolver, CrossRef API, arXiv, NeurIPS
proceedings, GitHub, Google Books) -- never from a search snippet or memory. Full detail:
audit/references_check.txt.
  1. Al-Fakih et al. 2025 (Sci Rep, well-log GAN)          RESOLVED_MISMATCH: author order
     corrected to Al-Fakih, Koeshidayatullah, Mukerji, Al-Azani and Kaka (draft had Al-Azani
     and Kaka swapped). No sentence needed rewriting -- pre-resolution it was cited generically.
  2-15. All RESOLVED_MATCH: Antariksa et al. 2023; Athy 1930; Bormann et al. 2020 (FORCE 2020);
     Deutsch and Journel 1998 (GSLIB); Gama et al. 2025; Hallam et al. 2022; Koeshidayatullah,
     Al-Fakih and Kaka 2024; Qi et al. 2025 (WLFM); Radford et al. 2019 (GPT-2); Sclater and
     Christie 1980; Strebelle 2002; Tancik et al. 2020; van den Oord et al. 2017 (VQ-VAE); Yoon
     et al. 2019 (TimeGAN).
0 unresolved, 0 removed. All 15 are formal in-text citations in
manuscript/manuscript.md's Introduction and Related Work, plus a new References section at the
end of the manuscript.

================================================================================
4. FROZEN FACTS (unchanged from v2.0 -- do not re-derive)
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
Guards: signed convention 5 rows exclude zero; magnitude convention 1 row (B-linear
  minus B-abs RHOB).
Dispersion: real pooled std 0.160875. Understatement 35.9 to 51.3 percent pooled.
Slope contrasts: B2 minus A -0.199674 [-0.355271,-0.098880]; B-abs minus A -0.031815
  [-0.115435,+0.032240]; B-linear minus B-abs -0.070710 [-0.122007,-0.021300]; C minus
  A -0.032818 [-0.159231,+0.078536]. Leave-one-out: B2 minus A and B-linear minus
  B-abs both exclude zero, sign-stable under all 8 omissions -- F5 authorized as a
  main figure.
Third estimator convention (absolute before realization reduction) EXISTS on disk,
  row 26 = B-linear minus B-abs, point 0.016942285207397677, CI [0.0015034300876249668,
  0.03326014400310464]. Post-hoc.
Estimator provenance: original script pooled 1,000 resamples over 40 non-independent
  realization values; paired well-level 10,000-resample estimator committed
  2026-07-27 20:35:28 UTC, ~17h after the first result commit ef8883e
  (2026-07-27 03:29:42 UTC). Only atce_v3_recompute.py intervals are citable.
Seed: no torch.manual_seed exists anywhere in the training code. "One realized fit
  per arm", never "one seed per arm".
Final training losses: A 1.4262, B-linear 1.4213, B-abs 1.4331, B2 1.3520, C (MSE,
  not comparable) 0.0292. No arm plateaued.
Params: A 5,383,144; B-linear 5,383,656; B-abs 5,383,656; B2 5,386,472; C 5,127,172.
Tokenizer sealed: 1000/1000 clusters, entropy 9.800, RMSE GR 3.928 / RDEP 9.309 /
  NPHI 0.0136 / RHOB 0.0254. Archived-pin refit could not run on this Mac
  (scikit-learn 1.9.0 needs Python >=3.10, unavailable).
Athy frozen fit: phi0 0.6052, lambda 4068.0 m; train-only 4375.8 m, shift +307.8 m,
  max feature shift 0.0267.
Arm D WITHDRAWN: mentioned exactly once, in Limitations, never supporting evidence,
  never in any table or figure.
Raw generation outputs: atce_ablation_v3_raw_results_2026-07-26.json, 149,074,228
  bytes, sha256 ac963f2c56ec27ac8f2fd837faa90108dc580a53560dbeb3c50a41c35f0110ed --
  never committed to any repo (exceeds GitHub's limit), deposited to Zenodo instead
  (DOI not yet minted; manuscript states "DOI to be inserted on deposit", not invented).

================================================================================
5. LANGUAGE RULES (unchanged, verified 0 hits on the published manuscript)
================================================================================
Banned: em dash / en dash characters; "statistically significant"; "pre-specified" and
"pre-registered" anywhere; "pilot" as a name for this study; "regresses toward
corpus-mean porosity"; "discrete outputs outperform continuous"; "MSE causes
smoothing"; "the comparison isolates output representation"; "fair" applied to the
continuous baseline; "variance collapse"; "calibrated by construction"; "reserves";
"volumetric"; "proves"; "groundbreaking"; "unusable"; "clean null"; "robust to the
leakage direction"; placeholder brackets and TODO markers.
Required forms: "the paired 95 percent bootstrap interval excluded zero"; "no
detectable correction at this precision" with the MDE beside it; B-linear is a
feature-design mismatch, never a defect; "one realized fit per arm"; every contrast
row labelled "X minus Y".

================================================================================
6. WHAT IS DONE (briefs DQ through DV)
================================================================================
G1-G11 (briefs DQ/DR): analysis, traceability, tables, manuscript core sections,
  original 2 references, first audit, plotting venv, figures rendered, found draft
  integrated, reaudit -- all complete, see v2.0 for detail.
G12/G14 (briefs DS/DT): all 15 references resolved and restored, References section
  added. Complete.
G15 (brief DT): repo-publish prep -- .gitignore entry + analysis/RAW_OUTPUTS_LOCATION.md
  for the excluded raw JSON; Code Availability rewritten to name the target repo;
  secrets grep clean; RunPod-path fix applied to the 4 scripts Code Availability
  actually points to (ROOT now resolves to the clone's own root by default via
  LITHOGPT2_ROOT env-var override, was hardcoded to /workspace/LithoGPT-2). Complete.
G16-G17 (brief DV): PUSHED. Explicit live consent given in chat before any publish
  action. Sequence:
  - origin-orig remote reset from SSH back to HTTPS
    (https://github.com/Ammar12Falah/LithoGPT.git).
  - New branch atce-v1-5-audit-2026-07-29 created FROM local-audit-env-pins-2026-07-29
    (source branch untouched). .github/workflows/ci.yml removed on the NEW branch only
    (publishing token lacks workflow scope; ci.yml is intact on
    local-audit-env-pins-2026-07-29, not deleted from the project).
  - Pre-push safety: zero secrets (ghp_/github_pat_/rpa_/sk-/AKIA/private-key patterns),
    zero .env files, zero RunPod API keys (rpa_ prefix specifically checked), no file
    over 90MB, no live/actionable RunPod path or pod ID (the only pod-ID mentions found
    are historical decision-log provenance about already-terminated pods, left as-is
    per "do not delete provenance notes").
  - Pushed to origin-orig as atce-v1-5-audit-2026-07-29 (branch only, no force, no
    history rewrite, main untouched). Verified via git fetch + rev-parse against the
    remote: all 10 figure files (5 PDF + 5 PNG) present, raw JSON absent,
    .github/workflows absent.
  - Code Availability's commit-hash placeholder replaced with the VERIFIED remote
    commit b730d622faf3e9aa049131d6e8e29e5b93fca0eb, then a follow-up commit + push
    landed at 2e033eca1ce61dba42069415497c4f8c9243fedf (the final state). Zenodo DOI
    slot still literal placeholder text, not invented.
  audit/verify_all.py: ALL CHECKS PASSED at every stage of this process.

================================================================================
7. WHAT REMAINS
================================================================================
(a) Human/editorial review: Ammar or Plan reading the full manuscript end to end for
    scientific judgment calls no gate can make.
(b) The manuscript's published branch is NOT merged to main and NOT on the default
    branch -- it is reachable only via its direct URL/branch name until someone with
    write access to github.com/Ammar12Falah/LithoGPT decides to open a PR or merge.
    That decision was explicitly out of scope for brief DV ("do not merge").
(c) Zenodo deposit for the raw outputs (149,074,228 bytes) is still pending -- the DOI
    slot in Code Availability is a literal placeholder until that happens.
(d) Decide whether/how to commit the BC-BW local-Mac-only analysis referenced in
    earlier session memory (still unrelated to this work, still open).
(e) Results-freeze date (5 Aug 2026 per earlier project record) -- re-check against
    how much of (a)-(c) still needs doing.
(f) Copy the found draft (section 2) out of ~/.codex/attachments/ into the repo or
    archive if Ammar wants it preserved as a citable source document -- it is not
    committed anywhere and could be lost if that tool's local store is cleared.
(g) `.github/workflows/ci.yml` is absent from the published branch; if Ammar later
    wants CI running there too, the publishing token needs the workflow scope added
    (not done here, per the brief's explicit "do not ask Ammar to change token scopes").

================================================================================
8. PLAN'S ERROR LIST -- ITEMS 17-19 (items 1-16 not located; all of 17-19 resolved)
================================================================================
17. RESOLVED: the third estimator convention exists on disk (44-row CSV, independently
    reproduced to 1e-9 for row 26) and was wrongly denied in an earlier pass.
18. RESOLVED: under-dispersion is 35.9 to 51.3 percent (pooled), not 40 to 50 percent.
19. RESOLVED: the "earlier draft" (section 2) used "one training seed per arm"
    throughout; corrected to "one realized fit per arm" everywhere restored into the
    manuscript. No torch.manual_seed call exists in the training code.

================================================================================
9. NEXT BRIEF LETTER: DW
================================================================================
````
