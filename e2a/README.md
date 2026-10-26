# E2A 2026 conference version

The version of the paper for E2A 2026, to be published in Springer's Lecture Notes in
Electrical Engineering (LNEE). The conference asks for the Springer proceedings format
(LaTeX or Word template), at most 12 pages including figures, tables and references,
no double-blind review. Guidelines: `../../e2a-conf-paper/instructions.txt`.

`paper.md` is the 12-page DACS text (`../dacs/paper.md`) with the sentences unchanged.
The only edits are the front matter (LNCS keywords, title-case keywords), the figure
widths for the 122 mm LNCS text width, the original opening sentence "ACS Income shows
the clearest trend, so we start there." (the DACS cut had left "Its accuracy" without
a subject) and a reference to Eq. (1) ("the CBPE estimate of Eq. (1)"), since every
numbered equation must be referenced. The title is the DACS title, without
"Reliability Analysis", because the reliability stage is not evaluated in this cut.

The file is written on the Springer LNCS Word template (`../../icmmdu-conf-paper/splnproc2311.docm`,
the same layout as `llncs.cls`): Times 10 pt, 122 x 193 mm text area, LNCS headings,
captions and references, keywords separated by middots.

| File | Content |
|---|---|
| `paper.md` | source text |
| `build/E2A_paper.docx` | the submission file (12 pages) |
| `build/E2A_paper.pdf` | PDF made with LibreOffice, for checking the layout |
| `figures/Fig04.{pdf,png}` | accuracy timelines, one row of four panels at 122 mm |

Fig. 1 and Fig. 2 are the PPEECS drawings and Fig. 3 is the one-column PPEECS confusion
figure (`../ppeecs/figures/`); a row of four confusion matrices is too narrow at 122 mm.

## Build

    python examples/paper/build_springer12.py e2a              # Word and PDF
    python examples/paper/build_springer12.py e2a --figures    # also redraw Fig. 4

The build fails if the paper exceeds 12 pages, a table or figure is not on the page of
its first mention (below it, or at the top of the next page when it does not fit),
or a float or equation is never referenced.
