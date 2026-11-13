#!/usr/bin/env bash
# NLOG bulk files and the pages that document them. Raw files go to
# raw/netherlands/ (not in git). The borehole list is the "All boreholes" file
# that NLOG's page https://www.nlog.nl/en/files-interactive-map links to; it
# is served by www.gdngeoservices.nl.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p raw/netherlands/pages && cd raw/netherlands
get() { curl -sS -L --fail -o "$1" "$2"; echo "$1"; }
get thematische_data_boringen.zip https://www.nlog.nl/sites/default/files/2026-09/thematische_data_boringen.zip
get NLOG_Boreholes_ED50UTM31N.json "https://www.gdngeoservices.nl/geoserver/nlog/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=nlog:gdw_ng_wll_all_utm&outputFormat=json&srs_name=epsg:23031"
get pages/boreholes.html https://www.nlog.nl/en/boreholes
get pages/data.html https://www.nlog.nl/en/data
get pages/disclaimer.html https://www.nlog.nl/en/disclaimer
get pages/files-interactive-map.html https://www.nlog.nl/en/files-interactive-map
