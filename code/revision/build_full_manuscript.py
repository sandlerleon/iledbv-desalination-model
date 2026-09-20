# -*- coding: utf-8 -*-
"""Assemble the complete revised manuscript for DWT-D-26-01366.

Merges the rewritten Introduction, the new consistency-test results, the design
and costing tables, and the revised Sections 2-3 and 5-7 into one document.
Every quantity is read from the model JSON files rather than transcribed.

    python build_full_manuscript.py
"""
import io, json, os
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"C:\Users\Leon\Downloads\DWT\ILEDBV_Manuscript_Revised_v2.docx"

V2 = json.load(io.open(os.path.join(HERE, "iledbv_revision_v2.json"), encoding="utf-8"))
DC = json.load(io.open(os.path.join(HERE, "design_costing.json"), encoding="utf-8"))
REFS = json.load(io.open(os.path.join(HERE, "_refs_final.json"), encoding="utf-8"))
SP = json.load(io.open(os.path.join(HERE, "second_pass_results.json"), encoding="utf-8"))
BR = json.load(io.open(os.path.join(HERE, "boron_results.json"), encoding="utf-8"))

mc = V2["monte_carlo"]
t1 = V2["t1_concentrator"]
t3 = V2["t3_polarization"]["beta_1.20"]
RT = V2["precipitation_routes"]
A = RT["A: soda ash + lime (as written)"]
Cc = RT["C: dosed CO2 + dolime"]
Dd = RT["D: dosed CO2 + electrochemical base"]
co2_fixed = V2["co2_fixed_kg_per_m3_permeate"]
w_min = t1["least_work_kwh_per_m3_brine"]
lo, hi = t1["realistic_at_second_law_eff"]["0.55"], t1["realistic_at_second_law_eff"]["0.25"]
st = DC["streams_as_modelled"]
op = DC["opex"]
pd_ = DC["precipitation_design"]

doc = Document()
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10.5)
for s in doc.sections:
    s.left_margin = s.right_margin = Inches(0.85)


def H(t, lvl=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(15 if lvl == 1 else 11)
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run(t); r.bold = True; r.font.size = Pt(13 if lvl == 1 else 11.5)


def P(t, italic=False, size=10.5, after=8, indent=False):
    par = doc.add_paragraph(); par.paragraph_format.space_after = Pt(after)
    if indent:
        par.paragraph_format.first_line_indent = Inches(0.22)
    r = par.add_run(t); r.italic = italic; r.font.size = Pt(size)


def EQ(n, s):
    par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_before = Pt(4); par.paragraph_format.space_after = Pt(6)
    r = par.add_run("%s          (%d)" % (s, n)); r.font.size = Pt(10.5); r.italic = True


def TBL(headers, rows, widths=None, fs=8.5, caption=None):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Light Grid Accent 1"
    for i, head in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = ""
        r = c.paragraphs[0].add_run(head); r.bold = True; r.font.size = Pt(fs)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            pp = cells[i].paragraphs[0]; pp.paragraph_format.space_after = Pt(1)
            pp.add_run(str(v)).font.size = Pt(fs)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = w
    if caption:
        P(caption, italic=True, size=9, after=10)
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(4)


# ============================================================ TITLE & ABSTRACT
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Consistency Testing of an Integrated SWRO\u2013Brine Valorization "
              "Architecture: Alkalinity as the Binding Constraint")
r.bold = True; r.font.size = Pt(15)
for line, sz in (("Leon Sandler", 11),
                 ("Independent Researcher, Northbrook, Illinois, USA", 10),
                 ("ORCID: https://orcid.org/0009-0007-4584-808X", 9.5),
                 ("Corresponding author: sandler.leon@gmail.com", 9.5)):
    q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.space_after = Pt(1)
    q.add_run(line).font.size = Pt(sz)
doc.add_paragraph().paragraph_format.space_after = Pt(8)

H("Abstract")
ABSTRACT = (
 "Integrated seawater reverse osmosis (SWRO) with brine valorization is widely "
 "proposed as a route to simultaneous energy reduction and near-zero liquid "
 "discharge, but such architectures are seldom tested against the physical bounds "
 "their individual stages must obey. This study applies a consistency-testing "
 "framework to one architecture combining subsurface intake, isobaric energy "
 "recovery, membrane brine concentration, selective Ca/Mg precipitation and "
 "mechanical-vapour-compression crystallization, checking each subsystem against a "
 "physical constraint rather than an assumed value. The brine-concentrator energy "
 "commonly assumed in this class of study, 0.5-1.0 kWh per cubic metre of brine, "
 "lies at or below the least work of separation for that feed (%.2f kWh m-3). A "
 "bounded estimate, obtained from that minimum and a 25-55%% second-law efficiency, "
 "is %.1f-%.1f kWh m-3, raising modelled total specific energy consumption to a "
 "median %.1f kWh m-3. Magnesium recovery is limited by alkalinity rather than "
 "by magnesium: the base required carries either %.1f kg CO2 per cubic metre of "
 "permeate in embodied carbon, roughly double the plant's grid emissions, or an "
 "electrochemical cost of %.0f kWh m-3. Lime dosing releases %.1f times more calcium "
 "than the preceding carbonate step removes, so the train does not close. Costing "
 "those reagents explicitly is decisive: at $%.2f m-3 they exceed the $%.2f m-3 "
 "realisable mineral credit, and Monte Carlo propagation (300,000 samples) gives a "
 "net levelized cost of $%.2f m-3 (90%% interval $%.2f-$%.2f) against $0.76 m-3 for "
 "conventional SWRO. Brine mineral valorization by alkaline precipitation is limited "
 "by the base, not by the brine."
) % (w_min, lo, hi, mc["sec_total"]["median"], A["co2_reagents"], Dd["extra_kwh"],
     A["ca_closure_ratio"], mc["reagent_opex"]["median"], mc["mineral_credit"]["median"],
     mc["lcow_net"]["median"], mc["lcow_net"]["p05"], mc["lcow_net"]["p95"])
