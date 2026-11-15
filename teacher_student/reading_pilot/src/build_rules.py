"""Assembles reading_rules.md from the fixed sections below and the exact instruction files
that the readers get. Run once, before the first test well is read. After that commit the
file does not change.

Usage: python -I src/build_rules.py <curve_instr.md> <log_instr.md> <text_instr.md>
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HEAD = """# Reading rules of the reading pilot

Fixed on 15 November 2026, before any test well was read and before any expert label of a test
well was opened. After the commit that adds this file, it does not change.

## 1. The 12 rock classes of the training file

As given by `train.csv` and the starter notebook of the FORCE 2020 competition:

| code | class |
|---|---|
| 30000 | Sandstone |
| 65030 | Sandstone/Shale |
| 65000 | Shale |
| 80000 | Marl |
| 74000 | Dolomite |
| 70000 | Limestone |
| 70032 | Chalk |
| 88000 | Halite |
| 86000 | Anhydrite |
| 99000 | Tuff |
| 90000 | Coal |
| 93000 | Basement |

The confidence column of the file means: 1 = high, 2 = medium, 3 = low (starter notebook).

## 2. Word map: from the words geologists use to the 12 classes

| words in the documents | class |
|---|---|
| sand, sandstone (Sst, Sd), conglomerate, gravel, pebbles | Sandstone |
| sandstone called very argillaceous or shaly; sand and clay/shale in thin alternating beds (thinner than about 2 m each) or thinly interbedded in similar amounts | Sandstone/Shale |
| clay, claystone (Clst), shale (Sh), mudstone, also silty or sandy claystone | Shale |
| siltstone, silt (Sltst) | Shale, with Sandstone/Shale as second class |
| marl, marlstone | Marl |
| limestone (Lst, Ls), also argillaceous or sandy limestone, limestone stringers | Limestone |
| chalk | Chalk |
| dolomite (Dol), dolostone | Dolomite |
| salt, halite, rock salt, potash salts | Halite |
| anhydrite, gypsum | Anhydrite |
| tuff, volcanic ash; claystone or siltstone that is called tuffaceous without a weakening word, or drawn with tuff marks all through the interval | Tuff |
| coal, lignite | Coal |
| basement, granite, gneiss, schist and other igneous or metamorphic rock | Basement |

Small accessories (pyrite, glauconite, mica, fossils, calcite cement, "calcareous", "carbonaceous",
"slightly / partly / occasionally tuffaceous") do not change the class.

Two entries were settled on the two practice wells (25/7-2 and 25/4-5), where the expert labels
may be seen:
- Siltstone. The first draft sent siltstone to Sandstone/Shale. At the depths that the practice
  documents call siltstone, the experts wrote Shale more often than Sandstone/Shale
  (log pictures: 257 m Shale against 160 m Sandstone/Shale; text: 350 m against 180 m).
  So siltstone goes to Shale, with Sandstone/Shale as second class.
- Tuff. In both practice wells the experts wrote Tuff where the documents show claystone or
  siltstone with tuff marks, or call it tuffaceous (Balder Formation). So such rock goes to Tuff.

## 3. The main rock when a sentence or a column names several

- If shares are given (percent, "mainly", "predominantly"), the main rock has the largest share.
- Else the main rock is the rock the sentence is about: the first-named rock, or the head of the
  entry. Words such as "with", "minor", "some", "occasional", "traces of", "stringers of",
  "thin beds of" introduce second rocks.
- On a drawn column the main rock is the fill pattern that takes most of the column in the
  interval. Scattered accessory symbols do not count.
- The second class is recorded only if the second rock is more than a trace (about a fifth of the
  interval or more, or named or drawn as beds or stringers).
- Sand(stone) and clay/shale alternating in similar amounts, with no depths for the single beds:
  main class Sandstone/Shale.
- A class is never chosen from the formation name alone.

## 4. Families of near classes (for the soft score)

- Sandstone, Sandstone/Shale and Shale are near each other.
- Limestone, Chalk and Marl are near each other.
- Every other class stands alone: Dolomite, Halite, Anhydrite, Tuff, Coal, Basement.

## 5. From a reading file to one class per depth step

One item is one depth step of `train.csv` that has an expert label. Every reading is first put on
the depth steps of the training file (`src/readings.py`):
- A row gives its `rock_class` to every depth step d with depth_from <= d < depth_to.
- A row with depth_from = depth_to (a sidewall core, a single point) covers d within 0.25 m of it.
- A row with an empty class, or with a depth that is not a number, gives no class.
- Where rows overlap: a row with confidence low counts only where no row with confidence medium
  or high gives a class. Among the rest the shortest row wins. Ties go to the higher confidence,
  then to the later row. (The low-confidence part was settled on the practice wells: it lifted
  the tolerant agreement of the text reading from 65.4 to 68.0 percent on 25/7-2 and from 53.4 to
  54.6 percent on 25/4-5.)
