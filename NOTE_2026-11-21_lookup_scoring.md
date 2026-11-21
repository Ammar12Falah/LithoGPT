# Note added 21 November 2026, before any confirmatory result was opened

On 20 November 2026 another AI agent, working for the author on a different question, scored
simple lookup rules on the 20 official FORCE 2020 test wells (the 10 open and the 10 blind wells
used as confirmatory wells here). It used only their rock labels (FORCE_2020_LITHOFACIES_LITHOLOGY),
well names, depths and formation names. It used no log curves and no model. Its rules were: the
most common training rock for each formation name, and the most common training rock 10 m and
100 m deeper, from the formation name with and without the current rock. The numbers it showed
were 59.6, 64.2, 62.7, 73.5, 60.3 and 63.1 (as reported by the author; not recomputed for this note).

Script: /Users/ammar/Documents/Codex/2026-11-20/you-are-an-independent-thinking-partner/outputs/check_norwegian_wells.py
(file created 2026-11-20 15:21:03 UTC, last changed 15:21:24 UTC). That agent downloaded its own
copies of the competition files from the FORCE GitHub repository between 15:11 and 15:24 UTC on
20 November. The copies used by this study (downloaded by c06_prepare_confirmatory.py) were last
read on 19 November at 10:15 UTC, so they were not used.

Timing, all UTC:
- Protocol frozen: commit 9ac65572dc7d89541637e0bfd639dd4419297c92, pushed 2026-11-18 23:31:02.
- Author's rulings (CLARIFICATIONS.md): commit 937b50849dfce619b1f50c876a9bcc03651f942d, pushed 2026-11-19 10:13:58.
- Confirmatory wells first downloaded: 2026-11-19 10:14:50.
- Run launched (the launch that produced the results): driver started 2026-11-19 11:29:25.
- The lookup scoring above: 2026-11-20, about 15:11 to 15:24.
- Run finished: 2026-11-20 23:29:43.

So the lookup scoring happened after the protocol freeze, after the rulings and after the run
launch, while the run was generating its secondary (step-3,000) results. The pipeline, its
settings and the models were fixed before it and did not change. No confirmatory result of this
study had been opened, scored by hand or summarised when it happened, or when this note was written.
