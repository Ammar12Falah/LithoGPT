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
