# DQ Gate 4 — G4 MANUSCRIPT

## Blocker: no rev3 draft exists

Searched `/Users/ammar/LithoGPT_archive/LithoGPT-2` (full repo, all branches via `git grep`),
`~/LithoGPT_archive`, and `~/Documents/Codex` for any manuscript draft (by content match on the
ruled title and by filename). None found. The `~/Documents/Codex/.../outputs/ATCE_V1_5_*` files
are audit/analysis packet outputs (JSON/CSV/py), not a manuscript draft with prose sections.

Per governing rule ("never fabricate... write NOT PRESENT and continue"), `manuscript/manuscript.md`
therefore contains **only** the sections G4 explicitly specifies content for: Abstract (folded
into the title matter — see note below), Results (confirmatory + descriptive subsections),
Discussion (with the future-work paragraph), Conclusions, Limitations (11 items), the
corrections-to-v1 paragraph, and Code Availability. Introduction, Methods/Protocol, and Related
Work are written as explicit `NOT PRESENT` stubs with a build note at the top of the file,
rather than invented. This is flagged as the second-largest outstanding item after the G3
figure-image gap.

**Correction to my own build, recorded not absorbed**: the first draft of this gate omitted a
separate Abstract section — a miss against the explicit instruction ("Write Results, Discussion,
Conclusions, and Abstract"). Caught on self-review before the gate closed; an Abstract section
was added to `manuscript.template.md` (summarizing the four primary comparisons, the two
unplanned-finding highlights, and the oracle sentence) and the manuscript was rebuilt. Final
token count 92 (was 89), 0 missing, 0 banned-string hits, word count 3,139 (was 2,883).

## What was built

- `manuscript/manuscript.template.md` — the source template, `{{key}}` / `{{key:fmt}}` tokens
  only, no hand-typed numbers in any of the drafted sections.
- `analysis/fill.py manuscript/manuscript.template.md` → `manuscript/manuscript.md`: 92 tokens
  substituted, 0 missing, 0 format errors.
- Banned-string scan (`—`, `–`, and every string in section 4) against the rendered
  `manuscript.md`: 0 hits after one fix (an initial draft used "pre-registered" in the future-work
  paragraph; corrected to "declared in advance").
- Required forms used: "the paired 95 percent bootstrap interval excluded zero" (B-linear minus
  B-abs, C minus A); "no detectable correction at this precision" with MDE beside it (B2 minus
  A, B-abs minus A); "one realized fit per arm" (Results methods line, training-loss paragraph,
  Limitations item 2); B-linear framed as a feature-design mismatch, never called a defect; every
  contrast row labelled "X minus Y".
- Arm D appears exactly once, in Limitations, documenting its withdrawal; never used as
  supporting evidence anywhere (checked by `grep -n "Arm D" manuscript/manuscript.md`, single
  hit).
- Word count: 3,139 words (well under the 6,500 target / 6,800 ceiling — expected, since three
  of seven planned sections are NOT PRESENT rather than drafted; the 3.6 cut order was not
  triggered).
- Ruled title used verbatim as the document's H1.

G4 STATUS: **PARTIAL.** Abstract, Results, Discussion, Conclusions, Limitations, corrections
note, and Code Availability all drafted, pass the banned-string and required-form checks.
Missing: Introduction, Methods/Protocol, Related Work (all NOT PRESENT, rev3 not found — the
largest outstanding item together with the G3 figure images). Continuing to G5.
