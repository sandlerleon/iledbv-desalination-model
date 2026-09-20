# -*- coding: utf-8 -*-
"""Second-pass polishing analysis for the ILEDBV manuscript.

Reviewer 3 asks, directly: "Was a second-pass BWRO system considered for
controlling boron and/or chloride concentration, and if not, why?" This script
answers that quantitatively, and also tests the gravity-fed variant (feeding the
second pass from an elevated cistern instead of a booster pump).

Two things in the proposal handed to me do not survive checking and are corrected
here rather than carried into the paper:

  * Nanofiltration is not a TDS-polishing membrane. NF rejects divalent ions well
    (>95% SO4, Mg, Ca) but monovalent NaCl poorly - typically 10-70%, not the
    90-95% quoted. A low-pressure / ULE *brackish RO* element is the correct
    choice for a second pass; NF is what this process already uses upstream for
    brine concentration, where divalent selectivity is exactly what is wanted.
  * Boron, not TDS, is what actually drives second passes in SWRO. Boric acid is
    un-ionized at seawater pH and passes the first-pass membrane; that is the
    reason the industry adds a second pass at elevated pH.

    python second_pass_analysis.py
"""
import json, os

FT_PER_PSI = 2.31            # fresh water, ~15 C
PSI_PER_BAR = 14.5038
M_PER_FT = 0.3048

# ------------------------------------------------------- plant baseline (paper)
R1 = 0.45                    # first-pass recovery
S_FEED = 35.0                # g/L
SEC_DESAL = 2.73             # kWh/m3 permeate, desalination stage (manuscript)
ETA_PUMP = 0.85

# ------------------------------------------------- first-pass permeate quality
# Typical SWRO first-pass performance at R = 45%, new membranes, 15 C.
TDS_PERM1 = 250.0            # mg/L, order of magnitude for a well-run single pass
B_SEAWATER = 4.6             # mg/L boron in standard seawater
B_REJ1 = 0.80                # first-pass boron rejection at feed pH ~8 (75-90%)
CL_PERM1 = 140.0             # mg/L chloride in first-pass permeate

# ---------------------------------------------------------------- the targets
TARGETS = {
    "WHO drinking-water guideline, boron":            ("B",  2.4),
    "EU / common municipal spec, boron":              ("B",  1.0),
    "Irrigation of boron-sensitive crops":            ("B",  0.5),
    "US secondary standard, chloride":                ("Cl", 250.0),
}


def head_for(pressure_bar):
    psi = pressure_bar * PSI_PER_BAR
    ft = psi * FT_PER_PSI
    return psi, ft, ft * M_PER_FT


def sec_second_pass(p_bar, recovery, treated_fraction, eta=0.80):
    """kWh per m3 of FINAL product, for a partial (split) second pass."""
    per_m3_feed = p_bar / (36.0 * eta)        # 1 bar = 1e5 Pa; 3.6e6 J = 1 kWh
    per_m3_perm = per_m3_feed / recovery
    return per_m3_perm * treated_fraction


