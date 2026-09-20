# -*- coding: utf-8 -*-
"""Attribute the reversal, rank the uncertainty, and map where the architecture
would work.

Three analyses, none of which introduces a new modelling assumption -- all run
off the Monte Carlo already specified in iledbv_revision_v2.py.

  1  ABLATION. The revision reverses the original's conclusion, but does not say
     which correction did it. Turning each on in sequence answers that, and the
     answer is not the one the manuscript's emphasis implies.

  2  VARIANCE ATTRIBUTION. Spearman rank correlation of each sampled input
     against net LCOW, plus the swing each input commands across its own range.
     Reporting a sensitivity coefficient without the matching uncertainty can
     inverct the conclusion, so both are reported.

  3  ADMISSIBILITY MAP. Instead of one headline cost, a domain over reagent cost
     and mineral value showing where net LCOW falls below the conventional
     comparator -- converting a negative result into a design target.

    python attribution_analysis.py
"""
import json

import numpy as np
from scipy.stats import spearmanr

import iledbv_revision_v2 as M

N = 300_000
SEED = 20260919
COMPARATOR = 0.76
KG_SODA, KG_LIME = 1.0231, 3.7923
FIXED_OPEX = 0.235
CAPEX_BASE = 1375.0

LABEL = {
 "elec": "electricity price", "p_lime": "hydrated lime price",
 "f_mg": "sellable fraction, Mg(OH)2", "p_mg": "Mg(OH)2 price",
 "p_soda": "soda ash price", "cryst": "crystallizer energy",
 "p_ca": "carbonate price", "f_ca": "sellable fraction, carbonate",
 "eff2": "concentrator second-law efficiency", "uplift": "CAPEX uplift",
 "intake": "intake energy", "grid": "grid carbon intensity",
 "emb_soda": "soda ash embodied carbon", "emb_cao": "lime embodied carbon",
}


def draw(n=N, seed=SEED):
    """Reproduce the manuscript's Monte Carlo, retaining every sampled input."""
    rng = np.random.default_rng(seed)
    w_min = float(M.least_work(M.PI_BRINE, M.CONC_RECOVERY))
    v = {}
    v["eff2"] = rng.uniform(0.25, 0.55, n)
    conc_sec = w_min / v["eff2"]
    v["cryst"] = rng.uniform(8.0, 15.0, n)
    v["intake"] = rng.uniform(0.05, 0.80, n)
    v["elec"] = rng.uniform(0.05, 0.12, n)
    v["uplift"] = rng.uniform(0.20, 0.60, n)
    v["f_ca"] = rng.uniform(0.50, 0.70, n)
    v["f_mg"] = rng.uniform(0.05, 0.20, n)
    v["p_ca"] = M.PRICE_CA * rng.uniform(0.7, 1.3, n)
    v["p_mg"] = M.PRICE_MG * rng.uniform(0.7, 1.3, n)
    rng.uniform(0.25, 0.45, n)                      # opex_frac: drawn, unused
    v["emb_cao"] = rng.uniform(0.9, 1.5, n)
    v["emb_soda"] = rng.uniform(0.8, 1.3, n)
    v["grid"] = rng.uniform(0.15, 0.65, n)
    v["p_soda"] = rng.uniform(0.18, 0.35, n)
    v["p_lime"] = rng.uniform(0.08, 0.18, n)

    qp, qb = M.R, 1.0 - M.R
    q_conc = qb * (1.0 - M.CONC_RECOVERY)
    sec = v["intake"] + (M.SEC_DESAL - 0.10) + conc_sec * qb / qp + v["cryst"] * q_conc / qp
    reagents = (KG_SODA * v["p_soda"] + KG_LIME * v["p_lime"]) / M.R
    capex = CAPEX_BASE * (1 + v["uplift"]) * 0.08 / 365.0
    credit = (M.KG_CACO3_FEED * v["f_ca"] * v["p_ca"]
              + M.KG_MGOH2_FEED * v["f_mg"] * v["p_mg"]) / 1000.0 / qp
    lcow = capex + sec * v["elec"] + reagents + FIXED_OPEX - credit
    return v, dict(sec=sec, reagents=reagents, credit=credit, capex=capex, lcow=lcow,
                   w_min=w_min)


