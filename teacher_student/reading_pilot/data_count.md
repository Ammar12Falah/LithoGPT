# Part C. Counting the data

Counted on 16 November 2026 from listing files only. No site was crawled. Every number names
its source file. The counting script is `src/c_count.py`. Downloaded files are in `manifest.csv`.

## What I could not do in this part

- **Kansas scanned documents could not be opened.** The scan addresses in the Kansas listing
  redirect to the host `kgsimages.blob.core.windows.net`. That host is not allowed in this
  environment (the request was refused). By rule 5 I stopped that step. Three documents were drawn
  with the seed and are listed below, but none was opened or described.
- **The Netherlands has no listing file for logs or documents.** The files NLOG offers for
  download list boreholes, deviation, stratigraphy and core analyses. None says which borehole
  has digital logs, a composite log, a lithology log or an end-of-well report. That is shown only
  on the page of each borehole in the NLOG data centre, and reading 6 739 such pages would be
  crawling. So, as the brief says, I stopped that part. No Dutch document was drawn or opened.

## Norway

Source: FactPages table "wellbore_document" (`raw/factpages/wellbore_document.csv`, from
`https://factpages.sodir.no`, downloaded 15 November 2026). 10 569 rows, 1 994 wellbore names.
The table lists documents of exploration wellbores that the directorate has released.

| what | wellbores |
|---|---|
| in the documents table | 1 994 |
| with a completion log, by the rule of A1 | 1 159 |
| with a report of the kinds named in A1 | 1 101 |
| with both, by the rule of A1 | 1 049 |

The rule of A1 (see `notes.md`): a completion log is a document of type "COMPOSITE LOG", or a
name with COMPLETION_LOG, COMPOSITE_LOG, "REPORT_AND_LOG", or an old "WDSS completion log"
sheet. A report is a name with COMPLETION and REPORT, FINAL_WELL_REPORT, END_OF_WELL_REPORT or
GEOLOGICAL_REPORT.

A caution found in this pilot: on the seven wells I opened, the files of type "COMPOSITE LOG"
(made by the directorate) were plots of the curves with no rock column. The rock column was on
the licensees' own completion logs. Counted more strictly:

| what | wellbores |
|---|---|
| with a licensee completion log (by document name) | 1 000 |
| with a licensee completion log and a report | 975 |
| with a licensee completion log or an old WDSS completion-log sheet | 1 043 |
| the same, and a report | 995 |
| with an old WDSS completion-log sheet | 529 |
| counted as "has a completion log" by the A1 rule only because of a directorate curve plot | 116 |

Judgment: about 1 000 Norwegian wellbores have both documents in a usable form. I did not open
any WDSS sheet, so I do not know whether those show a rock column.
What I could not count from this table: how many of these wellbores also have digital logs.
The documents table does not say.

## Kansas

Sources: two listing files of the Kansas Geological Survey, downloaded 16 November 2026 from
`https://www.kgs.ku.edu/PRS/Ora_Archive/`:
`ks_las_files.zip` ("info on all wells with LAS files", page
`https://www.kgs.ku.edu/Magellan/Logs/index.html`) and `ks_elog_scans.zip` ("the data for all the
scanned logs we have", page `https://www.kgs.ku.edu/Magellan/Elog/scan.html`).
Wells are counted by the survey's well number (`KGS_ID` in the first file, `KID` in the second).

| what | number | source |
|---|---|---|
| LAS files listed | 29 317 | ks_las_files.txt, rows |
| wells with a digital log file (LAS) | 24 468 | ks_las_files.txt, distinct KGS_ID |
| scanned logs listed, all kinds | 370 364 | ks_elog_scans.txt, rows |
| wells with any scanned log | 149 600 | ks_elog_scans.txt, distinct KID |
| wells with a scanned geologist's report | 20 922 | LOGGER = "Geologist's Report", or TOOL holds "Geologic(al) Report" |
| wells with a scanned sample log | 28 991 | TOOL holds "Sample Log" |
| wells with a scanned strip log | 11 941 | LOGGER = "Strip/Sample Logs", or TOOL holds "Strip" |
| wells with a scanned mud log | 1 448 | TOOL holds "Mud Log" |
| wells with at least one of these four kinds | 31 901 | 35 448 scans |
| wells with a LAS file and at least one of these four kinds | 4 252 | both files, same well number |
| wells with a LAS file and any scanned log | 22 955 | both files |

The four kinds overlap: the usual entry is LOGGER "Geologist's Report" with TOOL "Drilling Time
and Sample Log" (19 455 scans), which counts as geologist's report and as sample log.
The survey also keeps scanned completion forms and drillers' logs (page
`https://www.kgs.ku.edu/Magellan/ACO/index.html`). That page has a search form only and no listing
file, so they are not counted.

