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
           ("Error-rate monitoring", "Error-rate\nmonitor"), ("BBSE first", "BBSE\nfirst"),
           ("Input monitoring", "Input\nmonitor")]


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
    ax = fig.add_axes([0.045, 0.17, 0.50, 0.63])
    ax.patch.set_alpha(0)
    x = range(len(METHODS))
    w = 0.4
    a = [means[m]["A"] for m, _ in METHODS]
    b = [means[m]["B"] for m, _ in METHODS]
    bars_a = ax.bar([i - w / 2 for i in x], a, w, color=NAVY, label="Matched drift")
    bars_b = ax.bar([i + w / 2 for i in x], b, w, color=LIGHT, edgecolor=NAVY, linewidth=0.7,
                    label="Held-out drift")
    for bars in (bars_a, bars_b):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5, f"{bar.get_height():.0f}",
                    ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_xticks(list(x), [short for _, short in METHODS], fontsize=9)
    ax.set_ylim(0, 118)
    ax.set_yticks([0, 50, 100])
    ax.tick_params(axis="y", labelsize=8.5, length=2)
    ax.tick_params(axis="x", length=0, pad=2)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK)
        ax.spines[side].set_linewidth(0.7)
    ax.grid(axis="y", color=INK, alpha=0.15, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9, frameon=False, ncol=2, handlelength=1.1, columnspacing=1.0,
              borderaxespad=0, bbox_to_anchor=(1.0, 1.08))
    fig.text(0.045, 0.9, "Correct drift type (%)", fontsize=12, fontweight="bold")

    # right: headline numbers
    tiles = [
        (f"{r['bench-a-ours-min']}–{r['bench-a-ours-max']}%", "correct type,\nmatched drift"),
        (f"{r['bench-b-ours-min']}–{r['bench-b-ours-max']}%",
         f"held-out drift\n(meta-classifier:\n{r['bench-b-meta-min']}–{r['bench-b-meta-max']}%)"),
        (f"{ctrl_flagged}", "false alarms on\nreal control data"),
        (f"{r['rem-recent-correct']} / {r['rem-recent-n']}", "correct retrain\nadvice, real data"),
    ]
    x0, y0, tw, th, gap = 0.578, 0.04, 0.198, 0.39, 0.015
    for k, (big, small) in enumerate(tiles):
        col, row = k % 2, 1 - k // 2
        tx, ty = x0 + col * (tw + gap), y0 + row * (th + gap * 3)
        fig.patches.append(FancyBboxPatch((tx, ty), tw, th, boxstyle="round,pad=0,rounding_size=0.02",
                                          transform=fig.transFigure, facecolor="white", alpha=0.75,
                                          edgecolor=NAVY, linewidth=0.8))
        fig.text(tx + tw / 2, ty + th * 0.74, big, ha="center", va="center", fontsize=16,
                 fontweight="bold", color=NAVY)
        fig.text(tx + tw / 2, ty + th * 0.31, small, ha="center", va="center", fontsize=9, linespacing=1.1)

    fig.savefig(OUT, dpi=DPI, transparent=True)
    print(f"{OUT.relative_to(ROOT)}: {WIDTH_CM} x {HEIGHT_CM} cm at {DPI} dpi")


if __name__ == "__main__":
    main()
