"""Figures of the black book, written to paper/black-book/figures/.

Diagrams are drawn with Graphviz (dot) from descriptions of the implemented code in
src/drift_autopsy; the Gantt chart comes from the commit history of both repositories;
the result figures are the paper's (paper/ppeecs/figures, paper/figures) converted to
PNG. Dashboard screenshots need the dashboard running on 127.0.0.1:8599:

    streamlit run examples/dashboard/app.py --server.headless true --server.address 127.0.0.1 --server.port 8599
    python paper/black-book/make_figures.py --screens

Run from anywhere:

    python paper/black-book/make_figures.py            # diagrams, Gantt chart, paper figures
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

BB = Path(__file__).resolve().parent
REPO = BB.parents[1]
OUT = BB / "figures"
FONT = "Liberation Sans"
INK = "#1f2a3a"
FILL = {"in": "#eef2f7", "stage": "#dfe8f5", "core": "#c9daf0", "out": "#e8f1e4", "note": "#fbf3df", "grey": "#eeeeee"}


def dot(name: str, src: str, dpi: int = 300) -> None:
    head = (f'graph [fontname="{FONT}", dpi={dpi}, bgcolor="white", pad="0.15"];\n'
            f'node [fontname="{FONT}", fontsize=11, color="{INK}", fontcolor="{INK}", penwidth=1.1];\n'
            f'edge [fontname="{FONT}", fontsize=9.5, color="{INK}", fontcolor="{INK}", penwidth=1.0, arrowsize=0.7];\n')
    text = src.replace("{{HEAD}}", head)
    (OUT / f"{name}.dot").write_text(text)
    subprocess.run(["dot", "-Tpng", "-o", str(OUT / f"{name}.png"), str(OUT / f"{name}.dot")], check=True)
    (OUT / f"{name}.dot").unlink()


def box(label: str, fill: str, shape: str = "box", extra: str = "") -> str:
    return f'[shape={shape}, style="rounded,filled", fillcolor="{FILL[fill]}", label=<{label}>{extra}]'


# --------------------------------------------------------------------------- #

def block_diagram() -> None:
    dot("block_diagram", """digraph G { {{HEAD}} rankdir=TB; nodesep=0.22; ranksep=0.32; newrank=true; node [fontsize=10.5];
  subgraph cluster_in { label=<<b>A. Inputs</b>>; style="rounded,dashed"; color="#7a8699"; fontsize=11;
    model %s; ref %s; prod %s; audit %s; }
  prep %s;
  subgraph cluster_c { label=<<b>C. Detection and estimation</b>>; style="rounded"; color="#7a8699"; fontsize=11;
    det %s; est %s; loc %s; }
  subgraph cluster_d { label=<<b>D. Drift type and cause</b>>; style="rounded"; color="#7a8699"; fontsize=11;
    lf %s; au %s; rca %s; }
  subgraph cluster_ef { label=<<b>E, F. Acting on the findings</b>>; style="rounded"; color="#7a8699"; fontsize=11;
    rel %s; tri %s; }
  rep %s; dash %s; art %s;
  {rank=same; model ref prod audit}
  {rank=same; det est loc}
  {rank=same; lf au rca}
  {rank=same; rel tri}
  {rank=same; dash art}
  {model ref prod} -> prep; prep -> {det est loc};
  det -> lf; loc -> lf; lf -> au [label=" no label-free\\n rejection"]; audit -> au [style=dashed, constraint=false];
  lf -> rca [constraint=false];
  {lf au rca} -> rel [style=invis]; rel -> tri; lf -> rep [style=invis];
  est -> rep [style=dashed, constraint=false];
  tri -> rep; au -> rep [style=invis];
  rep -> {dash art};
}""" % (box("Deployed model", "in"), box("Labeled reference<br/>data", "in"), box("Unlabeled production<br/>windows", "in"),
        box("Late audit labels<br/>(optional)", "in"),
        box("<b>B. Preparation</b>: feature typing, image embeddings,<br/>train / calibration / test split", "stage"),
        box("Shift detectors<br/>KS, PSI, MMD,<br/>confidence test", "stage"), box("Accuracy estimate<br/>CBPE (AC, DoC, ATC)", "stage"),
        box("Localization<br/>per-feature tests,<br/>effect sizes", "stage"),
        box("<b>Label-free stage</b><br/>weighted Holm family,<br/>BBSE consistency test", "core"),
        box("<b>Audit stage</b><br/>accuracy drop,<br/>error-structure tests", "core"), box("<b>Root cause</b><br/>SHAP (tabular),<br/>CAM (images)", "core"),
        box("<b>E. Reliability</b><br/>risk of each prediction", "stage"), box("<b>F. Remediation triage</b><br/>will a cheap retrain help?", "stage"),
        box("<b>JSON report</b> per study", "out", "note"), box("Interactive dashboard<br/>(Streamlit)", "out"),
        box("Paper tables, figures<br/>and result keys", "out")))


def module_diagram() -> None:
    """The packages of src/drift_autopsy as layers; each layer uses the ones below it."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    layers = [
        ("Presentation", "out", [("dashboard", "app, charts, narrative"), ("paper build", "result keys, tables, figures")]),
        ("Orchestration", "stage", [("experiments", "ACS, gas sensor, CLEAR-10"), ("benchmark", "injectors, windows, metrics"),
                                    ("config", "schema, YAML loader")]),
        ("Analysis", "core", [("detectors", "KS, PSI, MMD, CBPE,\nBBSD, classifier test"), ("estimation", "CBPE, AC, DoC, ATC"),
                              ("localizers", "per-feature tests"), ("diagnosis", "label-free, audit,\nbaselines")]),
        ("", "core", [("rca", "SHAP, CAM, concept probe"), ("reliability", "signals, OOD, fusion"),
                      ("remediation", "strategies, triage")]),
        ("Foundation", "in", [("core", "Dataset, DriftPipeline,\nbase classes, results"), ("stats", "Holm, chi-square,\nweighted KS, Wilson"),
                              ("data", "loaders, validators,\nimage tabularizer"), ("extractors", "ResNet-18, CLIP")]),
    ]
    plt.rcParams.update({"font.family": FONT, "font.size": 9})
    fig, ax = plt.subplots(figsize=(6.5, 5.0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    band_h, gap, top, x0, x1 = 16.5, 2.5, 99, 17.5, 99.5
    bands = {"Presentation": (0, 0), "Orchestration": (1, 1), "Analysis": (2, 3), "Foundation": (4, 4)}
    for name, (a, b) in bands.items():
        y_top = top - a * (band_h + gap)
        y_bot = top - b * (band_h + gap) - band_h
        ax.add_patch(FancyBboxPatch((0.5, y_bot), x1 - 0.5, y_top - y_bot, boxstyle="round,pad=0,rounding_size=1.5",
                                    fc="#f7f8fa", ec="#7a8699", lw=0.8))
        ax.text(9.6, (y_top + y_bot) / 2, name, ha="center", va="center", fontweight="bold", fontsize=8)
    for k, (_, fill, pkgs) in enumerate(layers):
        y = top - k * (band_h + gap) - band_h + 1.5
        w = (x1 - x0 - 1.5 * (len(pkgs) - 1)) / len(pkgs) if len(pkgs) > 2 else 30
        start = x0 if len(pkgs) > 2 else x0 + (x1 - x0 - 2 * 30 - 1.5) / 2
        for i, (title, desc) in enumerate(pkgs):
            x = start + i * (w + 1.5)
            ax.add_patch(FancyBboxPatch((x + 0.4, y), w - 0.8, band_h - 3, boxstyle="round,pad=0,rounding_size=1.2",
                                        fc=FILL[fill], ec=INK, lw=0.9))
            ax.text(x + w / 2, y + band_h - 6.0, title, ha="center", va="center", fontweight="bold", fontsize=8)
            ax.text(x + w / 2, y + (band_h - 6.5) / 2, desc, ha="center", va="center", fontsize=6.6, linespacing=1.15)
    fig.savefig(OUT / "module_diagram.png", dpi=300, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def class_diagram() -> None:
    def cls(name: str, attrs: list, methods: list) -> str:
        rows = "".join(f'<tr><td align="left" balign="left">{a}</td></tr>' for a in attrs) or "<tr><td> </td></tr>"
        meth = "".join(f'<tr><td align="left" balign="left">{m}</td></tr>' for m in methods) or "<tr><td> </td></tr>"
        return (f'[shape=plain, label=<<table border="1" cellborder="0" cellspacing="0" cellpadding="3" bgcolor="white">'
                f'<tr><td bgcolor="{FILL["core"]}"><b>{name}</b></td></tr>'
                f'<tr><td><table border="0" cellborder="0" cellspacing="0" cellpadding="1">{rows}</table></td></tr>'
                f'<tr><td sides="t" border="1"><table border="0" cellborder="0" cellspacing="0" cellpadding="1">{meth}</table></td></tr>'
                "</table>>]")
    nodes = {
        "DriftPipeline": cls("DriftPipeline", ["detector", "localizer", "rca", "model"], ["run(reference, test)"]),
        "BaseDriftDetector": cls("BaseDriftDetector", ["threshold", "fitted"], ["fit(reference)", "detect(test)"]),
        "Detectors": cls("Detectors", ["KSTest, PSI, MMD,", "CBPE, BBSD,", "DomainClassifier"], ["fit()", "detect()"]),
        "Localizer": cls("UnivariateLocalizer", [], ["localize(reference, test)"]),
        "SHAP": cls("SHAPAnalyzer", ["model", "n_samples"], ["analyze(reference, test)"]),
        "PipelineResult": cls("PipelineResult", ["detection", "localization", "rca", "execution_time"], ["to_dict()"]),
        "DetectionResult": cls("DetectionResult", ["detector_name", "drift_detected", "p_value", "statistic"], ["to_dict()"]),
        "diag": cls("diagnosis module", [], ["label_free_diagnosis()", "audit_diagnosis()", "combine()"]),
        "Diagnosis": cls("Diagnosis", ["drift_type", "stage", "rationale", "localized_features"], ["to_dict()"]),
        "Dataset": cls("Dataset", ["data, feature_names", "target, predictions", "prediction_probabilities",
                                   "categorical_features"], ["from_pandas()", "to_numpy()"]),
        "Reliability": cls("ReliabilityAnalyzer", ["fusion model"], ["analyze(X)", "summarize()"]),
        "Triage": cls("remediation_triage()", [], ["importance-weighting probe", "recent-window probe"]),
    }
    edges = """
  {rank=same; DriftPipeline BaseDriftDetector Detectors}
  {rank=same; Localizer SHAP PipelineResult}
  {rank=same; DetectionResult diag Reliability}
  {rank=same; Diagnosis Dataset Triage}
  Detectors -> BaseDriftDetector [arrowhead=empty, label=" extends"];
  DriftPipeline -> BaseDriftDetector [arrowtail=odiamond, dir=back];
  DriftPipeline -> Localizer [arrowtail=odiamond, dir=back];
  DriftPipeline -> SHAP [arrowtail=odiamond, dir=back];
  DriftPipeline -> PipelineResult [style=dashed, label=" returns"];
  PipelineResult -> DetectionResult [arrowtail=diamond, dir=back];
  diag -> Diagnosis [style=dashed, label=" returns"];
  diag -> Dataset [style=dashed, label=" reads"];
  Reliability -> Dataset [style=dashed]; Triage -> Dataset [style=dashed, constraint=false];
  SHAP -> diag [style=invis]; BaseDriftDetector -> PipelineResult [style=invis]; Detectors -> Reliability [style=invis];
"""
    body = "\n".join(f"  {k} {v};" for k, v in nodes.items())
    dot("class_diagram", "digraph G { {{HEAD}} rankdir=TB; nodesep=0.3; ranksep=0.45; node [fontsize=10];\n"
        + body + edges + "}")


def dataflow_diagram() -> None:
    dot("dataflow", """digraph G { {{HEAD}} rankdir=TB; nodesep=0.35; ranksep=0.3; node [fontsize=10.5];
  src %s; load %s; study %s; bench %s; json %s; build %s; res %s; dash %s; paper %s; book %s;
  {rank=same; study bench} {rank=same; dash build} {rank=same; paper book}
  src -> load; load -> {study bench}; {study bench} -> json; json -> dash; json -> build -> res -> {paper book};
}""" % (box("Public datasets: Folktables ACS, UCI gas sensor, CLEAR-10", "in", "cylinder"),
        box("Loaders and validators (cached, typed features)", "stage"),
        box("Study scripts<br/>examples/quickstart/*_study.py", "stage"), box("Injection benchmark<br/>5 states x 10 seeds", "stage"),
        box("outputs/*.json: one report per study", "out", "note"), box("build_artifacts.py", "stage"),
        box("results.tex, tables, figures", "out", "note"), box("Streamlit dashboard", "out"),
        box("Research paper versions", "out"), box("This report", "out")))


def flow_detection() -> None:
    dot("flow_detection", """digraph G { {{HEAD}} rankdir=TB; nodesep=0.3; ranksep=0.3; node [fontsize=10.5];
  s %s; a %s; b %s; c %s; d %s; e %s; f %s; g %s; h %s;
  s -> a -> b -> c -> d -> e; e -> f [label="yes"]; e -> g [label="no"]; f -> h; g -> h;
}""" % (box("Start: production window", "grey", "oval"), box("Validate schema and types<br/>against the reference", "stage"),
        box("Model predicts labels and<br/>class probabilities", "stage"),
        box("Run KS, PSI, MMD and the<br/>confidence test against<br/>the calibration part", "stage"),
        box("Estimate accuracy (CBPE)<br/>from the confidences", "stage"),
        box("Any test significant<br/>after correction?", "note", "diamond"),
        box("Localize: per-feature tests,<br/>effect sizes, unseen categories", "core"),
        box("Report no shift", "out"), box("Pass alarms, estimate and<br/>localization to the diagnosis", "grey", "oval")))


def flow_reliability_triage() -> None:
    dot("flow_triage", """digraph G { {{HEAD}} rankdir=TB; nodesep=0.35; ranksep=0.3; node [fontsize=10.5];
  subgraph cluster_r { label=<<b>(a) Reliability of each prediction</b>>; style="rounded"; color="#7a8699";
    r1 %s; r2 %s; r3 %s; r4 %s; r5 %s; r1 -> r2 -> r3; r3 -> r4 [label="yes"]; r3 -> r5 [label="no"]; }
  subgraph cluster_t { label=<<b>(b) Remediation triage</b>>; style="rounded"; color="#7a8699";
    t1 %s; t2 %s; t3 %s; t4 %s; t5 %s; t6 %s; t1 -> t2; t1 -> t3 [label="if an earlier\\nwindow is labeled"];
    t2 -> t4; t3 -> t4; t4 -> t5 [label="yes"]; t4 -> t6 [label="no"]; }
}""" % (box("Signals per row: confidence risk 1-c,<br/>instability under perturbation, OOD score", "stage"),
        box("Count wrong predictions<br/>in the calibration part", "stage"),
        box("At least ten per signal?", "note", "diamond"), box("Learned fusion: logistic<br/>regression to P(error)", "core"),
        box("Fall back to<br/>risk = 1 - c", "core"),
        box("Density-ratio weights from a<br/>reference-vs-production classifier", "stage"),
        box("Probe 1: importance-weighted<br/>retrain vs. deployed model", "stage"),
        box("Probe 2: retrain on the<br/>earlier labeled window", "stage"),
        box("Gain significant after<br/>Holm over the probes?", "note", "diamond"),
        box("Recommend the retrain", "out"), box("Hold: keep the deployed<br/>model, keep monitoring", "out")))


def usecase_diagram() -> None:
    dot("usecase", """digraph G { {{HEAD}} rankdir=LR; nodesep=0.22; ranksep=0.9; node [fontsize=10.5];
  eng [shape=none, label=<<b>ML engineer</b>>, image="", fontsize=11]; team [shape=none, label=<<b>Monitoring team</b>>];
  lab [shape=none, label=<<b>Labeling team</b>>];
  subgraph cluster_s { label=<<b>ResilientAI</b>>; style="rounded"; color="#7a8699";
    u1 [shape=ellipse, style=filled, fillcolor="%s", label="Register model and\\nreference data"];
    u2 [shape=ellipse, style=filled, fillcolor="%s", label="Run a production window"];
    u3 [shape=ellipse, style=filled, fillcolor="%s", label="View alarms, estimate\\nand shifted features"];
    u4 [shape=ellipse, style=filled, fillcolor="%s", label="Read the drift type\\nand its rationale"];
    u5 [shape=ellipse, style=filled, fillcolor="%s", label="Provide audit labels"];
    u6 [shape=ellipse, style=filled, fillcolor="%s", label="Check doubtful predictions"];
    u7 [shape=ellipse, style=filled, fillcolor="%s", label="Decide on retraining"];
    u8 [shape=ellipse, style=filled, fillcolor="%s", label="Export the JSON report"]; }
  eng -> {u1 u2 u8}; team -> {u3 u4 u6 u7}; lab -> u5;
}""" % tuple([FILL["stage"]] * 8))


def gantt() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    from datetime import date
    # end dates are commits in the code and paper repositories; start dates are the team's estimates
    phases = [
        ("Problem study and literature survey", date(2026, 1, 12), date(2026, 2, 19), "Capstone I"),
        ("Prototype: detection, RCA, first dashboard", date(2026, 2, 1), date(2026, 2, 20), "Capstone I"),
        ("Geographic drift, project documentation", date(2026, 3, 2), date(2026, 3, 23), "Capstone I"),
        ("Image pipeline: CLEAR-10, embeddings, CAM", date(2026, 3, 9), date(2026, 3, 25), "Capstone I"),
        ("First paper draft (IEEE template)", date(2026, 8, 17), date(2026, 9, 9), "Capstone II"),
        ("Dashboard rebuild, reliability layer", date(2026, 8, 24), date(2026, 9, 7), "Capstone II"),
        ("Injection benchmark (design A)", date(2026, 8, 31), date(2026, 9, 8), "Capstone II"),
        ("Statistical redesign, baselines, design B,\ngas sensor data, second model", date(2026, 9, 14), date(2026, 10, 15), "Capstone II"),
        ("Error-control correction, full rerun", date(2026, 10, 14), date(2026, 10, 16), "Capstone II"),
        ("Journal and conference papers", date(2026, 10, 15), date(2026, 10, 26), "Capstone II"),
        ("Black book and final review", date(2026, 10, 27), date(2026, 11, 6), "Capstone II"),
    ]
    milestones = [(date(2026, 2, 20), "first commit"), (date(2026, 9, 8), "benchmark"), (date(2026, 10, 16), "results frozen"),
                  (date(2026, 10, 25), "ICMMDU deadline")]
    plt.rcParams.update({"font.family": "Liberation Serif", "font.size": 9})
    fig, ax = plt.subplots(figsize=(6.5, 3.9))
    colors = {"Capstone I": "#8fa9cf", "Capstone II": "#2f5b9a"}
    for i, (name, a, b, part) in enumerate(phases):
        ax.barh(i, (b - a).days + 1, left=mdates.date2num(a), height=0.55, color=colors[part], edgecolor="#1f2a3a", lw=0.5)
    ax.set_yticks(range(len(phases)), [p[0] for p in phases])
    ax.set_ylim(len(phases) - 0.4, -2.2)
    for k, (d, label) in enumerate(milestones):
        x = mdates.date2num(d)
        ax.axvline(x, color="#b04a2f", lw=0.7, ls="--")
        ax.text(x, -0.75 - 0.55 * (k % 3), f"{label} ", ha="right", va="center", fontsize=7, color="#b04a2f")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.set_xlim(mdates.date2num(date(2026, 1, 1)), mdates.date2num(date(2026, 11, 15)))
    ax.axvspan(mdates.date2num(date(2026, 4, 15)), mdates.date2num(date(2026, 7, 31)), color="#eeeeee", zorder=0)
    ax.text(mdates.date2num(date(2026, 6, 7)), len(phases) - 0.6, "semester break,\nexaminations", ha="center",
            fontsize=7, color="#555555")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=k) for k, c in colors.items()], loc="center", bbox_to_anchor=(0.42, 0.62), fontsize=7.5, frameon=False)
    ax.set_xlabel("2026")
    ax.grid(axis="x", color="#dddddd", lw=0.5)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "gantt.png", dpi=300)
    plt.close(fig)


