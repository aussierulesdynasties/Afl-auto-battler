"""Build data/fine_wine.csv: every real player with the Fine Wine trait.

Fine Wine (director, 2026-11-13: "when a player has unnatural longevity like
Zorko, Gawn, Pendlebury etc"): a real player has it when he was on an AFL list
in the season he turned FINE_WINE_AGE or older. Measured on the 1990-2025 lists
(data/legacy/*/lists.csv) and the 2026 list (data/players_enriched_2026.csv):
36 of 2,789 players who joined a list aged 21 or younger from 1991 (born 1990
or earlier) reached that season, 1.29%. Traits.FINE_WINE_DRAFTEE_ODDS is set
from that rate.

Run from the repo root: python tools/build_fine_wine.py
"""
import csv
import glob

FINE_WINE_AGE = 35
OUT = "data/fine_wine.csv"


def main():
    best = {}

    def note(first, last, dob, year):
        if not dob or not first or not last:
            return
        key = (first.strip(), last.strip(), dob.strip())
        age = year - int(dob[:4])
        old = best.get(key)
        if old is None or age > old[0]:
            best[key] = (age, year)

    for path in sorted(glob.glob("data/legacy/*/lists.csv")):
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                note(r["first"], r["last"], r["dob"], int(r["year"]))
    with open("data/players_enriched_2026.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            note(r["first"], r["last"], r["dob"], 2026)
    rows = sorted(((k, v) for k, v in best.items() if v[0] >= FINE_WINE_AGE),
                  key=lambda kv: (kv[0][2], kv[0][1]))
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["first", "last", "dob", "oldest_age", "last_listed"])
        for (first, last, dob), (age, year) in rows:
            w.writerow([first, last, dob, age, year])
    print("%s: %d players" % (OUT, len(rows)))


if __name__ == "__main__":
    main()
