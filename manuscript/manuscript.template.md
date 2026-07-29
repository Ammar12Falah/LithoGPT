# Depth Conditioning Did Not Correct Mean Porosity Bias in Discrete Autoregressive Well-Log Generation: A Single-Basin Ablation

**[BUILD NOTE, remove before submission: this document was assembled at rev4 per brief DQ. No
rev3 draft of Introduction, Methods, Protocol, or Related Work was found anywhere on this
machine (searched the repo, `~/LithoGPT_archive`, and `~/Documents/Codex`); those sections are
NOT PRESENT below rather than invented. Only Abstract, Results, Discussion, Conclusions,
Limitations, the corrections note, and Code Availability are drafted here, per the explicit G4
instruction. See `reports/DQ_GATE_4.md`.]**

## Abstract

We test whether conditioning a discrete autoregressive well-log generator on depth information
corrects a mean-porosity bias observed without it. Five model variants (no depth conditioning;
two single-channel depth embeddings differing only in reference frame; a twelve-feature
absolute-depth and Athy-decay basis; a continuous-output deterministic baseline) are trained on
{{n_train_wells}} FORCE 2020 wells and evaluated on {{n_test_wells}} held-out test wells,
{{n_realizations}} realizations per well, one realized fit per arm. On the four comparisons
fixed in advance for the primary metric (signed mean NPHI bias), depth conditioning did not
correct the bias at the minimum detectable effects computed here: neither B2 minus A nor B-abs
minus A excludes zero. Two comparisons between structurally different arms did exclude zero
(B-linear minus B-abs, read as a feature-design mismatch between depth reference frames, not a
defect; and C minus A, between the discrete and continuous formulations), but neither
characterizes either arm's own bias as small. Three unplanned descriptive findings sharpen the
picture: the flattening of the generated depth trend relative to the observed profile is
universal across every arm; the four discrete arms generate below both the held-out real mean
and their own training-corpus mean while the continuous arm generates above both; and every arm
under-disperses NPHI by an amount roughly two orders of magnitude larger than the sealed
tokenizer's own reconstruction error, ruling out quantization as the primary cause. The model is
given the true depth coordinate at every generated token and fits its training data measurably
better for having it, and still does not recover the observed profile.

## Introduction

NOT PRESENT (rev3 not found; not drafted this session; see build note above).

## Methods / Protocol

NOT PRESENT (rev3 not found; not drafted this session; see build note above).

**Estimator revision disclosure (required content, placed here as the natural methods-level
disclosure even though the surrounding Methods section is absent):** the analysis originally
used {{estimator_original_n_resamples}} resamples pooling realization values as independent.
The intervals reported below use {{estimator_recompute_n_resamples}} paired well-level
resamples. The revision postdates the first results (first result commit
{{estimator_first_result_commit_utc}} UTC; paired well-level estimator first committed
{{estimator_recompute_commit_utc}} UTC). The reason for the revision is that pooling
realizations treats non-independent samples (five realizations drawn from the same trained
model on the same well) as independent, which understates the true resampling uncertainty.
Every interval printed inside the sealed run log itself uses the original, superseded
estimator and is not citable; only the paired well-level intervals recomputed from the
archived raw outputs, reported throughout this manuscript, are used for inference.

## Related Work

NOT PRESENT (rev3 not found; not drafted this session; see build note above).

## Results

The ablation compares five model variants against the observed (real) test-well signal: Arm A
(no depth conditioning), Arm B-linear (a rank-1 linear depth embedding on per-well relative
depth), Arm B-abs (the same rank-1 mechanism on corpus-standardized absolute depth), Arm B2 (a
twelve-feature absolute-depth and Athy-decay basis with sinusoidal terms), and Arm C (a
continuous-output, deterministic baseline). All five condition on {{n_train_wells}} training
wells and are evaluated on {{n_test_wells}} held-out FORCE 2020 test wells, {{n_realizations}}
realizations per well. One realized fit per arm; weight initialisation is not explicitly seeded
(see Limitations).

### Confirmatory results: the four primary comparisons

The primary metric is signed mean NPHI bias, equal-weight across the {{n_test_wells}} test
wells. Four comparisons on this metric were fixed in advance and are reported without
re-weighting or re-metricking, each with its paired 95 percent bootstrap interval
({{estimator_recompute_n_resamples}} resamples) and its minimum detectable effect (MDE) at 80
percent power, two-sided alpha 0.05, paired t-test with 7 degrees of freedom:

