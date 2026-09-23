# -*- coding: utf-8 -*-
"""Repair the regressions introduced by the Rubriq copyedit of v2 -> v3.

The copyedit made 102 changes. Most are wanted: British to US spelling,
hyphen to en dash in numeric ranges, curly apostrophes, and a large number of
ordinary style improvements. Those are kept in full.

Roughly forty changes are not improvements. They fall into four kinds, and the
first two are the reason this file exists:

  reversals   a conditional turned indicative, a comparison inverted, a
              hedge deleted. "would raise it" -> "increase it" asserts as fact
              what the sentence exists to mark as unverified; "Against plants
              operating at 2.5-3.5" -> "Unlike plants operating at 2.5-3.5"
              reverses which side of the comparison holds the advantage.

  corruption  sentences that no longer parse or no longer mean anything:
              "no conclusion in this paper is reached", "whose original
              credited at 100%", "a partial second pass at an elevated pH of
              35-100% of the permeate", "the two routes cost the same amount
              is 0.061 kWh-1" (which also lost its dollar sign).

  terminology "brine" changed to "saltwater" in two places where the salinity
              range is the point, and "however the base arrives" (meaning
              regardless of how) punctuated into "; however, the base
              arrives", which inverts it.

  agreement   "values ... falls", "the swing of each command", "the thirteen
              samples" for thirteen sampled parameters.

Each repair below keeps the copyeditor's US spelling and en dashes and
restores only the sense.

    python fix_rubriq_v3.py
"""
import io
import os
import shutil

from docx import Document

DWT = r"C:\Users\Leon\Downloads\DWT"
SRC = os.path.join(DWT, "ILEDBV_Manuscript_Revised_v3.docx")

EN = "\u2013"
EM = "\u2014"
RS = "\u2019"


def replace_in_paragraph(p, old, new):
    """Replace old with new, preserving per-run formatting.

    Builds a map from each character of the paragraph to the run that owns it,
    performs the replacement on the flat string, then reassigns text run by
    run. A naive p.text = ... would flatten subscripts and italics.
    """
    runs = p.runs
    if not runs:
        return False
    full = "".join(r.text for r in runs)
    if old not in full:
        return False
    owner = []
    for i, r in enumerate(runs):
        owner.extend([i] * len(r.text))
    start = full.index(old)
    end = start + len(old)
    home = owner[start] if start < len(owner) else len(runs) - 1
    pieces = [[] for _ in runs]
    for i in range(len(full)):
        if start <= i < end:
            continue
        pieces[owner[i]].append(full[i])
    # splice the replacement into the run that owned the first character
    before = "".join(full[i] for i in range(start) if owner[i] == home)
    after = "".join(full[i] for i in range(end, len(full)) if owner[i] == home)
    pieces[home] = list(before + new + after)
    for i, r in enumerate(runs):
        r.text = "".join(pieces[i])
    return True


