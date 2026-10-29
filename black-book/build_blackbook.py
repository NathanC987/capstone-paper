"""Build the Capstone Project II black book on the department template.

The template (Modified Capstone_Project_II_26CMCP71_Blackbook_Template_SEM_VII_2026-27.docx)
gives the page sequence, the wording of the front pages, the header and footer, the
VESIT logo and the formatting rules: Times New Roman, chapter headings 20 pt bold,
sections 16 pt bold, subsections 14 pt bold, body 12 pt justified at 1.5 line spacing,
figures and tables numbered by chapter. This script keeps the template's package
(styles, theme, header, footer, logo) and writes a new document body:

    title page | certificate, approval, declaration, acknowledgement, course outcomes,
    contents, lists, abbreviations, abstract (roman page numbers) |
    chapters 1 to 8, references, appendix (arabic page numbers)

The text lives in chapters/*.md, in the Markdown dialect of the paper builds
(examples/paper/build_ppeecs.py) extended with chapters, bullet lists, algorithms and
[[...]] placeholders. Every number is a \\res{key} from paper/generated/results.tex.
The table of contents and the lists of figures and tables are Word fields, filled
with the page numbers of the LibreOffice rendering (two passes), so they read right
in the PDF and Word can update them.

Run from anywhere:

    python paper/black-book/build_blackbook.py
"""

from __future__ import annotations

import datetime as dt
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BB = Path(__file__).resolve().parent
REPO = BB.parents[1]
sys.path.insert(0, str(REPO / "examples" / "paper"))
sys.path.insert(0, str(BB))
from build_ppeecs import (DOLLAR, GENERATORS, MATH_CACHE, TRANSFORMS, Block, Table, column_widths,  # noqa: E402
                          esc, load_results, parse_attrs, parse_bib, parse_pipe_table, parse_tabular, pdf_pages,
                          plain_text, png_size, tex_unicode, to_pdf)
from omml import to_omml  # noqa: E402

TEMPLATE = BB / "Modified Capstone_Project_II_26CMCP71_Blackbook_Template_SEM_VII_2026-27.docx"
CHAPTERS = BB / "chapters"
FIGS = BB / "figures"
BIB = BB / "references.bib"
NAME = "39-AIDeepLearningDWHMining-Sanjay"
OUT = BB / f"{NAME}.docx"

TEXT_W = 9360                      # twips: Letter page, 1 inch margins (template)
MAIN_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
REL_IMAGE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
REL_LINK = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
REL_FOOTER = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"
FOOTER_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"
LOGO = "media/image1.png"          # VESIT logo in the template package
TNR = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman"/>'
HEAD_FILL = "D9E2F3"               # header row shading, as in the template's tables
PLACEHOLDER = re.compile(r"\[\[(.+?)\]\]")


# --------------------------------------------------------------------------- #
# small XML helpers

def run(text: str, rpr: str = "") -> str:
    if not text:
        return ""
    parts = text.split("\t")
    props = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
    body = "<w:tab/>".join(f'<w:t xml:space="preserve">{esc(p)}</w:t>' for p in parts)
    return f"<w:r>{props}{body}</w:r>"