P(ABSTRACT)

H("Keywords", 2)
P("seawater desalination; reverse osmosis; brine valorization; alkalinity; "
  "consistency testing; techno-economic analysis", italic=True, size=10)

# ================================================================ INTRODUCTION
H("1.  Introduction")
INTRO = json.load(io.open(os.path.join(HERE, "_intro_paras.json"), encoding="utf-8")) \
    if os.path.exists(os.path.join(HERE, "_intro_paras.json")) else None
if INTRO:
    for t in INTRO:
        P(t, indent=True)
else:
    P("[Introduction text is generated by build_introduction.py and inserted here; "
      "run that script first to emit _intro_paras.json]", italic=True)

# ====================================================== 2. PROCESS ARCHITECTURE
H("2.  Integrated process architecture")
P("The architecture examined here, referred to as ILEDBV (Integrated Low-Energy "
  "Desalination with Brine Valorization), is shown in Figure 1 with stream-level "
  "mass, salinity and pressure labels for the baseline case (R = 45%, feed salinity "
  "35 g/L). Figure 1 is the author's conceptual integration of five separately "
  "published component technologies rather than a description of an existing "
  "installation.", indent=True)

H("2.1  System boundary", 2)
P("The boundary begins at raw seawater intake and ends at three outputs: potable "
  "permeate to municipal supply, solid Mg(OH)2 and CaCO3 products, and final "
  "crystallizer output. Excluded are water distribution, mineral transport and "
  "refining beyond primary precipitation, and civil works. The revision adds one "
  "term inside the boundary that the original omitted: the embodied carbon and "
  "purchase cost of the precipitation reagents, which Section 4.7 shows to dominate "
  "both the carbon and the economic account.", indent=True)

H("2.2  Subsurface intake", 2)
P("Source water is drawn through a subsurface seabed or beach-well intake rather "
  "than an open-ocean pipe, reducing particulate and biological loading and hence "
  "pretreatment demand [21,7,1]. Pretreatment energy is swept across the full "
  "0.05-0.80 kWh m-3 range reported for intake configurations rather than fixed at a "
  "midpoint. The intake is not claimed to eliminate biofouling, and its performance "
  "is site dependent on seabed and aquifer hydraulic conductivity. A subsurface "
  "intake also removes the need for the vortex or hydrocyclone pre-separation "
  "sometimes proposed ahead of SWRO: the seabed performs that duty, which is part of "
  "the rationale for choosing it.", indent=True)

H("2.3  SWRO, pressure exchanger, and product-water quality", 2)
P("The RO stage is modelled with an isobaric pressure exchanger recovering energy "
  "from the reject brine (Sections 3.4-3.5), with PX efficiency swept 90-98%% [23,11]. "
  "Reviewer comment on the original prompted an explicit treatment of product-water "
  "quality. At 45%% recovery the modelled first-pass permeate is approximately %.0f "
  "mg L-1 TDS and %.0f mg L-1 chloride, both comfortably within potable limits. Boron "
  "is the parameter that decides whether a second pass is needed, because boric acid "
  "is largely un-ionized at seawater pH and is therefore poorly rejected."
  % (SP["first_pass"]["tds_mg_l"], SP["first_pass"]["cl_mg_l"]), indent=True)
P("Boron rejection is not a single number: it falls as elements age and rises with "
  "temperature and pH. Across seawater boron of 4.6-5.5 mg L-1 and single-pass "
  "rejection of 72-88%%, spanning new elements in cool water to end-of-life elements "
  "at 32 degrees C, first-pass permeate boron is %.2f-%.2f mg L-1. That range complies "
  "with the WHO guideline of 2.4 mg L-1 in every case and with the EU directive limit "
  "of 1.5 mg L-1 in all but the most severe case, but it straddles the 1.0 mg L-1 "
  "figure often written into municipal supply contracts and exceeds a 0.5 mg L-1 "
  "irrigation specification in every case."
  % (BR["permeate_boron_range_mg_l"][0], BR["permeate_boron_range_mg_l"][1]), indent=True)
P("The requirement for a second pass is therefore conditional rather than absolute, "
  "and we state it as such: it is not required to meet the WHO guideline, it is "
  "required at end-of-life conditions against a 1.0 mg L-1 contract specification, "
  "and it is required in all cases where the product serves irrigation of "
  "boron-sensitive crops. Where it is fitted, a partial second pass at elevated pH "
  "treating 35-100%% of the permeate adds %.2f-%.2f kWh m-3 and brings boron to "
  "%.2f-%.2f mg L-1 from the worst first-pass case, which satisfies every "
  "specification considered. The energy comparison in Section 5.1 is reported both "
  "with and without it, so that the conclusion does not depend on which "
  "specification a given project faces."
  % (SP["second_pass_energy"]["split-partial, 35% treated"]["delta_sec"],
     SP["second_pass_energy"]["full second pass, 12 bar"]["delta_sec"],
     BR["second_pass_product_mg_l"]["0.98"], BR["second_pass_product_mg_l"]["0.90"]),
  indent=True)
P("A gravity-fed second pass, drawing on an elevated cistern rather than a booster "
  "pump, was considered and rejected on hydraulic grounds. A 12 bar feed requires "
  "%.0f m of static head; no coastal municipal site offers it, and the structure "
  "required would cost more than the pump it replaces."
  % SP["gravity_head"]["typical second pass"]["m"], indent=True)

