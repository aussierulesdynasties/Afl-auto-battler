#!/usr/bin/env python3
"""
Every season 2012-2025 rated on its own scale (docs/RATING_REBUILD.md §4),
for what the game generates and how players age.

  data/draftee_ranges.csv
      type,positions,attribute,p10,p90,n: each attribute's 10th and 90th
      percentile among real first-season players of that type: a first
      season counts for every type he held in any season 2012-2025, aged
      18-20 at debut, a ruck at any age (director 2026-11-25, question box:
      "Type he held later", "Any debut age").
  data/age_curves.csv
      attribute,age,change,n: the average change a season, by his age in
      the first of two seasons (Endurance, Durability, the technical and
      Footy IQ attributes).

The players of a season are the club lists' (data/legacy/2010s and 2020s
lists.csv) who played that season, each rated by attributes.py on that
season's scale, his body from the list. First season: no AFL games before
it (games_prior 0). Age: Wheelo's age that season.

Types (Director Bible 4.2.30 and C:/kt/interview.md rulings 21-26): each
type's score is its stats a game, each against his AFL position that season,
weighted as TYPES below records his definitions of 2026-11-15; he holds
the type in the top quarter of his position (players with 12+ games) on
that score. A short season leans to his position's
average over 5 games, as the attributes do. A stat Wheelo never kept
(distance run, smothers) is left out, as the attributes leave one out.
High half forward is also a Mid-Forward's type (ruling 26).

Age curves: two seasons in a row with 12+ games each (the league the scale
is set on); Durability, games out of the club's games, over every two
seasons in a row on a list.

    python3 tools/wheelo/league.py            # writes both files
    python3 tools/wheelo/league.py --check    # prints them only
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
import model as M  # noqa: E402
import wheelo as W  # noqa: E402

DATA = A.DATA
LISTS = [os.path.join(DATA, "legacy", "2010s", "lists.csv"), os.path.join(DATA, "legacy", "2020s", "lists.csv")]
FIRST, LAST = W.FIRST, 2025
RANGES_OUT = os.path.join(DATA, "draftee_ranges.csv")
CURVES_OUT = os.path.join(DATA, "age_curves.csv")
DRAFT_AGES = (18, 19, 20)      # a ruck counts at any debut age

# The director's types, 2026-11-15, in the engine's stat keys. 1 = listed;
# 1.5 = "more"/"highly"; 0.75 = "slightly less"; 0.5 = "to a lesser degree".
# accuracy = goals over shots. Each listed idea with two engine stats splits
# its weight between them.
TYPES = {
    "RUCK": {
        "Mobile ruck": {"hitouts": 0.5, "hitouts_adv": 0.5, "clearances": 1, "distance_run": 1,
                        "contested_possessions": 1, "disposals": 1, "marks": 1},
        "Tap ruck": {"hitouts": 0.75, "hitouts_adv": 0.75, "marks": 1.5, "goals": 1.5,
                     "contested_possessions": 1, "clearances": 0.75},
    },
    "MID": {
        "Inside midfielder": {"contested_possessions": 1, "disposals": 1, "clearances": 1,
                              "ground_ball_gets": 1, "pressure_acts": 1, "tackles": 1, "handballs": 1},
        "Wing": {"distance_run": 1, "metres_gained": 0.5, "running_bounces": 0.5, "inside50": 1, "kicks": 1,
                 "effective_disposals": 1, "goal_assists": 0.5, "score_involvements": 0.5,
                 "pressure_acts": 0.5, "marks": 0.5, "tackles": 0.5},
        "Defensive midfielder": {"tackles": 1, "pressure_acts": 1, "marks": 1, "one_percenters": 1,
                                 "clearances": 1},
    },
    "DEF": {
        "Key defender": {"contested_marks": 1, "intercepts": 0.5, "intercept_marks": 0.5, "rebounds": 1,
                         "marks": 1, "clangers": -1},
        "Interceptor": {"intercepts": 0.75, "intercept_marks": 0.75, "metres_gained": 1, "kicks": 1,
                        "effective_disposals": 1},
        "Small defender": {"running_bounces": 1, "kicks": 1, "metres_gained": 1, "effective_disposals": 1,
                           "ground_ball_gets": 1},
    },
    "FWD": {
        "Key forward": {"marks": 1, "contested_marks": 1, "accuracy": 1, "shots": 1, "one_percenters": 0.5,
                        "spoils": 0.5, "distance_run": 1},
        "Small forward": {"goals": 1, "pressure_acts": 1, "effective_disposals": 0.5, "goal_assists": 0.5,
                          "score_involvements": 1, "running_bounces": 1},
        "Pressure forward": {"pressure_acts": 1, "goals": 1, "one_percenters": 0.5, "smothers": 0.5,
                             "running_bounces": 1, "tackles": 1},
        "High half forward": {"distance_run": 1, "metres_gained": 1, "inside50": 1, "running_bounces": 1,
                              "goals": 1, "score_involvements": 1},
    },
}

# The type's line -> the AFL positions tested on it.
LINE_POSITIONS = {
    "RUCK": ["Ruck"],
    "MID": ["Midfielder", "Mid-Forward"],
    "DEF": ["Key Defender", "Gen. Defender"],
    "FWD": ["Gen. Forward", "Key Forward"],
}
EXTRA_POSITIONS = {"High half forward": ["Mid-Forward"]}   # ruling 26

# A type stat -> the Wheelo stat a game. None: never
# kept. Effective disposals: effective kicks plus effective handballs.
STAT = {
    "hitouts": "Hitouts", "hitouts_adv": "HitoutsToAdvantage", "clearances": "TotalClearances",
    "distance_run": None, "contested_possessions": "ContestedPossessions", "disposals": "Disposals",
    "marks": "Marks", "goals": "Goals_Avg", "ground_ball_gets": "GroundBallGets",
    "pressure_acts": "PressureActs", "tackles": "Tackles", "handballs": "Handballs",
    "metres_gained": "MetresGained", "running_bounces": "Bounces", "inside50": "Inside50s", "kicks": "Kicks",
    "effective_disposals": "_eff", "goal_assists": "GoalAssists", "score_involvements": "ScoreInvolvements",
    "one_percenters": "OnePercenters", "contested_marks": "ContestedMarks", "intercepts": "Intercepts",
    "intercept_marks": "InterceptMarks", "rebounds": "Rebound50s", "clangers": "Clangers",
    "accuracy": "_acc", "shots": "ShotsAtGoal", "spoils": "Spoils", "smothers": None,
}
TECHNICAL = ["kicking", "handballing", "marking", "contested_marking", "one_on_one", "contested_ball",
             "goalkicking", "ruck"]
FOOTY_IQ = ["vision", "reading_play", "pressure", "forward_craft"]
CURVE_ATTRS = ["endurance", "durability"] + TECHNICAL + FOOTY_IQ


def type_positions():
    """[(type, line, [positions])] in the director's order."""
    out = []
    for line, types in TYPES.items():
        for name in types:
            out.append((name, line, LINE_POSITIONS[line] + EXTRA_POSITIONS.get(name, [])))
    return out


