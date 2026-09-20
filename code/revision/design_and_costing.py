# -*- coding: utf-8 -*-
"""Design basis, ion-by-ion stream table, OPEX breakdown and stage costing.

Answers the design questions Reviewer 3 asked (membrane selection and rejections,
precipitation reagents and dosages, crystallizer inlet composition, salinity and
ionic profile across the whole process) and the costing questions Reviewer 1
asked (OPEX composition, and a like-for-like stage cost comparison).

    python design_and_costing.py  ->  design_costing.json
"""
import io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))

# Standard seawater reference composition at S = 35 g/kg, g/L
SEAWATER = {"Na+": 10.781, "Mg2+": 1.284, "Ca2+": 0.4119, "K+": 0.399,
            "Cl-": 19.353, "SO4 2-": 2.712, "HCO3-": 0.126, "Br-": 0.0673}
VALENCE = {"Na+": 1, "Mg2+": 2, "Ca2+": 2, "K+": 1,
           "Cl-": 1, "SO4 2-": 2, "HCO3-": 1, "Br-": 1}
MW = {"Ca2+": 40.08, "Mg2+": 24.305, "CaCO3": 100.09, "MgOH2": 58.32,
      "Na2CO3": 105.99, "CaOH2": 74.09, "CO2": 44.009}

R_RO = 0.45
REJ_RO = {1: 0.993, 2: 0.997}
R_CONC = 0.50
REJ_CONC_ASSUMED = {1: 0.90, 2: 0.98}      # as used in the manuscript
REJ_CONC_TRUE_NF = {1: 0.30, 2: 0.97}      # what a real NF element would do
Y_CA, Y_MG = 0.95, 0.98


def stage(feed_gl, q_in, recovery, rej):
    """One membrane stage: returns (permeate dict, concentrate dict, q_perm, q_conc)."""
    q_p = q_in * recovery
    q_c = q_in - q_p
    perm, conc = {}, {}
    for ion, c in feed_gl.items():
        r = rej[VALENCE[ion]]
        c_p = c * (1 - r)
        c_c = (q_in * c - q_p * c_p) / q_c
        perm[ion], conc[ion] = c_p, c_c
    return perm, conc, q_p, q_c


def tds(d):
    return sum(d.values())


def build_streams(rej_conc):
    s = {}
    s["S1 raw seawater"] = (dict(SEAWATER), 1.0)
    perm, brine, qp, qb = stage(SEAWATER, 1.0, R_RO, REJ_RO)
    s["S2 RO permeate"] = (perm, qp)
    s["S3 RO brine"] = (brine, qb)
    p2, conc2, qp2, qc2 = stage(brine, qb, R_CONC, rej_conc)
    s["S4 concentrator permeate"] = (p2, qp2)
    s["S5 concentrator concentrate"] = (conc2, qc2)

    # precipitation: Ca removed as CaCO3 (soda ash), Mg removed as Mg(OH)2 (lime),
    # and the lime returns one Ca2+ per Mg2+ precipitated
    after = dict(conc2)
    ca_removed = conc2["Ca2+"] * Y_CA
    mg_removed = conc2["Mg2+"] * Y_MG
    ca_added = mg_removed / MW["Mg2+"] * MW["Ca2+"]        # from Ca(OH)2 dosing
    na_added = (ca_removed / MW["Ca2+"]) * 2 * 22.99       # from Na2CO3
    after["Ca2+"] = conc2["Ca2+"] - ca_removed + ca_added
    after["Mg2+"] = conc2["Mg2+"] - mg_removed
    after["Na+"] = conc2["Na+"] + na_added
    after["HCO3-"] = conc2["HCO3-"]
    s["S6 crystallizer feed"] = (after, qc2)
    return s, {"ca_removed_g_l": ca_removed, "ca_added_g_l": ca_added,
               "mg_removed_g_l": mg_removed, "q_conc2": qc2}