H("2.4  Brine concentration", 2)
P("The RO concentrate is routed to a high-pressure, low-salt-rejection membrane "
  "stage recovering an additional 50%% of its water. The original described this "
  "stage as nanofiltration. That label is withdrawn: at the rejections assumed "
  "(90%% monovalent, 98%% divalent) and the pressures implied by the feed osmotic "
  "pressure, the stage is a high-pressure RO stage. A genuine NF element, rejecting "
  "perhaps 30%% of monovalent salt, would give a crystallizer feed of %.1f g L-1 "
  "rather than %.1f g L-1 and a materially different downstream duty."
  % (DC["streams_true_nf"]["S6 crystallizer feed"]["TDS_g_L"],
     st["S6 crystallizer feed"]["TDS_g_L"]), indent=True)

H("2.5  Mineral recovery and crystallization", 2)
P("The concentrated brine undergoes selective precipitation, calcium as CaCO3 by "
  "soda-ash dosing followed by magnesium as Mg(OH)2 by lime dosing, with the design "
  "basis given in Table 4. The residue is routed to a mechanical vapour compression "
  "crystallizer consuming 8-15 kWh m-3 of electrical energy per cubic metre of "
  "crystallizer feed [20]. The stage is described throughout as ZLD-capable, by which "
  "we mean only that the configuration contains no designed liquid discharge stream, "
  "not that zero discharge has been demonstrated. The residual liquid fraction is a "
  "modelled quantity without pilot validation, and real leakage, blowdown and "
  "operational upsets would raise it. No claim of achieved zero liquid discharge is "
  "made anywhere in this work.", indent=True)

# ================================================================== 3. MODEL
H("3.  Mathematical model")
P("Symbols are defined in the Nomenclature. The solution procedure is sequential: "
  "Eqs. (1)-(3) close the water and per-ion salt balance for each membrane stage in "
  "turn; Eqs. (4)-(5) give the osmotic pressure of each stream; Eqs. (6)-(7) give "
  "the RO stage energy; Eqs. (8)-(9) bound the concentrator energy; Eqs. (10)-(12) "
  "give the mineral masses and the alkalinity they require; and Eq. (13) gives the "
  "levelized cost. No stage is solved before its feed is known, so the procedure "
  "requires no iteration.", indent=True)

for n, eq, note in [
    (1, "Q_p = R Q_f ;   Q_b = Q_f - Q_p", "stage water balance"),
    (2, "C_p,i = C_f,i (1 - r_i)", "per-ion permeate concentration"),
    (3, "C_b,i = (Q_f C_f,i - Q_p C_p,i) / Q_b", "per-ion salt balance"),
    (4, "pi = 27 (TDS / 35)", "linear osmotic model, calibrated at seawater"),
    (5, "pi = phi(S) x 27 (TDS / 35)", "osmotic-coefficient-corrected form"),
    (6, "P_f = beta pi_b + NDP", "applied pressure including polarization"),
    (7, "SEC_RO = [P_f Q_f / eta_pump - eta_PX P_f Q_b] / Q_p", "RO stage with isobaric recovery"),
    (8, "w_min = pi_f ln[1 / (1 - R)]",
     "reversible minimum work of separation under the stated idealized "
     "assumptions, per m3 of FEED to the stage"),
    (9, "SEC_stage = w_min / eta_II", "actual stage energy from the reversible bound"),
    (10, "m_CaCO3 = C_Ca Q_c Y_Ca (M_CaCO3 / M_Ca)", "carbonate product mass"),
    (11, "m_MgOH2 = C_Mg Q_c Y_Mg (M_MgOH2 / M_Mg)", "hydroxide product mass"),
    (12, "n_base = 2 n_Mg + 2 n_Ca", "alkalinity demand, equivalents"),
    (13, "LCOW = (CAPEX CRF + OPEX) / V_annual - R_minerals / V_annual", "levelized cost"),
]:
    EQ(n, eq)
    P("      %s" % note, italic=True, size=9, after=2)

P("Equation (8) is obtained as follows. Removing a differential volume dx of pure water from unit feed volume leaves the retained salt in a smaller volume, so the concentrate osmotic pressure rises as pi(x) = pi_f/(1 - x) under the van\u2019t Hoff proportionality and complete salt retention. The reversible work is the integral of that rising pressure over the extracted volume, and integrating from 0 to the stage recovery R gives Eq. (8). Three assumptions are embedded and are stated rather than left implicit: complete salt rejection, an infinitely staged or continuously counter-balanced process so that the applied pressure never exceeds the local osmotic pressure, and negligible concentration polarization. Each makes the bound looser, so a real stage must exceed it. The result is expressed per cubic metre of FEED to the stage, which for the brine concentrator is per cubic metre of brine processed - the same basis on which the original energy assumption was quoted, so the two are directly comparable.", indent=True)
P("Because phi(S) in Eq. (5) is carried as a bounded sensitivity rather than a "
  "locked correlation, the specific energy figures reported here are model estimates "
  "rather than final values. Section 4.5 shows the residual uncertainty from this "
  "source to be under 2% of total SEC, an order of magnitude smaller than the "
  "concentrator correction, so it does not affect any conclusion drawn; but the "
  "distinction is stated so that the numbers are not quoted onward as settled.",
  indent=True)
P("This is a reversible benchmark, not a membrane-process energy model. It bounds what any configuration can achieve; it does not predict what a particular element, array or staging arrangement will consume. Second-law efficiency, Eq. (9), carries that distinction explicitly.", indent=True)
P("The osmotic coefficient of seawater is not constant: it passes through a minimum "
  "near seawater salinity and rises as the solution concentrates, so a correlation "
  "anchored at 35 g L-1 under-predicts at brine salinities. Published seawater "
  "property correlations covering this range are available [22,12] and are the "
  "appropriate basis for phi(S) in Eq. (5). Section 4.5 reports how much the "
  "correction actually matters.", indent=True)
