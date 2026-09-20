# -*- coding: utf-8 -*-
"""Do the two proposed additions earn a place in the ILEDBV manuscript?

Each is treated the same way as the three consistency tests: compute the bound
it implies, and let it fail if it fails.

  Idea 1a  hydrocyclone / vortex pre-filtration
  Idea 1b  centrifugal RO - rotating the element to suppress concentration
           polarization
  Idea 2   CO2 dosing of the feed, and CO2 mineralization in the CaCO3 product

    python new_ideas_assessment.py
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BAR2KWH = 1e5 / 3.6e6

R = 0.45
PI_BRINE = 49.0            # bar, RO brine at 63.5 g/L
NDP = 15.0
ETA_PUMP, ETA_PX = 0.85, 0.96
SEC_DESAL = 2.73           # kWh/m3 permeate
SEC_TOTAL = 12.07          # kWh/m3 permeate, Monte Carlo median with the corrected concentrator

KG_CACO3_PER_M3_FEED = 0.966
KG_MGOH2_PER_M3_FEED = 3.00

M_CO2, M_CACO3 = 44.009, 100.09
M_NAOH, M_NA2CO3, M_CA = 39.997, 105.99, 40.08
M_MG, M_MGOH2 = 24.305, 58.32

GRID_KG_CO2_PER_KWH = 0.40      # global average-ish; swept below


# ------------------------------------------------------- idea 1b: centrifugal RO
def cp_factor_benefit(beta):
    """Upper bound on the SEC saving from eliminating concentration polarization.

    Concentration polarization raises the salt concentration at the membrane wall
    to beta times the bulk value, so the applied pressure must overcome
    beta * pi_bulk rather than pi_bulk. Removing polarization entirely - which is
    the most any boundary-layer management scheme can do - saves exactly the
    (beta - 1) * pi_bulk term. This is a hard ceiling, not an estimate.
    """
    pf_with = beta * PI_BRINE + NDP
    pf_without = PI_BRINE + NDP
    qf, qp, qb = 1.0, R, 1.0 - R

    def sec(pf):
        gross = (pf * qf / ETA_PUMP) * BAR2KWH / qp
        credit = (ETA_PX * pf * qb) * BAR2KWH / qp
        return gross - credit

    s_with, s_without = sec(pf_with), sec(pf_without)
    return {"beta": beta,
            "applied_pressure_bar": round(pf_with, 1),
            "sec_with_cp": round(s_with, 3),
            "sec_no_cp": round(s_without, 3),
            "max_saving_kwh_m3": round(s_with - s_without, 3),
            "max_saving_pct": round(100 * (s_with - s_without) / s_with, 1)}


# ------------------------------------------------------------ idea 2: CO2 balance
def co2_mineralization():
    """CO2 fixed in the CaCO3 product, against the CO2 owed for the alkalinity."""
    kg_caco3 = KG_CACO3_PER_M3_FEED / R          # per m3 PERMEATE
    kg_mgoh2 = KG_MGOH2_PER_M3_FEED / R

    co2_fixed = kg_caco3 * M_CO2 / M_CACO3       # carbon locked into the carbonate

    # Stoichiometry of the two precipitation routes actually available.
    #   soda-ash route : Ca2+ + Na2CO3 -> CaCO3 + 2Na+
    #   CO2/caustic    : Ca2+ + CO2 + 2NaOH -> CaCO3 + 2Na+ + H2O
    # Magnesium needs two equivalents of base either way:
    #   Mg2+ + 2NaOH -> Mg(OH)2 + 2Na+
    mol_caco3 = kg_caco3 / M_CACO3
    mol_mgoh2 = kg_mgoh2 / M_MGOH2

    kg_na2co3 = mol_caco3 * M_NA2CO3
    kg_naoh_for_ca = mol_caco3 * 2 * M_NAOH
    kg_naoh_for_mg = mol_mgoh2 * 2 * M_NAOH

    # Embodied CO2 of the reagents (cradle-to-gate, order of magnitude).
    # These need locking against a published LCA before submission; they are
    # swept below rather than relied on as point values.
    EMB = {"NaOH (chlor-alkali)": 1.9, "Na2CO3 (Solvay)": 1.0}

    routes = {}
    for label, (kg_reagent, emb_key, extra_naoh) in {
        "soda-ash route (as written)": (kg_na2co3, "Na2CO3 (Solvay)", kg_naoh_for_mg),
        "CO2 + caustic route": (kg_naoh_for_ca, "NaOH (chlor-alkali)", kg_naoh_for_mg),
    }.items():
        owed = kg_reagent * EMB[emb_key] + extra_naoh * EMB["NaOH (chlor-alkali)"]
        routes[label] = {
            "kg_reagent_per_m3_permeate": round(kg_reagent, 3),
            "kg_naoh_for_mg_per_m3_permeate": round(extra_naoh, 3),
            "co2_owed_for_reagents_kg_per_m3": round(owed, 3),
            "co2_fixed_in_caco3_kg_per_m3": round(co2_fixed, 3),
            "net_kg_co2_per_m3_permeate": round(owed - co2_fixed, 3),
        }
    return co2_fixed, kg_caco3, kg_mgoh2, routes, EMB


def main():
    res = {}
    print("=" * 76)
    print("IDEA 1a  Hydrocyclone / vortex pre-filtration")
    print("=" * 76)
    print("""  Not applicable to this architecture, and saying so strengthens it.
  The paper's premise is a SUBSURFACE beach-well intake: the seabed sand is
  already the filter, which is precisely why the paper claims reduced
  pretreatment (SDI typically <2, negligible suspended solids). A hydrocyclone
  removes grit that a subsurface intake never admits. Adding one would be
  redundant equipment defended by an argument that undercuts the intake choice.
  -> Use as one sentence justifying the intake, not as a process step.""")
    res["idea_1a"] = "not applicable - subsurface intake already performs this duty"

    print("\n" + "=" * 76)
    print("IDEA 1b  Centrifugal RO: the ceiling on boundary-layer management")
    print("=" * 76)
    print("  Concentration polarization raises wall concentration to beta x bulk.")
    print("  Eliminating it entirely saves exactly (beta-1)*pi_bulk - a hard ceiling.\n")
    print("  %-8s %12s %11s %11s %10s" % ("beta", "applied bar", "SEC now", "SEC ideal", "max saving"))
    cro = {}
    for beta in (1.05, 1.10, 1.15, 1.20):
        d = cp_factor_benefit(beta)
        cro["beta_%.2f" % beta] = d
        print("  %-8.2f %12.1f %11.3f %11.3f %7.3f (%.1f%%)"
              % (beta, d["applied_pressure_bar"], d["sec_with_cp"], d["sec_no_cp"],
                 d["max_saving_kwh_m3"], d["max_saving_pct"]))
    res["idea_1b_centrifugal_ro"] = cro
    best = cp_factor_benefit(1.20)["max_saving_kwh_m3"]
    print("""
  Reading: even at an aggressive beta = 1.20, perfect boundary-layer control
  saves at most %.2f kWh/m3. ANY rotating scheme must therefore consume less
  than %.2f kWh/m3 in shaft power, net of seals and bearings, or it loses.
  That is a falsifiable design criterion rather than a claim, and it is the
  form in which this idea is worth publishing.""" % (best, best))

    print("\n" + "=" * 76)
    print("IDEA 2  CO2 dosing and carbon mineralization in the CaCO3 product")
    print("=" * 76)
    co2_fixed, kg_ca, kg_mg, routes, EMB = co2_mineralization()
    res["idea_2_co2"] = {"routes": routes, "embodied_factors_kg_co2_per_kg": EMB}
    print("  Product per m3 of permeate : %.2f kg CaCO3, %.2f kg Mg(OH)2" % (kg_ca, kg_mg))
    print("  CO2 locked into the carbonate: %.3f kg per m3 permeate\n" % co2_fixed)
    print("  Against grid emissions at SEC = %.2f kWh/m3:" % SEC_TOTAL)
    for gi in (0.20, 0.40, 0.60):
        em = SEC_TOTAL * gi
        print("     grid %.2f kg/kWh -> %.2f kg CO2/m3 emitted; carbonate offsets %.0f%%"
              % (gi, em, 100 * co2_fixed / em))
    print("\n  BUT the alkalinity has to come from somewhere:")
    print("  %-30s %10s %10s %10s" % ("route", "reagent CO2", "fixed", "NET"))
    for label, d in routes.items():
        print("  %-30s %10.2f %10.2f %+10.2f"
              % (label, d["co2_owed_for_reagents_kg_per_m3"],
                 d["co2_fixed_in_caco3_kg_per_m3"], d["net_kg_co2_per_m3_permeate"]))
    print("""
  Reading: the carbonate genuinely fixes %.2f kg CO2 per m3 of permeate, but the
  soda ash and caustic needed to precipitate the two minerals carry an order of
  magnitude more embodied CO2 than the product locks away. The manuscript's
  environmental section counts only grid electricity and therefore MISSES the
  larger term entirely.""" % co2_fixed)

    with open(os.path.join(HERE, "new_ideas_results.json"), "w") as f:
        json.dump(res, f, indent=1)
    print("\nwrote new_ideas_results.json")


if __name__ == "__main__":
    main()
