# DQ Gate 11 — G11 REAUDIT AND CLOSE

`audit/verify_all.py` extended with one new check for this gate (5b: every in-text citation-
shaped parenthetical must contain a surname from `audit/references_check.txt`'s resolved set —
added because G10 introduced the manuscript's first real citations). The word-count check was
also fixed: it previously flipped the overall exit code on missing the 6,500 *target*, contrary
to its own printed "informational, not a FAIL condition" claim; it's now a soft `[INFO]` line
that never fails the run, while the 6,800 *ceiling* remains a hard `[PASS]`/`[FAIL]`.

```
[PASS] rebuild byte-identical to committed manuscript.md
[PASS] banned strings (section 4), 0 hits -- []
[PASS] 'fair' not used (0 occurrences found) -- 0 occurrence(s)
[PASS] 'pilot' not used as study name (0 occurrences) -- 0 occurrence(s)
[PASS] word count 6515 <= 6800 hard ceiling -- 6515 words
[INFO] word count 6515 <= 6500 target -- 6515 words over target by 15 (soft target per 3.6, not a hard-ceiling FAIL)
[PASS] 'Arm D' appears exactly once (withdrawal note only) -- 1 occurrence(s)
[PASS] every in-text citation matches a resolved reference (audit/references_check.txt) -- set()
       (3 citation-shaped parenthetical(s) found: ['Koeshidayatullah, Al-Fakih and Kaka 2024',
       'Koeshidayatullah, Al-Fakih and Kaka 2024', 'Bormann, Aursand, Dilib, Dischington and
       Manral 2020'])
[PASS] no superseded v3 run-log interval value cited in manuscript -- []

AUDIT: ALL CHECKS PASSED.
```
Full output: `audit/verify_all_output.txt`.

## a. Rerun, zero mismatches

Byte-identical template rebuild passes: every number added in G10 (372 `FROZEN_RESULTS.json`
keys total, 44 added this gate) traces to a token, none hand-typed.

## b. Banned-string / dash grep

Zero hits across the whole rendered manuscript, including the four new sections. Two dash
characters were introduced while drafting the G10 sections (one em dash in an internal
source-note comment, one en dash in a numeric range) — both caught by this same check during
drafting and fixed before this gate's official run; see `reports/DQ_GATE_10_sections.md`.

## c. Word count

6,515 words. 15 over the 6,500 target, 285 under the 6,800 hard ceiling. One trim was applied
to Protocol (the first item in the 3.6 cut order) before accepting the remainder; further
cutting was judged not worth the content risk for a 15-word margin against a soft target,
especially since the next two items in the cut order (tokenizer audit arithmetic, Related Work)
carry disclosures this project has repeatedly found load-bearing (the reconstruction-bias audit
and depth-correlation numbers in particular). Limitations, the corrections note, and the
estimator disclosure were never touched, per the protected list.

## d. Arm D and run-log-interval checks

Arm D appears exactly once, in Limitations, documenting withdrawal (unchanged from G6 — the new
G10 sections describe the excluded trend-residual arm generically, never by the letter D, so
the count did not change). No value from the superseded v3 run-log bootstrap is cited anywhere.

## e. Handoff doc

Rewritten: `reports/LITHOGPT2_PLAN_HANDOFF_v2.0.md`, reflecting the finished state (draft found
and used, figures rendered, plot venv pinned), next brief letter **DS**.

G11 STATUS: COMPLETE. Continuing to commit.
