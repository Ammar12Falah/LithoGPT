# Reading rules of the reading pilot

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
  (first practice round, log pictures: 257 m Shale against 160 m Sandstone/Shale; text: 355 m
  against 182 m). So siltstone goes to Shale, with Sandstone/Shale as second class.
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
before text that describes long intervals or mixed cuttings. On the two practice sections
(25/7-2 from 1400 to 2600 m, 25/4-5 from 1700 to 2900 m; second practice round, with the final
instructions) the pooled tolerant agreement was: combined by this rule 75.8 percent, log picture
alone 74.4, text alone 67.6, all-shale line 51.2. These numbers come from the same two wells on
which the word map was settled, so they are too rosy. The practice wells hold no cuttings sample
lists, so the practice could not show whether cuttings samples should come before or after the
log picture. I put them after, for the reason given above. That part is a judgment, not a
measured result.

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

### 10.1 Curve-picture reader

````markdown
# Instructions for the curve-picture reader

You read pictures of well-log curves and name the rock at every depth. You get three things only:
these instructions, a folder of labelled example pictures, and a folder with the pictures of one
unknown well. You work from the pictures alone.

## Hard limits
- Open only the files named in your task: this file, the example pictures and the well pictures.
  Use the Read tool to look at pictures and the Write tool for your output file. Use no other tool.
- Do not open any data file, table, script or other folder. Do not search the disk or the web.
- Do not try to find out which well it is. Do not use anything you may remember about a well.
- Do not guess from the file names. The four-letter code in a file name means nothing.

## The pictures
- Paper style, depth runs down the page. Depth numbers (metres, measured depth) are on the left.
  Heavy grid lines carry a depth number. Light grid lines are the small steps between them
  (2 m on a 100 m picture, 1 m on a 50 m picture).
- Tracks from left to right. Each track names its curves and scales at the top:
  1. Gamma ray GR (green, 0 to 200 API), caliper CALI (dashed) and bit size BS (dotted), 6 to 26 inches.
  2. Resistivity on a log scale, 0.2 to 2000 ohm.m: deep (solid red), medium (dashed blue), shallow (dotted).
  3. Density RHOB (solid red, 1.95 to 2.95 g/cc), neutron NPHI (dashed blue, 0.45 on the left to -0.15 on the right), PEF (dotted, 0 to 10).
  4. Sonic DTC (240 on the left to 40 us/ft on the right). Slow rock plots to the left, fast rock to the right.
  5. Other curves the well has: SP, rate of penetration ROP, density correction DRHO.
  6. Group name (bold) and formation name (italic) as text. You may use them as context.
- A curve that is not drawn is missing in that well or at that depth. A curve that runs flat on the
  edge of its track is off scale.
- Example pictures have one more track on the right: the rock class that experts gave, in colour,
  with a legend at the bottom. The pictures of the unknown well do not have it.

## The 12 rock classes (use these names exactly)
Sandstone, Sandstone/Shale, Shale, Marl, Dolomite, Limestone, Chalk, Halite, Anhydrite, Tuff, Coal, Basement

## How to work
1. Look at every example picture first, one by one. Learn how the experts label: which curve
   shapes they call Sandstone, Sandstone/Shale, Shale, Marl, Limestone, Chalk and so on, how thin
   their beds are, and how the classes go with the group and formation names.
2. Then read the pictures of the unknown well in depth order, every picture, top to bottom.
3. For each picture write intervals: depth from, depth to, rock class, confidence.
   - The intervals follow each other without gaps and without overlaps, from the first depth with
     curves to the last.
   - The smallest interval is 1 m. Merge thinner beds into the neighbour.
   - Read the boundaries off the depth grid as well as you can, to the nearest metre.
   - One class per interval, from the list above. No other words.
   - Confidence is high, medium or low: how sure you are of the class.
   - Where no curve is drawn at all for 1 m or more, write a row with an empty rock class.
   - An interval may run across the edge of two pictures. Then write it as one row.
4. Things that usually hold (the examples take priority where they show otherwise):
   - Shale is the most common class by far. Most of a well is Shale.
   - Sandstone: low gamma ray, often with density and neutron curves close together or crossing.
     Sandstone/Shale: in between sandstone and shale, or thin beds of both.
   - Limestone, Chalk and Dolomite: low gamma ray, high density, fast sonic, high resistivity.
     Marl: between limestone and shale. Chalk is mostly found in chalk groups.
   - Coal: very low density, very slow sonic, high neutron, in thin beds.
   - Halite: density near 2.0 to 2.1, very low gamma ray, very high resistivity, washed-out hole.
     Anhydrite: density near 2.95, very low gamma ray.
   - Tuff: named in tuff-bearing formations; follow what the examples show.
   - Do not split the well into more beds than the curves support.