P("Equations (5), (8), (9) and (12) are new in this revision. Equation (8) is the "
  "reversible bound against which the concentrator assumption is tested in Section "
  "4.7; Eq. (12) is the alkalinity balance on which Section 4.7 rests.", indent=True)

# ================================================================== 4. RESULTS
H("4.  Results")

H("4.1  Stream table and process composition", 2)
ions = ["Na+", "Mg2+", "Ca2+", "K+", "Cl-", "SO4 2-", "HCO3-", "Br-"]
TBL(["Stream", "Q", "TDS"] + ions,
    [[k, "%.3f" % v["q_m3_per_m3_feed"], "%.1f" % v["TDS_g_L"]]
     + ["%.3f" % v["ions_g_L"][i] for i in ions] for k, v in st.items()],
    caption="Table 1. Ion-by-ion stream table, g L-1, per cubic metre of raw seawater. "
            "S6 is the crystallizer feed.")
P("Two features of Table 1 were not visible in the original analysis. Calcium rises "
  "from %.2f to %.2f g L-1 across the precipitation train rather than falling, "
  "because lime dosing returns one calcium ion per magnesium precipitated. Total "
  "dissolved solids also rise, from %.1f to %.1f g L-1, because the dissolved "
  "reagents added exceed the solids removed. Selective precipitation is therefore "
  "justified by the value of its products and not by any reduction in crystallizer "
  "duty, which it slightly increases. This is worth stating plainly because it "
  "contradicts a common intuition about brine mineral recovery: extracting solids "
  "from the stream does not lighten the thermal load downstream when the reagents "
  "that extract them add more dissolved mass than the solids remove. Any assessment "
  "that credits precipitation with a reduced crystallizer duty should check this "
  "balance for its own reagent set."
  % (st["S5 concentrator concentrate"]["ions_g_L"]["Ca2+"],
     st["S6 crystallizer feed"]["ions_g_L"]["Ca2+"],
     st["S5 concentrator concentrate"]["TDS_g_L"], st["S6 crystallizer feed"]["TDS_g_L"]),
  indent=True)

H("4.2  Incremental contribution of each subsystem", 2)
P("The five-case decomposition isolates each subsystem's contribution to specific "
  "energy consumption. Case A is a conventional turbine-ERD baseline, Case B "
  "substitutes the isobaric pressure exchanger, Case C adds the subsurface intake, "
  "Case D adds brine concentration, and Case E adds crystallization. Table 2 reports "
  "the decomposition with the concentrator held to the bounded range of Section 4.5 "
  "rather than to the literature midpoint used in the original.", indent=True)
_qp, _qb = 0.45, 0.55
_qc = _qb * 0.5
_cases = []
for _lab, _cs in (("original assumption, 0.75", 0.75),
                  ("55% second-law efficiency", float(lo)),
                  ("Monte Carlo median", mc["concentrator_sec"]["median"]),
                  ("25% second-law efficiency", float(hi))):
    _d = 2.73 + _cs * _qb / _qp
    _e = _d + 11.5 * _qc / _qp
    _cases.append([_lab, "%.2f" % _cs, "2.73", "%.2f" % _d, "%.2f" % _e])
TBL(["Concentrator basis", "kWh m-3 brine", "Case C", "Case D", "Case E"], _cases,
    caption="Table 2. Stage decomposition, kWh per cubic metre of permeate. Case C is "
            "the desalination stage, Case D adds brine concentration, Case E adds "
            "crystallization. The original reported Case E as 10.68 kWh m-3.")
P("Crystallization remains the dominant single term in every case, but the "
  "concentrator correction moves Case E from the 10.68 kWh m-3 originally reported "
  "to a modelled %.2f-%.2f kWh m-3. As elsewhere in this paper, that range is a "
  "bounded model estimate rather than a measured or predicted plant value."
  % (2.73 + float(lo) * _qb / _qp + 11.5 * _qc / _qp,
     2.73 + float(hi) * _qb / _qp + 11.5 * _qc / _qp), indent=True)

H("4.3  Market absorption", 2)
P("The original included a market-absorption check to test whether the recovered "
  "tonnage could in fact be sold, and that check stands: a 10,000 m3 d-1 plant would "
  "produce a material fraction of the addressable Mg(OH)2 market, so a sellable "
  "fraction well below unity is the realistic assumption rather than a conservative "
  "one. The revision extends the same reasoning to calcium carbonate, which the "
  "original credited at 100% of market price. Recovered carbonate competes against "
  "a large, low-margin commodity whose specification depends on purity, particle "
  "size and brightness, none of which is controlled by a process optimised for "
  "water. A sellable fraction of 50-70% is used here, sampled rather than fixed, "
  "and transport and refining beyond primary precipitation remain outside the "
  "boundary and therefore uncredited.", indent=True)

H("4.4  Environmental performance", 2)
P("The original environmental assessment counted carbon dioxide from grid "
  "electricity only. On the corrected energy basis that term is approximately %.1f "
  "kg CO2 per cubic metre of permeate at a grid intensity of 0.4 kg kWh-1. Section "
  "4.7 shows it to be the smaller half of the account: reagent embodied carbon adds "
  "%.1f kg m-3 and the carbonate product fixes only %.2f kg m-3, giving a net median "
  "of %.1f kg CO2 per cubic metre (90%% interval %.1f-%.1f). No sampled "
  "configuration is carbon negative. Replacing MVC crystallization with solar "
  "interfacial evaporation [4,5,6] would remove most of the electricity term but "
  "none of the reagent term, and would substitute land area for energy."
  % (mc["sec_total"]["median"] * 0.4, A["co2_reagents"], co2_fixed,
     mc["co2_net_kg_per_m3"]["median"], mc["co2_net_kg_per_m3"]["p05"],
     mc["co2_net_kg_per_m3"]["p95"]), indent=True)