Three scanned documents, drawn at random with the seed (20261115 + 20) from the 35 448 scans of
the four kinds. **Not opened: the host is blocked (see above).** What the listing says about them:

| well number (KID) | LOGGER | TOOL | top to base as listed (ft) | address in the listing |
|---|---|---|---|---|
| 1039801831 | Geologist's Report | Drilling Time and Sample Log | 3300 to 4400 | http://www.kgs.ku.edu/PRS/Scans/kcc_logs_2009/216903.tif |
| 1006098035 | Strip/Sample Logs | Kansas Sample Log Service | 3600 to 4494 | http://www.kgs.ku.edu/PRS/Scans/Elog3/W/19S25/518366.tif |
| 1044837786 | Strip/Sample Logs | Sample Log | (no top) to 3264 | http://www.kgs.ku.edu/PRS/Scans/Elog3/E/21S2/624178.tif |

So I cannot say whether these show a drawn rock column, written rock descriptions or a depth
scale, or whether they can be read.

## Netherlands

Sources, downloaded 16 November 2026: the NLOG borehole listing
(`https://www.gdngeoservices.nl/geoserver/nlog/ows`, layer `nlog:gdw_ng_wll_all_utm`, linked from
`https://www.nlog.nl/en/files-interactive-map`), and "Thematic borehole data"
(`thematische_data_boringen.zip`, linked from `https://www.nlog.nl/en/boreholes`).

| what | number | source |
|---|---|---|
| boreholes in the listing | 6 739 | NLOG borehole listing, rows |
| of these with a "public as of" date | 6 735 | column PUBLIC_AS_OF |
| boreholes with digital logs | no listing file gives this | |
| boreholes with a composite log, a lithology log or an end-of-well report | no listing file gives this | |
| boreholes with both | no listing file gives this | |

The borehole listing has 43 columns. None is about logs, documents or reports. The thematic
download holds deviation surveys, stratigraphy, gas composition, porosity and permeability,
Rock-Eval and vitrinite tables. The file host offers seven layers (seismic lines, seismic grids,
boreholes, licences, trajectories, fields, facilities) and none lists logs or documents.
The NLOG data centre shows logs and documents borehole by borehole, in a web application.
I stopped here, as the brief says.

## What the sources say about reuse

- FactPages (Norway): "The content on the FactPages may be used in accordance with Norwegian
  Licence for Open Government Data (NLOD). In this context we emphasize that there may be
  limitations with respect to the use of information subject to third party rights, such as
  reports, core images and logs etc."
- Kansas Geological Survey (`https://www.kgs.ku.edu/General/copyright.html`, dated July 2002):
  the terms grant use "without any fee or cost" and ask for this credit: "The source of this
  material is the Kansas Geological Survey website at http://www.kgs.ku.edu/. All Rights
  Reserved." I read only parts of the page; read it in full before any reuse.
- NLOG (`https://www.nlog.nl/en/disclaimer`): "Users are also permitted to copy, duplicate,
  process or edit the information and/or layout, provided NLOG.NL is quoted as the source."

No listing file and no document from Part C is in git. Only the counts are.
