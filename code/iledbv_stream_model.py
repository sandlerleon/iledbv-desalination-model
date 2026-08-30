#!/usr/bin/env python3
"""
ILEDBV stream-by-stream mass/energy/economic reconciliation model.

Reproduces every headline number already quoted in the manuscript body
(Sections 3-4: SEC 2.73 / 3.65 / 10.68 kWh/m3-permeate; 0.966 kg CaCO3 and
3.00 kg Mg(OH)2 per m3 feed; net LCOW $0.42/m3 at 10% Mg(OH)2 sellable
fraction) directly from the equations already stated in Sections 3.1-3.9,
using no parameters beyond those already given in the manuscript text.
This closes reviewer must-fix #1 (stream-by-stream reconciliation of
2.73 -> 3.65 -> 10.68) with a table traceable line-by-line to Table 4 below.

It then extends the same, now-validated model with:
  - a corrected, third-party-sourced global Mg(OH)2 market-volume figure
    (reviewer must-fix #4) -- the manuscript's previous 1.55e6 t/yr figure
    could not be traced to a citable primary source; the real, current
    market-research figure is roughly 4x smaller, which *strengthens*
    (not weakens) the paper's market-absorption-is-constraining finding.
  - a membrane-rejection sensitivity for Mg/Ca recovery (reviewer
    strongly-recommended #8)
  - a mineral-price sensitivity extending the existing LCOW tornado
    (reviewer must-fix #6)

All results are written to iledbv_results.json and the two new figures
(Figure 7 stream table + rejection sensitivity, Figure 8 updated tornado
with mineral price) are regenerated as PNGs.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Baseline process parameters (all taken directly from the manuscript,
# Sections 2-3; nothing here is a new assumption)
# ---------------------------------------------------------------------
R = 0.45                # recovery ratio (Section 3.1)
S_FEED = 35.0            # g/L feed TDS
NDP_BAR = 15.0            # net driving pressure allowance, bar (Section 3.4)
ETA_PUMP = 0.85           # high-pressure pump efficiency (Section 3.5)
ETA_PX = 0.96             # isobaric PX efficiency, baseline case (Section 2.4/4.1)
ETA_TURBINE = 0.78        # conventional turbine-type ERD efficiency (Table 1, Case A)

PRETREAT_SUBSURFACE = 0.10   # kWh/m3 permeate, subsurface intake (Section 2.2)
POST_TREAT = 0.07            # kWh/m3 permeate (Section 3.5)

CONCENTRATOR_RECOVERY = 0.50      # secondary concentrator additional water recovery (Section 2.5)
CONCENTRATOR_SEC = 0.75           # kWh/m3 of brine processed, midpoint (Section 3.6)
CONCENTRATOR_REJ_MONO = 0.90      # Section 3.6
CONCENTRATOR_REJ_DIV = 0.98       # Section 3.6

CRYSTALLIZER_SEC = 11.5   # kWh/m3 of crystallizer feed, midpoint (Section 3.8)

RO_REJ_MONO = 0.993   # Section 3.2
RO_REJ_DIV = 0.997     # Section 3.2
RO_REJ_LI = 0.985      # Section 3.2

# Standard seawater reference composition at S=35 g/kg (Millero et al. 2008,
# ref [10], already cited in the manuscript for this exact purpose)
C_F_MG = 1.280   # g/L Mg2+
C_F_CA = 0.4121  # g/L Ca2+

Y_CA = 0.95   # CaCO3 precipitation yield (Section 3.7)
Y_MG = 0.98   # Mg(OH)2 precipitation yield (Section 3.7)
M_CACO3_OVER_CA = 100.09 / 40.08
M_MGOH2_OVER_MG = 58.32 / 24.305

BAR_M3_TO_KWH = 1e5 / 3.6e6   # 1 bar*m3 = 100,000 J = 0.027778 kWh

PRICE_MG = 800.0    # $/t Mg(OH)2 industrial grade (Section 3.9)
PRICE_CA = 470.0    # $/t CaCO3 industrial grade (Section 3.9)


def osmotic_pressure_bar(tds_g_l):
    """pi(TDS) = 27 * (TDS/35), Section 3.3."""
    return 27.0 * (tds_g_l / 35.0)


def bulk_tds_brine(qf=1.0, r=R, s_feed=S_FEED):
    """Bulk-TDS mass balance for the RO brine stream, using a mass-weighted
    effective bulk rejection between the monovalent (~85% of seawater TDS
    by mass) and divalent (~15%) ion classes given in Section 3.2. This
    reproduces the manuscript's stated 63.5 g/L RO-brine TDS (Section 4.3)
    to within rounding, and is used only for the osmotic-pressure/SEC
    calculation -- mineral masses use the explicit per-ion balance below,
    not this bulk approximation."""
    qp = qf * r
    qb = qf - qp
    r_eff = 0.85 * RO_REJ_MONO + 0.15 * RO_REJ_DIV
    c_p = s_feed * (1 - r_eff)
    c_b = (qf * s_feed - qp * c_p) / qb
    return c_b, qp, qb


def ro_px_sec(eta_erd, qf=1.0, r=R, s_feed=S_FEED, ndp=NDP_BAR, eta_pump=ETA_PUMP):
    """SEC_RO per Section 3.5, split into gross pumping energy and the PX
    (or turbine) recovery credit so both can be reported separately in the
    stream table."""
    c_b, qp, qb = bulk_tds_brine(qf, r, s_feed)
    pf = osmotic_pressure_bar(c_b) + ndp
    gross = (pf * qf / eta_pump) * BAR_M3_TO_KWH / qp
    credit = (eta_erd * pf * qb) * BAR_M3_TO_KWH / qp
    return gross, credit, gross - credit, pf, c_b


def ion_balance(c_f, r_ro, r_conc, qf=1.0, r=R, concentrator_recovery=CONCENTRATOR_RECOVERY):
    """Per-ion mass balance through RO then the secondary concentrator,
    Sections 3.2 and 3.6, returning the final concentrated-brine
    concentration (g/L) and the concentrator's concentrate volume (m3 per
    m3 of original feed)."""
    qp = qf * r
    qb = qf - qp
    c_p = c_f * (1 - r_ro)
    c_b = (qf * c_f - qp * c_p) / qb

    q_perm2 = qb * concentrator_recovery
    q_conc2 = qb - q_perm2
    c_perm2 = c_b * (1 - r_conc)
    c_conc2 = (qb * c_b - q_perm2 * c_perm2) / q_conc2
    return c_conc2, q_conc2


def mineral_masses(r_div=RO_REJ_DIV, r_div_conc=CONCENTRATOR_REJ_DIV):
    """kg CaCO3 and kg Mg(OH)2 recovered per m3 of original feed, Section 3.7."""
    c_ca, q_conc2 = ion_balance(C_F_CA, r_div, r_div_conc)
    c_mg, _ = ion_balance(C_F_MG, r_div, r_div_conc)
    m_caco3 = c_ca * q_conc2 * Y_CA * M_CACO3_OVER_CA
    m_mgoh2 = c_mg * q_conc2 * Y_MG * M_MGOH2_OVER_MG
    return m_caco3, m_mgoh2, q_conc2


def stream_table():
    """The reviewer-requested stream-by-stream table, Cases C->D->E."""
    gross, credit, sec_ro, pf, c_b = ro_px_sec(ETA_PX)
    qp = R
    qb = 1 - R
    q_conc2 = qb * (1 - CONCENTRATOR_RECOVERY)  # 0.275 at baseline

    row_pretreat = PRETREAT_SUBSURFACE
    row_gross = gross
    row_credit = -credit
    row_post = POST_TREAT
    case_c = row_pretreat + row_gross + row_credit + row_post

    row_concentrator = CONCENTRATOR_SEC * (qb / qp)
    case_d = case_c + row_concentrator

    row_precip = 0.0  # dosing/mixing energy not separately modeled; see note
    row_crystallizer = CRYSTALLIZER_SEC * (q_conc2 / qp)
    case_e = case_d + row_precip + row_crystallizer

    rows = [
        {"stage": "Pretreatment (subsurface intake)", "flow_basis": "m3 permeate", "energy_raw": PRETREAT_SUBSURFACE, "unit_raw": "kWh/m3 permeate", "kwh_per_m3_permeate": row_pretreat},
        {"stage": "SWRO pumping (gross, pre-recovery)", "flow_basis": "Pf*Qf/eta_pump", "energy_raw": None, "unit_raw": "-", "kwh_per_m3_permeate": row_gross},
        {"stage": "Isobaric PX recovery credit", "flow_basis": "m3 RO brine", "energy_raw": None, "unit_raw": "-", "kwh_per_m3_permeate": row_credit},
        {"stage": "Post-treatment", "flow_basis": "m3 permeate", "energy_raw": POST_TREAT, "unit_raw": "kWh/m3 permeate", "kwh_per_m3_permeate": row_post},
        {"stage": "SUBTOTAL -- Case C (desalination stage)", "flow_basis": "", "energy_raw": None, "unit_raw": "", "kwh_per_m3_permeate": case_c},
        {"stage": "Secondary brine concentration (NF)", "flow_basis": "m3 RO brine", "energy_raw": CONCENTRATOR_SEC, "unit_raw": "kWh/m3 brine", "kwh_per_m3_permeate": row_concentrator},
        {"stage": "SUBTOTAL -- Case D", "flow_basis": "", "energy_raw": None, "unit_raw": "", "kwh_per_m3_permeate": case_d},
        {"stage": "Precipitation (Ca/Mg dosing+mixing)", "flow_basis": "m3 concentrate", "energy_raw": 0.0, "unit_raw": "not separately modeled (Note 1)", "kwh_per_m3_permeate": row_precip},
        {"stage": "Crystallization (MVC, electrical)", "flow_basis": "m3 crystallizer feed", "energy_raw": CRYSTALLIZER_SEC, "unit_raw": "kWh/m3 crystallizer feed", "kwh_per_m3_permeate": row_crystallizer},
        {"stage": "TOTAL -- Case E (complete, near-ZLD)", "flow_basis": "", "energy_raw": None, "unit_raw": "", "kwh_per_m3_permeate": case_e},
    ]
    return rows, {"case_c": case_c, "case_d": case_d, "case_e": case_e, "pf_bar": pf, "c_b_brine_g_l": c_b, "q_conc2": q_conc2}


def rejection_sensitivity():
    """Sweep divalent RO rejection 98.5-99.7% (the range named by the
    reviewer) and report the resulting CaCO3/Mg(OH)2 recovery mass."""
    rejs = [0.985, 0.990, 0.995, 0.997]
    out = []
    for r_div in rejs:
        m_caco3, m_mgoh2, _ = mineral_masses(r_div=r_div)
        out.append({"ro_divalent_rejection": r_div, "kg_caco3_per_m3_feed": m_caco3, "kg_mgoh2_per_m3_feed": m_mgoh2})
    return out


def market_and_lcow(plant_m3_d=10000.0):
    m_caco3, m_mgoh2, _ = mineral_masses()
    v_annual_plant = plant_m3_d * 365.0
    # per-feed-m3 masses above are per m3 of FEED; convert to per m3 of
    # PERMEATE (plant capacity basis) by dividing by R, matching Table 2's
    # convention (plant capacity is expressed in permeate m3/d)
    mgoh2_t_yr = m_mgoh2 / R * plant_m3_d * 365.0 / 1000.0
    caco3_t_yr = m_caco3 / R * plant_m3_d * 365.0 / 1000.0

    # Corrected global Mg(OH)2 market volume: KBV Research (Report
    # KBV-20009, Feb 2024) states a 2022 global market volume of 3,875.8
    # hundred tonnes = 387,580 t/yr -- the manuscript's previous 1.55e6
    # t/yr figure could not be traced to a citable primary source.
    global_market_t_yr = 387580.0
    market_share_pct = 100.0 * mgoh2_t_yr / global_market_t_yr

    return {
        "plant_m3_d": plant_m3_d,
        "mgoh2_t_yr": mgoh2_t_yr,
        "caco3_t_yr": caco3_t_yr,
        "global_mgoh2_market_t_yr": global_market_t_yr,
        "market_share_pct": market_share_pct,
        "v_annual_m3": v_annual_plant,
    }


def mineral_price_sensitivity(sellable_fraction=0.10, lcow_gross=1.96):
    """Sensitivity of net LCOW to +/-30% mineral price, at the
    market-realistic 10% Mg(OH)2 sellable fraction (Section 4.5), holding
    gross LCOW fixed per the manuscript's own LCOW_net = LCOW - R/V formula
    (Section 3.9)."""
    mk = market_and_lcow()
    v = mk["v_annual_m3"]
    mgoh2_t = mk["mgoh2_t_yr"]
    caco3_t = mk["caco3_t_yr"]

    def lcow_net(p_mg, p_ca):
        r_minerals = sellable_fraction * mgoh2_t * p_mg + 1.0 * caco3_t * p_ca
        return lcow_gross - r_minerals / v

    base = lcow_net(PRICE_MG, PRICE_CA)
    low_mg = lcow_net(PRICE_MG * 0.7, PRICE_CA)
    high_mg = lcow_net(PRICE_MG * 1.3, PRICE_CA)
    low_ca = lcow_net(PRICE_MG, PRICE_CA * 0.7)
    high_ca = lcow_net(PRICE_MG, PRICE_CA * 1.3)
    low_both = lcow_net(PRICE_MG * 0.7, PRICE_CA * 0.7)
    high_both = lcow_net(PRICE_MG * 1.3, PRICE_CA * 1.3)

    return {
        "baseline_net_lcow": base,
        "mgoh2_price_-30%": low_mg, "mgoh2_price_+30%": high_mg,
        "caco3_price_-30%": low_ca, "caco3_price_+30%": high_ca,
        "both_prices_-30%": low_both, "both_prices_+30%": high_both,
    }


def main():
    rows, subtotals = stream_table()
    print("=== Stream-by-stream table ===")
    for row in rows:
        print(f"  {row['stage']:<42s} {row['kwh_per_m3_permeate']:+7.4f} kWh/m3 permeate")
    print(f"\nValidation vs. manuscript: Case C target 2.73 -> got {subtotals['case_c']:.3f}")
    print(f"Validation vs. manuscript: Case D target 3.65 -> got {subtotals['case_d']:.3f}")
    print(f"Validation vs. manuscript: Case E target 10.68 -> got {subtotals['case_e']:.3f}")

    m_caco3, m_mgoh2, q_conc2 = mineral_masses()
    print(f"\nValidation: 0.966 kg CaCO3/m3 feed -> got {m_caco3:.3f}")
    print(f"Validation: 3.00 kg Mg(OH)2/m3 feed -> got {m_mgoh2:.3f}")

    rej_sens = rejection_sensitivity()
    market = market_and_lcow()
    price_sens = mineral_price_sensitivity()

    results = {
        "stream_table": rows,
        "subtotals_kwh_per_m3": subtotals,
        "validation": {
            "case_c_target": 2.73, "case_c_model": subtotals["case_c"],
            "case_d_target": 3.65, "case_d_model": subtotals["case_d"],
            "case_e_target": 10.68, "case_e_model": subtotals["case_e"],
            "caco3_target_kg_per_m3_feed": 0.966, "caco3_model": m_caco3,
            "mgoh2_target_kg_per_m3_feed": 3.00, "mgoh2_model": m_mgoh2,
        },
        "rejection_sensitivity": rej_sens,
        "market_corrected": market,
        "mineral_price_sensitivity": price_sens,
        "market_source": "KBV Research, Global Magnesium Hydroxide Market Size, Share & Trends Analysis Report, Report ID KBV-20009, Feb 2024 (2022 base-year volume: 3,875.8 hundred tonnes = 387,580 t/yr, +4.6% CAGR 2019-2022)",
    }
    with open("iledbv_results.json", "w") as fh:
        json.dump(results, fh, indent=2)

    # --- Figure 7: stream-by-stream waterfall + rejection sensitivity ---
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))

    ax = axes[0]
    labels = ["Pretreat", "RO gross", "PX credit", "Post-treat", "Concentrator", "Precip.", "Crystallizer"]
    vals = [row_val for row_val, r in zip(
        [PRETREAT_SUBSURFACE, ro_px_sec(ETA_PX)[0], -ro_px_sec(ETA_PX)[1], POST_TREAT,
         CONCENTRATOR_SEC * ((1 - R) / R), 0.0, CRYSTALLIZER_SEC * (subtotals["q_conc2"] / R)], labels)]
    cum = np.cumsum([0] + vals[:-1])
    colors = ["#4C72B0" if v >= 0 else "#DD8452" for v in vals]
    ax.bar(labels, vals, bottom=cum, color=colors)
    ax.axhline(0, color="gray", lw=0.5)
    ax.set_ylabel("kWh/m$^3$ permeate")
    ax.set_title("(a) Stream-by-stream energy\n(Case C to Case E)")
    ax.tick_params(axis="x", rotation=35)
    for lbl in ax.get_xticklabels():
        lbl.set_ha("right")

    ax2 = axes[1]
    rejs = [d["ro_divalent_rejection"] * 100 for d in rej_sens]
    mg_vals = [d["kg_mgoh2_per_m3_feed"] for d in rej_sens]
    ca_vals = [d["kg_caco3_per_m3_feed"] for d in rej_sens]
    ax2.plot(rejs, mg_vals, "o-", label="Mg(OH)$_2$", color="#4C72B0")
    ax2b = ax2.twinx()
    ax2b.plot(rejs, ca_vals, "s--", label="CaCO$_3$", color="#DD8452")
    ax2.set_xlabel("RO divalent-ion rejection (%)")
    ax2.set_ylabel("kg Mg(OH)$_2$ / m$^3$ feed", color="#4C72B0")
    ax2b.set_ylabel("kg CaCO$_3$ / m$^3$ feed", color="#DD8452")
    ax2.set_title("(b) Mineral recovery vs.\nRO rejection sensitivity")

    plt.tight_layout()
    plt.savefig("figure7_stream_and_rejection.png", dpi=200)

    # --- Figure 8: updated tornado with mineral price ---
    fig2, ax3 = plt.subplots(figsize=(7.5, 4.2))
    base = price_sens["baseline_net_lcow"]
    bars = [
        ("Electricity price (±50%)", None, None),  # placeholder for existing param, not recomputed here
        ("Mg(OH)$_2$ + CaCO$_3$ price (±30%)", price_sens["both_prices_-30%"], price_sens["both_prices_+30%"]),
        ("Mg(OH)$_2$ price only (±30%)", price_sens["mgoh2_price_-30%"], price_sens["mgoh2_price_+30%"]),
        ("CaCO$_3$ price only (±30%)", price_sens["caco3_price_-30%"], price_sens["caco3_price_+30%"]),
    ]
    bars = [b for b in bars if b[1] is not None]
    names = [b[0] for b in bars]
    los = [min(b[1], b[2]) for b in bars]
    his = [max(b[1], b[2]) for b in bars]
    y = np.arange(len(names))
    ax3.barh(y, [h - l for l, h in zip(los, his)], left=los, color="#4C72B0", alpha=0.8)
    ax3.axvline(base, color="black", lw=1, ls="--", label=f"baseline \\${base:.2f}/m$^3$")
    ax3.set_yticks(y)
    ax3.set_yticklabels(names)
    ax3.set_xlabel("Net LCOW (\\$/m$^3$), 10,000 m$^3$/d, 10% Mg(OH)$_2$ sellable")
    ax3.set_title("Mineral-price sensitivity added to\nFigure 6 (new panel)")
    ax3.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    plt.savefig("figure8_mineral_price_tornado.png", dpi=200)

    print("\n=== Market (corrected) ===")
    print(json.dumps(market, indent=2))
    print("\n=== Mineral price sensitivity ===")
    print(json.dumps(price_sens, indent=2))


if __name__ == "__main__":
    main()
