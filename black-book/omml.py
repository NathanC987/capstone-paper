"""LaTeX math to Word equations (OMML) for the subset the black book uses.

The paper builds convert math with pandoc and cache the result in
paper/ppeecs/math_cache.json; build_blackbook.py takes cached equations from there and
converts the rest here, in the same form pandoc writes: letters italic, digits and
operators upright, an n-ary operator taking the next atom as its body.

Supported: letters, digits, operators, \\frac, ^, _, \\sum, \\prod, \\sqrt, \\hat, \\bar,
\\tilde, \\mathrm, \\text, \\operatorname, \\left...\\right, Greek letters, the usual relation
symbols and upright function names (\\ln, \\log, \\exp, \\max, \\min, \\sup, \\arg).
"""

from __future__ import annotations

import html
import re
from typing import List, Tuple

GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ϵ", "varepsilon": "ε", "zeta": "ζ",
    "eta": "η", "theta": "θ", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π",
    "rho": "ρ", "sigma": "σ", "tau": "τ", "phi": "ϕ", "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Sigma": "Σ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}
SYMBOLS = {
    "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "neq": "≠", "ne": "≠", "in": "∈", "notin": "∉", "cdot": "⋅",
    "times": "×", "infty": "∞", "sim": "∼", "approx": "≈", "to": "→", "rightarrow": "→", "leftarrow": "←",
    "mid": "∣", "pm": "±", "cup": "∪", "cap": "∩", "subset": "⊂", "subseteq": "⊆", "forall": "∀", "exists": "∃",
    "lfloor": "⌊", "rfloor": "⌋", "lceil": "⌈", "rceil": "⌉", "ldots": "…", "dots": "…", "cdots": "⋯",
    "Vert": "‖", "lvert": "|", "rvert": "|", "langle": "⟨", "rangle": "⟩", "{": "{", "}": "}", "|": "‖",
    "%": "%", "#": "#", "&": "&", "_": "_", "partial": "∂", "nabla": "∇", "propto": "∝", "equiv": "≡",
}
FUNCS = {"ln", "log", "exp", "max", "min", "sup", "inf", "arg", "argmax", "argmin", "sin", "cos", "lim", "det", "Pr"}
NARY = {"sum": "∑", "prod": "∏", "int": "∫"}
ACCENTS = {"hat": "̂", "widehat": "̂", "bar": "̅", "overline": "̅", "tilde": "̃",
           "widetilde": "̃", "dot": "̇", "vec": "⃗"}
SPACES = {",": " ", ";": " ", ":": " ", "quad": " ", "qquad": "  ", " ": " ", "!": ""}


def _r(text: str, upright: bool) -> str:
    sty = '<m:rPr><m:sty m:val="p" /></m:rPr>' if upright else ""
    return f"<m:r>{sty}<m:t>{html.escape(text, quote=False)}</m:t></m:r>"


