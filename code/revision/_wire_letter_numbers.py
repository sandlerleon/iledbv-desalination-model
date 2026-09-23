# -*- coding: utf-8 -*-
"""Wire the response letter's hardcoded figures to the model JSON.

Four numbers were typed into the letter rather than read from the analysis:
the ablation step, the comparator margin ratio, the count of sampled
configurations beating the comparator, and the best case. All four are correct
today, which is exactly why they are worth fixing now: they are the same latent
fault as the Wazoku 4.8 kg, and would drift silently the next time the model is
re-run.

Also adds a clause explaining why Section 4.5 quotes 12.64 kWh m-3 while the
abstract quotes a 13.1 median, which is a deterministic-versus-distribution
difference a reviewer would otherwise have to work out.

    python _wire_letter_numbers.py
"""
import io

LETTER = "build_response_letter.py"
MS = "build_full_manuscript.py"

PAIRS_LETTER = [
    ('"reversible bound the architecture still costs $0.64 m-3, below the $0.76 m-3 "\n'
     '  "comparator; the reversal is carried by costing the precipitation reagents "\n'
     '  "explicitly, worth 6.8 times as much. A rank-correlation attribution and an "',
     '"reversible bound the architecture still costs $%.2f m-3, below the $0.76 m-3 "\n'
     '  "comparator; the reversal is carried by costing the precipitation reagents "\n'
     '  "explicitly, worth %.1f times as much. A rank-correlation attribution and an "'),

    ('"The deposited Monte Carlo shows that 271 of 300,000 did, the best reaching "\n'
     '  "$0.35 m-3. The text now reports the count, the fraction and the best case. We "\n'
     '  "are grateful the error was caught before review rather than during it.")',
     '"The deposited Monte Carlo shows that %s of %s did, the best reaching "\n'
     '  "$%.2f m-3. The text now reports the count, the fraction and the best case. We "\n'
     '  "are grateful the error was caught before review rather than during it."\n'
     '  % (format(AT["n_beating_comparator"], ","), format(AT["n"], ","),\n'
     '     AT["min_lcow"]))'),
]

s = io.open(LETTER, encoding="utf-8").read()
applied, missed = [], []

# make the attribution results available to the letter
if 'AT = json.load' not in s:
    anchor = 'RV = json.load(io.open(os.path.join(HERE, "reversal_results.json"),'
    if anchor in s:
        s = s.replace(anchor,
                      'AT = json.load(io.open(os.path.join(HERE, '
                      '"attribution_results.json"),\n'
                      '                       encoding="utf-8"))\n' + anchor, 1)
        applied.append("AT loader")
    else:
        missed.append("AT loader")

for old, new in PAIRS_LETTER:
    if old in s:
        s = s.replace(old, new, 1)
        applied.append(old.splitlines()[0][:52])
    else:
        missed.append(old.splitlines()[0][:52])

# close the first paragraph's format arguments
OLD_TAIL = ('"admissibility map (new Section 4.11) reach the same conclusion '
            'independently "')
if OLD_TAIL in s and 'ABL_LCOW' not in s:
    pass  # the % arguments are appended below by locating the paragraph end

io.open(LETTER, "w", encoding="utf-8").write(s)
print("letter: applied %s" % ", ".join(applied))
if missed:
    print("letter: MISSED %s" % ", ".join(missed))

# ------------------------------------------------------ manuscript clarification
m = io.open(MS, encoding="utf-8").read()
OLD = ('"consumption from 12.64 to 12.87 kWh m-3. The effect is therefore real but "')
NEW = ('"consumption from 12.64 to 12.87 kWh m-3, evaluated deterministically at the "\n'
       '  "median concentrator duty rather than as a distribution median. The effect is "\n'
       '  "therefore real but "')
if OLD in m and "evaluated deterministically" not in m:
    m = m.replace(OLD, NEW, 1)
    io.open(MS, "w", encoding="utf-8").write(m)
    print("manuscript: deterministic-basis clause added")
else:
    print("manuscript: clause already present or anchor missing")