## Output
Write one CSV file to the path named in your task, with this header and one row per interval:

depth_from,depth_to,rock_class,confidence

Example rows:
1800,1836,Shale,high
1836,1841,Limestone,medium
1841,1900,Shale,high

Numbers are metres. Do not add other columns. Do not leave out any depth between the first and the
last row. When the file is written, answer with: the number of example pictures you looked at, the
number of well pictures you looked at, the number of rows written, and anything you could not read.
````

### 10.2 Log-picture reader

````markdown
# Instructions for the log-picture reader

You read the rock column that geologists drew on the completion log of one well, and write down the
rock by depth. You get these instructions, the header pictures of the sheet (title block and legend
of rock symbols) and the pictures cut from the sheet, in depth order. You work from these alone.

## Hard limits
- Open only the files named in your task. Use Glob on the named folder, Read for pictures and
  Write for your output file. Use no other tool. Run no commands. Do not search the disk or the web.
- Use the drawn rock column and the written rock descriptions next to it. Do NOT use the log
  curves on the sheet (gamma ray, resistivity, sonic and so on), even where a piece of a curve
  shows in a picture.
- Do not use anything you may remember about this well or field. Read what is on the sheet.
- Do not guess. If something cannot be read, leave the cell empty and say so in your final answer.
  Never invent a depth.

## The pictures
- `00_header_*.png`: the title block and the legend of rock symbols. Read the legend first. Note the
  depth unit and reference written on the sheet (for example "m RKB").
- `NN_log_about_A-Bm.png`: pieces of the sheet from top to bottom. Each picture shows several
  columns of the sheet side by side, separated by grey bars: usually the stratigraphy names, the
  rock column with its depth numbers, and the written descriptions. The numbers in the file name are
  only a rough guide. Read the true depths from the depth numbers printed on the sheet, and
  interpolate between them with the grid lines.
- Neighbouring pictures overlap by a few metres. Do not record the overlap twice.

## The 12 rock classes (use these names exactly)
Sandstone, Sandstone/Shale, Shale, Marl, Dolomite, Limestone, Chalk, Halite, Anhydrite, Tuff, Coal, Basement

## Word map (rock as drawn or written -> rock class)
- sand, sandstone, conglomerate, gravel, pebbles -> Sandstone
- sandstone drawn or described as very shaly or argillaceous; sand and clay/shale drawn in thin
  alternating beds (thinner than about 2 m each) -> Sandstone/Shale
- clay, claystone, shale, mudstone (also silty or sandy claystone) -> Shale
- siltstone, silt -> Shale, and write Sandstone/Shale in `second_class`
  (on the practice wells the experts called most siltstone Shale)
- marl, marlstone -> Marl
- limestone (also argillaceous or sandy limestone, limestone stringers) -> Limestone
- chalk -> Chalk
- dolomite, dolostone -> Dolomite
- salt, halite, rock salt, potash salts -> Halite
- anhydrite, gypsum -> Anhydrite
- tuff, volcanic ash -> Tuff. Also Tuff: claystone or siltstone that carries tuff marks all through
  the interval, or that the description next to it calls tuffaceous without a weakening word.
  A weakening word ("slightly", "partly", "occasionally", "locally", "traces of") or a few scattered
  tuff marks do not make it Tuff; then write Tuff in `second_class`.
- coal, lignite -> Coal
- basement, granite, gneiss, schist and other igneous or metamorphic rock -> Basement
- small accessory symbols scattered in a column (pyrite, glauconite, mica, fossils, calcareous
  or tuffaceous marks, carbonaceous specks) do not change the class.

## How to work
1. Go through the pictures in order. Follow the rock column down the sheet and split it wherever the
   main fill pattern changes. Name every pattern with the legend. If two rocks alternate in thin
   bands (for example limestone and marl), the main rock is the one that fills more of the column
   and the other goes into `second_class`.
