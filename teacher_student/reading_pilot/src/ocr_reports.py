"""Local text extraction for the report PDFs (text layer if present, else tesseract OCR).

Writes one text file per page to work/ocr/<well>/<document>/p0001.txt.
Pages longer than 600 mm (log strips) are skipped here.

Usage: python -I src/ocr_reports.py <well_code> [<well_code> ...]
"""
import os
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
os.environ["OMP_THREAD_LIMIT"] = "1"


def do_page(args):
    pdf, pno, out = args
    out = Path(out)
    if out.exists():
        return 0
    doc = pymupdf.open(pdf)
    pg = doc[pno]
    if max(pg.rect.width, pg.rect.height) / 72 * 25.4 > 600:
        return 0
    txt = pg.get_text().strip()
    src = "textlayer"
    if len(txt) < 50:
        pix = pg.get_pixmap(dpi=200, colorspace=pymupdf.csGRAY)
        tmp = str(out) + ".png"
        pix.save(tmp)
        r = subprocess.run(["tesseract", tmp, "stdout", "--psm", "4", "-l", "eng"],
                           capture_output=True, text=True)
        txt = r.stdout
        os.remove(tmp)
        src = "ocr"
    out.write_text(f"[{src}]\n" + txt, encoding="utf-8")
    return 1


def main():
    jobs = []
    for well in sys.argv[1:]:
        for pdf in sorted((ROOT / "docs" / well).glob("*.pdf")):
            name = pdf.stem
            if name.startswith("composite_log_") or "WDSS" in name:
                continue
            doc = pymupdf.open(pdf)
            od = ROOT / "work" / "ocr" / well / name
            od.mkdir(parents=True, exist_ok=True)
            for i in range(doc.page_count):
                jobs.append((str(pdf), i, str(od / f"p{i + 1:04d}.txt")))
    with Pool(4) as p:
        n = 0
        for k, r in enumerate(p.imap_unordered(do_page, jobs, chunksize=4)):
            n += r
            if k % 100 == 0:
                print(k, "of", len(jobs), flush=True)
    print("done", n, "pages written")


if __name__ == "__main__":
    main()
