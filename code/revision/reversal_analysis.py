# -*- coding: utf-8 -*-
"""Can the conclusion be reversed, and if so on what?

The revision's negative result is driven by one term: the soda ash and lime that
supply alkalinity cost more than the minerals they produce are worth. That is a
statement about a particular way of supplying base, not about the architecture as
such. Route D supplies the same alkalinity electrochemically instead, which
trades the reagent bill for electricity.

Electricity has a price that varies by more than an order of magnitude across
sites, and the Gulf sites this architecture targets have among the cheapest solar
in the world. So the question is quantitative, not rhetorical: at what electricity
price does the electrochemical route beat the reagent route, and does either beat
the conventional comparator?

Two things this analysis does NOT do, and the answer is conditional on both:

  * It does not add capital cost for the on-site electrochemical plant. A unit
    producing ~11 kg NaOH per cubic metre of permeate is a real plant with real
    CAPEX, and the model has no basis for costing it. Everything below is
    therefore an upper bound on route D's performance.
  * It does not revisit the concentrator correction. That stands regardless of
    how alkalinity is supplied.

    python reversal_analysis.py
"""
import json

import numpy as np

import iledbv_revision_v2 as M

COMPARATOR = 0.76
FIXED_OPEX = 0.235
CAPEX_BASE = 1375.0
UPLIFT = 0.40                 # median of the sampled range
CRF = 0.08 / 365.0
KG_SODA, KG_LIME = 1.0231, 3.7923      # per m3 FEED, from design_and_costing.py

routes, co2_fixed, n_ca, n_mg = M.precipitation_routes()
A = routes["A: soda ash + lime (as written)"]
D = routes["D: dosed CO2 + electrochemical base"]
C = routes["C: dosed CO2 + dolime"]

# medians of the manuscript's sampled ranges
P_SODA, P_LIME = 0.265, 0.13          # $/kg
P_CO2 = 0.04                          # $/kg, captured CO2 delivered on site
SEC_BASE = 13.11                      # kWh/m3 permeate, corrected total
CREDIT = 1.252                        # $/m3, realisable mineral credit
capex = CAPEX_BASE * (1 + UPLIFT) * CRF

reagent_A = (KG_SODA * P_SODA + KG_LIME * P_LIME) / M.R
reagent_D = P_CO2 * D["reagents"]["CO2 (captured)"]      # NaOH is made, not bought
sec_D = SEC_BASE + D["extra_kwh"]

res = {"comparator": COMPARATOR, "capex": round(capex, 3),
       "fixed_opex": FIXED_OPEX, "credit": CREDIT,
       "sec_base": SEC_BASE, "sec_route_D": round(sec_D, 2),
       "reagent_A": round(reagent_A, 3), "reagent_D": round(reagent_D, 3),
       "extra_kwh_D": D["extra_kwh"]}

print("=" * 74)
print("SETUP (per m3 permeate, medians of the manuscript's ranges)")
print("=" * 74)
print("  capex %.2f   fixed %.3f   mineral credit %.2f" % (capex, FIXED_OPEX, CREDIT))
print("  route A: SEC %.2f kWh, reagents $%.2f" % (SEC_BASE, reagent_A))
print("  route D: SEC %.2f kWh (+%.2f electrochemical), reagents $%.2f"
      % (sec_D, D["extra_kwh"], reagent_D))


def lcow(elec, route):
    if route == "A":
        return capex + SEC_BASE * elec + reagent_A + FIXED_OPEX - CREDIT
    return capex + sec_D * elec + reagent_D + FIXED_OPEX - CREDIT


# ------------------------------------------------- 1. where do the routes cross?
# A and D are equal when the extra electricity costs what the reagents cost
cross = (reagent_A - reagent_D) / D["extra_kwh"]
res["route_crossover_usd_per_kwh"] = round(float(cross), 5)
print("\n" + "=" * 74)
print("1. WHERE THE ELECTROCHEMICAL ROUTE OVERTAKES THE REAGENT ROUTE")
print("=" * 74)
print("  crossover electricity price: $%.4f /kWh" % cross)
print("  below this, supplying alkalinity electrochemically is cheaper")