def main():
    res = {"n": N, "seed": SEED, "comparator": COMPARATOR}
    v, out = draw()
    lcow = out["lcow"]
    med = {k: float(np.median(x)) for k, x in v.items()}

    # ===================================================== 1. ABLATION
    qp, qb = M.R, 1.0 - M.R
    q_conc = qb * (1.0 - M.CONC_RECOVERY)
    capex_med = CAPEX_BASE * (1 + med["uplift"]) * 0.08 / 365.0
    reagent_med = (KG_SODA * med["p_soda"] + KG_LIME * med["p_lime"]) / M.R
    credit_med = (M.KG_CACO3_FEED * med["f_ca"] * med["p_ca"]
                  + M.KG_MGOH2_FEED * med["f_mg"] * med["p_mg"]) / 1000.0 / qp


    def step(conc_sec_val, opex_mode):
        sec = med["intake"] + (M.SEC_DESAL - 0.10) + conc_sec_val * qb / qp \
            + med["cryst"] * q_conc / qp
        energy = sec * med["elec"]
        # the original modelled non-energy OPEX as a share of energy cost, which is
        # what concealed the reagent term
        opex = 0.35 * energy if opex_mode == "fraction" else reagent_med + FIXED_OPEX
        return capex_med + energy + opex - credit_med, sec


    ORIGINAL_CONC = 0.75                       # midpoint of the original 0.5-1.0 range
    corrected_conc = out["w_min"] / med["eff2"]
    ablation = []
    prev = None
    for name, cs, mode in [
        ("original assumptions", ORIGINAL_CONC, "fraction"),
        ("concentrator corrected to the thermodynamic bound", corrected_conc, "fraction"),
        ("reagents costed explicitly", corrected_conc, "explicit"),
    ]:
        val, sec = step(cs, mode)
        ablation.append({"step": name, "lcow": round(val, 3), "sec": round(sec, 2),
                         "delta": None if prev is None else round(val - prev, 3)})
        prev = val
    res["ablation"] = ablation
    res["ablation_note"] = {
        "thermodynamic_delta": ablation[1]["delta"],
        "reagent_delta": ablation[2]["delta"],
        "ratio": round(ablation[2]["delta"] / ablation[1]["delta"], 1),
        "beats_comparator_after_thermodynamic_correction": bool(ablation[1]["lcow"] < COMPARATOR),
    }

    print("=" * 72)
    print("ABLATION (median parameters)")
    print("=" * 72)
    for a in ablation:
        d = "" if a["delta"] is None else "  (%+.2f)" % a["delta"]
        print("  %-52s $%.2f%s" % (a["step"], a["lcow"], d))
    print("  %-52s $%.2f" % ("conventional comparator", COMPARATOR))
    print("\n  reagent correction is %.1fx the thermodynamic one"
          % res["ablation_note"]["ratio"])
    print("  after the thermodynamic correction alone, the architecture still %s"
          % ("beats the comparator"
             if res["ablation_note"]["beats_comparator_after_thermodynamic_correction"]
             else "loses"))

    # ===================================================== 2. VARIANCE ATTRIBUTION
    rows = []
    for k, x in v.items():
        rho = float(spearmanr(x, lcow).statistic)
        lo = float(lcow[x <= np.percentile(x, 10)].mean())
        hi = float(lcow[x >= np.percentile(x, 90)].mean())
        rows.append({"parameter": LABEL[k], "key": k, "spearman": round(rho, 3),
                     "swing": round(abs(hi - lo), 3)})
    rows.sort(key=lambda r: -abs(r["spearman"]))
    res["attribution"] = rows
    tot = sum(r["swing"] for r in rows)
    res["attribution_note"] = {
        "top3_share": round(sum(r["swing"] for r in rows[:3]) / tot, 3),
        "eff2_rank": 1 + next(i for i, r in enumerate(rows) if r["key"] == "eff2"),
        "eff2_spearman": next(r["spearman"] for r in rows if r["key"] == "eff2"),
    }
    print("\n" + "=" * 72)
    print("VARIANCE ATTRIBUTION FOR NET LCOW")
    print("=" * 72)
    print("  %-36s %9s %10s" % ("parameter", "Spearman", "swing"))
    for r in rows:
        print("  %-36s %9.3f %10.3f" % (r["parameter"], r["spearman"], r["swing"]))
    print("\n  concentrator second-law efficiency ranks %d of %d (rho = %.3f)"
          % (res["attribution_note"]["eff2_rank"], len(rows),
             res["attribution_note"]["eff2_spearman"]))

    # ===================================================== 3. ADMISSIBILITY MAP
    sec_med = float(np.median(out["sec"]))
    energy_med = sec_med * med["elec"]
    rf = np.linspace(0.0, 1.5, 121)          # reagent cost multiplier
    cf = np.linspace(0.5, 4.0, 121)          # mineral value multiplier
    RF, CF = np.meshgrid(rf, cf, indexing="ij")
    det = capex_med + energy_med + reagent_med * RF + FIXED_OPEX - credit_med * CF

    # probabilistic version: rescale the sampled reagent and credit terms
    sub = slice(0, 40_000)                   # subsample keeps the grid tractable
    prob = np.empty_like(det)
    base = (out["capex"][sub] + out["sec"][sub] * v["elec"][sub] + FIXED_OPEX)
    for i, a in enumerate(rf):
        for j, b in enumerate(cf):
            prob[i, j] = float((base + out["reagents"][sub] * a
                                - out["credit"][sub] * b < COMPARATOR).mean())

    res["admissibility"] = {
        "reagent_multiplier": rf.tolist(), "credit_multiplier": cf.tolist(),
        "median_lcow_grid": det.round(4).tolist(),
        "prob_beats_comparator": prob.round(4).tolist(),
        "baseline": {"capex": round(capex_med, 3), "energy": round(energy_med, 3),
                     "reagents": round(reagent_med, 3), "credit": round(credit_med, 3),
                     "fixed": FIXED_OPEX},
    }


    def needed(mult_index):
        col = det[mult_index, :]
        j = np.where(col < COMPARATOR)[0]
        return float(cf[j[0]]) if j.size else None


    i_full = int(np.argmin(np.abs(rf - 1.0)))
    res["admissibility"]["credit_needed_at_full_reagent_cost"] = needed(i_full)
    res["admissibility"]["credit_needed_at_zero_reagent_cost"] = needed(0)
    # probabilistic: highest P at the current operating point
    i0, j0 = int(np.argmin(np.abs(rf - 1.0))), int(np.argmin(np.abs(cf - 1.0)))
    res["admissibility"]["p_beats_at_current_point"] = float(prob[i0, j0])
    n_beat = int((lcow < COMPARATOR).sum())
    res["n_beating_comparator"] = n_beat
    res["frac_beating_comparator"] = round(n_beat / lcow.size, 6)
    res["min_lcow"] = round(float(lcow.min()), 3)

    print("\n" + "=" * 72)
    print("ADMISSIBILITY")
    print("=" * 72)
    print("  at medians: capex $%.2f  energy $%.2f  reagents $%.2f  credit $%.2f  fixed $%.3f"
          % (capex_med, energy_med, reagent_med, credit_med, FIXED_OPEX))
    print("  P(net LCOW < $%.2f) at the modelled operating point : %.4f"
          % (COMPARATOR, res["admissibility"]["p_beats_at_current_point"]))
    print("  minerals must be worth %.1fx the modelled value at today's reagent prices"
          % res["admissibility"]["credit_needed_at_full_reagent_cost"])
    print("  with reagents free, %.1fx still required"
          % res["admissibility"]["credit_needed_at_zero_reagent_cost"])

    json.dump(res, open("attribution_results.json", "w"), indent=1)
    print("\nwrote attribution_results.json")


if __name__ == "__main__":
    main()
