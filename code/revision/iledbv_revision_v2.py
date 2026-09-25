# -*- coding: utf-8 -*-
"""ILEDBV revision model v2 - the computational basis of the DWT revision.

Everything the revised manuscript quotes is produced here and written to
iledbv_revision_v2.json, so the text cannot drift from the computation.

Structure follows a consistency-test approach: each subsystem claim is checked
against a physical or published constraint rather than carried as an assumed
value, and a claim is allowed to fail.

    T1  concentrator energy vs the least work of separation
    T2  osmotic-pressure model deviation at brine salinity
    T3  boundary-layer management: the ceiling on any centrifugal scheme
    T4  alkalinity: the carbon and energy cost of the base that makes Mg(OH)2
    T5  calcium closure across the precipitation train
    EROI + full carbon balance + Monte Carlo on net LCOW

    python iledbv_revision_v2.py
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BAR2KWH = 1e5 / 3.6e6

# ----------------------------------------------------------------- baseline
R = 0.45                     # RO recovery
S_FEED, S_BRINE, S_CONC = 35.0, 63.5, 121.0      # g/L
CONC_RECOVERY = 0.50
CRYST_SEC = 11.5             # kWh per m3 crystallizer feed
SEC_DESAL = 2.73             # kWh/m3 permeate, desalination stage
NDP, ETA_PUMP, ETA_PX = 15.0, 0.85, 0.96
PI_BRINE = 49.0              # bar

KG_CACO3_FEED, KG_MGOH2_FEED = 0.966, 3.00       # kg per m3 of FEED
PRICE_CA, PRICE_MG = 470.0, 800.0                # $/t

MW = dict(CO2=44.009, CaCO3=100.09, Na2CO3=105.99, MgOH2=58.32,
          CaOH2=74.09, CaO=56.08, MgO=40.30, NaOH=39.997,
          dolime=96.38, Ca=40.08, Mg=24.305)

# Cradle-to-gate embodied CO2. TO BE LOCKED against a published LCA before
# submission; swept in the Monte Carlo rather than relied on as point values.
EMB = {"Na2CO3": 1.00, "CaO": 1.20, "dolime": 1.20, "NaOH": 1.90}
KWH_PER_KG_NAOH = 2.5        # electrochemical route, membrane chlor-alkali


def pi_linear(tds):
    return 27.0 * tds / 35.0


# ============================================================== T1 concentrator
def least_work(pi_feed, recovery):
    """Reversible work per m3 of FEED: integral of pi_f/(1-x) dx from 0 to r."""
    return pi_feed * np.log(1.0 / (1.0 - recovery)) * BAR2KWH


def t1_concentrator():
    w = least_work(PI_BRINE, CONC_RECOVERY)
    return {"pi_feed_bar": PI_BRINE,
            "least_work_kwh_per_m3_brine": round(float(w), 4),
            "manuscript_range": [0.50, 0.75, 1.00],
            "ratio_to_minimum": {str(v): round(v / float(w), 3) for v in (0.5, 0.75, 1.0)},
            "realistic_at_second_law_eff":
                {str(e): round(float(w) / e, 3) for e in (0.25, 0.40, 0.55)}}


# ============================================================== T2 osmotic model
def t2_osmotic():
    out = {}
    for gain in (0.00, 0.08, 0.16, 0.24):
        f = 1.0 + gain * (S_CONC - 35.0) / (120.0 - 35.0)
        out["phi_gain_%.2f" % gain] = {"linear_bar": round(pi_linear(S_CONC), 1),
                                       "corrected_bar": round(pi_linear(S_CONC) * f, 1),
                                       "understated_pct": round(100 * (f - 1), 1)}
    return out


# ================================================= T3 boundary-layer ceiling
def t3_polarization():
    qf, qp, qb = 1.0, R, 1.0 - R

    def sec(pf):
        gross = (pf * qf / ETA_PUMP) * BAR2KWH / qp
        credit = (ETA_PX * pf * qb) * BAR2KWH / qp
        return gross - credit

    out = {}
    for beta in (1.05, 1.10, 1.15, 1.20):
        s_cp, s_ideal = sec(beta * PI_BRINE + NDP), sec(PI_BRINE + NDP)
        out["beta_%.2f" % beta] = {"sec_with_polarization": round(s_cp, 3),
                                   "sec_if_eliminated": round(s_ideal, 3),
                                   "ceiling_kwh_per_m3": round(s_cp - s_ideal, 3),
                                   "ceiling_pct": round(100 * (s_cp - s_ideal) / s_cp, 1)}
    return out


# ============================================ T4/T5 alkalinity and calcium
def precipitation_routes():
    """Reagent demand, carbon, and calcium closure for four alkalinity routes.

    Per m3 of PERMEATE. Magnesium recovery needs two equivalents of base per mole
    of Mg(OH)2 however it is supplied; the routes differ in where the base comes
    from and what else it puts into the stream.
    """
    kg_ca, kg_mg = KG_CACO3_FEED / R, KG_MGOH2_FEED / R
    n_ca, n_mg = kg_ca / MW["CaCO3"], kg_mg / MW["MgOH2"]      # kmol per m3 permeate
    co2_fixed = kg_ca * MW["CO2"] / MW["CaCO3"]

    routes = {}

    # (A) as written: soda ash for Ca, lime for Mg
    kg_soda = n_ca * MW["Na2CO3"]
    kg_cao = n_mg * MW["CaO"]
    routes["A: soda ash + lime (as written)"] = dict(
        reagents={"Na2CO3": round(kg_soda, 3), "CaO": round(kg_cao, 3)},
        co2_reagents=kg_soda * EMB["Na2CO3"] + kg_cao * EMB["CaO"],
        ca_released_kmol=n_mg, mg_imported_kg=0.0, extra_kwh=0.0)

    # (B) dosed CO2 replaces the soda ash; lime still supplies the Mg base.
    # Ca2+ + CO2 + 2OH- -> CaCO3 + H2O, so the carbonate source is the dosed gas.
    kg_co2_dosed = n_ca * MW["CO2"]
    kg_cao_b = (n_mg + n_ca) * MW["CaO"]        # base for Mg, plus 2 OH- for the carbonate
    routes["B: dosed CO2 + lime"] = dict(
        reagents={"CO2 (captured)": round(kg_co2_dosed, 3), "CaO": round(kg_cao_b, 3)},
        co2_reagents=kg_cao_b * EMB["CaO"] - kg_co2_dosed,   # dosed CO2 is a credit if captured
        ca_released_kmol=n_mg + n_ca, mg_imported_kg=0.0, extra_kwh=0.0)

    # (C) dolime: CaO.MgO supplies alkalinity AND magnesium, halving the calcium
    # released, but half the product is then imported rather than recovered.
    n_dolime = n_mg / 2.0
    routes["C: dosed CO2 + dolime"] = dict(
        reagents={"CO2 (captured)": round(kg_co2_dosed, 3),
                  "dolime CaO.MgO": round(n_dolime * MW["dolime"], 3)},
        co2_reagents=n_dolime * MW["dolime"] * EMB["dolime"] - kg_co2_dosed,
        ca_released_kmol=n_dolime + n_ca,
        mg_imported_kg=n_dolime * MW["MgOH2"], extra_kwh=0.0)

    # (D) electrochemical base: no calcination carbon, but the energy is real
    kg_naoh = (2 * n_mg + 2 * n_ca) * MW["NaOH"]
    routes["D: dosed CO2 + electrochemical base"] = dict(
        reagents={"CO2 (captured)": round(kg_co2_dosed, 3), "NaOH (on-site)": round(kg_naoh, 3)},
        co2_reagents=-kg_co2_dosed, ca_released_kmol=n_ca * 0.0,
        mg_imported_kg=0.0, extra_kwh=kg_naoh * KWH_PER_KG_NAOH)

    for k, v in routes.items():
        v["co2_reagents"] = round(float(v["co2_reagents"]), 3)
        v["co2_fixed_in_product"] = round(float(co2_fixed), 3)
        v["ca_released_kmol"] = round(float(v["ca_released_kmol"]), 4)
        v["ca_removed_kmol"] = round(float(n_ca), 4)
        v["ca_closure_ratio"] = round(float(v["ca_released_kmol"] / n_ca), 2)
        v["extra_kwh"] = round(float(v["extra_kwh"]), 2)
    return routes, co2_fixed, n_ca, n_mg


# ======================================================================= EROI
def eroi(conc_sec):
    qp, qb = R, 1.0 - R
    q_conc = qb * (1.0 - CONC_RECOVERY)
    e = conc_sec * qb + CRYST_SEC * q_conc                 # kWh per m3 feed
    kg = KG_CACO3_FEED + KG_MGOH2_FEED
    val = (KG_CACO3_FEED * PRICE_CA + KG_MGOH2_FEED * PRICE_MG) / 1000.0
    return {"conc_sec_used": conc_sec,
            "kwh_per_m3_permeate": round(e / qp, 3),
            "kwh_per_tonne_product": round(e / (kg / 1000.0), 0),
            "gross_value_usd_per_m3_feed": round(val, 4),
            "kwh_per_usd_product": round(e / val, 2)}


# =============================================================== Monte Carlo
def monte_carlo(n=300_000, seed=20260919, return_samples=False):
    rng = np.random.default_rng(seed)
    w_min = float(least_work(PI_BRINE, CONC_RECOVERY))

    eff2 = rng.uniform(0.25, 0.55, n)                 # second-law eff of concentrator
    conc_sec = w_min / eff2                           # now physically bounded
    cryst = rng.uniform(8.0, 15.0, n)
    intake = rng.uniform(0.05, 0.80, n)
    elec = rng.uniform(0.05, 0.12, n)
    uplift = rng.uniform(0.20, 0.60, n)
    f_ca = rng.uniform(0.50, 0.70, n)
    f_mg = rng.uniform(0.05, 0.20, n)
    p_ca = PRICE_CA * rng.uniform(0.7, 1.3, n)
    p_mg = PRICE_MG * rng.uniform(0.7, 1.3, n)
    opex_frac = rng.uniform(0.25, 0.45, n)
    emb_cao = rng.uniform(0.9, 1.5, n)
    emb_soda = rng.uniform(0.8, 1.3, n)
    grid = rng.uniform(0.15, 0.65, n)

    qp, qb = R, 1.0 - R
    q_conc = qb * (1.0 - CONC_RECOVERY)
    sec = intake + (SEC_DESAL - 0.10) + conc_sec * qb / qp + cryst * q_conc / qp

    # OPEX is costed explicitly rather than as a share of energy. Treating it as a
    # fraction hid the dominant term: the precipitation reagents cost more per cubic
    # metre than the minerals they produce are worth.
    p_soda = rng.uniform(0.18, 0.35, n)          # $/kg soda ash
    p_lime = rng.uniform(0.08, 0.18, n)          # $/kg hydrated lime
    KG_SODA, KG_LIME = 1.0231, 3.7923            # per m3 FEED, from design_and_costing.py
    reagents = (KG_SODA * p_soda + KG_LIME * p_lime) / R
    fixed_opex = 0.235                           # membranes, labour, maintenance, insurance, solids
    capex = 1375.0 * (1 + uplift) * 0.08 / 365.0
    lcow_gross = capex + sec * elec + reagents + fixed_opex
    credit = (KG_CACO3_FEED * f_ca * p_ca + KG_MGOH2_FEED * f_mg * p_mg) / 1000.0 / qp
    lcow_net = lcow_gross - credit

    kg_ca, kg_mg = KG_CACO3_FEED / R, KG_MGOH2_FEED / R
    n_ca, n_mg = kg_ca / MW["CaCO3"], kg_mg / MW["MgOH2"]
    co2 = (sec * grid
           + n_ca * MW["Na2CO3"] * emb_soda
           + n_mg * MW["CaO"] * emb_cao
           - kg_ca * MW["CO2"] / MW["CaCO3"])

    def s(a):
        return {"median": round(float(np.median(a)), 3),
                "p05": round(float(np.percentile(a, 5)), 3),
                "p95": round(float(np.percentile(a, 95)), 3)}

    if return_samples:          # used by make_figures.py so Figure 5 is this exact draw
        return {"lcow_net": lcow_net, "reagents": reagents, "credit": credit}

    return {"n": n, "seed": seed,
            "concentrator_sec": s(conc_sec), "sec_total": s(sec),
            "lcow_gross": s(lcow_gross), "mineral_credit": s(credit),
            "reagent_opex": s(reagents), "total_opex": s(sec * elec + reagents + fixed_opex),
            "lcow_net": s(lcow_net), "co2_net_kg_per_m3": s(co2),
            "p_beats_conventional_lcow": round(float((lcow_net < 0.76).mean()), 3),
            "p_lcow_negative": round(float((lcow_net < 0).mean()), 4),
            "p_carbon_negative": round(float((co2 < 0).mean()), 4)}


def main():
    res = {}
    line = "=" * 78

    res["t1_concentrator"] = t1 = t1_concentrator()
    print(line); print("T1  Concentrator energy against the least work of separation"); print(line)
    print("   reversible minimum : %.3f kWh per m3 of brine processed"
          % t1["least_work_kwh_per_m3_brine"])
    for v, r in t1["ratio_to_minimum"].items():
        print("   assumed %-5s      : %.2f x minimum   %s"
              % (v, r, "IMPOSSIBLE" if r < 1 else "needs %.0f%% second-law eff" % (100 / r)))
    print("   physically realistic: %s kWh/m3 brine"
          % " to ".join("%.2f" % v for v in
                        (t1["realistic_at_second_law_eff"]["0.55"],
                         t1["realistic_at_second_law_eff"]["0.25"])))

    res["t2_osmotic"] = t2_osmotic()
    res["t3_polarization"] = t3 = t3_polarization()
    print("\n" + line); print("T3  Ceiling on any boundary-layer / centrifugal scheme"); print(line)
    for k, v in t3.items():
        print("   %s : at most %.3f kWh/m3 (%.1f%%)" % (k, v["ceiling_kwh_per_m3"], v["ceiling_pct"]))

    routes, co2_fixed, n_ca, n_mg = precipitation_routes()
    res["precipitation_routes"] = routes
    res["co2_fixed_kg_per_m3_permeate"] = round(float(co2_fixed), 3)
    print("\n" + line); print("T4/T5  Alkalinity carbon, energy, and calcium closure"); print(line)
    print("   CO2 permanently fixed in the carbonate product: %.2f kg per m3 permeate\n" % co2_fixed)
    print("   %-38s %9s %9s %8s %9s" % ("route", "reagentCO2", "Ca ratio", "Mg imp.", "extra kWh"))
    for k, v in routes.items():
        print("   %-38s %9.2f %9.1fx %8.2f %9.1f"
              % (k, v["co2_reagents"], v["ca_closure_ratio"], v["mg_imported_kg"], v["extra_kwh"]))

    res["eroi"] = {}
    print("\n" + line); print("EROI of the valorization stage"); print(line)
    for cs in (0.75, 1.71, 2.36):
        e = eroi(cs); res["eroi"]["conc_%.2f" % cs] = e
        print("   concentrator %.2f -> %6.2f kWh/m3 permeate, %5.0f kWh per tonne product"
              % (cs, e["kwh_per_m3_permeate"], e["kwh_per_tonne_product"]))

    res["monte_carlo"] = mc = monte_carlo()
    print("\n" + line); print("MONTE CARLO  300,000 samples"); print(line)
    for k in ("concentrator_sec", "sec_total", "reagent_opex", "total_opex",
              "lcow_gross", "mineral_credit", "lcow_net", "co2_net_kg_per_m3"):
        d = mc[k]
        print("   %-20s median %8.3f   90%% interval %8.3f to %8.3f"
              % (k, d["median"], d["p05"], d["p95"]))
    print("   P(net LCOW beats $0.76/m3) = %.0f%%" % (100 * mc["p_beats_conventional_lcow"]))
    print("   P(net LCOW < 0)            = %.1f%%" % (100 * mc["p_lcow_negative"]))
    print("   P(carbon negative)         = %.1f%%" % (100 * mc["p_carbon_negative"]))

    with open(os.path.join(HERE, "iledbv_revision_v2.json"), "w") as f:
        json.dump(res, f, indent=1)
    print("\nwrote iledbv_revision_v2.json")


if __name__ == "__main__":
    main()
