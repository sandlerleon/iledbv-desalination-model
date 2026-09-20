# -*- coding: utf-8 -*-
"""Figure 7: what flipped the conclusion, what drives the spread, and where the
architecture would work.

All three panels read attribution_results.json; nothing is drawn by hand.

    python make_attribution_figure.py
"""
import json

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = json.load(open("attribution_results.json"))
COMP = R["comparator"]
DPI = 300
plt.rcParams.update({"font.size": 8.5, "axes.labelsize": 9, "axes.titlesize": 9,
                     "legend.fontsize": 7.5, "xtick.labelsize": 8,
                     "ytick.labelsize": 8, "axes.linewidth": 0.8,
                     "font.family": "DejaVu Sans"})
BLUE, RED, GREY = "#1b6ca8", "#c1553b", "#8a8a8a"

fig, ax = plt.subplots(1, 3, figsize=(13.0, 3.9),
                       gridspec_kw={"width_ratios": [1.0, 1.15, 1.1]})

# ------------------------------------------------------------- A: ablation
abl = R["ablation"]
labels = ["original\nassumptions", "+ concentrator\ncorrected", "+ reagents\ncosted"]
vals = [a["lcow"] for a in abl]
cols = [GREY, BLUE, RED]
bars = ax[0].bar(range(3), vals, color=cols, width=0.58)
ax[0].axhline(COMP, color="#333333", lw=1.2, ls="--")
ax[0].text(2.42, COMP + 0.05, "conventional\ncomparator $%.2f" % COMP,
           ha="right", va="bottom", fontsize=7.4, color="#333333")
for i, a in enumerate(abl):
    off = 0.13 if abs(a["lcow"] - COMP) < 0.16 else 0.06
    ax[0].text(i, a["lcow"] + off, "$%.2f" % a["lcow"], ha="center", fontsize=8.4,
               fontweight="bold")
    if a["delta"] is not None:
        ax[0].annotate("", xy=(i, a["lcow"]), xytext=(i - 1, abl[i - 1]["lcow"]),
                       arrowprops=dict(arrowstyle="->", lw=1.0, color="#555555",
                                       connectionstyle="arc3,rad=-0.25"))
        ax[0].text(i - 0.5, max(a["lcow"], abl[i - 1]["lcow"]) * 0.55,
                   "%+.2f" % a["delta"], ha="center", fontsize=8, color="#555555")
ax[0].set_xticks(range(3))
ax[0].set_xticklabels(labels)
ax[0].set_ylabel("net LCOW (\$ m$^{-3}$)")
ax[0].set_ylim(0, 2.65)
ax[0].set_title("A   The reagent term, not the thermodynamics,\n      reverses the conclusion",
                loc="left", fontweight="bold")

# --------------------------------------------------------- B: attribution
rows = R["attribution"][::-1]
y = np.arange(len(rows))
rho = [r["spearman"] for r in rows]
cols = [RED if v > 0 else BLUE for v in rho]
ax[1].barh(y, rho, color=cols, height=0.62)
ax[1].axvline(0, color="#333333", lw=0.8)
ax[1].set_yticks(y)
ax[1].set_yticklabels([r["parameter"] for r in rows], fontsize=7.1)
ax[1].set_xlabel("Spearman rank correlation with net LCOW")
ax[1].set_xlim(-0.62, 0.62)
ax[1].set_title("B   What drives the spread", loc="left", fontweight="bold")
# mark the concentrator efficiency, which the paper spends longest on
k = next(i for i, r in enumerate(rows) if r["key"] == "eff2")
ax[1].annotate("concentrator efficiency:\nrank %d of %d"
               % (R["attribution_note"]["eff2_rank"], len(rows)),
               xy=(rho[k], y[k]), xytext=(0.13, y[k] - 2.1), fontsize=7.2,
               color="#444444",
               arrowprops=dict(arrowstyle="->", lw=0.8, color="#444444"))

# ------------------------------------------------------- C: admissibility
A = R["admissibility"]
rf = np.array(A["reagent_multiplier"])
cf = np.array(A["credit_multiplier"])
P = np.array(A["prob_beats_comparator"])
im = ax[2].pcolormesh(rf, cf, P.T, cmap="viridis", shading="auto", vmin=0, vmax=1)
cs = ax[2].contour(rf, cf, P.T, levels=[0.05, 0.5, 0.95], colors="white",
                   linewidths=1.0)
ax[2].clabel(cs, fmt=lambda v: "P=%.2f" % v, fontsize=6.8)
ax[2].plot([1.0], [1.0], "o", ms=7, color="#ffffff", markeredgecolor="#c1553b",
           markeredgewidth=1.6, zorder=6)
ax[2].annotate("modelled plant\n%s of %s"
               % (format(R["n_beating_comparator"], ","), format(R["n"], ",")),
               xy=(0.96, 1.01), xytext=(0.06, 0.72), fontsize=7.2, color="white",
               ha="left", va="center",
               arrowprops=dict(arrowstyle="->", lw=1.0, color="white"))
need = A["credit_needed_at_full_reagent_cost"]
ax[2].plot([1.0], [need], "s", ms=6, color="#ffd166", markeredgecolor="#333333",
           markeredgewidth=0.8, zorder=6)
ax[2].annotate("%.1f× mineral value\nreaches the comparator" % need,
               xy=(0.97, need), xytext=(0.06, 3.40), fontsize=7.2,
               color="white", ha="left",
               arrowprops=dict(arrowstyle="->", lw=1.0, color="white"))
ax[2].set_xlabel("reagent cost, relative to modelled")
ax[2].set_ylabel("mineral value, relative to modelled")
ax[2].set_title("C   Where it would beat the comparator", loc="left",
                fontweight="bold")
cb = fig.colorbar(im, ax=ax[2], pad=0.02)
cb.set_label("P(net LCOW < $%.2f)" % COMP, fontsize=8)

for a in ax[:2]:
    a.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("figure7_attribution.png", dpi=DPI, bbox_inches="tight")
print("figure7_attribution.png")
