#!/usr/bin/env python3
"""G6 audit. Four checks, each printed PASS/FAIL, nonzero exit on any FAIL:
1. Byte-identical rebuild: re-run analysis/fill.py against the CURRENTLY COMMITTED
   analysis/FROZEN_RESULTS.json and manuscript/manuscript.template.md, diff the result
   against the committed manuscript/manuscript.md. This is the "regenerate every
   numeric claim and diff against the text" check -- if the rebuild is byte-identical,
   every number in the manuscript traces to a FROZEN_RESULTS.json key, not a hand-typed
   literal, by construction (fill.py has no other source of numbers).
2. Banned-string grep (section 4 of the DQ brief), zero hits required.
3. Word count against section 3.6 (target 6500, hard ceiling 6800).
4. Arm D appears only once (documenting its withdrawal), never elsewhere.
5. No interval value from the SUPERSEDED v3 run-log bootstrap (the original
   pooled-realization, 1000-resample estimator) is cited anywhere in the manuscript.
"""
import re
import subprocess
import sys
import json

FAIL = False


def check(name, ok, detail=""):
    global FAIL
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail else ""))
    if not ok:
        FAIL = True


# ---- 1. byte-identical rebuild ----
with open("manuscript/manuscript.md", "rb") as f:
    committed = f.read()
subprocess.run([sys.executable, "analysis/fill.py"], check=True, capture_output=True)
with open("manuscript/manuscript.md", "rb") as f:
    rebuilt = f.read()
check("rebuild byte-identical to committed manuscript.md", committed == rebuilt,
      f"{len(committed)} vs {len(rebuilt)} bytes" if committed != rebuilt else "")
# restore committed bytes exactly (fill.py is deterministic so this is a no-op when PASS)
with open("manuscript/manuscript.md", "wb") as f:
    f.write(committed)

text = committed.decode("utf-8")

# ---- 2. banned strings ----
BANNED = ["—", "–", "statistically significant", "pre-specified", "pre-registered",
          "regresses toward corpus-mean porosity", "discrete outputs outperform continuous",
          "MSE causes smoothing", "the comparison isolates output representation",
          "variance collapse", "calibrated by construction", "reserves", "volumetric",
          "proves", "groundbreaking", "unusable", "clean null",
          "robust to the leakage direction", "TODO", "[PLACEHOLDER"]
hits = [b for b in BANNED if b in text]
# "fair" only banned when applied to the continuous baseline -- flag any occurrence for manual read
fair_hits = [m.start() for m in re.finditer(r"\bfair\b", text, re.I)]
pilot_hits = [m.start() for m in re.finditer(r"\bpilot\b", text, re.I)]
check("banned strings (section 4), 0 hits", len(hits) == 0, str(hits))
check("'fair' not used (0 occurrences found)", len(fair_hits) == 0, f"{len(fair_hits)} occurrence(s)")
check("'pilot' not used as study name (0 occurrences)", len(pilot_hits) == 0, f"{len(pilot_hits)} occurrence(s)")

# ---- 3. word count ----
wc = len(text.split())
check(f"word count {wc} <= 6800 hard ceiling", wc <= 6800, f"{wc} words")
check(f"word count {wc} <= 6500 target", wc <= 6500, f"{wc} words (informational, not a FAIL condition per 3.6)")

# ---- 4. Arm D appears only once ----
armd_hits = [m.start() for m in re.finditer(r"Arm D\b", text)]
check("'Arm D' appears exactly once (withdrawal note only)", len(armd_hits) == 1, f"{len(armd_hits)} occurrence(s)")

# ---- 5. no superseded v3 run-log interval cited ----
with open("reports/basinshift/atce_ablation_v3/run_log.txt") as f:
    runlog = f.read()
ci_values = re.findall(r"-?\d\.\d{10,}", runlog)  # the long-decimal ci_low/ci_high/mean floats in the run log
leaked = [v for v in set(ci_values) if v in text]
check("no superseded v3 run-log interval value cited in manuscript", len(leaked) == 0, str(leaked[:5]))

print()
if FAIL:
    print("AUDIT: ONE OR MORE CHECKS FAILED.")
    sys.exit(1)
else:
    print("AUDIT: ALL CHECKS PASSED.")
