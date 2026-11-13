#!/usr/bin/env bash
# One command for the whole run. Needs the virtual environment:
#   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# Reads only blind_test/tops_headroom/data and results (first run, unchanged).
#   1. split of the development period (dates only)
#   2. stage 1: features, choices on the tuning half, final models, hashes
#   3. stage 2: the scoring half, with the frozen models
#   4. report tables and hashes.txt
set -euo pipefail
cd "$(dirname "$0")"
PY=".venv/bin/python -I"
$PY src/make_split.py
$PY src/train.py kansas netherlands
$PY src/score.py --final kansas netherlands
$PY src/report_tables.py
$PY src/build_report.py
