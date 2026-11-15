#!/usr/bin/env python3
"""
Write docs/research/WHEELO_WEIGHTS.md: how much each skill counts in a
pre-2012 player's overall, by AFL position and by what each era recorded
(ruling 19, interview 2026-11-15: the weights are measured on 2012+ and shown
to the director before they are used).

    python3 tools/wheelo/weights_report.py
Stdlib only.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import seasons_rated as S  # noqa: E402

NAMES = {"kicking": "Kicking", "handballing": "Handballing", "contested_marking": "Contested marking",
         "uncontested_marking": "Uncontested marking", "contested": "Contested ball", "pressure": "Pressure",
         "intercept": "Intercepting", "speed": "Speed", "carry": "Carry", "goalkicking": "Goalkicking",
         "accuracy": "Accuracy", "creating": "Creating", "ruck": "Ruck", "discipline": "Discipline",
         "durability": "Durability", "star": "Star"}
POS_ORDER = ["Key Defender", "Gen. Defender", "Midfielder", "Mid-Forward", "Gen. Forward", "Key Forward", "Ruck"]
POS_WORDS = {"Gen. Defender": "General defender", "Gen. Forward": "General forward"}
ERAS = [
    ("1987", "1987-1997", "kicks, marks, handballs, goals, behinds, hit-outs, tackles and free kicks. "
     "No contested possessions, contested marks, clearances, inside 50s, rebounds or bounces, so Contested ball, "
     "Contested marking, Intercepting, Carry and Creating sit at the position's average and count for nothing, "
     "and Uncontested marking (marks less contested marks) is every mark."),
    ("1998", "1998", "the 1987 list plus rebound 50s, inside 50s, clearances and clangers. Still no contested "
     "marks, so Uncontested marking is every mark."),
    ("1999", "1999-2002", "everything AFL Tables keeps except goal assists and time on ground."),
    ("2003", "2003-2011", "everything AFL Tables keeps. Still no pressure acts, metres gained, intercept "
     "possessions, one-on-ones, coaches votes or speed (those start in 2012)."),
]


def main():
    fits = S.fits()
    out = ["# Pre-2012 overall: how much each skill counts", "",
           "_Ruling 19 (director, 2026-11-15): before 2012 there is no AFL Player Rating, so a season's overall "
           "is built from its skills, weighted by what the AFL Player Rating rewarded in 2012-2025. Written by "
           "tools/wheelo/weights_report.py from tools/wheelo/fit.py._", "",
           "How it was measured: every 2012-2025 season was rated twice, once from Wheelo (the AFL Player "
           "Rating against his position) and once from only the stats a past era recorded. For each position, "
           "the weights are the mix of skills that best matches the AFL Player Rating; no skill may count "
           "against a player. \"Match\" is how closely that mix follows the real rating (1 = exactly).", ""]
    for tier, label, kept in ERAS:
        out += ["## %s" % label, "", "Recorded: %s" % kept, "",
                "| Position | Match | Skills, most important first |", "|---|---|---|"]
        for pos in POS_ORDER:
            f = fits[tier].get(pos)
            if not f:
                continue
            parts = ["%s %d%%" % (NAMES[k], round(s * 100))
                     for k, s in sorted(f["share"].items(), key=lambda x: -x[1]) if s >= 0.015]
            out.append("| %s | %.2f | %s |" % (POS_WORDS.get(pos, pos), f["r"], ", ".join(parts)))
        out.append("")
    path = os.path.join(ROOT, "docs", "research", "WHEELO_WEIGHTS.md")
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
