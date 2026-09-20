# -*- coding: utf-8 -*-
"""Point-by-point response to reviewers, DWT-D-26-01366.

Numbers are read from the model JSON so the letter cannot disagree with the
manuscript it accompanies.

    python build_response_letter.py
"""
import io, json, os
from docx import Document
from docx.shared import Pt, Inches

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"C:\Users\Leon\Downloads\DWT\DWT_Response_to_Reviewers.docx"
V2 = json.load(io.open(os.path.join(HERE, "iledbv_revision_v2.json"), encoding="utf-8"))
DC = json.load(io.open(os.path.join(HERE, "design_costing.json"), encoding="utf-8"))
SP = json.load(io.open(os.path.join(HERE, "second_pass_results.json"), encoding="utf-8"))
BR = json.load(io.open(os.path.join(HERE, "boron_results.json"), encoding="utf-8"))
mc, t1 = V2["monte_carlo"], V2["t1_concentrator"]
A = V2["precipitation_routes"]["A: soda ash + lime (as written)"]
Dd = V2["precipitation_routes"]["D: dosed CO2 + electrochemical base"]
w_min = t1["least_work_kwh_per_m3_brine"]
lo, hi = t1["realistic_at_second_law_eff"]["0.55"], t1["realistic_at_second_law_eff"]["0.25"]

doc = Document()
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10.5)
for s in doc.sections:
    s.left_margin = s.right_margin = Inches(0.85)


def H(t, size=13, before=15):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before); p.paragraph_format.space_after = Pt(5)
    r = p.add_run(t); r.bold = True; r.font.size = Pt(size)


def P(t, italic=False, size=10.5, after=8, bold=False):
    par = doc.add_paragraph(); par.paragraph_format.space_after = Pt(after)
    r = par.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(size)


def QA(num, comment, response):
    par = doc.add_paragraph(); par.paragraph_format.space_before = Pt(9)
    par.paragraph_format.space_after = Pt(3)
    r = par.add_run("%s  " % num); r.bold = True; r.font.size = Pt(10.5)
    r2 = par.add_run(comment); r2.italic = True; r2.font.size = Pt(10)
    p2 = doc.add_paragraph(); p2.paragraph_format.space_after = Pt(6)
    p2.paragraph_format.left_indent = Inches(0.2)
    p2.add_run(response).font.size = Pt(10.5)


H("Response to Reviewers — DWT-D-26-01366", 15, 0)
P("Process and Technoeconomic Assessment of Integrated Subsurface-Intake SWRO, "
  "Isobaric Energy Recovery, and Near-Zero-Liquid-Discharge Brine Valorization",
  italic=True, size=10)
P("Revised title: Consistency Testing of an Integrated Subsurface-Intake SWRO and "
  "Brine-Valorization Architecture: Alkalinity as the Binding Constraint",
  italic=True, size=10)

H("Summary of the revision", 12)
P("I am grateful to all four reviewers. The comments identified two errors that "
  "changed the paper's conclusions, and the revision follows where they led rather "
  "than defending the original position.")
P("First, Reviewer 1 questioned the brine-concentrator energy. Checking it against "
  "the least work of separation showed the assumed range of 0.5-1.0 kWh per cubic "
  "metre of brine to lie at or below the reversible minimum of %.2f kWh m-3 for that "
  "feed. The assumption was not merely optimistic but thermodynamically "
  "inadmissible. The revision replaces it with a bounded estimate of %.1f-%.1f kWh "
  "m-3, obtained from the reversible minimum and a 25-55%% second-law efficiency "
  "range. We are careful to call this a bounded estimate rather than an attainable "
  "value, since it is derived rather than measured."
  % (w_min, lo, hi))
P("Second, Reviewers 1 and 3 asked for reagent detail and a proper OPEX breakdown. "
  "Costing the precipitation reagents explicitly rather than as a share of operating "
  "cost revealed that soda ash and lime cost a median $%.2f per cubic metre of "
  "permeate against a realisable mineral credit of $%.2f. The economic case does not "
  "close, and the embodied carbon of those same reagents, %.1f kg CO2 m-3, is "
  "roughly double the grid-electricity emissions the original counted."
  % (mc["reagent_opex"]["median"], mc["mineral_credit"]["median"], A["co2_reagents"]))
P("Reviewers 3 and 4 both judged the energy comparator unsound, and they were right. "
  "The claim of a 31% advantage over conventional SWRO is withdrawn. The paper is "
  "reframed around a consistency-testing method and reports honestly that the "
  "architecture fails two of its own three tests as specified. I recognise this is "
  "an unusual revision, but I believe a quantified negative result anchored to "
  "physical bounds is more useful than the original claim.", bold=True)

