#!/usr/bin/env python3
"""Trim Wheelo Ratings season files to the columns the game's ratings use.

Source: https://www.wheeloratings.com/src/afl_stats/player_stats/afl/<year>.json
(the stats sit under "Data", one list per column, per-game averages except
Matches, Goals_Total, CoachesVotes_Total, BnFVotes_Total and xScoreShots).

    python tools/wheelo/extract.py C:/kt/wheelo     # folder of <year>.json

Writes tools/wheelo/seasons/<year>.csv. Columns a season does not publish
(Position before 2019 bar 2013, the 2021+ metres and expected-score columns)
are left blank, never filled.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COLS = [
    "PlayerId", "Player", "Team", "Position", "Age", "Matches", "RatingPoints_Avg",
    "CoachesVotes_Total", "TimeOnGround", "Kicks", "Handballs", "Disposals",
    "KickingEfficiency", "HandballEfficiency", "KickMetresGainedPerKick",
    "HandballMetresGained", "MetresGained", "Inside50s", "Rebound50s", "Clangers",
    "ContestedPossessions", "ContestedPossessionRate", "Intercepts", "GroundBallGets",
    "HardBallGets", "TotalClearances", "Marks", "ContestedMarks", "MarksInside50",
    "InterceptMarks", "MarksOnLead", "Goals_Total", "Goals_Avg", "Behinds",
    "ShotsAtGoal", "GoalAssists", "ScoreInvolvements", "ScoreLaunches",
    "ContestOffensiveOneOnOnes", "ContestOffensiveWinPercentage",
    "ContestDefensiveOneOnOnes", "ContestDefensiveLossPercentage", "xScoreShots",
    "xScoreRatingPerShot", "Tackles", "TacklesInside50", "PressureActs",
    "PressureActsDefensiveHalf", "Spoils", "Bounces", "OnePercenters", "FreesFor",
    "FreesAgainst", "Hitouts", "HitoutsWinPercentage", "HitoutsToAdvantage",
]


def main(src):
    out_dir = os.path.join(HERE, "seasons")
    os.makedirs(out_dir, exist_ok=True)
    for name in sorted(os.listdir(src)):
        if not name.endswith(".json"):
            continue
        year = name[:-5]
        data = json.load(open(os.path.join(src, name), encoding="utf-8"))["Data"]
        n = len(data["Player"])
        with open(os.path.join(out_dir, year + ".csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(COLS)
            for i in range(n):
                row = []
                for c in COLS:
                    v = data[c][i] if c in data else ""
                    if v is None or v == "NA":
                        v = ""
                    row.append(v)
                w.writerow(row)
        print(year, n)


if __name__ == "__main__":
    main(sys.argv[1])
