# DACS 2026 conference version

This folder holds the version of the paper for the 9th International Conference on
Data Analytics and Cyber Security (DACS 2026), published by Springer in Lecture Notes in
Electrical Engineering. The conference allows at most 12 pages in the standard Springer
format, using the Springer Nature LaTeX template in `../dacs-conf-paper/` (`sn-jnl`,
reference style `sn-mathphys-num`).

`paper.md` is the PPEECS text (`../ppeecs/paper.md`) shortened to 12 pages by removing
whole parts: the positioning, datasets, mechanism, detector, estimator and ACS Income
tables, the confusion and timeline figures, root cause analysis, the reliability and
triage stages (Fig. 1 still shows them; the text says they are not evaluated here), the
ablations and several detail sentences. The remaining sentences are unchanged apart
from a few joins (an abbreviation spelled out where it is now first used, a shortened
sentence). There is no supplement.

| File | Content |
|---|---|
| `paper.md` | source text |
| `build/DACS_paper.tex` | generated LaTeX on the Springer template |
| `build/DACS_paper.pdf` | the paper (12 pages) |
| `build/references.bib` | the PPEECS references; proceedings and journal entries without the full-text URLs |
| `build/figures/` | Fig. 1 and Fig. 2 as vector PDF |
| `build/sn-jnl.cls`, `build/sn-mathphys-num.bst` | template files, copied so the folder compiles on its own |

## Build

From the repository root:

```
python examples/paper/build_dacs.py
```

It needs tectonic (`TECTONIC=...`) for the PDF and fails if the paper exceeds 12 pages
or a table or figure is not on the page of its first mention. `build/` also compiles
with pdflatex and bibtex, for example on Overleaf.
