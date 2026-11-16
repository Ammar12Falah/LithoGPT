### Three main findings

1. **The picture idea holds for the main model, and only for it.** Fact: reading the log curves
   as pictures, after 20 labelled example pictures, gave 80.6 percent. The plain model trained on
   the same ten example wells gave 79.9. The picture reader was more even over the rock classes
   (balanced 71.0 against 46.2) and better on strict agreement (76.6 against 69.8). The all-well
   model (93 wells) stayed above it in all five wells, by 4.5 points pooled. With cheaper readers
   the same method fell to 67.6 (Sonnet) and 48.7 (Haiku).
2. **The teacher from documents sits between the all-shale line and ten expert wells on the
   headline number, and above ten expert wells on rare rocks.** Fact: the combined reading gave
   75.4 percent, 15.1 points above the all-shale line and 4.5 below the ten-well model, which was
   ahead in all five wells. The teacher was much better on Tuff (75 against 19), Coal (89 against
   48), Limestone (58 against 40) and Marl (47 against 0). It almost never matched Sandstone/Shale
   (6 percent of 1 155 m). Judgment: the documents name the main rock well and the rare beds well,
   but they do not carry the experts' line between Shale, Sandstone/Shale and Sandstone.
3. **Cheaper readers read text as well as the main model, and pictures worse.** Fact: text
   reading gave 72.1 (main), 72.2 (Sonnet) and 71.7 (Haiku). Log pictures gave 74.4, 68.7 and 63.6.
   The combined teacher reading gave 75.4, 70.7 (not decided, 4.7 points lower and behind in 4 of 5
   wells) and 65.7 (behind). The cheaper readers wrote far fewer rows from pictures and took a sixth
   to a ninth of the time.

### Three main doubts

1. **Five wells are few.** Fact: on the curve wells the gap between two plain models changes
   from well to well with a spread of about 6 points, so five wells can show a gap of about
   5.5 points at best (power check, table T2). The gaps that decide Mark 2 (4.5 points) and the
   distance of the curve pictures to the all-well model (4.5 points) are inside that noise. One
   well, 30/6-5, holds 41 percent of the scored depth.
2. **Claude may already know these wells.** Fact: the FORCE 2020 files and the reports of these
   wells have been public for years, and the document readers saw the well names. I cannot check
   what the model has seen in training. The readers were told to use only what is on the page.
   Judgment: the readers' weak score on Sandstone/Shale, and the many places where they disagree
   with the experts, do not look like recall of the labels. This is not proof.
3. **The method was fitted on little data, by me, and for the main model only.** Fact: the word
   map and the combined rule were settled on two practice wells, the curve-picture method on three
   example wells, and nothing was tuned for Sonnet or Haiku. Two practice choices cut both ways on
   the test wells: sending siltstone to Shale, and sending tuffaceous claystone to Tuff (of the
   194 m of conflicts between teacher and experts, 128 m are teacher Tuff against expert Shale).
   I also had to repair my own picture cutting during the readings (30/6-5 was read twice; see
   "What went differently"). The experts' labels themselves differ in habit from well to well
   (the plain model scores between 35 and 93 percent strict on single curve wells).
