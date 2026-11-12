# Bulletin of the National Research Centre version

This folder holds the version of the paper for the Bulletin of the National Research Centre
(Springer Open, journal 42269), set on the Springer Nature LaTeX template in
`../../sn-journal-paper/` (`sn-jnl`, reference style `sn-basic`, author-year). The
manuscript is double-spaced (`referee`) with line numbers (`lineno`), as the journal asks
for review.

`paper.md` is the PPEECS text (`../ppeecs/paper.md`) in the journal's structure. Nothing is
reworded apart from what that structure needs:

- Introduction is called Background, with Related work as its subsection.
- Method and Experimental setup are subsections of one Methods section, which has a
  one-line opening.
- Discussion and conclusions is split into Discussion and Conclusions by moving its
  sentences. The roadmap sentence names the new sections.
- The abstract carries the labels Background, Methods, Results and Conclusions (350 words,
  limit 350).
- The supplement is cited as Additional file 1.
- Two caption titles are split by a full stop to keep titles within 15 words.
- The back matter has the Supplementary information entry, the List of abbreviations and
  the Declarations in the journal's order. Every declaration heading is required, with
  "Not applicable" where it does not apply. Availability of data and materials follows the
  journal's format for datasets and software (public repository link, MIT license). The
  authors' contributions are split evenly between the four students, by initials.
- Numbers are written without thousands separators anywhere, as the editor asked.

`supplement.md` is the PPEECS supplement, published as Additional file 1, with Tables S3 and
S4 (spread over seeds and states) added in the revision.

## Revision for the editor (November 2026)

The editor's pre-review mail listed 23 requests. 17 are done in this version; the response
letter is `response/response_to_editor.tex` (build with `tectonic`), where red `[[...]]`
marks what is still open: the ORCID iDs, the Zenodo DOI and the 6 requests still in
progress. The BNRC version reads its own result set, run with 1000 permutations in every
permutation test: `outputs/bnrc/` in the code repository, generated into
`../generated/bnrc/` and `../figures/bnrc/`. The other versions keep `../generated/`.
Against the 200-permutation set, no diagnosis verdict changed; the MMD false alarm rate
went from 7.0 to 6.0% and the learned meta-classifier moved by up to 0.6 points.
`datasets.bib` adds the data citations the journal requires: the UCI gas sensor dataset
(DOI) and the Census Bureau's ACS microdata page.

| File | Content |
|---|---|
| `paper.md`, `supplement.md` | source texts |
| `build/BNRC_manuscript.tex` / `.pdf` | the manuscript (36 pages, double-spaced) |
| `BNRC_manuscript_latex.zip` | the manuscript upload: .tex, .bbl, .bib, class, style and figures, compiles on its own |
| `build/BNRC_additional_file_1.tex` / `.pdf` | Additional file 1 (7 pages) |
| `build/references.bib` | the PPEECS references and the data citations; web pages carry "Accessed <date>" |
| `build/BNRC_manuscript.bbl` | the formatted bibliography, so the source compiles even without bibtex |
| `build/figures/` | the figures used by the LaTeX files |
| `build/sn-jnl.cls`, `build/sn-basic.bst` | template files, copied so the folder compiles on its own |

## Build

From the repository root:

```
python examples/paper/build_bnrc.py --figures    # figures, LaTeX and PDF
python examples/paper/build_bnrc.py --no-pdf     # LaTeX only
```

It needs tectonic (`TECTONIC=...`) for the PDF. Unlike the conference versions,
figures and tables are LaTeX floats with the journal's captions: a table's title is set
above it, its legend below it as a table note. `flafter` keeps every float after the text
that introduces it, on the same page or a later one. A table wider than the text gets
two-line headers and, if still too wide, wrapping long columns (`tabularx`).

The build checks the journal's rules and fails if one is broken:
- abstract length, its four labels and no citations in it;
- 3 to 10 keywords;
- caption titles of at most 15 words;
- no page breaks;
- no float before its first mention;
- no thousands separators in the body.

`build/` also compiles with pdflatex and bibtex, for example on Overleaf.
