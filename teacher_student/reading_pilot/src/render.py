"""Render a piece of a PDF page to a PNG file (local tool, no network).

Usage: python -I src/render.py <pdf> <page_number_from_1> <y0_mm> <y1_mm> <dpi> <out.png> [x0_mm x1_mm]
"""
import sys

import pymupdf

MM = 72 / 25.4


def render(pdf, page, y0, y1, dpi, out, x0=None, x1=None, gray=True):
    doc = pymupdf.open(pdf)
    pg = doc[page - 1]
    r = pg.rect
    xa = r.x0 + (x0 * MM if x0 is not None else 0)
    xb = r.x0 + (x1 * MM if x1 is not None else r.width)
    clip = pymupdf.Rect(xa, r.y0 + y0 * MM, min(xb, r.x1), min(r.y0 + y1 * MM, r.y1))
    pix = pg.get_pixmap(dpi=dpi, clip=clip, colorspace=pymupdf.csGRAY if gray else pymupdf.csRGB)
    pix.save(out)
    return pix.width, pix.height


if __name__ == "__main__":
    a = sys.argv
    x0 = float(a[7]) if len(a) > 7 else None
    x1 = float(a[8]) if len(a) > 8 else None
    print(render(a[1], int(a[2]), float(a[3]), float(a[4]), int(a[5]), a[6], x0, x1, gray=False))
