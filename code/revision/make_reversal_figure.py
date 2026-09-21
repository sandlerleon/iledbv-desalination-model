# -*- coding: utf-8 -*-
"""Figure 8: what would reverse the conclusion, and what would not.

    python make_reversal_figure.py
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "reversal_results.json")))
DPI = 300
plt.rcParams.update({"font.size": 8.5, "axes.labelsize": 9, "axes.titlesize": 9,
                     "legend.fontsize": 7.6, "xtick.labelsize": 8,
                     "ytick.labelsize": 8, "axes.linewidth": 0.8,
                     "font.family": "DejaVu Sans"})
BLUE, RED, GREEN, GREY = "#1b6ca8", "#c1553b", "#3f8f4a", "#8a8a8a"
COMP = R["comparator"]

fig, ax = plt.subplots(1, 2, figsize=(9.8, 3.8))

# ------------------------------------------- A: LCOW against electricity price
e = np.linspace(0.0, 0.13, 400)
lc_A = R["capex"] + R["sec_base"] * e + R["reagent_A"] + R["fixed_opex"] - R["credit"]
lc_D = R["capex"] + R["sec_route_D"] * e + R["reagent_D"] + R["fixed_opex"] - R["credit"]
ax[0].axhspan(-0.8, COMP, color=GREEN, alpha=0.07)
ax[0].axvspan(0.0104, 0.0150, color="#ffd166", alpha=0.35)
ax[0].text(0.0127, -0.63, "Gulf solar\nPPA range", ha="center", fontsize=7.0,
           color="#8a6d1f")
ax[0].plot(e, lc_A, color=RED, lw=1.9,
           label="A  soda ash + lime (as published)")
ax[0].plot(e, lc_D, color=BLUE, lw=1.9,
           label="D  dosed CO$_2$ + electrochemical base")
ax[0].axhline(COMP, color="#333333", lw=1.2, ls="--")
ax[0].text(0.128, COMP + 0.09, "conventional SWRO $%.2f" % COMP, ha="right",
           fontsize=7.4, color="#333333")
# route A never reaches the comparator
ax[0].plot([0], [lc_A[0]], "o", ms=6, color=RED, markeredgecolor="white",
           markeredgewidth=0.8, zorder=6)
ax[0].annotate("even at zero electricity cost\nroute A is $%.2f above" % (lc_A[0] - COMP),
               xy=(0.0015, lc_A[0]), xytext=(0.043, 0.98), fontsize=7.3, color=RED,
               arrowprops=dict(arrowstyle="->", lw=0.9, color=RED))
b = R["breakeven_D"]
ax[0].plot([b], [COMP], "o", ms=6, color=BLUE, markeredgecolor="white",
           markeredgewidth=0.8, zorder=6)
ax[0].annotate("route D crosses at\n$%.3f/kWh" % b, xy=(b, COMP),
               xytext=(0.055, -0.35), fontsize=7.3, color=BLUE,
               arrowprops=dict(arrowstyle="->", lw=0.9, color=BLUE))
ax[0].set_xlim(0, 0.13)
ax[0].set_ylim(-0.8, 3.4)
ax[0].set_xlabel("electricity price (\$ kWh$^{-1}$)")
ax[0].set_ylabel("net LCOW (\$ m$^{-3}$)")
ax[0].set_title("A   Only the electrochemical route can cross",
                loc="left", fontweight="bold")
ax[0].legend(frameon=False, loc="upper left")

# --------------------------------- B: how much of that depends on the credit
fracs = np.linspace(0.0, 1.0, 41)
be = []
for f in fracs:
    c = R["credit"] * f
    floor = R["capex"] + R["reagent_D"] + R["fixed_opex"] - c
    be.append((COMP - floor) / R["sec_route_D"] if floor < COMP else np.nan)
be = np.array(be)
ax[1].plot(100 * fracs, 1000 * be, color=BLUE, lw=1.9)
ax[1].axhspan(10.4, 15.0, color="#ffd166", alpha=0.35)
ax[1].text(4, 12.7, "Gulf solar PPA range", fontsize=7.2, color="#8a6d1f",
           va="center")
ax[1].set_xlabel("realisable mineral credit (% of modelled value)")
ax[1].set_ylabel("electricity price needed to reach $%.2f (\\$/MWh)" % COMP)
ax[1].set_title("B   The reversal does not rest on the credit alone",
                loc="left", fontweight="bold")
ax[1].set_xlim(0, 100)
ax[1].set_ylim(0, 38)
for f, lab in [(1.0, "full credit"), (0.5, "half credit"), (0.0, "no credit")]:
    i = int(round(f * (len(fracs) - 1)))
    if np.isfinite(be[i]):
        ax[1].plot([100 * fracs[i]], [1000 * be[i]], "o", ms=5, color=RED,
                   markeredgecolor="white", markeredgewidth=0.7, zorder=6)
        ax[1].annotate("%s\n$%.1f/MWh" % (lab, 1000 * be[i]),
                       xy=(100 * fracs[i], 1000 * be[i]),
                       xytext=(100 * fracs[i] - (30 if f > 0.6 else -6),
                               1000 * be[i] + (5 if f < 0.9 else -6)),
                       fontsize=7.0, color="#444444")

for a in ax:
    a.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
out = os.path.join(HERE, "figure8_reversal.png")
fig.savefig(out, dpi=DPI, bbox_inches="tight")
print(os.path.basename(out))