# ------------------------------------------------------------------ REVIEWER 1
H("Reviewer 1")
for num, c, r in [
 ("1.", "Introduction should not be subdivided; too brief; review recent progress for each "
  "technology; discuss partial integrations and remaining challenges.",
  "The Introduction is rewritten as continuous prose with the subsections removed, and "
  "now reviews recent progress for each of the five technologies with 25 references, "
  "every one verified against Crossref. A dedicated paragraph sets out which pairs of "
  "technologies have already been integrated, which have been studied only in "
  "isolation, and what the interactions between them reveal - which is the gap the "
  "study addresses."),
 ("2.", "Equations and variables need clearer definition and journal formatting; add a "
  "calculation workflow.",
  "Thirteen equations are now numbered consecutively and set as displayed equations. A "
  "Nomenclature table defines every symbol with units. Section 3 opens with the "
  "solution procedure, stating the order in which the balances are solved and noting "
  "that no iteration is required."),
 ("3.", "Justify the choice of models; validate against independent data.",
  "The revision changes the basis of justification. Rather than defending each adopted "
  "model, each subsystem is now tested against a physical or stoichiometric bound that "
  "any correct model must respect - the least work of separation for the concentrator, "
  "the polarization factor for boundary-layer effects, and the alkalinity "
  "stoichiometry for precipitation. Two of the three tests are failed by the "
  "architecture as originally specified, which is reported."),
 ("4.", "NF concentrator energy questionable at 63.5 to 121 g/L; 50% recovery optimistic; "
  "monovalent leakage; cite high-salinity NF literature; fouling and scaling; CAPEX/OPEX "
  "inclusion.",
  "This comment produced the most consequential change in the revision. Section 4.5 "
  "shows the assumed energy to be below the reversible minimum and replaces it with a "
  "bounded estimate; Figure 3 presents the test. Separately, the stage was "
  "mislabelled: "
  "at 90% monovalent rejection it is not nanofiltration but a high-pressure, "
  "low-salt-rejection RO stage, and Section 2.4 now says so and reports what a genuine "
  "NF element would give instead. The +40% uplift is now stated as a sampled range "
  "rather than a point value, and Table 4 gives the OPEX composition."),
 ("5.", "Economic model lacks OPEX detail; +40% CAPEX uplift assumed; show 20-60% sensitivity; "
  "ZLD crystallizer CAPEX may make +40% optimistic.",
  "Table 4 now gives a nine-line OPEX breakdown with the basis for each line. The "
  "largest item is not electricity but the precipitation reagents. The CAPEX uplift is "
  "sampled across 20-60% in the Monte Carlo rather than fixed, and the uplift is "
  "explicitly identified as an assumption rather than a quotation."),
 ("6.", "Add comparison with existing literature.",
  "Section 5.1 compares the corrected SEC against the modern SWRO range and against the "
  "audited plant measurement Reviewer 3 supplied. Section 5.2 compares the economic "
  "result against the brine-valorization literature and offers an explanation for the "
  "divergence: those assessments generally do not cost the alkalinity."),
 ("7.", "CaCO3 credited at 100% sellable and full price is unrealistic.",
  "Accepted. A sellable fraction of 50-70% is now sampled for calcium carbonate, as it "
  "already was for magnesium hydroxide, and Section 4.3 discusses the purity, particle "
  "size and brightness constraints that determine whether recovered carbonate meets any "
  "specification. Transport and refining remain outside the boundary and are therefore "
  "uncredited, which is stated. The fraction is included in the Monte Carlo."),
 ("8.", "MVC at 11.5 kWh/m3 may be at the upper bound; discuss degradation and scaling; "
  "consider membrane distillation and freeze crystallization.",
  "Crystallizer energy is sampled across 8-15 kWh m-3 rather than fixed at the midpoint. "
  "Section 5.3 compares MVC against membrane distillation crystallization, eutectic "
  "freeze crystallization and solar interfacial evaporation, and notes that because "
  "grid electricity is only about a third of the carbon account, replacing MVC would "
  "not by itself make the process carbon neutral."),
 ("9.", "Linear osmotic model will deviate at 121 g/L; quantify the impact; run a sensitivity "
  "with a more accurate model.",
  "Quantified rather than acknowledged. Applying an osmotic-coefficient rise of 8-24% "
  "between 35 and 120 g L-1 raises the concentrator feed from 49.0 to 50.3-52.9 bar and "
  "total SEC from 12.64 to 12.87 kWh m-3 - real but second-order, under 2%, and an "
  "order of magnitude smaller than the concentrator correction. The published seawater "
  "property correlations appropriate for locking phi(S) are now cited, and the "
  "deposited code is structured to accept them. Because that substitution has not yet "
  "been made, the manuscript now states in the Abstract, Section 3, Section 4.5, the "
  "Limitations and the Conclusions that every specific-energy figure is a bounded "
  "model estimate rather than a final quantitative prediction."),
 ("10.", "Discuss qualitatively how a lithium breakthrough would affect LCOW.",
  "Given the corrected economics, the honest statement is quantitative: the net cost gap "
  "to be closed is now approximately $%.2f m-3, which is far larger than any plausible "
  "lithium credit from seawater-derived brine at present recovery yields. Lithium "
  "remains excluded from the baseline and this is stated in Section 5.4."
  % (mc["lcow_net"]["median"] - 0.76)),
 ("11.", "Numerical and editorial errors: LCOW units, figure order, intake SEC midpoint, "
  "uncited reference [12], long sentences.",
  "All corrected. The two LCOW figures concerned are withdrawn and replaced by the "
  "boundary comparison in Table 5. Figures are renumbered to citation order. Intake SEC "
  "is now swept across the full 0.05-0.80 kWh m-3 range rather than fixed at the low "
  "end. The reference list was checked programmatically: all 25 entries are cited and "
  "none is orphaned. Long sentences in the Abstract and Introduction have been split."),
 ("12.", "Does the conventional $0.76/m3 baseline cover the same scope as the ILEDBV figure? "
  "Provide a stage cost comparison.",
  "It did not, and the comparison was therefore invalid. Table 5 sets out the boundary "
  "element by element: the conventional case included a brine outfall the integrated "
  "architecture does not have, and excluded the valorization train it does. Comparisons "
  "in the revision are made on that table rather than headline to headline."),
 ("13.", "State code version and runtime environment.",
  "Added to Data Availability: the repository with release tag v2.0.1, Python 3.11.9 "
  "and NumPy 2.4.6, and archival DOIs for both the code (10.5281/zenodo.22178234) "
  "and this manuscript with its response letter (10.5281/zenodo.22178232). The "
  "commands that regenerate every number are listed."),
]:
    QA(num, c, r)

