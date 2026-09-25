# -*- coding: utf-8 -*-
"""Alkalinity supply and calcium closure treated as one design problem.

Section 4.7 showed that the lime step returns 5.3 times more calcium than the
carbonate step removes, and Sections 4.10-4.12 showed that the purchased
alkalinity is what makes the architecture uncompetitive. Those were evaluated
one route at a time. This script asks the coupled question instead: which mix
of alkalinity sources, carbonate sources and calcium sinks minimises net cost
while closing the calcium balance, and what would an electrochemical base
source have to achieve for the valorization loop to close?

Everything is per cubic metre of permeate, on the same basis as
iledbv_revision_v2.py and reversal_analysis.py, and every central value that
also appears there is taken from there.

Decision variables (kmol per m3 permeate)
    xL  OH- supplied as Ca(OH)2          (imports 1/2 Ca per OH)
    xN  OH- supplied as purchased NaOH   (no Ca; embodied carbon)
    xE  OH- generated on site            (no Ca; electricity)
    s   carbonate supplied as Na2CO3
    d   carbonate supplied as dosed CO2  (needs 2 OH- per mole)
    g   Ca removed as gypsum, CaSO4.2H2O (limited by the sulfate present)

    min  C_alk + C_energy + C_disposal - C_products
    s.t. xL + xN + xE - 2d >= 2 n_Mg            (Eq. 12 alkalinity demand)
         s + d = n_Ca                          (carbonate for the Ca step)
         xL/2 - n_Ca - g <= dCa_max            (calcium closure)
         g <= f_gyp * n_SO4,  g <= Ca in stream
         SEC <= SEC_target,  CO2 <= CO2_target (optional)

C_disposal is left at zero and the calcium balance is imposed as a
constraint instead, so that its shadow price reports what closure costs.

    python alkalinity_calcium_design.py
"""
import io
import json
import os

import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
RV = json.load(io.open(os.path.join(HERE, "reversal_results.json"), encoding="utf-8"))

# ------------------------------------------------------------ plant basis
R = 0.45
Q_CONC = (1 - R) * 0.5 / R            # m3 crystallizer feed per m3 permeate
MW = dict(CO2=44.009, CaCO3=100.09, Na2CO3=105.99, MgOH2=58.32, CaOH2=74.09,
          CaO=56.08, NaOH=39.997, Ca=40.08, SO4=96.06, CaSO4_2H2O=172.17)

N_CA = 0.966 / R / MW["CaCO3"]        # kmol Ca removed as CaCO3
N_MG = 3.00 / R / MW["MgOH2"]         # kmol Mg(OH)2 recovered
C_F_CA = 0.4121                       # g/L feed, reference composition
C_F_SO4 = 2.7124 * 1.02476            # g/kg -> g/L at S = 35 (Millero et al. 2008)
N_CA_FEED = C_F_CA / MW["Ca"] / R     # kmol Ca entering per m3 permeate
N_SO4 = C_F_SO4 / MW["SO4"] / R       # kmol sulfate entering (RO rejects it)

# ------------------------------------------------ economics (central values)
CAPEX, FIXED, CREDIT = RV["capex"], RV["fixed_opex"], RV["credit"]
SEC_BASE, COMPARATOR = RV["sec_base"], RV["comparator"]
P = dict(soda=0.265, lime=0.13, naoh=0.45, co2=0.04)      # $/kg, mid of swept ranges
EMB = dict(soda=1.00, cao=1.20, naoh=1.90, co2=-1.0)       # kg CO2 per kg reagent
KWH_KG_CHLOR = 2.5                     # kWh per kg NaOH, as in Section 4.12

# per kmol OH- (or per kmol carbonate)
LIME_KG = MW["CaOH2"] / 2.0
NAOH_KG = MW["NaOH"]


def unit(p_e, grid, eps):
    """Cost ($), carbon (kg), energy (kWh) per kmol of each supply."""
    kwh_E = eps * NAOH_KG
    return {
        "xL": (LIME_KG * P["lime"], MW["CaO"] / 2.0 * EMB["cao"], 0.0),
        "xN": (NAOH_KG * P["naoh"], NAOH_KG * EMB["naoh"], 0.0),
        "xE": (kwh_E * p_e, kwh_E * grid, kwh_E),
        "s": (MW["Na2CO3"] * P["soda"], MW["Na2CO3"] * EMB["soda"], 0.0),
        "d": (MW["CO2"] * P["co2"], MW["CO2"] * EMB["co2"], 0.0),
        "g": (0.0, 0.0, 0.0),
    }


VARS = ["xL", "xN", "xE", "s", "d", "g"]
F_GYP = 0.70                          # fraction of sulfate recoverable as gypsum


