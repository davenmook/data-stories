"""One chart style for every story, in the look of davenoel.me.

Usage:
    import sys; sys.path.insert(0, "../tools")
    import style
    style.use()
    fig, ax = plt.subplots()
    ...
    style.credit(fig)                 # source line, bottom left
    style.save(fig, "charts/name")    # writes name.svg and name.png
"""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager

CARBON = "#131517"
RAISE = "#1B1E21"
GRID = "#2A2E33"
FG = "#ECEEEF"
FG2 = "#C9CDD0"
MUTED = "#8E9499"
SAGE = "#A9C4A1"
TEAL = "#33A6B8"
NEUTRAL = "#6B7177"

OOKLA_CREDIT = ("Data: Speedtest® by Ookla® Global Fixed and Mobile Network Performance Maps, "
                "CC BY-NC-SA 4.0")


def _font():
    """JetBrains Mono if it's installed, else whatever monospace is around."""
    names = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("JetBrains Mono", "IBM Plex Mono", "Menlo", "DejaVu Sans Mono"):
        if name in names:
            return name
    return "monospace"


def use():
    """Apply the site look to every chart drawn after this call."""
    mpl.rcParams.update({
        "figure.facecolor": CARBON,
        "axes.facecolor": CARBON,
        "savefig.facecolor": CARBON,
        "axes.edgecolor": GRID,
        "axes.labelcolor": FG2,
        "axes.titlecolor": FG,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 14,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "text.color": FG,
        "font.family": _font(),
        "font.size": 11,
        "legend.frameon": False,
        "legend.labelcolor": FG2,
        "axes.prop_cycle": mpl.cycler(color=[SAGE, TEAL, NEUTRAL, FG2]),
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "svg.fonttype": "none",
    })


def credit(fig, text=OOKLA_CREDIT, mark="davenoel.me"):
    """Source line bottom left, a small watermark bottom right (below the axis label)."""
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.text(0.01, 0.01, text, fontsize=7.5, color=MUTED, ha="left", va="bottom")
    fig.text(0.99, 0.01, mark, fontsize=8, color=SAGE, ha="right", va="bottom")


def save(fig, stem):
    """Write stem.svg (for the site) and stem.png (for GitHub and LinkedIn)."""
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "png"):
        fig.savefig(stem.with_suffix(f".{ext}"), bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print(f"saved {stem}.svg and {stem}.png")
