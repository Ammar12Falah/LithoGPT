#!/usr/bin/env bash
# Kansas Geological Survey statewide bulk files and the pages that document them.
# Official KGS hosts only. Raw files go to raw/kansas/ (not in git).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p raw/kansas && cd raw/kansas
get() { curl -sS -L --fail -o "$1" "$2"; echo "$1"; }
get ks_wells.zip   https://www.kgs.ku.edu/PRS/Ora_Archive/ks_wells.zip
get ks_tops.zip    https://www.kgs.ku.edu/PRS/Ora_Archive/ks_tops.zip
get OG_Column_Definitions.xlsx https://www.kgs.ku.edu/PRS/OG_Column_Definitions.xlsx
get petroDB.html   https://www.kgs.ku.edu/PRS/petroDB.html
get file_format.html https://www.kgs.ku.edu/PRS/file_format.html
get status.html    https://www.kgs.ku.edu/Magellan/Elog/status.html
get ogwell_fgdc.html https://www.kgs.ku.edu/Magellan/Qualified/ogwell_fgdc.html
get copyright.html https://www.kgs.ku.edu/General/copyright.html
get HorizWells.html "https://chasm.kgs.ku.edu/ords/qualified.ogw5.HorizWells"
get kgs_home.html  https://kgs.ku.edu/
get dataLib.html   https://www.kgs.ku.edu/General/dataLib.html
