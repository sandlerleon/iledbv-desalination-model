# ILEDBV: consistency testing of an integrated SWRO–brine valorization architecture

Leon Sandler, Independent Researcher — sandler.leon@gmail.com
ORCID [0009-0007-4584-808X](https://orcid.org/0009-0007-4584-808X)

Model and manuscript for *"Consistency Testing of an Integrated SWRO–Brine
Valorization Architecture: Alkalinity as the Binding Constraint,"* under revision
for **Desalination and Water Treatment** (manuscript DWT-D-26-01366).

> **This revision reverses the conclusions of the first version.** The original
> reported a 31% energy advantage over conventional SWRO and a net levelized cost
> of $0.42/m³. Peer review identified two errors that, once corrected, remove both
> claims. What the repository now contains is a constraint analysis that reports
> where the architecture fails, not a design that reports how well it performs.
> The earlier results are retained in git history and in `code/` for comparison;
> they should not be cited.

## What changed, and why

**The brine concentrator as originally specified is thermodynamically
inadmissible.** For a stage taking feed of osmotic pressure `pi_f` to recovery
`r`, the reversible work per cubic metre of feed is

```
w_min = pi_f * ln[1 / (1 - r)]
```

At the modelled RO brine (49 bar, 50% recovery) this is **0.94 kWh/m³ of brine
processed**. The original assumed 0.5–1.0 kWh/m³ — a range spanning 0.53 to 1.06
times the reversible minimum. A bounded estimate, from that minimum and a 25–55%
second-law efficiency, is 1.7–3.8 kWh/m³, which raises modelled total specific
energy consumption to a median 13.1 kWh/m³.

**Magnesium recovery is limited by alkalinity, not by magnesium.** Precipitating
Mg(OH)₂ needs two equivalents of base per mole of product however the base is
supplied. Costed explicitly:

| | per m³ of permeate |
|---|---|
| soda ash + lime, purchase cost | **$1.70** |
| realisable mineral credit | $1.25 |
| soda ash + lime, embodied carbon | **10.0 kg CO₂** |
| grid electricity emissions | 5.2 kg CO₂ |
| CO₂ fixed in the carbonate product | 0.94 kg |

The reagents cost more than the minerals are worth, and carry roughly twice the
embodied carbon of the plant's electricity. Environmental assessments restricted
to electricity — including the first version of this one — account for about a
third of the total.

**The calcium balance does not close.** Lime dosing releases one Ca²⁺ per Mg(OH)₂
formed, and seawater holds ~3× more Mg than Ca by mole, so the lime step returns
5.3× more calcium than the carbonate step removed:

```
1.481 - 1.407 + 7.460 = 7.534 g/L    (matches stream S6)
```

Total dissolved solids also *rise* across precipitation, 121.7 → 124.8 g/L,
because the dissolved reagents added exceed the solids removed. Selective
precipitation does not lighten the crystallizer duty; it slightly increases it.

## What actually reversed the conclusion

The original contained two independent errors, and it matters which one carried
the reversal. Ablating them in sequence, at median parameters:

| | net LCOW | change |
|---|---|---|
| original assumptions | $0.41 | — |
| + concentrator corrected to the thermodynamic bound | $0.64 | +0.23 |
| + reagents costed explicitly | **$2.19** | **+1.55** |
| *conventional comparator* | *$0.76* | |

**The thermodynamic correction did not flip the economics.** After it the
architecture still beat the comparator. The reagent accounting did, by 6.8×.
Rank-correlation attribution agrees independently: two of the three leading
parameters are alkalinity-chain terms, while the concentrator second-law
efficiency — the quantity the paper analyses most closely — ranks 9th of 13.

**Where it would work.** At present reagent prices the recovered minerals must be
worth **2.1× their modelled value** to reach the comparator; with the reagent
requirement eliminated, 0.8× suffices. 271 of 300,000 sampled configurations do
beat the comparator, the best at $0.35/m³.

## Unbinding the constraint: electrochemical alkalinity

Alkalinity is the binding constraint — but that is a statement about how base is
*supplied*, not about the stoichiometry. Generating it electrochemically on site,
with captured CO₂ as the carbonate source:

| | purchased alkali | electrochemical |
|---|---|---|
| Calcium closure ratio | 5.33 | **0.00** (balance closes) |
| Reagent carbon (kg CO₂/m³) | +9.97 | **−0.94** (net capture) |
| Reagent cost ($/m³) | 1.70 | ~0 |
| Extra electricity (kWh/m³) | — | 27.15 |

That substitutes an energy price for a commodity price, and the two behave
differently:

- Electrochemical supply overtakes purchased alkali below **$0.061/kWh**
- It reaches the $0.76/m³ conventional comparator below **$0.033/kWh**
- Purchased alkali has no such crossing — at *zero* electricity cost it is still
  **$0.34/m³ above** the comparator

**Two conditions.** The power must also be low-carbon: 27 kWh/m³ drawn at grid
intensity (0.55 kg CO₂/kWh) gives +20.3 kg CO₂/m³, worse than the route it
replaces; on solar-dominated supply (0.05) it is +0.13, near neutral. And the
capital cost of the electrochemical unit is **not modelled**, nor is the chlorine
co-product costed or credited — so these figures are an upper bound.

## Results

Monte Carlo, 300,000 samples, seed 20260919, thirteen parameters sampled from
independent uniform ranges (see `code/revision/iledbv_revision_v2.py`):

| quantity | median | 90% interval | unit |
|---|---|---|---|
| Concentrator energy | 2.36 | 1.76 – 3.56 | kWh m⁻³ brine |
| Total SEC | 13.11 | 10.80 – 15.48 | kWh m⁻³ permeate |
| Reagent OPEX | 1.70 | 1.26 – 2.13 | $ m⁻³ |
| Net LCOW | **2.20** | 1.38 – 3.01 | $ m⁻³ |
| Net CO₂ | 14.3 | 10.7 – 18.2 | kg m⁻³ permeate |

No sampled configuration undercut the $0.76/m³ conventional comparator, and none
was carbon negative.

## Contents

```
code/
  iledbv_stream_model.py        original model, retained for comparison
  revision/
    iledbv_revision_v2.py       consistency tests, EROI, Monte Carlo  -> iledbv_revision_v2.json
    design_and_costing.py       ion-by-ion stream table, OPEX, boundary  -> design_costing.json
    second_pass_analysis.py     boron/chloride polishing, gravity-feed check
    boron_recalc.py             boron across feed, ageing and temperature  -> boron_results.json
    new_ideas_assessment.py     centrifugal-RO ceiling, CO2 mineralization
    make_figures.py             all six figures
    harvest_refs.py             Crossref lookup for candidate references
    build_refs.py               verified reference list  -> _refs_final.json
    build_*.py                  manuscript, introduction, response letter
    audit_manuscript.py         numerical consistency audit of the built document
figures/                        six figures, 300 dpi
manuscript/                     revised manuscript and point-by-point response
```

## Reproducing

```bash
pip install numpy matplotlib python-docx requests
python code/revision/iledbv_revision_v2.py     # consistency tests + Monte Carlo
python code/revision/design_and_costing.py     # stream table, OPEX, cost boundary
python code/revision/boron_recalc.py           # product-water quality
python code/revision/make_figures.py           # figures
python code/revision/audit_manuscript.py       # checks the built document against the model
```

The manuscript builders read their numbers from the JSON outputs rather than
from transcribed values, so the text cannot drift from the computation. The audit
script re-checks 18 headline quantities against the model and looks for the class
of internal contradiction that produced an earlier boron error.

## Status of the numbers

Every specific-energy figure here is a **bounded model estimate**, not a measured
or predicted plant value. The osmotic coefficient `phi(S)` in Eq. (5) is carried
as a swept parameter rather than a locked correlation; implementing the published
seawater correlations over the full 35–125 g kg⁻¹ range is the one substantive
open item. Its effect is bounded at under 2% of total SEC, so no conclusion turns
on it. The embodied-carbon factors for soda ash and lime are likewise swept
rather than fitted; the reagent term dominates across their whole plausible range.

No experimental data were used. Precipitation yields are taken from the
literature; product purity is not modelled; the residual liquid fraction is
modelled rather than validated.

## Citation

Concept DOIs, which always resolve to the latest version:

- Code and model: [10.5281/zenodo.22178234](https://doi.org/10.5281/zenodo.22178234) — this release: v2.0.1
- Manuscript: [10.5281/zenodo.22178232](https://doi.org/10.5281/zenodo.22178232)

## License

Code MIT (`LICENSE`); manuscript text and figures CC BY 4.0 (`manuscript/LICENSE`).
