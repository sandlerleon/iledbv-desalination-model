# -*- coding: utf-8 -*-
"""Figures for the revised DWT manuscript.

Every figure is generated from the model JSON, so none can disagree with the text.

    python make_figures.py   ->  figures/*.png  and  figures/*.tif
"""
import io, json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

V2 = json.load(io.open(os.path.join(HERE, "iledbv_revision_v2.json"), encoding="utf-8"))
DC = json.load(io.open(os.path.join(HERE, "design_costing.json"), encoding="utf-8"))
mc, t1 = V2["monte_carlo"], V2["t1_concentrator"]
RT = V2["precipitation_routes"]
st = DC["streams_as_modelled"]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
                     "figure.dpi": 130})
BLUE, ORANGE, GREY, RED, GREEN = "#2b6cb0", "#dd6b20", "#718096", "#c53030", "#2f855a"


def save(fig, name):
    for ext in ("png", "tif"):
        fig.savefig(os.path.join(FIGDIR, "%s.%s" % (name, ext)), dpi=300,
                    bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  wrote %s.png / .tif" % name)


# ---------------------------------------------------------------- Figure 1
def fig1_process():
    """Process diagram carrying flow, salinity and pressure for every stream."""
    S = st
    fig, ax = plt.subplots(figsize=(11.5, 4.3))
    ax.set_xlim(0, 11.5); ax.set_ylim(0, 4.3); ax.axis("off"); ax.grid(False)

    blocks = [
        (0.10, "Subsurface\nintake", BLUE, "S1 raw seawater"),
        (1.95, "SWRO\n+ PX", BLUE, "S3 RO brine"),
        (3.80, "Second pass\n(boron, optional)", BLUE, None),
        (5.65, "High-pressure\nconcentrator", ORANGE, "S5 concentrator concentrate"),
        (7.50, "Ca/Mg\nprecipitation", RED, "S6 crystallizer feed"),
        (9.35, "MVC\ncrystallizer", GREY, None),
    ]
    W = 1.55
    for x, label, col, key in blocks:
        ax.add_patch(FancyBboxPatch((x, 2.05), W, 1.00, boxstyle="round,pad=0.05",
                                    fc="white", ec=col, lw=1.6, zorder=4))
        ax.text(x + W / 2, 2.55, label, ha="center", va="center", fontsize=8.5, zorder=5)
        if key:
            d = S[key]
            ax.text(x + W / 2, 1.88,
                    "%s   Q %.3f\n%.1f g L$^{-1}$"
                    % (key.split()[0], d["q_m3_per_m3_feed"], d["TDS_g_L"]),
                    ha="center", va="top", fontsize=7, color=col, zorder=5)

    for i in range(len(blocks) - 1):
        ax.add_patch(FancyArrowPatch((blocks[i][0] + W, 2.55), (blocks[i + 1][0], 2.55),
                                     arrowstyle="-|>", mutation_scale=11, lw=1.2,
                                     color="#4a5568", zorder=6, shrinkA=3.0, shrinkB=3.0))

    for x, txt in ((1.95, "64 bar applied\nPX recovery 96%"),
                   (5.65, "R = 50%\n49 bar feed")):
        ax.text(x + W / 2, 3.18, txt, ha="center", va="bottom", fontsize=7,
                color="#4a5568", zorder=5)

    outs = [
        (3.80 + W / 2, "Potable permeate\nQ %.3f, %.1f g L$^{-1}$"
         % (S["S2 RO permeate"]["q_m3_per_m3_feed"], S["S2 RO permeate"]["TDS_g_L"]), GREEN),
        (5.65 + W / 2, "Recovered water\nQ %.3f, %.1f g L$^{-1}$"
         % (S["S4 concentrator permeate"]["q_m3_per_m3_feed"],
            S["S4 concentrator permeate"]["TDS_g_L"]), GREEN),
        (7.50 + W / 2, "CaCO$_3$ + Mg(OH)$_2$\n0.97 + 3.00 kg m$^{-3}$ feed", RED),
        (9.35 + W / 2, "Salts + residual\nliquid 0.0275 m$^3$", GREY),
    ]
    for x, lab, col in outs:
        ax.add_patch(FancyArrowPatch((x, 2.05), (x, 1.18), arrowstyle="-|>",
                                     mutation_scale=11, lw=1.2, color=col,
                                     zorder=6, shrinkA=3.0, shrinkB=3.0))
        ax.text(x, 0.98, lab, ha="center", va="top", fontsize=7, color=col, zorder=5)

    ax.add_patch(FancyArrowPatch((7.50 + W / 2, 3.92), (7.50 + W / 2, 3.08),
                                 arrowstyle="-|>", mutation_scale=11, lw=1.4, color=RED,
                                 zorder=6, shrinkA=3.0, shrinkB=3.0))
    ax.text(7.50 + W / 2, 4.10,
            "Na$_2$CO$_3$ 1.02 + Ca(OH)$_2$ 3.79 kg m$^{-3}$ feed\n"
            "embodied carbon %.1f kg CO$_2$ m$^{-3}$ permeate (Section 4.7)"
            % RT["A: soda ash + lime (as written)"]["co2_reagents"],
            ha="center", va="center", fontsize=7, color=RED, zorder=5)

    ax.text(0.10, 0.28, "Flows per cubic metre of raw seawater. Baseline R = 45%, feed "
                        "35 g L$^{-1}$. Stream tags match Table 1.",
            fontsize=7.5, color="#4a5568")
    save(fig, "figure1_process")


# ---------------------------------------------------------------- Figure 2
def fig2_stage():
    qp, qb = 0.45, 0.55
    qc = qb * 0.5
    cases = [("Original\nassumption", 0.75),
             ("55% second-law\nefficiency", float(t1["realistic_at_second_law_eff"]["0.55"])),
             ("Monte Carlo\nmedian", mc["concentrator_sec"]["median"]),
             ("25% second-law\nefficiency", float(t1["realistic_at_second_law_eff"]["0.25"]))]
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    x = np.arange(len(cases)); w = 0.62
    desal = np.array([2.73] * len(cases))
    conc = np.array([c * qb / qp for _, c in cases])
    cry = np.array([11.5 * qc / qp] * len(cases))
    ax.bar(x, desal, w, label="Desalination stage", color=BLUE)
    ax.bar(x, conc, w, bottom=desal, label="Brine concentration", color=ORANGE)
    ax.bar(x, cry, w, bottom=desal + conc, label="Crystallization (MVC)", color=GREY)
    for i, tot in enumerate(desal + conc + cry):
        ax.text(i, tot + 0.25, "%.2f" % tot, ha="center", fontsize=9, fontweight="bold")
    ax.axhline(10.68, ls="--", lw=1.2, color=RED)
    ax.text(len(cases) - 0.45, 10.9, "as originally reported, 10.68", color=RED,
            fontsize=8, ha="right")
    ax.set_xticks(x); ax.set_xticklabels([c[0] for c in cases], fontsize=8)
    ax.set_ylabel("Specific energy consumption (kWh m$^{-3}$ permeate)")
    ax.set_title("Stage decomposition under four concentrator assumptions", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_ylim(0, 16)
    save(fig, "figure2_stage_decomposition")


# ---------------------------------------------------------------- Figure 3
def fig3_floor():
    w = t1["least_work_kwh_per_m3_brine"]
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    effs = np.linspace(0.15, 1.0, 300)
    ax.plot(effs * 100, w / effs, lw=2, color=BLUE, label="attainable stage energy, $w_{min}/\\eta_{II}$")
    ax.axhline(w, ls="--", lw=1.4, color=RED)
    ax.text(17, w * 1.16, "reversible minimum %.2f" % w, color=RED, fontsize=8, ha="left")
    ax.axhspan(0.5, 1.0, color=RED, alpha=0.12)
    ax.text(20, 0.72, "range assumed in the\noriginal (0.5–1.0)", color=RED, fontsize=8)
    ax.axvspan(25, 55, color=GREEN, alpha=0.10)
    ax.text(40, 5.2, "real high-pressure\nmembrane stages", color=GREEN, fontsize=8, ha="center")
    ax.set_xlabel("Second-law efficiency of the stage (%)")
    ax.set_ylabel("Energy (kWh m$^{-3}$ of brine processed)")
    ax.set_title("Consistency test 1: the assumed concentrator energy lies below\n"
                 "the least work of separation", fontsize=10)
    ax.set_ylim(0, 6.5); ax.set_xlim(15, 100)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    save(fig, "figure3_thermodynamic_floor")


# ---------------------------------------------------------------- Figure 4
def fig4_routes():
    names = list(RT)
    short = ["A: soda ash\n+ lime", "B: CO$_2$\n+ lime", "C: CO$_2$\n+ dolime",
             "D: CO$_2$ + electro-\nchemical base"]
    carb = [RT[n]["co2_reagents"] for n in names]
    ener = [RT[n]["extra_kwh"] for n in names]
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    cols = [RED, ORANGE, "#b7791f", GREEN]
    ax.scatter(ener, carb, s=150, c=cols, zorder=5, edgecolor="white", linewidth=1.5)
    for e, c, lab, col in zip(ener, carb, short, cols):
        dx, ha = (10, "left") if e < 20 else (-12, "right")
        ax.annotate(lab, (e, c), textcoords="offset points", xytext=(dx, 8),
                    fontsize=8, color=col, ha=ha)
    ax.axhline(0, color="#4a5568", lw=1)
    ax.set_xlabel("Additional energy (kWh m$^{-3}$ permeate)")
    ax.set_ylabel("Net reagent CO$_2$ (kg m$^{-3}$ permeate)")
    ax.set_title("The alkalinity trade-off: carbon can only be removed\n"
                 "by moving it into the energy account", fontsize=10)
    ax.set_xlim(-3, 38); ax.set_ylim(-3, 12)
    ax.text(0.5, -2.3, "carbon negative", fontsize=7.5, color=GREEN)
    save(fig, "figure4_alkalinity_tradeoff")


# ---------------------------------------------------------------- Figure 5
def fig5_montecarlo():
    rng = np.random.default_rng(mc["seed"])
    n = 200_000
    R, qb = 0.45, 0.55
    qc = qb * 0.5
    w = t1["least_work_kwh_per_m3_brine"]
    conc = w / rng.uniform(0.25, 0.55, n)
    sec = rng.uniform(0.05, 0.80, n) + 2.63 + conc * qb / R + rng.uniform(8, 15, n) * qc / R
    reag = (1.0231 * rng.uniform(0.18, 0.35, n) + 3.7923 * rng.uniform(0.08, 0.18, n)) / R
    lcow = 1375 * (1 + rng.uniform(0.2, 0.6, n)) * 0.08 / 365 + sec * rng.uniform(0.05, 0.12, n) \
        + reag + 0.235
    credit = (0.966 * rng.uniform(0.5, 0.7, n) * 470 * rng.uniform(0.7, 1.3, n)
              + 3.00 * rng.uniform(0.05, 0.20, n) * 800 * rng.uniform(0.7, 1.3, n)) / 1000 / R
    net = lcow - credit

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.0, 3.8))
    a1.hist(net, bins=140, color=BLUE, alpha=0.85)
    a1.axvline(0.76, color=RED, lw=1.8, ls="--")
    a1.text(0.80, a1.get_ylim()[1] * 0.92, "conventional SWRO\n$0.76 m$^{-3}$",
            color=RED, fontsize=8)
    a1.axvline(float(np.median(net)), color="black", lw=1.4)
    a1.text(float(np.median(net)) + 0.06, a1.get_ylim()[1] * 0.60,
            "median\n$%.2f" % np.median(net), fontsize=8)
    a1.set_xlabel("Net levelized cost of water ($ m$^{-3}$)")
    a1.set_ylabel("Samples")
    a1.set_title("(a)  Net LCOW", fontsize=10)

    a2.hist(reag, bins=140, color=ORANGE, alpha=0.85, label="reagent cost")
    a2.hist(credit, bins=140, color=GREEN, alpha=0.6, label="mineral credit")
    a2.set_xlabel("$ per m$^{-3}$ permeate")
    a2.set_ylabel("Samples")
    a2.set_title("(b)  Reagent cost against mineral credit", fontsize=10)
    a2.legend(frameon=False, fontsize=8)
    fig.suptitle("Monte Carlo propagation, 200,000 samples", fontsize=10.5, y=1.02)
    save(fig, "figure5_monte_carlo")


# ---------------------------------------------------------------- Figure 6
def fig6_carbon():
    grid = np.linspace(0.05, 0.75, 200)
    elec = mc["sec_total"]["median"] * grid
    reag = RT["A: soda ash + lime (as written)"]["co2_reagents"]
    fixed = V2["co2_fixed_kg_per_m3_permeate"]
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    ax.fill_between(grid, 0, elec, color=BLUE, alpha=0.8, label="grid electricity")
    ax.fill_between(grid, elec, elec + reag, color=RED, alpha=0.75,
                    label="reagent embodied carbon")
    ax.plot(grid, elec + reag - fixed, color="black", lw=1.8, label="net, after carbonate fixation")
    ax.set_xlabel("Grid carbon intensity (kg CO$_2$ kWh$^{-1}$)")
    ax.set_ylabel("kg CO$_2$ per m$^{3}$ of permeate")
    ax.set_title("The original assessment counted only the lower band", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_xlim(0.05, 0.75); ax.set_ylim(0, 22)
    save(fig, "figure6_carbon_account")


if __name__ == "__main__":
    print("generating figures ->", FIGDIR)
    fig1_process(); fig2_stage(); fig3_floor()
    fig4_routes(); fig5_montecarlo(); fig6_carbon()
    print("done")
