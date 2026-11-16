#!/usr/bin/env python3
"""
The real players a generated player is copied from (director, 2026-11-17: "im happy for
generated players to be based on real players, but we have to make sure that they arent
based on players pre-2012"; asked which seasons: "what about every other year").

  data/copy_pool.csv
      year,id,name,club,line,pos,gm,ovr,<the 16 skills>: one row per player per AFL
      season 2012-2026 that Wheelo rates, each season rated on its own by the same
      model as the start's rating files (seasons_rated._rate_wheelo_year: his AFL Player
      Rating against his AFL position that season, and each skill against his
      position that season). line is the game's line for his AFL position (DEF, MID,
      FWD, RUCK). Prospects._shape_for reads it.

    python3 tools/wheelo/copy_pool.py
Stdlib only.
"""
from __future__ import annotations

import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import wheelo as W  # noqa: E402
import model as M  # noqa: E402
import seasons_rated as S  # noqa: E402

OUT = os.path.join(ROOT, "data", "copy_pool.csv")
GAME_LINE = {"DEF": "DEF", "MID": "MID", "FWD": "FWD", "RUC": "RUCK"}


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
               "ovr": int(round(got["ovr"]))}
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
    cols = ["year", "id", "name", "club", "line", "pos", "gm", "ovr"] + list(M.SKILLS)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print("wrote %s: %d rows" % (os.path.relpath(OUT, ROOT), len(rows)))


if __name__ == "__main__":
    main()