def list_rows():
    """{year: [list row]} of players who played that season, one row each."""
    out, seen = defaultdict(list), set()
    for path in LISTS:
        for r in A.read(path):
            y = int(r["year"])
            key = (y, r["club"], r["first"], r["last"])
            if FIRST <= y <= LAST and key not in seen:
                seen.add(key)
                out[y].append(r)
    return out


def player_key(r):
    return r.get("draftguru_id") or (r["first"], r["last"], r["dob"])


def rate_season(year: int, rows):
    """[(list row, attribute row)] of a season's players who played, and the
    ones not found in Wheelo."""
    s = A.season(year)
    players, missed = [], []
    for r in rows:
        if float(r.get("games") or 0) <= 0:
            continue
        got = s.find(r["first"], r["last"], r["club"])
        if got is None:
            missed.append("%s %s %s" % (r["club"], r["first"], r["last"]))
            continue
        players.append((r, r, year, got))
    out, _info = A.rate(players, missed, year)
    return out, missed


def stat_value(w: dict, key: str):
    """A Wheelo row's type stat a game (or a rate), and the sample it
    leans over: (value, sample, lean)."""
    g = w.get("Matches") or 0.0
    name = STAT[key]
    if name == "_eff":
        k, h, ke, he = (w.get(x) for x in ("Kicks", "Handballs", "KickingEfficiency", "HandballEfficiency"))
        if None in (k, h, ke, he):
            return None, g, M.SHRINK_GAMES
        return k * ke / 100.0 + h * he / 100.0, g, M.SHRINK_GAMES
    if name == "_acc":
        shots = (w.get("ShotsAtGoal") or 0.0) * g
        goals = (w.get("Goals_Avg") or 0.0) * g
        return (goals / shots if shots > 0 else None), shots, M.SHRINK_SHOTS
    v = w.get(name)
    return v, g, M.SHRINK_GAMES


