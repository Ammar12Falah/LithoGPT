"""manifest.csv (every downloaded file) and hashes.txt (sha256 of every downloaded file and result file).

Usage: python -I src/make_manifest.py
"""
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULT_DIRS = ["readings", "scores", "curve", "conflicts", "check_sheet"]
RESULT_FILES = ["draw.csv", "reading_rules.md", "notes.md", "data_count.md", "report.md", "FREEZE"]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    src = pd.read_csv(ROOT / "src" / "sources.csv").drop_duplicates("path", keep="last")
    rows, lines = [], []
    for _, r in src.iterrows():
        p = ROOT / r.path
        if not p.exists():
            continue
        h = sha(p)
        rows.append({"name": r.path, "source_address": r.url, "date_utc": r.date_utc,
                     "size_bytes": p.stat().st_size, "sha256": h})
        lines.append(f"{h}  {r.path}  (downloaded, not in git)")
    pd.DataFrame(rows).to_csv(ROOT / "manifest.csv", index=False)
    for d in RESULT_DIRS:
        for p in sorted((ROOT / d).rglob("*")):
            if p.is_file():
                lines.append(f"{sha(p)}  {p.relative_to(ROOT)}")
    for f in RESULT_FILES:
        p = ROOT / f
        if p.exists():
            lines.append(f"{sha(p)}  {f}")
    (ROOT / "hashes.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(len(rows), "downloaded files in manifest.csv;", len(lines), "lines in hashes.txt")


if __name__ == "__main__":
    main()
