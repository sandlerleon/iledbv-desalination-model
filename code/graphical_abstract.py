#!/usr/bin/env python3
"""
Programmatic graphical abstract for the ILEDBV manuscript.

Built entirely with matplotlib shapes/text/arrows -- deliberately NOT a
general-purpose generative-AI image, consistent with Elsevier's current
graphical-abstract policy (reviewer item #13).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

fig, ax = plt.subplots(figsize=(9.5, 5.2))
ax.set_xlim(0, 10)
ax.set_ylim(0, 5.6)
ax.axis("off")

boxes = [
    (0.3, 3.6, 1.7, 1.2, "Seawater\n(subsurface\nintake)", "#DCE6F1"),
    (2.4, 3.6, 2.0, 1.2, "SWRO +\nisobaric PX", "#C6DBEF"),
    (4.8, 3.6, 2.1, 1.2, "Brine\nconcentration\n(NF, +50% rec.)", "#C6DBEF"),
    (7.3, 3.6, 2.1, 1.2, "Mg/Ca\nprecipitation", "#C6DBEF"),
    (7.3, 1.4, 2.1, 1.2, "MVC crystallizer\n(near-ZLD)", "#FDD9B5"),
    (4.8, 1.4, 2.1, 1.2, "Economic\ntrade-off\n(LCOW)", "#E2D6F3"),
]
for x, y, w, h, label, color in boxes:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.12",
                                 linewidth=1.2, edgecolor="#2E4057", facecolor=color))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=9.5, weight="bold")

arrow_kw = dict(arrowstyle="-|>", mutation_scale=16, color="#2E4057", lw=1.6)
ax.add_patch(FancyArrowPatch((2.0, 4.2), (2.4, 4.2), **arrow_kw))
ax.add_patch(FancyArrowPatch((4.4, 4.2), (4.8, 4.2), **arrow_kw))
ax.add_patch(FancyArrowPatch((6.9, 4.2), (7.3, 4.2), **arrow_kw))
ax.add_patch(FancyArrowPatch((8.35, 3.6), (8.35, 2.6), **arrow_kw))
ax.add_patch(FancyArrowPatch((7.3, 2.0), (6.9, 2.0), **arrow_kw))

ax.text(3.4, 3.35, "2.73 kWh/m$^3$\n(Case C)", ha="center", va="top", fontsize=9, color="#1F5C99", weight="bold")
ax.text(8.35, 1.15, "10.68 kWh/m$^3$ total\n(Case E, near-ZLD)", ha="center", va="top", fontsize=9, color="#B85C1A", weight="bold")
ax.text(5.85, 1.15, "\\$0.42/m$^3$ net\n(10% Mg(OH)$_2$ sellable)", ha="center", va="top", fontsize=9, color="#5B3E96", weight="bold")

ax.text(5.0, 5.25, "ILEDBV: subsurface-intake SWRO + isobaric PX + near-ZLD brine valorization",
        ha="center", va="top", fontsize=11.5, weight="bold")
ax.text(5.0, 0.35, "31% lower desalination-stage energy  —  but near-ZLD crystallization is the dominant system energy cost",
        ha="center", va="center", fontsize=9.5, style="italic", color="#333333")

plt.tight_layout()
plt.savefig("graphical_abstract.png", dpi=220)
print("saved graphical_abstract.png")