2. Write one row for every interval of the rock column:
   - `depth_from`, `depth_to`: in metres as on the sheet. If the sheet is in feet, write the feet in
     `depth_unit_ref` and convert to metres (1 ft = 0.3048 m).
   - `depth_unit_ref`: unit and reference exactly as written on the sheet, for example "m RKB".
   - `rock_as_drawn`: the legend name of the main fill pattern, in the words of the legend, plus
     the description text if it helped (short).
   - `rock_class`: one of the 12 classes, by the word map. One class only.
   - `second_class`: fill in only if the column clearly shows a second rock inside the interval
     (for example thin limestone bands inside claystone, or a mixed pattern). Else leave empty.
   - `confidence`: high, medium or low. Use low where the pattern is hard to see.
   - `picture_file`: the picture where the interval starts.
3. The smallest interval is 1 m. A thinner band that is clearly drawn (a limestone stringer, a coal
   bed) becomes a 1 m interval at its depth. Bands too thin or too many to list go into
   `second_class` of the surrounding interval.
4. If the drawn column and the written description disagree, follow the drawn column and set the
   confidence to low. If the column is empty or cannot be read at some depth but a written
   description next to it names the rock, use the description and say so in `rock_as_drawn`.
   If neither can be read, write a row with an empty `rock_class`.
5. Read only the depth range named in your task. Rows follow each other from the top of that range
   to its base, without overlaps.

## Output
Write one CSV file to the path named in your task, with this header:

depth_from,depth_to,depth_unit_ref,rock_as_drawn,rock_class,second_class,confidence,picture_file

Put text that holds a comma in double quotes. When the file is written, answer with: the number of
pictures you looked at, the number of rows, the depth unit and reference you found, and anything
you could not read.
````

### 10.3 Text reader

````markdown
# Instructions for the text reader

You read the reports of one well and write down the rock by depth, with the source of every row.
You get these instructions and one folder with the report pages of the well. You work from these alone.

## Hard limits
- Open only files inside the folder named in your task. You may use Glob, Grep and Read inside
  that folder, and Write for your two output files. Use no other tool. Run no commands. Do not
  search the web or other folders.
- Do not use anything you may remember about this well or field. Write down only what the pages say.
- Do not guess. If a value cannot be read, leave the cell empty and say so. Never invent a number.

## The folder
- `documents.csv`: one line per document: the folder name, the number of pages and the document address.
- One folder per document, with two files per page: `p0012.png` (picture of the page) and
  `p0012.txt` (text of the page from a text layer or from local OCR; the first line says which).
  The page number in the file name is the page of the PDF file. Use it as the page number.
- `candidate_pages.txt`: pages with many rock words, from a local text search. It is a starting
  point. Check the list of contents of each report too, and search the text files yourself
  (useful words: lithology, claystone, sandstone, limestone, cuttings, sample description,
  sidewall core, core description, clst, sst, lst, sltst).
- OCR text has errors. Where a depth or a rock word looks wrong or doubtful in the text file, open
  the page picture and read it there.

## What to look for
Descriptions of the rock against depth, such as: lists of cuttings samples, core descriptions,
sidewall core descriptions, and the lithology part of the geological summary (by formation or by
depth interval). Use the finest descriptions the documents hold: sample-by-sample descriptions beat
formation summaries. Work in this order:
1. Record the finest descriptions first (samples, cores, sidewall cores).
2. Then add coarser descriptions (lithology by formation or by interval) for the depths that the
   fine descriptions do not cover, or cover only with single points.
Read only the depth range named in your task.

Take rock descriptions only from the parts of a report where geologists describe the rock: sample,
core and sidewall-core descriptions, and the lithology or stratigraphy sections of the geology
chapter. Do NOT make rows from drilling, mud, pressure, testing or seismic chapters, from table
labels, from figures without words, or from forecasts written before drilling.
Do not write a row for a rock that is only named as stringers or traces inside a longer interval
and has no depths of its own; it belongs in `second_class` of that interval.

## The 12 rock classes (use these names exactly)
Sandstone, Sandstone/Shale, Shale, Marl, Dolomite, Limestone, Chalk, Halite, Anhydrite, Tuff, Coal, Basement

## Word map (words of the geologist -> rock class)
- sand, sandstone (Sst, Sd), conglomerate, gravel -> Sandstone
- sandstone called very argillaceous or shaly; sand and clay/shale described as thinly interbedded
  or interlaminated in similar amounts -> Sandstone/Shale
