# -*- coding: utf-8 -*-
"""Find and verify the references the revised Introduction needs.

Three reviewers asked for a proper literature review. Every candidate is looked
up in Crossref and written out with its full record so each can be checked before
it goes in the paper; nothing is cited from memory.

    python harvest_refs.py   ->  _refs_found.txt  (+ _refs.json)
"""
import io, json, os, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "ref-harvest/1.0 (mailto:sandler.leon@gmail.com)"}

# (a) named by reviewers - these must appear in the revision
BY_DOI = {
    "R3 low-SEC SWRO plant": "10.1016/j.ecmx.2026.101682",
}

BY_SEARCH = {
    # reviewer 2's four solar interfacial evaporation papers, by journal/volume/page
    "R2 solar evap AFM e76165":
        "Advanced Functional Materials 2026 volume 36 e76165 solar interfacial evaporation",
    "R2 solar evap AFM e12220":
        "Advanced Functional Materials 2026 volume 36 e12220 solar evaporation hypersaline",
    "R2 solar evap Water Research 125053":
        "Water Research 2026 volume 290 125053 solar interfacial evaporation brine",
    "R2 solar evap IJBM 152880":
        "International Journal of Biological Macromolecules 2026 volume 370 152880 solar evaporation",

    # the five technologies the Introduction has to review
    "SWRO energy state of the art":
        "seawater reverse osmosis specific energy consumption state of the art review",
    "SWRO thermodynamic limit":
        "energy efficiency of seawater desalination thermodynamic minimum reverse osmosis",
    "Subsurface intake review":
        "subsurface intake beach well seawater desalination review feasibility",
    "Subsurface intake pretreatment":
        "beach well intake versus open ocean intake pretreatment SDI desalination",
    "Pressure exchanger energy recovery":
        "isobaric pressure exchanger energy recovery device seawater reverse osmosis efficiency",
    "ERD review":
        "energy recovery devices in reverse osmosis desalination review",
    "Brine concentration high salinity":
        "high salinity brine concentration reverse osmosis osmotically assisted review",
    "Osmotically assisted RO":
        "osmotically assisted reverse osmosis hypersaline brine concentration energy",
    "NF brine treatment":
        "nanofiltration desalination brine divalent ion separation selectivity",
    "Minimum energy brine concentration":
        "minimum energy consumption brine concentration desalination thermodynamic analysis",
    "ZLD review":
        "zero liquid discharge desalination brine review technologies cost energy",
    "MLD ZLD cost":
        "minimal liquid discharge zero liquid discharge desalination economic assessment",
    "MVC crystallizer energy":
        "mechanical vapor compression crystallizer energy consumption brine",
    "Membrane distillation brine":
        "membrane distillation crystallization hypersaline brine energy",
    "Eutectic freeze crystallization":
        "eutectic freeze crystallization brine treatment energy recovery salts",
    "Mineral recovery from brine":
        "mineral recovery from desalination brine magnesium calcium review resource",
    "Mg(OH)2 from seawater brine":
        "magnesium hydroxide recovery from seawater desalination brine precipitation",
    "Selective precipitation brine":
        "selective precipitation calcium magnesium desalination brine purity",
    "Lithium from brine":
        "lithium recovery from seawater desalination brine review",
    "Brine valorization techno-economic":
        "techno-economic assessment brine valorization desalination mineral recovery",
    "CO2 mineralization brine":
        "carbon dioxide mineralization desalination brine alkalinity calcium carbonate",
    "Alkalinity carbon cost":
        "life cycle assessment sodium hydroxide lime embodied carbon chemical production",
    "Boron removal second pass":
        "boron removal seawater reverse osmosis second pass pH elevated",
    "Concentration polarization RO":
        "concentration polarization reverse osmosis membrane mass transfer modeling",
    "Desalination environmental impact":
        "environmental impact of desalination brine discharge review",
}


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=45))


def rec(m):
    return {
        "doi": m.get("DOI"),
        "title": (m.get("title") or [""])[0],
        "authors": [("%s %s" % (a.get("family", ""), "".join(
            w[0] for w in (a.get("given", "") or "").replace("-", " ").split() if w))).strip()
            for a in m.get("author", [])][:12],
        "journal": (m.get("short-container-title") or m.get("container-title") or [""])[0],
        "year": ((m.get("issued", {}).get("date-parts") or [[None]])[0] or [None])[0],
        "volume": m.get("volume"),
        "pages": m.get("page") or m.get("article-number"),
        "type": m.get("type"),
        "cited_by": m.get("is-referenced-by-count", 0),
    }


def main():
    found, lines = {}, []

    for tag, doi in BY_DOI.items():
        try:
            m = rec(get("https://api.crossref.org/works/" + urllib.parse.quote(doi)))
            found[tag] = [m]
        except Exception as e:
            found[tag] = []
            lines.append("!! %s : DOI lookup failed (%s)" % (tag, e))
        time.sleep(0.3)

    for tag, q in BY_SEARCH.items():
        url = ("https://api.crossref.org/works?rows=3&select=DOI,title,author,"
               "short-container-title,container-title,issued,volume,page,article-number,"
               "type,is-referenced-by-count&query.bibliographic=" + urllib.parse.quote(q))
        try:
            found[tag] = [rec(x) for x in get(url)["message"]["items"]]
        except Exception as e:
            found[tag] = []
            lines.append("!! %s : search failed (%s)" % (tag, e))
        time.sleep(0.4)

    for tag, items in found.items():
        lines.append("=" * 96)
        lines.append(tag)
        lines.append("=" * 96)
        if not items:
            lines.append("   nothing returned")
        for m in items:
            lines.append("   %s" % m["title"][:110])
            lines.append("      %s" % ", ".join(m["authors"][:6]))
            lines.append("      %s %s; vol %s: %s   cited %s   doi %s"
                         % (m["journal"], m["year"], m["volume"], m["pages"],
                            m["cited_by"], m["doi"]))
            lines.append("")

    io.open(os.path.join(HERE, "_refs_found.txt"), "w", encoding="utf-8").write("\n".join(lines))
    io.open(os.path.join(HERE, "_refs.json"), "w", encoding="utf-8").write(
        json.dumps(found, ensure_ascii=False, indent=1))
    n = sum(len(v) for v in found.values())
    print("queries: %d   candidate records retrieved: %d" % (len(found), n))
    print("wrote _refs_found.txt and _refs.json")


if __name__ == "__main__":
    main()