def solve(p_e, grid, eps, dca_max=0.0, f_gyp=F_GYP, sec_max=None, co2_max=None,
          allow=None, objective="cost"):
    u = unit(p_e, grid, eps)
    idx = {v: i for i, v in enumerate(VARS)}
    c = np.array([u[v][1 if objective == "co2" else 0] for v in VARS])
    A, b = [], []
    row = np.zeros(6); row[[idx["xL"], idx["xN"], idx["xE"]]] = -1; row[idx["d"]] = 2
    A.append(row); b.append(-2 * N_MG)                              # alkalinity
    row = np.zeros(6); row[idx["xL"]] = 0.5; row[idx["g"]] = -1
    A.append(row); b.append(dca_max + N_CA)                           # calcium
    row = np.zeros(6); row[idx["g"]] = 1
    A.append(row); b.append(f_gyp * N_SO4)                            # sulfate limit
    row = np.zeros(6); row[idx["g"]] = 1; row[idx["xL"]] = -0.5
    A.append(row); b.append(N_CA_FEED - N_CA)                         # Ca present
    if sec_max is not None:
        row = np.zeros(6); row[idx["xE"]] = u["xE"][2]
        A.append(row); b.append(sec_max - SEC_BASE)
    if co2_max is not None:
        row = np.array([u[v][1] for v in VARS])
        A.append(row); b.append(co2_max - SEC_BASE * grid)
    Aeq = np.zeros((1, 6)); Aeq[0, idx["s"]] = 1; Aeq[0, idx["d"]] = 1
    bounds = [(0, None)] * 6
    if allow is not None:
        bounds = [(0, None) if v in allow else (0, 0) for v in VARS]
    r = linprog(c, A_ub=np.array(A), b_ub=np.array(b), A_eq=Aeq, b_eq=[N_CA],
                bounds=bounds, method="highs")
    if not r.success:
        return None
    x = dict(zip(VARS, r.x))
    return summarise(x, p_e, grid, eps, r.ineqlin.marginals[1])


def summarise(x, p_e, grid, eps, ca_shadow=0.0):
    u = unit(p_e, grid, eps)
    reag = sum(x[v] * u[v][0] for v in ("xL", "xN", "s", "d"))
    kwh = x["xE"] * u["xE"][2]
    sec = SEC_BASE + kwh
    co2 = sec * grid + sum(x[v] * u[v][1] for v in ("xL", "xN", "s", "d"))
    # CO2 fixed in the carbonate product is credited once, and only for the
    # soda-ash share: the dosed-CO2 credit above already is that carbon.
    co2 -= x["s"] * MW["CO2"]
    lcow = CAPEX + FIXED + sec * p_e + reag - CREDIT
    oh = x["xL"] + x["xN"] + x["xE"]
    dca = x["xL"] / 2 - N_CA - x["g"]
    removed = N_CA + x["g"]
    return {
        "mix_OH_fraction": {"lime": round(x["xL"] / oh, 3), "NaOH_purchased": round(x["xN"] / oh, 3),
                            "on_site": round(x["xE"] / oh, 3)},
        "carbonate": "dosed CO2" if x["d"] > x["s"] else "soda ash",
        "gypsum_kmol": round(x["g"], 4),
        "gypsum_kg": round(x["g"] * MW["CaSO4_2H2O"], 3),
        "reagent_usd": round(reag, 3), "extra_kwh": round(kwh, 2), "sec": round(sec, 2),
        "co2_kg": round(co2, 2), "lcow_net": round(lcow, 3),
        "dCa_kmol": round(dca, 4),
        "dCa_g_per_L_conc": round(dca * MW["Ca"] / Q_CONC, 3),
        "ca_import_over_removal": round((x["xL"] / 2) / removed, 2),
        "ca_shadow_usd_per_kmol": round(-float(ca_shadow), 2),
        "mol_OH_per_kWh_on_site": round(1000.0 / (eps * NAOH_KG), 2) if x["xE"] > 1e-9 else None,
    }


def pure(label, xL=0.0, xN=0.0, xE=0.0, carb="s", g=0.0, p_e=0.08, grid=0.55, eps=KWH_KG_CHLOR):
    s_, d_ = (N_CA, 0.0) if carb == "s" else (0.0, N_CA)
    x = dict(xL=xL, xN=xN, xE=xE, s=s_, d=d_, g=g)
    return label, x


