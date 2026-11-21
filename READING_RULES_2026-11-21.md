# How the results will be read

Added on 21 November 2026, after the run finished and before any confirmatory result was opened.
This note is not part of the frozen protocol (PROTOCOL_confirmatory_test.md, commit
9ac65572dc7d89541637e0bfd639dd4419297c92), and it does not change it or CLARIFICATIONS.md.
The hashes of the result files were made public at 11:43:18 UTC on 21 November 2026, in commit
e2acd0e1423d857b6efe97e2002e062eab345827 (run_record/run_folder_2026-11-21.sha256), before this note.

1. Direction. Each comparison is the first-named minus the second-named: B2 minus A, A minus tuned
   chain, A minus trigram, A minus block resampling. For absolute NPHI bias and for the structure
   score, lower is better. So a negative difference favours the first-named.

2. What is reported. Each comparison is reported as its estimate and its 95% interval, computed as the
   frozen protocol (section 9) and CLARIFICATIONS.md Q31 say. The only wording used is "the interval
   excluded zero" or "the interval included zero". No other test is run. No minimum effect size is set.

3. Four comparisons. There is no adjustment for having four comparisons. The paper will say that with
   four unadjusted 95% intervals, the chance that at least one excludes zero by chance alone can
   approach 20%.

4. Order and scope. All four comparisons appear in the abstract and in the results, in the protocol's
   order. None is promoted, dropped or renamed after opening. The governing results are the confirmatory
   wells at the lowest-development-loss checkpoint. Step-3000 results and pilot wells are secondary and
   never replace them.
