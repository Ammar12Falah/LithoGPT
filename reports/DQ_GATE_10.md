# DQ Gate 10 — G10 LOCATE OR REPLACE THE EARLIER DRAFT

## a. What was searched

- `git branch -a` (local-audit-env-pins-2026-07-29, main, origin/HEAD, origin/main,
  origin/checkpoints) — no manuscript content on any branch by filename or by
  `git grep` for the ruled title / "single-basin ablation" (origin/checkpoints checked
  explicitly: an unrelated old NLOG-ingest checkpoint branch, 238 files different from
  main, zero manuscript-related content).
- `git stash list` — empty.
- `git fsck --unreachable --no-reflogs` — no dangling commits.
- `git reflog --all` — only this session's and prior sessions' ordinary commits/checkout/clone
  events, nothing pointing at lost work.
- "the original LithoGPT repository if present on disk" — no separate v1 code repository was
  found; `/Users/ammar/Downloads/Docs/LithoGPT.pdf` (modified 2026-07-20, i.e. before the
  ablation's own results existed) was found and read (raw PDF stream extraction, no `pdftotext`
  available and none installed, per no-installs outside G8's matplotlib exception) — it is the
  **v1 single-model paper** ("LithoGPT: Discrete Representation Learning for Stochastic
  Stratigraphic Modeling", dated 15 Jan 2026) that this whole project's corrections note is
  about, not a draft of the 5-arm ablation manuscript. Not used as source text (different study,
  predates the ablation), only confirms context already known.
- Whole-home-directory search: `find` for `*.md *.tex *.docx *.odt *.pdf *.txt` modified since
  2026-06-01, outside `~/Library` and `~/.Trash` — 2,356 candidates. Filtered by content match
  on the ruled title text, "B-linear minus B-abs", "single-basin ablation", and "Arm B2" (grep
  -l across all candidates).

## b. Found

**`/Users/ammar/.codex/attachments/ea7dcacd-3e84-4bc0-81b0-48a94dafe5b9/pasted-text.txt`**,
modified 2026-07-29 13:35 (i.e. before this DQ/DR session's own work today), 35,967 bytes.
Header: `# Depth Conditioning Does Not Correct Porosity Bias in Discrete Autoregressive Well-Log
Generation: A Pre-Specified Ablation` / `Results-independent sections, revision 2. Drafted 29
July 2026 for SPE ATCE 2026.` It contains full Introduction, Related Work, Data, Method
(tokenization/backbone/conditioning arms/training/generation), and Experimental Protocol
sections, plus its own Limitations, Code/Data Availability, Acknowledgements, and References —
i.e. essentially the "rev3" this brief describes, produced by a parallel tool session (path
under `~/.codex/`, a different assistant's attachment store, not this repo). Confirmed unique
(no other file under any searched location matches the title text or contains a second `#
Depth Conditioning` header).

**Numeric cross-check against `analysis/FROZEN_RESULTS.json` / DQ section 1** (spot-checked,
not exhaustively): 80/10/8 well split, 72,064 full-valid samples, 54,051 scored samples,
1,295.6–3,897.3 m scored depth range, real NPHI mean 0.328089 (eqw), tokenizer 1000/1000
clusters, entropy 9.800, RMSE (GR/RDEP/NPHI/RHOB) 3.928/9.309/0.0136/0.0254, reconstruction
bias +0.000487 (eqw), Athy phi0 0.6052 / lambda 4068.0 m / train-only 4375.8 m / shift 307.8 m /
max feature shift 0.0267, final training losses 1.4262/1.4213/1.4331/1.3520, params 5,383,144
— **every one matches exactly.** This is strong evidence the draft is genuine, contemporaneous
project output, not a mismatched or fabricated document.

**Two problems found in the draft, both corrected before use, per this brief's own rules:**
1. It uses "pre-specified" extensively (banned string, section 4) and "pre-registered" once
   (also banned) in the same sentence contrasting the two. Every instance is edited out below.
2. It frames the single-fit-per-arm limitation as "one training seed per arm" / "a single seed"
   throughout — **this is exactly the error Plan's error-list item 19 (added in
   `LITHOGPT2_PLAN_HANDOFF_v2.0.md`, G7) describes**, since no `torch.manual_seed` call exists
   anywhere in the training code (DK task 4), so nothing was actually controlled by a "seed" at
   the weight-initialisation level. This draft is very likely the "earlier draft" item 19 was
   written to correct. Every instance is reworded to "one realized fit per arm" below, matching
   the required form already in the DQ section 4 language rules.
3. It cites 15 references, of which only one (Koeshidayatullah, Al-Fakih and Kaka 2024,
   arXiv:2412.05681) is in `audit/references_check.txt`. Per this brief ("every citation must
   already be in audit/references_check.txt... cite nothing unresolved") and because no network
   gate is open in G10 (only G5 had network permission, already closed), the other 14 are NOT
   cited by name/year in the sections built below — described generically without formal
   attribution where the point being made still stands without a citation, or dropped where it
   does not. Full list of removed citations in the Related Work sub-report below.

## c. Sections written (using the found draft as source, edited per (b) above)

Introduction, Related Work, Protocol, and Experimental Family were all built FROM this found
draft (not written fresh from FROZEN_RESULTS.json alone, since something was found) — condensed
and edited per the constraints above. Full accounting of edits and word counts in
`reports/DQ_GATE_10_sections.md`.

G10 STATUS: draft located and used (not "nothing found"). Continuing with section assembly.
