# -*- coding: utf-8 -*-
"""Numerical consistency audit of the revised manuscript.

The feedback asked for a final pass checking every number in the abstract,
tables, discussion and conclusions against the model. This does that
mechanically: it pulls the headline quantities out of the model JSON, then
requires each to appear in the document, and separately looks for internal
contradictions of the kind that produced the boron error.

    python audit_manuscript.py
"""
import io, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
DOC = r"C:\Users\Leon\Downloads\DWT\ILEDBV_Manuscript_Revised_v3.docx"
from docx import Document

V2 = json.load(io.open(os.path.join(HERE, "iledbv_revision_v2.json"), encoding="utf-8"))
DC = json.load(io.open(os.path.join(HERE, "design_costing.json"), encoding="utf-8"))
BR = json.load(io.open(os.path.join(HERE, "boron_results.json"), encoding="utf-8"))
mc, t1 = V2["monte_carlo"], V2["t1_concentrator"]
A = V2["precipitation_routes"]["A: soda ash + lime (as written)"]
st = DC["streams_as_modelled"]

doc = Document(DOC)
text = "\n".join(p.text for p in doc.paragraphs)
for t in doc.tables:
    for row in t.rows:
        text += "\n" + " | ".join(c.text for c in row.cells)

CHECKS = [
    ("least work of separation", "%.2f" % t1["least_work_kwh_per_m3_brine"]),
    ("attainable concentrator, low", "%.1f" % float(t1["realistic_at_second_law_eff"]["0.55"])),
    ("attainable concentrator, high", "%.1f" % float(t1["realistic_at_second_law_eff"]["0.25"])),
    ("median total SEC", "%.1f" % mc["sec_total"]["median"]),
    ("reagent embodied carbon", "%.1f" % A["co2_reagents"]),
    ("electrochemical energy", "%.0f" % A["co2_reagents"] if False else "%.0f" %
     V2["precipitation_routes"]["D: dosed CO2 + electrochemical base"]["extra_kwh"]),
    ("calcium closure ratio", "%.1f" % A["ca_closure_ratio"]),
    ("median reagent OPEX", "%.2f" % mc["reagent_opex"]["median"]),
    ("median mineral credit", "%.2f" % mc["mineral_credit"]["median"]),
    ("median net LCOW", "%.2f" % mc["lcow_net"]["median"]),
    ("net LCOW p05", "%.2f" % mc["lcow_net"]["p05"]),
    ("net LCOW p95", "%.2f" % mc["lcow_net"]["p95"]),
    ("crystallizer feed TDS", "%.1f" % st["S6 crystallizer feed"]["TDS_g_L"]),
    ("concentrate TDS", "%.1f" % st["S5 concentrator concentrate"]["TDS_g_L"]),
    ("Ca before precipitation", "%.3f" % st["S5 concentrator concentrate"]["ions_g_L"]["Ca2+"]),
    ("Ca after precipitation", "%.3f" % st["S6 crystallizer feed"]["ions_g_L"]["Ca2+"]),
    ("boron range low", "%.2f" % BR["permeate_boron_range_mg_l"][0]),
    ("boron range high", "%.2f" % BR["permeate_boron_range_mg_l"][1]),
]

print("HEADLINE NUMBERS PRESENT IN THE DOCUMENT")
missing = []
for label, val in CHECKS:
    present = val in text
    if not present:
        missing.append((label, val))
    print("   %-32s %-10s %s" % (label, val, "ok" if present else "NOT FOUND"))

print("\nINTERNAL CONTRADICTION CHECKS")
problems = []

# the class of error that produced the boron mistake: a value described as being
# on the wrong side of a threshold stated in the same sentence
for m in re.finditer(r"([\d.]+)\s*mg L-1[^.]{0,120}?(above|below|exceeds)[^.]{0,60}?([\d.]+)\s*mg L-1",
                     text):
    v, rel, lim = float(m.group(1)), m.group(2), float(m.group(3))
    wrong = (rel in ("above", "exceeds") and v <= lim) or (rel == "below" and v >= lim)
    if wrong:
        problems.append("value %.2f described as %s %.2f: %s" % (v, rel, lim, m.group(0)[:90]))

# the withdrawn claims must not have survived anywhere
for phrase in ("31%", "3.95 kWh", "10.68 kWh", "0.75 kWh m-3 of brine",
               "nanofiltration brine concentration"):
    if phrase in text and phrase not in ("10.68 kWh",):
        problems.append("withdrawn claim still present: %r" % phrase)
    elif phrase == "10.68 kWh" and phrase in text:
        ctx = text[max(0, text.find(phrase) - 90):text.find(phrase) + 30]
        if "originally" not in ctx and "original" not in ctx:
            problems.append("10.68 kWh appears without being marked as the original value")

# every table referenced must have a caption and vice versa
caps = {int(m) for m in re.findall(r"^Table (\d+)\.", text, re.M)}
refs = {int(m) for m in re.findall(r"Table (\d+)", text)}
if caps != refs:
    problems.append("table captions %s vs references %s" % (sorted(caps), sorted(refs)))

# nomenclature must define every symbol introduced in this revision
for sym in ("phi(S)", "w_min", "n_base", "eta_II", "beta"):
    if text.count(sym) < 2:
        problems.append("symbol %r appears fewer than twice - check it is in the Nomenclature" % sym)

for p in problems:
    print("   !! %s" % p)
if not problems:
    print("   none found")

print("\nSUMMARY")
print("   headline numbers checked : %d" % len(CHECKS))
print("   not found in document    : %d" % len(missing))
print("   contradictions / issues  : %d" % len(problems))
print("   verdict                  : %s"
      % ("PASS" if not missing and not problems else "NEEDS ATTENTION"))