- clay, claystone (Clst), shale (Sh), mudstone (also silty or sandy claystone) -> Shale
- siltstone, silt (Sltst) -> Shale, and write Sandstone/Shale in `second_class`
  (on the practice wells the experts called most siltstone Shale)
- marl, marlstone -> Marl
- limestone (Lst, Ls; also argillaceous or sandy limestone) -> Limestone
- chalk -> Chalk
- dolomite (Dol), dolostone -> Dolomite
- salt, halite, rock salt, potash salts -> Halite
- anhydrite, gypsum -> Anhydrite
- tuff, volcanic ash -> Tuff. Also Tuff: claystone or siltstone that the sentence calls tuffaceous
  without a weakening word. With a weakening word ("slightly", "partly", "occasionally", "locally",
  "traces of") it keeps its own class and Tuff goes into `second_class`.
- coal, lignite -> Coal
- basement, granite, gneiss, schist and other igneous or metamorphic rock -> Basement
- words for small amounts of something (pyrite, glauconite, mica, calcite cement, shell fragments,
  "calcareous", "carbonaceous", "tuffaceous" as an adjective) do not change the class.

## The main rock when a sentence names several
- If shares are given (percent, or "mainly", "predominantly", "dominantly"), the main rock is the
  one with the largest share.
- Else the main rock is the rock the sentence is about: the first-named rock, or the head of the
  entry. Words such as "with", "minor", "some", "occasional", "traces of", "stringers of",
  "thin beds of", "interbedded with thin" introduce second rocks.
- `second_class`: the clearest second rock, only if it is said to be more than a trace
  (about a fifth of the interval or more, or named as beds or stringers). Else leave empty.
- Sand(stone) and clay/shale described as alternating in similar amounts, with no depths for the
  single beds -> main class Sandstone/Shale.
- Never choose a class from the formation name alone. The sentence must name the rock.

## Depths
- Write depths in metres measured depth from the drill floor / rotary table / kelly bushing
  (RKB, KB, DF, RT, "driller's depth", "logger's depth"), as the report gives them.
- `depth_unit_ref`: the unit and reference exactly as written in the report, for example "m RKB".
- If the report is in feet: convert to metres (1 ft = 0.3048 m) and write the original feet
  values in `note`.
- If the report gives depths with another reference (true vertical depth, below sea level): convert
  only if the same document gives the numbers needed. Say so in `note`. If it does not, write the row
  with empty `depth_from` and `depth_to` and say so in `note`.
- A cuttings sample listed with a depth interval covers that interval. A cuttings sample listed
  with one depth stands for the interval from the previous sample depth in the list to this depth
  (for the first sample of a list: one sampling step above it).
- A core piece described with a top and a base depth covers that interval. A sidewall core or a
  single core point has one depth: write it in both `depth_from` and `depth_to`.
- An entry that covers a long interval with one sentence (a formation summary) is written as one row
  for that interval. Set its confidence to low if the sentence names several rocks without shares.
- If a printed depth looks like a misprint, do not correct it. Leave the doubtful depth cell empty
  and write the printed value in `note`.

## One row per described interval
- `depth_from`, `depth_to`, `depth_unit_ref` as above.
- `kind`: what kind of description the row comes from. One of: core, sidewall_core,
  cuttings_sample, interval_summary (lithology by formation or by depth interval).
- `source_sentence`: the exact words of the report that the row rests on. Copy, do not reword.
  You may cut a long sentence short with "..." after about 200 characters.
- `page`: page number of the PDF (from the file name). `document_address`: from documents.csv.
- `rock_class`, `second_class`: by the word map and the main-rock rule.
- `confidence`: high, medium or low: how sure you are that the row says what the report says and
  that the class is right.
- `note`: unit conversions, reading problems, anything unusual. May be empty.

## Other things to note
If a report shows a table of forecast (prognosed) depth against found depth of formation tops, do
not extract it. Write the document folder and page number into the notes file named in your task.
Write there also: which pages you read closely, and which kinds of description you found.

## Output
Write one CSV file to the path named in your task, with this header:

depth_from,depth_to,depth_unit_ref,kind,source_sentence,page,document_address,rock_class,second_class,confidence,note

Put every text cell in double quotes (double any quote mark inside it). Sort the rows by depth.
When both files are written, answer with: the number of pages whose text you read, the number of
page pictures you opened, the number of rows, and what you could not read or find.
````