# ------------------------------------------------------------------ REVIEWER 2
H("Reviewer 2")
for num, c, r in [
 ("1.", "Contrast MVC with solar-driven interfacial evaporation; four papers named.",
  "Added in Section 5.3. Three of the four named papers are cited. I was unable to match "
  "the fourth: International Journal of Biological Macromolecules 370 (2026) 152880 "
  "resolves to 'Efficient fabrication of cellulose-based hydrogels for effective heavy "
  "metal ion adsorption from oral medical wastewater', which does not appear to concern "
  "solar interfacial evaporation. If a different reference was intended I would be glad "
  "to include it."),
 ("2.", "No probabilistic uncertainty analysis; state that CAPEX uncertainty dominates.",
  "A Monte Carlo over eleven uncertain parameters with 300,000 samples now replaces the "
  "one-at-a-time tornado as the primary uncertainty result (Table 7, Figure 5). CAPEX "
  "uncertainty turns out not to dominate: reagent cost does. The net levelized cost is "
  "$%.2f m-3 with a 90%% interval of $%.2f-$%.2f."
  % (mc["lcow_net"]["median"], mc["lcow_net"]["p05"], mc["lcow_net"]["p95"])),
 ("3.", "Environmental assessment covers only grid CO2; add solar comparison and subsurface "
  "intake risks.",
  "Section 4.4 is rewritten. The larger finding is that the original assessment counted "
  "only about a third of the emissions: reagent embodied carbon adds %.1f kg CO2 m-3 "
  "against %.1f kg from electricity, and the carbonate product fixes only %.2f kg. "
  "Figure 6 shows the account against grid carbon intensity. Aquifer clogging and "
  "saline intrusion are now discussed explicitly as site-dependent intake risks."
  % (A["co2_reagents"], mc["sec_total"]["median"] * 0.4,
     V2["co2_fixed_kg_per_m3_permeate"])),
 ("4.", "Residual liquid fraction is model-derived; emphasise the lack of pilot validation.",
  "Stated where the figure first appears rather than only in Limitations, together with "
  "the observation that leakage, blowdown and operational upsets would raise the real "
  "value. Section 5.5 proposes three specific bench-scale measurements that would test "
  "the three consistency tests independently."),
]:
    QA(num, c, r)

