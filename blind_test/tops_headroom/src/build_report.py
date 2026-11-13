"""Assemble report.md from report_src.md. Lines of the form
<!-- TABLES:kansas --> are replaced by results/kansas_tables.md, which
run.py writes from the result files (report_tables.py).

    .venv/bin/python -I src/build_report.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    src = (ROOT / "report_src.md").read_text()

    def tables(m):
        f = ROOT / "results" / f"{m.group(1)}_tables.md"
        return f.read_text().rstrip() if f.exists() else f"*(no results for {m.group(1)})*"

    out = re.sub(r"<!-- TABLES:(\w+) -->", tables, src)
    (ROOT / "report.md").write_text(out)
    print("report.md written,", len(out.splitlines()), "lines")


if __name__ == "__main__":
    main()
