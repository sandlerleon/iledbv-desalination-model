# -*- coding: utf-8 -*-
"""Curate the verified reference list for the revised Introduction.

Only DOIs confirmed against Crossref go in. Supplementary-material records
(ACS .s001 style) and preprint shadows of published work are excluded: they are
not citable objects even though a bibliographic search returns them.

    python build_refs.py  ->  _refs_final.txt / _refs_final.json
"""
import io, json, os, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "ref-build/1.0 (mailto:sandler.leon@gmail.com)"}

# doi -> what it is used for in the revision
SELECTED = {
    # --- the comparator fight (R3-A, R4-6)
    "10.1016/j.ecmx.2026.101682": "R3's named paper: lowest measured SWRO SEC, 1.794 kWh/m3",
    "10.1016/j.desal.2025.118654": "modern SWRO SEC across operating plants",

    # --- subsurface intake (R1-1, R3-I)
    "10.1016/j.desal.2014.12.003": "beach well vs open intake, environmental and economic",
    "10.3390/w12092420": "beach well intake as pretreatment, numerical model",
    "10.5004/dwt.2020.24953": "beach well vs open intake operating costs (in this journal)",

    # --- isobaric energy recovery (R1-1)
    "10.1016/j.desal.2006.03.528": "isobaric ERD in SWRO, the standard reference",
    "10.1016/j.desal.2004.06.034": "pressure exchanger calculation model",

    # --- brine concentration and the thermodynamic floor (R1-1, R1-4, T1)
    "10.1016/j.energy.2020.118733": "minimum vs actual energy for brine treatment - anchors Test 1",
    "10.1016/j.desal.2017.04.012": "osmotically assisted RO for high-salinity brine",
    "10.1016/j.desal.2013.04.006": "theoretical energy consumption of seawater desalination",
    "10.1016/j.desal.2021.115069": "MLD/ZLD pathways with enhanced RO, module-scale modelling",

    # --- ZLD / MLD economics (R1-1, R1-5)
    "10.1016/j.seta.2022.102477": "MLD vs ZLD techno-economic and environmental comparison",

    # --- crystallization alternatives (R1-8)
    "10.5541/ijot.673573": "MVC techno-economics for near-ZLD brine management",
    "10.2166/wrd.2024.086": "seeded membrane distillation crystallization, hypersaline",
    "10.1007/s11356-025-36553-7": "eutectic freeze crystallization of RO brine",
    "10.1080/19443994.2015.1030110": "membrane crystallization for salt recovery (in this journal)",

    # --- mineral recovery, yield, purity (R3-E/G/H)
    "10.1016/j.desal.2024.117443": "NaCl effect on yield, purity and polymorph in sequential Ca/Mg precipitation",
    "10.1016/j.desal.2024.117436": "high-purity MgSO4 and vaterite CaCO3 from seawater and brine",
    "10.1016/j.nxsust.2026.100388": "selective Ca/Mg recovery by mineral carbonation and alkaline precipitation",

    # --- the CO2 / alkalinity argument (new contribution)
    "10.1016/j.desal.2023.116629": "Mg recovery from brine via CO2 mineralization - the dosed-CO2 route in the literature",

    # --- seawater property correlations, to lock Eq. (5) (R1-9)
    "10.5004/dwt.2010.1079": "seawater thermophysical property correlations incl. osmotic coefficient",
    "10.1016/j.desal.2016.02.024": "updated seawater property correlations with pressure dependence",

    # --- reviewer 2's solar interfacial evaporation papers (R2-1)
    "10.1002/adfm.76165": "R2 named: spatial decoupling of evaporation and salt crystallization",
    "10.1002/adfm.202512220": "R2 named: tree-inspired 3D biomimetic solar evaporator",
    "10.1016/j.watres.2025.125053": "R2 named: modular gradient-porous evaporator, high-salinity",
}

# named by reviewer 2 as solar interfacial evaporation, but the record is not that
FLAGGED = {
    "10.1016/j.ijbiomac.2026.152880":
        "Reviewer 2 cited this as solar interfacial evaporation. The record is "
        "'Efficient fabrication of cellulose-based hydrogels for effective heavy "
        "metal ion adsorption', which addresses a different subject. Query with "
        "the editor rather than cite.",
}


def fetch(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    m = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=45))["message"]
    auth = []
    for a in m.get("author", []):
        fam = a.get("family", "")
        ini = ".".join(w[0] for w in (a.get("given", "") or "").replace("-", " ").split() if w)
        auth.append(("%s. %s" % (ini, fam)).strip() if ini else fam)
    return {"doi": m.get("DOI"),
            "title": (m.get("title") or [""])[0],
            "authors": auth,
            "journal": (m.get("container-title") or m.get("short-container-title") or [""])[0],
            "year": ((m.get("issued", {}).get("date-parts") or [[None]])[0] or [None])[0],
            "volume": m.get("volume"),
            "pages": m.get("page") or m.get("article-number"),
            "type": m.get("type"),
            "cited_by": m.get("is-referenced-by-count", 0)}


def elsevier_style(r, n):
    a = ", ".join(r["authors"][:6]) + (", et al." if len(r["authors"]) > 6 else "")
    vol = (" %s" % r["volume"]) if r["volume"] else ""
    pg = (" (%s) %s" % (r["year"], r["pages"])) if r["pages"] else " (%s)" % r["year"]
    return "[%d] %s, %s, %s%s%s. https://doi.org/%s" % (n, a, r["title"], r["journal"], vol, pg, r["doi"])


def main():
    out, lines, problems = [], [], []
    for i, (doi, why) in enumerate(SELECTED.items(), 1):
        try:
            r = fetch(doi)
        except Exception as e:
            problems.append("%s : %s" % (doi, e))
            continue
        r["used_for"] = why
        out.append(r)
        time.sleep(0.25)

    out.sort(key=lambda r: (r["authors"][0].split(". ")[-1] if r["authors"] else "zz"))
    for i, r in enumerate(out, 1):
        lines.append(elsevier_style(r, i))
        lines.append("      -> %s   [%s, cited %d]" % (r["used_for"], r["type"], r["cited_by"]))
        lines.append("")

    lines.append("=" * 90)
    lines.append("NOT CITED - flagged for the response letter")
    lines.append("=" * 90)
    for doi, note in FLAGGED.items():
        try:
            r = fetch(doi)
            lines.append("%s" % doi)
            lines.append("   actual record: %s" % r["title"])
            lines.append("   %s" % note)
        except Exception as e:
            lines.append("%s : lookup failed %s" % (doi, e))

    if problems:
        lines.append("")
        lines.append("LOOKUP FAILURES:")
        lines += ["   " + p for p in problems]

    io.open(os.path.join(HERE, "_refs_final.txt"), "w", encoding="utf-8").write("\n".join(lines))
    io.open(os.path.join(HERE, "_refs_final.json"), "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print("verified and formatted: %d references; failures: %d" % (len(out), len(problems)))
    for p in problems:
        print("   FAILED", p)


if __name__ == "__main__":
    main()