def type_holders(year: int, rated):
    """{id(attribute row): [types he holds]} for a season."""
    s = A.season(year)
    by_pos = defaultdict(list)
    for w in s.rows:
        if w.get("pos"):
            by_pos[w["pos"]].append(w)
    rated_rows = {id(a["_p"]["row"]): a for _r, a in rated if a["_p"].get("row") is not None}
    held = defaultdict(list)
    for name, line, positions in type_positions():
        weights = {k: wt for k, wt in TYPES[line][name].items() if STAT[k] is not None}
        for pos in positions:
            ws = by_pos.get(pos, [])
            base = [w for w in ws if (w.get("Matches") or 0) >= M.NORM_GAMES]
            if len(base) < 8:
                continue
            leaned = {}
            for k in weights:
                raw = {id(w): stat_value(w, k) for w in ws}
                vals = [raw[id(w)][0] for w in base if raw[id(w)][0] is not None]
                mean = sum(vals) / len(vals)
                sd = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5 or 1.0
                for w in ws:
                    v, n, lean = raw[id(w)]
                    x = mean if v is None else (v * n + lean * mean) / (n + lean)
                    leaned[(id(w), k)] = (x - mean) / sd
            score = {id(w): sum(wt * leaned[(id(w), k)] for k, wt in weights.items()) for w in ws}
            cut = M._pct(sorted(score[id(w)] for w in base), 0.75)
            for w in ws:
                if score[id(w)] >= cut and id(w) in rated_rows:
                    held[id(rated_rows[id(w)])].append(name)
    return held


def pct(vals, q):
    return M._pct(sorted(vals), q)


