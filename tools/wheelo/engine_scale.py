#!/usr/bin/env python3
"""
The match engine's reading of each skill (2026-11-16).

The skills a coach sees are rated against the player's AFL position (interview
2026-11-15, ruling 20): a key forward's contested marking 70 is good for a key
forward. The engine has to know he out-marks a small defender rated 70 for a
small defender, so it reads every skill league-wide: the same Wheelo recipe,
with every 2026 player in one group, ranks him within his line (defence,
midfield, forwards, ruck), and the value at that rank on his line's scale the
engine was tuned on (main at d8b72dd76, tools/wheelo/engine_targets.csv) is
what the engine rolls against. So each line keeps the strength the engine's
rates were tuned to, and the director's stats decide who in it is good.

  data/engine_scale.csv
      apos,key,v0,v10,...,v100: the engine's value at position-relative skill
      0, 10, ... 100 for that position (Skills.engine interpolates). Fitted on
      the 2026 Wheelo players, so a generated player of the same position and
      skill reads the same.

    python3 tools/wheelo/engine_scale.py
Stdlib only.
"""
from __future__ import annotations

import copy
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "legacy_1990s"))

import wheelo as W  # noqa: E402
import model as M  # noqa: E402
import seasons_rated as S  # noqa: E402

YEAR = 2026
OUT = os.path.join(ROOT, "data", "engine_scale.csv")
TARGETS = os.path.join(HERE, "engine_targets.csv")
# Each skill the engine reads, and the old attribute whose scale it takes.
TARGET_OF = {
    "disposal": "disposal", "kicking": "disposal", "handballing": "disposal",
    "contested_marking": "marking", "uncontested_marking": "marking",
    "contested": "contested", "pressure": "pressure", "intercept": "intercept",
    "carry": "carry", "goalkicking": "goalkicking", "accuracy": "accuracy",
    "creating": "creating", "ruck": "ruck", "discipline": "discipline",
    "durability": "durability", "star": "star",
}
# His line on the old scale. A mid-forward plays both, so he is ranked among
# both and read on both lines' scale.
LINE_OF = {"Key Defender": "DEF", "Gen. Defender": "DEF", "Midfielder": "MID", "Mid-Forward": "MID+FWD",
           "Gen. Forward": "FWD", "Key Forward": "FWD", "Ruck": "RUCK"}
LINE_POS = {"DEF": {"Key Defender", "Gen. Defender"}, "MID": {"Midfielder", "Mid-Forward"},
            "FWD": {"Gen. Forward", "Key Forward", "Mid-Forward"}, "RUCK": {"Ruck"},
            "MID+FWD": {"Midfielder", "Mid-Forward", "Gen. Forward", "Key Forward"}}
KICK_SHARE = 0.56   # Skills.disposal_of: 0.56 kicking + 0.44 handballing
KNOTS = list(range(0, 101, 10))


def targets():
    out = {}
    with open(TARGETS, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[(r["line"], r["key"])] = [float(r["q%d" % i]) for i in range(101)]
    return out


def at_rank(q, p):
    i = max(0.0, min(1.0, p)) * 100.0
    lo = int(i)
    hi = min(100, lo + 1)
    return q[lo] + (q[hi] - q[lo]) * (i - lo)


def with_disposal(s):
    s = dict(s)
    s["disposal"] = KICK_SHARE * s["kicking"] + (1.0 - KICK_SHARE) * s["handballing"]
    return s


def rate():
    rows = W.seasons()[YEAR]
    apr = W.apr_ovr(YEAR)
    rows = [r for r in rows if r["pos"] and r["PlayerId"] in apr]
    own = [{"pos": r["pos"], "m": M.wheelo_inputs(r), "name": r["Player"]} for r in rows]
    M.rate_season(own, S.speed())
    # One group for the league. His one-on-one record stays the one his
    # position counts (attack or defence), as in his own rating.
    pool = []
    for p, r in zip(own, rows):
        m = M.wheelo_inputs(r)
        m["_off"] = (p["m"]["one_on_one"], p["m"]["_contests"])
        m["_def"] = (None, 0.0)
        pool.append({"pos": "League", "m": m, "name": r["Player"]})
    M.rate_season(pool, S.speed())
    return own, pool


def isotonic(ys):
    """Pool adjacent violators: the closest non-decreasing run."""
    blocks = [[y, 1] for y in ys]
    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] > blocks[i + 1][0]:
            a, b = blocks[i], blocks[i + 1]
            n = a[1] + b[1]
            blocks[i] = [(a[0] * a[1] + b[0] * b[1]) / n, n]
            del blocks[i + 1]
            i = max(0, i - 1)
        else:
            i += 1
    out = []
    for y, n in blocks:
        out += [y] * n
    return out


def fit(points):
    """[(position-relative 1..99, engine value)] -> engine value at KNOTS."""
    vals = []
    for x in KNOTS:
        w = 7.5
        near = []
        while len(near) < 5 and w <= 40:
            near = sorted(e for v, e in points if abs(v - x) <= w)
            w += 2.5
        vals.append(near[len(near) // 2] if near else None)
    known = [i for i, v in enumerate(vals) if v is not None]
    for i in range(len(vals)):
        if vals[i] is None:
            j = min(known, key=lambda k: abs(k - i))
            vals[i] = vals[j]
    return [max(1.0, min(99.0, v)) for v in isotonic(vals)]


def main():
    tq = targets()
    own, pool = rate()
    n = len(pool)
    skills = {p_key: None for p_key in TARGET_OF}
    pooled = [with_disposal(p["skill01"]) for p in pool]
    out = []
    for pos in sorted({p["pos"] for p in own}):
        line = LINE_OF[pos]
        peers = [i for i, p in enumerate(own) if p["pos"] in LINE_POS[line]]
        idx = [i for i, p in enumerate(own) if p["pos"] == pos]
        for key in TARGET_OF:
            order = sorted(peers, key=lambda i: pooled[i][key])
            rank = {i: r / max(1, len(order) - 1) for r, i in enumerate(order)}
            q = tq[(line, TARGET_OF[key])]
            pts = [(with_disposal(own[i]["skills"])[key], at_rank(q, rank[i])) for i in idx]
            out.append([pos, key] + ["%.1f" % v for v in fit(pts)])
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["apos", "key"] + ["v%d" % x for x in KNOTS])
        w.writerows(out)
    print("%d players, %d rows -> %s" % (n, len(out), os.path.relpath(OUT, ROOT)))


if __name__ == "__main__":
    main()
