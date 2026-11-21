# Independent checks

Two read-only checks of the confirmatory results, run by Codex, an AI agent from another vendor,
working separately from the agent that built and ran the pipeline. The author ran them and supplied
the input files. They were made on 21 November 2026, after the results were opened (11:49:31 UTC)
and published (OPENING_RECORD_2026-11-21.md, pushed 11:50:22 UTC):
recount.py created 12:00:00 UTC, last changed 13:36:51 UTC; 15-cell-score-check.csv written 13:52:49 UTC.
The two files here are byte-identical to the files in the Codex output folder:
- recount.py, SHA-256 773cd505c0efe150ef1075d6c02640ca3f3b7717ad37fead4bfbdd02b7615a36
- 15-cell-score-check.csv, SHA-256 10e973f3147809b3cb5b82553167e68802aaae2d805e9275e5e892b94b4e30a1

Inputs. The checks read copies of 210 files from the run folder and 3 data files. Before this folder
was added, all 210 were found equal to the public hash list run_record/run_folder_2026-11-21.sha256,
and the 3 data files (confirmatory_wells.csv, hidden_test.csv, leaderboard_test_features.csv) equal
to the SHA-256 values in the pipeline's c06 manifest.

## What they checked
1. recount.py, on the governing results only (confirmatory wells, lowest-development-loss checkpoint;
   A, B2, the tuned chain, the trigram and block resampling; 12 seeds; all 20 wells). From the stored
   per-well scores it checks that each stored mean is the mean of its 5 realizations, that every
   stored absolute bias equals the absolute value of the stored signed bias, and that the wells and
   metadata agree across files. It then recomputes the four comparisons with a 10,000-draw bootstrap
   over wells and seeds, under five sampling conventions ("primary", "seeds first", "continue stream",
   "MT19937", "nearest rank"). Its printed output is not in this folder.
2. 15-cell-score-check.csv: for 15 preselected cells (method, seed, well) on the confirmatory wells,
   5 realizations each (75 rows), the absolute NPHI bias (Q25) and the structure score (Q26) were
   recomputed from the generated archives and the raw well files, and set beside the stored values with
   the size of each difference. The script that made it is not in this folder.

## What they did not check
- No retraining, no regeneration, and no check that the generated sequences came from the stated
  checkpoints or that the checkpoints were chosen correctly.
- recount.py covers only the governing results; the step-3000 and pilot comparisons were not recounted.
- The CSV covers 15 cells, not every well, seed and source.
- Scores other than absolute NPHI bias and the structure score, Arm C, the side baselines, the
  tokenizer fit and the training itself were not checked.