def para(style: str, body: str, ppr: str = "") -> str:
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{ppr}</w:pPr>{body}</w:p>'


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def roman(n: int) -> str:
    vals = [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"), (50, "l"), (40, "xl"),
            (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


# --------------------------------------------------------------------------- #
# styles: the template's rules made into Word styles

def style(sid: str, name: str, ppr: str, rpr: str, kind: str = "paragraph", based: str = "Normal",
          extra: str = "") -> str:
    base = f'<w:basedOn w:val="{based}"/>' if based else ""
    return (f'<w:style w:type="{kind}" w:customStyle="1" w:styleId="{sid}"><w:name w:val="{name}"/>{base}{extra}'
            f'<w:qFormat/><w:pPr>{ppr}</w:pPr><w:rPr>{rpr}</w:rPr></w:style>')


def heading_style(level: int, size: int, bold: bool, before: int, after: int, extra_ppr: str = "") -> str:
    b = "<w:b/><w:bCs/>" if bold else '<w:b w:val="0"/><w:bCs w:val="0"/>'
    return (f'<w:style w:type="paragraph" w:styleId="Heading{level}"><w:name w:val="heading {level}"/>'
            f'<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="9"/><w:qFormat/>'
            f'<w:pPr><w:keepNext/><w:keepLines/>{extra_ppr}<w:spacing w:before="{before}" w:after="{after}" '
            f'w:line="276" w:lineRule="auto"/><w:jc w:val="left"/><w:outlineLvl w:val="{level - 1}"/></w:pPr>'
            f'<w:rPr>{TNR}{b}<w:color w:val="000000"/><w:sz w:val="{2 * size}"/><w:szCs w:val="{2 * size}"/></w:rPr>'
            "</w:style>")


def toc_style(level: int) -> str:
    ind = (level - 1) * 360
    bold = "<w:b/><w:bCs/>" if level == 1 else ""
    return (f'<w:style w:type="paragraph" w:styleId="TOC{level}"><w:name w:val="toc {level}"/>'
            f'<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="39"/>'
            f'<w:pPr><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="{TEXT_W}"/></w:tabs>'
            f'<w:spacing w:before="{60 if level == 1 else 0}" w:after="40" w:line="300" w:lineRule="auto"/>'
            f'<w:ind w:left="{ind}" w:right="400" w:hanging="0"/><w:jc w:val="left"/></w:pPr><w:rPr>{TNR}{bold}'
            '<w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>')


def styles_xml(src: str) -> str:
    """The template's styles with Normal, the headings and the TOC levels set to its formatting rules,
    plus the paragraph styles of the book."""
    for sid in ("Normal", "Heading1", "Heading2", "Heading3", "Heading4", "TOC1", "TOC2", "TOC3", "Caption"):
        src = re.sub(rf'<w:style [^>]*w:styleId="{sid}"[^>]*>.*?</w:style>', "", src, flags=re.S)
    sz = '<w:sz w:val="24"/><w:szCs w:val="24"/>'
    normal = ('<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/>'
              '<w:pPr><w:widowControl/><w:spacing w:before="0" w:after="120" w:line="360" w:lineRule="auto"/>'
              f'<w:jc w:val="both"/></w:pPr><w:rPr>{TNR}<w:color w:val="000000"/>{sz}<w:lang w:val="en-US"/>'
              "</w:rPr></w:style>")
    single = '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
    ours = [
        normal,
        heading_style(1, 20, True, 0, 360, "<w:pageBreakBefore/>"),
        heading_style(2, 16, True, 280, 120),
        heading_style(3, 14, True, 220, 100),
        heading_style(4, 14, False, 180, 80),
        toc_style(1), toc_style(2), toc_style(3),
        style("Caption", "caption", '<w:keepLines/><w:spacing w:before="60" w:after="240" w:line="276" w:lineRule="auto"/>'
              '<w:jc w:val="center"/>', f"{TNR}<w:sz w:val=\"22\"/><w:szCs w:val=\"22\"/>"),
        style("FigureCaption", "Figure Caption", '<w:keepLines/><w:spacing w:before="60" w:after="240" w:line="276" '
              'w:lineRule="auto"/><w:jc w:val="center"/>', f'{TNR}<w:sz w:val="22"/><w:szCs w:val="22"/>'),
        style("TableCaption", "Table Caption", '<w:keepNext/><w:keepLines/><w:spacing w:before="200" w:after="100" '
              'w:line="276" w:lineRule="auto"/><w:jc w:val="center"/>', f'{TNR}<w:sz w:val="22"/><w:szCs w:val="22"/>'),
        style("AlgCaption", "Algorithm Caption", '<w:keepNext/><w:keepLines/><w:spacing w:before="200" w:after="60" '
              'w:line="276" w:lineRule="auto"/><w:jc w:val="left"/>', f'{TNR}<w:b/><w:bCs/>{sz}'),
        style("FigureBody", "Figure", f'<w:keepNext/><w:spacing w:before="200" w:after="60" w:line="240" '
              'w:lineRule="auto"/><w:jc w:val="center"/>', ""),
        style("TableText", "Table Text", f"{single}<w:jc w:val=\"left\"/>",
              f'{TNR}<w:sz w:val="20"/><w:szCs w:val="20"/>'),
        style("Code", "Pseudocode", f'<w:keepLines/>{single}<w:ind w:left="240"/><w:jc w:val="left"/>',
              '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/><w:sz w:val="19"/>'
              '<w:szCs w:val="19"/>'),
        style("ListItem", "List Item", '<w:spacing w:before="0" w:after="60" w:line="360" w:lineRule="auto"/>'
              '<w:jc w:val="both"/>', ""),
        style("Equation", "Equation", f'<w:tabs><w:tab w:val="center" w:pos="{TEXT_W // 2}"/>'
              f'<w:tab w:val="right" w:pos="{TEXT_W}"/></w:tabs><w:spacing w:before="120" w:after="120" '
              'w:line="276" w:lineRule="auto"/><w:jc w:val="left"/>', ""),
        style("FrontTitle", "Front Title", '<w:keepNext/><w:spacing w:before="120" w:after="240" w:line="276" '
              'w:lineRule="auto"/><w:jc w:val="center"/>', f'{TNR}<w:b/><w:bCs/><w:sz w:val="36"/><w:szCs w:val="36"/>'),
        style("Center", "Centered", '<w:spacing w:before="0" w:after="60" w:line="276" w:lineRule="auto"/>'
              '<w:jc w:val="center"/>', ""),
        style("Signature", "Signature Line", '<w:spacing w:before="0" w:after="0" w:line="276" w:lineRule="auto"/>'
              '<w:jc w:val="left"/>', ""),
        style("Reference", "Reference Item", '<w:spacing w:before="0" w:after="100" w:line="276" w:lineRule="auto"/>'
              '<w:ind w:left="567" w:hanging="567"/><w:jc w:val="left"/>', ""),
    ]
    return src.replace("</w:styles>", "".join(ours) + "</w:styles>")


# --------------------------------------------------------------------------- #
# source parsing: the paper dialect plus chapters, bullets, algorithms

INLINE = re.compile(
    r"(?P<math>\$[^$]+\$)|(?P<bold>\*\*.+?\*\*)|(?P<ital>\*[^*\s][^*]*?\*)|(?P<code>`[^`]+`)|(?P<cite>\[@[^\]]+\])"
    r"|(?P<hold>\[\[.+?\]\])|(?P<ref>@(?:ch|sec|fig|tab|eq|alg):[A-Za-z0-9_-]+)|(?P<url><https?://[^>]+>)")


def parse_chapter(path: Path) -> Tuple[Dict[str, List[str]], List[Block]]:
    text = path.read_text()
    front: Dict[str, List[str]] = {}
    if text.startswith("---"):
        head, text = text[3:].split("\n---", 1)
        for line in head.strip().splitlines():
            k, v = line.split(":", 1)
            front.setdefault(k.strip(), []).append(v.strip())
    # fenced algorithms keep their blank lines and indentation
    fences: List[str] = []

    def keep(m: "re.Match[str]") -> str:
        fences.append(m.group(2))
        return f"\n\n\x00ALG{len(fences) - 1} {m.group(1)}\n\n"
    text = re.sub(r"```([^\n]*)\n(.*?)\n```", keep, text, flags=re.S)
    text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("%"))
    blocks: List[Block] = []
    for chunk in re.split(r"\n\s*\n", text.strip()):
        chunk = chunk.strip()
        if not chunk:
            continue
        if chunk.startswith("\x00ALG"):
            m = re.match(r"\x00ALG(\d+)\s*(.*?)\s*(?:\{([^}]*)\})?$", chunk)
            b = Block("alg", m.group(2), attrs=parse_attrs(m.group(3)))
            b.lines = fences[int(m.group(1))].splitlines()
            blocks.append(b)
        elif chunk == "\\newpage":
            blocks.append(Block("pagebreak"))
        elif chunk.startswith("#"):
            m = re.match(r"(#{1,4})\s+(.*?)\s*(?:\{([^}]*)\})?$", chunk)
            blocks.append(Block("heading", m.group(2), len(m.group(1)), parse_attrs(m.group(3))))
        elif chunk.startswith("$$"):
            m = re.match(r"\$\$(.*?)\$\$\s*([.,;]?)\s*(?:\{([^}]*)\})?$", chunk, re.S)
            b = Block("eq", " ".join(m.group(1).split()), attrs=parse_attrs(m.group(3)))
            b.attrs["punct"] = m.group(2)
            blocks.append(b)
        elif chunk.startswith("!["):
            m = re.match(r"!\[(.*)\]\((.*?)\)\{([^}]*)\}$", chunk, re.S)
            b = Block("fig", " ".join(m.group(1).split()), attrs=parse_attrs(m.group(3)))
            b.attrs["file"] = m.group(2)
            blocks.append(b)
        elif chunk.startswith("Table:"):
            lines = chunk.splitlines()
            m = re.match(r"Table:\s*(.*?)\s*\{([^}]*)\}$", lines[0])
            blocks.append(Block("table", m.group(1), attrs=parse_attrs(m.group(2)), lines=lines[1:]))
        elif re.match(r"\d+\.\s", chunk):
            items = re.split(r"\n(?=\d+\.\s)", chunk)
            blocks.append(Block("list", lines=[" ".join(re.sub(r"^\d+\.\s+", "", i).split()) for i in items]))
        elif chunk.startswith("- "):
            items = re.split(r"\n(?=- )", chunk)
            blocks.append(Block("bullets", lines=[" ".join(i[2:].split()) for i in items]))
        else:
            blocks.append(Block("para", " ".join(chunk.split())))
    return front, blocks


# --------------------------------------------------------------------------- #
# values this report adds to results.tex: test counts, run times, energy, code size

STAGES = ("ks", "psi", "mmd", "conf", "bbsd", "dc", "diagnosis", "reliability")   # timed stages of a window
CPU_WATTS = 181          # rated maximum turbo power of the Intel Core i5-14600K (Intel specifications)
GRID_KG_PER_KWH = 0.727  # Indian grid, weighted average 2023-24 (CEA CO2 Baseline Database v20.0, Table S)
TARIFF_INR = 10          # assumed electricity price per kWh
TEST_LOG = BB / "evidence" / "pytest-2026-10-30.txt"


def derived_results(res: Dict[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    times: Dict[Tuple[str, str], float] = {}
    for key, val in res.items():
        m = re.fullmatch(r"((?:inc|emp|gas|clr)(?:-hgb)?)-(\w+)-time-(\w+)", key)
        if m and m.group(3) in STAGES:
            try:
                times[(m.group(1), m.group(2))] = times.get((m.group(1), m.group(2)), 0.0) + float(val)
            except ValueError:
                continue
    total_s = sum(times.values())
    out["bb-time-max"] = f"{max(times.values()):.0f}"
    out["bb-time-total-min"] = f"{total_s / 60:.1f}"
    out["bb-nwindows-timed"] = str(len(times))
    kwh = (total_s / 3600 + float(res["bench-total-hours"])) * CPU_WATTS / 1000
    out["bb-energy-total-kwh"] = f"{kwh:.2f}"
    out["bb-energy-total-inr"] = f"{kwh * TARIFF_INR:.0f}"
    out["bb-co2-total-kg"] = f"{kwh * GRID_KG_PER_KWH:.2f}"
    log = TEST_LOG.read_text()
    m = re.search(r"=+ (\d+) passed in ([\d.]+)s", log)
    if not m or re.search(r"\d+ failed", log):
        raise ValueError(f"{TEST_LOG.name}: not a clean test run")
    out["bb-tests-total"], out["bb-tests-seconds"] = m.group(1), f"{float(m.group(2)):.0f}"
    passed = re.findall(r"^PASSED tests/(\S+?)::", log, re.M)
    out["bb-tests-unit"] = str(sum(t.startswith("unit/") for t in passed))
    out["bb-tests-integration"] = str(sum(t.startswith("integration/") for t in passed))
    out["bb-tests-smoke"] = str(sum(t.startswith("test_smoke") for t in passed))
    fwer = __import__("json").loads((REPO / "outputs" / "fwer_check.json").read_text())
    out["bb-fwer-reps"] = f"{fwer['replicates']:,}"
    src = [p for p in (REPO / "src" / "drift_autopsy").rglob("*.py")]
    out["bb-src-modules"] = str(sum(p.name != "__init__.py" for p in src))
    out["bb-src-lines"] = f"{sum(len(p.read_text().splitlines()) for p in src):,}"
    out["bb-src-packages"] = str(sum(1 for d in (REPO / "src" / "drift_autopsy").iterdir()
                                     if d.is_dir() and (d / "__init__.py").exists()))
    return out


# --------------------------------------------------------------------------- #
# references in IEEE style

MONTHS = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."]


def ieee_name(name: str) -> str:
    name = name.strip()
    if name.startswith("{") and name.endswith("}"):
        return tex_unicode(name[1:-1])
    if "," in name:
        last, first = (p.strip() for p in name.split(",", 1))
    else:
        parts = name.split()
        last, first = parts[-1], " ".join(parts[:-1])

    def ini(p: str) -> str:
        if "-" in p:
            return "-".join(ini(q) for q in p.split("-") if q)
        return p if (p.endswith(".") and len(p) <= 2) else p[0] + "."
    first = " ".join(ini(p) for p in tex_unicode(first).split())
    return f"{first} {tex_unicode(last)}".strip()


def ieee_authors(field_: str) -> str:
    names = [ieee_name(a) for a in re.split(r"\s+and\s+", field_)]
    if len(names) > 6:
        return names[0] + " et al."
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + ", and " + names[-1]


def ieee_date(text: str) -> str:
    """2026-10-30 or 30 October 2026 as Oct. 30, 2026."""
    when = None
    for fmt in ("%Y-%m-%d", "%d %B %Y", "%B %d, %Y"):
        try:
            when = dt.datetime.strptime(text.strip(), fmt)
            break
        except ValueError:
            continue
    if when is None:
        raise ValueError(f"unknown date format: {text}")
    return f"{MONTHS[when.month - 1]} {when.day}, {when.year}"


def ieee_reference(e: Dict[str, str]) -> List[Tuple[str, str, Optional[str]]]:
    """One reference as (text, style, link) segments; style is '' or 'i' (italic)."""
    t = e["_type"]
    title = tex_unicode(e.get("title", "")).replace("{", "").replace("}", "")
    year = e.get("year", "")
    authors = ieee_authors(e["author"]) if e.get("author") else ""
    pages = tex_unicode(e.get("pages", "")).replace("--", "\u2013")
    segs: List[Tuple[str, str, Optional[str]]] = []
    if t == "article":
        vol = f", vol. {e['volume']}" if e.get("volume") else ""
        num = f", no. {e['number']}" if e.get("number") else ""
        pp = f", pp. {pages}" if pages else (f", Art. no. {e['eid']}" if e.get("eid") else "")
        segs += [(f"{authors}, \u201c{title},\u201d ", "", None), (tex_unicode(e["journal"]), "i", None),
                 (f"{vol}{num}{pp}, {year}", "", None)]
    elif t == "inproceedings":
        pp = f", pp. {pages}" if pages else ""
        segs += [(f"{authors}, \u201c{title},\u201d in ", "", None),
                 (tex_unicode(e["booktitle"]).replace("{", "").replace("}", ""), "i", None), (f", {year}{pp}", "", None)]
    elif t == "book":
        where = f"{tex_unicode(e['address'])}: " if e.get("address") else ""
        if not authors and e.get("editor"):
            authors = ieee_authors(e["editor"]) + ", Eds."
        segs += [(f"{authors}, " if authors else "", "", None), (title, "i", None),
                 (f". {where}{tex_unicode(e.get('publisher', ''))}, {year}", "", None)]
    elif t in ("techreport", "phdthesis"):
        inst = tex_unicode(e.get("institution", e.get("school", "")))
        kind = "Ph.D. dissertation" if t == "phdthesis" else f"Tech. Rep. {e.get('number', '')}".strip()
        segs += [(f"{authors}, \u201c{title},\u201d {inst}, {kind}, {year}", "", None)]
    elif t == "patent":
        segs += [(f"{authors}, \u201c{title},\u201d {e['country']} Patent {e['number']}, "
                  f"{e.get('note', '')}{ieee_date(e['date'])}", "", None)]
    elif t in ("online", "misc"):
        org = authors or tex_unicode(e.get("organization", ""))
        where = f"{tex_unicode(e['howpublished'])}, " if e.get("howpublished") else ""
        segs += [(f"{org}, \u201c{title},\u201d {where}{year}" if org else f"\u201c{title},\u201d {where}{year}", "", None)]
    else:
        raise ValueError(f"unsupported entry type {t}")
    if e.get("doi"):
        url = f"https://doi.org/{e['doi']}"
        segs += [(", doi: ", "", None), (e["doi"], "", url), (".", "", None)]
    elif e.get("url"):
        acc = f" (accessed {ieee_date(e['urldate'])})" if e.get("urldate") else ""
        segs += [(". [Online]. Available: ", "", None), (e["url"], "", e["url"]), (acc + ".", "", None)]
    else:
        segs.append((".", "", None))
    return segs


# --------------------------------------------------------------------------- #
# the document

@dataclass
class Entry:                        # a heading or caption that goes in the contents or a list
    kind: str                       # toc1, toc2, toc3, fig, tab
    text: str
    key: str                        # text to find on the rendered page
    page: str = ""


@dataclass
class Book:
    res: Dict[str, str]
    bib: Dict[str, Dict[str, str]]
    pages: Dict[str, str] = field(default_factory=dict)       # entry key -> printed page number

    def __post_init__(self) -> None:
        self.math_cache = __import__("json").loads(MATH_CACHE.read_text())
        self.front, self.front_blocks = parse_chapter(CHAPTERS / "00-front.md")
        self.chapters = [parse_chapter(p)[1] for p in sorted(CHAPTERS.glob("[0-9][0-9]-*.md"))
                         if not p.name.startswith("00-")]
        self.number()

    # ---- numbering -------------------------------------------------------- #
    def number(self) -> None:
        self.labels: Dict[str, str] = {}
        ch = 0
        for blocks in self.chapters:
            sec = [0, 0, 0, 0]
            counts = {"fig": 0, "tab": 0, "eq": 0, "alg": 0}
            for b in blocks:
                if b.kind == "heading":
                    if "unnumbered" in b.attrs:
                        b.number = ""
                    elif b.level == 1:
                        ch += 1
                        sec = [ch, 0, 0, 0]
                        counts = dict.fromkeys(counts, 0)
                        b.number = str(ch)
                    elif b.level <= 3:
                        sec[b.level - 1] += 1
                        for j in range(b.level, 4):
                            sec[j] = 0
                        b.number = ".".join(str(n) for n in sec[:b.level])
                elif b.kind in ("fig", "table", "eq", "alg"):
                    kind = "tab" if b.kind == "table" else b.kind
                    counts[kind] += 1
                    b.number = f"{ch}.{counts[kind]}" if ch else f"A.{counts[kind]}"
                if "id" in b.attrs:
                    if b.attrs["id"] in self.labels:
                        raise ValueError(f"duplicate label {b.attrs['id']}")
                    self.labels[b.attrs["id"]] = b.number

    # ---- inline text ------------------------------------------------------ #
    def substitute(self, text: str) -> str:
        def res(m: "re.Match[str]") -> str:
            if m.group(1) not in self.res:
                raise KeyError(f"undefined result key {m.group(1)}")
            self.used_res.add(m.group(1))
            return self.res[m.group(1)]
        text = text.replace("\\$", DOLLAR)
        text = re.sub(r"\\res\{([^}]+)\}", res, text)
        return re.sub(r'"([^"]*)"', "\u201c\\1\u201d", text)

    def cite(self, group: str) -> str:
        nums = []
        for k in (k.strip().lstrip("@") for k in group[1:-1].split(";")):
            if k not in self.bib:
                raise KeyError(f"unknown citation {k}")
            if k not in self.cites:
                self.cites.append(k)
            nums.append(self.cites.index(k) + 1)
        nums = sorted(set(nums))
        parts, i = [], 0
        while i < len(nums):
            j = i
            while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
                j += 1
            parts.append(f"[{nums[i]}]\u2013[{nums[j]}]" if j - i >= 2 else ", ".join(f"[{n}]" for n in nums[i:j + 1]))
            i = j + 1
        return ", ".join(parts)

    def math(self, latex: str, display: bool = False) -> str:
        key = ("D:" if display else "I:") + latex.strip()
        if key in self.math_cache:
            return self.math_cache[key]
        return to_omml(latex)

    def inline(self, text: str, rpr: str = "", subst: bool = True) -> str:
        if subst:
            text = self.substitute(text)
        out, pos = [], 0
        for m in INLINE.finditer(text):
            out.append(run(plain_text(text[pos:m.start()]), rpr))
            tok = m.group(0)
            if m.group("math"):
                out.append(self.math(tok[1:-1].replace(DOLLAR, "\\$")))
            elif m.group("bold"):
                out.append(self.inline(tok[2:-2], rpr + "<w:b/><w:bCs/>", False))
            elif m.group("ital"):
                out.append(self.inline(tok[1:-1], rpr + "<w:i/><w:iCs/>", False))
            elif m.group("code"):
                out.append(run(tok[1:-1], rpr + '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" '
                               'w:cs="Courier New"/><w:sz w:val="21"/><w:szCs w:val="21"/>'))
            elif m.group("cite"):
                out.append(run(self.cite(tok), rpr))
            elif m.group("hold"):
                self.placeholders.append(tok[2:-2])
                out.append(run(tok[2:-2], rpr + '<w:highlight w:val="yellow"/>'))
            elif m.group("url"):
                out.append(self.link(tok[1:-1], tok[1:-1], rpr))
            else:
                label = tok[1:]
                if label not in self.labels:
                    raise KeyError(f"unknown label {label}")
                self.refs.add(label)
                out.append(run(self.labels[label], rpr))
            pos = m.end()
        out.append(run(plain_text(text[pos:]), rpr))
        return "".join(out)

    def link(self, url: str, text: str, rpr: str = "") -> str:
        rid = f"rIdL{len(self.rels) + 1}"
        self.rels.append((rid, REL_LINK, url, True))
        return (f'<w:hyperlink r:id="{rid}" w:history="1"><w:r><w:rPr>{rpr}<w:color w:val="1F3B73"/></w:rPr>'
                f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:hyperlink>')

    # ---- figures and tables ---------------------------------------------- #
    def image(self, path: Path, width_mm: float, name: str) -> str:
        w_px, h_px = png_size(path)
        cx = int(width_mm * 36000)
        cy = int(cx * h_px / w_px)
        n = len(self.media) + 1
        rid = f"rIdI{n}"
        target = f"media/bb{n}{path.suffix}"
        self.media.append((target, path))
        self.rels.append((rid, REL_IMAGE, target, False))
        a = "http://schemas.openxmlformats.org/drawingml/2006/main"
        pic = "http://schemas.openxmlformats.org/drawingml/2006/picture"
        return (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
                f'<wp:docPr id="{1000 + n}" name="{esc(name)}" descr="{esc(name)}"/>'
                f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="{a}" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
                f'<a:graphic xmlns:a="{a}"><a:graphicData uri="{pic}"><pic:pic xmlns:pic="{pic}">'
                f'<pic:nvPicPr><pic:cNvPr id="{1000 + n}" name="{esc(path.name)}"/><pic:cNvPicPr/></pic:nvPicPr>'
                f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
                "</wp:inline></w:drawing></w:r>")

    def caption(self, kind: str, b: Block, style_: str) -> str:
        tag = {"fig": "Fig.", "tab": "Table", "alg": "Algorithm"}[kind]
        text = b.text.rstrip(".")
        if kind in ("fig", "tab"):
            shown = self.plain(text)
            short = re.split(r"(?<=[a-z0-9)])[.;] ", shown)[0]      # the lists carry the first sentence only
            self.entries.append(Entry(kind, f"{tag} {b.number}: {short}", f"{tag} {b.number}: " + " ".join(shown.split()[:3])))
        jc = '<w:jc w:val="both"/>' if len(text) > 120 and kind == "fig" else ""
        return para(style_, run(f"{tag} {b.number}: ", "<w:b/><w:bCs/>") + self.inline(text), jc)

    def plain(self, text: str) -> str:
        """Caption text without markup, for the lists of figures and tables."""
        text = self.substitute(text)
        text = re.sub(r"\[@[^\]]+\]", "", text)
        text = re.sub(r"\$([^$]*)\$", lambda m: re.sub(r"\\[a-z]+|[{}_^\\]", "", m.group(1)), text)
        text = re.sub(r"\*\*?([^*]+)\*\*?", r"\1", text)
        text = re.sub(r"@(?:ch|sec|fig|tab|eq|alg):[A-Za-z0-9_-]+", lambda m: self.labels[m.group(0)[1:]], text)
        return plain_text(" ".join(text.split())).replace(" ,", ",")

    def figure(self, b: Block) -> str:
        path = FIGS / b.attrs["file"]
        if not path.exists():
            raise FileNotFoundError(path)
        width = float(b.attrs.get("width", 150))
        return para("FigureBody", self.image(path, width, f"Figure {b.number}")) + self.caption("fig", b, "FigureCaption")

    def table(self, b: Block) -> str:
        src = b.lines
        gen = re.match(r"<<gen:(\w+)(?:\s+(\w+))?>>", src[0].strip()) if src else None
        code = re.match(r"<<code:(\w+)>>", src[0].strip()) if src else None
        if code:
            t = GENERATORS[code.group(1)]()
        elif gen:
            t = parse_tabular(gen.group(1))
            if gen.group(2):
                t = TRANSFORMS[gen.group(2)](t)
        else:
            t = parse_pipe_table(src)
        size = float(b.attrs.get("size", 10))
        out = self.caption("tab", b, "TableCaption") if b.number and "caption" not in b.attrs else ""
        rel = [float(x) for x in b.attrs["widths"].split(",")] if "widths" in b.attrs else None
        out += self.table_xml(t, size, rel, grid="grid" in b.attrs.get("style", "grid"))
        return out + '<w:p><w:pPr><w:spacing w:before="0" w:after="120" w:line="240" w:lineRule="auto"/></w:pPr></w:p>'

    def table_xml(self, t: Table, size: float, rel: Optional[List[float]] = None, grid: bool = True,
                  avail: int = TEXT_W - 100, shade: bool = True) -> str:
        ncol = len(t.aligns)
        half = int(round(2 * size))
        rpr = f'<w:sz w:val="{half}"/><w:szCs w:val="{half}"/>'
        if rel:
            if len(rel) != ncol:
                raise ValueError(f"widths give {len(rel)} columns, table has {ncol}")
            widths = [int(avail * r / sum(rel)) for r in rel]
        else:
            widths = [int(w * size / 8) for w in column_widths(t, int(avail * 8 / size))]
        grid_xml = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
        rows, last = [], len(t.rows) - 1
        for ri, r in enumerate(t.rows):
            head = ri < t.header_rows
            col, tcs = 0, []
            for c in r.cells:
                align = "center" if (c.span > 1 or head) else {"l": "left", "r": "right", "c": "center"}[t.aligns[col]]
                w = sum(widths[col:col + c.span])
                span = f'<w:gridSpan w:val="{c.span}"/>' if c.span > 1 else ""
                fill = f'<w:shd w:val="clear" w:color="auto" w:fill="{HEAD_FILL}"/>' if head and shade else ""
                text = re.sub(r"(\$[^$]*\$)|_", lambda m: m.group(1) or "_\u200b", c.text)
                body = self.inline(text, rpr + ("<w:b/><w:bCs/>" if head else ""))
                keep = "<w:keepNext/>" if ri < last and ri < 3 else ""
                tcs.append(f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{span}{fill}<w:vAlign w:val="center"/></w:tcPr>'
                           + para("TableText", body, f'{keep}<w:jc w:val="{align}"/>') + "</w:tc>")
                col += c.span
            if col != ncol:
                raise ValueError(f"table row {ri} has {col} columns, expected {ncol}")
            trpr = "<w:cantSplit/>" + ("<w:tblHeader/>" if head else "")
            rows.append(f"<w:tr><w:trPr>{trpr}</w:trPr>{''.join(tcs)}</w:tr>")
        line = '<w:{0} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        borders = "".join(line.format(s) for s in ("top", "left", "bottom", "right", "insideH", "insideV")) if grid else ""
        return (f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:jc w:val="center"/>'
                f'<w:tblBorders>{borders}</w:tblBorders><w:tblLayout w:type="fixed"/>'
                '<w:tblCellMar><w:top w:w="30" w:type="dxa"/><w:left w:w="80" w:type="dxa"/>'
                '<w:bottom w:w="30" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar>'
                f'<w:tblLook w:val="0000"/></w:tblPr><w:tblGrid>{grid_xml}</w:tblGrid>{"".join(rows)}</w:tbl>')

    def algorithm(self, b: Block) -> str:
        out = self.caption("alg", b, "AlgCaption")
        line = '<w:{0} w:val="single" w:sz="6" w:space="4" w:color="000000"/>'
        n = len(b.lines)
        for i, l in enumerate(b.lines):
            indent = len(l) - len(l.lstrip(" "))
            bdr = (line.format("top") if i == 0 else "") + (line.format("bottom") if i == n - 1 else "")
            keep = "<w:keepNext/>" if i < n - 1 else ""
            ppr = (f"{keep}<w:pBdr>{bdr}</w:pBdr>" if bdr else keep) + f'<w:ind w:left="{240 + indent * 110}"/>'
            out += para("Code", self.inline(l.strip(), '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" '
                                             'w:cs="Courier New"/>', subst=True) if l.strip() else "", ppr)
        return out + '<w:p><w:pPr><w:spacing w:before="0" w:after="120" w:line="240" w:lineRule="auto"/></w:pPr></w:p>'

    def equation(self, b: Block) -> str:
        body = ("<w:r><w:tab/></w:r>" + self.math(self.substitute(b.text), display=True)
                + run(b.attrs.get("punct", "")) + "<w:r><w:tab/></w:r>" + run(f"({b.number})"))
        return para("Equation", body)

    def lists(self, b: Block) -> str:
        if b.kind == "bullets":
            num = self.bullet_num
        else:
            self.list_nums.append(len(self.list_nums))
            num = 200 + self.list_nums[-1]
        return "".join(para("ListItem", self.inline(item), f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num}"/>'
                            '</w:numPr><w:ind w:left="567" w:hanging="340"/>') for item in b.lines)

    # ---- headings --------------------------------------------------------- #
    def heading(self, b: Block) -> str:
        text = self.plain(b.text)
        if b.level == 1:
            shown = f"CHAPTER {b.number}: {text.upper()}" if b.number else text.upper()
            self.entries.append(Entry("toc1", shown, shown))
            return para("Heading1", run(shown))
        shown = f"{b.number} {text}" if b.number else text
        if b.level <= 3:
            self.entries.append(Entry(f"toc{b.level}", shown, shown))
        return para(f"Heading{b.level}", self.inline(f"{b.number} {b.text}" if b.number else b.text))

    def chapter_body(self, blocks: List[Block]) -> str:
        out = []
        for b in blocks:
            if b.kind == "heading":
                if b.text == "References" and "unnumbered" in b.attrs:
                    out.append(self.heading(b) + self.references())
                else:
                    out.append(self.heading(b))
            elif b.kind == "para":
                out.append(para("Normal", self.inline(b.text.replace("\\noindent", "").strip())))
            elif b.kind in ("list", "bullets"):
                out.append(self.lists(b))
            elif b.kind == "eq":
                out.append(self.equation(b))
            elif b.kind == "fig":
                out.append(self.figure(b))
            elif b.kind == "table":
                out.append(self.table(b))
            elif b.kind == "alg":
                out.append(self.algorithm(b))
            elif b.kind == "pagebreak":
                out.append(page_break())
        return "".join(out)

    def references(self) -> str:
        out = []
        for i, k in enumerate(self.cites, 1):
            body = run(f"[{i}]\t")
            for text, sty, url in ieee_reference(self.bib[k]):
                rpr = "<w:i/><w:iCs/>" if sty == "i" else ""
                body += self.link(url, text, rpr) if url else run(text, rpr)
            out.append(para("Reference", body, '<w:tabs><w:tab w:val="left" w:pos="567"/></w:tabs>'))
        return "".join(out)

    # ---- front pages ------------------------------------------------------ #
    def institute_block(self) -> str:
        b = "<w:b/><w:bCs/>"
        return (para("Center", run("VIVEKANAND EDUCATION SOCIETY\u2019S INSTITUTE OF TECHNOLOGY", f'{b}<w:sz w:val="28"/>'))
                + para("Center", run("An Autonomous Institute Affiliated to the University of Mumbai", '<w:sz w:val="24"/>'))
                + para("Center", run("DEPARTMENT OF COMPUTER ENGINEERING", f'{b}<w:sz w:val="26"/>'),
                       '<w:spacing w:before="0" w:after="200"/>'))

    def logo(self, width_mm: float = 28) -> str:
        cx = int(width_mm * 36000)
        cy = int(cx * 325 / 220)
        n = 990
        a = "http://schemas.openxmlformats.org/drawingml/2006/main"
        pic = "http://schemas.openxmlformats.org/drawingml/2006/picture"
        self.logo_count += 1
        return para("Center", (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
                               f'<wp:docPr id="{n + self.logo_count}" name="VESIT logo" descr="VESIT logo"/>'
                               f'<a:graphic xmlns:a="{a}"><a:graphicData uri="{pic}"><pic:pic xmlns:pic="{pic}">'
                               f'<pic:nvPicPr><pic:cNvPr id="{n + self.logo_count}" name="logo.png"/><pic:cNvPicPr/></pic:nvPicPr>'
                               '<pic:blipFill><a:blip r:embed="rIdLogo"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                               f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                               '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData>'
                               "</a:graphic></wp:inline></w:drawing></w:r>"), '<w:spacing w:before="120" w:after="240"/>')

    def students(self) -> List[Tuple[str, str]]:
        return [tuple(p.strip() for p in s.split(";", 1)) for s in self.front["student"]]

    def mentor(self) -> str:
        return self.front["mentor"][0]

    def title_page(self) -> str:
        f = self.front
        b = "<w:b/><w:bCs/>"
        c = lambda text, rpr="", after=60: para("Center", self.inline(text, rpr), f'<w:spacing w:before="0" w:after="{after}"/>')
        out = [self.institute_block(), self.logo(30),
               c("CAPSTONE PROJECT\u2013II", f'{b}<w:sz w:val="28"/>', 40),
               c("PROJECT REPORT", f'{b}<w:sz w:val="28"/>', 360),
               c(f["title"][0], f'{b}<w:sz w:val="36"/><w:szCs w:val="36"/>', 360),
               c("Submitted in partial fulfilment of the requirements for the"),
               c("Bachelor of Engineering (B.E.) Degree in Computer Engineering", b),
               c(f"Semester VII | Academic Year {f['year'][0]}", "", 360),
               c("Submitted by", b, 120)]
        for name, roll in self.students():
            out.append(c(f"{name} \u2013 {roll}"))
        out += [para("Center", "", '<w:spacing w:before="0" w:after="200"/>'), c("Project Mentor", b, 120),
                c(f"{self.mentor()}, {f['mentor-designation'][0]}", "", 360),
                c(f"A. Y. {f['year'][0]}", b)]
        return "".join(out)

    def signature(self, label: str, width: int = 4200) -> str:
        return (para("Signature", run("_" * 40), '<w:spacing w:before="480" w:after="0"/>')
                + para("Signature", self.inline(label)))

    def front_pages(self) -> str:
        f = self.front
        title = f["title"][0]
        names = [n for n, _ in self.students()]
        name_list = ", ".join(names[:-1]) + " and " + names[-1]
        b = "<w:b/><w:bCs/>"
        out = []
        # certificate
        out.append(self.institute_block() + self.logo(24) + para("FrontTitle", run("Certificate")))   # the section break starts the page
        out.append(para("Normal", self.inline(
            f"This is to certify that **{name_list}** of Fourth Year Computer Engineering studying in Vivekanand "
            "Education Society\u2019s Institute of Technology, affiliated to University of Mumbai have satisfactorily "
            f"completed the project on **\u201c{title}\u201d** as a part of their coursework of Capstone Project - II for "
            f"Semester-VII under the guidance of their mentor **{self.mentor()}** in the year {f['year'][0]}.")))
        out.append(para("Normal", self.inline(
            f"This project report entitled \u201c{title}\u201d by {name_list} is approved for the degree of Bachelor of "
            "Engineering (B.E.) in Computer Engineering.")))
        po = Table(["l", "c"], [], 1)
        from build_ppeecs import Cell, Row
        po.rows = [Row([Cell("Programme Outcomes"), Cell("Grade")]),
                   Row([Cell("PO1, PO2, PO3, PO4, PO5, PO6, PO7, PO8, PO9, PO10, PO11, PSO1, PSO2"), Cell(" ")])]
        out.append(self.table_xml(po, 11, [4, 1], avail=6000, shade=False))
        out.append(para("Signature", run("Date:"), '<w:spacing w:before="480" w:after="0"/>'))
        out.append(self.signature("Project Guide: " + self.mentor()))
        # approval
        out.append(page_break() + para("FrontTitle", run("Project Report Approval")) + para("Center", run("For", b))
                   + para("Center", run("B. E. (Computer Engineering)", b), '<w:spacing w:before="0" w:after="360"/>'))
        out.append(para("Normal", self.inline(
            f"This project report entitled \u201c{title}\u201d by {name_list} is approved for the degree of Bachelor of "
            "Engineering (B.E.) in Computer Engineering.")))
        for who in ("Internal Examiner", "External Examiner", "Head of the Department", "Principal"):
            out.append(para("Signature", run("_" * 40), '<w:spacing w:before="600" w:after="0"/><w:jc w:val="right"/>')
                       + para("Signature", run(who), '<w:jc w:val="right"/>'))
        out.append(para("Signature", run("Date:"), '<w:spacing w:before="480" w:after="0"/>')
                   + para("Signature", run("Place:"), '<w:spacing w:before="240" w:after="0"/>'))
        # declaration
        out.append(page_break() + para("FrontTitle", run("Declaration")))
        out.append(para("Normal", run(
            "We declare that this written submission represents our ideas in our own words and where others\u2019 ideas "
            "or words have been included, we have adequately cited and referenced the original sources. We also declare "
            "that we have adhered to all principles of academic honesty and integrity and have not misrepresented or "
            "fabricated or falsified any idea/data/fact/source in our submission. We understand that any violation of "
            "the above will be cause for disciplinary action by the Institute and can also evoke penal action from the "
            "sources which have thus not been properly cited or from whom proper permission has not been taken when "
            "needed.")))
        cells = []
        for name, roll in self.students():
            cells.append(para("Signature", run("_" * 32), '<w:spacing w:before="560" w:after="0"/>')
                         + para("Signature", run("(Signature)"))
                         + para("Signature", self.inline(f"{name} ({roll})"), '<w:spacing w:before="60" w:after="0"/>'))
        rows = "".join("<w:tr>" + "".join(f'<w:tc><w:tcPr><w:tcW w:w="4600" w:type="dxa"/></w:tcPr>{c}</w:tc>'
                                          for c in cells[i:i + 2]) + "</w:tr>" for i in range(0, len(cells), 2))
        out.append('<w:tbl><w:tblPr><w:tblW w:w="9200" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblLook w:val="0000"/>'
                   '</w:tblPr><w:tblGrid><w:gridCol w:w="4600"/><w:gridCol w:w="4600"/></w:tblGrid>' + rows + "</w:tbl>")
        out.append(para("Signature", run("Date:"), '<w:spacing w:before="480" w:after="0"/>'))
        # acknowledgement, course outcomes, abbreviations, abstract come from 00-front.md
        sections: Dict[str, List[Block]] = {}
        cur = None
        for blk in self.front_blocks:
            if blk.kind == "heading" and blk.level == 1:
                cur = blk.attrs["id"]
                sections[cur] = []
            elif cur:
                sections[cur].append(blk)
        out.append(page_break() + para("FrontTitle", run("ACKNOWLEDGEMENT")) + self.chapter_body(sections["front:ack"]))
        out.append(self.course_outcomes(sections["front:co"]))
        out.append(self.contents())
        out.append(page_break() + para("FrontTitle", run("LIST OF ABBREVIATIONS")) + self.chapter_body(sections["front:abbr"]))
        abstract = Block("heading", "Abstract", 1, {"unnumbered": "1"})
        out.append(self.heading(abstract) + self.chapter_body(sections["front:abstract"]))
        return "".join(out)

    def course_outcomes(self, evidence: List[Block]) -> str:
        from build_ppeecs import Cell, Row
        b = "<w:b/><w:bCs/>"
        out = [page_break(), para("Center", run("DEPARTMENT OF COMPUTER ENGINEERING", f'{b}<w:sz w:val="26"/>')),
               para("FrontTitle", run("COURSE OUTCOMES FOR CAPSTONE PROJECT\u2013II", '<w:sz w:val="28"/>'))]
        cos = [("CO1", "Implement and integrate all modules of the proposed system effectively."),
               ("CO2", "Perform testing, debugging, validation, and performance optimization of the developed solution."),
               ("CO3", "Analyze project outcomes using appropriate engineering tools and metrics."),
               ("CO4", "Demonstrate deployment readiness, usability, security, scalability, and sustainability considerations."),
               ("CO5", "Analyze, interpret, and present research outcomes effectively using appropriate research "
                       "methodologies, analytical tools, and presentation techniques."),
               ("CO6", "Present and defend the complete project professionally through demonstrations, presentations, "
                       "and comprehensive technical documentation.")]
        t = Table(["c", "l"], [Row([Cell("Course Outcome"), Cell("Description")])] + [Row([Cell(a), Cell(d)]) for a, d in cos], 1)
        out.append(self.table_xml(t, 11, [1.3, 6]))
        out.append(para("Normal", "", '<w:spacing w:before="0" w:after="0"/>'))
        out.append(para("Center", run("CO\u2013PO\u2013PSO Mapping Table", f'{b}<w:sz w:val="28"/>'),
                        '<w:spacing w:before="240" w:after="120"/>'))
        heads = ["CO"] + [f"PO{i}" for i in range(1, 12)] + ["PSO1", "PSO2"]
        vals = ["2 3 3 \u2013 3 \u2013 \u2013 \u2013 3 \u2013 2 3 3", "2 3 2 3 3 \u2013 \u2013 \u2013 2 \u2013 2 3 2",
                "2 3 2 3 3 \u2013 \u2013 \u2013 \u2013 2 2 3 2", "2 2 3 2 3 2 3 2 \u2013 \u2013 3 3 3",
                "2 3 \u2013 3 3 \u2013 \u2013 2 \u2013 3 2 2 2", "\u2013 \u2013 \u2013 \u2013 2 \u2013 \u2013 2 3 3 2 2 2"]
        t = Table(["c"] * 14, [Row([Cell(h) for h in heads])]
                  + [Row([Cell(f"CO{i + 1}")] + [Cell(v) for v in row.split()]) for i, row in enumerate(vals)], 1)
        out.append(self.table_xml(t, 10, [1.3] + [1] * 13))
        out.append(para("Normal", self.inline("*Mapping scale: 3 = High correlation; 2 = Moderate correlation; "
                                              "1 = Low correlation; \u2013 = No direct correlation.*"),
                        '<w:spacing w:before="120" w:after="120"/>'))
        out.append(self.chapter_body(evidence))
        return "".join(out)

    # ---- contents and lists ----------------------------------------------- #
    def contents(self) -> str:
        """Contents, list of figures and list of tables as Word fields, filled with known page numbers."""
        out = []
        groups = [("TABLE OF CONTENTS", 'TOC \\o "1-3" \\h \\z \\u', ("toc1", "toc2", "toc3")),
                  ("LIST OF FIGURES", 'TOC \\h \\z \\t "Figure Caption,1"', ("fig",)),
                  ("LIST OF TABLES", 'TOC \\h \\z \\t "Table Caption,1"', ("tab",))]
        for title, instr, kinds in groups:
            entries = [e for e in self.prev_entries if e.kind in kinds] or [Entry(kinds[0], "(updated on build)", "")]
            out.append(page_break() + para("FrontTitle", run(title)))
            label = {"toc1": "Title", "fig": "Figure", "tab": "Table"}[kinds[0]]
            out.append(para("TOC1", run(label) + run("\tPage No."), '<w:pBdr><w:bottom w:val="single" w:sz="4" '
                            'w:space="2" w:color="000000"/></w:pBdr>'))
            for i, e in enumerate(entries):
                style_ = {"toc1": "TOC1", "toc2": "TOC2", "toc3": "TOC3"}.get(e.kind, "TOC2")
                ppr = '<w:ind w:left="0" w:right="400" w:hanging="0"/>' if e.kind in ("fig", "tab") else ""
                body = run(e.text + "\t" + self.pages.get(e.key, ""))
                if i == 0:
                    body = (f'<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> {instr} '
                            '</w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>' + body)
                if i == len(entries) - 1:
                    body += '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
                out.append(para(style_, body, ppr))
        return "".join(out)

    # ---- whole body ------------------------------------------------------- #
    def body(self, prev_entries: List[Entry]) -> str:
        self.prev_entries = prev_entries
        self.cites: List[str] = []
        self.rels: List[Tuple[str, str, str, bool]] = []
        self.media: List[Tuple[str, Path]] = []
        self.entries: List[Entry] = []
        self.refs: set = set()
        self.used_res: set = set()
        self.placeholders: List[str] = []
        self.list_nums: List[int] = []
        self.bullet_num = 100
        self.logo_count = 0
        hdr = '<w:headerReference w:type="default" r:id="rId9"/><w:footerReference w:type="default" r:id="rIdFtr"/>'
        geom = ('<w:pgSz w:w="12240" w:h="15840" w:orient="portrait"/><w:pgMar w:top="1152" w:right="1440" '
                'w:bottom="1152" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>')
        title_sect = f'<w:p><w:pPr><w:sectPr>{geom}<w:vAlign w:val="center"/></w:sectPr></w:pPr></w:p>'
        front_sect = f'<w:p><w:pPr><w:sectPr>{hdr}{geom}<w:pgNumType w:fmt="lowerRoman" w:start="1"/></w:sectPr></w:pPr></w:p>'
        main_sect = f'<w:sectPr>{hdr}{geom}<w:pgNumType w:fmt="decimal" w:start="1"/></w:sectPr>'
        front = self.title_page() + title_sect + self.front_pages() + front_sect
        chapters = "".join(self.chapter_body(blocks) for blocks in self.chapters)
        # the abstract heading is the first contents entry; chapters follow
        return front + chapters + main_sect

    def check(self) -> List[str]:
        problems = []
        for label in self.labels:
            if label.split(":")[0] in ("fig", "tab", "eq", "alg") and label not in self.refs:
                problems.append(f"{label} is never referenced")
        unused = sorted(set(self.bib) - set(self.cites))
        if unused:
            print(f"note: {len(unused)} bibliography entries not cited (left out of the list)")
        return problems


# --------------------------------------------------------------------------- #
# package

FOOTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<w:p><w:pPr><w:pBdr><w:top w:val="single" w:sz="4" w:space="4" w:color="808080"/></w:pBdr>'
          f'<w:tabs><w:tab w:val="center" w:pos="{TEXT_W // 2}"/><w:tab w:val="right" w:pos="{TEXT_W}"/></w:tabs>'
          '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr>'
          f'<w:r><w:rPr>{TNR}<w:i/><w:sz w:val="18"/></w:rPr><w:tab/><w:t xml:space="preserve">Capstone Project\u2013II '
          'Blackbook | Academic Year 2026\u201327</w:t><w:tab/></w:r>'
          f'<w:r><w:rPr>{TNR}<w:sz w:val="20"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
          f'<w:r><w:rPr>{TNR}<w:sz w:val="20"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
          f'<w:r><w:rPr>{TNR}<w:sz w:val="20"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r>'
          f'<w:r><w:rPr>{TNR}<w:sz w:val="20"/></w:rPr><w:t>1</w:t></w:r>'
          f'<w:r><w:rPr>{TNR}<w:sz w:val="20"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')

NUMBERING = ('<w:abstractNum w:abstractNumId="100"><w:multiLevelType w:val="singleLevel"/>'
             '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="\u2022"/>'
             '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="567" w:hanging="340"/></w:pPr>'
             f'<w:rPr>{TNR}</w:rPr></w:lvl></w:abstractNum>'
             '<w:abstractNum w:abstractNumId="101"><w:multiLevelType w:val="singleLevel"/>'
             '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/>'
             '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="567" w:hanging="340"/></w:pPr>'
             f'<w:rPr>{TNR}</w:rPr></w:lvl></w:abstractNum>')


def numbering_xml(src: str, lists: int) -> str:
    nums = '<w:num w:numId="100"><w:abstractNumId w:val="100"/></w:num>' + "".join(
        f'<w:num w:numId="{200 + i}"><w:abstractNumId w:val="101"/><w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/>'
        "</w:lvlOverride></w:num>" for i in range(lists))
    # abstract numbering definitions must come before the num instances
    first_num = src.find("<w:num ")
    if first_num < 0:
        return src.replace("</w:numbering>", NUMBERING + nums + "</w:numbering>")
    return src[:first_num] + NUMBERING + src[first_num:].replace("</w:numbering>", nums + "</w:numbering>")


def write(book: Book, entries: List[Entry], out: Path) -> None:
    zin = zipfile.ZipFile(TEMPLATE)
    parts = {n: zin.read(n) for n in zin.namelist()}
    doc = parts["word/document.xml"].decode()
    root = re.search(r"<w:document[^>]*>", doc).group(0)
    body = book.body(entries)
    parts["word/document.xml"] = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                                  f"{root}<w:body>{body}</w:body></w:document>").encode()
    parts["word/styles.xml"] = styles_xml(parts["word/styles.xml"].decode()).encode()
    parts["word/numbering.xml"] = numbering_xml(parts["word/numbering.xml"].decode(), len(book.list_nums)).encode()
    parts["word/footer2.xml"] = FOOTER.encode()
    rels = parts["word/_rels/document.xml.rels"].decode()
    rels = re.sub(r'<Relationship Id="rId[78]"[^>]*/>', "", rels)          # the template's own image placements
    extra = [("rIdLogo", REL_IMAGE, LOGO, False), ("rIdFtr", REL_FOOTER, "footer2.xml", False)] + book.rels
    rels = rels.replace("</Relationships>", "".join(
        f'<Relationship Id="{i}" Type="{t}" Target="{esc(tg)}"' + (' TargetMode="External"' if ext else "") + "/>"
        for i, t, tg, ext in extra) + "</Relationships>")
    parts["word/_rels/document.xml.rels"] = rels.encode()
    ct = parts["[Content_Types].xml"].decode()
    if 'Extension="png"' not in ct:
        ct = ct.replace("<Default ", '<Default Extension="png" ContentType="image/png"/><Default ', 1)
    ct = ct.replace("</Types>", f'<Override PartName="/word/footer2.xml" ContentType="{FOOTER_CT}"/></Types>')
    parts["[Content_Types].xml"] = ct.encode()
    for name, path in book.media:
        parts["word/" + name] = path.read_bytes()
    settings = parts["word/settings.xml"].decode()
    settings = re.sub(r"<w:documentProtection[^>]*/>|<w:attachedTemplate[^>]*/>", "", settings)
    parts["word/settings.xml"] = settings.encode()
    names = "; ".join(n for n, _ in book.students())
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts["docProps/core.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f"<dc:title>{esc(book.front['title'][0])}</dc:title><dc:subject>Capstone Project II report, Group 39</dc:subject>"
        f"<dc:creator>{esc(names)}</dc:creator><cp:lastModifiedBy>{esc(names.split(';')[0])}</cp:lastModifiedBy>"
        f'<cp:revision>1</cp:revision><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>').encode()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name in [n for n in zin.namelist() if n in parts] + [n for n in parts if n not in zin.namelist()]:
            z.writestr(name, parts[name])


# --------------------------------------------------------------------------- #
# page numbers from the rendering

def page_map(pdf: Path, entries: List[Entry]) -> Dict[str, str]:
    """Printed page number of every contents entry: roman before Chapter 1, arabic from it."""
    pages = [" ".join(p.split()) for p in pdf_pages(pdf)]
    norm = lambda s: " ".join(s.split())
    # the contents pages list every entry too; search only after the last list page
    start = next(i for i, p in enumerate(pages) if "LIST OF ABBREVIATIONS" in p[:200])
    ch1 = next(i for i in range(start, len(pages)) if "CHAPTER 1:" in pages[i])
    out: Dict[str, str] = {}
    cur = start
    for e in entries:
        key = norm(e.key)
        if not key:
            continue
        for i in range(cur, len(pages)):
            if key in pages[i]:
                cur = i
                out[e.key] = str(i - ch1 + 1) if i >= ch1 else roman(i)      # physical page 1 is the title page
                break
        else:
            print(f"  page not found for: {e.key[:70]}")
    return out


def lint_sources() -> List[str]:
    issues = []
    for path in sorted(CHAPTERS.glob("*.md")):
        _, blocks = parse_chapter(path)
        for b in blocks:
            for t in [b.text] + (b.lines if b.kind in ("list", "bullets") else []):
                prose = re.sub(r"\$[^$]*\$|\[@[^\]]+\]|\\res\{[^}]+\}|`[^`]*`", "X", t)
                if b.kind in ("table", "alg", "fig"):
                    continue
                for pat, msg in ((r", and\b", "comma before 'and'"), ("\u2014|---", "em dash"),
                                 (r"\b(Moreover|Furthermore|Additionally|In conclusion|delve|leverag\w*|seamless\w*|"
                                  r"utiliz\w*|robust\w*|crucial|pivotal|showcas\w*|underscor\w*)\b", "stock word"),
                                 (r"\b(labell\w*|modell\w*|standardis\w*|normalis\w*|behaviour\w*|analys(?:e|ed|ing)\b|"
                                  r"optimis(?:e|ed|es|ing|ation)\b|organis\w*|summaris\w*)", "British spelling")):
                    for m in re.finditer(pat, prose):
                        issues.append(f"{path.name}: {msg}: ...{prose[max(0, m.start() - 40):m.end() + 30]}...")
    return issues


def main() -> None:
    res = load_results()
    res.update(derived_results(res))
    bib = parse_bib(BIB)
    entries: List[Entry] = []
    book = Book(res, bib)
    for attempt in range(4):
        write(book, entries, OUT)
        new_entries = book.entries
        pdf = to_pdf(OUT)
        pages = page_map(pdf, new_entries)
        stable = pages == book.pages and [e.key for e in new_entries] == [e.key for e in entries]
        book.pages = pages
        entries = new_entries
        print(f"pass {attempt + 1}: {len(pdf_pages(pdf))} pages")
        if stable:
            break
    problems = book.check()
    for i in lint_sources():
        print("LINT", i)
    print(f"{OUT.name}: {len(pdf_pages(pdf))} pages, {len(book.cites)} references, {len(book.media)} figures, "
          f"{sum(e.kind == 'tab' for e in entries)} tables, {len(book.used_res)} result keys")
    if book.placeholders:
        print(f"{len(book.placeholders)} placeholders to fill: " + "; ".join(sorted(set(book.placeholders))))
    for p in problems:
        print("FAIL", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
