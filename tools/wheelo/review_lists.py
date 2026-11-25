#!/usr/bin/env python3
"""
REVIEW.md at the repo root (gitignored): the 2027 lists with their 18
attributes and OVR, then the past starts, for the director's read (rating
rebuild, director 2026-11-25: "dump them cleanly into a gitignored
`REVIEW.md` file in the repo root").

OVR here is the blueprint's starting weights (docs/RATING_REBUILD.md §3) on
his AFL position. Phase 4 measures the weights; until then these are the
starting numbers, and Work Rate has none.

    python3 tools/wheelo/attributes.py && python3 tools/wheelo/review_lists.py
Stdlib only.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import attributes as A  # noqa: E402

OUT = os.path.join(ROOT, "REVIEW.md")
POS = ["Key Defender", "Gen. Defender", "Midfielder", "Mid-Forward", "Gen. Forward", "Key Forward", "Ruck"]
SHORT = {"Key Defender": "KD", "Gen. Defender": "GD", "Midfielder": "Mid", "Mid-Forward": "Mid-Fwd",
         "Gen. Forward": "Gen Fwd", "Key Forward": "KF", "Ruck": "Ruck"}
LABEL = {"speed": "Speed", "endurance": "Endurance", "strength": "Strength", "work_rate": "Work Rate",
         "kicking": "Kicking", "handballing": "Handballing", "marking": "Marking",
         "contested_marking": "Contested marking", "one_on_one": "One-on-one defence",
         "contested_ball": "Contested ball", "goalkicking": "Goalkicking", "ruck": "Ruck", "vision": "Vision",
         "reading_play": "Reading the play", "pressure": "Pressure", "forward_craft": "Forward craft",
         "discipline": "Discipline", "durability": "Durability"}
HEAD = {"speed": "Spd", "endurance": "End", "strength": "Str", "work_rate": "WR", "kicking": "Kick",
        "handballing": "HB", "marking": "Mk", "contested_marking": "CM", "one_on_one": "1v1",
        "contested_ball": "CB", "goalkicking": "GK", "ruck": "Ruck", "vision": "Vis", "reading_play": "Read",
        "pressure": "Pres", "forward_craft": "FC", "discipline": "Disc", "durability": "Dur"}

# docs/RATING_REBUILD.md §3, the starting weights (each position sums to 100).
WEIGHTS = {
    "Key Defender": {"speed": 5, "endurance": 4, "strength": 10, "kicking": 8, "handballing": 3, "marking": 5,
                     "contested_marking": 15, "one_on_one": 25, "reading_play": 15, "pressure": 5, "discipline": 5},
    "Gen. Defender": {"speed": 10, "endurance": 6, "kicking": 15, "handballing": 7, "marking": 10,
                      "contested_marking": 5, "one_on_one": 12, "vision": 4, "reading_play": 18, "pressure": 8,
                      "discipline": 5},
    "Midfielder": {"speed": 6, "endurance": 10, "strength": 6, "kicking": 12, "handballing": 12, "marking": 4,
                   "contested_ball": 22, "goalkicking": 3, "vision": 10, "pressure": 12, "discipline": 3},
    "Mid-Forward": {"speed": 8, "endurance": 5, "kicking": 10, "handballing": 6, "marking": 6, "contested_ball": 12,
                    "goalkicking": 12, "vision": 12, "pressure": 12, "forward_craft": 14, "discipline": 3},
    "Gen. Forward": {"speed": 10, "endurance": 4, "kicking": 5, "marking": 10, "contested_marking": 5,
                     "goalkicking": 18, "vision": 10, "pressure": 14, "forward_craft": 20, "discipline": 4},
    "Key Forward": {"endurance": 4, "strength": 10, "kicking": 5, "marking": 10, "contested_marking": 25,
                    "goalkicking": 20, "pressure": 4, "forward_craft": 18, "discipline": 4},
    "Ruck": {"endurance": 8, "strength": 12, "handballing": 5, "contested_marking": 10, "contested_ball": 15,
             "ruck": 40, "pressure": 5, "discipline": 5},
}

# What each past start's season kept, in plain words (tools/wheelo/attributes.py TABLES_TIERS).
KEPT = {
    "2020": "Wheelo 2019: every stat the 2026 lists use.",
    "2010": "AFL Tables 2009: kicks, handballs, marks, goals, behinds, hit-outs, tackles, frees, contested and "
            "uncontested possessions, clearances, contested marks, marks inside 50, one percenters, inside and "
            "rebound 50s, bounces, goal assists, clangers, time on ground.",
    "2000": "AFL Tables 1999: as 2009 but no goal assists and no time on ground.",
    "1990": "AFL Tables 1989: kicks, handballs, marks, goals, behinds, hit-outs, tackles, frees.",
}


def ovr(row) -> int:
    w = WEIGHTS[row["apos"]]
    return int(round(sum(wt * int(row[k]) for k, wt in w.items()) / 100.0))


def name(r):
    return "%s %s" % (r["first"], r["last"])


def cell(r, k):
    v = r[k]
    if k == "speed":
        return {"gps": v, "20m": v + "s", "est": "~" + v}[r["speed_src"]]
    return v


def load(start):
    with open(os.path.join(A.DATA, A.STARTS[start][4]), newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["ovr"] = ovr(r)
    return rows


def avg(v):
    return sum(v) / len(v) if v else 0.0


def by_ovr(rows):
    return sorted(rows, key=lambda r: (-r["ovr"], name(r)))


def position_averages(say, rows):
    say("| Attribute | " + " | ".join(SHORT[p] for p in POS) + " | All |")
    say("|---|" + "---|" * (len(POS) + 1))
    for k in A.ATTRS + ["ovr"]:
        cells = ["%d" % round(avg([int(r[k]) for r in rows if r["apos"] == p])) for p in POS]
        say("| %s | %s | %d |" % (LABEL.get(k, "OVR"), " | ".join(cells), round(avg([int(r[k]) for r in rows]))))
    say("")
    say("Players by position: " + ", ".join("%s %d" % (SHORT[p], sum(r["apos"] == p for r in rows)) for p in POS) + ".")


def list_table(say, rows, clubs):
    by_club = defaultdict(list)
    for r in rows:
        by_club[r["club"]].append(r)
    for code in sorted(by_club, key=lambda c: clubs.get(c, c)):
        say("")
        say("#### %s" % clubs.get(code, code))
        say("")
        say("| Player | Pos | Yr | OVR | " + " | ".join(HEAD[k] for k in A.ATTRS) + " |")
        say("|---|---|---|---|" + "---|" * len(A.ATTRS))
        for r in by_ovr(by_club[code]):
            say("| %s | %s | %s | **%d** | %s |" % (name(r), SHORT[r["apos"]], r["src"], r["ovr"],
                                                   " | ".join(cell(r, k) for k in A.ATTRS)))
    return len(by_club)


def named_table(say, rows, start):
    say("| Player | Club | Pos | OVR | " + " | ".join(HEAD[k] for k in A.ATTRS) + " |")
    say("|---|---|---|---|" + "---|" * len(A.ATTRS))
    for nm in A.SAMPLE_NAMES[start]:
        for r in rows:
            if name(r) == nm:
                say("| %s | %s | %s | **%d** | %s |" % (nm, r["club"], SHORT[r["apos"]], r["ovr"],
                                                       " | ".join(cell(r, k) for k in A.ATTRS)))


def main():
    rows = load("2026")
    clubs = {}
    with open(os.path.join(ROOT, "data", "clubs.csv"), newline="", encoding="utf-8") as fh:
        for c in csv.DictReader(fh):
            clubs[c["code"]] = c["name"]
    L = []
    say = L.append
    say("# Rating rebuild: the 2027 lists (for the director's read)")
    say("")
    say("Generated by `tools/wheelo/attributes.py` and `tools/wheelo/review_lists.py` from `data/attributes_2026.csv` "
        "(%d listed players). This file is gitignored. The past starts (1990, 2000, 2010, 2020) follow the 2027 "
        "lists." % len(rows))
    say("")
    say("**OVR here is the starting weights** (table below) on his AFL position. Phase 4 measures the real weights "
        "and that table comes back to you here. Work Rate has no starting weight, so it adds nothing to these OVRs yet.")
    say("")
    say("## The six you named")
    say("")
    say("| Player | Club | Position | Speed | Work Rate | OVR |")
    say("|---|---|---|---|---|---|")
    for nm in A.SAMPLE_NAMES["2026"]:
        for r in rows:
            if name(r) == nm:
                sp = r["speed"] + {"gps": " (GPS)", "20m": " (20 m)", "est": " (estimate)"}[r["speed_src"]]
                say("| %s | %s | %s | %s | %s | %d |" % (nm, r["club"], SHORT[r["apos"]], sp, r["work_rate"], r["ovr"]))
    say("")
    n = defaultdict(int)
    for r in rows:
        n[r["speed_src"]] += 1
    say("Speed comes from one of three places. **GPS top speed** (%d players): the straight line you set, 32.5 km/h = "
        "70 up to 36.0 km/h = 98. Pickett 35.4 km/h = 93. Blakey's 36.1 km/h is past 36.0, so it reads 98, not the 96 "
        "your message mentioned. **Combine 20 m sprint, no GPS** (%d players, marked s in the lists): the straight line "
        "you picked, 2.80 s = 90 and 3.10 s = 50. **Neither** (%d players, marked ~): his position's base plus 0 to +10 "
        "from bounces and pressure acts, capped at 68." % (n["gps"], n["20m"], n["est"]))
    say("")
    # Facts below are worked out from the rows, so they stay true on a rebuild.
    ranked = by_ovr(rows)
    mid_ovr = sorted(r["ovr"] for r in rows)[len(rows) // 2]
    top5 = ranked[:5]
    best_mid = next(r for r in ranked if r["apos"] == "Midfielder")
    late = sum(1 for r in rows if r["src"] != "2026")
    full = sum(1 for r in rows if r["durability"] == "99")
    end = {p: round(avg([int(r["endurance"]) for r in rows if r["apos"] == p])) for p in POS}
    say("## Things to know before you read the lists")
    say("")
    say("- **Charlie Comben's 37.8 km/h is gone.** The search found it in a SEN story (5 May 2026) that explains the "
        "reading came from the ambulance taking him to hospital, not from his running. He is back to an estimate.")
    say("- The speed records spell clubs three ways (WBD, Western Bulldogs, blank). Only one name on the lists belongs "
        "to two players, Bailey Williams: the Bulldogs' one now takes his 34.0 km/h GPS (82). West Coast's has a 2018 "
        "combine time with no club on it, so neither is given it and he stays on the estimate.")
    say("- A player with several GPS records takes his best one (Rankine: 36.0 in 2023, 34.3 in 2025, so 98).")
    body = {}
    for f in (A.STARTS["2026"][1], A.STARTS["2026"][3]):
        with open(os.path.join(A.DATA, f), newline="", encoding="utf-8") as fh:
            for b in csv.DictReader(fh):
                body.setdefault((b["club"], b["first"], b["last"]), b.get("weight_kg", ""))
    no_kg = [r for r in rows if not body.get((r["club"], r["first"], r["last"]))]
    late_no_kg = sum(1 for r in no_kg if r["src"] != "2026")
    say("- %d players have no weight on file: %d of the %d rated on a season before 2026 (added to lists after it, "
        "or who missed it) and %d who played in 2026. Their Strength is contested possessions alone, and their Work "
        "Rate is measured against position and height only." % (len(no_kg), late_no_kg, late, len(no_kg) - late_no_kg))
    say("- Durability is the share of his club's games he played that season, so a young player who was not picked "
        "reads low too. %d players played every game and read 99." % full)
    say("- Goal kicking and one-on-ones are percentages, and a player with one shot or one contest has 0% or 100%. "
        "Each player's percentage leans to his position's average until he has 14 shots (10 contests), and the "
        "scale's ends (2nd percentile = 1, 98th = 99) are taken on those leaned percentages, so a one-shot player "
        "no longer sets the top.")
    say("- **At the starting weights the best OVR is %d** (%s), the middle of the league is %d, and the top five are "
        "%s; %s is the best midfielder at %d. Endurance is time on ground, so midfielders who rotate average %d and "
        "key defenders %d. Phase 4's measured weights replace these, and Phase 8 sets the colour cuts and grades on "
        "the new range." % (top5[0]["ovr"], name(top5[0]), mid_ovr,
                            ", ".join("%s (%s %d)" % (name(r), SHORT[r["apos"]], r["ovr"]) for r in top5),
                            name(best_mid), best_mid["ovr"], end["Midfielder"], end["Key Defender"]))
    say("- Work Rate averages about %d, because most players sit near what their position and size predict and a few "
        "big runners stretch the top (the scale's 98th percentile is 99)." % round(avg([int(r["work_rate"]) for r in rows])))
    say("")
    say("## Starting OVR weights (docs/RATING_REBUILD.md §3)")
    say("")
    say("| Attribute | " + " | ".join(SHORT[p] for p in POS) + " |")
    say("|---|" + "---|" * len(POS))
    for k in A.ATTRS:
        say("| %s | %s |" % (LABEL[k], " | ".join(str(WEIGHTS[p].get(k, "")) for p in POS)))
    say("")
    say("## Averages by position")
    say("")
    position_averages(say, rows)
    say("")
    say("## Top five in each attribute")
    say("")
    say("| Attribute | Top five |")
    say("|---|---|")
    for k in A.ATTRS + ["ovr"]:
        top = sorted(rows, key=lambda r: (-int(r[k]), name(r)))[:5]
        say("| %s | %s |" % (LABEL.get(k, "OVR"), ", ".join("%s %s" % (name(r), cell(r, k) if k != "ovr" else r["ovr"])
                                                              for r in top)))
    say("")
    say("## The lists")
    say("")
    say("Columns: Pos = AFL position that season, Yr = the season rated (2026 unless he missed it). "
        + ", ".join("%s = %s" % (HEAD[k], LABEL[k]) for k in A.ATTRS)
        + ". Speed: plain = GPS, s = combine 20 m sprint, ~ = estimate.")
    n_clubs = list_table(say, rows, clubs)

    # ---------------------------------------------------------- past starts
    say("")
    say("# The past starts")
    say("")
    say("Your ruling: each attribute uses the closest stat that season kept, a game, on that season's league scale; "
        "an attribute the season never recorded takes his position's average. Positions are the ones each start "
        "already had (unchanged from the old ratings). Seasons before 2012 have no position data, so those positions "
        "come from matching each player's stats to 2012-2025 players at known positions; the same goes for three "
        "2020 players whose 2018 season has no position on file (Wylie Buzza, Logan Austin, Bradley Lynch).")
    say("")
    say("How I read the gaps (as real football works, none of these change a rule you set):")
    say("")
    say("- Speed: a GPS or combine record counts only if it is from the season rated or earlier, so a 2000 player "
        "does not get a time he ran in 2005. AFL Tables seasons have no GPS; combine 20 m times start in 2000.")
    say("- Marking is marks minus contested marks once a season kept contested marks (1999 on); 1989 is all marks.")
    say("- Ruck is hit-outs, with clearances where the season kept them.")
    say("- Reading the play (intercepts) was never kept before 2012, so every pre-2012 player has his position's "
        "average, taken from 2026's lists because no player of that start has one of his own.")
    say("- Strength: weight for his height, plus contested possessions where the season kept them (1989 did not).")
    say("- Work Rate: bounces, inside and rebound 50s and uncontested possessions where kept; 1989 kept none, so "
        "position average.")
    tables = []
    for start in ("2020", "2010", "2000", "1990"):
        prow = load(start)
        tables.append((start, prow))
        season = A.STARTS[start][0]
        never = [LABEL[k] for k in A.ATTRS if k != "speed" and all(
            len({r[k] for r in prow if r["apos"] == p}) <= 1 for p in POS if any(r["apos"] == p for r in prow))]
        sp = defaultdict(int)
        for r in prow:
            sp[r["speed_src"]] += 1
        ranked = by_ovr(prow)
        say("")
        say("## %s start (season %d): %d players" % (start, season, len(prow)))
        say("")
        say("Stats kept: " + KEPT[start])
        say("")
        say("Position average for everyone (the season never recorded it): %s." % (", ".join(never) or "nothing"))
        say("Speed: %d GPS, %d combine 20 m, %d estimate." % (sp["gps"], sp["20m"], sp["est"]))
        say("")
        say("### Named players")
        say("")
        named_table(say, prow, start)
        say("")
        say("### Top ten by OVR")
        say("")
        say("| # | Player | Club | Pos | OVR |")
        say("|---|---|---|---|---|")
        for i, r in enumerate(ranked[:10], 1):
            say("| %d | %s | %s | %s | %d |" % (i, name(r), r["club"], SHORT[r["apos"]], r["ovr"]))
        say("")
        say("### Averages by position")
        say("")
        position_averages(say, prow)
    for start, prow in tables:
        say("")
        say("## %s start: the lists" % start)
        list_table(say, prow, clubs)
    with open(OUT, "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote REVIEW.md: %d players, %d clubs; past starts %s" % (
        len(rows), n_clubs, ", ".join("%s %d" % (s, len(p)) for s, p in tables)))


if __name__ == "__main__":
    main()