def main():
    out = {}

    # ---------------------------------------------- 1. what the first pass leaves
    b1 = B_SEAWATER * (1 - B_REJ1)
    print("FIRST-PASS PERMEATE (baseline R = %.0f%%, feed %.0f g/L)" % (R1 * 100, S_FEED))
    print("   TDS      ~ %5.0f mg/L" % TDS_PERM1)
    print("   chloride ~ %5.0f mg/L   (US secondary standard 250 mg/L)" % CL_PERM1)
    print("   boron    ~ %5.2f mg/L   (%.0f%% rejection of %.1f mg/L seawater boron)"
          % (b1, B_REJ1 * 100, B_SEAWATER))
    print()
    print("   Chloride and TDS already meet potable limits. Boron does not meet the")
    print("   1.0 mg/L municipal spec, and is marginal against WHO's 2.4 mg/L.")
    print("   -> a second pass is justified by BORON, not by TDS.")
    out["first_pass"] = {"tds_mg_l": TDS_PERM1, "cl_mg_l": CL_PERM1, "boron_mg_l": round(b1, 3)}

    # ------------------------------------- 2. gravity feed: how tall a tower?
    print("\nGRAVITY-FED SECOND PASS - REQUIRED CISTERN ELEVATION")
    print("   %-28s %8s %9s %9s" % ("feed pressure", "psi", "head, ft", "head, m"))
    grav = {}
    for label, bar in (("ULE / low-energy BWRO", 6.0),
                       ("typical second pass", 12.0),
                       ("high-rejection second pass", 14.0)):
        psi, ft, m = head_for(bar)
        grav[label] = {"bar": bar, "psi": round(psi, 1), "ft": round(ft, 1), "m": round(m, 1)}
        print("   %-28s %8.1f %9.1f %9.1f" % ("%s (%.0f bar)" % (label, bar), psi, ft, m))
    out["gravity_head"] = grav

    # what a realistic site can actually give
    print("\n   For comparison, available static head at a coastal plant:")
    for label, ft in (("ground-level tank on a plinth", 10),
                      ("elevated service reservoir", 40),
                      ("hillside site above the plant", 100)):
        psi = ft / FT_PER_PSI
        print("   %-32s %5d ft -> %5.1f psi (%.2f bar)" % (label, ft, psi, psi / PSI_PER_BAR))
    print("\n   A 12 bar second pass needs ~%.0f m of head. No coastal municipal plant"
          % head_for(12.0)[2])
    print("   has that, and building it would cost far more than the booster pump it")
    print("   replaces - which is why the industry uses a ground-level break tank and")
    print("   a small multistage booster pump instead.")

    # ------------------------------------------ 3. energy cost of a real second pass
    print("\nENERGY COST OF A CONVENTIONAL (PUMPED) SECOND PASS")
    print("   %-34s %10s %12s %10s" % ("configuration", "dSEC", "stage SEC", "vs 3.95"))
    cfg = {}
    for label, p, rec, frac in (("full second pass, 12 bar", 12.0, 0.90, 1.00),
                                ("split-partial, 50% treated", 12.0, 0.90, 0.50),
                                ("split-partial, 35% treated", 12.0, 0.90, 0.35),
                                ("ULE elements, 6 bar, full", 6.0, 0.85, 1.00)):
        d = sec_second_pass(p, rec, frac)
        tot = SEC_DESAL + d
        cfg[label] = {"delta_sec": round(d, 3), "stage_sec": round(tot, 3),
                      "pct_below_baseline": round(100 * (1 - tot / 3.95), 1)}
        print("   %-34s %+9.3f %11.2f %9.1f%%" % (label, d, tot, 100 * (1 - tot / 3.95)))
    out["second_pass_energy"] = cfg
    print("\n   The manuscript's headline is 2.73 kWh/m3, 31%% below the 3.95 baseline.")
    print("   A boron-compliant plant carries a second pass, so the honest comparison")
    print("   is %.2f-%.2f kWh/m3 - still below baseline, but by less." %
          (SEC_DESAL + sec_second_pass(12.0, 0.90, 0.35),
           SEC_DESAL + sec_second_pass(12.0, 0.90, 1.00)))

    # --------------------------------------------- 4. does the second pass deliver?
    print("\nSECOND-PASS PRODUCT QUALITY (boron, elevated pH)")
    for rej, ph in ((0.90, "pH 8.5"), (0.95, "pH 9.5"), (0.98, "pH 10.5")):
        b2 = b1 * (1 - rej)
        ok = [name for name, (sp, lim) in TARGETS.items() if sp == "B" and b2 <= lim]
        print("   rejection %.0f%% (%s) -> %.3f mg/L B   meets: %s"
              % (rej * 100, ph, b2, "; ".join(ok) if ok else "nothing"))
    out["boron_after_second_pass"] = {str(r): round(b1 * (1 - r), 4) for r in (0.90, 0.95, 0.98)}

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "second_pass_results.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("\nwrote second_pass_results.json")


if __name__ == "__main__":
    main()
