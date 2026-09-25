# -*- coding: utf-8 -*-
"""Add Section 4.13 (alkalinity and calcium as one design problem) to v3.

Works on the copyedited v3 document directly, so that the copyedit is kept;
every number is read from alkalinity_calcium_results.json or
reversal_results.json. Also:

  - corrects the Section 4.12 carbon figures for route D, which had counted
    the dosed CO2 twice (as a reagent credit and again as carbon fixed in the
    product): +20.3 -> +21.2 kg m-3 on the Saudi mix and +0.13 -> +1.07 on
    solar-dominated supply;
  - adds Discussion Section 5.4 (research agenda) and renumbers 5.4-5.5;
  - extends Limitations, Conclusions, Data availability, Nomenclature and
    the abstract; adds reference [26] for the sulfate content of seawater.

    python add_alkalinity_calcium_section.py
"""
import copy
import io
import json
import os
import re
import shutil

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsdecls

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "manuscript", "ILEDBV_Manuscript_Revised_v3.docx")
OUT = os.path.join(REPO, "manuscript", "ILEDBV_Manuscript_Revised_v4.docx")

AC = json.load(io.open(os.path.join(HERE, "alkalinity_calcium_results.json"), encoding="utf-8"))
RV = json.load(io.open(os.path.join(HERE, "reversal_results.json"), encoding="utf-8"))

B = AC["basis"]
OPT = AC["optimisation"]
BASE, SOLAR = OPT["model base case"], OPT["Gulf solar PPA"]
REQ = AC["required_intensity_to_reach_comparator"]
CEIL = AC["price_ceiling_usd_per_kwh"]
REV = AC["reversible_limit"]
UNIT = {r["p_e"]: r for r in AC["usd_per_kmol_OH"]}
BE = AC["breakeven_onsite_vs_lime"]
ARCH = {a["architecture"][:2]: a for a in AC["architectures"]}
SENS = {(s["naoh_usd_per_kg"], s["f_gyp"]): s["closure_cost"] for s in AC["closure_cost_sensitivity"]}
CB = {c["kg_per_kwh"]: c for c in RV["carbon"]}

# per-kmol carbon of the three base sources (kg CO2 per kmol OH-)
CO2_LIME = 56.08 / 2 * 1.20
CO2_NAOH = 39.997 * 1.90
CO2_ONSITE_MIX = 100.0 * 0.55 / 1.0 * 1.0      # 10 mol/kWh at 0.55 kg/kWh

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def para(text, kind="body"):
    ppr = {
        "body": '<w:spacing w:before="0" w:after="160"/><w:ind w:firstLine="317"/>',
        "head": '<w:spacing w:before="220" w:after="100"/>',
        "eq": '<w:spacing w:before="80" w:after="120"/><w:jc w:val="center"/>',
        "eqnote": '<w:spacing w:before="0" w:after="40"/>',
        "caption": '<w:spacing w:before="0" w:after="200"/>',
        "ref": '<w:spacing w:before="0" w:after="60"/>',
    }[kind]
    rpr = {
        "body": '<w:sz w:val="21"/>', "head": '<w:b/><w:sz w:val="23"/>',
        "eq": '<w:i/><w:sz w:val="21"/>', "eqnote": '<w:i/><w:sz w:val="18"/>',
        "caption": '<w:i/><w:sz w:val="18"/>', "ref": '<w:sz w:val="18"/>',
    }[kind]
    return parse_xml(
        '<w:p %s><w:pPr><w:pStyle w:val="Normal"/>%s<w:rPr/></w:pPr>'
        '<w:r><w:rPr>%s<w:lang w:val="en-US"/></w:rPr><w:t xml:space="preserve">%s</w:t></w:r></w:p>'
        % (nsdecls("w"), ppr, rpr, esc(text)))


