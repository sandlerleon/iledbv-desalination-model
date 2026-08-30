# ILEDBV: Integrated Subsurface-Intake SWRO, Isobaric Energy Recovery, and Near-ZLD Brine Valorization

Leon Sandler, The Conscious Machine, Independent Researcher — sandler.leon@gmail.com

Code and manuscript for "Process and Techno-Economic Assessment of Integrated
Subsurface-Intake SWRO, Isobaric Energy Recovery, and Near-Zero-Liquid-Discharge
Brine Valorization," prepared for submission to *Desalination* (Elsevier).

## Summary

The manuscript presents ILEDBV, an integrated seawater reverse osmosis (SWRO)
architecture combining subsurface seabed intake, isobaric pressure-exchanger
(PX) energy recovery, and staged brine concentration with selective mineral
precipitation toward a near-zero-liquid-discharge (ZLD)-capable configuration.
A five-case incremental analysis (conventional SWRO → +subsurface intake →
+isobaric PX → +brine concentration → complete near-ZLD system) isolates the
energy contribution of each subsystem, reporting a desalination-stage SEC of
2.73 kWh/m³ (31% below a 3.95 kWh/m³ conventional baseline) that rises to
10.68 kWh/m³ once near-ZLD crystallization is included — confirming that
brine crystallization, not desalination, dominates total system energy
demand.

This repository contains the complete process-model implementation used to
generate every quantitative result in the manuscript, including the
stream-by-stream energy reconciliation (Table 4, Figure 7) that traces
2.73 → 3.65 → 10.68 kWh/m³ directly to the underlying mass/energy-balance
equations, a corrected and sourced global Mg(OH)₂ market-volume figure
(387,580 t/yr, KBV Research 2024) used for the market-absorption check, a
membrane-rejection sensitivity, and a mineral-price sensitivity extending the
manuscript's LCOW tornado analysis.

## Contents

- `manuscript/` — manuscript and cover letter (Word), CC BY 4.0.
- `code/` — Python/NumPy/Matplotlib model, MIT license:
  - `iledbv_stream_model.py` — mass balance, salt balance, RO/PX energy
    model, secondary-concentration and MVC crystallization energy model,
    mineral-recovery stoichiometry, corrected market-volume/LCOW model, and
    the stream-by-stream reconciliation, rejection-sensitivity, and
    mineral-price-sensitivity analyses. Validates against every headline
    number already quoted in the manuscript body (Sections 3-4) to within
    rounding.
  - `graphical_abstract.py` — programmatic (non-generative-AI) process-flow
    graphical abstract, built entirely with matplotlib shapes/text/arrows.
  - `iledbv_results.json` — machine-readable output of the model run (all
    numbers quoted in Section 4 and Table 4 of the manuscript).
  - `figure7_stream_and_rejection.png`, `figure8_mineral_price_tornado.png`,
    `graphical_abstract.png` — regenerated figures from the same run.

Run with `python iledbv_stream_model.py` (requires `numpy`, `matplotlib`);
reproduces every quantitative value in Sections 3-4 exactly (closed-form
calculation, no fitting step). Run `python graphical_abstract.py` to
regenerate the graphical abstract.

**All process parameters (rejections, energy coefficients, prices) are the
same representative literature values already cited in the manuscript text
— nothing here is a new, uncited assumption.** The one substantive
correction made relative to the manuscript's pre-review draft is the global
Mg(OH)₂ market-volume figure: the previous 1.55 million t/yr figure could
not be traced to a citable primary source, and the current, sourced
third-party estimate (387,580 t/yr, KBV Research 2024) is roughly 4× smaller
— which strengthens, not weakens, the manuscript's market-absorption
finding (plant share ≈ 6.2%, not 1.6%).

## License

Code: MIT (see `LICENSE` at repo root — the top-level `LICENSE` file
applies to `code/`). Manuscript: CC BY 4.0 (see `manuscript/LICENSE`).
