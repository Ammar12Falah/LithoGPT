# DQ Gate 10 — section-level detail

Source: `/Users/ammar/.codex/attachments/ea7dcacd-3e84-4bc0-81b0-48a94dafe5b9/pasted-text.txt`
("Depth Conditioning Does Not Correct Porosity Bias..., Results-independent sections, revision
2, drafted 29 July 2026 for SPE ATCE 2026"). See `reports/DQ_GATE_10.md` for the search that
found it.

## Word counts (target -> actual)

- Introduction: 700 -> 748
- Related Work: 450 -> 475
- Protocol: 700 -> 645
- Experimental Family: 850 -> 1,654 (see note below)
- **Document total: 6,515 words** (target 6,500, hard ceiling 6,800 — 15 words over target,
  well under ceiling; one trim applied to Protocol per the cut order in 3.6 before accepting
  the remainder rather than risk losing content by cutting further).

Experimental Family ran to roughly double its individual target because it absorbed five
subsections from the source draft (Data, Tokenization, Backbone, Conditioning arms, Training
and generation) plus the estimator revision disclosure this brief requires to sit there (G10d).
Not cut, because the document-level total (which is what 3.6 actually gates) is under both the
target and the ceiling; cutting a technically load-bearing methods section to hit a
sub-target that isn't itself a hard rule would have traded real content for a number.

## Edits made to the source draft

1. **Banned language removed.** "pre-specified" (used throughout the source) -> "fixed in
   advance" / "written down before any result was seen"; the one sentence contrasting
   "pre-specified" against "pre-registered" was rewritten to avoid both banned terms; "robust to
   the direction of the leakage" (a near-paraphrase of the banned "robust to the leakage
   direction") was not carried into the built sections at all (it lived in the source draft's
   own Limitations, which was not used — DQ's already-built Limitations, from G4, stands
   unchanged). No em dash / en dash characters in the final rendered `manuscript.md` (checked
   programmatically, see `reports/DQ_GATE_11.md`); two were introduced by this gate's own
   editing (one in a source-note comment, one in a numeric range) and fixed before the final
   build.
2. **"One training seed per arm" corrected.** The source draft frames the single-fit limitation
   as a seed issue ("one training seed per arm", "a single seed") in at least four places. This
   is exactly the error Plan's error-list item 19 (`LITHOGPT2_PLAN_HANDOFF_v2.0.md`, written
   during G7 before this draft was found) describes: no `torch.manual_seed` call exists in the
   training code, so nothing was actually controlled by a seed at weight initialisation. Every
   instance was reworded to "one realized fit per arm" / "weight initialisation is not
   explicitly seeded", matching the required form already in DQ section 4.
3. **Unresolved citations removed.** The source draft cites 15 works. Only 2 are in
   `audit/references_check.txt` (Koeshidayatullah, Al-Fakih and Kaka 2024; Bormann, Aursand,
   Dilib, Dischington and Manral 2020 for the FORCE 2020 dataset) — both kept, by name. The
   other 13 were removed as formal citations and, where the point they supported still stood on
   its own, restated without a name/year attribution:
   Al-Fakih et al. 2025 (GAN synthesis/imputation pair), Antariksa et al. 2023 (sequence
   imputation), Athy 1930 (compaction physics — restated as "classical," unattributed),
   Deutsch and Journel 1998 (sequential Gaussian simulation), Gama et al. 2025 (imputation
   benchmark), Hallam et al. 2022 (chained-equations imputation), Qi et al. 2025 (WLFM
   foundation model — restated generically as "at least one foundation-scale study"), Radford
   et al. 2019 (GPT-2, language-model pretraining precedent — restated generically), Sclater
   and Christie 1980 (North Sea compaction quantification — restated as "the regional
   literature"), Strebelle 2002 (multiple-point statistics), Tancik et al. 2020 (Fourier
   features — restated generically as motivating the twelve-feature arm), van den Oord et al.
   2017 (VQ-VAE, tokenization precedent — restated generically), Yoon et al. 2019 (TimeGAN).
   None of these 13 are asserted as specific findings attributed to a named, unverified source
   anywhere in the built sections; every remaining unattributed sentence states only what is
   either common knowledge in the field or directly evidenced by this study's own data.
4. **One drafting error in the source caught and fixed**: the Arm B2 paragraph's Athy-fit
   sentence said the parameters were "estimated on all 98 wells" without stating which 98 (the
   source draft's own Data section defines the 98-well figure as the training-eligible
   partition before the 80/10/8 split); corrected to name the partition explicitly rather than
   propagate an under-specified number.
5. **Title**: the source draft's own working title ("...Does Not Correct Porosity Bias...: A
   Pre-Specified Ablation") was NOT used; the manuscript's H1 is the ruled title from DQ section
   4 ("...Did Not Correct Mean Porosity Bias...: A Single-Basin Ablation"), unchanged since G4.

## What was NOT touched

Abstract, Results, Discussion, Conclusions, Limitations, the corrections-to-v1 paragraph, and
Code Availability are unchanged from the G4 build (DQ) — the source draft's own versions of
Limitations, Code/Data Availability, Acknowledgements, and References were read for cross-
checking only and are not used; DQ's versions of the overlapping sections already pass every
G6 check and are not duplicated.