- Depths are metres measured depth from the rotary table or kelly bushing, as in `train.csv`
  (column DEPTH_MD). No depth shift is applied to any reading.

## 6. Scores

- Coverage: the share of items that got a class.
- Strict agreement: the reader's class at the item equals the expert class.
- Tolerant agreement: the expert class of the item appears as the reader's class at some depth
  step of the same well within 3 m above or below the item.
- Soft agreement: as tolerant, and a class of the same family also counts.
- Balanced agreement: tolerant agreement for each rock class with at least 20 m of expert label,
  then averaged over those classes.
- Each number is given twice: with unread items counted as wrong, and on read items only.
- Only the main class (`rock_class`) counts in all of these, for every reader, so that readers and
  models are judged alike. A side table shows the tolerant agreement when the second class of a
  document reading also counts. It is not used for any mark.
- The headline number is the tolerant agreement with unread items counted as wrong, pooled over
  the test wells scored.

## 7. Combined reading

One rule joins the text reading and the log-picture reading into one class by depth
(`src/combine.py`). At each depth step:
1. if the text reading gives a class from a core or sidewall-core description
   (column `kind` of the text reading is `core` or `sidewall_core`), take the text class;
2. else, if the log-picture reading gives a class, take the log-picture class;
3. else take the class of the text reading from any other row, if there is one;
4. else no class.

Why this rule. A core is the rock itself at a known depth, so it comes first. The rock column on
the completion log is the geologist's own picture of the rock by depth, bed by bed, so it comes
before text that describes long intervals or mixed cuttings. On the two practice sections the
rule "fine text first, then log picture, then other text" gave a pooled tolerant agreement of
67 percent, against 65 percent for the log picture alone and 62 percent for the text alone
(first practice round; see notes.md). The practice wells hold no cuttings sample lists, so the
practice could not show whether cuttings samples should come before or after the log picture.
I put them after, for the reason given above. This is a judgment, not a measured result.

## 8. The teacher reading that Mark 2 judges

**The combined reading.** It is named here before any test well is read.

## 9. The curve-picture method (fixed after the trial on example wells)

- Pictures are drawn by `src/a3_pictures.py` from the logs file only. Paper style, 860 x 1320
  pixels, 100 m of depth per picture. Tracks: gamma ray with caliper and bit size; resistivity on
  a log scale; density with neutron and PEF; sonic; other curves (SP, ROP, DRHO); group and
  formation names as text; depth numbers on the left. No well name. No rock labels. File names
  carry a random four-letter code.
- Example pictures: the same, plus one track with the expert rock class in colour and a legend.
  20 example pictures from the 10 example wells, chosen by `src/a3_trial.py final 100`: first one
  picture for every rock class the example wells hold (rarest class first, the picture with most
  metres of that class), then wells in turn, preferring pictures with two or more classes.
  The example wells hold 11 of the 12 classes (no Basement).
- A fresh reader sees the 20 example pictures, then all pictures of one test well in depth order,
  and writes intervals: depth from, depth to, rock class, confidence. Smallest interval 1 m.
  Where no curve is drawn it writes no class.
- Trial on three example wells with hidden labels (17/11-1, 25/4-5, 16/1-2; a 1000 m section of
  each, 200 m for 16/1-2), readers saw labelled pictures of the other 7 example wells:
  100 m pictures gave 78.9 percent tolerant agreement, 50 m pictures 78.6 percent, at about twice
  the reading effort. A second version of the instructions (more words on Sandstone/Shale and
  Marl) gave 78.5 percent. So: 100 m pictures, first version of the instructions.

## 10. The exact instructions each reader gets

Each reader is a subagent with a fresh memory. Its task message names only: the instructions
file, the folder(s) it may open, the depth range (document readers), and the output path.
The three instruction files follow, word for word.

"""


def main():
    curve, log, text = [Path(a).read_text(encoding="utf-8") for a in sys.argv[1:4]]
    out = HEAD
    for title, body in [("10.1 Curve-picture reader", curve), ("10.2 Log-picture reader", log), ("10.3 Text reader", text)]:
        out += f"### {title}\n\n````markdown\n{body.rstrip()}\n````\n\n"
    (ROOT / "reading_rules.md").write_text(out, encoding="utf-8")
    print("reading_rules.md written,", len(out), "characters")


if __name__ == "__main__":
    main()
