# -*- coding: utf-8 -*-
"""Merge a third-party language edit of manuscript v6 without letting it change the science.

The edited file (Rubriq) is accepted paragraph by paragraph. A paragraph of the edit is taken only
when, after punctuation, articles, function words and routine copy-editing synonyms are normalised,
it carries exactly the same content words, the same numbers, the same currency and unit tokens and
the same subscript and superscript runs as the source. Otherwise the source paragraph is kept.
Reference entries and equation paragraphs are never taken from the edit.

This matters because the edit as supplied introduces changes that are not stylistic: 'brine' becomes
'saltwater', the reagent masses of Section 4.1 become 'solids', '$0.061' loses its dollar sign,
'precipitation train' becomes 'training' and 'vapor' becomes 'vapoour'.

    python merge_language_edit_v6.py <edited.docx>      ->  v6 updated in place, plus a merge report
"""
import io
import os
import re
import sys

from docx import Document
from docx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
REV = os.path.abspath(os.path.join(HERE, "..", "..", "revision2"))
SRC = os.path.join(REV, "ILEDBV_Manuscript_Revised_v6.docx")
REPORT = os.path.join(REV, "v6_language_edit_merge_report.txt")

DASHES = "‐‑‒–—―−"
STOP = set("a an the of is are was were be been being in on at that which and as to for by with from it its their this "
           "these those has have had can could would will may also do does did not no so such then than when where "
           "while whereas there here each both either per into out up".split())
# routine copy-editing swaps that carry no technical content
SYN = {"rises": "increase", "rise": "increase", "raises": "increase", "raise": "increase", "increases": "increase",
       "increased": "increase", "increasing": "increase", "falls": "decrease", "fall": "decrease", "lowers": "decrease",
       "lower": "decrease", "decreases": "decrease", "decreased": "decrease", "about": "approximately",
       "roughly": "approximately", "cheapest": "leastexpensive", "leastexpensive": "leastexpensive",
       "on-site": "onsite", "onsite": "onsite",
       "attainable": "obtainable", "obtainable": "obtainable", "instance": "example", "example": "example",
       "gives": "give", "give": "give", "costed": "cost", "costing": "cost", "costs": "cost", "cost": "cost",
       "saving": "saving", "savings": "saving", "analyzes": "analyze", "analyzed": "analyze",
       "desalination": "desalination"}
WORD = re.compile(r"\$?[0-9]+(?:[.,][0-9]+)*%?|[A-Za-zµα-ω][A-Za-z0-9µα-ω'’]*")
NUM = re.compile(r"\$?\d+(?:[.,]\d+)*%?")


# Paragraphs where the edit changes word order or adds "as follows", "respectively" or an article, and a
# hand review found no change of meaning. Matched on a prefix of the source paragraph.
ACCEPT_REVIEWED = [
    "Symbols are defined in the Nomenclature.",
    "Here Q is volumetric flow, C is concentration",
    "The applied feed pressure, which includes an allowance",
    "The reversible minimum work of separation for a stage",
    "The masses of the two precipitation products",
    "The levelized cost of water, net of the mineral credit",
    "The original included a market absorption check",
    "Fig. 5. Consistency test 3. Net reagent carbon",
]


def norm(s):
    s = re.sub("[%s]" % DASHES, "-", s).replace("’", "'")
    return s


def tokens(text):
    out = []
    for w in WORD.findall(norm(text).lower()):
        w = SYN.get(w, w)
        if w in STOP:
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss") and not any(c.isdigit() for c in w):
            w = w[:-1]
        out.append(w)
    return out


def numbers(text):
    return sorted(NUM.findall(norm(text).replace(" ", "")))


def ptext(p):
    return "".join(t.text or "" for t in p.iter(qn("w:t")))


def script_sig(p):
    sub = sup = 0
    for r in p.iter(qn("w:r")):
        rpr = r.find(qn("w:rPr"))
        if rpr is None or r.find(qn("w:t")) is None:
            continue
        va = rpr.find(qn("w:vertAlign"))
        if va is not None:
            sub += va.get(qn("w:val")) == "subscript"
            sup += va.get(qn("w:val")) == "superscript"
    math = "".join(e.text or "" for e in p.iter("{http://schemas.openxmlformats.org/officeDocument/2006/math}t"))
    return sub, sup, math


def main(edit_path):
    src = Document(SRC)
    edit = Document(edit_path)
    sp = list(src.element.body.iter(qn("w:p")))
    ep = list(edit.element.body.iter(qn("w:p")))
    assert len(sp) == len(ep), "paragraph counts differ: %d vs %d" % (len(sp), len(ep))

    same = accepted = rejected = 0
    report = []
    for i, (a, b) in enumerate(zip(sp, ep)):
        ta, tb = ptext(a), ptext(b)
        if ta == tb:
            same += 1
            continue
        reason = None
        if re.match(r"^\[\d+\] ", ta.strip()):
            reason = "reference entry (verified Crossref record)"
        elif script_sig(a)[2] or script_sig(b)[2]:
            reason = "equation paragraph"
        elif numbers(ta) != numbers(tb):
            reason = "numbers differ: %s" % sorted(set(numbers(ta)) ^ set(numbers(tb)))
        elif any(ta.strip().startswith(x) for x in ACCEPT_REVIEWED):
            reason = None
        elif tokens(ta) != tokens(tb):
            ca, cb = tokens(ta), tokens(tb)
            d = [x for x in ca if x not in cb] + ["+" + x for x in cb if x not in ca]
            reason = "content words differ: %s" % " ".join(d[:12])
        elif script_sig(a)[:2] != script_sig(b)[:2]:
            reason = "subscript or superscript runs differ"
        if reason:
            rejected += 1
            report.append("#%d REJECT (%s)\n    kept : %s\n    edit : %s" % (i, reason, ta[:260], tb[:260]))
        else:
            accepted += 1
            report.append("#%d accept\n    was  : %s\n    now  : %s" % (i, ta[:260], tb[:260]))
            a.getparent().replace(a, b)

    src.save(SRC)
    io.open(REPORT, "w", encoding="utf-8").write(
        "Language edit of manuscript v6: merge report\n"
        "Source: ILEDBV_Manuscript_Revised_v6.docx   Edit: %s\n\n"
        "unchanged paragraphs : %d\naccepted from the edit: %d\nkept from the source  : %d\n\n%s\n"
        % (os.path.basename(edit_path), same, accepted, rejected, "\n\n".join(report)))
    print("unchanged %d | accepted %d | rejected %d" % (same, accepted, rejected))
    print("report:", REPORT)


if __name__ == "__main__":
    main(sys.argv[1])
