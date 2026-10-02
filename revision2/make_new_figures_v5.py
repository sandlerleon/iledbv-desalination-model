# -*- coding: utf-8 -*-
"""Revision 2 (Reviewer 4, comment 3): convert quantitative results that the v4
manuscript carried only as tables or prose into figures.

Two new figures and a graphical abstract. Every number plotted here is read from
a table already in ILEDBV_Manuscript_Revised_v4.docx -- nothing is recomputed and
no new result is introduced.

  new Fig. 2  stream composition profile            <- Table 1
  new Fig. 7  OPEX composition and cost waterfall   <- Table 5 (a), Table 8 (b)
  graphical abstract                                <- Sections 4.5, 4.6, 4.7, 4.13

    python make_new_figures_v5.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures_v5")
os.makedirs(OUT, exist_ok=True)

BLUE = "#1f77b4"
ORANGE = "#ff7f0e"
GREY = "#7f8c9b"
RED = "#c0392b"
GREEN = "#2e7d4f"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 100,
})


def save(fig, stem):
    png = os.path.join(OUT, stem + ".png")
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    try:
        fig.savefig(os.path.join(OUT, stem + ".tif"), dpi=300,
                    bbox_inches="tight", facecolor="white", pil_kwargs={"compression": "tiff_lzw"})
    except Exception as exc:          # TIFF is a convenience, not a requirement
        print("   (tif skipped: %s)" % exc)
    plt.close(fig)
    print("wrote", png)


# ===================================================== new Figure 2: Table 1
# Stream | TDS | Mg2+ | Ca2+   (g L-1), per cubic metre of raw seawater
STREAMS = ["S1\nraw\nseawater", "S2\nRO\npermeate", "S3\nRO\nbrine",
           "S4\nconc.\npermeate", "S5\nconc.\nconcentrate", "S6\ncrystallizer\nfeed"]
TDS = [35.1, 0.2, 63.7, 5.7, 121.7, 124.8]
MG = [1.284, 0.004, 2.331, 0.047, 4.616, 0.092]
CA = [0.412, 0.001, 0.748, 0.015, 1.481, 7.534]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.6))

x = np.arange(len(STREAMS))
bars = ax1.bar(x, TDS, color=[GREY] * 4 + [BLUE, ORANGE], width=0.62,
               edgecolor="white", linewidth=0.8)
for xi, v in zip(x, TDS):
    ax1.text(xi, v + 2.5, "%.1f" % v, ha="center", va="bottom",
             fontsize=11, fontweight="bold")
ax1.set_xticks(x)
ax1.set_xticklabels(STREAMS, fontsize=10)
ax1.set_ylabel("Total dissolved solids (g L$^{-1}$)")
ax1.set_ylim(0, 164)
ax1.set_title("(a)  Salinity through the train", loc="left", fontweight="bold")
ax1.grid(axis="y", alpha=0.3)
ax1.set_axisbelow(True)
ax1.annotate("", xy=(5.32, 137), xytext=(3.68, 137),
             arrowprops=dict(arrowstyle="->", color=RED, lw=1.8))
ax1.text(4.5, 141, "TDS rises across\nthe precipitation train", ha="center", va="bottom",
         fontsize=10.5, color=RED)

w = 0.36
ax2.bar(x - w / 2, MG, w, label="Mg$^{2+}$", color=BLUE,
        edgecolor="white", linewidth=0.8)
ax2.bar(x + w / 2, CA, w, label="Ca$^{2+}$", color=ORANGE,
        edgecolor="white", linewidth=0.8)
ax2.set_xticks(x)
ax2.set_xticklabels(STREAMS, fontsize=10)
ax2.set_ylabel("Concentration (g L$^{-1}$)")
ax2.set_ylim(0, 9.4)
ax2.set_title("(b)  Divalent cations: the calcium reversal", loc="left", fontweight="bold")
ax2.legend(frameon=False, loc="upper left")
ax2.grid(axis="y", alpha=0.3)
ax2.set_axisbelow(True)
ax2.text(4.0 + w / 2, 4.616 + 0.25, "4.62", ha="center", fontsize=10.5, color=BLUE)
ax2.text(5.0 - w / 2, 0.092 + 0.25, "0.09", ha="center", fontsize=10.5, color=BLUE)
ax2.text(4.0 - w / 2 + w, 1.481 + 0.25, "1.48", ha="center", fontsize=10.5, color=ORANGE)
ax2.text(5.0 + w / 2, 7.534 + 0.25, "7.53", ha="center", fontsize=11,
         fontweight="bold", color=ORANGE)
ax2.annotate("lime returns one Ca$^{2+}$\nper Mg$^{2+}$ precipitated:\n$\\times$5.1 across S5$\\rightarrow$S6",
             xy=(4.98, 6.55), xytext=(1.70, 6.05),
             fontsize=10.5, color=RED, ha="left",
             arrowprops=dict(arrowstyle="->", color=RED, lw=1.6,
                             connectionstyle="arc3,rad=-0.18"))

save(fig, "figure2_stream_profile")


# ===================================================== new Figure 7: Tables 5 and 8
OPEX_ITEMS = [
    ("Precipitation reagents", 1.580),
    ("Electricity", 1.049),
    ("Maintenance and spares", 0.055),
    ("Labor", 0.045),
    ("Membrane replacement", 0.040),
    ("Solids handling and logistics", 0.035),
    ("Pretreatment and CIP chemicals", 0.030),
    ("Insurance and overhead", 0.020),
    ("Cartridge filters, consumables", 0.010),
]
GROSS, CREDIT, NET = 3.462, 1.252, 2.198
NET_LO, NET_HI = 1.383, 3.010
COMPARATOR = 0.76

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8),
                               gridspec_kw={"width_ratios": [1.18, 1.0]})

labels = [k for k, _ in OPEX_ITEMS][::-1]
vals = [v for _, v in OPEX_ITEMS][::-1]
cols = [ORANGE if k == "Precipitation reagents" else
        (BLUE if k == "Electricity" else GREY) for k in labels]
y = np.arange(len(labels))
ax1.barh(y, vals, color=cols, height=0.68, edgecolor="white", linewidth=0.8)
for yi, v in zip(y, vals):
    ax1.text(v + 0.03, yi, "%.3f" % v, va="center", fontsize=10.5,
             fontweight="bold" if v > 0.5 else "normal")
ax1.set_yticks(y)
ax1.set_yticklabels(labels, fontsize=11)
ax1.set_xlabel(r"\$ per m$^{3}$ permeate")
ax1.set_xlim(0, 1.86)
ax1.set_title("(a)  Operating cost composition\n" + r"(total \$2.864 m$^{-3}$)",
              loc="left", fontweight="bold")
ax1.grid(axis="x", alpha=0.3)
ax1.set_axisbelow(True)

steps = [("Gross\nLCOW", GROSS, 0.0, BLUE),
         ("Mineral\ncredit", -CREDIT, NET, GREEN),
         ("Net\nLCOW", NET, 0.0, ORANGE)]
for i, (lab, h, bot, c) in enumerate(steps):
    ax2.bar(i, abs(h), bottom=bot, color=c, width=0.58,
            edgecolor="white", linewidth=0.8)
    top = bot + abs(h)
    ax2.text(i, top + 0.09, ("%.2f" % abs(h)) if i != 1 else ("-%.2f" % CREDIT),
             ha="center", fontsize=12, fontweight="bold",
             color=GREEN if i == 1 else "black")
ax2.plot([0.29, 0.71], [GROSS, GROSS], color="0.4", lw=1.0, ls=":")
ax2.plot([1.29, 1.71], [NET, NET], color="0.4", lw=1.0, ls=":")
ax2.errorbar(2, NET, yerr=[[NET - NET_LO], [NET_HI - NET]], fmt="none",
             ecolor="0.25", elinewidth=1.6, capsize=7, capthick=1.6)
ax2.text(2.34, NET_HI, "95th", fontsize=9.5, va="center", color="0.25")
ax2.text(2.34, NET_LO, "5th", fontsize=9.5, va="center", color="0.25")
ax2.axhline(COMPARATOR, color=RED, ls="--", lw=1.8)
ax2.text(2.46, COMPARATOR + 0.07, r"conventional SWRO, \$0.76 m$^{-3}$",
         color=RED, fontsize=10.5, ha="right")
ax2.set_xticks(range(3))
ax2.set_xticklabels([s[0] for s in steps], fontsize=11)
ax2.set_ylabel(r"Levelized cost (\$ m$^{-3}$)")
ax2.set_ylim(0, 4.0)
ax2.set_title("(b)  Monte Carlo medians, 300,000 samples",
              loc="left", fontweight="bold")
ax2.grid(axis="y", alpha=0.3)
ax2.set_axisbelow(True)

save(fig, "figure7_cost_structure")


# ===================================================== graphical abstract
fig, ax = plt.subplots(figsize=(13.5, 5.4))
ax.set_xlim(0, 100)
ax.set_ylim(0, 40)
ax.axis("off")

ax.text(50, 37.4, "Three consistency tests on an integrated SWRO–brine valorization architecture",
        ha="center", va="center", fontsize=15.5, fontweight="bold")

CARDS = [
    (4.0, "Test 1   Energy",
     "Assumed concentrator duty\n0.5–1.0 kWh m$^{-3}$ brine\nvs least work 0.94",
     "FAILS", RED),
    (36.0, "Test 2   Boundary layer",
     "Ceiling on eliminating\npolarization entirely\n0.39 kWh m$^{-3}$, 13% of stage",
     "PASSES", GREEN),
    (68.0, "Test 3   Alkalinity",
     "2 eq base per mol Mg(OH)$_2$\nlime returns 5.3× the Ca\nthe carbonate step removes",
     "FAILS", RED),
]
for x0, title, body, verdict, col in CARDS:
    ax.add_patch(FancyBboxPatch((x0, 15.0), 28.0, 17.2,
                                boxstyle="round,pad=0.45,rounding_size=1.1",
                                linewidth=1.9, edgecolor=col, facecolor="#f7f9fb"))
    ax.text(x0 + 14.0, 30.1, title, ha="center", va="center",
            fontsize=12.6, fontweight="bold")
    ax.text(x0 + 14.0, 23.8, body, ha="center", va="center", fontsize=10.8)
    ax.text(x0 + 14.0, 17.2, verdict, ha="center", va="center",
            fontsize=12.4, fontweight="bold", color=col)
    ax.add_patch(FancyArrowPatch((x0 + 14.0, 14.6), (x0 + 14.0, 11.4),
                                 arrowstyle="-|>", mutation_scale=17,
                                 linewidth=1.7, color="0.45"))

ax.add_patch(FancyBboxPatch((4.0, 2.2), 92.0, 8.9,
                            boxstyle="round,pad=0.45,rounding_size=1.1",
                            linewidth=2.2, edgecolor=ORANGE, facecolor="#fff6ec"))
ax.text(50, 8.5, "Alkalinity, not thermodynamics, is the binding constraint",
        ha="center", va="center", fontsize=13.6, fontweight="bold")
ax.text(50, 5.9,
        "Reagents " + r"\$1.70 m$^{-3}$" + " exceed the " + r"\$1.25 m$^{-3}$" +
        " mineral credit   •   net LCOW " + r"\$2.20 m$^{-3}$" +
        " against " + r"\$0.76 m$^{-3}$",
        ha="center", va="center", fontsize=11.3)
ax.text(50, 3.4,
        "Closing the calcium balance costs " + r"\$0.44 m$^{-3}$" +
        "; no on-site base closes the loop above " + r"\$0.069 kWh$^{-1}$",
        ha="center", va="center", fontsize=11.3)

save(fig, "graphical_abstract")
print("\nAll figures written to", OUT)
