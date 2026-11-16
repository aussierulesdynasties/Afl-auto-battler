#!/usr/bin/env python3
"""
Wheelo seasons (tools/wheelo/seasons/<year>.csv, 2012-2026, from extract.py):
the AFL's own per-game numbers, its 7 positions and the official AFL Player
Rating, read the way the director's rating interview of 2026-11-15 rules
(C:/kt/interview.md, recorded in docs/DIRECTOR_BIBLE.md).

  seasons()            {year: [row]} with every number a float (None when the
                       season does not keep it) and "pos" filled
  apr_ovr(year)        {PlayerId: overall} - ruling 2: a 2012+ player's
                       overall is his official AFL Player Rating against his
                       AFL position that season
  Matcher(year)        finds our player (first, last, club code) in a season

Stdlib only.
"""
from __future__ import annotations

import csv
import os
import re
import unicodedata
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEASON_DIR = os.path.join(HERE, "seasons")
FIRST, LAST = 2012, 2026

# The AFL's 7 positions as Wheelo lists them (ruling 20).
POSITIONS = ["Key Defender", "Gen. Defender", "Midfielder", "Mid-Forward", "Gen. Forward", "Key Forward", "Ruck"]
# The line each position plays on (Ratings.gd keeps lines for selection).
LINE = {"Key Defender": "DEF", "Gen. Defender": "DEF", "Midfielder": "MID", "Mid-Forward": "MID",
        "Gen. Forward": "FWD", "Key Forward": "FWD", "Ruck": "RUC"}
TEXT = {"PlayerId", "Player", "Team", "Position"}

# A season's rating is trusted from 12 games (Ratings.POSITION_NORM_MIN): those
# players set each position's scale; fewer games pull toward his position's
# average, as Ratings.rate_overall's confidence shrink does.
NORM_GAMES = 12
SHRINK_GAMES = 5.0

# The overall scale: a season's rating a game, as standard deviations from
# his position's average that season, at APR_SCALE points each above
# APR_MIDDLE. Measured 2026-11-15 on the 2026 start's 3-season records:
# 63 and 15 keep the list's middle where it is (median 63) and put the
# best record in the league, Marcus Bontempelli's, at 95 - the overall the
# director set for him by hand.
APR_MIDDLE = 63.0
APR_SCALE = 15.0
OVR_MIN, OVR_MAX = 30.0, 99.0

_cache: dict = {}


def _f(v):
    if v is None or v == "" or v == "NA":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def seasons() -> dict:
    """{year: [row]}; row["pos"] is his AFL position that season. Wheelo leaves
    Position blank in 2012 and 2014-2018: those take his listed position in
    the nearest season that has one (the later season on a tie)."""
    if "seasons" in _cache:
        return _cache["seasons"]
    out, listed = {}, defaultdict(dict)
    for y in range(FIRST, LAST + 1):
        path = os.path.join(SEASON_DIR, "%d.csv" % y)
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for r in rows:
            for k in list(r):
                if k not in TEXT:
                    r[k] = _f(r[k])
            if r["Position"]:
                listed[r["PlayerId"]][y] = r["Position"]
        out[y] = rows
    for y, rows in out.items():
        for r in rows:
            d = listed.get(r["PlayerId"], {})
            r["pos"] = r["Position"] or (d[min(d, key=lambda s: (abs(s - y), -s))] if d else "")
    _cache["seasons"] = out
    return out


def apr_ovr(year: int) -> dict:
    """{PlayerId: (overall, games)} for one season. His AFL Player Rating a
    game, pulled toward his position's average when he played few games,
    against the position's 12+ game players that season."""
    key = ("apr", year)
    if key in _cache:
        return _cache[key]
    rows = seasons().get(year, [])
    pool = defaultdict(list)
    for r in rows:
        if r["pos"] and (r["Matches"] or 0) >= NORM_GAMES and r["RatingPoints_Avg"] is not None:
            pool[r["pos"]].append(r["RatingPoints_Avg"])
    scale = {}
    for pos, v in pool.items():
        m = sum(v) / len(v)
        scale[pos] = (m, (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5 or 1.0)
    out = {}
    for r in rows:
        if r["pos"] not in scale or r["RatingPoints_Avg"] is None:
            continue
        m, sd = scale[r["pos"]]
        g = r["Matches"] or 0
        a = (r["RatingPoints_Avg"] * g + SHRINK_GAMES * m) / (g + SHRINK_GAMES)
        out[r["PlayerId"]] = (max(OVR_MIN, min(OVR_MAX, APR_MIDDLE + APR_SCALE * (a - m) / sd)), int(g))
    _cache[key] = out
    return out


# ------------------------------------------------------------- matching --
def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower())


def club_codes() -> dict:
    """Wheelo team name -> our club code (data/clubs.csv names match Wheelo's)."""
    if "clubs" not in _cache:
        with open(os.path.join(ROOT, "data", "clubs.csv"), newline="", encoding="utf-8") as fh:
            m = {r["name"]: r["code"] for r in csv.DictReader(fh)}
        # Wheelo's older team names.
        m.setdefault("Brisbane Lions", m.get("Brisbane", "BRL"))
        m.setdefault("GWS", m.get("Greater Western Sydney", "GWS"))
        _cache["clubs"] = m
    return _cache["clubs"]


# Our lists' given names against Wheelo's (the AFL's) where they differ.
NICK = {"cam": "cameron", "tom": "thomas", "matt": "matthew", "josh": "joshua", "mitch": "mitchell",
        "nick": "nicholas", "sam": "samuel", "zac": "zachary", "zak": "zachary", "jack": "john",
        "nat": "nathan", "ollie": "oliver", "will": "william", "dan": "daniel", "alex": "alexander",
        "jake": "jacob", "lachie": "lachlan", "tim": "timothy", "ed": "edward", "ben": "benjamin",
        "jon": "jonathan", "rob": "robert", "bobby": "robert", "harry": "henry", "charlie": "charles"}


class Matcher:
    """Finds a player's Wheelo row in one season: full name and club, then
    surname and club with the same first initial, then full name alone when
    only one player that season has it."""

    def __init__(self, year: int):
        self.rows = seasons().get(year, [])
        codes = club_codes()
        self.by_full_club, self.by_last_club, self.by_full = defaultdict(list), defaultdict(list), defaultdict(list)
        for r in self.rows:
            # "Josh P. Kennedy", "Robert Hansen Jr": initials and suffixes are not names.
            parts = [t for t in r["Player"].split() if len(t.rstrip(".")) > 1 and t.rstrip(".") not in ("Jr", "Jnr")]
            first, last = (parts[0], " ".join(parts[1:])) if len(parts) > 1 else ("", " ".join(parts))
            c = codes.get(r["Team"], r["Team"])
            r["club"] = c
            self.by_full_club[(norm(first + last), c)].append(r)
            self.by_last_club[(norm(last), c)].append(r)
            self.by_full[norm(first + last)].append(r)

    def find(self, first: str, last: str, club: str):
        f, l = norm(first), norm(last)
        for key in ((f + l, club), (NICK.get(f, f) + l, club)):
            got = self.by_full_club.get(key)
            if got and len(got) == 1:
                return got[0]
        cand = [r for r in self.by_last_club.get((l, club), []) if norm(r["Player"])[:1] == f[:1]]
        if len(cand) == 1:
            return cand[0]
        got = self.by_full.get(f + l) or self.by_full.get(NICK.get(f, f) + l)
        if got and len(got) == 1:
            return got[0]
        return None
