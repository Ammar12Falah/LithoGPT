"""Write manifest.csv: every downloaded file with source page, date, size and
sha256. Run after the downloads (download_*.sh). Raw files stay out of git."""
import csv
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"

# file -> (url it was downloaded from, page that links to it / what it is)
SOURCES = {
    "kansas/ks_wells.zip": ("https://www.kgs.ku.edu/PRS/Ora_Archive/ks_wells.zip",
                            "https://www.kgs.ku.edu/PRS/petroDB.html (All Wells, statewide, file dated October 9, 2026)"),
    "kansas/ks_tops.zip": ("https://www.kgs.ku.edu/PRS/Ora_Archive/ks_tops.zip",
                           "https://www.kgs.ku.edu/PRS/petroDB.html (All Tops, statewide, file dated October 9, 2026)"),
    "kansas/OG_Column_Definitions.xlsx": ("https://www.kgs.ku.edu/PRS/OG_Column_Definitions.xlsx",
                                          "https://www.kgs.ku.edu/PRS/petroDB.html (column definitions)"),
    "kansas/petroDB.html": ("https://www.kgs.ku.edu/PRS/petroDB.html", "KGS oil and gas database page (lists the downloads)"),
    "kansas/file_format.html": ("https://www.kgs.ku.edu/PRS/file_format.html", "KGS format of the well file"),
    "kansas/status.html": ("https://www.kgs.ku.edu/Magellan/Elog/status.html", "KGS well status codes"),
    "kansas/ogwell_fgdc.html": ("https://www.kgs.ku.edu/Magellan/Qualified/ogwell_fgdc.html", "KGS metadata of the well database"),
    "kansas/copyright.html": ("https://www.kgs.ku.edu/General/copyright.html", "KGS terms of use"),
    "kansas/HorizWells.html": ("https://chasm.kgs.ku.edu/ords/qualified.ogw5.HorizWells",
                               "KGS horizontal-well list, first page only: read for the rule the KGS uses to mark horizontal wells"),
    "kansas/kgs_home.html": ("https://kgs.ku.edu/", "KGS home page (looked for terms of use)"),
    "kansas/dataLib.html": ("https://www.kgs.ku.edu/General/dataLib.html", "KGS data resources library page (looked for terms of use)"),
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def main():
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from nl_sources import SOURCES as NL
        SOURCES.update(NL)
    except ImportError:
        pass
    rows = []
    for p in sorted(RAW.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(RAW).as_posix()
        url, page = SOURCES.get(rel, ("", ""))
        day = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
        rows.append(dict(file=rel, url=url, source_page=page, date_downloaded_utc=day,
                         size_bytes=p.stat().st_size, sha256=sha256(p)))
    with open(ROOT / "manifest.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    missing = [r["file"] for r in rows if not r["url"]]
    print(len(rows), "files;", "no source recorded for:", missing)


if __name__ == "__main__":
    main()
