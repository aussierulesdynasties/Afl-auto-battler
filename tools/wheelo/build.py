#!/usr/bin/env python3
"""
Write each start's rating file and today's rated seasons, the director's way
(interview 2026-11-15; tools/wheelo/seasons_rated.py rates every season).

  data/rating_stats_2026.csv, data/legacy/<start>/rating_stats_<start>.csv
      club,first,last,src,apos,ovr,<the 16 skills>: one row per listed player
      with a rated AFL season (the players file's own season, or a list
      addition's latest), GameDB matching on club + first + last. apos is his
      AFL position that season, ovr his overall for that season alone (the
      game blends it with the seasons before, Ratings.rate_on_record), the
      skills each against his AFL position that season (1-99).
  data/player_history_2026.csv
      its seasons column ("year:overall:games") re-rated. The past starts'
      history files take the same overalls through
      tools/legacy_1990s/build_start.py::rate_seasons: rerun their builders.

    python3 tools/wheelo/build.py
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

import wheelo as W  # noqa: E402
import model as M  # noqa: E402
import seasons_rated as S  # noqa: E402

B = S.B
DATA = os.path.join(ROOT, "data")
LEG = os.path.join(DATA, "legacy")

# start -> (players file, list addition stats file, rating file, data season)
STARTS = {
    "1990": ("legacy/1990/players_1990.csv", "legacy/1990/list_addition_stats_1990.csv",
             "legacy/1990/rating_stats_1990.csv", 1989),
    "2000": ("legacy/2000/players_2000.csv", "legacy/2000/list_addition_stats_2000.csv",
             "legacy/2000/rating_stats_2000.csv", 1999),
    "2010": ("legacy/2010/players_2010.csv", "legacy/2010/list_addition_stats_2010.csv",
             "legacy/2010/rating_stats_2010.csv", 2009),
    "2020": ("legacy/2020/players_2020.csv", "legacy/2020/list_addition_stats_2020.csv",
             "legacy/2020/rating_stats_2020.csv", 2019),
    "2026": ("players_enriched_2026.csv", "list_additions_stats.csv", "rating_stats_2026.csv", 2026),
}
COLS = ["club", "first", "last", "src", "apos", "ovr"] + M.SKILLS
IMPORT = "[remap]\n\nimporter=\"keep\"\n"


def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class SeasonIndex:
    """A season's rated players by name and club: AFL Tables rows (to 2025),
    else Wheelo's (2026, which AFL Tables does not have yet)."""

    def __init__(self, year):
        self.year = year
        self.rated = S.rated(year)
        self.by_name_club, self.by_name, self.by_last_club = {}, defaultdict(list), defaultdict(list)
        self.by_line = defaultdict(list)
        if year > 2025:
            self.matcher = W.Matcher(year)
            self.by_wheelo = {v["wheelo"]: k for k, v in self.rated.items()}
            return
        self.matcher = None
        for pid, r in S.merged(year).items():
            if pid not in self.rated:
                continue
            f, l, c = W.norm(r["first"]), W.norm(r["last"]), B.code(r["club"])
            self.by_name_club[(f + l, c)] = pid
            self.by_name[f + l].append(pid)
            self.by_last_club[(l, c)].append((f, pid))
            self.by_line[(l, str(int(float(r['gm'] or 0))), str(int(float(r['ki'] or 0))))].append(pid)
        # A player traded mid-season: his first club's rows too.
        for r in B.load_seasons().get(year, []):
            pid = r["afltables_id"]
            if pid in self.rated:
                self.by_name_club.setdefault((W.norm(r["first"]) + W.norm(r["last"]), B.code(r["club"])), pid)

    def club_of(self, pid):
        v = self.rated[pid]
        if "club" in v:
            return v["club"]
        r = S.merged(self.year).get(pid)
        return B.code(r["club"]) if r else ""

    def find(self, first, last, club, gm=None, ki=None):
        if self.matcher:
            w = self.matcher.find(first, last, club)
            return self.by_wheelo.get(w["PlayerId"]) if w else None
        f, l = W.norm(first), W.norm(last)
        for ff in (f, W.NICK.get(f, f)):
            pid = self.by_name_club.get((ff + l, club))
            if pid:
                return pid
        cand = [pid for fi, pid in self.by_last_club.get((l, club), []) if fi[:1] == f[:1]]
        if len(cand) == 1:
            return cand[0]
        # Traded or known by another first name (Brad / Bradley Hill): his
        # surname with the same games and kicks that season.
        if gm not in (None, ""):
            got = self.by_line.get((l, str(int(float(gm))), str(int(float(ki or 0)))))
            if got and len(got) == 1:
                return got[0]
        got = self.by_name.get(f + l) or self.by_name.get(W.NICK.get(f, f) + l)
        if got and len(got) == 1:
            return got[0]
        return None


