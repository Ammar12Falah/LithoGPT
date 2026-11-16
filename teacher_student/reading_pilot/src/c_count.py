"""Part C: counts from listing files only (no document is opened here).
Norway: FactPages wellbore documents table.  Kansas: KGS ks_las_files.txt and ks_elog_scans.txt.
Netherlands: NLOG borehole listing (no listing of logs or documents exists there).
Usage: python -I src/c_count.py     writes work/partc_counts.json and work/partc_kansas_draw.csv
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from a1_roles import is_log, is_report  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261115
out = {}

# ---------------- Norway ----------------
d = pd.read_csv(ROOT / "raw" / "factpages" / "wellbore_document.csv", encoding="utf-8-sig")
d["log"] = [is_log(t, str(n)) for t, n in zip(d.wlbDocumentType, d.wlbDocumentName)]
d["rep"] = [is_report(t, str(n)) for t, n in zip(d.wlbDocumentType, d.wlbDocumentName)]
n = d.wlbDocumentName.astype(str).str.upper()
d["log_npd_plot"] = d.wlbDocumentType == "COMPOSITE LOG"
d["log_wdss"] = n.str.contains("WDSS") & d.log
d["log_licensee"] = d.log & ~d.log_npd_plot & ~d.log_wdss
g = d.groupby("wlbName")
has = g[["log", "rep", "log_npd_plot", "log_wdss", "log_licensee"]].any()
out["norway"] = {
    "rows_in_table": int(len(d)), "wellbores_in_table": int(d.wlbName.nunique()),
    "with_completion_log_A1_rule": int(has.log.sum()), "with_report_A1_rule": int(has.rep.sum()),
    "with_both_A1_rule": int((has.log & has.rep).sum()),
    "with_licensee_completion_log": int(has.log_licensee.sum()),
    "with_licensee_completion_log_and_report": int((has.log_licensee & has.rep).sum()),
    "with_directorate_curve_plot_only_as_log": int((has.log & ~has.log_licensee & ~has.log_wdss).sum()),
    "with_old_wdss_completion_log_sheet": int(has.log_wdss.sum()),
    "with_licensee_log_or_wdss_sheet": int((has.log_licensee | has.log_wdss).sum()),
    "with_licensee_log_or_wdss_sheet_and_report": int(((has.log_licensee | has.log_wdss) & has.rep).sum()),
}

# ---------------- Kansas ----------------
las = pd.read_csv(ROOT / "raw/partc/kgs/las/ks_las_files.txt", dtype=str, encoding="latin-1")
sc = pd.read_csv(ROOT / "raw/partc/kgs/scans/ks_elog_scans.txt", dtype=str, encoding="latin-1",
                 usecols=["KID", "LOGGER", "TOOL", "SCAN_URL", "LOG_TOP", "LOG_BOTTOM"], on_bad_lines="skip")
tool = sc.TOOL.fillna("")
logger = sc.LOGGER.fillna("")
kinds = {
    "geologists_report": logger.eq("Geologist's Report") | tool.str.contains(r"geologic(?:al)? report|geologic report", case=False),
    "sample_log": tool.str.contains(r"sample log", case=False),
    "strip_log": logger.eq("Strip/Sample Logs") | tool.str.contains(r"strip", case=False),
    "mud_log": tool.str.contains(r"mud ?log", case=False),
}
anyk = np.zeros(len(sc), dtype=bool)
k = {"las_rows": int(len(las)), "wells_with_las": int(las.KGS_ID.nunique()),
     "scan_rows": int(len(sc)), "wells_with_any_scanned_log": int(sc.KID.nunique())}
for name, m in kinds.items():
    k[f"scan_rows_{name}"] = int(m.sum())
    k[f"wells_with_{name}"] = int(sc[m].KID.nunique())
    anyk |= m.to_numpy()
rock = sc[anyk]
k["scan_rows_any_of_the_four_kinds"] = int(anyk.sum())
k["wells_with_any_of_the_four_kinds"] = int(rock.KID.nunique())
k["wells_with_las_and_any_of_the_four_kinds"] = int(len(set(las.KGS_ID) & set(rock.KID)))
k["wells_with_las_and_any_scanned_log"] = int(len(set(las.KGS_ID) & set(sc.KID)))
out["kansas"] = k
rng = np.random.default_rng(SEED + 20)
pick = rock[rock.SCAN_URL.fillna("").str.len() > 0].reset_index(drop=True)
pick = pick.iloc[np.sort(rng.choice(len(pick), size=3, replace=False))]
pick.to_csv(ROOT / "work" / "partc_kansas_draw.csv", index=False)

# ---------------- Netherlands ----------------
b = pd.read_csv(ROOT / "raw/partc/nlog/NLOG_Boreholes.csv", dtype=str)
out["netherlands"] = {"boreholes_in_listing": int(len(b)), "with_public_date": int(b.PUBLIC_AS_OF.notna().sum()),
                      "columns_about_logs_or_documents": [c for c in b.columns if re.search(r"log|doc|report", c, re.I)]}
(ROOT / "work" / "partc_counts.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
print(pick.to_string(index=False))
