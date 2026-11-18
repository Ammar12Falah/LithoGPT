# LithoGPT confirmatory test: protocol

Author: Ammar Falah Hasan Al Saeedi. Written 18 November 2026.
This file was committed before the FORCE 2020 open and blind test wells were downloaded or opened.

## 1. Purpose
Test, on wells never used before, how a small autoregressive transformer for well-log generation compares with simple non-neural baselines, and whether depth conditioning helps.

## 2. What has already been seen
The 98-well FORCE 2020 training file was split by well into 80 training, 10 development and 8 held-out wells (split_manifest_2026-07-31.json). The author has analysed those 8 held-out wells (August 2026 manuscript, checks of 18 November 2026). They are reported as pilot wells only. This protocol was designed after seeing them.

## 3. Confirmatory wells
The 10 open and 10 blind test wells of FORCE 2020. A sample is valid when GR, RDEP, NPHI and RHOB are all finite and RDEP is above zero. A well is eligible if it has at least 2,000 valid samples. Every eligible well is used. None is dropped after results are seen.

## 4. Data handling (changes from the pilot)
- Deep resistivity enters as log10.
- A boundary token marks every removed interval. No training window, transition count, run or lag pair crosses one. In generation, boundary positions are copied from the real well.
- The tokenizer (scaler and 1,000-centroid k-means, seed 20260715, pilot settings) is fitted once on the 80 training wells and saved with its SHA-256.
- Nothing is fitted on development, pilot or confirmatory wells, except the tuned settings in section 6, which use development wells only.

## 5. Models
- Arm A: decoder-only transformer, 6 layers, width 256, 8 heads, 512-token context, no depth input.
- Arm B2: the same model with the 12-feature depth channel. The decay constant is fitted on training wells only. Depth is the real measured depth of the well.
- Arm C: the same backbone with a 4-output regression head, mean squared error loss, deterministic decoding, one realization.
- Seeds: 20260715 to 20260726 for A and B2, paired. 20260715 to 20260719 for C.

## 6. Tuning, development wells only
- Transformer: dropout (0, 0.1, 0.2) and weight decay (0.01, 0.1), tried on Arm A with seed 20260715. The setting with the lowest development loss is used for every arm and seed.
- Checkpoints every 100 steps up to 3,000. The reported model is the checkpoint with the lowest development loss. The step-3,000 checkpoint is also scored, as a secondary result.
- First-order chain: interpolation weight. Trigram: discount. Block resampling: block length, from 8, 16, 32, 64, 128, 256 and 512 samples, chosen by the structure score in section 8.

## 7. Baselines
Constant predictor. Tuned first-order chain. Tuned trigram. Block resampling: real intervals drawn from training wells. Depth-matched block resampling: the same, drawn from within 100 m of the target depth, widening to 250 m, then any depth. Each sampled baseline is run with 12 sampling seeds, paired by order with the 12 training seeds.

## 8. Generation and scores
Each well is primed with its first quarter (at least 512 tokens) and the rest is generated, 5 realizations, temperature 1. Scores are computed per well on matched positions, averaged over realizations, then over wells with equal weight.
- Bias: absolute and signed mean NPHI error.
- W1: Wasserstein-1 distance on NPHI.
- Spread: generated over real NPHI standard deviation.
- Trend share: share of NPHI variance carried by 100 m bin means.
- Structure score: mean absolute gap between generated and real chance-corrected token agreement at lags 1, 2, 5, 10, 20, 50, 100 and 200. Lower is better.
- Facies structure score: the same on lithofacies. Each token is mapped to its most common lithofacies in the training wells. Real wells use their true labels where the file has them.
- Copying: share of generated 10-, 20- and 50-token sequences found word for word in the training wells, against the same share for real wells.
- One step ahead: negative log-likelihood and top-1 accuracy.

## 9. Main comparisons
On the confirmatory wells, with the selected checkpoints:
1. B2 minus A, absolute NPHI bias.
2. A minus tuned chain, absolute NPHI bias.
3. A minus trigram, structure score.
4. A minus block resampling, structure score.
Each is reported with a 95% interval from a bootstrap that resamples wells and seeds together, 10,000 draws. All four are reported whatever they show. Everything else is descriptive. Pilot-well results are reported separately.

## 10. Changes
Any departure from this file is recorded in DEVIATIONS.md with its date and reason, and reported in the paper.