def table(doc, headers, rows):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = doc.tables[0].style
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = 108000          # 8.5 pt in EMU
    for j, row in enumerate(rows, 1):
        for i, v in enumerate(row):
            c = t.rows[j].cells[i]
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.space_after = 12700
            p.add_run(str(v)).font.size = 108000
    el = t._tbl
    el.getparent().remove(el)
    return el


def text_of(el):
    return "".join(x.text or "" for x in el.iter(qn("w:t")))


def set_text(el, text):
    runs = el.findall(qn("w:r"))
    for r in runs[1:]:
        el.remove(r)
    ts = runs[0].findall(qn("w:t"))
    for t in ts[1:]:
        runs[0].remove(t)
    ts[0].text = text
    ts[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def find(body, start):
    for el in body.iterchildren():
        if el.tag == qn("w:p") and text_of(el).startswith(start):
            return el
    raise KeyError(start)


def insert_after(anchor, els):
    for el in els:
        anchor.addnext(el)
        anchor = el
    return anchor


def pct(x):
    return "%d%%" % round(100 * x)


def main():
    shutil.copy2(SRC, OUT)
    doc = Document(OUT)
    body = doc.element.body

    # ------------------------------------------------ 4.12 carbon correction
    p = find(body, "Two conditions bound the result")
    t = text_of(p)
    t2 = t.replace("yields +20.3 kg CO2 m-3", "yields %+.1f kg CO2 m-3" % CB[0.55]["co2_D"])
    t2 = t2.replace("the same pattern is +0.13 kg m-3, which is close to neutral.",
                    "the same pattern is %+.2f kg m-3, against %+.2f for the purchased-alkali "
                    "route on the same supply." % (CB[0.05]["co2_D"], CB[0.05]["co2_A"]))
    assert t2 != t and "+0.13" not in t2 and "20.3" not in t2, "4.12 carbon text not found"
    set_text(p, t2)

    # --------------------------------------------------- 4.13 new section
    anchor = find(body, "Finally, one cost is absent from all the above.")
    a1, a2, a5, a6 = ARCH["P1"], ARCH["P2"], ARCH["P5"], ARCH["P6"]
    a3, a4 = ARCH["P3"], ARCH["P4"]
    bu, bc, bn = BASE["unconstrained"], BASE["closed_dCa_le_0"], BASE["closed_without_gypsum"]
    sc = SOLAR["closed_dCa_le_0"]
    so4_mol = B["n_SO4_kmol"] * 1000
    mg_mol = B["n_Mg_kmol"] * 1000
    new = [
        para("4.13 Alkalinity and calcium as one design problem", "head"),
        para("Sections 4.7 and 4.12 evaluated alkalinity routes one at a time and reported "
             "the calcium balance of each as a consequence of the route. The two are coupled. "
             "Every mole of hydroxide supplied as Ca(OH)2 imports half a mole of calcium, and "
             "the cheapest base per mole is also the one that imports it. This section "
             "therefore treats base supply, carbonate supply and calcium removal as a single "
             "linear program per cubic meter of permeate, Eq. (14), and asks two questions: "
             "what it costs to close the calcium balance, and what an on-site base source "
             "would have to achieve for the closed loop to reach the conventional comparator."),
        para("min [C_alk + C_energy + C_disposal - C_products]  subject to  "
             "x_L + x_N + x_E - 2d >= 2 n_Mg;  s + d = n_Ca;  "
             "x_L/2 - n_Ca - g <= dCa_max;  g <= f_gyp n_SO4;  "
             "SEC <= SEC_target;  CO2 <= CO2_target          (14)", "eq"),
        para("      coupled alkalinity and calcium-closure program", "eqnote"),
        para("Hydroxide may be supplied as Ca(OH)2 (x_L), as purchased NaOH (x_N) or by "
             "on-site electrochemical generation (x_E); carbonate for the calcium step as "
             "Na2CO3 (s) or as dosed captured CO2 (d), which requires two further "
             "equivalents of base per mole. A third calcium sink is added that the original "
             "sequence did not use: after the hydroxide step, the calcium-rich stream is "
             "brought to gypsum saturation so that the imported calcium leaves as "
             "CaSO4.2H2O (g) instead of reporting to the crystallizer. Its capacity is fixed "
             "by the sulfate the feed brings, 2.712 g kg-1 at S = 35 [26], or %.1f mol per "
             "cubic meter of permeate; the fraction recoverable against the residual "
             "solubility of gypsum in concentrated NaCl brine is not modeled and is carried "
             "as f_gyp = %.2f, swept from 0.5 to 0.9. The disposal term is left at zero and "
             "the calcium balance is imposed as the constraint dCa <= 0 instead, so that its "
             "shadow price reports what closure costs. Soda ash and lime prices are the "
             "midpoints of the ranges in Table 7, and their embodied carbon is taken at the "
             "point values behind Table 3; captured CO2 is taken at "
             "$40 t-1, the basis of route D's reagent cost in Section 4.12; purchased NaOH "
             "is taken at $%.2f kg-1, swept from $0.30 to $0.70, with %.1f kg CO2 kg-1 "
             "embodied. The on-site source is characterized by a single number, its "
             "yield in moles of OH- per kWh, which places chlor-alkali, bipolar-membrane and "
             "other electrochemical routes on one axis regardless of chemistry. As in "
             "Section 4.12, the capital cost of the electrochemical unit and the value or "
             "liability of its acid or chlorine coproduct are excluded, so every on-site "
             "result below is a lower bound on cost."
             % (so4_mol, B["f_gyp"], B["prices_usd_per_kg"]["naoh"],
                B["embodied_kgCO2_per_kg"]["naoh"])),
        para("Per mole of base, the three sources order differently in money and in carbon "
             "(Fig. 9A). Lime costs $%.2f per kmol of OH- and carries %.1f kg CO2; purchased "
             "NaOH costs $%.2f and carries %.0f kg CO2; the on-site source at the chlor-alkali "
             "basis of Section 4.12, 10 mol kWh-1, costs $%.2f at $0.08 kWh-1 and $%.2f at "
             "$0.015 kWh-1. On-site base undercuts lime once its yield exceeds %.1f mol kWh-1 "
             "at $0.08 kWh-1, or %.1f mol kWh-1 at $0.05. Purchased NaOH removes the calcium "
             "import but never enters an optimum: across its whole price range it costs more "
             "per mole than lime and more than 10 mol kWh-1 on-site base at any electricity "
             "price below $0.12 kWh-1, "
             "and it carries the most embodied carbon of the three."
             % (UNIT[0.08]["lime_usd"], CO2_LIME, UNIT[0.08]["naoh_usd"], CO2_NAOH,
                UNIT[0.08]["onsite_usd"], UNIT[0.015]["onsite_usd"],
                BE["0.080"]["mol_OH_per_kWh"], BE["0.050"]["mol_OH_per_kWh"])),
    ]
    rows = []
    for key, label in (("P1", "Na2CO3 + Ca(OH)2, as written"),
                       ("P2", "Na2CO3 + purchased NaOH"),
                       ("P3", "Na2CO3 + on-site NaOH"),
                       ("P4", "Dosed CO2 + on-site NaOH (route D)"),
                       ("P5", "As written, then gypsum removal"),
                       ("P6", "Lime/NaOH blend + gypsum, dCa = 0")):
        a = ARCH[key]
        m, s_ = a["model base case"], a["Gulf solar PPA"]
        rows.append([label, ("%+.1f" % (m["dCa_kmol"] * 1000)).replace("+0.0", "0.0"), "%.2f" % m["ca_import_over_removal"],
                     "%.2f" % m["reagent_usd"], "%.1f" % m["extra_kwh"],
                     "%.2f / %.2f" % (m["lcow_net"], s_["lcow_net"]),
                     "%.1f / %.1f" % (m["co2_kg"], s_["co2_kg"])])
    new.append(table(doc, ["Architecture", "dCa (mol m-3)", "Ca imported / removed",
                           "Reagents ($ m-3)", "Extra kWh m-3", "Net LCOW ($ m-3), $0.08 / $0.015",
                           "CO2 (kg m-3), 0.55 / 0.05 grid"], rows))
    new.append(para("Table 11. Candidate architectures per cubic meter of permeate. dCa is calcium "
                    "imported minus calcium removed; negative values mean the train removes more "
                    "than it adds. On-site base at 10 mol OH- kWh-1; gypsum at f_gyp = %.2f. "
                    "Carbon counts CO2 fixed in the carbonate product once." % B["f_gyp"],
                    "caption"))
    new += [
        para("Table 11 separates what a change of sequence can do from what a change of base "
             "supply can do. Adding the gypsum step to the train as written roughly halves "
             "the imbalance, from %+.1f to %+.1f mol m-3, and the import-to-removal ratio "
             "from %.2f to %.2f, at no reagent cost; however, it cannot close the balance. "
             "Seawater carries %.0f mol of sulfate against %.0f mol of magnesium per cubic "
             "meter of permeate, so even complete gypsum recovery could absorb only %s of the "
             "calcium that lime imports. Closing the balance with purchased reagents alone, by "
             "blending in NaOH until dCa = 0, raises the net cost from $%.2f to $%.2f m-3 at "
             "the base case, which is worse than the train as written. Calcium closure is not "
             "available cheaply from reagents; it has to be bought with energy."
             % (a1["model base case"]["dCa_kmol"] * 1000, a5["model base case"]["dCa_kmol"] * 1000,
                a1["model base case"]["ca_import_over_removal"],
                a5["model base case"]["ca_import_over_removal"], so4_mol, mg_mol,
                pct(so4_mol / mg_mol), a1["model base case"]["lcow_net"],
                a6["model base case"]["lcow_net"])),
        para("Solving Eq. (14) gives the cost of closure directly (Table 12). At the model base "
             "case, $0.08 kWh-1 on the Saudi grid mix, the unconstrained optimum is not the "
             "route as written: dosed CO2 displaces soda ash as the carbonate source, because "
             "captured CO2 plus its two equivalents of lime costs less per mole than Na2CO3, "
             "and all the base comes from lime. That lowers the net cost to $%.2f m-3 but "
             "raises the calcium import to %+.0f mol m-3. Imposing dCa <= 0 moves %s of the "
             "base to the on-site source, uses the full gypsum sink (%.2f kg m-3), and raises "
             "the net cost to $%.2f m-3: closing the calcium balance costs $%.2f per cubic "
             "meter of permeate. Without the gypsum step the on-site share rises to %s and "
             "closure costs $%.2f. The closure cost falls from $%.2f to $%.2f as f_gyp rises "
             "from 0.5 to 0.9 and does not depend on the NaOH price, which never enters the "
             "solution. On Gulf solar power at $0.015 kWh-1 the optimum is route D itself, "
             "the calcium balance closes without being imposed, and closure costs nothing."
             % (bu["lcow_net"], bu["dCa_kmol"] * 1000, pct(bc["mix_OH_fraction"]["on_site"]),
                bc["gypsum_kg"], bc["lcow_net"], BASE["closure_cost_usd_per_m3"],
                pct(bn["mix_OH_fraction"]["on_site"]), BASE["closure_cost_without_gypsum"],
                SENS[(0.45, 0.5)], SENS[(0.45, 0.9)])),
    ]
    trows = []
    for label, s_ in (("$0.08, Saudi mix: unconstrained", bu),
                      ("$0.08, Saudi mix: dCa <= 0", bc),
                      ("$0.08, Saudi mix: dCa <= 0, no gypsum", bn),
                      ("$0.015, solar: dCa <= 0", sc)):
        mx = s_["mix_OH_fraction"]
        trows.append([label, "%s / %s / %s" % (pct(mx["lime"]), pct(mx["NaOH_purchased"]), pct(mx["on_site"])),
                      s_["carbonate"], "%.2f" % abs(s_["gypsum_kg"]), "%.1f" % s_["extra_kwh"],
                      "%.2f" % s_["lcow_net"], "%.1f" % s_["co2_kg"], ("%+.1f" % (s_["dCa_kmol"] * 1000)).replace("+0.0", "0.0").replace("-0.0", "0.0")])
    new.append(table(doc, ["Case", "Base: lime / NaOH / on-site", "Carbonate", "Gypsum (kg m-3)",
                           "Extra kWh m-3", "Net LCOW ($ m-3)", "CO2 (kg m-3)", "dCa (mol m-3)"], trows))
    new.append(para("Table 12. Optima of Eq. (14) at 10 mol OH- kWh-1. The difference between the "
                    "first two rows, $%.2f m-3, is the cost of closing the calcium balance at the "
                    "base case." % BASE["closure_cost_usd_per_m3"], "caption"))
    new += [
        para("The second question has a sharper answer (Fig. 9B). For the calcium-closed loop to "
             "reach the $0.76 m-3 comparator, the on-site source must deliver at least %.1f mol "
             "OH- per kWh at $0.015 kWh-1, %.1f at $0.03, %.1f at $0.048 and %.0f at $0.08. "
             "The last figure is not attainable by any electrochemical route. Splitting water "
             "into H+ and OH- across a bipolar junction requires at least (RT/F) ln 10 x dpH, "
             "%.3f V for a gradient from pH 0 to 14, which caps the yield at %.1f mol OH- "
             "kWh-1, or %.3f kWh per kg of NaOH equivalent; chlor-alkali electrolysis, which "
             "also evolves gas at both electrodes, sits well below that cap. Above $%.3f kWh-1, "
             "therefore, no base source however efficient closes the loop against the "
             "comparator: at that price the plant's other %.1f kWh m-3 already cost $%.2f "
             "m-3, leaving too little of the margin to pay even for reversibly generated base. At the chlor-alkali basis the ceiling is $%.4f kWh-1, which reproduces "
             "the route-D crossing of Section 4.12 by an independent calculation, and doubling "
             "the yield to 20 mol kWh-1 lifts it only to $%.4f."
             % (REQ["0.015"]["min_mol_OH_per_kWh"], REQ["0.030"]["min_mol_OH_per_kWh"],
                REQ["0.048"]["min_mol_OH_per_kWh"], REQ["0.080"]["min_mol_OH_per_kWh"],
                REV["E_V"], REV["max_mol_OH_per_kWh"], REV["min_kwh_per_kg_NaOH"],
                CEIL["reversible_limit"], RV["sec_base"], RV["sec_base"] * CEIL["reversible_limit"],
                CEIL["chlor_alkali_10_mol_per_kWh"], CEIL["20_mol_per_kWh"])),
        para("Carbon pulls the other way on a carbon-intensive grid. On-site base at 10 mol "
             "kWh-1 on the Saudi mix carries %.0f kg CO2 per kmol of OH-, against %.1f for "
             "lime, so the calcium-closed optimum at the base case emits %.1f kg CO2 m-3 "
             "against %.1f for the unconstrained one; minimizing carbon instead of cost under "
             "the same closure constraint selects the same mix. Calcium closure and a carbon "
             "target are compatible only where the electricity is itself low in carbon, which "
             "is the same condition that makes it cheap enough to close the cost gap. Taken "
             "together, the coupled problem gives the architecture question a quantitative "
             "answer: the loop closes, in calcium and in cost, only with calcium-free base "
             "generated at better than about %.0f mol OH- per kWh from electricity at or below "
             "the $0.048 kWh-1 industrial tariff, and at lower yields on cheaper "
             "power, with a gypsum sink absorbing whatever calcium the cheaper "
             "lime share still imports."
             % (CO2_ONSITE_MIX, CO2_LIME, bc["co2_kg"], bu["co2_kg"],
                REQ["0.048"]["min_mol_OH_per_kWh"])),
    ]
    insert_after(anchor, new)

    # ---------------------------------------------- 5.x renumber + new 5.4
    for old, new_ in (("5.5 Proposed validation", "5.6 Proposed validation"),
                      ("5.4 Limitations", "5.5 Limitations")):
        el = find(body, old)
        set_text(el, new_ + text_of(el)[len(old):])
    lim = find(body, "5.5 Limitations")
    disc = [
        para("5.4 Toward a closed valorization loop", "head"),
        para("Section 4.13 turns the negative result of Sections 4.7-4.12 into a design "
             "target, and the target defines the next stage of this work more precisely than "
             "the original question did. The question is no longer whether this architecture "
             "works but what an alkalinity pathway must achieve for desalination and brine "
             "valorization to close together, and it can be pursued computationally before "
             "any laboratory work, by adding candidate pathways to Eq. (14). A single "
             "reagent price is the wrong basis for comparing them. Each should be scored on "
             "three quantities at once, net cost per cubic meter of permeate, embodied and "
             "operational carbon per cubic meter, and moles of alkalinity delivered per kWh, "
             "together with the calcium it adds or removes; Fig. 9 and Table 11 report the "
             "existing routes on that basis."),
        para("Five directions follow from the analysis, and each carries a specific test. "
             "First, electrochemical base, including bipolar-membrane electrodialysis of the "
             "brine itself, avoids both purchased reagent and calcium import; the target is "
             "the yield and price combination of Fig. 9B, and the hard constraint is the "
             "acid stream it coproduces, which must have a sink. Neutralizing that acid "
             "with limestone would reimport exactly the calcium the route was chosen to "
             "avoid. Second, CO2-assisted pathways already win the carbonate step whenever "
             "captured CO2 is cheap and low in carbon, but they raise the base demand by two "
             "equivalents per mole of calcium, about %s at this composition. Third, alkaline "
             "industrial residues could replace purchased base, but most are calcium-bearing "
             "and would reproduce the lime problem unless they are magnesium-rich; their "
             "purity, leaching behavior and regulatory status would also have to be "
             "established. Fourth, alkalinity regeneration, in which base is recovered within "
             "the process rather than consumed once, is the most promising systems-level "
             "direction and the least developed; the most direct version would generate base "
             "electrochemically from the NaCl product stream, closing the loop internally. "
             "Fifth, the precipitation sequence should be optimized as a whole rather than "
             "stage by stage. The gypsum step of Section 4.13 is one instance: moving calcium "
             "removal after the hydroxide step changes what the calcium import costs, and the "
             "order of carbonate, magnesium, sulfate and calcium removal determines what each "
             "later step has available [10,25]."
             % pct(2 * B["n_Ca_removed_kmol"] / B["OH_required_kmol"])),
    ]
    insert_after(lim.getprevious(), disc)

    # cross-reference to the renumbered Limitations section
    for el in body.iterchildren():
        if el.tag == qn("w:p") and "Sections 3 and 5.4" in text_of(el):
            for tn in el.iter(qn("w:t")):
                if "5.4" in (tn.text or ""):
                    tn.text = tn.text.replace("Sections 3 and 5.4", "Sections 3 and 5.5").replace("5.4", "5.5")

    # ------------------------------------------------------- limitations
    p = find(body, "The osmotic coefficient correction in Eq. (5)")
    set_text(p, text_of(p) + (
        " The coupled program of Section 4.13 is linear and deliberately coarse: it "
        "does not represent precipitation kinetics, coprecipitation between steps or the "
        "residual solubility of gypsum in concentrated brine, which is carried as the swept "
        "fraction f_gyp; it excludes the capital cost of any electrochemical unit and the "
        "disposition of its acid or chlorine coproduct; and the reversible limit it uses "
        "is a thermodynamic bound, not an achievable operating point."))

    # --------------------------------------------------------- conclusions
    p = find(body, "One route unbinds that constraint")
    concl = para(
        "Treated as one design problem, alkalinity supply and calcium closure give the "
        "architecture question a quantitative answer. Closing the calcium balance costs "
        "$%.2f per cubic meter at the base case even with gypsum as a calcium sink, and "
        "$%.2f without it, and it cannot be bought cheaply with purchased reagents. With "
        "on-site base, the closed loop reaches the comparator only if the base is generated "
        "at better than about %.0f mol OH- per kWh from electricity at or below the "
        "$0.048 kWh-1 industrial tariff, and above $%.3f kWh-1 it cannot reach it at all, because the "
        "reversible limit of water dissociation, %.0f mol OH- per kWh, binds first. The next "
        "stage of this work is therefore to score candidate alkalinity pathways on cost, "
        "carbon, yield per kWh and calcium together, as Section 5.4 sets out."
        % (BASE["closure_cost_usd_per_m3"], BASE["closure_cost_without_gypsum"],
           REQ["0.048"]["min_mol_OH_per_kWh"], CEIL["reversible_limit"],
           REV["max_mol_OH_per_kWh"]), "body")
    p.addnext(concl)

    # ------------------------------------------------------------ abstract
    p = find(body, "Integrated seawater reverse osmosis (SWRO) with brine valorization")
    old = "That conclusion is conditional on low-carbon supply and excludes uncosted electrochemical capital."
    t = text_of(p)
    assert old in t
    set_text(p, t.replace(old, (
        "That conclusion is conditional on low-carbon supply and excludes electrochemical "
        "capital. Treated as a single optimization, closing the calcium balance costs $%.2f "
        "m-3 at the base case even with a gypsum sink, and above $%.3f kWh-1 no on-site base "
        "can close the loop, because the reversible limit of water dissociation binds."
        % (BASE["closure_cost_usd_per_m3"], CEIL["reversible_limit"]))))

    # ---------------------------------------------------- data availability
    p = find(body, "The model implementation, the parameter set")
    t = text_of(p)
    t = t.replace("release tag v2.0.1", "release tag v2.1.0")
    t = t.replace("Running iledbv_revision_v2.py, design_and_costing.py and boron_recalc.py",
                  "Running iledbv_revision_v2.py, design_and_costing.py, boron_recalc.py, "
                  "reversal_analysis.py and alkalinity_calcium_design.py")
    assert "alkalinity_calcium_design.py" in t and "v2.1.0" in t
    set_text(p, t)

    # --------------------------------------------------------- nomenclature
    nom = doc.tables[-1]
    for sym, dfn, un in (("x_L, x_N, x_E", "OH- supplied as Ca(OH)2, purchased NaOH, on-site base", "kmol m-3"),
                         ("s, d", "carbonate supplied as Na2CO3, as dosed CO2", "kmol m-3"),
                         ("g", "calcium removed as gypsum", "kmol m-3"),
                         ("f_gyp", "fraction of feed sulfate recoverable as gypsum", "-"),
                         ("dCa", "calcium imported minus calcium removed", "kmol m-3")):
        cells = nom.add_row().cells
        for c, v in zip(cells, (sym, dfn, un)):
            c.text = v
            for r in c.paragraphs[0].runs:
                r.font.size = 108000

    # ------------------------------------------------------------ reference
    last = find(body, "[25] D. Zhang")
    last.addnext(para(
        "[26] F.J. Millero, R. Feistel, D.G. Wright, T.J. McDougall, The composition of "
        "Standard Seawater and the definition of the Reference-Composition Salinity Scale, "
        "Deep Sea Research Part I: Oceanographic Research Papers 55 (2008) 50-72. "
        "https://doi.org/10.1016/j.dsr.2007.10.001", "ref"))

    doc.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
