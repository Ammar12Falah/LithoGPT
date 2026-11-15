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