# ------------------------------------------------------------------ the repairs
# (search, replacement, one-line reason)
FIXES = [
    # --- abstract ---------------------------------------------------------
    ("The cost of those reagents explicitly is decisive",
     "Costing those reagents explicitly is decisive",
     "abstract: the verb phrase no longer parses"),
    ("is limited by the base but by its supply route, not its stoichiometry",
     "is limited by the base " + EM + " but by its supply route, not its "
     "stoichiometry",
     "abstract: deleted em dash makes 'limited by the base but by' meaningless"),

    # --- introduction -----------------------------------------------------
    ("the cost penalty sharply increases over the final increments",
     "the cost penalty rises steeply over the final increments",
     "intro: 'sharply increases over' reads as a rate, not a magnitude"),
    ("because the osmotic pressure to be overcome increases.",
     "because the osmotic pressure to be overcome rises with it.",
     "intro: dropped referent leaves 'increases' with nothing to increase with"),
    ("of this work" + EM + "falls below the least work",
     "of this work" + EM + "fall below the least work",
     "intro: subject is 'values', not 'work'"),
    ("lower theoretical energy and has been applied specifically to RO brine "
     "[13], and solar-driven",
     "lower theoretical energy and has been applied specifically to RO brine "
     "[13]; and solar-driven",
     "intro: three-item list with internal commas needs the semicolon"),
    ("from seawater and saltwater feeds [17]",
     "from seawater and brine feeds [17]",
     "intro: [17] is a brine feed; 'saltwater' loses the salinity range"),
    ("which is the development of Section 4.7.",
     "which is the observation Section 4.7 develops.",
     "intro: a section is not a development of an observation"),
    ("Mineral recovery has been studied in brine streams",
     "Mineral recovery has been studied on brine streams",
     "intro: studied on the stream, not inside it"),
    ("has not been reported, and critically, each stage is then tested "
     "against the physical bound it must respect.",
     "has not been reported " + EM + " nor one in which, critically, each "
     "stage is then tested against the physical bound it must respect.",
     "intro: dropping 'in which' asserts the missing work as done"),
    ("returns ions to the stream in which the concentrator is just removed",
     "returns ions to the stream the concentrator has just stripped",
     "intro: sentence no longer parses"),
    ("The conceptual integration of these five published component "
     "technologies rather than a description of an existing installation is "
     "presented in Figure 1.",
     "Figure 1 is the author" + RS + "s conceptual integration of these five "
     "published component technologies rather than a description of an "
     "existing installation, and is presented as such.",
     "intro: restores the authorship disclosure added for the reviewers"),
    ("but to test it: Each subsystem claim",
     "but to test it: each subsystem claim",
     "intro: sentence-case after a colon, as everywhere else"),
    ("realizable mineral value propagates probabilistically rather than "
     "varying one factor at a time, does the integrated architecture",
     "realizable mineral value, propagated probabilistically rather than "
     "varied one factor at a time, does the integrated architecture",
     "intro: it is the value that is propagated, not the combination"),
    ("Under what combination of capital cost, electricity price",
     "And under what combination of capital cost, electricity price",
     "intro: third item of a three-question list"),
    ("per cubic meter of permeate and that the economic case",
     "per cubic meter of permeate, and that the economic case",
     "intro: comma before the third 'that' clause"),

    # --- methods ----------------------------------------------------------
    ("blowdown and operational upsets increase it.",
     "blowdown and operational upsets would raise it.",
     "methods: turns a stated caveat into an assertion about the real plant"),
    ("a partial second pass at an elevated pH of " + EN + "100% of the "
     "permeate adds",
     "a partial second pass at elevated pH treating 35" + EN + "100% of the "
     "permeate adds",
     "methods: gives the pass a pH of 35-100"),
    ("a partial second pass at an elevated pH of 35" + EN + "100% of the "
     "permeate adds",
     "a partial second pass at elevated pH treating 35" + EN + "100% of the "
     "permeate adds",
     "methods: gives the pass a pH of 35-100"),
    ("and increases the concentration of boron to 0.03" + EN + "0.15 mg L-1 "
     "from the worst first pass case",
     "and brings boron to 0.03" + EN + "0.15 mg L-1 from the worst first-pass "
     "case",
     "methods: the second pass reduces boron; this says it raises it"),
    ("underpredicts at saltwater salinities",
     "underpredicts at brine salinities",
     "methods: the correction is for brine salinity, 35-125 g kg-1"),

    # --- results ----------------------------------------------------------
    ("rather than decreasing because lime dosing returns one calcium ion per "
     "magnesium precipitate.",
     "rather than decreasing, because lime dosing returns one calcium ion per "
     "magnesium precipitated.",
     "results: 'decreasing because' inverts the causal attachment"),
    ("The total dissolved solids also increased from 121.7 to 124.8 g L-1 "
     "because the amount of dissolved solids added exceeded the amount of "
     "solids removed.",
     "Total dissolved solids also increase, from 121.7 to 124.8 g L-1, "
     "because the dissolved reagents added exceed the solids removed.",
     "results: past tense for a model output, and it is reagents that are "
     "added"),
    ("add more dissolved mass than the solids removed.",
     "add more dissolved mass than the solids remove.",
     "results: tense"),
    ("The original reported Case E is 10.68 kWh m-3.",
     "The original reported Case E as 10.68 kWh m-3.",
     "Table 2 note: the original reported it, it is not the current value"),
    ("to calcium carbonate, whose original credited at 100% of the market "
     "price.",
     "to calcium carbonate, which the original credited at 100% of the market "
     "price.",
     "results: sentence no longer parses"),
    ("solar interfacial evaporation [4,5,6] removes most of the electricity "
     "term but not the reagent term and substitutes land area for energy.",
     "solar interfacial evaporation [4,5,6] would remove most of the "
     "electricity term but none of the reagent term, and would substitute "
     "land area for energy.",
     "results: asserts an unmodelled substitution as fact"),
    ("With respect to the modeled RO brine (49 bar) and 50% concentrator "
     "recovery, this value is 0.944",
     "At the modeled RO brine (49 bar) and 50% concentrator recovery this "
     "evaluates to 0.944",
     "results: the bound is evaluated at that condition, not with respect "
     "to it"),
    ("than the carbonate step removed does, and calcium is reported to the "
     "crystallizer",
     "than the carbonate step removed, and that calcium reports to the "
     "crystallizer",
     "results: 'reports to' is the process term; the passive loses the "
     "referent"),
    ("Specifically, the precipitation reagents cost a median of $1.70",
     "Costed explicitly, the precipitation reagents come to a median of $1.70",
     "results: 'costed explicitly' is the point of the sentence"),
    ("in a small corner of the sampled space, where Section 4.11 is located.",
     "in a small corner of the sampled space, which Section 4.11 locates.",
     "results: Section 4.11 is not inside the parameter space"),
    ("It excludes distribution and excludes any valorization training.",
     "It excludes distribution and excludes any valorization train.",
     "results: the valorization train, not training"),
    ("This reverses the conclusion that the precipitation reagents explicitly "
     "cost $1.55 m-3",
     "What reverses the conclusion is costing the precipitation reagents "
     "explicitly, worth $1.55 m-3",
     "ablation: inverts the finding the section exists to report"),
    ("the economic reversal is carried out almost entirely by",
     "the economic reversal is carried almost entirely by",
     "ablation: carried by, not carried out by"),
    ("and is any region of the parameter space competitive?",
     "and whether any region of the parameter space is competitive.",
     "attribution: a declarative list of two questions, not a question"),
    ("together with the swing of each command between",
     "together with the swing each commands between",
     "attribution: agreement"),
    ("the cost model is not linear for every input.",
     "the cost model is not linear in every input.",
     "attribution: linear in an input"),
    ("most strongly associated with the net LCOW of the thirteen samples.",
     "most strongly associated with net LCOW, of the thirteen sampled.",
     "Table 10 caption: thirteen sampled parameters, not thirteen samples "
     "(there are 300,000)"),
    ("With respect to the second-law efficiency of the concentrator, the "
     "quantity analyzed in this paper is most closely related to 9 of 14, "
     "with rho = -0.114.",
     "The concentrator second-law efficiency, the quantity this paper "
     "analyzes most closely, ranks 9 of 14 with rho = -0.114.",
     "attribution: 'related to 9 of 14' is not a rank and means nothing"),
    ("determines whether the original specification is admissible at all, a "
     "question that no cost sensitivity can answer while contributing",
     "determines whether the original specification was admissible at all, a "
     "question no cost sensitivity can answer, while contributing",
     "attribution: the original specification is the one already withdrawn"),
    ("where the reagent requirement is eliminated entirely, 0.8 times would "
     "suffice",
     "were the reagent requirement eliminated entirely, 0.8 times would "
     "suffice",
     "admissibility: subjunctive; the requirement has not been eliminated"),
    ("their magnitudes are the specifications that any future version",
     "their magnitudes are the specification any future version",
     "admissibility: one specification, two levers"),
    ("of Mg(OH)2; however, the base arrives" + EM,
     "of Mg(OH)2 however the base arrives" + EM,
     "route D: 'however the base arrives' means regardless of how"),
    ("Route D, in which a base is generated electrochemically",
     "Route D, in which base is generated electrochemically",
     "route D: base as a mass noun, as throughout"),
    ("thus, the amount of reagent carbon becomes -0.94",
     "thus, reagent carbon becomes -0.94",
     "route D: carbon is already a quantity"),
    ("the two routes cost the same amount is 0.061 kWh-1",
     "the two routes cost the same gives $0.061 kWh-1",
     "route D: sentence lost its verb and its dollar sign"),

    # --- discussion and conclusions --------------------------------------
    ("The results of the present analysis suggest that these results are "
     "sensitive",
     "The present analysis suggests those results are sensitive",
     "discussion: 'results ... results' and a lost subject"),
    ("is costed. where the reagent demand implied by Eq. (12) is priced at "
     "bulk industrial rates and exceeds the value",
     "is costed. Where the reagent demand implied by Eq. (12) is priced at "
     "bulk industrial rates, it exceeds the value",
     "discussion: lowercase sentence start, and the clause lost its main verb"),
    ("correction in Eq. (5) is carried out as a swept parameter",
     "correction in Eq. (5) is carried as a swept parameter",
     "limitations: carried as, not carried out as"),
    ("to under 2% of the total SEC; thus, no conclusion in this paper is "
     "reached.",
     "at under 2% of the total SEC, so no conclusion in this paper turns "
     "on it.",
     "limitations: states that the paper reaches no conclusion"),
    ("The residual liquid fraction is modeled and not validated.",
     "The residual liquid fraction is modeled, not validated.",
     "limitations: 'and not validated' reads as a second property"),
    ("operating on real SWRO brine is 60" + EN + "65 g L-1, which fixes the "
     "energy term of the original assumption.",
     "operating on real SWRO brine at 60" + EN + "65 g L-1, which fixes the "
     "energy term the original assumed.",
     "future work: the efficiency is not a salinity"),
    ("which Table 1 predicts, does not close.",
     "which Table 1 predicts does not close.",
     "future work: the comma makes Table 1 predict the train"),
    ("Unlike plants operating at 2.5" + EN + "3.5 kWh m-3, the desalination "
     "stage",
     "Against plants operating at 2.5" + EN + "3.5 kWh m-3, the desalination "
     "stage",
     "conclusions: 'unlike' reverses which side holds the advantage"),
    ("When the base is generated on site, with captured CO2",
     "When the base is generated electrochemically on site, with captured CO2",
     "conclusions: drops the one word that identifies route D"),
    ("the net negative value of the reagent carbon is -0.94 kg CO2 m-3",
     "reagent carbon is made net negative at -0.94 kg CO2 m-3",
     "conclusions: 'net negative value ... is -0.94' says it twice and "
     "parses badly"),
]


def main():
    doc = Document(SRC)
    paras = list(doc.paragraphs)
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                paras.extend(c.paragraphs)

    applied, missed = [], []
    for old, new, why in FIXES:
        hit = False
        for p in paras:
            if replace_in_paragraph(p, old, new):
                hit = True
                break
        (applied if hit else missed).append((old[:58], why))

    doc.save(SRC)

    print("applied %d of %d" % (len(applied), len(FIXES)))
    for frag, why in applied:
        print("   + %s" % why)
    if missed:
        print("\nNOT FOUND (%d):" % len(missed))
        for frag, why in missed:
            print("   ! %s   <- %s" % (frag, why))


if __name__ == "__main__":
    main()
