# -*- coding: utf-8 -*-
"""Figure 9 from alkalinity_calcium_results.json.

(A) cost of one kmol of OH- by source against electricity price.
(B) net LCOW of the calcium-closed optimum over electricity price and the
    on-site alkalinity yield (mol OH- per kWh), with the comparator contour,
    the chlor-alkali basis of Section 4.12 and the reversible limit.

    python make_alkalinity_figure.py
"""
import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "figures", "figure9_alkalinity_calcium.png")
R = json.load(io.open(os.path.join(HERE, "alkalinity_calcium_results.json"), encoding="utf-8"))

u = {r["p_e"]: r for r in R["usd_per_kmol_OH"]}
lime = u[0.08]["lime_usd"]
naoh = u[0.08]["naoh_usd"]
rev = R["reversible_limit"]["max_mol_OH_per_kWh"]

fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.6))

pe = np.linspace(0.0, 0.12, 200)
a = ax[0]
a.axhline(lime, color="#8c6d31", lw=2, label="Ca(OH)$_2$ (imports 0.5 Ca per OH$^-$)")
a.axhline(naoh, color="#7f7f7f", lw=2, ls="--", label="purchased NaOH")
for mol, c, lab in ((10.0, "#1f77b4", "on-site, 10 mol kWh$^{-1}$ (chlor-alkali basis)"),
                    (20.0, "#2ca02c", "on-site, 20 mol kWh$^{-1}$"),
                    (rev, "#d62728", "on-site at reversible limit, %.0f mol kWh$^{-1}$" % rev)):
    a.plot(pe, pe * 1000.0 / mol, color=c, lw=1.8, label=lab)
a.set_xlabel(r"Electricity price (\$ kWh$^{-1}$)")
a.set_ylabel(r"Cost of alkalinity (\$ per kmol OH$^-$)")
a.set_xlim(0, 0.12); a.set_ylim(0, 22)
a.legend(fontsize=7.5, loc="upper left", frameon=False)
a.set_title("A   Cost per unit of base, by source", loc="left", fontsize=10)

m = R["map"]
P, M = np.meshgrid(m["p_e"], m["mol_OH_per_kWh"])
Z = np.array(m["lcow_net"])
b = ax[1]
cs = b.contourf(P, M, Z, levels=np.arange(-0.6, 3.01, 0.2), cmap="RdYlGn_r")
cl = b.contour(P, M, Z, levels=[0.76],
               colors="k", linewidths=1.8)
b.clabel(cl, fmt={0.76: r"conventional SWRO, \$0.76 m$^{-3}$"}, fontsize=7.5)
b.axhspan(rev, 60, color="white", alpha=0.75, hatch="//", lw=0)
b.axhline(rev, color="#d62728", lw=1.2)
b.text(0.007, rev + 1.5, "above the reversible limit", fontsize=7.5, color="#d62728")
b.axhline(10.0, color="#1f77b4", lw=1.2, ls="--")
b.text(0.007, 11.0, "chlor-alkali basis (Section 4.12)", fontsize=7.5, color="#1f77b4")
for x, lab in ((0.015, "Gulf solar PPA"), (0.048, "Saudi industrial"), (0.08, "model base")):
    b.axvline(x, color="0.3", lw=0.8, ls=":")
    b.text(x + 0.001, 57, lab, rotation=90, va="top", fontsize=7)
fig.colorbar(cs, ax=b, label=r"Net LCOW, calcium balance closed (\$ m$^{-3}$)")
b.set_xlabel(r"Electricity price (\$ kWh$^{-1}$)")
b.set_ylabel("On-site alkalinity yield (mol OH$^-$ kWh$^{-1}$)")
b.set_title("B   Where the closed loop reaches the comparator", loc="left", fontsize=10)

fig.tight_layout()
fig.savefig(OUT, dpi=300)
fig.savefig(OUT.replace(".png", ".tif"), dpi=300, pil_kwargs={"compression": "tiff_lzw"})
print("saved", os.path.abspath(OUT))
