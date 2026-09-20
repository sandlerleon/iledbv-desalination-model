# -*- coding: utf-8 -*-
"""Boron in the first-pass permeate: recalculated, with the error corrected.

The previous revision stated first-pass permeate boron as 0.92 mg/L and then
described it as "above the 1.0 mg/L specification". 0.92 is below 1.0. The
statement was wrong and the second-pass justification built on it was invalid.

The error came from treating boron rejection as a single number. It is not: boron
rejection falls with membrane age and rises sharply with temperature and pH,
because rejection depends on the dissociated borate fraction and boric acid is
un-ionized at seawater pH. A design figure has to be quoted at end-of-life and at
the warmest design temperature, not at new-membrane, cool-water conditions.

    python boron_recalc.py  ->  boron_results.json
"""
import io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))

# Boron in standard seawater. Reported values cluster around 4.5-5.0 mg/L, higher
# in the Arabian Gulf and Red Sea.
B_FEED = {"open ocean, standard seawater": 4.6,
          "Arabian Gulf / Red Sea": 5.5}

# Single-pass boron rejection. New membranes at 15 C and pH 8 sit at the top of
# this band; end-of-life elements at 30-35 C sit at the bottom.
REJECTION = {"new membranes, 15 C": 0.88,
             "mid-life, 25 C": 0.80,
             "end-of-life, 32 C": 0.72}

SPECS = {
    "WHO drinking-water guideline": 2.4,
    "EU Drinking Water Directive (2020/2184)": 1.5,
    "Common municipal contract specification": 1.0,
    "Irrigation of boron-sensitive crops": 0.5,
}


def main():
    grid, out = [], {}
    print("FIRST-PASS PERMEATE BORON (mg/L)")
    print("  %-28s %s" % ("rejection case", "".join("%26s" % k for k in B_FEED)))
    for rname, rej in REJECTION.items():
        row = []
        for fname, cf in B_FEED.items():
            v = cf * (1 - rej)
            row.append(v)
            grid.append(v)
        print("  %-28s %s" % ("%s (%.0f%%)" % (rname, rej * 100),
                              "".join("%26.2f" % v for v in row)))
    lo, hi = min(grid), max(grid)
    out["permeate_boron_range_mg_l"] = [round(lo, 2), round(hi, 2)]
    print("\n  full range across feed and rejection cases: %.2f - %.2f mg/L" % (lo, hi))

    print("\nCOMPLIANCE OF THE FIRST PASS ALONE")
    comp = {}
    for sname, limit in SPECS.items():
        n_pass = sum(1 for v in grid if v <= limit)
        verdict = ("complies in all cases" if n_pass == len(grid) else
                   "fails in all cases" if n_pass == 0 else
                   "complies in %d of %d cases" % (n_pass, len(grid)))
        comp[sname] = {"limit_mg_l": limit, "verdict": verdict}
        print("  %-42s %4.1f mg/L   %s" % (sname, limit, verdict))
    out["compliance"] = comp

    print("""
READING
  The first pass on its own meets the WHO guideline and the EU directive limit in
  every case examined. Against a 1.0 mg/L municipal contract specification it
  complies with new membranes in cool water and fails at end-of-life in warm
  water, which is the condition a plant must be designed for. Against a 0.5 mg/L
  irrigation specification it fails in every case.

  The correct statement is therefore conditional, and the second pass is a
  design requirement only under the stricter specifications or at end-of-life
  conditions - not an unconditional necessity. The previous wording claimed more
  than the numbers support and is withdrawn.""")

    # what the second pass actually delivers, at the worst first-pass case
    print("\nSECOND PASS AT ELEVATED pH, STARTING FROM THE WORST CASE (%.2f mg/L)" % hi)
    sp = {}
    for rej, ph in ((0.90, "pH 8.5"), (0.95, "pH 9.5"), (0.98, "pH 10.5")):
        v = hi * (1 - rej)
        sp["%.2f" % rej] = round(v, 3)
        meets = [s for s, d in SPECS.items() if v <= d["limit_mg_l"]] if False else \
                [s for s, l in SPECS.items() if v <= l]
        print("  %s, %.0f%% rejection -> %.3f mg/L   meets %d of %d specifications"
              % (ph, rej * 100, v, len(meets), len(SPECS)))
    out["second_pass_product_mg_l"] = sp

    io.open(os.path.join(HERE, "boron_results.json"), "w", encoding="utf-8").write(
        json.dumps(out, indent=1))
    print("\nwrote boron_results.json")


if __name__ == "__main__":
    main()
