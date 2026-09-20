# -*- coding: utf-8 -*-
"""Add the attribution analyses to the manuscript, and correct one false claim
they exposed.

  1  The text says no sampled combination beat the conventional comparator. The
     deposited Monte Carlo says 271 of 300,000 did. An absolute claim the
     deposited data contradicts is the worst kind to leave in, and the true
     statement is more useful anyway because it carries a best case.

  2  Section 4.10 attributes the reversal. The manuscript's emphasis implies the
     thermodynamic correction overturned the original result. It did not: after
     that correction alone the architecture still beat the comparator. The
     reagent accounting reversed it, by a factor of about seven. That is the
     paper's own title restated as a measurement.

  3  Section 4.11 ranks the parameters and maps where the architecture would be
     competitive, turning a negative result into a design target.

    python add_attribution_sections.py
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "build_full_manuscript.py")

s = io.open(SRC, encoding="utf-8").read()
applied, missed = [], []


def patch(old, new, tag):
    global s
    if old in s:
        s = s.replace(old, new, 1)
        applied.append(tag)
    else:
        missed.append(tag)


# ------------------------------------------- 0. load the new results file
if "ATTR = json.load" not in s:
    anchor = 'mc = V2["monte_carlo"]'
    patch(anchor,
          anchor + '\nATTR = json.load(io.open(os.path.join(HERE, "attribution_results.json"),\n'
                   '                         encoding="utf-8"))',
          "load attribution_results.json")

# ------------------------------------------- 1. correct the absolute claim
patch(
 '"precipitate the two products cost more than the products are worth, and no "\n'
 '  "sampled combination of prices, sellable fractions and capital assumptions "\n'
 '  "produced a net cost below the conventional comparator. No sampled configuration "\n'
 '  "is carbon negative. The comparator itself requires definition: the $0.76 m-3 "',
 '"precipitate the two products cost more than the products are worth. Of the "\n'
 '  "300,000 sampled combinations of prices, sellable fractions and capital "\n'
 '  "assumptions, %d (%.2f%%%%) produced a net cost below the conventional "\n'
 '  "comparator, the most favourable reaching $%.2f m-3. The architecture is "\n'
 '  "therefore not categorically more expensive; it is competitive only in a small "\n'
 '  "corner of the sampled space, which Section 4.11 locates. No sampled "\n'
 '  "configuration is carbon negative. The comparator itself requires definition: '
 'the $0.76 m-3 "',
 "correct the 'no sampled combination' claim")

patch('  % (mc["reagent_opex"]["median"], mc["mineral_credit"]["median"]), indent=True)',
      '  % (mc["reagent_opex"]["median"], mc["mineral_credit"]["median"],\n'
      '     ATTR["n_beating_comparator"], 100.0 * ATTR["frac_beating_comparator"],\n'
      '     ATTR["min_lcow"]), indent=True)',
      "supply the corrected numbers")

# ------------------------------------------- 2. the two new sections
NEW = '''
# ------------------------------------------ 4.10 attribution of the reversal
H("4.10  Which correction reverses the conclusion", 2)
P("The revision reverses the original's economic conclusion, but the original "
  "contained two independent errors and the analysis so far does not say which is "
  "responsible. Turning each correction on in sequence, with every other parameter "
  "at its median, separates them (Table 9, Figure 7A).", indent=True)
TBL(["Configuration", "SEC (kWh m-3)", "Net LCOW ($ m-3)", "Change ($ m-3)"],
    [[a["step"][0].upper() + a["step"][1:], "%.2f" % a["sec"], "%.2f" % a["lcow"],
      "-" if a["delta"] is None else "%+.2f" % a["delta"]]
     for a in ATTR["ablation"]],
    caption="Table 9. Ablation of the two corrections. Each row adds one "
            "correction to the row above, all other parameters held at their "
            "median. The conventional comparator is $0.76 m-3.")
P("The result is not what this paper's emphasis implies. Correcting the "
  "concentrator to the thermodynamic bound raises the modelled cost by $%.2f m-3 "
  "and leaves the architecture at $%.2f m-3, still below the $0.76 m-3 comparator. "
  "What reverses the conclusion is costing the precipitation reagents explicitly, "
  "worth $%.2f m-3, or %.1f times the thermodynamic correction. Consistency test 1 "
  "establishes that the original concentrator specification was thermodynamically "
  "inadmissible, which is a statement about physical possibility and stands on its "
  "own merits; but the economic reversal is carried almost entirely by consistency "
  "test 3. Alkalinity, not thermodynamics, is what makes this architecture "
  "uncompetitive, and the title of this paper should be read accordingly."
  % (ATTR["ablation"][1]["delta"], ATTR["ablation"][1]["lcow"],
     ATTR["ablation"][2]["delta"], ATTR["ablation_note"]["ratio"]), indent=True)

# ------------------------------ 4.11 parameter attribution and admissibility
H("4.11  Parameter attribution and the admissibility domain", 2)
P("Two questions follow: which sampled parameter governs the spread in net cost, "
  "and whether any region of the parameter space is competitive. Table 10 ranks "
  "the sampled parameters by Spearman rank correlation with net LCOW, together "
  "with the swing each commands between the lowest and highest deciles of its own "
  "range (Figure 7B). Rank correlation is used because the cost model is not "
  "linear in every input.", indent=True)
TBL(["Parameter", "Spearman rho", "Swing ($ m-3)"],
    [[r["parameter"], "%+.3f" % r["spearman"], "%.3f" % r["swing"]]
     for r in ATTR["attribution"][:8]],
    caption="Table 10. The eight parameters most strongly associated with net "
            "LCOW, of the thirteen sampled.")
P("Two of the three leading parameters, hydrated lime price and the sellable "
  "fraction of Mg(OH)2, belong to the alkalinity chain, which is the conclusion "
  "the ablation reaches by a different route. The concentrator second-law "
  "efficiency, the quantity this paper analyses most closely, ranks %d of %d with "
  "rho = %.3f. That is not a contradiction. The thermodynamic argument decides "
  "whether the original specification was admissible at all, a question no cost "
  "sensitivity can answer, while contributing little to the cost spread once a "
  "physically admissible range is imposed. Sensitivity and admissibility are "
  "different questions and are reported here separately."
  % (ATTR["attribution_note"]["eff2_rank"], len(ATTR["attribution"]),
     ATTR["attribution_note"]["eff2_spearman"]), indent=True)
P("Figure 7C maps the probability that net LCOW falls below the comparator over "
  "the plane of reagent cost and mineral value, both relative to the values "
  "modelled here. The modelled operating point lies deep in the inadmissible "
  "region. Reaching the comparator at present reagent prices requires the "
  "recovered minerals to be worth %.1f times the value assumed here; were the "
  "reagent requirement eliminated entirely, %.1f times would suffice. These are "
  "the two available levers, and their magnitudes are the specification any future "
  "version of this architecture would have to meet. Neither is reached by "
  "improving the concentrator."
  % (ATTR["admissibility"]["credit_needed_at_full_reagent_cost"],
     ATTR["admissibility"]["credit_needed_at_zero_reagent_cost"]), indent=True)

'''
patch("# =============================================================== 5. DISCUSSION",
      NEW + "# =============================================================== 5. DISCUSSION",
      "sections 4.10 and 4.11")

io.open(SRC, "w", encoding="utf-8").write(s)
print("applied: %s" % ", ".join(applied))
if missed:
    print("MISSED : %s" % ", ".join(missed))
