# ICMMDU 2026 version

Conference: 1st International Conference on Machine Intelligence, Modeling, Digitalization
and Ubiquity (ICMMDU-2026), proceedings in Springer Nature / Atlantis Press "Advances in
Intelligent Systems Research". Word submission on the Springer proceedings template
(`../../icmmdu-conf-paper/splnproc2311.docm`), at least 10 pages, no upper limit stated.

`paper.md` is the full paper: the PPEECS text (`../ppeecs/paper.md`) with its supplement
merged in, plus two additions computed from the same results:

- the audit-size figure and the remediation table sit in the results (Sections 5.3, 5.6);
- the dashboard views are Figs. 6 and 7 (the PPEECS screenshot split at its panel line);
- the RELP code mapping is Appendix A;
- new: Table 7 (real drift by dataset and model family) and Section 5.8 with Table 10
  (wall-clock time per window, summed over the stages of Section 3).

Title is the PPEECS title (reliability analysis is included in full). Headings are in title
case and references in the LNCS style of the template. Floats sit after the sentence that
first mentions them, on the same page or at the top of the next page when they do not fit.

Build (from the repository root):

    venv/bin/python examples/paper/build_icmmdu.py              # docx and PDF
    venv/bin/python examples/paper/build_icmmdu.py --figures    # redraw Fig. 5 first

Output: `build/ICMMDU_paper.docx` (the submission file) and `build/ICMMDU_paper.pdf`.
