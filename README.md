# Bible Commentator

The Berean Standard Bible (BSB) plus layers of scriptural citation data — who cited
each chapter, from the New Testament's use of the Old, through the Ante-Nicene Church
Fathers, to a modern scholar's teaching videos.

Built on a LAN fleet of local models (Hermes Agent bots) — zero cloud tokens.
The extraction tooling is included, so every layer can be regenerated or extended.

## Layout

```
bible/
  ot/<Book>/chapter<N>.txt       BSB Old Testament text (39 books, 929 chapters)
  nt/<Book>/chapter<N>.txt       BSB New Testament text (27 books, 260 chapters)
  ot/<Book>/fathers.citation     Church Fathers citing that OT book/chapter
  nt/<Book>/ot.citation          NT author citing the OT (book -> chapter:verse | context)
  nt/<Book>/fathers.citation     Church Fathers citing that NT book/chapter
  nt/<Book>/wright.citation      N.T. Wright citing the passage in his teaching (growing)
citations/
  nt_to_ot.db                    sqlite: NT->OT citation candidates + resolutions
  fathers.db                     sqlite: 10,749+ resolved citations from ANF vols 1-6
  wright.db                      sqlite: citations from N.T. Wright transcripts (in progress)
tools/
  extract_fathers_citations.py   CCEL ANF/NPNF volume -> resolved citations + files
  scan_wright_transcripts.py     cleaned YouTube transcripts -> citation candidates
  clean_vtt.py                   VTT auto-captions -> plain text
```

## Citation file format

Every `.citation` file lives inside its book directory, one citation per line:

```
<Book> <chapter>:<verse> | <Source>, <Work> (<ref>): <context, max ~150 chars>
```

Examples:

```
Matthew 2:17 -> Jeremiah 31:15 | Rachel weeping for children
Isaiah 1:18 | Irenaeus, the_first_epistle_of_clement_to_the_corinthians (anf01): Comp. Isa. i. 18.
```

## Sources

- **BSB text**: Berean Standard Bible (public domain), organized book/chapter
- **Church Fathers**: Ante-Nicene Fathers + Nicene and Post-Nicene Fathers
  (CCEL, Schaff edition), 24 volumes, ~90 MB
- **N.T. Wright**: auto-caption transcripts from the N.T. Wright Online YouTube channel

## Status

- BSB corpus: complete (66 books, 1,189 chapters)
- NT→OT citations: 115 citations across 13 books — complete
- Church Fathers: 10,749 citations from ANF vols 1–6 (41 book files); remaining
  18 volumes in progress
- N.T. Wright: 152 transcripts scanned; citation extraction in progress

## Regenerate

```bash
python3 tools/extract_fathers_citations.py   # needs CCEL volume texts + sections/ maps
```

## License

- This repo's tooling and structure: MIT
- BSB text: public domain
- ANF/NPNF texts: public domain (19th-century translations)
- N.T. Wright transcripts: for personal study; not redistributed here (fetch your own)