# Questions on the protocol, and the reading used

Where `PROTOCOL.md` is unclear, the most cautious reading was taken and the work carried on.
Each item: the question, the choice, and why. Section numbers refer to the protocol.
None of these is a departure from the protocol, so `DEVIATIONS.md` lists none.

## Data (sections 3 and 4)

**Q1. What is a "removed interval"?**
Choice: a boundary token goes wherever one or more rows were removed by the validity mask between two kept rows, and wherever the depth step between two kept rows is more than 1.5 times the well's median step (a gap in the file itself; 1.5 is the a31 convention). A row with no finite depth is also removed. No boundary at the top or bottom of a well.
Why: both are places where two kept samples are not one sample apart; leaving either out would let pairs cross a gap.

**Q2. Does the validity mask apply to training, development and pilot wells too?**
Choice: yes, the same mask everywhere. In the 98 wells, RDEP > 0 removes no row (628,916 valid training rows, as before).
Why: section 4 changes data handling for the whole pipeline; one rule for all wells.

**Q3. Does a training window that starts with a boundary token "cross" it?**
Choice: a window may start with the boundary token that opens a segment, but it never holds tokens from two segments. The boundary then works as a start marker. The same rule holds for the count models: the count from the boundary to the first token of the next segment is kept; no count runs from the last token of one segment.
Why: if the boundary token could never enter a window, the model could not start a new segment in generation (it would have no input at all). This reading never joins two segments.

**Q4. Segments too short for a full 513-token window.**
Choice: not used for training windows; no padding. That is 1.4% of training tokens. They are used everywhere else (development loss, counts, scoring).
Why: padding would change the training recipe; the pilot never padded.

**Q5. Context after a boundary, in generation and in one-step-ahead scoring.**
Choice: the context starts at the boundary token and is at most 512 tokens. The model never sees across a boundary.
Why: section 4, read strictly.

**Q6. Boundary depth for Arm B2.**
Choice: a boundary position carries the measured depth of the row after it.

## Models and training (sections 5 and 6)

**Q7. Development loss.**
Choice: teacher-forced mean next-token cross entropy over every development token that has a predecessor in its segment (or the boundary that opens it), in non-overlapping chunks of up to 512 inputs that never cross a boundary (the 11b layout, per segment). Arm C: mean squared error in standardized units on the same chunks. Computed every 100 steps.
Why: covers every development token once, uses the pilot's layout, never crosses a boundary.

**Q8. Where does dropout go, and what does weight decay touch?**
Choice: dropout on the embeddings, the attention weights and both residual branches, one rate. Weight decay on all parameters, as in the pilot (torch AdamW, which the pilot ran at its default 0.01 on every parameter).
Why: standard placement; keeps the pilot recipe for weight decay. With dropout 0 the block computes what the pilot block computed.

**Q9. Checkpoint selection and ties.**
Choice: best.pt is the checkpoint with the lowest development loss among steps 100, 200, ..., 3000; a tie goes to the earlier step. final.pt (step 3000) is also generated and scored, as the secondary result.

**Q10. Which checkpoints to keep.**
Choice: every 100-step checkpoint (weights only) stays on the pod volume; best.pt, final.pt, run.json and the development-loss history come back to the Mac.

**Q11. Arm C details.**
Choice: target = the next row's standardized GR, log10 RDEP, NPHI, RHOB; generation feeds back the nearest centroid as the next input token (the sealed pilot run's convention); the generated curve is the decoded regression output.

**Q12. Training batches.**
Choice: the pilot scheme (pick a training well uniformly, then a window start uniformly), limited to windows inside one segment.

**Q13. Determinism on the GPU.**
Choice: on CUDA the plain math attention kernel is forced, TF32 is off and deterministic algorithms are on. The same-seed test is rerun on the pod before the study starts (RUN_PLAN.md). If it fails there, the run stops and the author decides.

## Generation (section 8)

**Q14. "The rest is generated."**
Choice: the whole rest of the well, no cap. The pilot capped at 20,000 samples.
Why: the literal reading. It costs more generation time; the run plan counts it.

**Q15. Prime length with boundary tokens.**
Choice: prime = max(512, int(0.25 x L)), L the sequence length including boundary tokens. Boundary tokens inside the prime are the real well's.

**Q16. Generation seed.**
Choice: the pilot convention. One generation seed, 20260715, for every model run; the NumPy generator is re-seeded at the start of each well. So the seed-to-seed spread is training spread. Sampled baselines: each well's generator is seeded with that run's sampling seed.

