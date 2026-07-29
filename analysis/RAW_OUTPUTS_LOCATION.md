# Raw generation outputs: location and integrity

The sealed v3 ablation's raw per-realization generation outputs are **not** in this git
repository, under any branch, at any commit — they exceed GitHub's 100MB hard limit and this
repository's own 90MB publish threshold (brief DT, G15a). This was true from the first result
commit onward (`ef8883e`'s own message states this file was excluded for size reasons) and
remains true for the audit branch built in briefs DK through DT.

- **Filename:** `atce_ablation_v3_raw_results_2026-07-26.json`
- **Byte size:** 149,074,228 bytes (149.07 MB decimal / 142.16 MiB binary)
- **SHA-256:** `ac963f2c56ec27ac8f2fd837faa90108dc580a53560dbeb3c50a41c35f0110ed`
- **Where it lives:** deposited to Zenodo (see Code Availability in `manuscript/manuscript.md`
  for the deposit reference once inserted; DOI to be inserted on deposit — not yet minted as of
  this writing, per brief DT G15c: "do not invent a DOI").
- **Integrity verification:** the sha256 above was independently recomputed from a local copy
  of the file (`/Users/ammar/LithoGPT_archive/atce_ablation_v3_raw_results_2026-07-26.json`,
  outside this repo) and confirmed to match the sidecar file committed alongside the sealed
  results (`reports/basinshift/atce_ablation_v3/atce_ablation_v3_raw_results_2026-07-26.sha256`)
  byte-for-byte — see `reports/dl_brief_2026-07-29/dl_q2_walltime_artifact.txt` for the original
  verification.
- **What every arm-level metric in this repository's analysis was computed from:** this exact
  file, identified unambiguously by the digest above. Anyone who obtains a copy of the file with
  a matching sha256 can independently regenerate every arm-level number in
  `analysis/FROZEN_RESULTS.json` from it directly (see `analysis/build_frozen_results.py`); this
  is the claim Code Availability makes, and no stronger one.
- **`.gitignore`:** an entry for this exact filename was added (see `.gitignore`) so that a
  future accidental `git add` of a local copy inside this repo does not silently commit a
  149MB blob.
