#!/usr/bin/env python3
"""
Every start's ratings against the real record (bug bash, 2026-11-23: "player
ratings ... jon patton 99 pot is INSANE", "gun players were in the mid 70s").

Reads the dumps tools/ratings_dump.gd writes (one CSV per start, the players as
a new career opens them) and checks them against the honours the data holds
(data/legacy/honours: All-Australian, club best-and-fairest; Brownlow votes
from AFL Tables' season rows):

  honoured now   the data season's All-Australians and club champions and its
                 Brownlow top 10: where they rate (median, lowest, under 80)
  ceilings       how many 95+ and 90+ potentials, and how many of those men
                 never had an honour in their real careers (a dud's ceiling)

    godot --headless --path . --script tools/ratings_dump.gd -- <dir>
    python3 tools/ratings_check.py <dir> [<dir after> ...]
Stdlib only.
"""
from __future__ import annotations

import csv
import glob
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEG = os.path.join(ROOT, "data", "legacy")
STARTS = {"1990": 1989, "2000": 1999, "2010": 2009, "2020": 2019, "2026": 2025}
CODE = {"BRB": "BRL", "FOO": "WBD", "KAN": "NTH"}


def norm(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())


def code(c):
    return CODE.get(c, c)


def honours():
    """year -> {"aa": {(first initial, last, club)}, "bf": {...}, "br10": {...}}, plus
    every man (first+last) with any honour in any season."""
    by_year = defaultdict(lambda: defaultdict(set))
    ever = set()
    for fn, kind in (("all_australian.csv", "aa"), ("club_bf.csv", "bf"), ("team_of_the_year.csv", "aa")):
        with open(os.path.join(LEG, "honours", fn), newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                k = (norm(r["first"])[:1], norm(r["last"]), code(r["club"]))
                by_year[int(r["year"])][kind].add(k)
                ever.add((norm(r["first"]), norm(r["last"])))
    for path in glob.glob(os.path.join(LEG, "*s", "season_stats.csv")):
        votes = defaultdict(list)
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                try:
                    v = float(r.get("br") or 0)
                except ValueError:
                    v = 0
                if v > 0:
                    votes[int(r["year"])].append((v, norm(r["first"]), norm(r["last"]), code(r["club"])))
        for y, rows in votes.items():
            rows.sort(reverse=True)
            for v, f, l, c in rows:
                place = 1 + sum(1 for o in rows if o[0] > v)
                if place <= 10:
                    by_year[y]["br10"].add((f[:1], l, c))
                if place <= 3:
                    ever.add((f, l))
    return by_year, ever


def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def report(d, hon, ever):
    out = []
    for start, season in STARTS.items():
        path = os.path.join(d, "ratings_%s.csv" % start)
        if not os.path.exists(path):
            continue
        rows = read(path)
        lists = [r for r in rows if r["kind"] == "list"]
        ovr = sorted(int(r["overall"]) for r in lists)
        line = ["%s start (rated on %d): %d listed, median %d, 80+ %d, 90+ %d" % (
            start, season, len(ovr), ovr[len(ovr) // 2], sum(v >= 80 for v in ovr), sum(v >= 90 for v in ovr))]
        for kind, label in (("aa", "All-Australians"), ("br10", "Brownlow top 10"), ("bf", "club champions")):
            want = hon[season][kind]
            got = sorted(int(r["overall"]) for r in lists if (norm(r["first"])[:1], norm(r["last"]), r["club"]) in want)
            if got:
                low = [("%s %s %s" % (r["first"], r["last"], r["overall"])) for r in lists
                       if (norm(r["first"])[:1], norm(r["last"]), r["club"]) in want and int(r["overall"]) < 80]
                line.append("  %d %s %s: median %d, lowest %d, under 80: %d%s" % (
                    season, label, "(%d found)" % len(got), got[len(got) // 2], got[0], len(low),
                    (" (" + ", ".join(low) + ")") if low else ""))
        pot = [r for r in rows if r["potential"]]
        for cut in (95, 90):
            hi = [r for r in pot if int(r["potential"]) >= cut]
            dud = [r for r in hi if (norm(r["first"]), norm(r["last"])) not in ever and int(r["overall"]) < cut - 10]
            line.append("  potential %d+: %d, of them %d with no honour in their real career and rated 10+ under it%s" % (
                cut, len(hi), len(dud), (" (e.g. " + ", ".join("%s %s %s/%s" % (r["first"], r["last"], r["overall"], r["potential"]) for r in dud[:8]) + ")") if dud and cut == 95 else ""))
        out.append("\n".join(line))
    return "\n\n".join(out)


def main():
    hon, ever = honours()
    for d in sys.argv[1:]:
        print("== %s\n" % d)
        print(report(d, hon, ever))
        print()


if __name__ == "__main__":
    main()