def rating_rows(start):
    players_f, adds_f, _out, season = STARTS[start]
    idx = {}
    rows, missed, seen = [], [], set()
    for path in (players_f, adds_f):
        full = os.path.join(DATA, path)
        if not os.path.exists(full):
            continue
        for r in read(full):
            src = int(r.get("src") or season)
            if src not in idx:
                idx[src] = SeasonIndex(src)
            pid = idx[src].find(r["first"], r["last"], r["club"], r.get("gm"), r.get("ki"))
            key = (r["club"], r["first"], r["last"])
            if pid is None:
                missed.append("%s %s %s %d" % (r["club"], r["first"], r["last"], src))
                continue
            if key in seen:
                continue
            seen.add(key)
            got = idx[src].rated[pid]
            row = {"club": r["club"], "first": r["first"], "last": r["last"], "src": src, "apos": got["pos"],
                   "ovr": int(round(got["ovr"]))}
            row.update({k: got["skills"][k] for k in M.SKILLS})
            row["_pid"] = (src, pid)
            rows.append(row)
    # Two of our players matched to one season row (two Bailey Williams at
    # different clubs): the one at the row's club keeps it.
    by_pid = defaultdict(list)
    for r in rows:
        by_pid[r["_pid"]].append(r)
    drop = set()
    for (src, pid), same in by_pid.items():
        if len(same) > 1:
            club = idx[src].club_of(pid)
            for r in same:
                if r["club"] != club:
                    drop.add(id(r))
                    missed.append("%s %s %s %d (his name's row is %s's)" % (r["club"], r["first"], r["last"], src, club))
    rows = [r for r in rows if id(r) not in drop]
    for r in rows:
        del r["_pid"]
    return rows, missed


def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    imp = path + ".import"
    if not os.path.exists(imp):
        with open(imp, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(IMPORT)


def rerate_history_2026():
    """player_history_2026.csv: each "year:overall:games" season re-rated."""
    path = os.path.join(DATA, "player_history_2026.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        cols, rows = rd.fieldnames, list(rd)
    by_slug = {}
    for y in range(2004, 2026):
        for pid, v in S.rated(y).items():
            if not pid.startswith("wheelo:"):
                by_slug[(pid.rsplit("/", 1)[-1].replace(".html", ""), y)] = v
    changed = kept = 0
    for r in rows:
        out = []
        for chunk in [c for c in r["seasons"].split(";") if c]:
            y, ovr, g = chunk.split(":")
            got = by_slug.get((r["slug"], int(y)))
            if got:
                ovr = str(int(round(got["ovr"])))
                changed += 1
            else:
                kept += 1
            out.append("%s:%s:%s" % (y, ovr, g))
        r["seasons"] = ";".join(out)
    write_csv(path, cols, rows)
    print("player_history_2026: %d seasons re-rated, %d not found (kept)" % (changed, kept))


def main():
    for start, (_p, _a, out, _s) in STARTS.items():
        rows, missed = rating_rows(start)
        write_csv(os.path.join(DATA, out), COLS, rows)
        print("%s: %d rated, %d with no rated season%s" % (start, len(rows), len(missed),
                                                          (": " + "; ".join(missed[:12])) if missed else ""))
    rerate_history_2026()


if __name__ == "__main__":
    main()
