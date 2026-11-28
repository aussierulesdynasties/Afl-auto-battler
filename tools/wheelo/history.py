#!/usr/bin/env python3
"""
Every real player's past seasons on the attributes' scale (docs/RATING_REBUILD.md
mandate 3: OVR is read from the attributes, never stored on another scale).

  data/player_history_2026.csv, data/legacy/<start>/history_<start>.csv
      "seasons" (year:ovr:games): each season's OVR read from that season's
      18 attributes at his AFL position that season (Rating.of_attrs).
  data/legacy/<start>/history_<start>.csv and list_additions_<start>.csv
      "peak", a past start's real peak (Potential.assign, the director's
      "Informed" potential of 2026-11-11): the mean of his two best seasons of
      PEAK_GAMES or more from the data season on, on the same scale. The old
      rating's honours floor (HONOURS_*) is deleted with it (blueprint §1).
  data/legacy/classes.csv and entry_lists.csv
      "peak" the same way: a draft class's from the season after its draft, a
      new club's first list's from its first season (LegacyRollover).

Run it after tools/legacy_1990s/build_start.py and build_rollovers.py, which
write the files with the old scale's peaks. They, the other starts' builders
and tools/build_history.py read each season's ratings here (rated_seasons).

Seasons 2012-2025 are data/league_seasons.csv (league.py). Seasons before
2012 are every AFL Tables player of the season rated by attributes.rate on
that season's scale, as the past starts are (director 2026-11-25, "Nearest
stats"), his body from his nearest list row; an attribute no season kept
takes 2026's position average, as the starts' does. A player is his AFL
Tables slug, the history files' key.

    python3 tools/wheelo/history.py            # rewrites the files
    python3 tools/wheelo/history.py --check    # prints what would change
Stdlib only.
"""
from __future__ import annotations

import csv
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import attributes as A  # noqa: E402
import review_lists as R  # noqa: E402
import wheelo as W  # noqa: E402

B = A.B
DATA = A.DATA
LEG = os.path.join(DATA, "legacy")
FIRST_YEAR, LAST_YEAR = 1987, 2025
PEAK_GAMES = 8                       # tools/legacy_1990s/build_start.py
STARTS = {"1990": 1989, "2000": 1999, "2010": 2009, "2020": 2019}   # start -> data season
LISTS = [os.path.join(LEG, d, "lists.csv") for d in ("1990s", "2000s", "2010s", "2020s")]


def of_attrs(a: dict, apos: str) -> int:
    """Rating.of_attrs: Godot's round() is half away from zero."""
    w = R.WEIGHTS.get(apos, R.WEIGHTS["Midfielder"])
    return int(math.floor(R.stretch(sum(wt * float(a[k]) for k, wt in w.items()) / 100.0) + 0.5))


def slug_of(afltables_id: str) -> str:
    return afltables_id.rsplit("/", 1)[-1].replace(".html", "") if afltables_id else ""


def list_index():
    """From every list row: {slug: league_seasons id}, {slug: [(year, body
    row)]}, {(year, slug): games} and {(year, club, first, last): slug} plus
    {(first, last, dob): slug}. A season he played no AFL game leaves the AFL
    Tables id blank on that year's row: his DraftGuru id finds it on another
    year's. Both name maps take the id most of his rows carry (Nathan Grima's
    2008 row carries Blake Grima's)."""
    ls_id, bodies, games = {}, defaultdict(list), defaultdict(float)
    seen, blank = set(), []
    who = {}
    by_dg, by_name = defaultdict(Counter), defaultdict(Counter)
    for path in LISTS:
        for r in A.read(path):
            s = slug_of(r.get("afltables_id", ""))
            if not s:
                blank.append(r)
                continue
            who[(int(r["year"]), r["club"], r["first"], r["last"])] = s
            if r.get("dob"):
                by_name[(r["first"], r["last"], r["dob"])][s] += 1
            if r.get("draftguru_id"):
                by_dg[r["draftguru_id"]][s] += 1
            ls_id.setdefault(s, r.get("draftguru_id") or "%s_%s_%s" % (r["first"], r["last"], r["dob"]))
            if r.get("height_cm") or r.get("weight_kg"):
                bodies[s].append((int(r["year"]), r))
            key = (int(r["year"]), r["club"], s)
            if key not in seen:
                seen.add(key)
                games[(int(r["year"]), s)] += float(r.get("games") or 0)
    dg_slug = {k: c.most_common(1)[0][0] for k, c in by_dg.items()}
    for r in blank:
        s = dg_slug.get(r.get("draftguru_id") or "")
        if s:
            who.setdefault((int(r["year"]), r["club"], r["first"], r["last"]), s)
            if r.get("dob"):
                by_name.setdefault((r["first"], r["last"], r["dob"]), Counter({s: 1}))
    for k, c in by_name.items():
        who[k] = c.most_common(1)[0][0]
    return ls_id, bodies, games, who


def nearest_body(bodies, s, year):
    got = bodies.get(s)
    if not got:
        return {}
    return min(got, key=lambda yr: (abs(yr[0] - year), yr[0]))[1]


def rate_tables(year: int, bodies, ref: dict) -> dict:
    """{slug: (ovr, games, AFL position)} of every AFL Tables player of a season
    before 2012."""
    s = A.season(year)
    players, slug_by = [], {}
    for pid, row in s.rows.items():
        if pid not in s.pos:
            continue
        sl = slug_of(pid)
        c = B.code(row["club"])
        r = {"first": row["first"], "last": row["last"], "club": c}
        got = {"id": pid, "m": s.m[pid], "pos": s.pos[pid], "games": B.num(row["gm"]) or 0.0, "club": c,
               "club_games": s.club_games.get(c) or 0.0}
        players.append((r, nearest_body(bodies, sl, year), year, got))
        slug_by[id(r)] = sl
    rows, _info = A.rate(players, [], year, ref)
    return {slug_by[id(a["_p"]["r"])]: (of_attrs(a, a["apos"]), int(a["_p"]["games"]), a["apos"]) for a in rows}


