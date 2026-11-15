"""A1 step 2: note which documents exist for each training well and give roles.

Inputs : draw.csv (drawn order), raw/factpages/wellbore_document.csv
Output : draw.csv with document flags, roles and reasons.

Document rule (fixed before any document was opened):
 (a) completion log  = document type "COMPOSITE LOG", or a document name that holds
     COMPLETION_LOG, COMPLETIONLOG, COMPOSITE_LOG, COMPOSITE_WELL_LOG, or a combined
     "..._REPORT_AND_LOG" / "..._REPORT_&_COMPLETION_LOG" file, or the old scanned
     "WDSS_completion_log" sheet.
 (b) report          = a document name that holds COMPLETION and REPORT (in any order;
     this covers completion report, well completion report, geological completion
     report, drilling completion report and the combined report-and-log files),
     or FINAL_WELL_REPORT, END_OF_WELL_REPORT, FINAL_GEOLOGICAL_REPORT,
     GEOLOGICAL_REPORT.
 A well has both documents if it has at least one (a) and at least one (b).
 Name match: exact match of the well name after upper-casing and removing spaces.
 Anything else is "unsure" and the well is treated as having no documents.

Replacements (decided after the usability check) are read from
src/replacements.csv if that file exists: columns well, usable (yes/no), reason.

Usage: python -I src/a1_roles.py
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
N_TEST, N_EXAMPLE, N_PRACTICE, N_CURVE = 5, 10, 2, 23


def norm(name: str) -> str:
    return "".join(str(name).upper().split())


def is_log(doc_type: str, name: str) -> bool:
    n = name.upper()
    if doc_type == "COMPOSITE LOG":
        return True
    pats = [r"COMPLETION[_ ]?LOG", r"COMPOSITE[_ ]LOG", r"COMPOSITE[_ ]WELL[_ ]LOG",
            r"REPORT[_ ](AND|&)[_ ]LOG", r"COMPLETIONLOG"]
    return any(re.search(p, n) for p in pats)


def is_report(doc_type: str, name: str) -> bool:
    n = name.upper()
    if doc_type not in ("REPORTED BY LICENSEE", "NPD PAPER", "OLD NPD WDSS"):
        return False
    if re.search(r"COMPLETION.*REPORT|REPORT.*COMPLETION", n) and "WDSS" not in n:
        return True
    pats = [r"FINAL[_ ]WELL[_ ]REPORT", r"END[_ ]OF[_ ]WELL[_ ]REPORT",
            r"FINAL[_ ]GEOLOGICAL[_ ]REPORT", r"(^|_)GEOLOGICAL[_ ]REPORT"]
    return any(re.search(p, n) for p in pats)


def main() -> None:
    draw = pd.read_csv(ROOT / "draw.csv")[["draw_order", "well", "n_rows"]]
    docs = pd.read_csv(ROOT / "raw" / "factpages" / "wellbore_document.csv",
                       encoding="utf-8-sig")
    docs["key"] = docs["wlbName"].map(norm)
    docs["is_log"] = [is_log(t, str(n)) for t, n in zip(docs.wlbDocumentType, docs.wlbDocumentName)]
    docs["is_report"] = [is_report(t, str(n)) for t, n in zip(docs.wlbDocumentType, docs.wlbDocumentName)]
    keys = set(docs["key"])

    rows = []
    for _, r in draw.iterrows():
        k = norm(r.well)
        if k in keys:
            sub = docs[docs.key == k]
            logs = sub[sub.is_log].wlbDocumentName.astype(str).tolist()
            reps = sub[sub.is_report].wlbDocumentName.astype(str).tolist()
            match = "exact"
            fp_name = sub.wlbName.iloc[0]
        else:
            logs, reps, match, fp_name = [], [], "unsure (no exact name in the documents table)", ""
        rows.append({
            "draw_order": r.draw_order, "well": r.well, "n_rows": r.n_rows,
            "factpages_name": fp_name, "name_match": match,
            "n_log_docs": len(logs), "n_report_docs": len(reps),
            "has_both": bool(logs) and bool(reps),
            "log_docs": " | ".join(logs), "report_docs": " | ".join(reps),
        })
    t = pd.DataFrame(rows)

    rep_path = ROOT / "src" / "replacements.csv"
    unusable = {}
    if rep_path.exists():
        rep = pd.read_csv(rep_path)
        unusable = {w: str(why) for w, u, why in zip(rep.well, rep.usable, rep.reason) if str(u).lower() == "no"}
        usable_note = {w: str(why) for w, u, why in zip(rep.well, rep.usable, rep.reason) if str(u).lower() == "yes"}
    else:
        usable_note = {}

    # first pass: nominal roles in the drawn order
    role = {}
    reason = {}
    with_both = t[t.has_both].well.tolist()
    nominal_test = with_both[:N_TEST]
    last_test_pos = t.index[t.well == nominal_test[-1]][0]
    for i, r in t.iterrows():
        if i <= last_test_pos:
            if r.well in nominal_test:
                role[r.well] = "test"
                reason[r.well] = "one of the first 5 wells in the drawn order with both documents"
            else:
                role[r.well] = "extra"
                why = "passed over as test well: "
                if r.name_match != "exact":
                    why += "name match unsure, treated as having no documents"
                elif r.n_log_docs == 0 and r.n_report_docs == 0:
                    why += "no completion log and no report in the documents table"
                elif r.n_log_docs == 0:
                    why += "no completion log in the documents table"
                else:
                    why += "no report of the named kinds in the documents table"
                reason[r.well] = why
    after = t.iloc[last_test_pos + 1:]
    ex = after.well.tolist()[:N_EXAMPLE]
    for w in ex:
        role[w] = "example"
        reason[w] = "one of the 10 wells after the last test well"
    cur = after.well.tolist()[N_EXAMPLE:N_EXAMPLE + N_CURVE]
    for w in cur:
        role[w] = "curve"
        reason[w] = "one of the 23 wells after the last example well"
    for w in after.well.tolist()[N_EXAMPLE + N_CURVE:]:
        role[w] = "extra"
        reason[w] = "remaining well"

    # second pass: replace unusable test wells with the first extra wells that have both documents
    for w in list(nominal_test):
        if w in unusable:
            role[w] = "extra"
            reason[w] = "was drawn as test well, documents not usable: " + unusable[w]
            for cand in t.well:
                if role[cand] == "extra" and bool(t.loc[t.well == cand, "has_both"].iloc[0]) \
                        and cand not in unusable and cand not in nominal_test:
                    role[cand] = "test"
                    reason[cand] = f"replacement for {w}: first extra well in the drawn order with both documents"
                    break

    # practice wells: first 2 example wells with both documents (usable), else first extra wells
    practice = []
    for w in ex:
        if bool(t.loc[t.well == w, "has_both"].iloc[0]) and w not in unusable:
            practice.append(w)
        if len(practice) == N_PRACTICE:
            break
    if len(practice) < N_PRACTICE:
        for cand in t.well:
            if role[cand] == "extra" and bool(t.loc[t.well == cand, "has_both"].iloc[0]) \
                    and cand not in unusable and cand not in nominal_test:
                practice.append(cand)
            if len(practice) == N_PRACTICE:
                break
    t["role"] = t.well.map(role)
    t["practice_well"] = t.well.isin(practice)
    t["reason"] = t.well.map(reason)
    for w, why in unusable.items():
        if role.get(w) == "example" or (role.get(w) == "extra" and "was drawn" not in reason[w]):
            t.loc[t.well == w, "reason"] = t.loc[t.well == w, "reason"] + "; documents checked and not usable: " + why
    for w, why in usable_note.items():
        t.loc[t.well == w, "reason"] = t.loc[t.well == w, "reason"] + "; documents checked: " + why
    t.to_csv(ROOT / "draw.csv", index=False)
    print(t.role.value_counts().to_string())
    print("test wells    :", t[t.role == "test"].well.tolist())
    print("practice wells:", t[t.practice_well].well.tolist(), "roles", t[t.practice_well].role.tolist())
    print("example wells :", t[t.role == "example"].well.tolist())
    cols = ["draw_order", "well", "name_match", "n_log_docs", "n_report_docs", "has_both", "role", "practice_well"]
    print(t[cols].head(45).to_string(index=False))


if __name__ == "__main__":
    main()
