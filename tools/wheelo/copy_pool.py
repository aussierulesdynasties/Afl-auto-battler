#!/usr/bin/env python3
"""
The real players a generated player is copied from (director, 2026-11-17: "im happy for
generated players to be based on real players, but we have to make sure that they arent
based on players pre-2012"; asked which seasons: "what about every other year").

  data/copy_pool.csv
      year,id,name,club,line,pos,gm,ovr,height_cm,<the 16 skills>,fit_shift: one row per player per AFL
      season 2012-2026 that Wheelo rates, each season rated on its own by the same
      model as the start's rating files (seasons_rated._rate_wheelo_year: his AFL Player
      Rating against his AFL position that season, and each skill against his
      position that season). line is the game's line for his AFL position (DEF, MID,
      FWD, RUCK). height_cm is his height on that season's list (data/legacy/2010s|2020s
      lists, data/players_enriched_2026.csv), blank when no list has it. Prospects reads
      it to copy generated players; PlaysLike names the seasons with a height.

    python3 tools/wheelo/copy_pool.py
    godot --headless --path . --script tools/wheelo/fit_copy_pool.gd
The second step adds fit_shift: the points the game's own fit adds to his rated skills so
he rates at that season's overall, as a listed player's are (PlaysLike uses it; the
skills stay his real ones). Stdlib only.
"""
from __future__ import annotations

import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import wheelo as W  # noqa: E402
import model as M  # noqa: E402
import seasons_rated as S  # noqa: E402

OUT = os.path.join(ROOT, "data", "copy_pool.csv")
GAME_LINE = {"DEF": "DEF", "MID": "MID", "FWD": "FWD", "RUC": "RUCK"}
LISTS = [os.path.join(ROOT, "data", "legacy", d, "lists.csv") for d in ("2010s", "2020s")]
LISTS_2026 = os.path.join(ROOT, "data", "players_enriched_2026.csv")


def _key(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def _heights():
    """(year, club, name) -> height, and (year, club, surname, first initial) -> [heights]."""
    exact, loose = {}, {}
    def add(year, club, first, last, h):
        if not h:
            return
        exact[(year, club, _key(first + last))] = int(float(h))
        loose.setdefault((year, club, _key(last), _key(first)[:1]), []).append(int(float(h)))
    for path in LISTS:
        for r in csv.DictReader(open(path, encoding="utf-8")):
            add(int(r["year"]), r["club"], r["first"], r["last"], r["height_cm"])
    for r in csv.DictReader(open(LISTS_2026, encoding="utf-8")):
        add(2026, r["club"], r["first"], r["last"], r["height_cm"])
    return exact, loose


HEIGHTS = None


def height_of(year: int, club: str, name: str):
    global HEIGHTS
    if HEIGHTS is None:
        HEIGHTS = _heights()
    exact, loose = HEIGHTS
    h = exact.get((year, club, _key(name)))
    if h is not None:
        return h
    # "Scott D. Thompson", "Cam Sutcliffe": his club's only listed man of that surname
    # and first initial that season.
    parts = [w for w in name.replace(".", " ").split() if len(w) > 1]
    if len(parts) >= 2:
        got = loose.get((year, club, _key(parts[-1]), _key(parts[0])[:1]), [])
        if len(got) == 1:
            return got[0]
    return ""


def rows_for(year: int) -> list:
    out = []
    for key, got in S._rate_wheelo_year(year).items():
        wid = got["wheelo"]
        name = got.get("name", "")
        club = got.get("club", "")
        if not name:
            r = next((x for x in W.seasons()[year] if x["PlayerId"] == wid), None)
            name = r["Player"] if r else ""
            club = r.get("club", "") if r else ""
        row = {"year": year, "id": wid, "name": name, "club": club,
               "line": GAME_LINE[W.LINE[got["pos"]]], "pos": got["pos"], "gm": got["gm"],
               "ovr": int(round(got["ovr"])), "height_cm": height_of(year, club, name)}
        row.update({k: int(got["skills"][k]) for k in M.SKILLS})
        out.append(row)
    out.sort(key=lambda r: (r["line"], r["id"]))
    return out


def main() -> None:
    rows = []
    for year in range(W.FIRST, W.LAST + 1):
        got = rows_for(year)
        print("%d: %d player seasons" % (year, len(got)))
        rows.extend(got)
    cols = ["year", "id", "name", "club", "line", "pos", "gm", "ovr", "height_cm"] + list(M.SKILLS)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print("wrote %s: %d rows, %d with a height" % (os.path.relpath(OUT, ROOT), len(rows),
                                                  sum(1 for r in rows if r["height_cm"] != "")))


if __name__ == "__main__":
    main()
