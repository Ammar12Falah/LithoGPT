"""Step 6, the confirmatory wells file (protocol section 3; RUN_PLAN.md, "What the author provides", item 2).

Downloads the official FORCE 2020 open and blind test files, keeps them untouched with their
SHA-256, and builds the one CSV that RUN_PLAN.md asks for: `;` separated, columns
WELL, DEPTH_MD, GR, RDEP, NPHI, RHOB, FORCE_2020_LITHOFACIES_LITHOLOGY, the 10 open then the
10 blind wells. Lithofacies labels that come in a separate file are joined row by row.

Source. The dataset is FORCE 2020 (Bormann et al. 2020, doi 10.5281/zenodo.4351156). That Zenodo
record holds only a LAS zip of all 118 wells and NPD spreadsheets, no CSV test files. The official
competition CSVs are in the FORCE GitHub repository, the source scripts/fetch_force_no_blind.py
uses. They are fetched here at a pinned commit and checked against the sizes and git blob hashes
GitHub reported for that commit (author's choice, 2026-11-19).

What this script may print: file names, sizes, hashes, column names, well names and row counts
(rows per well, valid rows per section 3, rows with a label). It never prints, plots or summarises
curve values or labels. Values are copied as text, never parsed, when the CSV is built. Valid rows
are counted with the pipeline's own validity mask, on the built file. Any error whose message might
hold a data value is reported by its type only.

  python -B c06_prepare_confirmatory.py fetch          the real run: download, build, manifest
  python -B c06_prepare_confirmatory.py build --open_features F --open_target F --blind F \
        --out_csv F --manifest F                       build from local files (tests)

`fetch` refuses to run unless origin-orig/protocol/confirmatory-test holds CLARIFICATIONS.md and
its last line names a commit of this repo whose copy of this script is the one being run.
Writes the raw files (read-only), the CSV, and the manifest out/c06_manifest.json.
"""
import sys

sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.request
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4_common as vc  # noqa: E402

ARCHIVE = vc.REPO.parent
RAW_DIR = ARCHIVE / "force2020_confirm" / "raw"
OUT_CSV = ARCHIVE / "force2020_confirm" / "confirmatory_wells.csv"
MANIFEST = vc.OUT / "c06_manifest.json"

GH_REPO = "bolgebrygg/Force-2020-Machine-Learning-competition"
GH_COMMIT = "0b9d8b9e58f09bf284f58e2cb06adb5b43b781ce"      # last commit touching lithology_competition/data
GH_RAW = f"https://raw.githubusercontent.com/{GH_REPO}/{GH_COMMIT}/lithology_competition/data/"
DATASET_DOI = "10.5281/zenodo.4351156"
USER_AGENT = "research-data-client/1.0"                      # generic; no personal details
# name: (role, size in bytes, git blob SHA-1), as the GitHub API reported them on 2026-11-19
RAW_FILES = {
    "leaderboard_test_features.csv": ("open_features", 31688732, "7153017194f89b36ab17b37ff2079adbdc18cee5"),
    "leaderboard_test_target.csv": ("open_target", 3694123, "50ff419e342f06b58566ef4c41c236f721522b4a"),
    "hidden_test.csv": ("blind", 30292497, "2c6adce79789ee9a0f09a1b3f664be0422023a4f"),
}
REQUIRED = ["WELL", "DEPTH_MD"] + vc.FEATURES
LABEL = vc.LABEL_COL
OUT_COLS = REQUIRED + [LABEL]
N_EXPECTED = {"open": 10, "blind": 10}
MIN_VALID = 2000                                             # section 3
CLARIFICATIONS_REF = "origin-orig/protocol/confirmatory-test"


class Refuse(Exception):
    """An error raised by this script. Its message holds only names, counts and hashes."""


def say(msg):
    print(msg, flush=True)


# ----------------------------------------------------------------------------- hashes
def git_blob_sha1(path):
    h = hashlib.sha1()
    h.update(f"blob {os.path.getsize(path)}\0".encode())
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path):
    return dict(name=Path(path).name, size=os.path.getsize(path), sha256=vc.sha256_file(path))