def main():
    oh_req = 2 * N_MG
    g_max = F_GYP * N_SO4
    res = {"basis": {
        "n_Ca_removed_kmol": round(N_CA, 5), "n_Mg_kmol": round(N_MG, 5),
        "OH_required_kmol": round(oh_req, 5), "n_SO4_kmol": round(N_SO4, 5),
        "gypsum_max_kmol": round(g_max, 5), "f_gyp": F_GYP,
        "Ca_feed_kmol": round(N_CA_FEED, 5), "q_conc_m3": round(Q_CONC, 4),
        "prices_usd_per_kg": P, "embodied_kgCO2_per_kg": EMB,
        "kwh_per_kg_naoh_chloralkali": KWH_KG_CHLOR}}

    # ---- 1. unit economics of one kmol of OH-
    unitrows = []
    for p_e in (0.015, 0.08):
        u = unit(p_e, 0.55, KWH_KG_CHLOR)
        unitrows.append({"p_e": p_e, "lime_usd": round(u["xL"][0], 2),
                         "naoh_usd": round(u["xN"][0], 2), "onsite_usd": round(u["xE"][0], 2)})
    res["usd_per_kmol_OH"] = unitrows
    lime_usd = unit(0.08, 0.55, 1)["xL"][0]
    res["breakeven_onsite_vs_lime"] = {
        "%.3f" % pe: {"kwh_per_kmol": round(lime_usd / pe, 1),
                      "mol_OH_per_kWh": round(1000 * pe / lime_usd, 2),
                      "kwh_per_kg_NaOH": round(lime_usd / pe / NAOH_KG, 3)}
        for pe in (0.015, 0.03, 0.05, 0.08, 0.12)}

    # ---- 2. candidate architectures, each evaluated at two electricity cases
    arch = [
        pure("P1 Na2CO3 + Ca(OH)2 (as written)", xL=oh_req),
        pure("P2 Na2CO3 + purchased NaOH", xN=oh_req),
        pure("P3 Na2CO3 + on-site NaOH", xE=oh_req),
        pure("P4 dosed CO2 + on-site NaOH (route D)", xE=oh_req + 2 * N_CA, carb="d"),
        pure("P5 P1 followed by gypsum removal", xL=oh_req, g=g_max),
    ]
    # P6: cheapest calcium-closed purchased-reagent mix, lime share capped by closure
    xL6 = 2 * (N_CA + g_max)
    arch.append(pure("P6 lime/NaOH blend + gypsum, dCa = 0", xL=xL6, xN=oh_req - xL6, g=g_max))
    cases = [("Gulf solar PPA", 0.015, 0.05), ("model base case", 0.08, 0.55)]
    table = []
    for label, x in arch:
        row = {"architecture": label}
        for cname, pe, grid in cases:
            row[cname] = summarise(x, pe, grid, KWH_KG_CHLOR)
        table.append(row)
    res["architectures"] = table

    # ---- 3. optimisation: closure cost and the architecture it selects
    opt = {}
    for cname, pe, grid in cases:
        free = solve(pe, grid, KWH_KG_CHLOR, dca_max=10.0)
        closed = solve(pe, grid, KWH_KG_CHLOR, dca_max=0.0)
        no_gyp = solve(pe, grid, KWH_KG_CHLOR, dca_max=0.0, f_gyp=0.0)
        low_c = solve(pe, grid, KWH_KG_CHLOR, dca_max=0.0, objective="co2")
        opt[cname] = {"unconstrained": free, "closed_dCa_le_0": closed,
                      "closed_without_gypsum": no_gyp, "min_co2_closed": low_c,
                      "closure_cost_usd_per_m3": round(closed["lcow_net"] - free["lcow_net"], 3),
                      "closure_cost_without_gypsum": round(no_gyp["lcow_net"] - free["lcow_net"], 3)}
    res["optimisation"] = opt

    # ---- 4. map: net LCOW of the calcium-closed optimum over price x intensity
    pes = np.round(np.linspace(0.005, 0.12, 47), 4)
    mols = np.round(np.linspace(4.0, 60.0, 57), 2)          # mol OH- per kWh
    epss = 1000.0 / (mols * NAOH_KG)                         # kWh per kg NaOH
    grid_map = np.zeros((len(epss), len(pes)))
    onsite_share = np.zeros_like(grid_map)
    for i, e in enumerate(epss):
        for j, pe in enumerate(pes):
            s_ = solve(pe, 0.05, e, dca_max=0.0)
            grid_map[i, j] = s_["lcow_net"]
            onsite_share[i, j] = s_["mix_OH_fraction"]["on_site"]
    res["map"] = {"p_e": pes.tolist(), "mol_OH_per_kWh": mols.tolist(),
                  "lcow_net": np.round(grid_map, 3).tolist(),
                  "onsite_share": np.round(onsite_share, 3).tolist()}

    # required on-site intensity for the closed loop to reach the comparator
    req = {}
    for pe in (0.01, 0.015, 0.03, 0.048, 0.08):
        best = None
        for e in np.linspace(0.05, 20.0, 3991):
            s_ = solve(pe, 0.05, e, dca_max=0.0)
            if s_["lcow_net"] <= COMPARATOR:
                best = e
        req["%.3f" % pe] = None if best is None else {
            "max_kwh_per_kg_NaOH": round(float(best), 3),
            "min_mol_OH_per_kWh": round(1000.0 / (best * NAOH_KG), 2)}
    res["required_intensity_to_reach_comparator"] = req

    # reversible limit for splitting water into H+ and OH- across a bipolar
    # junction: E = (RT/F) ln10 * dpH, 0.828 V for a 14-unit pH gradient
    e_rev = 8.314 * 298.15 / 96485.0 * np.log(10) * 14
    res["reversible_limit"] = {"E_V": round(float(e_rev), 3),
                               "max_mol_OH_per_kWh": round(3.6e6 / (96485.0 * e_rev), 1),
                               "min_kwh_per_kg_NaOH": round(96485.0 * e_rev / 3.6e6 * 1000 / NAOH_KG * 1.0, 3)}

    # highest electricity price at which the closed loop still reaches the
    # comparator, for a given on-site yield
    def ceiling(mol):
        e = 1000.0 / (mol * NAOH_KG)
        lo, hi = 0.001, 0.2
        for _ in range(60):
            mid = (lo + hi) / 2
            if solve(mid, 0.05, e, dca_max=0.0)["lcow_net"] <= COMPARATOR:
                lo = mid
            else:
                hi = mid
        return round(lo, 4)
    res["price_ceiling_usd_per_kwh"] = {
        "chlor_alkali_10_mol_per_kWh": ceiling(10.0),
        "20_mol_per_kWh": ceiling(20.0),
        "reversible_limit": ceiling(res["reversible_limit"]["max_mol_OH_per_kWh"])}

    # floor: the closed loop with free alkalinity energy and free reagents
    floor = CAPEX + FIXED - CREDIT
    res["floor_without_energy_or_reagents"] = round(floor, 3)
    res["floor_with_base_sec"] = {"%.3f" % pe: round(floor + SEC_BASE * pe, 3)
                                  for pe in (0.015, 0.048, 0.08)}

    # ---- 5. sensitivity of the closure cost at the base case
    sens = []
    for pn in (0.30, 0.45, 0.70):
        for fg in (0.5, 0.7, 0.9):
            P["naoh"] = pn
            a = solve(0.08, 0.55, KWH_KG_CHLOR, dca_max=10.0)
            b = solve(0.08, 0.55, KWH_KG_CHLOR, dca_max=0.0, f_gyp=fg)
            sens.append({"naoh_usd_per_kg": pn, "f_gyp": fg,
                         "closure_cost": round(b["lcow_net"] - a["lcow_net"], 3),
                         "closed_mix": b["mix_OH_fraction"]})
    P["naoh"] = 0.45
    res["closure_cost_sensitivity"] = sens

    with io.open(os.path.join(HERE, "alkalinity_calcium_results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)

    b = res["basis"]
    print("OH- required %.4f kmol; Ca removed %.4f; SO4 %.4f; gypsum cap %.4f kmol"
          % (b["OH_required_kmol"], b["n_Ca_removed_kmol"], b["n_SO4_kmol"], b["gypsum_max_kmol"]))
    print("$ per kmol OH-:", res["usd_per_kmol_OH"])
    print("on-site vs lime breakeven:", res["breakeven_onsite_vs_lime"])
    for r in table:
        print("\n", r["architecture"])
        for cname, _, _ in cases:
            v = r[cname]
            print("   %-16s LCOW %+.3f  reag %.3f  kWh %+.1f  CO2 %+.2f  dCa %+.4f (%.2f g/L)  ratio %.2f"
                  % (cname, v["lcow_net"], v["reagent_usd"], v["extra_kwh"], v["co2_kg"],
                     v["dCa_kmol"], v["dCa_g_per_L_conc"], v["ca_import_over_removal"]))
    for cname, v in opt.items():
        print("\n OPT", cname)
        for k in ("unconstrained", "closed_dCa_le_0", "closed_without_gypsum", "min_co2_closed"):
            print("   %-24s %s" % (k, {kk: v[k][kk] for kk in ("mix_OH_fraction", "carbonate", "lcow_net",
                                                               "co2_kg", "dCa_kmol", "ca_shadow_usd_per_kmol")}))
        print("   closure cost %.3f  (without gypsum %.3f)" % (v["closure_cost_usd_per_m3"],
                                                            v["closure_cost_without_gypsum"]))
    print("\nrequired intensity:", req)
    print("floor:", res["floor_without_energy_or_reagents"], res["floor_with_base_sec"])
    print("sensitivity:", [(s["naoh_usd_per_kg"], s["f_gyp"], s["closure_cost"]) for s in sens])


if __name__ == "__main__":
    main()
