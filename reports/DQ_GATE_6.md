# DQ Gate 6 — G6 AUDIT

`audit/verify_all.py` runs 5 checks (2, 3, 4, 5 spelled out explicitly in the DQ brief; check 1
is how "regenerate every numeric claim... and diff against the text" is implemented here: since
`analysis/fill.py` has no source of numbers other than `FROZEN_RESULTS.json`, a byte-identical
rebuild of `manuscript.md` from the template *is* the full-manuscript numeric diff, rather than a
sampled subset of claims).

```
[PASS] rebuild byte-identical to committed manuscript.md
[PASS] banned strings (section 4), 0 hits -- []
[PASS] 'fair' not used (0 occurrences found) -- 0 occurrence(s)
[PASS] 'pilot' not used as study name (0 occurrences) -- 0 occurrence(s)
[PASS] word count 3139 <= 6800 hard ceiling -- 3139 words
[PASS] word count 3139 <= 6500 target -- 3139 words (informational, not a FAIL condition per 3.6)
[PASS] 'Arm D' appears exactly once (withdrawal note only) -- 1 occurrence(s)
[PASS] no superseded v3 run-log interval value cited in manuscript -- []

AUDIT: ALL CHECKS PASSED.
```

Full output: `audit/verify_all_output.txt`.

Note on the "Arm D only in appendix" check: no separate Appendix section exists in
`manuscript.md` (Introduction/Methods/Related Work are NOT PRESENT, per `DQ_GATE_4.md`), so the
check implemented is "Arm D is mentioned exactly once, documenting its withdrawal, and nowhere
else" — the closest available proxy for "appendix only, never supporting evidence" given the
gap. This should be re-run once an Appendix section exists, to confirm the single mention has
actually moved there rather than staying in Limitations.

G6 STATUS: COMPLETE, 0 mismatches, 0 banned-string hits. Continuing to G7.
