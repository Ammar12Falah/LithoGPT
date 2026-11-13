#!/usr/bin/env bash
# One command: cleaned input tables (data/) -> all results (results/), the
# date-rule test and hashes.txt. Needs the virtual environment:
#   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
set -euo pipefail
cd "$(dirname "$0")"
exec .venv/bin/python -I src/run.py "$@"
