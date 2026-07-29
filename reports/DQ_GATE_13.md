# Brief DT — G15 PREPARE FOR THE ORIGINAL REPO (local only, no push in this gate)

## a. File inventory / size limit

`git ls-files` over the current branch, largest first: largest tracked file is
`reports/basinshift/phaseB/frozen_adapted_pretrained_A.json.gz` at 39,168,241 bytes. **No
tracked file exceeds the 90MB / 90×1024×1024=94,371,840-byte threshold.** The 149,074,228-byte
`atce_ablation_v3_raw_results_2026-07-26.json` the brief expected to need excluding was never
tracked in this repository in the first place (confirmed: `find . -iname
atce_ablation_v3_raw_results_2026-07-26.json` inside the repo returns nothing; commit
`ef8883e`'s own message states it was excluded from the very first commit for exceeding
GitHub's 100MB limit). So there is nothing to actively remove — but the safety net and
documentation the brief asks for were still built, since a future session could otherwise copy
the file in and accidentally commit it.

## b. Exclusion + documentation

- `.gitignore`: added an entry for the exact filename `atce_ablation_v3_raw_results_2026-07-26.json`
  (not a Git-LFS pointer, not compressed/split — the brief explicitly forbids all three).
- `analysis/RAW_OUTPUTS_LOCATION.md`: records the filename, byte size (149,074,228),
  sha256 (`ac963f2c56ec27ac8f2fd837faa90108dc580a53560dbeb3c50a41c35f0110ed`), that it is
  deposited to Zenodo rather than GitHub, and the integrity chain (recomputed locally, matches
  the git-committed sidecar).

## c. Code-availability paragraph rewritten

`manuscript/manuscript.template.md`'s Code Availability section now names
`github.com/Ammar12Falah/LithoGPT` (the destination repo). The commit hash is left as the
literal text "commit hash to be inserted after push" (not invented — mirrors the existing "DOI
to be inserted on deposit" pattern already used for the Zenodo slot) until G16 actually creates
one. States raw outputs are in the Zenodo deposit. Still claims ONLY that the archived raw
outputs reproduce every arm-level metric; still does not claim pipeline reproducibility.

## d. Secrets grep

```
git grep -nIE "ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|
  -----BEGIN [A-Z ]*PRIVATE KEY-----|xox[baprs]-[0-9A-Za-z-]{10,}|AIza[0-9A-Za-z_-]{35}" -- .
```
Zero hits (exit 1, no match). No `.env` file is tracked. Two filenames contain "token" but are
about the ML tokenizer (`fsq_tokenizer.py`, a tokenizer-validation decision doc) — false-positive
name matches, confirmed by content, not credentials.

## e. RunPod / pod-ID / /workspace paths

Pervasive: 51 tracked files across the whole (pre-existing) codebase reference `/workspace`,
almost all of them ingestion/basinshift tooling unrelated to this manuscript, predating this
audit sequence (DK-DT) entirely. Fixing all 51 was judged out of proportion and out of scope —
none of them are referenced by this manuscript's Code Availability, and rewriting absolute-path
defaults across dozens of unfamiliar scripts risks introducing real bugs for no benefit to this
manuscript. **Fixed the 4 that ARE Code Availability's actual subject** (`scripts/atce/
atce_ablation.py`, `atce_ablation_v2.py`, `atce_ablation_v3.py`, `atce_v3_recompute.py`): each
had `ROOT = Path("/workspace/LithoGPT-2")` hardcoded; changed to
`Path(os.environ.get("LITHOGPT2_ROOT", Path(__file__).resolve().parents[2]))`, so a fresh clone
resolves ROOT to its own checkout by default while `LITHOGPT2_ROOT` still reproduces the
original pod layout exactly if set. `atce_ablation_v3.py`'s `V1_CKPT_DIR` (pointing at the v1
model checkpoint) was deliberately NOT changed and instead commented: the checkpoint it names is
permanently unrecoverable (per the corrections note), so no path would make it resolve to
anything real — rewriting it would misleadingly imply the data exists somewhere. All 4 edited
files compile (`python3 -m py_compile`, confirmed). Historical provenance (run_log.txt files,
decision docs, this session's own gate reports) left untouched, per "do not delete provenance
notes." Two harmless `runpod.io/pricing` citation URLs (a public pricing page, no pod ID or
credential) left as-is.

## Reaudit after these changes

```
AUDIT: ALL CHECKS PASSED.
```
(byte-identical rebuild, 0 banned strings, 0 unresolved citations, Arm D once, no superseded
interval cited). Body word count now 6,663 (163 over the 6,500 target, still 137 under the
6,800 ceiling) — grew slightly from the Code Availability rewrite; not trimmed further, per the
brief's own "acceptable if the total stays under the ceiling" allowance.

**G15 STATUS: COMPLETE.** Nothing has been pushed anywhere. G16 (the actual push to
`github.com/Ammar12Falah/LithoGPT`) is paused pending explicit confirmation from the user in
this conversation — publishing to a public, credentialed destination is not something this
session will do on brief-text authorization alone. See the chat reply for what's needed to
proceed.
