# DSISys 2026 conference version

The version of the paper for DSISys 2026. The conference asks for the Springer Word
template, exactly 12 pages including figures, tables and references (papers of 4 to 11
pages are not accepted), numbered references and double-blind review. Guidelines:
`../../dsis-conf-paper/instructions.txt`.

The conference's "template" (`../../dsis-conf-paper/springer-template-DSISys2026.docx`)
is Springer's *Guidelines for Authors of Proceedings* converted to Word, without usable
styles. The paper is therefore written on the official Springer LNCS Word template
(`../../icmmdu-conf-paper/splnproc2311.docm`), which is the layout those guidelines
describe: Times, heading sizes as in their Table 1, 9 pt captions (figures below,
tables above), numbered citations, keywords capitalized and separated by middots.

`paper.md` has the same text as the E2A version (`../e2a/paper.md`, see its README).
The only layout difference is the width of Fig. 1 (100 mm here, 81.6 mm in E2A), which
makes up for the shorter anonymous title block so that Fig. 2 stays on the page of its
first mention.

| File | Content |
|---|---|
| `paper.md` | source text, with the authors (used for the camera-ready version) |
| `build/DSISys_paper_anonymous.docx` | the submission file (12 pages): no author names, affiliation or e-mail in the text, running heads or file properties |
| `build/DSISys_paper_anonymous.pdf` | PDF made with LibreOffice, for checking the layout |
| `build/DSISys_paper.docx/.pdf` | the same paper with the authors, for the camera-ready version |
| `figures/Fig04.{pdf,png}` | accuracy timelines, one row of four panels at 122 mm |

## Build

    python examples/paper/build_springer12.py dsisys            # anonymous submission
    python examples/paper/build_springer12.py dsisys --named    # with the authors

The build fails if the paper is not exactly 12 pages, a float is not on the page of
its first mention, or (anonymous build) an author name, the institute or the e-mail
domain appears anywhere in the file.
