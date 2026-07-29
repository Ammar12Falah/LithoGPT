# Depth Conditioning Did Not Correct Mean Porosity Bias in Discrete Autoregressive Well-Log Generation: A Single-Basin Ablation

**[BUILD NOTE, remove before submission: Abstract, Results, Discussion, Conclusions,
Limitations, the corrections note, and Code Availability were assembled at rev4 per brief DQ
(no rev3 was found on this machine at that time, so these were written fresh from
FROZEN_RESULTS.json). Introduction, Related Work, Protocol, and Experimental Family were added
at rev5 per brief DR, after an exhaustive search located a results-independent draft at
`~/.codex/attachments/ea7dcacd-3e84-4bc0-81b0-48a94dafe5b9/pasted-text.txt` (dated 2026-07-29
13:35); those four sections are adapted from that draft, edited for banned language, resolved
citations only, and the seed/realized-fit correction. See `reports/DQ_GATE_4.md` and
`reports/DQ_GATE_10.md`.]**

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

**[Source note, remove before submission: adapted from a found draft, see
`reports/DQ_GATE_10.md`, edited to remove banned language, to cite only references present in
`audit/references_check.txt`, and to correct a "one seed per arm" framing to "one realized fit
per arm" per Plan's error-list item 19.]**

Wireline logs are the primary quantitative record of subsurface rock properties, yet complete,
shareable log data remain scarce: curves are missing over washed-out or uninstrumented
intervals, acquisition is costly, and much of the archive is proprietary. Generative models of
well logs serve several needs at once: augmentation for downstream petrophysical machine
learning, priors for imputation, stress-test scenarios for interpretation workflows, and
synthetic datasets that can be shared where raw logs cannot. Prior work spans sequence-based
adversarial synthesis of well logs, standardized imputation benchmarks, and foundation-scale
pretraining of time-series models across thousands of wells, including a general-purpose
time-series foundation model applied to log prediction and anomaly detection (Koeshidayatullah,
Al-Fakih and Kaka 2024).

This paper studies a discrete autoregressive formulation. Multi-curve depth samples are
tokenized by joint clustering into a shared vocabulary, and a decoder-only transformer models
the resulting token sequences exactly as a language model models text. Generation samples from
predicted categorical distributions, which captures multi-modal tool responses and cross-curve
coupling without committing to a parametric noise model.

The formulation has a structural blind spot: it is coordinate-blind. The model observes token
order but never depth. Porosity in clastic sections is known to decline with burial depth
through mechanical and chemical compaction, classically as an exponential trend, and a model
that cannot see depth has no direct means of expressing a population-level compaction law. At
the measured {{depth_grid_spacing_measured_m}} m sampling interval of this dataset, a 512-token
context spans roughly {{context_window_m:.1f}} m of section, far too short to infer absolute
burial depth from texture alone. A predecessor report on the same corpus observed a systematic
neutron-porosity bias in generated logs and attributed it, plausibly but without a controlled
test, to the missing coordinate. Depth-band offsets have been reported at foundation scale as
well, in independent work reporting systematic reconstruction offsets in shallow and
ultra-deep intervals after large-scale pretraining. Whether explicit depth conditioning
corrects such biases has not, to our knowledge, been tested under controlled conditions.

We test it directly. Everything is held fixed, including the {{n_train_wells}}-well FORCE 2020
training partition, the tokenizer family, a six-layer transformer of model dimension 256, and
the 512-token context, and exactly one factor varies: the mechanism by which depth reaches the
model. Five arms span no conditioning at all, a minimal linear channel on within-well
normalized depth, the same channel on absolute depth, a twelve-feature channel including an
explicit Athy-form compaction term, and a continuous mean-squared-error output head. Four
comparisons were fixed before any result was seen, under a decision rule requiring both a bias
improvement whose paired interval excludes zero and no degradation of any guard metric, with a
standing commitment to report all four outcomes. One realized fit per arm was used, and the
consequences of that choice are stated in Limitations rather than argued away.

The paper makes three contributions. First, the primary comparison returned a null, and the
null has a visible mechanism: depth conditioning, at three levels of feature richness, did not
correct the mean porosity bias, and binning the held-out interval by absolute depth shows that
every arm, conditioned or not, produces a porosity profile materially flatter than the real
one. Depth was supplied to the conditioned arms from each held-out well's true measured-depth
trajectory, so the models were handed the correct coordinate rather than asked to infer it, and
three levels of feature richness still left the flattening essentially unchanged. Second, the
one resolved depth finding is methodological rather than physical: within-well normalized depth
produced a systematically more negative porosity bias than absolute-depth encoding at an
identical parameter budget, consistent with fractional position being unable to identify
absolute burial depth across heterogeneous wells, and this is read as a feature-design
mismatch, not a defect. Third, as a secondary result, a deterministic continuous baseline was
constructed and scored under an evaluator identical to that used for the discrete arms; the two
formulations differ on the primary metric with an interval excluding zero, erring in opposite
directions.

A controlled reimplementation additionally did not reproduce the direction of the previously
reported porosity bias; the predecessor's artifacts are unrecoverable and the discrepancy
cannot be attributed to any single cause, so it is reported as a reproducibility finding at
moderate weight rather than a diagnosed mechanism (see Corrections, below).

## Related Work

**[Source note: same provenance as Introduction. 13 of 14 works cited by the found draft are
NOT in `audit/references_check.txt` and are therefore described here without formal citation,
per this brief's "cite nothing unresolved" rule; see `reports/DQ_GATE_10.md` for the full
removed-citation list.]**

The classical machinery for generating synthetic subsurface property fields is geostatistical:
simulation conditioned on variogram models or on training images. Two properties of that
tradition matter here. Spatial coordinates are first-class inputs, and systematic depth trends
are handled by explicit decomposition, in which a deterministic trend is fitted, removed,
simulated around, and restored. Neural autoregressive generators invert both defaults:
coordinates are absent unless injected, and any trend must be learned implicitly from windowed
context. This study asks whether reintroducing the coordinate, in forms ranging from a raw
channel to a featurization that embeds a classical compaction trend directly, recovers what the
classical decomposition provided.

Most deep-learning work on logs is conditional, predicting or imputing one curve from others,
including standardized imputation benchmarks and sequence-imputation studies in single-basin
settings. Closer to unconditional generation, prior work on this corpus family includes a
time-series generative-adversarial pairing for synthesis and imputation, and a general-purpose
time-series foundation model applied to log prediction and anomaly detection
(Koeshidayatullah, Al-Fakih and Kaka 2024). Adversarial and autoregressive approaches to
multivariate series more generally face a shared difficulty of jointly preserving marginal
distributions and spatial texture, which are the two axes our guard metrics monitor.

Discrete tokenization of continuous signals for autoregressive modeling follows the broader
pattern established for language-model pretraining. In the well-log domain, at least one
foundation-scale study tokenizes log patches into a learned vocabulary and pretrains across
more than a thousand wells for interpretation tasks, reporting systematic offsets in shallow
and ultra-deep intervals; that is evidence that scale alone does not resolve depth-dependent
bias, and evidence that small controlled studies remain useful for attribution. The present
work differs from that line and from the imputation literature in intent: rather than adding
scale, it holds a small model fixed and varies one factor in order to attribute an effect to
it.

How a coordinate is presented to a network matters independently of whether it is presented at
all; high-frequency coordinate encodings of the kind used in other domains motivate our
twelve-feature arm. The compaction physics itself is classical and, for offshore Norway
specifically, has been quantified in the regional literature, which makes this basin a setting
where the expected trend is characterized in advance.

No prior work known to us isolates depth conditioning as a single manipulated variable in
autoregressive log generation under a protocol fixed in advance. Imputation benchmarks
condition on other curves, foundation models change many factors at once, and geostatistics
assumes the trend rather than testing whether a sequence model can learn it or be given it.
That isolation, not a new state of the art, is the contribution.

## Protocol

**[Source note: same provenance as Introduction, section content only (no external citations
in this section beyond software).]**

### Fixed comparisons

Four comparisons were written down before any result was seen and committed to a private
repository, with a standing commitment to report all four regardless of outcome. Each is
stated in the explicit direction in which its difference is formed, so that no reader has to
infer the sign convention from an arm ordering: primary, B2 minus A, the strongest good-faith
test of the depth-conditioning hypothesis; secondary, B-abs minus A, the minimal-mechanism
test; methodological, B-linear minus B-abs, isolating the depth-encoding choice at matched
capacity; and output formulation, C minus A, testing whether comparison against a continuous
baseline is informative at all. A positive depth-conditioning claim required both an NPHI
mean-bias improvement whose paired well-level bootstrap interval excludes zero and no
degradation of the guard metrics, assessed with paired intervals of the same construction; a
porosity gain bought with texture loss counts as a trade-off, not a correction. The protocol
was committed privately, not externally time-stamped, so it is described as fixed in advance
rather than independently verifiable.

### Metrics

The primary metric is signed NPHI mean bias, generated minus real, computed over matched
evaluation support. Distributional fidelity is measured by the one-dimensional Wasserstein
distance between real and generated NPHI samples (`scipy.stats.wasserstein_distance`), which
satisfies W1 greater than or equal to the absolute mean difference by construction; that
inequality serves as a standing arithmetic check and holds without exception across all
{{w1_sanity_check_n_triples}} well, arm, and realization triples checked. Guard metrics are GR
mean bias, RHOB mean bias, and an autocorrelation fidelity score (root-mean-square difference
between generated and real NPHI autocorrelation, lags 1 to 20, computed per realization against
that well's own real autocorrelation and averaged over the five realizations within each well).

Degradation of a guard means growth in error magnitude, so guard bias is taken in absolute
value per well before averaging across wells; a first computation using signed differences
answers a different question wherever per-well biases cross sign, and both conventions are
reported in full, with the comparisons on which they disagree identified individually. The same
distinction bears on the primary metric: per-well NPHI biases cross sign within Arms A, B-abs,
and C, and do not within Arms B-linear and B2, so an arm's mean bias and its mean per-well
absolute bias can order two arms differently. The comparisons fixed in advance are on the
arm-level signed metric, because the hypothesis concerns a population-level compaction trend
rather than per-well accuracy; both readings are reported for all four comparisons.

### Estimators and uncertainty

The independent unit is the well. For each arm, well, and realization, a metric is computed per
realization; realizations are averaged within each well; wells receive equal weight; and arm
contrasts use paired well-level differences. Uncertainty is a nonparametric bootstrap over
wells, resampling the {{n_test_wells}} wells with replacement over
{{estimator_recompute_n_resamples}} resamples at seed 20260715, with 2.5 and 97.5 percentile
intervals on the mean paired difference and a shared index draw for pairing. Realizations are
never concatenated and treated as independent samples. For Arm C, the within-well average over
five identical realizations is an identity and does not alter any distributional statistic or
narrow any interval.

The equal-weight well mean is primary; a sample-weighted pooled statistic is reported as a
sensitivity estimator. Estimators are never mixed between the numerator and denominator of a
ratio; relative bias is reported as the ratio of pooled means, never as an arithmetic mean of
per-well percentages. Thirty-two paired intervals were computed in total and no multiplicity
correction was applied. Inferential language is confined to the four comparisons fixed in
advance on the primary metric; every other interval in this paper is reported as descriptive.
Guard intervals are deliberately left uncorrected, because widening them would make degradation
harder to detect and would therefore favour our own conclusion.

## Experimental Family

**[Source note: same provenance as Introduction; the estimator revision disclosure below is
placed in this section per this brief's explicit instruction (G10d).]**

**Estimator revision disclosure (required content):** the analysis originally used
{{estimator_original_n_resamples}} resamples pooling realization values as independent. The
intervals reported throughout this manuscript use {{estimator_recompute_n_resamples}} paired
well-level resamples. The revision postdates the first results (first result commit
{{estimator_first_result_commit_utc}} UTC; paired well-level estimator first committed
{{estimator_recompute_commit_utc}} UTC). The reason for the revision is that pooling
realizations treats non-independent samples (five realizations drawn from the same trained
model on the same well) as independent, which understates the true resampling uncertainty.
Every interval printed inside the sealed run log itself uses the original, superseded estimator
and is not citable; only the paired well-level intervals recomputed from the archived raw
outputs are used for inference anywhere in this manuscript.

### Data

We use the public well-log release of the FORCE 2020 machine-learning competition (Bormann,
Aursand, Dilib, Dischington and Manral 2020), curated from Norwegian Petroleum Directorate
holdings for offshore Norway. The full release comprises {{n_force_release_wells}} distinct
wells in three named partitions: {{n_train_wells}} training wells,
{{n_force_open_test_wells}} open leaderboard test wells, and {{n_force_blind_test_wells}} blind
final test wells. This study uses exactly the {{n_train_wells}}-well training partition and
does not use the competition's own 20 test wells at all; all splits below are a re-partition
within those {{n_train_wells}} wells.

Four curves are modeled, in the fixed order used throughout: gamma ray (GR, gAPI), deep
resistivity (RDEP, ohm-m), neutron porosity (NPHI, v/v), and bulk density (RHOB, g/cm3),
indexed by measured depth; resistivity enters untransformed, with no logarithmic compression
applied. A validity mask is applied before tokenization, and all sample counts below are counts
of masked-valid samples. The nominal FORCE depth grid is {{depth_grid_spacing_nominal_m}} m;
the pipeline measures its own spacing from the pooled data and obtains
{{depth_grid_spacing_measured_m}} m, which is used for all interval arithmetic.

Wells are split {{n_train_wells}}, {{n_dev_wells}}, and {{n_test_wells}} into training,
validation, and test partitions by wellbore at a fixed seed, so no borehole contributes samples
to more than one partition. The assignment is random by wellbore rather than spatial (see
Limitations). Standardization statistics and the tokenizer codebook are fitted on the training
wells only; the validation wells were not used for early stopping, checkpoint selection, or any
other decision.

The {{n_test_wells}} held-out wells contain {{full_valid_count}} valid samples, a mean of
{{mean_samples_per_well_full_valid:g}} samples (roughly {{mean_m_per_well_full_valid:g}} m) per
well. Generation is primed on the first quarter of each well and scored on the remainder, so
the scored window contains {{scored_count}} samples, a mean of roughly
{{mean_m_per_well_scored:g}} m per well, spanning {{depth_scored_min_m:.1f}} m to
{{depth_scored_max_m:.1f}} m in measured depth across the pooled window. The scored fraction is
{{scored_fraction:.6f}} rather than exactly three quarters because each well's priming cutoff
is truncated to an integer sample index.

Two population figures for real neutron porosity over the held-out wells are both correct under
their own estimator: the equal-weight mean of the eight per-well means is
{{real_nphi_mean_eqw:.6f}}, and the sample-weighted pooled mean is
{{real_nphi_mean_pooled:.6f}}. The equal-weight figure is primary; every table states its
estimator explicitly.

### Tokenization

Each valid depth sample is a four-component vector of standardized curve values (GR, RDEP,
NPHI, RHOB). Per-curve standardization statistics are computed on the training wells. A joint
codebook of 1,000 centroids is fitted on the standardized training vectors using minibatch
k-means with three initializations, a batch size of 4,096, and a fixed random state. Each
sample is tokenized as the index of its nearest centroid, yielding one token per depth sample
and one sequence per well; decoding inverts the map.

The fitted codebook uses all 1,000 clusters with a usage entropy of
{{tokenizer_sealed_entropy:.3f}} against a uniform ceiling of {{entropy_uniform_ceiling:.3f}},
and reconstructs the four curves with root-mean-square errors of
{{tokenizer_sealed_rmse_GR:.3f}} gAPI for GR, {{tokenizer_sealed_rmse_RDEP:.3f}} ohm-m for
RDEP, {{tokenizer_sealed_rmse_NPHI:.4f}} v/v for NPHI, and {{tokenizer_sealed_rmse_RHOB:.4f}}
g/cm3 for RHOB. The codebook is not persisted as an artifact but refit from the raw data at
each use under a seeded but stochastic minibatch algorithm, in an environment whose clustering
library version is not pinned; reconstruction statistics therefore reproduce only to roughly
three decimal places across builds (Limitations).

Per-sample reconstruction error does not bound the detectability of a population mean shift,
because zero-mean errors average down. The reconstruction mean bias for NPHI on the scored
held-out window was audited directly: {{tokenizer_reconstruction_bias_eqw:+.6f}} under the
equal-weight well estimator, and {{reconstruction_bias_pooled:+.6f}} under the sample-weighted
pooled estimator. The offset is roughly seventy to one hundred and forty times smaller than the
arm-level porosity biases at issue, and it is positive (reconstruction is very slightly too
porous) while four of the five arms are biased toward lower porosity, so a global tokenizer
offset is the wrong sign to explain them. Two second-order effects are disclosed as
limitations: reconstruction residual correlates with absolute depth at a per-well median of
{{reconstruction_depth_corr_median:+.4f}} across the eight held-out wells (range
{{reconstruction_depth_corr_range_low:+.4f}} to {{reconstruction_depth_corr_range_high:+.4f}}),
and quantization shrinks extreme NPHI values toward codebook centres.

Before any arm was trained, the predecessor's saved tokenizer artifacts were tested against a
fresh refit under a validation gate fixed in advance. The predecessor codebook used
{{predecessor_tokenizer_clusters_used}} of 1,000 clusters with a usage entropy of
{{predecessor_tokenizer_entropy:.3f}}, and reconstructed NPHI at
{{predecessor_tokenizer_rmse_NPHI:.4f}} v/v against {{tokenizer_sealed_rmse_NPHI:.4f}} for the
fresh fit; it failed the gate on every axis, and all arms use the fresh fit. Arm A therefore
cannot be described as a replication of the predecessor: it does not share the predecessor's
tokenizer.

### Backbone

All arms share a six-layer, pre-norm, decoder-only transformer with model dimension 256, eight
attention heads, a feed-forward expansion factor of four, learned positional embeddings over a
512-token context, and untied input and output embeddings. The parameter count is
{{params_A:,}} and reconciles exactly as {{backbone_token_embed_params:,}} token-embedding
parameters, {{backbone_positional_params:,}} positional parameters,
{{backbone_params_per_block:,}} parameters per block across {{backbone_n_blocks}} blocks, a
{{backbone_final_norm_params}}-parameter final normalization, and a
{{backbone_output_head_params_discrete:,}}-parameter output head. At the measured spacing, the
context window spans approximately {{context_window_m:.1f}} m of section.

### Conditioning arms

Arm A, the baseline, receives no depth input; it is the coordinate-blind predecessor
architecture reimplemented. Arm B-linear passes a single scalar depth feature (per-well
min-max normalized depth on [0, 1]) through a learned linear projection to 256 dimensions,
added to the token embedding at every position, adding 512 parameters; a given value therefore
denotes a fixed fractional position in the logged interval rather than a burial depth, so no
population-level compaction law can be expressed through this channel. The arm is retained
deliberately as a feature-design exhibit rather than silently corrected: relative depth carries
genuine within-well information, and the mismatch is between the feature and the cross-well
relationship under test, not a software defect. Arm B-abs applies the identical mechanism and
parameter budget to absolute measured depth under corpus-wide standardization, so the encoder
input identifies burial depth across wells; the B-linear/B-abs pair isolates the depth-encoding
choice at matched capacity. Arm B2 adds a twelve-feature depth channel (3,328 parameters): one
within-well normalized depth term, one Athy-form compaction term exp(-d/lambda), and five
sine-cosine Fourier pairs at log-spaced wavelengths from 10 m to 5,000 m. The Athy parameters
were obtained by nonlinear least squares with a Huber loss (scale {{athy_huber_loss_scale}}),
bounded {{athy_phi0_bounds_low}} to {{athy_phi0_bounds_high}} on surface porosity and
{{athy_lambda_bounds_low_m:g}} to {{athy_lambda_bounds_high_m:g}} m on decay length, fit as
phi(z) = phi0 * exp(-z/lambda): phi0 = {{athy_frozen_phi0}}, lambda = {{athy_frozen_lambda_m:g}}
m, estimated on all {{n_full_training_eligible_wells}} wells (the 80/10/8 partition combined)
before the split; the leakage this introduces is quantified in Limitations item 9. Only the
decay length enters the model input. B2 is the primary conditioning mechanism, being the strongest
good-faith featurization constructed in advance. Arm C replaces the 1,000-way softmax head with
a four-output linear head trained with mean squared error on standardized curve values
({{arm_C_param_delta:,}} parameters relative to A: {{backbone_output_head_params_discrete:,}}
for the discrete head versus {{backbone_output_head_params_continuous:,}} for the continuous
one); decoding is deterministic, so Arm C tests a complete continuous baseline formulation as
commonly deployed, bundling target representation, loss, head size, and probabilistic
semantics, rather than isolating any one of them. One further conditioning variant, a
trend-residual arm, was implemented, found on audit to omit the inverse trend transform at
decode and scoring time, and excluded; it lies outside the four comparisons and is documented
only in Limitations.

### Training and generation

Each arm reflects one realized fit; weight initialisation is not explicitly seeded (no
`torch.manual_seed` call exists anywhere in the training code), so this is disclosed as a
limitation rather than presented as a controlled repetition. Training uses AdamW at a constant
learning rate of {{training_lr}} with no scheduler, a batch size of {{training_batch_size}},
random-crop batching, and a fixed {{n_training_steps}} steps, with no early stopping and no
checkpoint selection. Final training losses for the four discrete arms were
{{final_train_loss_A}} for A, {{final_train_loss_Blinear}} for B-linear,
{{final_train_loss_Babs}} for B-abs, and {{final_train_loss_B2}} for B2; Arm C optimizes a mean
squared error on standardized curve values and its loss ({{final_train_loss_C_mse}}) is not
comparable. No arm had plateaued at the final step.

Each model is primed with an unmodified real token prefix consisting of the first quarter of
the held-out well (roughly {{prime_tokens_approx:g}} tokens, of which the model conditions on
the trailing 512), then generates autoregressively over the remaining three quarters. The
number of tokens to generate is fixed before the loop begins as the smaller of the remaining
real samples and a ceiling of {{max_gen_len:g}} samples; the ceiling never binds for this well
pool, so real and generated array lengths match element by element for every well and every
arm, and all metrics are computed on matched support. Depth-conditioned arms receive depth from
the held-out well's true measured-depth trajectory throughout generation, advancing by one grid
spacing per generated token: depth is oracle-supplied, not itself generated. This is the
intended manipulation: the question is whether a model given the correct coordinate uses it,
not whether the coordinate can be inferred. {{n_realizations}} realizations are generated per
well per arm; Arm C decodes at temperature zero, so its five stored realizations are identical
by construction, a property of the arm rather than an evaluation artifact.

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
