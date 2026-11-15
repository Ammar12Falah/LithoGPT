"""Download the completion-log and report documents of named wells from FactPages.

Only documents listed in the public documents table are fetched, and only for
the wells named on the command line (test wells and practice wells).
Every download is recorded in src/sources.csv (path, url, date).

Usage: python -I src/download_docs.py "31/3-1" "30/6-5" ...
       python -I src/download_docs.py --extra "<well>" "<exact document name>"
"""
import datetime as dt
import subprocess
import sys
import urllib.parse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from a1_roles import is_log, is_report  # noqa: E402


def code(well: str) -> str:
    return well.replace("/", "_").replace(" ", "_")


def record(path: Path, url: str) -> None:
    src = ROOT / "src" / "sources.csv"
    new = not src.exists()
    with open(src, "a", encoding="utf-8") as f:
        if new:
            f.write("path,url,date_utc\n")
        rel = path.relative_to(ROOT)
        f.write(f'"{rel}","{url}",{dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")}\n')


def fetch(url: str, out: Path) -> bool:
    if out.exists() and out.stat().st_size > 0:
        print("  have", out.name)
        return True
    out.parent.mkdir(parents=True, exist_ok=True)
    # the table holds raw addresses with spaces and commas; quote the path part only
    parts = urllib.parse.urlsplit(url)
    q = urllib.parse.urlunsplit((parts.scheme, parts.netloc, urllib.parse.quote(parts.path), parts.query, ""))
    r = subprocess.run(["curl", "-sS", "-L", "--fail", "--max-time", "500", "-o", str(out), q],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  FAILED", url, r.stderr.strip())
        if out.exists():
            out.unlink()
        return False
    record(out, url)
    print("  got", out.name, out.stat().st_size)
    return True


def main() -> None:
    docs = pd.read_csv(ROOT / "raw" / "factpages" / "wellbore_document.csv", encoding="utf-8-sig")
    args = sys.argv[1:]
    if args and args[0] == "--extra":
        well, name = args[1], args[2]
        sub = docs[(docs.wlbName == well) & (docs.wlbDocumentName.astype(str) == name)]
        for _, r in sub.iterrows():
            fn = str(r.wlbDocumentUrl).rsplit("/", 1)[-1].replace(" ", "_").replace(",", "_")
            fetch(r.wlbDocumentUrl, ROOT / "docs" / code(well) / fn)
        return
    for well in args:
        sub = docs[docs.wlbName == well]
        print(well, len(sub), "documents listed")
        for _, r in sub.iterrows():
            name = str(r.wlbDocumentName)
            if is_log(r.wlbDocumentType, name) or is_report(r.wlbDocumentType, name):
                fn = str(r.wlbDocumentUrl).rsplit("/", 1)[-1].replace(" ", "_").replace(",", "_")
                if r.wlbDocumentType == "COMPOSITE LOG":
                    fn = "composite_log_" + fn
                fetch(r.wlbDocumentUrl, ROOT / "docs" / code(well) / fn)


if __name__ == "__main__":
    main()
