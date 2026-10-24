# ICMMDU 2026 version

Conference: 1st International Conference on Machine Intelligence, Modeling, Digitalization
and Ubiquity (ICMMDU-2026), proceedings in Springer Nature / Atlantis Press "Advances in
Intelligent Systems Research". Word submission on the Springer proceedings template
(`../../icmmdu-conf-paper/splnproc2311.docm`), at least 10 pages, no upper limit stated.

`paper.md` is the PPEECS text (`../ppeecs/paper.md`) with the most useful parts of its
supplement brought in, kept below 20 pages so that it stays a conference-length paper:

- the audit-size result (Section 5.3) and the remediation triage results (Section 5.6), as text;
- Section 5.7 on the wall-clock time per window, summed over the stages of Section 3.

Left out for length: the dashboard views, the RELP code mapping and the detector, estimator,
mechanism, remediation and runtime tables; their key numbers are quoted in the text.

Title is the PPEECS title (reliability analysis is included in full). Headings are in title
case and references in the LNCS style of the template. Floats sit after the sentence that
first mentions them, on the same page as that mention.

Build (from the repository root):

    venv/bin/python examples/paper/build_icmmdu.py              # docx and PDF
    venv/bin/python examples/paper/build_icmmdu.py --figures    # redraw Fig. 4 (timelines) first

Output: `build/ICMMDU_paper.docx` (the submission file) and `build/ICMMDU_paper.pdf`.