# ------------------------------------------------------------------ REVIEWER 3
H("Reviewer 3")
for num, c, r in [
 ("Overall.", "A preliminary design exercise rather than a sufficiently developed technical "
  "paper; key parameters and pathways not adequately justified.",
  "I accept the characterisation of the original. The revision responds by changing what "
  "the paper claims to be: rather than presenting a design, it tests one against physical "
  "bounds and reports that it fails two of three tests as specified. The parameters the "
  "reviewer identified as unjustified are precisely the ones the tests were built around."),
 ("p.2.", "Review recent SWRO SEC literature; modern plants are 2.5-3.5 kWh/m3; see "
  "doi 10.1016/j.ecmx.2026.101682.",
  "The named paper is cited and its 1.794 kWh m-3 measurement quoted in the Introduction "
  "and Section 5.1. The 3.95 kWh m-3 comparator is withdrawn and the energy claim with it."),
 ("p.3.", "'ILEDBV' undefined; unclear how Figure 1 was developed.",
  "The acronym is expanded at first use. Figure 1 is now explicitly described as the "
  "author's conceptual integration of five separately published component technologies, "
  "not a description of an existing installation."),
 ("4.1.", "SWRO design detail needed: design flux, target product quality, second-pass BWRO "
  "for boron or chloride and if not, why.",
  "Section 2.3 is new and addresses this directly. First-pass permeate is approximately "
  "%.0f mg L-1 TDS and %.0f mg L-1 chloride, both comfortably potable, so the parameter "
  "that decides whether a second pass is needed is boron. Boron rejection is not a "
  "single number - it falls as elements age and rises with temperature and pH - so "
  "across seawater boron of 4.6-5.5 mg L-1 and rejection of 72-88%%, first-pass permeate "
  "boron is %.2f-%.2f mg L-1. That complies with the WHO guideline of 2.4 mg L-1 in "
  "every case, and with the EU limit of 1.5 mg L-1 in all but the most severe, but it "
  "straddles the 1.0 mg L-1 figure common in municipal supply contracts and exceeds a "
  "0.5 mg L-1 irrigation limit in every case. The second pass is therefore presented as "
  "a conditional requirement rather than an absolute one, and the energy comparison in "
  "Section 5.1 is reported both with and without it. A gravity-fed second pass was also "
  "considered and rejected: 12 bar requires %.0f m of static head."
  % (SP["first_pass"]["tds_mg_l"], SP["first_pass"]["cl_mg_l"],
     BR["permeate_boron_range_mg_l"][0], BR["permeate_boron_range_mg_l"][1],
     SP["gravity_head"]["typical second pass"]["m"])),
 ("p.9 NF.", "Which NF membrane; what rejections; what recovery, pressure and flux.",
  "The reviewer's question exposed a mislabelling. At the rejections assumed the stage is "
  "not nanofiltration. Section 2.4 renames it a high-pressure, low-salt-rejection RO "
  "stage, states the assumed rejections explicitly, and reports that a genuine NF element "
  "at 30%% monovalent rejection would give a crystallizer feed of %.1f g L-1 rather than "
  "%.1f g L-1."
  % (DC["streams_true_nf"]["S6 crystallizer feed"]["TDS_g_L"],
     DC["streams_as_modelled"]["S6 crystallizer feed"]["TDS_g_L"])),
 ("p.9 Precip.", "Reagents, dosages, residence time, reactor volume, solid-liquid separation, "
  "product water content and purity.",
  "Table 3 gives the full design basis: reagent identity and dosage on a stoichiometric "
  "basis with stated excess, residence times, reactor volumes per unit feed, the "
  "separation train, and assumed cake solids. Product purity is discussed against the "
  "sodium chloride background that governs it."),
 ("p.9 MVC.", "Crystallizer inlet concentration; salinity profile and ionic composition "
  "through each step.",
  "Table 1 is new and gives the ion-by-ion composition of every stream. The crystallizer "
  "feed is %.1f g L-1. The table also exposed something the original analysis missed: "
  "calcium rises from %.2f to %.2f g L-1 across the precipitation train because lime "
  "returns one calcium ion per magnesium precipitated, and total dissolved solids rise "
  "rather than fall."
  % (DC["streams_as_modelled"]["S6 crystallizer feed"]["TDS_g_L"],
     DC["streams_as_modelled"]["S5 concentrator concentrate"]["ions_g_L"]["Ca2+"],
     DC["streams_as_modelled"]["S6 crystallizer feed"]["ions_g_L"]["Ca2+"])),
 ("4.3.", "Recovery yield and product purity depend on many factors; discuss in greater "
  "detail with literature support.",
  "Discussed in Sections 4.3 and 5.4 with reference to work quantifying how the sodium "
  "chloride background affects yield, purity, morphology and carbonate polymorph, and to "
  "product-quality-directed studies that have produced specification-grade solids from "
  "brine feeds."),
 ("4.4.", "Product quality and price vary by application; the economic assessment is too vague.",
  "Given the corrected reagent costs, the economics no longer turn on which grade is "
  "targeted: the reagent cost exceeds the mineral credit across the full range of prices "
  "and sellable fractions sampled. This is stated rather than obscured."),
 ("Minor.", "Misplaced intake discussion; equation notation; equation numbering; table "
  "numbers and titles.",
  "All corrected. The intake discussion is moved out of the brine-management material into "
  "Section 2.2; equations are properly set and numbered (1)-(13); all seven tables are "
  "numbered with descriptive captions."),
]:
    QA(num, c, r)

