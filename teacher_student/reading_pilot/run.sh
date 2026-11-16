#!/bin/sh
# One command for the number work: learning curve, plain models, and scoring from the saved readings.
# The readings in readings/ are frozen and are not made again here (they were read by Claude).
# Needs: python3, curl. Takes about 15 to 30 minutes on 4 cores.
set -e
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt; }
PY=".venv/bin/python -I"
sh download.sh
$PY src/a1_draw.py > /dev/null && rm -f draw_order_only.csv   # held-out check and draw only; draw.csv with the roles stays as committed
$PY src/a1_split.py
$PY src/a2_model.py curve
$PY src/a2_report.py
$PY src/a2_model.py fixed
$PY src/combine.py "31/3-1" "30/6-5" "35/11-13" "35/11-11" "25/6-2"
$PY src/score.py
$PY src/sheets.py check || true        # needs the reading pictures in work/, skipped if they are absent
$PY src/sheets.py conflicts || true
$PY src/make_report.py
$PY src/make_manifest.py
echo "done: see scores/, curve/, conflicts/"
