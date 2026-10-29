# Capstone Project II black book

The project report ("black book") for Capstone Project II, Group 39, AI, Deep Learning & DWH
Mining, mentor Sanjay Mirchandani. The output follows the department's file naming rule
GroupNo-DomainName-MentorName:

| File | Content |
|---|---|
| `39-AIDeepLearningDWHMining-Sanjay.docx` | the report, on the department template (submit this) |
| `39-AIDeepLearningDWHMining-Sanjay.pdf` | PDF made with LibreOffice, for checking the layout |
| `Modified Capstone_Project_II_..._2026-27.docx` | the department template (styles, header, footer, logo, front-page wording) |
| `chapters/*.md` | the text: front matter and Chapters 1 to 8, references, appendix |
| `figures/` | diagrams, Gantt chart, dashboard screenshots and the paper's result figures |
| `references.bib` | references (PPEECS and AGH lists, the patents and the sustainability sources) |
| `evidence/pytest-2026-10-30.txt` | the test run quoted in Chapter 6 |
| `build_blackbook.py`, `omml.py` | build of the .docx and .pdf; LaTeX-to-Word equations |
| `make_figures.py`, `capture_screens.py` | figures and dashboard screenshots |

## Build

From the repository root:

```
python paper/black-book/make_figures.py            # diagrams, Gantt chart, paper figures
python paper/black-book/make_figures.py --screens  # screenshots; needs the dashboard on 127.0.0.1:8599
python paper/black-book/build_blackbook.py         # .docx and .pdf
```

The text uses the Markdown dialect of the paper builds (`examples/paper/build_ppeecs.py`):
`\res{key}` for every number (from `paper/generated/results.tex`, plus test counts, run
times and energy computed in the build), `[@key]` citations (IEEE style, numbered in order
of citation), `@fig:`, `@tab:`, `@eq:`, `@alg:`, `@sec:` and `@ch:` cross-references,
fenced algorithms and `[[...]]` placeholders, which print highlighted in yellow.

The build keeps the template's styles, header and logo, writes the title page, certificate,
approval and declaration with the template's wording, numbers figures, tables and equations
by chapter, and fills the table of contents and the lists of figures and tables (Word
fields) with the page numbers of the rendering. It fails when a figure, table, equation or
algorithm is never referenced, and it lints the text (comma before "and", em dashes, stock
words, British spelling). In Word, select all and press F9 to refresh the contents and lists
after editing.

Placeholders still to fill are listed at the end of every build (roll numbers, mentor
designation, review dates, publication status, scans for the appendix).