def main():
    by_year = list_rows()
    seasons = {}
    career = defaultdict(set)    # player -> every type he held, any season
    firsts = []                  # (player, attribute row) of each first season
    found_n, missed_n = 0, 0
    for y in range(FIRST, LAST + 1):
        rated, missed = rate_season(y, by_year[y])
        by_list = {id(a["_p"]["r"]): a for a in rated}
        pairs = [(r, by_list[id(r)]) for r in by_year[y] if id(r) in by_list]
        found_n += len(pairs)
        missed_n += len(missed)
        held = type_holders(y, pairs)
        for r, a in pairs:
            age = a["_p"]["row"].get("Age")
            a["_age"] = int(age) if age is not None else None
            career[player_key(r)].update(held.get(id(a), []))
            if int(float(r.get("games_prior") or 0)) == 0:
                firsts.append((player_key(r), a))
        seasons[y] = {player_key(r): (r, a) for r, a in pairs}
        print("%d: %d rated, %d not found in Wheelo" % (y, len(pairs), len(missed)), file=sys.stderr)

    # Draftee ranges.
    first_season = defaultdict(list)    # type -> [attribute row]
    for key, a in firsts:
        for t in career[key]:
            if a["_age"] in DRAFT_AGES or t in TYPES["RUCK"]:
                first_season[t].append(a)
    ranges = []
    for name, _line, positions in type_positions():
        rows = first_season.get(name, [])
        for k in A.ATTRS:
            vals = [a[k] for a in rows]
            ranges.append({"type": name, "positions": "|".join(positions), "attribute": k,
                           "p10": round(pct(vals, 0.10), 1) if vals else "",
                           "p90": round(pct(vals, 0.90), 1) if vals else "", "n": len(vals)})

    # Age curves.
    deltas = defaultdict(lambda: defaultdict(list))
    club_games = {y: A.season(y).club_games for y in range(FIRST, LAST + 1)}
    for y in range(FIRST, LAST):
        now, nxt = seasons[y], seasons[y + 1]
        for key, (r, a) in now.items():
            if key not in nxt or a["_age"] is None:
                continue
            r2, a2 = nxt[key]
            if a["_p"]["games"] >= M.NORM_GAMES and a2["_p"]["games"] >= M.NORM_GAMES:
                for k in CURVE_ATTRS:
                    if k != "durability":
                        deltas[k][a["_age"]].append(a2[k] - a[k])
    # Durability: every player on a list two seasons in a row, played or not.
    lists = {}
    for y in range(FIRST, LAST + 1):
        lists[y] = {}
        for r in by_year[y]:
            lists[y][player_key(r)] = r
    for path in LISTS:
        for r in A.read(path):
            y = int(r["year"])
            if FIRST <= y <= LAST:
                lists[y].setdefault(player_key(r), r)

    def dur(y, r):
        cg = club_games[y].get(r["club"]) or 0.0
        return M.scale_attr(min(1.0, float(r.get("games") or 0) / cg)) if cg else None

    def age_of(y, r):
        dob = r.get("dob") or ""
        return y - int(dob[:4]) - (1 if dob[5:] > "07-01" else 0) if len(dob) >= 10 else None
    for y in range(FIRST, LAST):
        for key, r in lists[y].items():
            r2 = lists[y + 1].get(key)
            a, b, age = dur(y, r), dur(y + 1, r2) if r2 else None, age_of(y, r)
            if r2 is not None and a is not None and b is not None and age is not None:
                deltas["durability"][age].append(b - a)
    curves = []
    for k in CURVE_ATTRS:
        for age in sorted(deltas[k]):
            v = deltas[k][age]
            curves.append({"attribute": k, "age": age, "change": round(sum(v) / len(v), 2), "n": len(v)})

    print("rated %d player seasons; %d list players not found in Wheelo" % (found_n, missed_n))
    young = [a for _k, a in firsts if a["_age"] in DRAFT_AGES]
    print("first seasons: %d, %d of them aged 18-20, %d of those held a type later" % (
        len(firsts), len(young), sum(1 for k, a in firsts if a["_age"] in DRAFT_AGES and career[k])))
    for name, _line, positions in type_positions():
        print("  %-22s %3d  (%s)" % (name, len(first_season.get(name, [])), ", ".join(positions)))
    if "--check" not in sys.argv:
        for path, rows, cols in ((RANGES_OUT, ranges, ["type", "positions", "attribute", "p10", "p90", "n"]),
                                 (CURVES_OUT, curves, ["attribute", "age", "change", "n"])):
            with open(path, "w", newline="", encoding="utf-8") as fh:
                wr = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
                wr.writeheader()
                wr.writerows(rows)
            if not os.path.exists(path + ".import"):
                with open(path + ".import", "w", newline="\n", encoding="utf-8") as fh:
                    fh.write(A.IMPORT)
            print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
