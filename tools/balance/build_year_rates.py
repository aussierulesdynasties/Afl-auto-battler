#!/usr/bin/env python3
"""Real per-team-per-match averages for every season, written to tools/balance/afl_year_rates.json.

Legacy mode (TODO row 142, L5): each season plays its own era's football, so the
balance harness's year mode (`tools/balance.sh match N --year Y`) reads that
season's real rates. The method is build_team_rates.py's, season by season: a
club's match average is the sum of its players' season totals
(data/legacy/<decade>/season_stats.csv, AFL Tables, finals included) divided by
the club's games (the most games any of its players played). The league figure
is the mean of the club averages; min and max the lowest and highest club; sd
their spread.

A stat is kept for a season only when AFL Tables recorded it that year (some
player of every club has a figure): tackles, hit-outs and frees are there from
1987, inside 50s, clearances, rebound 50s and contested marks only from 1998,
so a 1990 screen is read on the stats 1990 kept. 2026 is copied from
afl_team_rates.json (data/players_2026.csv), so the year mode's 2026 reference
is the one a plain run reads.

    python3 tools/balance/build_year_rates.py
"""
import csv, glob, json, os, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "tools", "balance")
STATS = {"disposals": "di", "kicks": "ki", "handballs": "hb", "marks": "mk",
         "contested_marks": "cm", "tackles": "tk", "inside_50s": "if50",
         "clearances": "cl", "hitouts": "ho", "frees_for": "ff", "goals": "gl",
         "behinds": "bh", "rebound_50s": "rb"}


def season_rows():
    by_year = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "legacy", "*", "season_stats.csv"))):
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                by_year.setdefault(int(r["year"]), []).append(r)
    return by_year


def rates_for(rows):
    totals, games, seen = {}, {}, {}
    for r in rows:
        c = r["club"]
        totals.setdefault(c, {k: 0.0 for k in STATS})
        seen.setdefault(c, {k: False for k in STATS})
        games[c] = max(games.get(c, 0), int(r["gm"] or 0))
        for k, col in STATS.items():
            v = (r.get(col) or "").strip()
            if v != "":
                totals[c][k] += float(v)
                if float(v) > 0:
                    seen[c][k] = True
    clubs = [c for c in totals if games[c] > 0]
    out = {}
    for k in STATS:
        # Recorded that season: every club has a figure for some player.
        if not all(seen[c][k] for c in clubs):
            continue
        vals = [totals[c][k] / games[c] for c in clubs]
        out[k] = {"mean": round(statistics.mean(vals), 2), "min": round(min(vals), 2),
                  "max": round(max(vals), 2), "sd": round(statistics.pstdev(vals), 2)}
    return len(clubs), sum(games[c] for c in clubs), out


def main() -> None:
    years = {}
    for y, rows in sorted(season_rows().items()):
        n, tg, rates = rates_for(rows)
        years[str(y)] = {"clubs": n, "team_games": tg, "per_team_match": rates}
    base = json.load(open(os.path.join(HERE, "afl_team_rates.json"), encoding="utf-8"))
    years["2026"] = {"clubs": base["clubs"], "team_games": base["team_games"],
                     "per_team_match": base["per_team_match"]}
    doc = {
        "source": "data/legacy/<decade>/season_stats.csv (AFL Tables season totals, finals included) summed per club and divided by the club's games (the most games any of its players played), season by season, as build_team_rates.py does for 2026; 2026 is afl_team_rates.json. A stat is left out of a season AFL Tables did not record it (inside 50s, clearances, rebound 50s and contested marks start in 1998). Behinds are player-credited (no rushed behinds). Per team per match; mean, lowest, highest and spread across the season's clubs. Regenerate with tools/balance/build_year_rates.py.",
        "years": years,
    }
    with open(os.path.join(HERE, "afl_year_rates.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    keys = list(STATS)
    print("year " + " ".join("%7s" % k[:7] for k in keys))
    for y, v in years.items():
        r = v["per_team_match"]
        print(y + " " + " ".join("%7.1f" % r[k]["mean"] if k in r else "      -" for k in keys))


if __name__ == "__main__":
    main()
