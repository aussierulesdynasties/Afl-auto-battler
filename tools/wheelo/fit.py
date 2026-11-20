#!/usr/bin/env python3
"""
Ruling 19 (director 2026-11-15): measure, from 2012+ seasons, how much each
skill counts towards the official AFL Player Rating in each AFL position.

  full   Wheelo's stats (every 2012+ skill): the game's overall for players
         rated on skills - generated players and every player's development
  1987 / 1998 / 1999 / 2003
         the stats AFL Tables keeps from that season on (ruling 18: a stat
         a season did not keep is left out), measured on 2012-2025 AFL
         Tables seasons against the same players' AFL Player Rating: the
         overall of a season before 2012

    python tools/wheelo/fit.py            # print the weights
    python tools/wheelo/fit.py --json F   # also write them to F
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "legacy_1990s"))

import wheelo as W  # noqa: E402
import model as M  # noqa: E402

# AFL Tables columns each era keeps (tools/legacy_1990s/build_start.unrecorded).
ALL_TABLES = ["gm", "ki", "mk", "hb", "di", "gl", "bh", "ho", "tk", "rb", "if50", "cl", "cg", "ff", "fa", "br",
              "cp", "up", "cm", "mi", "one_pct", "bo", "ga", "pct_played"]
TIERS = {
    "2003": set(ALL_TABLES),
    "1999": set(ALL_TABLES) - {"ga", "pct_played"},
    "1998": set(ALL_TABLES) - {"bo", "cm", "cp", "ga", "mi", "one_pct", "pct_played", "up"},
    "1987": {"gm", "ki", "mk", "hb", "di", "gl", "bh", "ho", "tk", "ff", "fa", "br"},
}


def tier_of(year: int) -> str:
    return "2003" if year >= 2003 else "1999" if year >= 1999 else "1998" if year >= 1998 else "1987"


def wheelo_samples(speed):
    out = []
    for y, rows in sorted(W.seasons().items()):
        apr = W.apr_ovr(y)
        ps = [{"pos": r["pos"], "m": M.wheelo_inputs(r), "name": r["Player"], "id": r["PlayerId"]}
              for r in rows if r["pos"] and r["PlayerId"] in apr]
        M.rate_season(ps, speed)
        out += [(p["pos"], p["skill_raw"], apr[p["id"]][0], apr[p["id"]][1]) for p in ps]
    return out


def tables_samples(tier: str):
    import build_start as B
    by_year = B.load_seasons()
    keep = TIERS[tier]
    out = []
    for y in range(W.FIRST, W.LAST):
        if y not in by_year:
            continue
        match, apr = W.Matcher(y), W.apr_ovr(y)
        ps = []
        for r in by_year[y]:
            w = match.find(r["first"], r["last"], B.code(r["club"]))
            if not w or w["PlayerId"] not in apr or not w["pos"]:
                continue
            masked = {k: (r.get(k, "") if k in keep else "") for k in ALL_TABLES}
            ps.append({"pos": w["pos"], "m": M.tables_inputs(masked), "id": w["PlayerId"]})
        M.rate_season(ps, {})
        out += [(p["pos"], p["skill_raw"], apr[p["id"]][0], apr[p["id"]][1]) for p in ps]
    return out


# The game's own overall (Ratings.rate_overall): a player's line (the four the
# match engine picks sides by) and his skills as the game keeps them, 1-99
# whole numbers, so a generated player or one whose skills have moved is rated
# the way the AFL Player Rating rates the players of his line.
GAME_LINES = ["DEF", "MID", "FWD", "RUCK"]


def game_line(pos):
    line = W.LINE[pos]
    return "RUCK" if line == "RUC" else line


def game_samples(speed):
    out = []
    for y, rows in sorted(W.seasons().items()):
        apr = W.apr_ovr(y)
        ps = [{"pos": r["pos"], "m": M.wheelo_inputs(r), "id": r["PlayerId"]}
              for r in rows if r["pos"] and r["PlayerId"] in apr]
        M.rate_season(ps, speed)
        out += [(game_line(p["pos"]), {k: (p["skills"][k] - 1) / 98.0 for k in M.SKILLS}, apr[p["id"]][0],
                 apr[p["id"]][1]) for p in ps]
    return out


def game_fit(speed=None):
    speed = speed if speed is not None else M.speed_scores(M.speed_records())
    return M.fit_weights(game_samples(speed), M.SKILLS, GAME_LINES)


def show(name, fit):
    print("\n== %s ==" % name)
    for pos, f in fit.items():
        top = sorted(f["share"].items(), key=lambda kv: -kv[1])
        print("%-14s r=%.2f rmse=%.1f n=%d  %s" % (pos, f["r"], f["rmse"], f["n"],
              ", ".join("%s %.0f%%" % (k, v * 100) for k, v in top if v >= 0.005)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    speed = M.speed_scores(M.speed_records())
    fits = {"full": M.fit_weights(wheelo_samples(speed), M.SKILLS)}
    show("full (2012+ Wheelo)", fits["full"])
    fits["game"] = game_fit(speed)
    show("game lines (whole-number skills)", fits["game"])
    for tier in TIERS:
        fits[tier] = M.fit_weights(tables_samples(tier), M.SKILLS)
        show("AFL Tables from %s" % tier, fits[tier])
    if a.json:
        with open(a.json, "w", newline="\n", encoding="utf-8") as fh:
            json.dump(fits, fh, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
