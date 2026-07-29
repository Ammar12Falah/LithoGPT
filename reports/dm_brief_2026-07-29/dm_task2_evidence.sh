#!/bin/bash
# DM Task 2: read-only evidence gathering. All commands as actually run.
set -e
cd "$(dirname "$0")/../.."

echo "===================================================================================================="
echo "TASK 2a. FILES WHOSE NAME CONTAINS atce_ablation"
echo "===================================================================================================="
git ls-files | grep -i "atce_ablation" > /tmp/atce_files.txt
while IFS= read -r f; do
  echo "### $f ###"
  size=$(stat -f%z "$f")
  sha=$(shasum -a 256 "$f" | awk '{print $1}')
  lastcommit=$(git log -1 --format='%H %ci' -- "$f")
  echo "size=$size bytes"
  echo "sha256=$sha"
  echo "last_commit=$lastcommit"
  case "$f" in
    *.py)
      printf 'arm_labels(py, literal string tokens): '
      grep -oE '"(A|B-linear|B-abs|B2|B|C|D)"' "$f" | sort -u | paste -sd' ' -
      ;;
    *.json)
      printf 'arm_labels(json top-level keys): '
      python3 -c "import json; d=json.load(open('$f')); print(list(d.keys()) if isinstance(d,dict) else 'not a dict')"
      ;;
    *run_log.txt)
      printf 'arm_labels(run_log \"=== Arm X:\" headers): '
      grep -oE '=== Arm[A-Za-z0-9 -]*:' "$f" | paste -sd' ' -
      ;;
    *)
      echo "arm_labels: n/a (sidecar/env file, no arm content)"
      ;;
  esac
  echo
done < /tmp/atce_files.txt

echo "===================================================================================================="
echo "TASK 2b. DIFF: free-running generation loop, atce_ablation.py vs atce_ablation_v3.py"
echo "===================================================================================================="
echo "--- v1 lines 204-245 (generate_batch) ---"
sed -n '204,245p' scripts/atce/atce_ablation.py
echo
echo "--- v3 lines 255-297 (generate_batch) ---"
sed -n '255,297p' scripts/atce/atce_ablation_v3.py
echo
echo "--- unified diff ---"
sed -n '204,245p' scripts/atce/atce_ablation.py > /tmp/gen_v1.txt
sed -n '255,297p' scripts/atce/atce_ablation_v3.py > /tmp/gen_v3.txt
diff -u /tmp/gen_v1.txt /tmp/gen_v3.txt || true
echo
echo "-- N_REALIZATIONS / CONTEXT constants in both files --"
grep -n "^N_REALIZATIONS\|^CONTEXT " scripts/atce/atce_ablation.py scripts/atce/atce_ablation_v3.py

echo
echo "===================================================================================================="
echo "TASK 2c. PROVENANCE OF atce_ablation_v3_raw_results_2026-07-26.json"
echo "===================================================================================================="
echo "-- (1) the JSON's own metadata/provenance fields, checked first --"
python3 -c "
import json
with open('/Users/ammar/LithoGPT_archive/atce_ablation_v3_raw_results_2026-07-26.json') as f:
    d = json.load(f)
print('top-level keys:', list(d.keys()))
a = list(d.keys())[0]; w = list(d[a].keys())[0]
print('per-well keys (one example):', list(d[a][w].keys()))
print('NO provenance/source/script/generated_by field present at any level shown above.')
"
echo
echo "-- (2) commit history / source code, checked second --"
grep -n "raw_results_2026-07-26\|json.dump\|write_text" scripts/atce/atce_ablation_v3.py
echo
grep -n "WRITTEN.*raw_results" reports/basinshift/atce_ablation_v3/run_log.txt
echo
git log --format='%H %ci %s' -- scripts/atce/atce_ablation_v3.py

echo
echo "===================================================================================================="
echo "TASK 2d. reports/basinshift/atce_ablation/run_log.txt VERBATIM"
echo "===================================================================================================="
echo "path: reports/basinshift/atce_ablation/run_log.txt"
git log -1 --format='last_commit=%H %ci' -- reports/basinshift/atce_ablation/run_log.txt
echo "--- verbatim content ---"
cat -n reports/basinshift/atce_ablation/run_log.txt
echo
echo "arm headers found: $(grep -oE '=== Arm[A-Za-z0-9 -]*:' reports/basinshift/atce_ablation/run_log.txt | paste -sd' ' -)"

echo
echo "===================================================================================================="
echo "TASK 2e. WALL-CLOCK TIME FOR THE FIVE ARMS A, B-linear, B-abs, B2, C -- WHOLE-REPO SEARCH"
echo "===================================================================================================="
echo "-- search 1: literal string 'pilot' anywhere in tracked files --"
git grep -in "pilot" -- . || echo "NO MATCHES (git grep exit nonzero = no hits)"
echo
echo "-- search 2: which run_log files contain ALL FIVE literal arm-header labels A/B-linear/B-abs/B2/C --"
for f in reports/basinshift/atce_ablation/run_log.txt reports/basinshift/atce_ablation_v2/run_log.txt reports/basinshift/atce_ablation_v3/run_log.txt; do
  echo "  $f: $(grep -oE '=== Arm[A-Za-z0-9 -]*:' "$f" | paste -sd' ' -)"
done
echo
echo "-- v3 run_log per-arm training times (only file with all five requested labels) --"
grep -n "=== Arm\|trained 3000 steps\|TOTAL WALL TIME" reports/basinshift/atce_ablation_v3/run_log.txt

echo
echo "===================================================================================================="
echo "TASK 2f. reports/basinshift/ -- PILOT/ATCE SCOPE VS OUT-OF-SCOPE BasinShift"
echo "===================================================================================================="
ls -la reports/basinshift/
echo
echo "-- first-add commit for each top-level non-ATCE item (sample) --"
for f in reports/basinshift/run_log.txt reports/basinshift/baseline_results.json reports/basinshift/basinshift_test_manifest.json reports/basinshift/atce_sequence_counts_2026-07-25.json; do
  echo "  $f:"
  git log --diff-filter=A --format='    %H %ci %s' -- "$f" | tail -1
done
echo
echo "-- reports/basinshift/run_log.txt head (identifies it) --"
head -5 reports/basinshift/run_log.txt