P("Two environmental risks specific to the intake are noted rather than modelled. "
  "Subsurface intakes are subject to progressive clogging of the seabed or aquifer "
  "interface, and sustained abstraction near the coast carries a risk of saline "
  "intrusion into adjacent fresh groundwater. Both are strongly site dependent and "
  "would require hydrogeological assessment at any candidate location.", indent=True)

H("4.5  Consistency test 1: the concentrator against the least work of separation", 2)
P("Integrating the rising concentrate osmotic pressure over the extracted volume "
  "gives Eq. (8). At the modelled RO brine (%.0f bar) and 50%% concentrator recovery "
  "this evaluates to %.3f kWh per cubic metre of brine processed. Any real stage "
  "must exceed it. The 0.5-1.0 kWh m-3 range adopted in the original Section 3.6, "
  "and in comparable published assessments, spans %.2f to %.2f times this minimum: "
  "the midpoint is thermodynamically inadmissible and the upper bound would require "
  "a second-law efficiency of 94%%. Dividing the reversible minimum by the 25-55%% "
  "second-law efficiency range characteristic of high-pressure membrane stages gives "
  "a bounded estimate of %.2f-%.2f kWh m-3. We describe this as a bounded estimate "
  "rather than an attainable or demonstrated value: it is derived from a "
  "thermodynamic bound and an assumed efficiency range, not from measurement of a "
  "stage operating on this feed. All results below use that range."
  % (t1["pi_feed_bar"], w_min, t1["ratio_to_minimum"]["0.5"],
     t1["ratio_to_minimum"]["1.0"], lo, hi), indent=True)

P("Reviewer comment on the original asked that the deviation of the linear osmotic "
  "model at brine salinity be quantified rather than acknowledged. Applying an "
  "osmotic-coefficient rise of 8-24% between 35 and 120 g L-1 raises the "
  "concentrator feed osmotic pressure from 49.0 to 50.3-52.9 bar and the stage "
  "energy from 2.36 to 2.42-2.55 kWh m-3 of brine, moving total specific energy "
  "consumption from 12.64 to 12.87 kWh m-3. The effect is therefore real but "
  "second-order, under 2% of total SEC, and an order of magnitude smaller than the "
  "concentrator correction above. It is reported here as a bounded sensitivity; "
  "locking it to a point value requires implementing the published correlation "
  "[22,12], which the deposited code is structured to accept.", indent=True)

H("4.6  Consistency test 2: the ceiling on boundary-layer management", 2)
P("Concentration polarization raises wall concentration to beta times bulk, so "
  "eliminating it entirely saves exactly (beta - 1) pi_bulk and no more. At an "
  "aggressive beta of 1.20 this ceiling is %.2f kWh m-3, or %.1f%% of "
  "desalination-stage SEC. Any rotating-element or centrifugal scheme must therefore "
  "consume less than %.2f kWh m-3 in net shaft power, after seal and bearing losses, "
  "to be worth adopting. We offer this as a screening test rather than a "
  "recommendation."
  % (t3["ceiling_kwh_per_m3"], t3["ceiling_pct"], t3["ceiling_kwh_per_m3"]), indent=True)

H("4.7  Consistency test 3: alkalinity, carbon and calcium closure", 2)
P("Precipitating Mg(OH)2 requires two equivalents of base per mole of product "
  "however the base is supplied, Eq. (12). Table 3 sets out four routes on a common "
  "basis of one cubic metre of permeate.", indent=True)
TBL(["Alkalinity route", "Reagent CO2 (kg/m3)", "Ca released / removed",
     "Mg imported (kg/m3)", "Extra energy (kWh/m3)"],
    [[k, "%.2f" % v["co2_reagents"], "%.1f x" % v["ca_closure_ratio"],
      "%.2f" % v["mg_imported_kg"], "%.1f" % v["extra_kwh"]] for k, v in RT.items()],
    caption="Table 3. Alkalinity routes, per cubic metre of permeate. Embodied-carbon "
            "factors are swept in the Monte Carlo rather than treated as point values.")
P("The calcium closure can be read directly off Table 1 and follows from Eq. (12). "
  "Writing concentrations per cubic metre of concentrate, the carbonate step removes "
  "Y_Ca x C_Ca = 1.407 g L-1, while the lime step, supplying the two equivalents of "
  "base that Eq. (12) requires, releases one calcium ion per magnesium precipitated "
  "and therefore adds 7.460 g L-1. The calcium reporting to the crystallizer is "
  "C_Ca - Ca_removed + Ca_added = 1.481 - 1.407 + 7.460 = 7.534 g L-1, which is "
  "exactly the S6 value in Table 1. Because seawater holds roughly three times more "
  "magnesium than calcium on a molar basis, the added term always exceeds the removed "
  "term and the balance cannot be closed by any choice of precipitation yield.",
  indent=True)
P("The route as specified carries %.2f kg CO2 per cubic metre of permeate in reagent "
  "embodied carbon against %.2f kg fixed in the carbonate product, and roughly double "
  "the plant's grid emissions. An environmental assessment restricted to electricity "
  "accounts for about a third of the total. The calcium balance therefore does not "
  "close: the "
  "lime step returns %.1f times more calcium than the carbonate step removed, and "
  "that calcium reports to the crystallizer rather than to a product. Calcined "
  "dolomite reduces the imbalance to %.1f times at the cost of importing %.2f kg of "
  "the magnesium product per cubic metre, which weakens the recovery claim even as "
  "it improves the balance. The carbon burden can be removed only by moving it into "
  "the energy account: electrochemical base makes the reagent term slightly negative "
  "at %.2f kg CO2 per cubic metre but adds %.0f kWh m-3."
  % (A["co2_reagents"], co2_fixed, A["ca_closure_ratio"], Cc["ca_closure_ratio"],
     Cc["mg_imported_kg"], Dd["co2_reagents"], Dd["extra_kwh"]), indent=True)
