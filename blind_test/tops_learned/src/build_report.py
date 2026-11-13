"""Assemble report.md from report_src.md. Lines of the form
<!-- TABLES:kansas --> are replaced by results/kansas_tables.md.

    .venv/bin/python -I src/build_report.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    srcp = ROOT / "report_src.md"
    if not srcp.exists():
        print("no report_src.md yet")
        return
    src = srcp.read_text()

    def tables(m):
        f = ROOT / "results" / f"{m.group(1)}_tables.md"
        return f.read_text().rstrip() if f.exists() else f"*(no results for {m.group(1)})*"

    out = re.sub(r"<!-- TABLES:(\w+) -->", tables, src)
    (ROOT / "report.md").write_text(out)
    print("report.md written,", len(out.splitlines()), "lines")


if __name__ == "__main__":
    main()
