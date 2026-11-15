"""Find report pages that describe the rock by depth (local text search on OCR text).

Counts rock words and depth-like numbers on each page and lists the pages with most hits.

Usage: python -I src/find_pages.py <well_code> [min_score]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORDS = ["lithology", "claystone", "sandstone", "limestone", "siltstone", "shale", "cuttings",
         "sample description", "sidewall core", "marl", "chalk", "dolomite", "coal", "tuff",
         "clay", "sand", "clst", "sst", "lst", "sltst", "anhydrite", "halite", "salt"]


def score_page(txt: str):
    low = txt.lower()
    hits = {w: len(re.findall(r"\b" + re.escape(w) + r"\b", low)) for w in WORDS}
    rock = sum(hits.values())
    depths = len(re.findall(r"\b\d{3,4}(?:[.,]\d)?\s*(?:-|to|–)\s*\d{3,4}(?:[.,]\d)?\s*(?:m|ft)?\b", low))
    return rock, depths, hits


def main():
    well = sys.argv[1]
    min_score = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    for doc in sorted((ROOT / "work" / "ocr" / well).iterdir()):
        if not doc.is_dir():
            continue
        rows = []
        for p in sorted(doc.glob("p*.txt")):
            txt = p.read_text(encoding="utf-8", errors="replace")
            rock, depths, hits = score_page(txt)
            if rock >= min_score:
                top = ",".join(f"{k}:{v}" for k, v in sorted(hits.items(), key=lambda x: -x[1])[:4] if v)
                rows.append((int(p.stem[1:]), rock, depths, len(txt), top))
        print(f"== {doc.name}: {len(list(doc.glob('p*.txt')))} pages, {len(rows)} with rock words >= {min_score}")
        for r in rows:
            print(f"   p{r[0]:<4} rock={r[1]:<3} depth_ranges={r[2]:<3} chars={r[3]:<5} {r[4]}")


if __name__ == "__main__":
    main()