class _Parser:
    def __init__(self, src: str) -> None:
        self.toks = re.findall(r"\\[A-Za-z]+|\\.|[A-Za-z]|\d+(?:\.\d+)?|\S", src)
        self.i = 0

    def peek(self) -> str:
        return self.toks[self.i] if self.i < len(self.toks) else ""

    def take(self) -> str:
        t = self.peek()
        self.i += 1
        return t

    def group(self) -> str:
        """A braced group or a single atom, as OMML."""
        if self.peek() == "{":
            self.take()
            out = self.seq("}")
            self.take()
            return out
        return self.atom_with_scripts(scripts=False)

    def raw_group(self) -> str:
        """The text of a braced group, for \\mathrm and \\text."""
        if self.peek() != "{":
            return self.take()
        self.take()
        depth, out = 1, []
        while self.i < len(self.toks):
            t = self.take()
            if t == "{":
                depth += 1
            elif t == "}":
                depth -= 1
                if depth == 0:
                    break
            out.append(t[1:] if t.startswith("\\") and len(t) == 2 else t)
        return "".join(out)

    def seq(self, stop: str = "") -> str:
        out: List[str] = []
        while self.i < len(self.toks) and self.peek() != stop and not (stop == "right" and self.peek() == "\\right"):
            out.append(self.atom_with_scripts())
        return "".join(out)

    def scripts(self) -> Tuple[str, str]:
        sub = sup = ""
        while self.peek() in ("_", "^"):
            kind = self.take()
            body = self.group()
            if kind == "_":
                sub = body
            else:
                sup = body
        return sub, sup

    def atom_with_scripts(self, scripts: bool = True) -> str:
        t = self.peek()
        if t.startswith("\\") and t[1:] in NARY:
            self.take()
            sub, sup = self.scripts()
            body = self.atom_with_scripts()
            hide = (f'<m:subHide m:val="{"off" if sub else "on"}" /><m:supHide m:val="{"off" if sup else "on"}" />')
            return (f'<m:nary><m:naryPr><m:chr m:val="{NARY[t[1:]]}" /><m:limLoc m:val="undOvr" />{hide}</m:naryPr>'
                    f"<m:sub>{sub}</m:sub><m:sup>{sup}</m:sup><m:e>{body}</m:e></m:nary>")
        base = self.atom()
        if not scripts:
            return base
        sub, sup = self.scripts()
        if sub and sup:
            return f"<m:sSubSup><m:e>{base}</m:e><m:sub>{sub}</m:sub><m:sup>{sup}</m:sup></m:sSubSup>"
        if sub:
            return f"<m:sSub><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>"
        if sup:
            return f"<m:sSup><m:e>{base}</m:e><m:sup>{sup}</m:sup></m:sSup>"
        return base

    def atom(self) -> str:
        t = self.take()
        if t == "{":
            out = self.seq("}")
            self.take()
            return out
        if t.isdigit() or re.fullmatch(r"\d+\.\d+", t):
            return _r(t, True)
        if re.fullmatch(r"[A-Za-z]", t):
            return _r(t, False)
        if not t.startswith("\\"):
            return _r({"-": "−", "'": "′", "*": "∗"}.get(t, t), True)
        name = t[1:]
        if name in ("frac", "dfrac", "tfrac"):
            num, den = self.group(), self.group()
            return f'<m:f><m:fPr><m:type m:val="bar" /></m:fPr><m:num>{num}</m:num><m:den>{den}</m:den></m:f>'
        if name == "sqrt":
            return f'<m:rad><m:radPr><m:degHide m:val="on" /></m:radPr><m:deg /><m:e>{self.group()}</m:e></m:rad>'
        if name in ACCENTS:
            return f'<m:acc><m:accPr><m:chr m:val="{ACCENTS[name]}" /></m:accPr><m:e>{self.group()}</m:e></m:acc>'
        if name in ("mathrm", "text", "operatorname", "textrm", "mathit", "mathbf"):
            text = self.raw_group()
            return _r(text, name != "mathit")
        if name == "left":
            open_ = self.take()
            body = self.seq("right")
            self.take()                        # \right
            close = self.take()
            fix = {"\\{": "{", "\\}": "}", ".": "", "\\|": "‖", "\\lvert": "|", "\\rvert": "|"}
            o, c = fix.get(open_, open_), fix.get(close, close)
            return (f'<m:d><m:dPr><m:begChr m:val="{html.escape(o)}" /><m:endChr m:val="{html.escape(c)}" /></m:dPr>'
                    f"<m:e>{body}</m:e></m:d>")
        if name in GREEK:
            return _r(GREEK[name], name[0].isupper())
        if name in SYMBOLS:
            return _r(SYMBOLS[name], True)
        if name in FUNCS:
            return _r(name, True)
        if name in SPACES:
            return _r(SPACES[name], True) if SPACES[name] else ""
        raise ValueError(f"unsupported LaTeX command \\{name}")


def to_omml(latex: str) -> str:
    """One expression as <m:oMath>."""
    p = _Parser(latex)
    body = p.seq()
    if p.i < len(p.toks):
        raise ValueError(f"could not parse {latex!r} at token {p.peek()!r}")
    return f"<m:oMath>{body}</m:oMath>"
