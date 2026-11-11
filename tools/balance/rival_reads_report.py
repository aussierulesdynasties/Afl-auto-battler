#!/usr/bin/env python3
"""How often the coach's reads on other clubs hold (row T1.R26 L3).

Adds up the snap["reads"] records of dynasty_run.gd --reads careers:

    python tools/balance/rival_reads_report.py run/reads_*.json [--json out.json]

--json also writes the POT counts by Recruiting level (all reads, and players
under 50 games), which tests/test_workload.gd holds the Recruiting budget
line's odds to, and the free-agency counts tests/test_contracts.gd holds the
offer gate's odds to (tools/balance/rival_reads_measured.json).

Prints a markdown page: the POT range on another club's player (how often his
true potential is outside it, by Recruiting budget and by games played), and
the free-agency gate's "the best other" figure (how often an offer that beats
it still leads once rivals answer, and how far they go).
"""
import json
import statistics
import sys

LEVELS = ["Minimal", "Standard", "Strong", "Elite"]
GAMES = [0, 50, 100, 150]
GAMES_WORDS = {0: "under 50 games", 50: "50-99", 100: "100-149", 150: "150 or more"}


def pct(a, b):
    return "-" if b == 0 else "%.1f%%" % (100.0 * a / b)


def money(v):
    return "$%dk" % round(v / 1000.0)