# ---------------------------------------- 2. where does each beat the comparator
def breakeven(route):
    lo, hi = 0.0, 1.0
    if lcow(lo, route) > COMPARATOR:
        return None                      # never beats it, even with free power
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if lcow(mid, route) < COMPARATOR:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


res["breakeven_A"] = breakeven("A")
res["breakeven_D"] = breakeven("D")
print("\n" + "=" * 74)
print("2. ELECTRICITY PRICE AT WHICH EACH ROUTE REACHES $%.2f/m3" % COMPARATOR)
print("=" * 74)
for k, label in (("A", "reagent route (as published)"),
                 ("D", "electrochemical route")):
    b = res["breakeven_" + k]
    print("  %-30s %s" % (label,
          ("$%.4f /kWh" % b) if b else "never, even at zero electricity cost"))

# ------------------------------------------------- 3. at real electricity prices
PRICES = [("Gulf utility-scale solar PPA, low", 0.0104),
          ("Gulf utility-scale solar PPA, typical", 0.0150),
          ("Saudi industrial tariff, indicative", 0.0480),
          ("Model base case", 0.0800),
          ("High-cost grid", 0.1200)]
print("\n" + "=" * 74)
print("3. NET LCOW AT REAL ELECTRICITY PRICES ($/m3)")
print("=" * 74)
print("  %-40s %8s %10s %10s" % ("scenario", "$/kWh", "route A", "route D"))
rows = []
for label, p in PRICES:
    a, d = lcow(p, "A"), lcow(p, "D")
    rows.append({"scenario": label, "usd_per_kwh": p,
                 "lcow_A": round(a, 3), "lcow_D": round(d, 3),
                 "D_beats_comparator": bool(d < COMPARATOR)})
    flag = "  <-- beats $%.2f" % COMPARATOR if d < COMPARATOR else ""
    print("  %-40s %8.4f %10.2f %10.2f%s" % (label, p, a, d, flag))
res["scenarios"] = rows

# --------------------------------------- 4. what else route D fixes, and doesn't
print("\n" + "=" * 74)
print("4. WHAT ROUTE D CHANGES BESIDES COST")
print("=" * 74)
print("  calcium closure ratio : %.2f (route A) -> %.2f (route D); 0 means the "
      "balance closes" % (A["ca_closure_ratio"], D["ca_closure_ratio"]))
print("  reagent carbon        : %+.2f -> %+.2f kg CO2/m3 (negative = net capture)"
      % (A["co2_reagents"], D["co2_reagents"]))
print("  magnesium imported    : %.1f -> %.1f kg/m3"
      % (A["mg_imported_kg"], D["mg_imported_kg"]))
res["route_D_effects"] = {
    "ca_closure_A": A["ca_closure_ratio"], "ca_closure_D": D["ca_closure_ratio"],
    "co2_reagents_A": A["co2_reagents"], "co2_reagents_D": D["co2_reagents"]}

# carbon at the cheap-power scenarios: grid intensity matters as much as price
GRID = [("solar-dominated, 0.05 kg CO2/kWh", 0.05),
        ("Saudi grid mix, 0.55 kg CO2/kWh", 0.55)]
print("\n  net CO2 (kg/m3), reagent carbon plus electricity carbon:")
carbon = []
for glabel, g in GRID:
    ca = SEC_BASE * g + A["co2_reagents"] - co2_fixed
    cd = sec_D * g + D["co2_reagents"] - co2_fixed
    carbon.append({"grid": glabel, "kg_per_kwh": g,
                   "co2_A": round(ca, 2), "co2_D": round(cd, 2),
                   "D_negative": bool(cd < 0)})
    print("    %-36s A %+7.2f   D %+7.2f%s"
          % (glabel, ca, cd, "   <-- net negative" if cd < 0 else ""))
res["carbon"] = carbon

json.dump(res, open("reversal_results.json", "w"), indent=1)
print("\nwrote reversal_results.json")