# ----------------------------------------------------------------------------- gate and download
def check_published():
    """The rulings must be on origin-orig before the confirmatory data is touched, and they must
    name a commit whose copy of this script is the one being run."""
    repo = vc.REPO
    here = Path(__file__).resolve()
    try:
        subprocess.run(["git", "-C", str(repo), "fetch", "-q", "origin-orig", "protocol/confirmatory-test"],
                       check=True, capture_output=True, timeout=120)
        text = subprocess.run(["git", "-C", str(repo), "show", f"{CLARIFICATIONS_REF}:CLARIFICATIONS.md"],
                              check=True, capture_output=True, text=True).stdout
    except Exception as e:  # noqa: BLE001
        raise Refuse(f"cannot read CLARIFICATIONS.md on {CLARIFICATIONS_REF} ({type(e).__name__}); "
                     "publish the rulings first") from None
    lines = [ln for ln in text.splitlines() if ln.strip()]
    m = re.search(r"\b([0-9a-f]{40})\b", lines[-1]) if lines else None
    if not m:
        raise Refuse("the last line of CLARIFICATIONS.md names no full commit hash")
    commit = m.group(1)
    v4_repo = Path(subprocess.run(["git", "-C", str(here.parent), "rev-parse", "--show-toplevel"],
                                  check=True, capture_output=True, text=True).stdout.strip())
    rel = here.relative_to(v4_repo)
    try:
        published = subprocess.run(["git", "-C", str(v4_repo), "show", f"{commit}:{rel}"],
                                   check=True, capture_output=True).stdout
    except subprocess.CalledProcessError:
        raise Refuse(f"commit {commit} (named in CLARIFICATIONS.md) has no {rel}") from None
    if published != here.read_bytes():
        raise Refuse(f"{rel} differs from its copy in the published commit {commit}")
    say(f"rulings published: CLARIFICATIONS.md on {CLARIFICATIONS_REF} names pipeline commit {commit}; "
        f"this script equals its copy there")
    return dict(clarifications_ref=CLARIFICATIONS_REF,
                clarifications_sha256=hashlib.sha256(text.encode()).hexdigest(), pipeline_commit=commit)


def download(raw_dir):
    """Fetch the three files at the pinned commit. Existing files are checked, never replaced."""
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, (role, size, blob) in RAW_FILES.items():
        dest = raw_dir / name
        if not dest.exists():
            part = dest.with_name(name + ".part")
            for attempt in range(3):
                try:
                    req = urllib.request.Request(GH_RAW + name, headers={"User-Agent": USER_AGENT})
                    with urllib.request.urlopen(req, timeout=300) as r, open(part, "wb") as f:  # noqa: S310
                        while True:
                            b = r.read(1 << 20)
                            if not b:
                                break
                            f.write(b)
                    break
                except Exception as e:  # noqa: BLE001
                    say(f"download {name}: attempt {attempt + 1} failed ({type(e).__name__})")
                    time.sleep(5 * (attempt + 1))
            else:
                raise Refuse(f"could not download {name}")
            part.replace(dest)
            os.chmod(dest, 0o444)
            say(f"downloaded {name}")
        got_size, got_blob = os.path.getsize(dest), git_blob_sha1(dest)
        if got_size != size or got_blob != blob:
            raise Refuse(f"{name}: size {got_size} and git blob {got_blob} do not match the pinned "
                         f"{size} and {blob}; the raw file is left as it is")
        say(f"{name}: {got_size} bytes, git blob {got_blob} matches the pinned commit")
        paths[role] = dest
    return paths


# ----------------------------------------------------------------------------- build
def read_text_table(path):
    """The whole file as text, nothing parsed. Refuses a file that is not `;` separated."""
    import pandas as pd
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\r\n")
    if ";" not in header:
        seps = [s for s in (",", "\t", "|") if s in header]
        raise Refuse(f"{Path(path).name}: the header has no ';' (found {seps or 'no separator'}); "
                     "wrong separator")
    df = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False, na_filter=False)
    df.columns = [c.strip() for c in df.columns]
    if len(set(df.columns)) != len(df.columns):
        raise Refuse(f"{Path(path).name}: repeated column names {list(df.columns)}")
    return df


