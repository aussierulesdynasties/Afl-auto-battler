"""Build data/fine_wine.csv: every real player with the Fine Wine trait.

The director, 2026-11-13: "research players who played a lot of games or
significant numbers games past the age of 32 and bring me a list of players for
my approval to gain the trait". He approved the list at 60 or more games in
seasons he turned 32 or older (72 players, 1990-2026), and draftee odds that
match the rate real draftees reached the same mark: 54 of the 2,789 who joined
a list at 21 or younger from 1991, born by 1990, played or not (1 in 52).

Games by season from AFL Tables via the repo: data/legacy/*/season_stats.csv
(1987-2025) and data/legacy/1990s/careers_before_1990.csv (the earlier seasons
of the men listed in 1990). Dates of birth from data/legacy/*/lists.csv. A
season counts as 32 or older when he turned 32 or more in it (season minus
birth year); AFL Tables keeps games by season, not by date. Only men who played
in 1990 or later count. 2026 players are counted to the end of 2025.

Each approved player is written under every name and date of birth the game's
lists use for him (data/legacy/*/lists.csv and data/players_enriched_2026.csv),
since Traits.fine_wine looks him up by real name and date of birth.

Run from the repo root: python tools/build_fine_wine.py [--table]
"""
import collections
import csv
import glob
import sys

FROM_AGE = 32   # Traits.FINE_WINE_FROM_AGE
GAMES = 60      # Traits.FINE_WINE_GAMES
OUT = "data/fine_wine.csv"


def main():
    seasons = {}
    names = {}
    for path in sorted(glob.glob("data/legacy/*/season_stats.csv")):
        for r in csv.DictReader(open(path, encoding="utf-8")):
            seasons[(r["afltables_id"], int(r["year"]), r["club"])] = int(r["gm"] or 0)
            names[r["afltables_id"]] = r["first"] + " " + r["last"]
    for r in csv.DictReader(open("data/legacy/1990s/careers_before_1990.csv", encoding="utf-8")):
        seasons.setdefault((r["afltables_id"], int(r["year"]), r["club"]), int(r["games"] or 0))
        names.setdefault(r["afltables_id"], r["first"] + " " + r["last"])

    dob = {}
    spellings = collections.defaultdict(set)
    for path in sorted(glob.glob("data/legacy/*/lists.csv")):
        for r in csv.DictReader(open(path, encoding="utf-8")):
            if r["afltables_id"] and r["dob"]:
                dob[r["afltables_id"]] = r["dob"]
                spellings[r["afltables_id"]].add((r["first"].strip(), r["last"].strip(), r["dob"].strip()))
    now = collections.defaultdict(list)   # (last, dob) -> 2026 spellings
    for r in csv.DictReader(open("data/players_enriched_2026.csv", encoding="utf-8")):
        now[(r["last"].strip(), r["dob"].strip())].append((r["first"].strip(), r["last"].strip(), r["dob"].strip()))

    per = collections.defaultdict(list)
    for (pid, year, club), g in seasons.items():
        if g > 0:
            per[pid].append((year, club, g))

    rows = []
    for pid, ss in per.items():
        if pid not in dob or max(y for y, _, _ in ss) < 1990:
            continue
        born = int(dob[pid][:4])
        old = sum(g for y, _, g in ss if y - born >= FROM_AGE)
        if old < GAMES:
            continue
        total = sum(g for _, _, g in ss)
        last = max(y for y, _, _ in ss)
        by_club = collections.Counter()
        for _, c, g in ss:
            by_club[c] += g
        rows.append((old, total, last - born, "/".join(c for c, _ in by_club.most_common()), names[pid], pid))
    rows.sort(key=lambda r: (-r[0], -r[1], r[4]))

    out = set()
    for old, total, age, clubs, name, pid in rows:
        out |= spellings[pid]
        for first, last, d in list(spellings[pid]):
            out |= set(now.get((last, d), []))
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["first", "last", "dob"])
        for first, last, d in sorted(out, key=lambda k: (k[2], k[1], k[0])):
            w.writerow([first, last, d])
    if "--table" in sys.argv:
        print("%-24s %5s %5s %4s  %s" % ("Player", "32+", "Total", "Last", "Club"))
        for old, total, age, clubs, name, pid in rows:
            print("%-24s %5d %5d %4d  %s" % (name, old, total, age, clubs))
    print("%s: %d players, %d name spellings" % (OUT, len(rows), len(out)))


if __name__ == "__main__":
    main()