def precipitation_design(conc2, qc2, pr):
    """Reagent dosages, reactor sizing and solids, per m3 of FEED."""
    kg_caco3 = pr["ca_removed_g_l"] * qc2 * MW["CaCO3"] / MW["Ca2+"]
    kg_mgoh2 = pr["mg_removed_g_l"] * qc2 * MW["MgOH2"] / MW["Mg2+"]
    n_ca = kg_caco3 / MW["CaCO3"]
    n_mg = kg_mgoh2 / MW["MgOH2"]
    return {
        "reagent_Na2CO3_kg_per_m3_feed": round(n_ca * MW["Na2CO3"], 4),
        "reagent_CaOH2_kg_per_m3_feed": round(n_mg * MW["CaOH2"], 4),
        "stoichiometric_ratio": "1.0 mol Na2CO3 per mol Ca; 1.0 mol Ca(OH)2 per mol Mg",
        "assumed_excess_dosing": "10% over stoichiometric, typical of seawater practice",
        "CaCO3_kg_per_m3_feed": round(kg_caco3, 4),
        "MgOH2_kg_per_m3_feed": round(kg_mgoh2, 4),
        "reactor_residence_time_min": {"CaCO3 stage": 30, "Mg(OH)2 stage": 45},
        "reactor_volume_m3_per_1000m3d_feed": {
            "CaCO3 stage": round(qc2 * 1000 * 30 / 1440, 2),
            "Mg(OH)2 stage": round(qc2 * 1000 * 45 / 1440, 2)},
        "solid_liquid_separation": "gravity thickener followed by filter press",
        "assumed_cake_solids_pct": {"CaCO3": 65, "Mg(OH)2": 45},
        "product_purity_basis": "purity is set by co-precipitation and occlusion of "
                                "the NaCl background; see [9] for the dependence of "
                                "yield, purity and polymorph on that background",
    }


def opex_breakdown(sec_total, elec_price, pr_design, plant_m3_d=10000.0):
    """OPEX composition, $ per m3 of permeate (R1-5)."""
    feed_per_perm = 1.0 / R_RO
    energy = sec_total * elec_price
    chem = (pr_design["reagent_Na2CO3_kg_per_m3_feed"] * 0.25      # $/kg soda ash
            + pr_design["reagent_CaOH2_kg_per_m3_feed"] * 0.12     # $/kg hydrated lime
            ) * feed_per_perm
    items = {
        "Electricity": round(energy, 4),
        "Precipitation reagents": round(chem, 4),
        "Pretreatment and CIP chemicals": 0.030,
        "Membrane replacement (RO + concentrator)": 0.040,
        "Cartridge filters and consumables": 0.010,
        "Labour": 0.045,
        "Maintenance and spares (2% CAPEX/yr)": 0.055,
        "Insurance and overhead": 0.020,
        "Solids handling and product logistics": 0.035,
    }
    items["TOTAL OPEX"] = round(sum(items.values()), 4)
    items["_basis"] = ("$ per m3 permeate; chemical unit prices are bulk industrial "
                       "indicative values and are swept in the Monte Carlo")
    return items


def stage_costs():
    """Like-for-like boundary comparison, answering R1-12 directly."""
    rows = [
        ("Intake and pretreatment", "yes", "yes"),
        ("High-pressure pumping and RO", "yes", "yes"),
        ("Energy recovery device", "turbine ERD", "isobaric PX"),
        ("Post-treatment", "yes", "yes"),
        ("Boron-compliant second pass", "yes", "yes (added in revision)"),
        ("Brine outfall / discharge", "yes", "not applicable (no outfall)"),
        ("Brine concentration", "no", "yes"),
        ("Precipitation and solids handling", "no", "yes"),
        ("Crystallization", "no", "yes"),
        ("Mineral revenue credit", "no", "yes"),
    ]
    return {"note": "The $0.76/m3 conventional figure and the ILEDBV figure did not "
                    "previously share a boundary: the conventional case included a "
                    "brine outfall that ILEDBV does not have, and excluded the "
                    "valorization train that ILEDBV does. Comparisons in the revision "
                    "are made stage by stage on this table rather than headline to "
                    "headline.",
            "rows": rows}


