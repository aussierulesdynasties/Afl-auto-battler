#!/usr/bin/env python3
"""Check data/legacy/fixtures.csv (TODO row 142, Legacy mode phase L6): the real
home-and-away fixtures 1990-2026 that Season.gd plays a real season from.

    python tools/check_legacy_fixtures.py            # report, exit 1 on a hard failure
    python tools/check_legacy_fixtures.py --quiet    # counts only

Hard failures (exit 1), any one of which would make the game draw that season
itself or play it wrong:
- a season missing, or its clubs not the clubs data/legacy/clubs_by_year.csv
  fields that year;
- a season whose round count or games differ from data/season_rules.csv;
- a club playing other than the season's games, or twice in a round, or itself;
- a ground the game does not know (its ground data, or OTHER_GROUNDS below);
- a date outside its season's year, or a duplicate row.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
FIXTURES = os.path.join(DATA, "legacy", "fixtures.csv")
SEASONS = range(1990, 2027)
ALIASES = {"BRB": "BRL", "FOO": "WBD"}  # GameDB.CLUB_CODE_ALIASES
# Grounds the AFL played at that the game has no other data for (no look, weather
# or kick-off row): one-off and regional venues, by the key build.py writes.
OTHER_GROUNDS = {
    "Accor Stadium", "Blacktown International Sportspark", "Bruce Stadium", "Cazaly's Stadium",
    "Hands Oval", "Jiangwan Stadium", "Mars Stadium", "North Hobart Oval", "Riverway Stadium",
    "Sky Stadium", "WACA", "Ikon Park", "Whitten Oval", "Waverley Park", "Football Park",
    "Subiaco Oval", "Victoria Park", "Windy Hill", "Moorabbin Oval",
}


def read_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def known_grounds() -> set:
    """Every ground name the game's own data carries, plus OTHER_GROUNDS."""
    out = set(OTHER_GROUNDS)
    with open(os.path.join(DATA, "grounds.json"), encoding="utf-8") as fh:
        out.update(json.load(fh)["grounds"].keys())
    with open(os.path.join(DATA, "weather_by_venue.json"), encoding="utf-8") as fh:
        out.update(json.load(fh)["venues"].keys())
    with open(os.path.join(DATA, "kickoff_by_venue.json"), encoding="utf-8") as fh:
        out.update(json.load(fh).get("venues", {}).keys())
    out.update(r["ground"] for r in read_csv(os.path.join(DATA, "clubs.csv")) if r.get("ground"))
    return {g for g in out if not g.startswith("_")}


def clubs_in(year: int) -> set:
    """The clubs clubs_by_year.csv fields in `year` (clubs.csv's enter year for a club with no rows)."""
    rows = defaultdict(list)
    for r in read_csv(os.path.join(DATA, "legacy", "clubs_by_year.csv")):
        rows[ALIASES.get(r["code"], r["code"])].append(r)
    out = set()
    for code, rs in rows.items():
        for r in rs:
            to = int(r["to"]) if r["to"] else 9999
            if int(r["from"]) <= year <= to:
                out.add(code)
    for r in read_csv(os.path.join(DATA, "clubs.csv")):
        if r["code"] not in rows and r.get("enter") and int(r["enter"]) <= year:
            out.add(r["code"])
    return out


def shape(year: int) -> dict:
    for r in read_csv(os.path.join(DATA, "season_rules.csv")):
        if int(r["from_year"]) <= year <= int(r["to_year"]):
            return {"rounds": int(r["rounds"]), "games": int(r["games"])}
    return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    fails: list[str] = []
    rows = read_csv(FIXTURES)
    grounds = known_grounds()
    by_year: dict = defaultdict(list)
    seen = set()
    for r in rows:
        key = (r["year"], r["round"], r["home"], r["away"])
        if key in seen:
            fails.append(f"duplicate row {key}")
        seen.add(key)
        by_year[int(r["year"])].append(r)
        if r["ground"] not in grounds:
            fails.append(f"{r['year']} round {r['round']} {r['home']} v {r['away']}: unknown ground '{r['ground']}'")
        if not r["date"].startswith(r["year"] + "-"):
            fails.append(f"{r['year']} round {r['round']} {r['home']} v {r['away']}: date {r['date']} outside the season")
        if r["home"] == r["away"]:
            fails.append(f"{r['year']} round {r['round']}: {r['home']} plays itself")
    for y in SEASONS:
        games = by_year.get(y, [])
        if not games:
            fails.append(f"{y}: no fixture")
            continue
        want = shape(y)
        if not want:
            fails.append(f"{y}: no season shape in season_rules.csv")
            continue
        played = Counter()
        per_round: dict = defaultdict(Counter)
        for g in games:
            played.update([g["home"], g["away"]])
            per_round[int(g["round"])].update([g["home"], g["away"]])
        clubs = clubs_in(y)
        if set(played) != clubs:
            fails.append(f"{y}: clubs {sorted(set(played))} are not clubs_by_year's {sorted(clubs)}")
        rounds = sorted(per_round)
        if rounds != list(range(1, want["rounds"] + 1)):
            fails.append(f"{y}: rounds {rounds[0]}..{rounds[-1]} ({len(rounds)}), season_rules has {want['rounds']}")
        for c, n in played.items():
            if n != want["games"]:
                fails.append(f"{y}: {c} plays {n} games, the season has {want['games']}")
        for rnd, cnt in per_round.items():
            twice = [c for c, n in cnt.items() if n > 1]
            if twice:
                fails.append(f"{y} round {rnd}: {twice} play twice")
        if len(games) * 2 != len(clubs) * want["games"]:
            fails.append(f"{y}: {len(games)} games, {len(clubs)} clubs x {want['games']} / 2 expected")
        if not a.quiet:
            print(f"{y}: {len(games)} games, {len(rounds)} rounds, {len(played)} clubs, {want['games']} each")
    print(f"fixtures: {len(rows)} games, {len(by_year)} seasons, {len(fails)} failures")
    for f in fails:
        print("FAIL " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