def wells_in_order(df):
    return list(dict.fromkeys(df["WELL"].tolist()))


def norm_well(w):
    return re.sub(r"\s+", " ", str(w)).strip().upper()


def join_labels(feat, target, tname):
    """Labels from a separate file, joined row by row. The rows must line up: same row count,
    and the same WELL and DEPTH_MD on every row where the label file has those columns."""
    import numpy as np
    if LABEL not in target.columns:
        raise Refuse(f"{tname}: no {LABEL} column (columns {list(target.columns)})")
    if len(target) != len(feat):
        raise Refuse(f"{tname}: {len(target)} rows, the features file has {len(feat)}; cannot join labels")
    how = ["row order"]
    if "WELL" in target.columns:
        bad = int((target["WELL"].to_numpy() != feat["WELL"].to_numpy()).sum())
        if bad:
            raise Refuse(f"{tname}: WELL differs from the features file on {bad} rows; cannot join labels")
        how.append("WELL equal on every row")
    if "DEPTH_MD" in target.columns:
        a = pd_float(target["DEPTH_MD"]); b = pd_float(feat["DEPTH_MD"])
        same = (a == b) | (np.isnan(a) & np.isnan(b))
        if not same.all():
            raise Refuse(f"{tname}: DEPTH_MD differs from the features file on {int((~same).sum())} rows; "
                         "cannot join labels")
        how.append("DEPTH_MD equal on every row")
    out = feat.copy()
    out[LABEL] = target[LABEL].to_numpy()
    return out, ", ".join(how)


def pd_float(s):
    import pandas as pd
    return pd.to_numeric(s.str.strip().replace("", "nan"), errors="coerce").to_numpy(dtype="float64")


