"""Local check of sideways drift of a scanned log strip: thin full-width slices of the sheet at several
depths, stacked into one picture with a millimetre ruler. Used only to place the cutting bands.
Usage: python -I src/drift_check.py <layout key> <out.png> <depth> [<depth> ...]"""
import json, sys
from pathlib import Path
import pymupdf
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent
MM = 72 / 25.4
key, out = sys.argv[1], sys.argv[2]
cfg = json.loads((ROOT / "src" / "log_tiles.json").read_text())[key]
page = pymupdf.open(ROOT / cfg["pdf"])[cfg["page"] - 1]
W = page.rect.width / MM
dpi, h_mm = 60, 42
rows = []
for d in map(float, sys.argv[3:]):
    y = cfg["ref"][0] + (d - cfg["ref"][1]) * cfg["mm_per_m"]
    clip = pymupdf.Rect(page.rect.x0, page.rect.y0 + (y - h_mm / 2) * MM, page.rect.x1, page.rect.y0 + (y + h_mm / 2) * MM)
    pix = page.get_pixmap(dpi=dpi, clip=clip, colorspace=pymupdf.csRGB)
    rows.append((d, Image.frombytes("RGB", (pix.width, pix.height), pix.samples)))
ruler_h = 16
img = Image.new("RGB", (rows[0][1].width, sum(r.height + ruler_h for _, r in rows)), "white")
dr = ImageDraw.Draw(img)
y0 = 0
for d, r in rows:
    for mm in range(0, int(W), 10):
        x = mm * dpi / 25.4
        dr.line([x, y0, x, y0 + (10 if mm % 50 == 0 else 5)], fill=(200, 0, 0))
        if mm % 50 == 0:
            dr.text((x + 2, y0 + 3), str(mm), fill=(200, 0, 0))
    dr.text((img.width - 70, y0 + 3), f"{d:.0f} m", fill=(0, 0, 200))
    img.paste(r, (0, y0 + ruler_h))
    y0 += r.height + ruler_h
img.save(out)
print(img.size)