- **B2 minus A**: {{contrast_signed_nphi_bias_B2_minus_A_point:+.4f}}
  [{{contrast_signed_nphi_bias_B2_minus_A_ci_low:+.4f}}, {{contrast_signed_nphi_bias_B2_minus_A_ci_high:+.4f}}].
  The interval includes zero: no detectable correction at this precision (MDE
  {{mde_B2_minus_A:.4f}}).
- **B-abs minus A**: {{contrast_signed_nphi_bias_B-abs_minus_A_point:+.4f}}
  [{{contrast_signed_nphi_bias_B-abs_minus_A_ci_low:+.4f}}, {{contrast_signed_nphi_bias_B-abs_minus_A_ci_high:+.4f}}].
  The interval includes zero: no detectable correction at this precision (MDE
  {{mde_B-abs_minus_A:.4f}}).
- **B-linear minus B-abs**: {{contrast_signed_nphi_bias_B-linear_minus_B-abs_point:+.4f}}
  [{{contrast_signed_nphi_bias_B-linear_minus_B-abs_ci_low:+.4f}}, {{contrast_signed_nphi_bias_B-linear_minus_B-abs_ci_high:+.4f}}].
  The paired 95 percent bootstrap interval excluded zero (MDE
  {{mde_B-linear_minus_B-abs:.4f}}). This is read as a feature-design mismatch between
  B-linear's per-well relative depth reference frame and B-abs's corpus-absolute frame, not as
  a defect in either mechanism: the two arms share the identical rank-1 linear form and differ
  only in which depth coordinate feeds it.
- **C minus A**: {{contrast_signed_nphi_bias_C_minus_A_point:+.4f}}
  [{{contrast_signed_nphi_bias_C_minus_A_ci_low:+.4f}}, {{contrast_signed_nphi_bias_C_minus_A_ci_high:+.4f}}].
  The paired 95 percent bootstrap interval excluded zero (MDE {{mde_C_minus_A:.4f}}). An
  interval that excludes zero here characterizes a difference in bias between two structurally
  different arms (discrete-token versus continuous-output generation); it is not evidence that
  either arm's own bias is small, and neither arm's own headline bias interval excludes zero
  against zero bias itself.

The magnitude-convention version of the B-linear minus B-abs comparison on the primary metric
(absolute value taken per well after the realization reduction, before averaging across wells)
is {{contrast_magnitude_nphi_bias_B-linear_minus_B-abs_point:+.4f}}
[{{contrast_magnitude_nphi_bias_B-linear_minus_B-abs_ci_low:+.4f}}, {{contrast_magnitude_nphi_bias_B-linear_minus_B-abs_ci_high:+.4f}}],
which includes zero: the signed-versus-magnitude disagreement on this one comparison is a
guard-table finding, addressed in the descriptive subsection below, not a second confirmatory
claim.

Headline signed NPHI bias, equal-weight, all five arms (Table T1,
`figs/T1_headline.csv`/`.tex`): A {{headline_nphi_bias_A:+.4f}}, B-linear
{{headline_nphi_bias_B-linear:+.4f}}, B-abs {{headline_nphi_bias_B-abs:+.4f}}, B2
{{headline_nphi_bias_B2:+.4f}}, C {{headline_nphi_bias_C:+.4f}}. Every arm's generated mean
NPHI sits on the same side of zero relative to the real mean except C, which overshoots in the
opposite direction (see the training-mean finding below). None of the four comparisons that
condition on depth (B2, B-abs, B-linear relative to A, and B-linear relative to B-abs) moved
the headline bias toward zero by a margin that both comparisons on Arm A cross zero for.

### Unplanned descriptive results

The following findings were not part of the four fixed comparisons above. They are reported as
descriptive, with interval language used only where 3.4/3.5 permit it, and are not treated as
confirmatory evidence.

**Guard metrics (Tables T2, T3; `figs/T2_guard_signed.csv`, `figs/T3_guard_magnitude.csv`).**
Under the signed convention, {{guard_signed_excl_count}} of 12 guard rows exclude zero (B2
minus A on GR and RHOB, B-abs minus A on RHOB, B-linear minus B-abs on GR, C minus A on RHOB).
Under the magnitude convention (absolute value taken per well after the realization reduction),
only {{guard_magnitude_excl_count}} of 12 rows exclude zero (B-linear minus B-abs on RHOB,
point {{guard_magnitude_B-linear_minus_B-abs_RHOB_point:+.4f}}
[{{guard_magnitude_B-linear_minus_B-abs_RHOB_ci_low:+.4f}}, {{guard_magnitude_B-linear_minus_B-abs_RHOB_ci_high:+.4f}}]).
The signed and magnitude conventions disagree on most rows because a signed paired difference
can exclude zero purely from a sign flip between arms rather than from a difference in
magnitude; almost none of the guard degradations implied by the signed table survive under the
magnitude convention, which is the more defensible reading of "the guard metric got worse."