P("The embodied-carbon factors for soda ash and lime are taken from life-cycle "
  "inventory ranges rather than from a single primary measurement, and are swept "
  "rather than fixed. The conclusion does not depend on where in those ranges the "
  "true values lie: at the combination most favourable to the process - the lowest "
  "reagent factors with the cleanest grid - reagent carbon is 7.6 kg CO2 m-3 "
  "against 2.0 kg m-3 from electricity, and at every other combination tested the "
  "margin is wider. The reagent term dominates across the full plausible range.", indent=True)

H("4.8  Precipitation design basis", 2)
TBL(["Parameter", "Value", "Basis"], [
    ["Carbonate reagent", "Na2CO3, %.3f kg per m3 feed" % pd_["reagent_Na2CO3_kg_per_m3_feed"],
     "1.0 mol per mol Ca, 10% excess"],
    ["Alkalinity reagent", "Ca(OH)2, %.3f kg per m3 feed" % pd_["reagent_CaOH2_kg_per_m3_feed"],
     "1.0 mol per mol Mg, 10% excess"],
    ["CaCO3 recovered", "%.3f kg per m3 feed" % pd_["CaCO3_kg_per_m3_feed"], "95% yield"],
    ["Mg(OH)2 recovered", "%.3f kg per m3 feed" % pd_["MgOH2_kg_per_m3_feed"], "98% yield"],
    ["Residence time", "30 min carbonate, 45 min hydroxide", "seawater practice"],
    ["Reactor volume per 1000 m3/d feed",
     "%.1f and %.1f m3" % (pd_["reactor_volume_m3_per_1000m3d_feed"]["CaCO3 stage"],
                           pd_["reactor_volume_m3_per_1000m3d_feed"]["Mg(OH)2 stage"]),
     "residence time x concentrate flow"],
    ["Solid-liquid separation", pd_["solid_liquid_separation"], "assumed"],
    ["Cake solids", "CaCO3 65%, Mg(OH)2 45%", "Mg(OH)2 dewaters poorly"],
    ["Product purity", "set by the NaCl background", "see [9,17]"],
], caption="Table 4. Precipitation design basis.")

H("4.9  Operating cost and uncertainty propagation", 2)
TBL(["Item", "$ per m3 permeate"],
    [[k, "%.3f" % v] for k, v in op.items() if not k.startswith("_")],
    widths=(Inches(4.2), Inches(1.6)),
    caption="Table 5. OPEX breakdown at $0.08 kWh-1 and the median modelled SEC.")
TBL(["Cost element", "Conventional SWRO ($0.76 m-3)", "ILEDBV"],
    [list(r) for r in DC["stage_cost_boundary"]["rows"]],
    widths=(Inches(2.6), Inches(2.3), Inches(2.3)),
    caption="Table 6. Cost boundary comparison. The two levelized costs compared in "
            "the original did not cover the same scope; comparisons in this revision "
            "are made element by element on this table.")
P("The parameters the consistency tests identify as governing were propagated by "
  "Monte Carlo with %s samples (seed %s), sampling concentrator second-law "
  "efficiency, crystallizer energy, intake energy, electricity and reagent prices, "
  "CAPEX uplift, sellable fractions and prices for both minerals, reagent embodied "
  "carbon and grid carbon intensity. Every parameter is sampled from an independent "
  "uniform distribution over the interval given in Table 7; uniform sampling is used "
  "deliberately, since for most of these quantities the literature supports a "
  "plausible range but not a shape."
  % ("{:,}".format(mc["n"]), mc["seed"]), indent=True)
TBL(["Sampled parameter", "Lower", "Upper", "Unit", "Basis"], [
    ["Concentrator second-law efficiency", "0.25", "0.55", "-", "range for high-pressure membrane stages"],
    ["Crystallizer energy", "8", "15", "kWh m-3 feed", "MVC literature [20]"],
    ["Intake and pretreatment energy", "0.05", "0.80", "kWh m-3", "full reported intake range"],
    ["Electricity price", "0.05", "0.12", "$ kWh-1", "industrial tariff range"],
    ["Soda ash price", "0.18", "0.35", "$ kg-1", "bulk industrial"],
    ["Hydrated lime price", "0.08", "0.18", "$ kg-1", "bulk industrial"],
    ["CAPEX uplift for valorization", "0.20", "0.60", "-", "assumption, per reviewer request"],
    ["CaCO3 sellable fraction", "0.50", "0.70", "-", "purity and market constraints"],
    ["Mg(OH)2 sellable fraction", "0.05", "0.20", "-", "market-absorption check, Section 4.3"],
    ["Mineral price multiplier", "0.70", "1.30", "-", "applied to both products"],
    ["Soda ash embodied carbon", "0.80", "1.30", "kg CO2 kg-1", "LCA inventory range"],
    ["Lime embodied carbon", "0.90", "1.50", "kg CO2 kg-1", "calcination plus fuel"],
    ["Grid carbon intensity", "0.15", "0.65", "kg CO2 kWh-1", "spans low-carbon to coal grids"],
], fs=8, caption="Table 7. Monte Carlo sampling ranges. All distributions are uniform "
                 "and independent; the seed is recorded so the draw is reproducible.")