**Q17. Eligibility for pilot and development wells.**
Choice: the section 3 rule (at least 2,000 valid samples) is applied to them too. All 8 pilot and all 10 development wells pass.

## Baselines (sections 6 and 7)

**Q18. Tuning criterion for the chain and the trigram.**
The words "chosen by the structure score in section 8" sit in the block-resampling sentence.
Choice: the structure score on development wells, for all three settings (interpolation weight, discount, block length).
Why: it is the only criterion the bullet states, and it gives the count baselines their best shot on comparisons 3 and 4. The development NLL of each setting is recorded too. On these wells it would pick weight 0.02 (structure picks 0.01) and discount 0.75 (structure picks 0.9). See out/b04_tuning.json.

**Q19. Grids.**
Chain weight: 0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005 (07_markov_interpolated.py). Trigram discount: the protocol gives none; chosen grid 0.1, 0.25, 0.5, 0.75, 0.9 (holds the pilot's 0.75). Block length: 8 to 512 as in section 6.

**Q20. How tuning runs are sampled.**
Choice: sampling seed 20260715, 5 realizations, all 10 development wells, same scoring code as the study. A tie goes to the earlier grid value.

**Q21. Block length for depth-matched block resampling.**
Choice: the length tuned for plain block resampling.
Why: section 4 allows no fitted setting on development wells beyond those listed in section 6, and section 6 lists one block length.

**Q22. How blocks are drawn.**
Choice: uniformly over all valid start rows pooled over the 80 training wells. A block lies inside one segment. The last block of a target segment is cut to fit. Depth matching compares the depth of the block's first row with the real depth at the first position it fills (within 100 m, else 250 m, else any depth). Curves are the real training curves; facies come from the token map, as for every generated sequence.

**Q23. Constant predictor.**
Choice: the equal-weight mean over the 80 training wells of each curve (01_constant_baseline.py convention), RDEP averaged in log10; its token is the nearest centroid. One realization, the same for every seed. Its structure scores and trend share are not defined (no variance; chance agreement 1) and are reported as not defined.

**Q24. Counts and the boundary.**
See Q3. The chain has one extra row for the boundary state; the trigram backs off to the bigram right after a boundary, and its context may be (boundary, first token) but never (token of one segment, boundary).

## Scores and comparisons (sections 8 and 9)

**Q25. Absolute bias.**
Choice: per realization |mean(gen NPHI) - mean(real NPHI)|, then averaged over realizations, then over wells.
Why: section 8 says scores are computed per realization first.

**Q26. Chance-corrected agreement per well.**
Choice: for one sequence, observed agreement over pairs inside one segment, chance from that sequence's own token shares (the a23/a31 estimator applied per well). A lag with no within-segment pair in the real well is left out for that well.

**Q27. Trend share.**
Choice: fixed 100 m bins of measured depth (floor(depth / 100)); variance of the bin means over the variance of NPHI, both with weights by sample. Reported for generated and real, and the gap.

**Q28. Copying.**
Choice: n-grams that lie inside one segment, matched exactly against all such n-grams of the 80 training wells; the share for real wells uses the same matched positions.

**Q29. One step ahead for Arm C and the non-likelihood baselines.**
Choice: Arm C has no likelihood; its top-1 (nearest centroid of the prediction) and mean squared error are reported. Block resampling and the constant have no one-step score.

**Q30. Real facies where a label is missing.**
Choice: the token's mapped facies. For the blind wells, if the labels sit in a separate file, joining them is a step of the confirmatory run, not of this build.

**Q31. Bootstrap.**
Choice: per (well, seed) differences, seeds paired by order (training seed i with sampling seed i; A and B2 with the same seed). Each of the 10,000 draws resamples wells with replacement and seeds with replacement, and takes the mean over the resampled grid. 95% percentile interval. Bootstrap seed 20260715.

## This build only

**Q32. Smoke test settings.**
Choice: dropout 0 and weight decay 0.01 (pilot settings), since the tuning runs need the GPU. The two pilot wells are the first two in manifest order (16/4-1, 25/2-14), to avoid picking.

## Rulings by the author, made before any confirmatory well was downloaded or opened
- Q18: the reading is kept. On the development wells, likelihood would pick the neighbouring grid value in both cases, by 0.0015 nats for the chain (weight 0.02) and 0.003 nats for the trigram (discount 0.75). Those two settings are also run on the confirmatory and pilot wells and reported as a side result. They are not part of the four main comparisons.
- All other readings are accepted as written.

Pipeline commit: f94ef8689b00177e218ad33496ebbc3dae157d8a (paper_atce repo, branch v4/confirmatory-pipeline)