**Universal flattening.** Real NPHI runs {{real_nphi_shallow:.3f}} at the shallow end of the
scored window to {{real_nphi_deep_low:.2f}} to {{real_nphi_deep_high:.2f}} at the deep end.
Every arm is materially flatter than this range, and the three levels of feature richness
tested (no depth signal in A, a single rank-1 depth channel in B-linear/B-abs, twelve features
including an explicit Athy decay term in B2) restore none of it.

**Not regression to the training mean.** The FORCE 2020 training corpus mean NPHI is
{{train_corpus_nphi_mean_eqw:.4f}} (equal-weight). The four discrete arms (A, B-linear, B-abs,
B2) generate means between {{discrete_arms_gen_mean_range_low:.4f}} and
{{discrete_arms_gen_mean_range_high:.4f}}, below both the held-out real mean
({{real_nphi_mean_eqw:.4f}}) and their own training mean. Arm C, at
{{arm_C_gen_mean:.4f}}, sits above both. The discrete and continuous formulations fail in
opposite directions, which is inconsistent with a single shared training-mean attractor
explaining both.

**Under-dispersion.** Real pooled NPHI standard deviation over the scored window is
{{dispersion_real_pooled_std:.6f}}. Every arm understates it: pooled understatement ranges from
{{dispersion_pooled_understatement_pct_B2:.1f}} to
{{dispersion_pooled_understatement_pct_B-abs:.1f}} percent (arm pooled standard deviations: A
{{dispersion_pooled_std_A:.6f}}, B-linear {{dispersion_pooled_std_B-linear:.6f}}, B-abs
{{dispersion_pooled_std_B-abs:.6f}}, B2 {{dispersion_pooled_std_B2:.6f}}, C
{{dispersion_pooled_std_C:.6f}}). The equal-weight-per-well version of this understatement
spans a much wider range and is reported in full in the supplementary dispersion table; it is
not summarized by a single bracket here because the pooled and equal-weight versions diverge
sharply for at least one arm. The ruled attribution: the sealed tokenizer reconstructs NPHI at
RMSE {{tokenizer_sealed_rmse_NPHI:.4f}} against a real pooled standard deviation of
{{dispersion_real_pooled_std:.6f}}, under one percent of the spread, so quantization alone
cannot account for the deficit. The study contains no arm that isolates quantization, because
the only continuous-output arm (C) is also the only deterministic arm and is under-dispersed by
construction, not by quantization.

**Training-loss argument (hedged).** Final single-step training batch losses: A
{{final_train_loss_A:.4f}}, B-linear {{final_train_loss_Blinear:.4f}}, B-abs
{{final_train_loss_Babs:.4f}} span {{training_loss_span_A_Blinear_Babs:.4f}}, while B2 sits
{{training_loss_B2_below_A:.4f}} below A. On this evidence alone the twelve-feature basis
measurably improved training fit while the single-channel depth encodings did not, and the arm
that used the coordinate returned no detectable correction on the primary metric. This is
hedged to a single realized fit per arm, a single training-batch loss snapshot at
{{n_training_steps}} steps, no held-out loss, and no convergence comparison; direction only, not
magnitude of effect.

**The oracle sentence.** The model receives the true depth coordinate at every generated token
and, on the training-loss evidence above, fits measurably better because of it, and still did
not recover the observed NPHI profile at generation time.