def drift_types() -> None:
    """The four drift types on two-dimensional toy data, against the reference."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    rng = np.random.default_rng(7)

    def sample(n, prior=0.5, shift=(0.0, 0.0)):
        y = (rng.random(n) < prior).astype(int)
        x = rng.normal(0, 1, (n, 2)) + np.where(y[:, None] == 1, 1.4, -1.4) * np.array([1.0, 0.6])
        return x + np.array(shift), y

    plt.rcParams.update({"font.family": "Liberation Serif", "font.size": 8.5})
    fig, axes = plt.subplots(1, 5, figsize=(6.6, 1.75), sharex=True, sharey=True)
    xr, yr = sample(260)
    xc, yc = sample(260, shift=(1.6, 0.9))
    xc = np.vstack([xr[:0], xc])
    yc = (xc @ np.array([1.0, 0.6]) + rng.normal(0, 1.1, len(xc)) > 0).astype(int)
    xp, yp = sample(260, prior=0.82)
    xk, yk = sample(260)
    region = xk[:, 1] > 1.0
    yk = np.where(region, 1 - yk, yk)
    xn, yn = sample(260)
    flip = rng.random(len(yn)) < 0.2
    yn = np.where(flip, 1 - yn, yn)
    panels = [("(a) Reference", xr, yr, None), ("(b) Covariate shift", xc, yc, None), ("(c) Prior shift", xp, yp, None),
              ("(d) Concept drift", xk, yk, "region"), ("(e) Label noise", xn, yn, None)]
    for ax, (title, x, y, mark) in zip(axes, panels):
        ax.scatter(*x[y == 0].T, s=4, c="#2f5b9a", lw=0)
        ax.scatter(*x[y == 1].T, s=4, c="#d9822b", lw=0, marker="^")
        t = np.linspace(-5, 6, 10)
        ax.plot(t, -t / 0.6, color="#555555", lw=0.8, ls="--")
        if mark:
            ax.axhspan(1.0, 6, color="#f4d7d7", zorder=0)
        ax.set_title(title, fontsize=8.5)
        ax.set_xlim(-4.5, 5.5)
        ax.set_ylim(-4, 5)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.tight_layout(pad=0.3, w_pad=0.4)
    fig.savefig(OUT / "drift_types.png", dpi=300)
    plt.close(fig)


def paper_figures() -> None:
    ppeecs = REPO / "paper" / "ppeecs" / "figures"
    for src, dst in (("Fig02.png", "decision_path.png"), ("Fig03.png", "confusion.png"), ("FigS1.png", "audit_budget.png"),
                     ("Fig04.png", "timelines_2x2.png")):
        shutil.copy(ppeecs / src, OUT / dst)
    for name in ("gen_timelines", "gen_cam"):
        pdf = REPO / "paper" / "figures" / f"{name}.pdf"
        subprocess.run(["pdftoppm", "-r", "400", "-png", "-singlefile", str(pdf), str(OUT / name)], check=True)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    if "--screens" in sys.argv:
        import capture_screens
        capture_screens.main()
        return
    block_diagram()
    module_diagram()
    class_diagram()
    dataflow_diagram()
    flow_detection()
    flow_reliability_triage()
    usecase_diagram()
    gantt()
    drift_types()
    paper_figures()
    print("figures:", ", ".join(sorted(p.name for p in OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
