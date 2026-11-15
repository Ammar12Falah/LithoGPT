"""B3: prepare the report pages of one well for the text reader (local tools only).

For every report document of the well (not the completion-log strips, not the NPD curve plots):
  work/text_read/<well>/<doc>/p0001.png   page picture at 110 dpi
  work/text_read/<well>/<doc>/p0001.txt   text of the page (text layer or local OCR)
  work/text_read/<well>/documents.csv     document folder, number of pages, document address
  work/text_read/<well>/candidate_pages.txt  pages with many rock words (from find_pages.py)
Pages longer than 600 mm (log strips and long enclosures) are left out.

Usage: python -I src/b_pages.py <well>
"""
import io
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pandas as pd
import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import find_pages  # noqa: E402
from common import ROOT, well_code  # noqa: E402


def main():
    well = sys.argv[1]
    code = well_code(well)
    src = pd.read_csv(ROOT / "src" / "sources.csv")
    out = ROOT / "work" / "text_read" / code
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for pdf in sorted((ROOT / "docs" / code).glob("*.pdf")):
        name = pdf.stem
        if name.startswith("composite_log_") or "WDSS" in name:
            continue
        doc = pymupdf.open(pdf)
        keep = [i for i in range(doc.page_count)
                if max(doc[i].rect.width, doc[i].rect.height) / 72 * 25.4 <= 600]
        if not keep:
            continue
        od = out / name
        od.mkdir(exist_ok=True)
        for i in keep:
            png = od / f"p{i + 1:04d}.png"
            if not png.exists():
                doc[i].get_pixmap(dpi=110, colorspace=pymupdf.csGRAY).save(png)
            txt = ROOT / "work" / "ocr" / code / name / f"p{i + 1:04d}.txt"
            if txt.exists():
                shutil.copy(txt, od / txt.name)
        url = src[src.path == f"docs/{code}/{pdf.name}"].url.iloc[0]
        rows.append({"document_folder": name, "pages_kept": len(keep), "pages_in_pdf": doc.page_count,
                     "document_address": url})
    pd.DataFrame(rows).to_csv(out / "documents.csv", index=False)
    buf = io.StringIO()
    sys.argv = ["find_pages.py", code, "6"]
    with redirect_stdout(buf):
        find_pages.main()
    (out / "candidate_pages.txt").write_text(
        "Pages with many rock words (local text search; a starting point, not a complete list).\n"
        "rock = number of rock words on the page, depth_ranges = number of 'from - to' depth pairs.\n\n"
        + buf.getvalue(), encoding="utf-8")
    print(well, [(r["document_folder"], r["pages_kept"]) for r in rows])


if __name__ == "__main__":
    main()
