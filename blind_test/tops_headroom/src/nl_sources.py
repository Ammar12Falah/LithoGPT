"""Sources of the Dutch downloads, for manifest.csv."""
SOURCES = {
    "netherlands/thematische_data_boringen.zip": (
        "https://www.nlog.nl/sites/default/files/2026-09/thematische_data_boringen.zip",
        "https://www.nlog.nl/en/boreholes (Combined data selections by type: Thematic borehole data; files dated 23 Sep 2026)"),
    "netherlands/NLOG_Boreholes_ED50UTM31N.json": (
        "https://www.gdngeoservices.nl/geoserver/nlog/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=nlog:gdw_ng_wll_all_utm&outputFormat=json&srs_name=epsg:23031",
        "https://www.nlog.nl/en/files-interactive-map (All boreholes, GeoJSON link; served by www.gdngeoservices.nl, host approved by Ammar on 13 Nov 2026)"),
    "netherlands/pages/home_en.html": ("https://www.nlog.nl/en", "NLOG home page, read to find downloads"),
    "netherlands/pages/boreholes.html": ("https://www.nlog.nl/en/boreholes", "NLOG boreholes page (lists the bulk downloads)"),
    "netherlands/pages/data.html": ("https://www.nlog.nl/en/data", "NLOG data page (confidentiality periods)"),
    "netherlands/pages/disclaimer.html": ("https://www.nlog.nl/en/disclaimer", "NLOG disclaimer (reuse terms)"),
    "netherlands/pages/files-interactive-map.html": ("https://www.nlog.nl/en/files-interactive-map", "NLOG page that links the All boreholes file"),
    "netherlands/pages/models-maps-and-datasets.html": ("https://www.nlog.nl/en/models-maps-and-datasets", "NLOG page, read to find downloads"),
    "netherlands/pages/boringen_nl.html": ("https://www.nlog.nl/boringen", "NLOG boreholes page, Dutch, read to find downloads"),
    "netherlands/pages/bestanden_nl.html": ("https://www.nlog.nl/bestanden-interactieve-kaart", "NLOG files page, Dutch, read to find downloads"),
    "netherlands/pages/brh-overview.html": ("https://www.nlog.nl/datacenter/brh-overview", "NLOG datacenter page (app shell only; no data taken from it)"),
    "netherlands/pages/dc_main.js": ("https://www.nlog.nl/datacenter/main-BV4YAAOX.js", "NLOG datacenter script, read to see how its export works; not used"),
}