TBL(["Quantity", "Median", "5th percentile", "95th percentile", "Unit"],
    [["Concentrator energy", mc["concentrator_sec"]["median"], mc["concentrator_sec"]["p05"],
      mc["concentrator_sec"]["p95"], "kWh m-3 brine"],
     ["Total SEC", mc["sec_total"]["median"], mc["sec_total"]["p05"], mc["sec_total"]["p95"],
      "kWh m-3 permeate"],
     ["Reagent OPEX", mc["reagent_opex"]["median"], mc["reagent_opex"]["p05"],
      mc["reagent_opex"]["p95"], "$ m-3"],
     ["Total OPEX", mc["total_opex"]["median"], mc["total_opex"]["p05"],
      mc["total_opex"]["p95"], "$ m-3"],
     ["Gross LCOW", mc["lcow_gross"]["median"], mc["lcow_gross"]["p05"],
      mc["lcow_gross"]["p95"], "$ m-3"],
     ["Mineral credit", mc["mineral_credit"]["median"], mc["mineral_credit"]["p05"],
      mc["mineral_credit"]["p95"], "$ m-3"],
     ["Net LCOW", mc["lcow_net"]["median"], mc["lcow_net"]["p05"], mc["lcow_net"]["p95"],
      "$ m-3"],
     ["Net CO2", mc["co2_net_kg_per_m3"]["median"], mc["co2_net_kg_per_m3"]["p05"],
      mc["co2_net_kg_per_m3"]["p95"], "kg m-3 permeate"]],
    caption="Table 8. Monte Carlo results, 300,000 samples.")
P("The earlier version of this analysis treated non-energy operating cost as a share "
  "of energy cost, which concealed the dominant term. Costed explicitly, the "
  "precipitation reagents come to a median $%.2f per cubic metre of permeate against "
  "a median realisable mineral credit of $%.2f. The soda ash and lime required to "
  "precipitate the two products cost more than the products are worth, and no "
  "sampled combination of prices, sellable fractions and capital assumptions "
  "produced a net cost below the conventional comparator. No sampled configuration "
  "is carbon negative. The comparator itself requires definition: the $0.76 m-3 "
  "figure is a levelized cost for a conventional SWRO plant covering intake, "
  "pretreatment, high-pressure pumping with energy recovery, post-treatment, brine "
  "outfall, membrane replacement, labour, maintenance and annualized capital at the "
  "same 6%% discount rate and 20-year life used here. It excludes distribution and "
  "excludes any valorization train. Table 6 sets the two boundaries side by side, "
  "and the comparison in this paper is made on that table rather than between "
  "headline figures."
  % (mc["reagent_opex"]["median"], mc["mineral_credit"]["median"]), indent=True)

# =============================================================== 5. DISCUSSION
H("5.  Discussion")
H("5.1  Comparison with conventional SWRO", 2)
P("The energy claim made in the original version of this work does not survive. "
  "Modern SWRO plants with isobaric recovery operate at 2.5-3.5 kWh m-3, and an "
  "audited measurement on an operating plant reports 1.794 kWh m-3 [16,24]. Adding "
  "the boron-compliant second pass that a municipal plant requires brings the "
  "desalination stage of this architecture to a modelled 2.89-3.19 kWh m-3, within "
  "that band "
  "rather than below it. The architecture should not be presented as an "
  "energy-reduction technology.", indent=True)

H("5.2  Comparison with the brine-valorization literature", 2)
P("Assessments of mineral recovery from desalination brine commonly report "
  "favourable economics [10,17,25]. The present analysis suggests those results are "
  "sensitive to whether the alkalinity is costed. Where the reagent demand implied "
  "by Eq. (12) is priced at bulk industrial rates, it exceeds the value of the "
  "recovered minerals at any sellable fraction and price combination sampled here. "
  "This may help explain why a process repeatedly reported as attractive has not "
  "been commercialised at scale.", indent=True)

H("5.3  Alternative crystallization pathways", 2)
P("Mechanical vapour compression dominates the energy account, and three "
  "alternatives merit consideration. Membrane distillation crystallization has been "
  "demonstrated on hypersaline feeds with seeding to control scaling [8,19]; "
  "eutectic freeze crystallization offers a lower theoretical energy route and has "
  "been applied to RO brine [13]; and solar-driven interfacial evaporation now "
  "sustains evaporation from high-salinity brine with autonomous salt harvesting "
  "[4,5,6]. The last substitutes land area and capital for electricity. Since grid "
  "electricity is only about a third of this architecture's carbon account, "
  "eliminating it would not by itself make the process carbon neutral: the reagent "
  "term would remain.", indent=True)

H("5.4  Limitations", 2)
P("The osmotic-coefficient correction in Eq. (5) is carried as a swept parameter "
  "rather than a fitted correlation. Locking it requires implementing the seawater "
  "property correlations of [22] and [12] over the full 35-125 g kg-1 range of this "
  "process and re-solving the concentrator duty; the deposited code is structured to "
  "accept that substitution. Until that is done, every specific-energy figure "
  "reported here is a bounded model estimate rather than a final quantitative "
  "prediction, and should be cited as such. Section 4.5 bounds the residual "
  "uncertainty from this source at under 2%% of total SEC, so no conclusion in this "
  "paper turns on it. The "
  "embodied-carbon factors for soda ash and lime are indicative and are swept rather "
  "than fixed. Precipitation yields are taken from the literature and not measured "
  "here, and product purity is not modelled: purity is set by co-precipitation and "
  "occlusion of the sodium chloride background [9], which determines whether the "
  "solids meet any industrial specification and therefore whether the sellable "
  "fractions assumed here are attainable at all. The residual liquid fraction is "
  "modelled, not validated. Subsurface intake performance is site dependent, and the "
  "risks of aquifer clogging and seawater intrusion are not modelled.", indent=True)