def league_rated(ls_id, games) -> dict:
    """{year: {slug: (ovr, games, AFL position)}} for 2012-2025 from
    league_seasons.csv."""
    by_id = defaultdict(dict)
    for r in A.read(os.path.join(DATA, "league_seasons.csv")):
        by_id[int(r["year"])][r["id"]] = (of_attrs(r, r["apos"]), r["apos"])
    out = defaultdict(dict)
    for s, i in ls_id.items():
        for y, got in by_id.items():
            if i in got:
                out[y][s] = (got[i][0], int(games.get((y, s), 0)), got[i][1])
    return out


def rated_seasons(years=None):
    """{year: {slug: (ovr, games, AFL position)}}: every season, or those in
    `years` (2012 on always comes, it is one file)."""
    ls_id, bodies, games, _who = list_index()
    ref = A.build("2026")[1]["means"]
    rated = league_rated(ls_id, games)
    for y in range(FIRST_YEAR, W.FIRST):
        if years is not None and y not in years:
            continue
        rated[y] = rate_tables(y, bodies, ref)
        print("%d: %d rated" % (y, len(rated[y])), file=sys.stderr)
    return rated


def peak(rated, s: str, from_year: int) -> int:
    best = sorted((rated[y][s][0] for y in rated if y >= from_year and s in rated[y]
                   and rated[y][s][1] >= PEAK_GAMES), reverse=True)
    return int(math.floor(sum(best[:2]) / len(best[:2]) + 0.5)) if best else 0


def reseason(cell: str, rated, s: str, report: dict) -> str:
    out = []
    for part in cell.split(";") if cell else []:
        y, ovr, g = part.split(":")
        got = rated.get(int(y), {}).get(s)
        report["seasons"] += 1
        if got is None:
            report["unrated"].append("%s %s" % (s, y))
            continue
        out.append("%s:%d:%s" % (y, got[0], g))
    return ";".join(out)


def rewrite(path, fn, check: bool):
    with open(path, newline="", encoding="utf-8") as fh:
        text = fh.read()
    rd = csv.DictReader(text.splitlines())
    cols, rows = rd.fieldnames, list(rd)
    for r in rows:
        fn(r)
    if not check:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            # Each file keeps its own line ends.
            wr = csv.DictWriter(fh, fieldnames=cols, lineterminator="\r\n" if "\r\n" in text else "\n")
            wr.writeheader()
            wr.writerows(rows)


def main():
    check = "--check" in sys.argv
    rated = rated_seasons()
    samples = {"Marcus_Bontempelli", "Sam_Darcy", "Jason_Dunstall", "Wayne_Carey", "Gary_Ablett", "Chris_Judd"}
    report = {"seasons": 0, "unrated": []}

    def hist(start):
        def fn(r):
            old = r["seasons"]
            r["seasons"] = reseason(old, rated, r["slug"], report)
            if start is not None:
                old_peak = r.get("peak", "")
                p = peak(rated, r["slug"], STARTS[start])
                r["peak"] = str(p) if p else ""
                if r["slug"] in samples:
                    print("  %s %s: %s -> %s; peak %s -> %s" % (start, r["slug"], old, r["seasons"], old_peak,
                                                               r["peak"]))
            elif r["slug"] in samples:
                print("  2026 %s: %s -> %s" % (r["slug"], old, r["seasons"]))
        return fn

    rewrite(os.path.join(DATA, "player_history_2026.csv"), hist(None), check)
    for start in STARTS:
        rewrite(os.path.join(LEG, start, "history_%s.csv" % start), hist(start), check)
    adds = {"n": 0, "peaks": 0}
    who = list_index()[3]
    for start in STARTS:
        def add_fn(r, start=start):
            # His AFL Tables page in the sources, else his row on the
            # start's list, else his name and birth date on any year's.
            sl = next((slug_of(u.strip()) for u in r.get("source_url", "").split("|")
                       if "/stats/players/" in u), "")                 or who.get((int(start), r["club"], r["first"], r["last"]), "")                 or who.get((r["first"], r["last"], r.get("dob", "")), "")
            adds["n"] += 1
            if sl:
                p = peak(rated, sl, STARTS[start])
                r["peak"] = str(p) if p else ""
                adds["peaks"] += 1 if p else 0
            else:
                r["peak"] = ""
        rewrite(os.path.join(LEG, start, "list_additions_%s.csv" % start), add_fn, check)
    # The legacy careers' real draft classes and new clubs' first lists.
    legacy = {"n": 0, "peaks": 0}

    def legacy_fn(after):
        def fn(r):
            sl = who.get((r["first"], r["last"], r.get("dob", "")), "")
            p = peak(rated, sl, int(r["year"]) + after) if sl else 0
            r["peak"] = str(p) if p else ""
            legacy["n"] += 1
            legacy["peaks"] += 1 if p else 0
        return fn

    rewrite(os.path.join(LEG, "classes.csv"), legacy_fn(1), check)
    rewrite(os.path.join(LEG, "entry_lists.csv"), legacy_fn(0), check)
    print("history seasons: %d, %d not rated (dropped): %s" % (
        report["seasons"], len(report["unrated"]), "; ".join(report["unrated"][:30])))
    print("list additions: %d, %d with a peak" % (adds["n"], adds["peaks"]))
    print("classes and first lists: %d, %d with a peak" % (legacy["n"], legacy["peaks"]))
    if not check:
        print("rewrote the history and list-addition files")


if __name__ == "__main__":
    main()