def build(files, out_csv, manifest_path, extra=None, expect_counts=True):
    """files: dict role -> path, roles open_features, open_target (may be None), blind."""
    import pandas as pd
    split = vc.load_split()
    pool = set(split["pool98"])
    pool_norm = {norm_well(w) for w in pool}
    man = dict(dataset_doi=DATASET_DOI, source=dict(repo=GH_REPO, commit=GH_COMMIT, url=GH_RAW),
               created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), raw_files={}, **(extra or {}))
    parts, wells_by_set, label_join = [], {}, {}
    for setname, frole, trole in (("open", "open_features", "open_target"), ("blind", "blind", None)):
        fpath = Path(files[frole])
        rec = file_record(fpath)
        df = read_text_table(fpath)
        rec.update(role=frole, columns=list(df.columns), n_rows=len(df))
        man["raw_files"][fpath.name] = rec
        say(f"{fpath.name}: {rec['size']} bytes, SHA-256 {rec['sha256']}, {len(df)} rows")
        say(f"  columns: {', '.join(df.columns)}")
        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            raise Refuse(f"{fpath.name}: missing column(s) {missing}")
        tpath = files.get(trole) if trole else None
        if tpath:
            tpath = Path(tpath)
            trec = file_record(tpath)
            tdf = read_text_table(tpath)
            trec.update(role=trole, columns=list(tdf.columns), n_rows=len(tdf))
            man["raw_files"][tpath.name] = trec
            say(f"{tpath.name}: {trec['size']} bytes, SHA-256 {trec['sha256']}, {len(tdf)} rows")
            say(f"  columns: {', '.join(tdf.columns)}")
            if LABEL in df.columns:
                raise Refuse(f"{fpath.name} already has {LABEL} and {tpath.name} brings it again")
            df, how = join_labels(df, tdf, tpath.name)
            label_join[setname] = f"from {tpath.name}, joined by {how}"
        elif LABEL in df.columns:
            label_join[setname] = f"in {fpath.name}"
        else:
            df[LABEL] = ""
            label_join[setname] = "none in the file; the token's mapped facies is used (QUESTIONS.md Q30)"
        say(f"  labels for the {setname} wells: {label_join[setname]}")
        wells = wells_in_order(df)
        bad = [w for w in wells if w in pool or norm_well(w) in pool_norm]
        if bad:
            raise Refuse(f"{fpath.name}: {len(bad)} pool well(s) present: {bad}")
        if expect_counts and len(wells) != N_EXPECTED[setname]:
            raise Refuse(f"{fpath.name}: {len(wells)} wells, expected {N_EXPECTED[setname]}")
        wells_by_set[setname] = wells
        parts.append(df[OUT_COLS])
    both = set(wells_by_set["open"]) & set(wells_by_set["blind"])
    if both:
        raise Refuse(f"wells in both the open and the blind file: {sorted(both)}")

    out = pd.concat(parts, ignore_index=True)
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_csv.with_name(out_csv.name + ".tmp")
    out.to_csv(tmp, sep=";", index=False)
    tmp.replace(out_csv)
    # the copy is exact: read back as text, it equals what was taken from the raw files
    back = pd.read_csv(out_csv, sep=";", dtype=str, keep_default_na=False, na_filter=False)
    if list(back.columns) != OUT_COLS or not back.equals(out):
        raise Refuse(f"{out_csv.name}: read back, it differs from the text taken from the raw files")

    # rows, valid rows (section 3, the pipeline's own mask) and labelled rows per well
    vdf = vc.load_df(out_csv)
    per_well, eligible = {}, []
    for setname, wells in wells_by_set.items():
        for w in wells:
            r = vc.well_rows(vdf, w)
            n_lab = int((out.loc[out.WELL == w, LABEL].str.strip() != "").sum())
            ok = r["n_valid"] >= MIN_VALID
            per_well[w] = dict(set=setname, n_rows=r["n_file_rows"], n_valid=r["n_valid"], n_labelled=n_lab,
                               eligible=bool(ok))
            if ok:
                eligible.append(w)
    rec = file_record(out_csv)
    rec.update(columns=OUT_COLS, n_rows=len(out), n_wells=len(per_well))
    man.update(output_csv=rec, label_join=label_join, wells=per_well, eligible_wells=eligible,
               n_eligible=len(eligible), min_valid_rows=MIN_VALID)
    vc.save_json(man, manifest_path)

    say(f"\n{out_csv.name}: {rec['size']} bytes, SHA-256 {rec['sha256']}, {len(out)} rows, {len(per_well)} wells")
    say(f"  columns: {', '.join(OUT_COLS)}")
    say("| Set | Well | Rows | Valid rows | Labelled rows | Eligible |")
    say("|---|---|---|---|---|---|")
    for w, p in per_well.items():
        say(f"| {p['set']} | {w} | {p['n_rows']} | {p['n_valid']} | {p['n_labelled']} | "
            f"{'yes' if p['eligible'] else 'no'} |")
    say(f"eligible wells (at least {MIN_VALID} valid rows): {len(eligible)} of {len(per_well)}")
    say(f"manifest: {manifest_path}")
    return man


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--raw_dir", default=str(RAW_DIR))
    f.add_argument("--out_csv", default=str(OUT_CSV))
    f.add_argument("--manifest", default=str(MANIFEST))
    b = sub.add_parser("build")
    b.add_argument("--open_features", required=True)
    b.add_argument("--open_target", default=None)
    b.add_argument("--blind", required=True)
    b.add_argument("--out_csv", required=True)
    b.add_argument("--manifest", required=True)
    b.add_argument("--any_count", action="store_true", help="do not require 10 open and 10 blind wells")
    args = ap.parse_args()
    warnings.simplefilter("error")          # a warning might quote data; treat it as an error
    try:
        vc.check_protocol()
        if args.cmd == "fetch":
            gate = check_published()
            paths = download(args.raw_dir)
            raw = {name: dict(size=os.path.getsize(p), git_blob_sha1=git_blob_sha1(p))
                   for name, p in ((p.name, p) for p in paths.values())}
            build(paths, args.out_csv, args.manifest, extra=dict(gate=gate, download=raw))
        else:
            build(dict(open_features=args.open_features, open_target=args.open_target, blind=args.blind),
                  args.out_csv, args.manifest, expect_counts=not args.any_count)
    except Refuse as e:
        say(f"REFUSED: {e}")
        sys.exit(2)
    except Exception as e:  # noqa: BLE001
        say(f"ABORT: {type(e).__name__} (message withheld: it may quote data values)")
        sys.exit(3)


if __name__ == "__main__":
    main()