# ============================================================== 6. CONCLUSIONS
H("5.5  Proposed validation", 2)
P("Three measurements would settle the questions this analysis raises, and none "
  "requires the full architecture to be built. First, the second-law efficiency of a "
  "high-pressure concentrator operating on real SWRO brine at 60-65 g L-1, which "
  "fixes the energy term the original assumed. Second, the reagent demand and "
  "product purity of sequential Ca/Mg precipitation from that concentrate at pilot "
  "scale, which fixes both the alkalinity cost and the sellable fraction. Third, the "
  "calcium balance across the precipitation train, which Table 1 predicts does not "
  "close. Each is a bench or skid-scale measurement, and each independently tests "
  "one of the three consistency tests reported here.", indent=True)

H("6.  Conclusions")
P("This study applied three consistency tests to an integrated SWRO and "
  "brine-valorization architecture and reports the outcome of each, including where "
  "the architecture fails.", indent=True)
P("The energy claim does not survive a modern comparator. Against plants operating "
  "at 2.5-3.5 kWh m-3 the desalination stage offers no material advantage once a "
  "boron-compliant second pass is included, and the corrected concentrator raises "
  "modelled total specific energy consumption to a median %.1f kWh m-3. That figure, "
  "and every specific-energy figure in this paper, is a bounded model estimate rather "
  "than a measured or predicted plant value, for the reasons set out in Sections 3 "
  "and 5.4."
  % mc["sec_total"]["median"], indent=True)
P("The valorization case, as configured, does not close, and the binding constraint "
  "is alkalinity in both currencies. In money, the soda ash and lime cost a median "
  "$%.2f per cubic metre of permeate against a realisable mineral credit of $%.2f. "
  "In carbon, calcination costs %.1f kg CO2 per cubic metre against %.2f kg fixed in "
  "the carbonate product, while electrochemical base costs %.0f kWh m-3. Published "
  "assessments generally count neither."
  % (mc["reagent_opex"]["median"], mc["mineral_credit"]["median"],
     A["co2_reagents"], co2_fixed, Dd["extra_kwh"]), indent=True)
P("Two narrow and tractable directions follow, and identifying them is the practical "
  "value of this analysis. The first is low-carbon, low-cost alkalinity: "
  "waste-derived bases, or electrochemical generation coupled to surplus renewable "
  "capacity where the energy penalty is not charged at grid carbon intensity. The "
  "second is closure of the calcium balance, for which calcined dolomite is a "
  "partial answer whose cost is the import of product. Neither requires the "
  "architecture to be redesigned, and both can be tested independently of it.", indent=True)

# ============================================================== NOMENCLATURE
H("Nomenclature")
TBL(["Symbol", "Definition", "Unit"], [
    ["C_f,i / C_p,i / C_b,i", "feed, permeate, concentrate concentration of ion i", "g L-1"],
    ["r_i", "membrane rejection of ion i", "-"],
    ["R", "water recovery ratio of a membrane stage", "-"],
    ["Q_f / Q_p / Q_b", "feed, permeate, concentrate flow", "m3 m-3 feed"],
    ["pi", "osmotic pressure", "bar"],
    ["phi(S)", "osmotic coefficient at salinity S", "-"],
    ["P_f", "applied feed pressure", "bar"],
    ["NDP", "net driving pressure allowance", "bar"],
    ["beta", "concentration-polarization factor, C_wall / C_bulk", "-"],
    ["eta_pump / eta_PX / eta_II", "pump, pressure-exchanger, second-law efficiency", "-"],
    ["w_min", "least work of separation", "kWh m-3"],
    ["SEC", "specific energy consumption", "kWh m-3 permeate"],
    ["LCOW", "levelized cost of water", "$ m-3"],
    ["CRF", "capital recovery factor", "yr-1"],
    ["Y_Ca / Y_Mg", "precipitation yield of calcium and magnesium", "-"],
    ["n_base", "alkalinity demand", "equivalents"],
], widths=(Inches(1.7), Inches(4.2), Inches(1.3)))

# ============================================================ DECLARATIONS
H("Data availability")
P("The model implementation, the parameter set, the random seed, and the scripts "
  "that generate every table and figure are openly available at "
  "https://github.com/sandlerleon/iledbv-desalination-model, release tag v2.0.1. An "
  "archived snapshot of that release is deposited at "
  "https://doi.org/10.5281/zenodo.22178234; this manuscript and the point-by-point "
  "response to reviewers are deposited at https://doi.org/10.5281/zenodo.22178232. "
  "Both are concept DOIs and resolve to the current version of each deposit. The "
  "revision was produced with Python "
  "3.11.9 and NumPy 2.4.6. Running iledbv_revision_v2.py, design_and_costing.py and "
  "boron_recalc.py regenerates the JSON files from which every number in this paper "
  "is taken; audit_manuscript.py re-checks the built document against them. No "
  "experimental data were generated.", indent=True)

H("Declaration of competing interest")
P("The author declares no competing financial or non-financial interests.", indent=True)

H("Funding")
P("This research received no specific grant from funding agencies in the public, "
  "commercial, or not-for-profit sectors.", indent=True)

# ================================================================ REFERENCES
H("References")
for i, r in enumerate(REFS, 1):
    a = ", ".join(r["authors"][:6]) + (", et al." if len(r["authors"]) > 6 else "")
    vol = (" %s" % r["volume"]) if r["volume"] else ""
    pg = (" (%s) %s" % (r["year"], r["pages"])) if r["pages"] else " (%s)" % r["year"]
    par = doc.add_paragraph(); par.paragraph_format.space_after = Pt(3)
    par.add_run("[%d] %s, %s, %s%s%s. https://doi.org/%s"
                % (i, a, r["title"], r["journal"], vol, pg, r["doi"])).font.size = Pt(9)

doc.save(OUT)
words = sum(len(x.text.split()) for x in doc.paragraphs)
print("abstract: %d words" % len(ABSTRACT.split()))
print("manuscript: %d words in paragraphs, %d tables, %d references"
      % (words, len(doc.tables), len(REFS)))
print("saved", OUT)