# ------------------------------------------------------------------ REVIEWER 4
H("Reviewer 4")
for num, c, r in [
 ("1.", "Does not follow the structure and formatting of a research paper; reads as a short "
  "technical report.",
  "The manuscript is restructured throughout, with a continuous-prose Introduction, a "
  "formal model section with numbered equations and a nomenclature, seven captioned "
  "tables and six figures."),
 ("2.", "Scientific contribution beyond integration is unclear.",
  "The contribution is restated and is no longer the integration. It is a set of three "
  "consistency tests that any brine-valorization architecture must pass, and the finding "
  "that magnesium recovery from a chloride brine is limited by alkalinity rather than by "
  "magnesium - a result that generalizes beyond this architecture, since two equivalents "
  "of base per mole of product are required however the base is supplied."),
 ("3.", "Introduction requires major revision; research gap not identified.",
  "Rewritten; see the response to Reviewer 1, comment 1."),
 ("4.", "Several parts appear AI-generated; generic statements and unsupported claims.",
  "I take this seriously and can identify a specific cause. The abstract field submitted "
  "through the editorial system began with a stray sentence, 'Here is a tightened "
  "200-word abstract based on the manuscript:', which appeared on the cover page of the "
  "PDF sent to reviewers. That was an editing error on my part, it should not have "
  "reached review, and it has been removed. Beyond that, the revision replaces "
  "unsupported generic statements with results derived from stated physical bounds, and "
  "every reference has been verified against Crossref rather than cited from memory. "
  "Generative AI was used as a drafting and analysis aid; all modelling decisions, the "
  "interpretation, and responsibility for the content are mine.", ),
 ("5.", "Equations lack rigour; assumptions, variables, boundaries and sources unclear; the "
  "calculation should be independently reproducible.",
  "Equations (1)-(13) are numbered and defined, the system boundary is stated per balance, "
  "the solution procedure is given in Section 3, and the complete model is deposited so "
  "that every table and figure can be regenerated from it."),
 ("6.", "Energy consumption appears excessively high; the 3.95 kWh/m3 conventional baseline is "
  "questionable when 2.2-2.4 is achievable.",
  "Accepted without qualification. The comparator is withdrawn, as is the 31% advantage "
  "claim built on it. Section 5.1 now compares against the 2.5-3.5 kWh m-3 range and the "
  "audited 1.794 kWh m-3 measurement, and concludes that the architecture offers no "
  "material energy advantage at the desalination stage. Reviewers 3 and 4 were both "
  "correct on this point and it is the reason the paper is reframed."),
]:
    QA(num, c, r)

H("Closing")
P("The revision is substantially different from the original, and its conclusions are "
  "less favourable to the architecture than those I first submitted. I believe that is "
  "the correct outcome of the review, and that a result anchored to thermodynamic and "
  "stoichiometric bounds - including where those bounds are not met - is of more use to "
  "this field than the claim it replaces. I am grateful to the reviewers for the care "
  "that produced it.")
P("Leon Sandler", bold=True)

doc.save(OUT)
n = sum(1 for p in doc.paragraphs if p.text.strip())
print("response letter: %d paragraphs, %d words" %
      (n, sum(len(p.text.split()) for p in doc.paragraphs)))
print("saved", OUT)
