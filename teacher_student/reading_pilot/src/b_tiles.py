"""B2: cut a completion log into pictures with overlap (local image cutting only).

The layout of every sheet is given in src/log_tiles.json:
  pdf, page            the document and the page that holds the completion log
  bands_mm             list of [x0, x1] columns to keep (rock column with its depth numbers, written
                       descriptions, formation names). The curve tracks are left out where possible.
  header_mm            list of [x0, y0, x1, y1] header boxes (title block, legend of rock symbols)
  ref                  [y_mm, depth_m] one depth mark found on the sheet, and
  mm_per_m             the paper scale (2.0 at 1:500), used ONLY to choose which part of the sheet to cut
  dpi, tile_m, overlap_m
The depth range to cut is the range that train.csv covers for the well (from the logs file).

Usage: python -I src/b_tiles.py <well> [d_from d_to]
"""
import json
import sys
from pathlib import Path

import pandas as pd
import pymupdf
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, well_code  # noqa: E402

MM = 72 / 25.4
Image.MAX_IMAGE_PIXELS = None


def grab(page, x0, y0, x1, y1, dpi):
    r = page.rect
    clip = pymupdf.Rect(r.x0 + x0 * MM, r.y0 + y0 * MM, min(r.x0 + x1 * MM, r.x1), min(r.y0 + y1 * MM, r.y1))
    pix = page.get_pixmap(dpi=dpi, clip=clip, colorspace=pymupdf.csRGB)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def main():
    well = sys.argv[1]
    cfg = json.loads((ROOT / "src" / "log_tiles.json").read_text())[well]
    logs = pd.read_parquet(ROOT / "data" / "logs_all.parquet", columns=["WELL", "DEPTH_MD"])
    d = logs[logs.WELL == well].DEPTH_MD
    d_from, d_to = float(d.min()), float(d.max())
    if len(sys.argv) > 3:
        d_from, d_to = float(sys.argv[2]), float(sys.argv[3])
    code = well_code(well)
    out = ROOT / "work" / "log_read" / code / "pictures"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.png"):
        f.unlink()
    doc = pymupdf.open(ROOT / cfg["pdf"])
    page = doc[cfg["page"] - 1]
    page_h = page.rect.height / MM
    # header pictures
    for i, (x0, y0, x1, y1) in enumerate(cfg["header_mm"], 1):
        im = grab(page, x0, y0, x1, y1, cfg.get("header_dpi", 110))
        im.save(out / f"00_header_{i}.png")
    y_ref, d_ref = cfg["ref"]
    k = cfg["mm_per_m"]
    tile, over, dpi = cfg["tile_m"], cfg["overlap_m"], cfg["dpi"]
    start = d_from - over
    rows = []
    n = 0
    while start < d_to:
        a, b = start, start + tile
        y0 = y_ref + (a - d_ref) * k
        y1 = y_ref + (b - d_ref) * k
        y0c, y1c = max(0.0, y0), min(page_h, y1)
        if y1c - y0c > 5:
            n += 1
            parts = [grab(page, x0, y0c, x1, y1c, dpi) for x0, x1 in cfg["bands_mm"]]
            h = max(p.height for p in parts)
            w = sum(p.width for p in parts) + 6 * (len(parts) - 1)
            im = Image.new("RGB", (w, h), "white")
            x = 0
            for p in parts:
                im.paste(p, (x, 0))
                x += p.width
                if x < w:
                    ImageDraw.Draw(im).rectangle([x, 0, x + 5, h], fill=(120, 120, 120))
                    x += 6
            fn = f"{n:02d}_log_about_{int(round(a))}-{int(round(b))}m.png"
            im.save(out / fn)
            rows.append({"file": fn, "approx_from_m": round(a), "approx_to_m": round(b), "w": w, "h": h})
        start += tile - over
    pd.DataFrame(rows).to_csv(out.parent / "tiles.csv", index=False)
    print(well, n, "log pictures;", "sizes", rows[0]["w"], "x", rows[0]["h"], "; depth range to read", round(d_from, 1), round(d_to, 1))


if __name__ == "__main__":
    main()
