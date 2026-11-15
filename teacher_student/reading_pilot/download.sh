#!/bin/sh
# Downloads the allowed FORCE files and the FactPages documents table (single files, no cloning).
# Never downloads hidden_test.csv, leaderboard_test_*.csv or anything in las_files_Lithostrat_data.
set -e
cd "$(dirname "$0")"
mkdir -p raw/force raw/factpages
base=https://raw.githubusercontent.com/bolgebrygg/Force-2020-Machine-Learning-competition/master/lithology_competition/data
for f in train.zip penalty_matrix.npy starter_notebook.ipynb; do
  [ -s "raw/force/$f" ] || curl -sS -L --fail -o "raw/force/$f" "$base/$f"
done
[ -s raw/factpages/wellbore_document.csv ] || curl -sS -L --fail -o raw/factpages/wellbore_document.csv \
  "https://factpages.sodir.no/public?/Factpages/external/tableview/wellbore_document&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&IpAddress=not_used&CultureCode=en&rs:Format=CSV&Top100=false"
echo "downloads present"