**Post-hoc depth-slope findings.** Two slope contrasts satisfy both the exclusion and the
leave-one-out sign-stability requirement (`reports/DQ_GATE_1.md` G1b) and are reported with
interval language: B2 minus A slope is {{slope_contrast_B2_minus_A_point:+.4f}} v/v per 1000 m
[{{slope_contrast_B2_minus_A_ci_low:+.4f}}, {{slope_contrast_B2_minus_A_ci_high:+.4f}}],
leave-one-out range [{{loo_slope_contrast_B2_minus_A_loo_min:+.4f}},
{{loo_slope_contrast_B2_minus_A_loo_max:+.4f}}]; B-linear minus B-abs slope is
{{slope_contrast_B-linear_minus_B-abs_point:+.4f}} v/v per 1000 m
[{{slope_contrast_B-linear_minus_B-abs_ci_low:+.4f}}, {{slope_contrast_B-linear_minus_B-abs_ci_high:+.4f}}],
leave-one-out range [{{loo_slope_contrast_B-linear_minus_B-abs_loo_min:+.4f}},
{{loo_slope_contrast_B-linear_minus_B-abs_loo_max:+.4f}}]. All other slope quantities (each
arm's own slope minus the real slope, and the B-abs minus A and C minus A slope contrasts) have
full intervals crossing zero and are reported descriptively only, with no interval language, per
3.4 (see `figs/F5_data.csv` for the full per-well table).

**Third estimator convention.** A third bias convention (absolute value taken inside the
per-realization loop, before the realization reduction) exists on disk in a separate audit
package and is post-hoc, not one of the two conventions (signed, magnitude-after-reduction)
used in the confirmatory or guard results above. Under this convention, B-linear minus B-abs
(row 26 of that package's contrast table) is {{third_convention_row26_point:.10g}}
[{{third_convention_row26_ci_low:.10g}}, {{third_convention_row26_ci_high:.10g}}], excluding
zero; it is noted here as a third data point on the same B-linear/B-abs feature-design
mismatch already reported above, not as an independent confirmatory result.

## Discussion

The central finding is that depth conditioning, at three levels of feature richness and
through two structurally different mechanisms (discrete-token and continuous-output
generation), did not correct the mean porosity bias observed without it, on the four fixed
comparisons and at the minimum detectable effects computed here. The two comparisons that did
exclude zero (B-linear minus B-abs, C minus A) characterize differences between arms, not
evidence that either arm's own bias is small.

Three unplanned findings sharpen this picture. First, the flattening of the generated NPHI
profile relative to the observed depth trend is universal across every arm tested, regardless
of whether or how depth enters the model; adding richer depth features did not reintroduce the
trend. Second, the failure is not a simple pull toward the training corpus mean: the four
discrete arms generate below both the held-out real mean and their own training mean, while the
continuous arm generates above both, so two different formulations of the same modeling problem
fail in opposite directions. Third, under-dispersion of the same order as the mean bias itself
is present in every arm, and the ruled attribution rules out quantization as the primary cause:
tokenizer reconstruction error is under one percent of the real spread. Because the only
continuous-output arm in this study is also the only deterministic arm, the design cannot
separate a quantization effect from a determinism effect within the continuous formulation, and
this study does not claim to.

The oracle sentence captures the strongest form of the result: the model is given the true
depth coordinate at every generated token, and the training-loss evidence (hedged, single
realized fit, direction only) indicates it fits measurably better for having it, and the
generated profile still does not recover the observed one. Whatever the underlying mechanism,
it does not appear to be a lack of access to the depth coordinate itself.

**Future work.** This study did not test whether the flattening is a property of the discrete
token vocabulary's resolution, of the autoregressive generation procedure's error accumulation
over the scored window, of the training objective's interaction with a highly skewed feature
distribution, or of some combination, and it asserts nothing about which of these is
responsible. A calibration-first evaluation programme, one that measures generation dispersion
and depth-trend fidelity as primary targets declared in advance of any depth-conditioning
mechanism being compared, would be needed to separate these candidate explanations from the
mean-bias question addressed here.

## Conclusions

Across five model variants and two structurally different generation mechanisms, no tested form
of depth conditioning corrected the signed mean NPHI bias observed in a discrete autoregressive
well-log generator trained without depth information, at the minimum detectable effects reported
above. Two of four fixed comparisons excluded zero; both characterize differences between arms
rather than evidence that either arm's own bias is small. Unplanned descriptive results found
the flattening of the generated depth trend, the under-dispersion, and the divergence from the
training-corpus mean to be properties shared across every arm tested, not corrected by any
tested depth-conditioning mechanism, including one (B2) that fits its training data measurably
better than the baseline. This is a single-basin ablation with {{n_test_wells}} test wells and
one realized fit per arm; the Limitations section states what that does and does not support.

## Limitations

1. Eight test wells is the inferential sample size for every interval in this manuscript, and
   is the binding constraint on statistical power. The minimum detectable effects reported
   alongside the four primary comparisons should be read together with each point estimate, not
   in place of it.
2. Each arm reflects one realized fit; weight initialisation was not explicitly seeded, so the
   training run for a given arm is not bit-reproducible even with the same code and data. No
   claim in this manuscript should be read as characterizing fit-to-fit variance.
3. No convergence comparability exists across arms: all arms trained for a fixed
   {{n_training_steps}} steps with no plateau reached and no early-stopping or checkpoint
   selection. Differences in final training loss are reported as directional evidence only, not
   as evidence of converged model quality.
4. The train/dev/test split is random, not spatial. Findings here should not be read as
   evidence about spatial or cross-basin generalization.
5. This is a single-basin study (FORCE 2020, Norwegian Continental Shelf). No claim is made
   about behavior on other basins or acquisition contexts.
6. The discrete token vocabulary and its clustering were designed once, for this study's data,
   and were not varied as an experimental factor. Any effect of tokenizer design choices on the
   findings above is untested.
7. The sealed tokenizer's reconstruction statistics did not reproduce under a different library
   environment (entropy {{tokenizer_diffenv_entropy:.3f}} versus the sealed
   {{tokenizer_sealed_entropy:.3f}}; NPHI RMSE {{tokenizer_diffenv_rmse_NPHI:.4f}} versus sealed
   {{tokenizer_sealed_rmse_NPHI:.4f}}), and a refit under the exact archived environment pins
   could not be attempted because no Python interpreter available on this machine supports the
   pinned scikit-learn version. Nothing stronger than these two facts is claimed about
   tokenizer reproducibility.
8. Reimplementing a method from its description is not the same as replicating a specific prior
   run: this study's transformer and tokenizer were reimplemented from specification, and no
   claim of replication (as distinct from independent implementation) is made anywhere in this
   manuscript.
9. Arm C bundles four choices at once (continuous output head, MSE training loss, deterministic
   generation, and nearest-centroid feedback quantization at inference), and this design cannot
   attribute an observed difference to any one of the four in isolation. No claim in this
   manuscript attributes Arm C's behavior to a single one of these choices.
10. Arm B2's Athy decay feature was fit with a leakage bound of {{athy_frozen_phi0:.4f}} versus
    a train-only fit shift of up to 0.0267 in feature units; this is a bounded leakage estimate,
    not a fully held-out evaluation, and its effect on the reported outcome for B2 was not
    separately measured.
11. Thirty-two intervals are reported across the headline, guard, and slope tables combined,
    with no multiplicity correction applied across them. Interval language ("the paired 95
    percent bootstrap interval excluded zero", "no detectable correction at this precision") is
    restricted in this manuscript to the four primary comparisons on the signed primary metric;
    every other interval is reported descriptively, per the subsection structure above.

Arm D, which subtracts the Athy trend from targets and never adds it back before scoring, is
withdrawn from every comparison, table, and figure above and appears only in an appendix as a
documented scoring defect, never as supporting evidence for any claim in this manuscript.

NPHI (neutron porosity) is a neutron porosity log, affected by lithology, shale content, gas
effect, and borehole conditions, and is not equivalent to effective porosity; every statement in
this manuscript about "porosity" should be read as a statement about the NPHI log response, not
about a corrected or effective porosity value.

## Corrections to the prior (v1) report

Four defects in the prior version of this study's reported results are corrected here. First,
its headline relative-bias figure of {{v1_relbias_reported_pct:g}} percent used the generated
mean as the denominator; the corrected figure, using the observed (real) mean as the
denominator, is {{v1_relbias_corrected_pct:.1f}} percent. Second, the table it labelled a
Wasserstein-1 distance was in fact a difference of means, not a W1 distance; every W1 value in
this manuscript is computed with `scipy.stats.wasserstein_distance` (see Table T1's caption for
the exact call signature) and is a genuine distributional distance. Third, the 4.8 million
parameter count it reported for its own model cannot be reconstructed from any artifact that
still exists; this manuscript reports parameter counts recovered by direct code inspection of
the reimplemented models instead (Arm A: {{params_A:,}}; see the run log for the full set).
Fourth, its code-availability statement, as published, was false. The prior version's source
code, model checkpoint, and generated outputs are permanently unrecoverable; only its tokenizer
artifacts survive, and this study did not use them (a validation gate found they reconstruct
this study's data materially worse than a fresh refit, so every arm here uses a tokenizer
refit fresh on this study's own training wells).

## Code Availability

The code that produced the archived raw outputs analyzed in this manuscript is at
`{{code_repo_name}}`, commit `{{code_commit_results}}`. The archived raw output file analyzed
throughout (`{{code_raw_filename}}`) has sha256 digest `{{code_raw_digest_sha256}}`. This
manuscript claims only that the archived raw outputs reproduce every arm-level metric reported
above (verified in `audit/verify_all.py`, see `reports/DQ_GATE_6.md`); it does not claim that
the training and generation pipeline itself is reproducible end to end, which was not tested. No
DOI is claimed for this repository state.