def main(paths):
    json_out = None
    if "--json" in paths:
        i = paths.index("--json")
        json_out = paths[i + 1]
        paths = paths[:i] + paths[i + 2:]
    pot = {}
    fa = []
    seasons = 0
    clubs = 0
    for path in paths:
        for career in json.load(open(path, encoding="utf-8")):
            for snap in career["seasons"]:
                reads = snap.get("reads")
                if not reads:
                    continue
                seasons += 1
                clubs += len(snap["clubs"])
                for key, c in reads["pot"].items():
                    t = pot.setdefault(key, [0, 0, 0, 0, 0])
                    t[0] += c[0]
                    t[1] += c[1]
                    t[2] += c[2]
                    t[3] = max(t[3], c[3])
                    t[4] += c[4]
                fa.extend(reads["fa"])
    print("# Rival reads: how often they hold\n")
    print("%d off-seasons, %d club-seasons of reads (every club as the reader), %d free-agent talks.\n"
          % (seasons, clubs, len(fa)))

    def total(level=None, games=None, grow=None, where=None):
        t = [0, 0, 0, 0, 0]
        for key, c in pot.items():
            li, g, gr, wh = key.split("|")
            if level is not None and int(li) != level:
                continue
            if games is not None and int(g) != games:
                continue
            if grow is not None and gr != grow:
                continue
            if where is not None and wh != where:
                continue
            t[0] += c[0]
            t[1] += c[1]
            t[2] += c[2]
            t[3] = max(t[3], c[3])
            t[4] += c[4]
        return t

    if json_out:
        summary = {"off_seasons": seasons, "club_seasons": clubs,
                   "careers": [p.replace(chr(92), "/").split("/")[-1] for p in paths],
                   "pot": [{"level": name, "reads": total(level=li)[0], "misses": total(level=li)[1],
                            "worst": total(level=li)[3]} for li, name in enumerate(LEVELS)],
                   "young": [{"level": name, "reads": total(level=li, games=0)[0],
                              "misses": total(level=li, games=0)[1]} for li, name in enumerate(LEVELS)]}
        # The free-agency gate's odds: how often the cheapest offer that leads
        # still leads once rivals answer, and what leading again costs when
        # it does not (salary a season, your second offer over your first).
        overtaken = [r for r in fa if not r["held"]]
        extra = [r["final"] - r["open"] for r in overtaken if "final" in r]
        summary["fa"] = {"talks": len(fa), "held": sum(1 for r in fa if r["held"]),
                         "led_again": len(extra),
                         "extra_median": statistics.median(extra) if extra else 0}
        with open(json_out, "w", encoding="utf-8", newline=chr(10)) as f:
            json.dump(summary, f, indent=1)
            f.write(chr(10))

    def cell(t):
        if t[0] == 0:
            return "-"
        return "%s (worst %d)" % (pct(t[1], t[0]), t[3])

    print("## POT range on another club's player: true potential outside the range shown\n")
    print("| Recruiting | all reads | " + " | ".join(GAMES_WORDS[g] for g in GAMES) + " | free agents only | reads |")
    print("|---|---|" + "---|" * (len(GAMES) + 2))
    for li, name in enumerate(LEVELS):
        row = [cell(total(level=li))] + [cell(total(level=li, games=g)) for g in GAMES]
        row.append(cell(total(level=li, where="m")))
        print("| %s | %s | %d |" % (name, " | ".join(row), total(level=li)[0]))
    print("\nPlayers with growth left (POT above OVR) against finished players (POT equals OVR):\n")
    print("| Recruiting | growth left | finished | mean range width (growth left) | mean miss when out |")
    print("|---|---|---|---|---|")
    for li, name in enumerate(LEVELS):
        g = total(level=li, grow="g")
        f = total(level=li, grow="f")
        a = total(level=li)
        print("| %s | %s | %s | %.1f | %.1f |" % (name, cell(g), cell(f),
              (g[4] / g[0]) if g[0] else 0.0, (a[2] / a[1]) if a[1] else 0.0))

    print("\n## Free agency: \"the best other\" before and after rivals answer\n")
    n = len(fa)
    if n == 0:
        print("no talks recorded")
        return
    held = sum(1 for r in fa if r["held"])
    moved = sum(1 for r in fa if r["answered"] > 0)
    won = sum(1 for r in fa if r["won"])
    rose = [r["after"] - r["shown"] for r in fa if r["after"] > r["shown"]]
    lost_first = [r for r in fa if not r["held"]]
    extra = [r["final"] - r["open"] for r in lost_first if "final" in r]
    under = sum(1 for r in fa if max(r["after"], r.get("after2", 0)) > r["ceiling"])
    beat_ceiling = [r for r in fa if r.get("final_w", r["open_w"]) > r["ceiling"]]
    print("| Measure | Result |")
    print("|---|---|")
    print("| Talks (a free agent with a rival offer on the table) | %d |" % n)
    print("| A rival improved or matched after your offer took the lead | %s |" % pct(moved, n))
    print("| Your opening offer (the cheapest that led) still led after they answered | %s |" % pct(held, n))
    print("| The best other offer rose, when it rose, by (worth to him a season) | median %s, most %s |"
          % (money(statistics.median(rose)) if rose else "-", money(max(rose)) if rose else "-"))
    print("| Overtaken, then the cheapest second offer that led again cost this much more a season | median %s, most %s |"
          % (money(statistics.median(extra)) if extra else "-", money(max(extra)) if extra else "-"))
    print("| He chose you after the second offer | %s |" % pct(won, n))
    print("| A rival went past the limit worked out for it | %d of %d |" % (under, n))
    print("| Offers worth more than every rival's limit that he took | %d of %d |"
          % (sum(1 for r in beat_ceiling if r["won"]), len(beat_ceiling)))
    gap = [r["ceiling"] - r["shown"] for r in fa]
    print("| Rivals' limit above the best other shown (worth to him a season) | median %s, 9 in 10 within %s, most %s |"
          % (money(statistics.median(gap)), money(sorted(gap)[int(0.9 * (len(gap) - 1))]), money(max(gap))))
    print("\nBy how many rivals were on the table:\n")
    print("| Rivals | talks | opening offer still led | best other rose |")
    print("|---|---|---|---|")
    for k in sorted(set(min(r["rivals"], 3) for r in fa)):
        sub = [r for r in fa if min(r["rivals"], 3) == k]
        print("| %s | %d | %s | %s |" % ("3 or more" if k == 3 else str(k), len(sub),
              pct(sum(1 for r in sub if r["held"]), len(sub)),
              pct(sum(1 for r in sub if r["after"] > r["shown"]), len(sub))))


if __name__ == "__main__":
    main(sys.argv[1:])