def main():
    out = {}
    streams, pr = build_streams(REJ_CONC_ASSUMED)
    out["streams_as_modelled"] = {k: {"q_m3_per_m3_feed": round(q, 4),
                                      "TDS_g_L": round(tds(c), 2),
                                      "ions_g_L": {i: round(v, 4) for i, v in c.items()}}
                                  for k, (c, q) in streams.items()}

    print("ION-BY-ION STREAM TABLE  (g/L, per m3 of raw seawater feed)")
    ions = list(SEAWATER)
    print("  %-28s %7s %8s %s" % ("stream", "Q", "TDS", "".join("%9s" % i for i in ions)))
    for k, (c, q) in streams.items():
        print("  %-28s %7.3f %8.1f %s"
              % (k, q, tds(c), "".join("%9.3f" % c[i] for i in ions)))

    # what a genuine NF element would have done
    streams_nf, pr_nf = build_streams(REJ_CONC_TRUE_NF)
    out["streams_true_nf"] = {k: {"TDS_g_L": round(tds(c), 2)} for k, (c, q) in streams_nf.items()}
    print("\n  If the 'NF' stage were a genuine nanofiltration element (30%% monovalent")
    print("  rejection rather than 90%%), the crystallizer feed would be %.1f g/L"
          % tds(streams_nf["S6 crystallizer feed"][0]))
    print("  instead of %.1f g/L. At the rejections and pressures actually assumed the"
          % tds(streams["S6 crystallizer feed"][0]))
    print("  stage is a high-pressure, low-salt-rejection RO stage, not nanofiltration.")

    conc2, qc2 = streams["S5 concentrator concentrate"]
    design = precipitation_design(conc2, qc2, pr)
    out["precipitation_design"] = design
    print("\nPRECIPITATION DESIGN BASIS  (per m3 of feed)")
    for k in ("reagent_Na2CO3_kg_per_m3_feed", "reagent_CaOH2_kg_per_m3_feed",
              "CaCO3_kg_per_m3_feed", "MgOH2_kg_per_m3_feed"):
        print("   %-38s %.4f" % (k, design[k]))
    print("   reactor volume per 1000 m3/d feed : %s" % design["reactor_volume_m3_per_1000m3d_feed"])

    print("\nCALCIUM CLOSURE")
    print("   Ca removed as CaCO3 : %.4f g/L of concentrate" % pr["ca_removed_g_l"])
    print("   Ca returned by lime : %.4f g/L of concentrate  (%.1fx)"
          % (pr["ca_added_g_l"], pr["ca_added_g_l"] / pr["ca_removed_g_l"]))
    out["calcium_closure"] = {k: round(v, 4) for k, v in pr.items()}

    op = opex_breakdown(13.11, 0.08, design)
    out["opex"] = op
    print("\nOPEX BREAKDOWN  ($ per m3 permeate, SEC 13.11 kWh/m3, $0.08/kWh)")
    for k, v in op.items():
        if not k.startswith("_"):
            print("   %-42s %6.3f" % (k, v))

    out["stage_cost_boundary"] = stage_costs()
    print("\nBOUNDARY COMPARISON (R1-12)")
    print("   %-40s %-14s %s" % ("cost element", "conventional", "ILEDBV"))
    for a, b, c in stage_costs()["rows"]:
        print("   %-40s %-14s %s" % (a, b, c))

    io.open(os.path.join(HERE, "design_costing.json"), "w", encoding="utf-8").write(
        json.dumps(out, indent=1))
    print("\nwrote design_costing.json")


if __name__ == "__main__":
    main()
