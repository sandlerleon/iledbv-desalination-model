# -*- coding: utf-8 -*-
"""Pre-submission structural check of the built manuscript.

Equations: numbered (1)..(N) without gaps, each cited in the text.
Tables:    captions numbered 1..N in order, each cited before or at its caption.
Figures:   every figure file in figures/ cited in the text.
References: [1]..[N] listed without gaps, each cited at least once, and each DOI
           resolved against Crossref with its title compared to the listed one.

    python verify_manuscript_structure.py [--no-doi]
"""
import difflib
import os
import re
import sys

import requests
from docx import Document
from docx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DOC = os.path.join(REPO, "manuscript", "ILEDBV_Manuscript_Revised_v4.docx")


def blocks(doc):
    out = []
    for el in doc.element.body.iterchildren():
        if el.tag == qn("w:p"):
            out.append(("p", "".join(t.text or "" for t in el.iter(qn("w:t")))))
        elif el.tag == qn("w:tbl"):
            out.append(("t", " | ".join("".join(t.text or "" for t in c.iter(qn("w:t")))
                                        for c in el.iter(qn("w:tc")))))
    return out


def expand(s):
    nums = set()
    for part in re.split(r"[,;]", s):
        part = part.strip()
        m = re.match(r"^(\d+)\s*[-–]\s*(\d+)$", part)
        if m:
            nums.update(range(int(m.group(1)), int(m.group(2)) + 1))
        elif part.isdigit():
            nums.add(int(part))
    return nums


def main():
    doc = Document(DOC)
    bl = blocks(doc)
    ref_start = next(i for i, (k, t) in enumerate(bl) if k == "p" and t.strip() == "References")
    body = bl[:ref_start]
    refs = [t for k, t in bl[ref_start + 1:] if re.match(r"^\[\d+\]", t)]
    text = "\n".join(t for _, t in body)
    problems = []

    # ---- equations
    eq_nums = [int(m) for m in re.findall(r"\s\((\d+)\)\s*$", text, re.M)]
    print("equations numbered:", eq_nums)
    if eq_nums != list(range(1, len(eq_nums) + 1)):
        problems.append("equation numbering not sequential: %s" % eq_nums)
    cited_eq = set()
    for m in re.finditer(r"Eqs?\.\s*\(([^)]*)\)((?:\s*(?:,|and|–|-)\s*\(\d+\))*)", text):
        cited_eq |= expand(m.group(1))
        tail = [int(x) for x in re.findall(r"\((\d+)\)", m.group(2))]
        cited_eq |= set(tail)
        if tail and re.match(r"\s*[–-]", m.group(2)) and m.group(1).strip().isdigit():
            cited_eq |= set(range(int(m.group(1)), tail[0] + 1))
    for m in re.finditer(r"Equations?\s*((?:\(\d+\)[\s,and–-]*)+)", text):
        nums = [int(x) for x in re.findall(r"\((\d+)\)", m.group(1))]
        if "–" in m.group(1) and len(nums) == 2:
            cited_eq |= set(range(nums[0], nums[1] + 1))
        cited_eq |= set(nums)
    miss = [n for n in eq_nums if n not in cited_eq]
    print("equations never cited:", miss)
    if miss:
        problems.append("equations never cited in text: %s" % miss)

    # ---- tables
    caps = [(i, int(m.group(1))) for i, (k, t) in enumerate(body) if k == "p"
            for m in [re.match(r"^Table (\d+)\.", t)] if m]
    tnums = [n for _, n in caps]
    print("table captions:", tnums)
    if tnums != list(range(1, len(tnums) + 1)):
        problems.append("table numbering: %s" % tnums)
    for i, n in caps:
        before = "\n".join(t for k, t in body[:i + 1] if not re.match(r"^Table %d\." % n, t))
        after = "\n".join(t for _, t in body[i + 1:])
        pat = r"Tables?\s[\d, and–-]*\b%d\b" % n
        if not re.search(pat, before + after):
            problems.append("Table %d never cited" % n)
    print("tables cited:", [n for _, n in caps if not any("Table %d never" % n in p for p in problems)])

    # ---- figures
    figs = sorted(set(int(m) for m in re.findall(r"figure(\d+)_", " ".join(os.listdir(os.path.join(REPO, "figures"))))))
    cited_fig = set(int(m) for m in re.findall(r"Fig(?:ure|\.)\s*(\d+)", text))
    print("figure files:", figs, " cited in text:", sorted(cited_fig))
    unc = [n for n in figs if n not in cited_fig]
    if unc:
        problems.append("figures with files but no in-text citation: %s" % unc)

    # ---- references
    rnums = [int(re.match(r"^\[(\d+)\]", r).group(1)) for r in refs]
    if rnums != list(range(1, len(rnums) + 1)):
        problems.append("reference list numbering: %s" % rnums)
    cited = set()
    for m in re.finditer(r"\[([\d,\s–-]+)\]", text):
        cited |= expand(m.group(1))
    never = [n for n in rnums if n not in cited]
    beyond = sorted(n for n in cited if n not in rnums)
    print("references listed: %d, cited: %d, never cited: %s, cited but not listed: %s"
          % (len(rnums), len(cited & set(rnums)), never, beyond))
    if never:
        problems.append("references never cited: %s" % never)
    if beyond:
        problems.append("citations with no reference entry: %s" % beyond)

    if "--no-doi" not in sys.argv:
        for r in refs:
            n = int(re.match(r"^\[(\d+)\]", r).group(1))
            m = re.search(r"https://doi\.org/(\S+)$", r.strip())
            if not m:
                problems.append("[%d] has no DOI" % n)
                continue
            doi = m.group(1).rstrip(".")
            try:
                j = requests.get("https://api.crossref.org/works/" + doi, timeout=30,
                                 headers={"User-Agent": "iledbv-verify (mailto:sandler.leon@gmail.com)"})
                if j.status_code != 200:
                    problems.append("[%d] DOI %s -> HTTP %d" % (n, doi, j.status_code))
                    print("  [%d] %s HTTP %d" % (n, doi, j.status_code))
                    continue
                title = (j.json()["message"].get("title") or [""])[0]
                norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
                ratio = difflib.SequenceMatcher(None, norm(title), norm(r), autojunk=False).find_longest_match(
                    0, len(norm(title)), 0, len(norm(r))).size / max(1, len(norm(title)))
                flag = "" if ratio > 0.9 else "   <-- title mismatch"
                print("  [%d] %s ok (title match %.2f)%s" % (n, doi, ratio, flag))
                if flag:
                    problems.append("[%d] Crossref title '%s' does not match" % (n, title))
            except Exception as e:
                problems.append("[%d] DOI lookup failed: %s" % (n, e))

    print("\nPROBLEMS" if problems else "\nNo problems found.")
    for p in problems:
        print("  -", p)


if __name__ == "__main__":
    main()
