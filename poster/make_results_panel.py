"""Results panel for the ResilientAI poster (Canva), drawn to fit its Results box.

The box is 20.96 cm x 7.83 cm; below its "RESULTS" label it leaves about 20.0 cm x 6.6 cm,
which is the size of this image. The background is transparent so the box's own gradient
shows through. Every number comes from paper/generated (the same source as the papers).

    python paper/poster/make_results_panel.py      -> paper/poster/results_panel.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "examples" / "paper"))
from build_ppeecs import load_results, parse_tabular  # noqa: E402

OUT = Path(__file__).with_name("results_panel.png")
WIDTH_CM, HEIGHT_CM, DPI = 20.0, 6.6, 600
INK, NAVY, LIGHT = "#1b1f3b", "#2e3a8c", "#9fb3e8"

METHODS = [("Ours (hierarchical tests)", "Ours"), ("Learned meta-classifier", "Meta-\nclassifier"),
           ("Error-rate monitoring", "Error-rate\nmonitoring"), ("BBSE first", "BBSE\nfirst"),
           ("Input monitoring", "Input\nmonitoring")]


def method_means():
    """Share of benchmark windows with the right type, averaged over 2 tasks x 2 models, per design."""
    t = parse_tabular("tab_methods")
    header = [c.text for c in t.rows[1].cells]
    rows = {r.cells[0].text: [c.text.rstrip("↑↓") for c in r.cells] for r in t.rows[2:]}
    means = {}
    for name, _ in METHODS:
        vals = rows[name]
        means[name] = {d: sum(float(vals[i]) for i, h in enumerate(header) if h.endswith(d)) / 4 for d in ("A", "B")}
    return means


def main() -> None:
    r = load_results()
    means = method_means()
    ctrl_flagged = sum(int(r[f"{k}-ctrl-ndrift"]) for k in ("inc", "inc-hgb", "emp", "emp-hgb", "gas", "gas-hgb",
                                                              "clr", "clr-hgb"))

    plt.rcParams.update({"font.family": "Noto Sans", "font.size": 8, "text.color": INK,
                         "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})
    fig = plt.figure(figsize=(WIDTH_CM / 2.54, HEIGHT_CM / 2.54), dpi=DPI)
    fig.patch.set_alpha(0)

    # left: correct drift type per method, matched against held-out drift
    ax = fig.add_axes([0.055, 0.21, 0.50, 0.62])
    ax.patch.set_alpha(0)
    x = range(len(METHODS))
    w = 0.38
    a = [means[m]["A"] for m, _ in METHODS]
    b = [means[m]["B"] for m, _ in METHODS]
    bars_a = ax.bar([i - w / 2 for i in x], a, w, color=NAVY, label="Matched drift (design A)")
    bars_b = ax.bar([i + w / 2 for i in x], b, w, color=LIGHT, edgecolor=NAVY, linewidth=0.6,
                    label="Held-out drift (design B)")
    for bars in (bars_a, bars_b):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5, f"{bar.get_height():.0f}",
                    ha="center", va="bottom", fontsize=6.5, fontweight="bold")
    ax.set_xticks(list(x), [short for _, short in METHODS], fontsize=6.8)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.tick_params(axis="y", labelsize=6.5, length=2)
    ax.tick_params(axis="x", length=0, pad=2)
    ax.set_ylabel("Windows with correct type (%)", fontsize=6.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK)
        ax.spines[side].set_linewidth(0.6)
    ax.grid(axis="y", color=INK, alpha=0.15, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=6.3, frameon=False, ncol=1, handlelength=1.2, borderaxespad=0)
    fig.text(0.055, 0.93, "Drift type diagnosis on the injection benchmark", fontsize=8.6, fontweight="bold")
    fig.text(0.055, 0.03, f"Mean over 2 census tasks × 2 model families, {r['bench-nreps']} replicates each.",
             fontsize=6)

    # right: headline numbers
    tiles = [
        (f"{r['bench-a-ours-min']}–{r['bench-a-ours-max']}%", "correct drift type on\nmatched drift"),
        (f"{r['bench-b-ours-min']}–{r['bench-b-ours-max']}%",
         f"on held-out drift, where the\nmeta-classifier falls to {r['bench-b-meta-min']}–{r['bench-b-meta-max']}%"),
        (f"{ctrl_flagged}", "control windows flagged on\n4 real datasets with 2 models"),
        (f"{r['rem-recent-correct']} / {r['rem-recent-n']}", "real settings where the\nretrain advice was right"),
    ]
    x0, y0, tw, th, gap = 0.605, 0.10, 0.185, 0.385, 0.012
    for k, (big, small) in enumerate(tiles):
        col, row = k % 2, 1 - k // 2
        tx, ty = x0 + col * (tw + gap), y0 + row * (th + gap * 3)
        fig.patches.append(FancyBboxPatch((tx, ty), tw, th, boxstyle="round,pad=0,rounding_size=0.02",
                                          transform=fig.transFigure, facecolor="white", alpha=0.72,
                                          edgecolor=NAVY, linewidth=0.7))
        fig.text(tx + tw / 2, ty + th * 0.66, big, ha="center", va="center", fontsize=12.5,
                 fontweight="bold", color=NAVY)
        fig.text(tx + tw / 2, ty + th * 0.27, small, ha="center", va="center", fontsize=6.3, linespacing=1.15)
    fig.text(x0, 0.93, "Key results", fontsize=8.6, fontweight="bold")
    fig.text(x0, 0.03, f"False verdicts on {r['det-ncontrols']} benchmark control windows: {r['diag-fa-pct']}% "
             f"(bound 2α = 10%).", fontsize=6)

    fig.savefig(OUT, dpi=DPI, transparent=True)
    print(f"{OUT.relative_to(ROOT)}: {WIDTH_CM} x {HEIGHT_CM} cm at {DPI} dpi")


if __name__ == "__main__":
    main()
