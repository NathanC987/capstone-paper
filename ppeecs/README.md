# Periodica Polytechnica EECS version

This folder holds the version of the paper prepared for *Periodica Polytechnica
Electrical Engineering and Computer Science* (PPEECS). The AGH version in `../main.tex`
is unchanged.

The journal works from Word files made with its template, so the paper is written in
`paper.md` (and `supplement.md`) and built into `.docx` and `.pdf` files.

| File | Content |
|---|---|
| `paper.md` | main text (12 pages, every table and figure that supports a claim) |
| `supplement.md` | online supplement: audit size (Fig. S1), triage by setting (Table S1), RELP code mapping (Table S2) |
| `references.bib` | references with DOIs or full-text URLs, formatted in the journal style |
| `template.docx` | the journal's MS Word template (styles, header) |
| `tikz/` | sources of Fig. 1 and Fig. 2 |
| `figures/` | figures as vector PDF and 600 dpi PNG, named as the journal asks (Fig01, ...) |
| `math_cache.json` | equations converted to Word format (rebuilt only when the math changes) |
| `build/` | `PPEECS_paper.docx/.pdf` and `PPEECS_supplement.docx/.pdf` |

## Build

From the repository root:

```
python examples/paper/build_artifacts.py     # numbers and tables, shared with the AGH paper
python examples/paper/build_ppeecs.py         # Word and PDF files
python examples/paper/build_ppeecs.py --figures   # also redraw the figures
```

The build needs LibreOffice (`soffice`) for the PDF. It needs pandoc (`PANDOC=...`) only
when an equation is new, and tectonic (`TECTONIC=...`) only to redraw Fig. 1 and Fig. 2.
The PDF matches the template best with the Open Sans font installed.

Every number is a `\res{key}` from `../generated/results.tex`, the same values as the AGH
paper (`../CLAIMS.md` maps each claim to its key). The build stops on an undefined
key, citation or label, on an abstract over 250 words, and on any figure or table that
is not referenced. It reports the page count and checks that every figure and table
sits on the page of its first mention. A lint pass flags a comma before "and", em
dashes, formulaic transitions, British spellings, "Figure" instead of "Fig." and
"equation (n)" instead of "Eq. (n)".

## Submission

- Submit `build/PPEECS_paper.pdf` and its Word source `build/PPEECS_paper.docx`, and the
  supplement as a separate file.
- After acceptance, upload each figure separately from `figures/` (vector PDF, or PNG).
- The PDF is made with LibreOffice, where Liberation Serif stands in for Times New Roman
  with identical metrics. Exporting the `.docx` to PDF from Microsoft Word gives the
  journal's exact fonts and equation rendering, with the same page breaks.
