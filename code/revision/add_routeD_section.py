# -*- coding: utf-8 -*-
"""Give the DWT manuscript a constructive conclusion.

The paper currently establishes that alkalinity is the binding constraint and
stops. Route D unbinds it: supplying the same base electrochemically closes the
calcium balance, makes reagent carbon net negative, and converts the reagent
bill into an electricity price with a computable crossover. That result belongs
in the paper, and it changes what the paper is for.

The finding that the purchased-alkali route fails is kept, because it is the
reason route D is needed and because the title says so. What changes is the
emphasis: route A's failure becomes the setup, and route D the answer.

Adds Section 4.12 and Figure 8, and rewrites the conclusion.

    python add_routeD_section.py
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


# load the reversal results alongside the others
if "RV = json.load" not in s:
    patch('ATTR = json.load(io.open(os.path.join(HERE, "attribution_results.json"),',
          'RV = json.load(io.open(os.path.join(HERE, "reversal_results.json"),\n'
          '                       encoding="utf-8"))\n'
          'ATTR = json.load(io.open(os.path.join(HERE, "attribution_results.json"),',
          "load reversal_results.json")

NEW = '''
# ------------------------------- 4.12 unbinding the constraint: route D
H("4.12  Unbinding the constraint: electrochemical alkalinity supply", 2)
P("Sections 4.10 and 4.11 establish that the alkalinity requirement, not the "
  "concentrator, is what makes this architecture uncompetitive. That is a "
  "statement about how base is supplied, not about the architecture as such. "
  "The stoichiometry is fixed \\u2014 two equivalents per mole of Mg(OH)2 "
  "however the base arrives \\u2014 but the supply route is a design choice, "
  "and Section 4.7 evaluated four of them. Route D, in which base is generated "
  "electrochemically on site and captured CO2 is dosed as the carbonate "
  "source, changes the binding constraint rather than relaxing it.", indent=True)
P("Three consequences follow, and they are of different kinds. Stoichiometrically, "
  "no lime is added, so no calcium is released and the closure ratio falls from "
  "%.2f to %.2f: the calcium balance closes exactly. In carbon terms the only "
  "reagent is captured CO2, which ends up bound in the carbonate product, so "
  "reagent carbon becomes %+.2f kg CO2 per cubic metre against %+.2f for the "
  "purchased-alkali route. Economically, the reagent bill of $%.2f m-3 is "
  "replaced by %.1f kWh m-3 of electrochemical demand, raising modelled total "
  "specific energy consumption from %.1f to %.1f kWh m-3."
  % (ROUTES_A["ca_closure_ratio"], ROUTES_D["ca_closure_ratio"],
     ROUTES_D["co2_reagents"], ROUTES_A["co2_reagents"],
     RV["reagent_A"], RV["extra_kwh_D"], RV["sec_base"], RV["sec_route_D"]),
  indent=True)
P("That substitution converts a commodity price into an energy price, and the "
  "two do not behave alike. Solving for the electricity price at which the two "
  "routes cost the same gives $%.3f kWh-1; below it, electrochemical supply is "
  "cheaper. Solving for the price at which route D reaches the conventional "
  "comparator gives $%.3f kWh-1 (Fig. 8A). The purchased-alkali route has no "
  "such crossing: at zero electricity cost it still sits at $%.2f m-3, $%.2f "
  "above the comparator, because the gap is reagents, capital and fixed "
  "operating cost net of the mineral credit rather than energy. No electricity "
  "price rescues route A; route D competes below a price that several "
  "desalination regions already contract."
  % (RV["route_crossover_usd_per_kwh"], RV["breakeven_D"],
     RV["capex"] + RV["reagent_A"] + RV["fixed_opex"] - RV["credit"],
     RV["capex"] + RV["reagent_A"] + RV["fixed_opex"] - RV["credit"]
     - RV["comparator"]), indent=True)
P("The conclusion does not rest on the mineral credit. Recomputing the "
  "crossing at reduced credit gives $%.4f kWh-1 at half the modelled value and "
  "$%.4f kWh-1 with no mineral revenue at all (Fig. 8B); the credit changes "
  "where the line sits, not whether it exists."
  % (RV_HALF, RV_ZERO), indent=True)
P("Two conditions bound the result, and both are stated rather than assumed. "
  "The electricity must be cheap, which is the crossing above; and it must "
  "also be clean, for a separate reason. Drawing %.1f kWh m-3 from a grid at "
  "0.55 kg CO2 kWh-1 yields %+.1f kg CO2 m-3, worse than the purchased-alkali "
  "route at %+.1f. On solar-dominated supply at 0.05 kg CO2 kWh-1 the same "
  "architecture is %+.2f kg m-3, close to neutral. Route D is therefore a "
  "proposition about dedicated low-carbon generation rather than about grid "
  "connection, and in a region with expensive or carbon-intensive power it is "
  "worse than conventional SWRO on both axes."
  % (RV["sec_route_D"], CO2_MIX, CO2_MIX_A, CO2_CLEAN), indent=True)
P("Finally, one cost is absent from all of the above. An electrochemical unit "
  "generating roughly 11 kg of base per cubic metre of permeate is an "
  "industrial installation with capital cost that this model has no basis to "
  "estimate, and the chlorine co-produced by a chlor-alkali route is neither "
  "costed as a liability nor credited as a product. The figures in this "
  "section are therefore an upper bound on route D's performance, and "
  "obtaining a vendor quotation is the first thing a serious evaluation of it "
  "would do.", indent=True)

'''
patch("# =============================================================== 5. DISCUSSION",
      NEW + "# =============================================================== 5. DISCUSSION",
      "section 4.12")

# helper bindings the new section needs
patch('ROUTES = V2["precipitation_routes"]' if 'ROUTES = V2["precipitation_routes"]' in s
      else 'RV = json.load(io.open(os.path.join(HERE, "reversal_results.json"),',
      'RV = json.load(io.open(os.path.join(HERE, "reversal_results.json"),',
      "noop")

if "ROUTES_A =" not in s:
    patch('ATTR = json.load(io.open(os.path.join(HERE, "attribution_results.json"),\n'
          '                         encoding="utf-8"))',
          'ATTR = json.load(io.open(os.path.join(HERE, "attribution_results.json"),\n'
          '                         encoding="utf-8"))\n'
          'ROUTES_A = V2["precipitation_routes"]["A: soda ash + lime (as written)"]\n'
          'ROUTES_D = V2["precipitation_routes"]["D: dosed CO2 + electrochemical base"]\n'
          '_CB = {c["grid"]: c for c in RV["carbon"]}\n'
          'CO2_MIX = _CB["Saudi grid mix, 0.55 kg CO2/kWh"]["co2_D"]\n'
          'CO2_MIX_A = _CB["Saudi grid mix, 0.55 kg CO2/kWh"]["co2_A"]\n'
          'CO2_CLEAN = _CB["solar-dominated, 0.05 kg CO2/kWh"]["co2_D"]\n'
          '_floor = lambda c: RV["capex"] + RV["reagent_D"] + RV["fixed_opex"] - c\n'
          'RV_HALF = (RV["comparator"] - _floor(RV["credit"] * 0.5)) / RV["sec_route_D"]\n'
          'RV_ZERO = (RV["comparator"] - _floor(0.0)) / RV["sec_route_D"]',
          "helper bindings")

io.open(SRC, "w", encoding="utf-8").write(s)
print("applied : %s" % ", ".join(a for a in applied if a != "noop"))
if [m for m in missed if m != "noop"]:
    print("MISSED  : %s" % ", ".join(m for m in missed if m != "noop"))
