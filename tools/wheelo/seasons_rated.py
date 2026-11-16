#!/usr/bin/env python3
"""
Every AFL season 1987-2026 rated the director's way (interview 2026-11-15):

  2012+   AFL position and overall from Wheelo (the official AFL Player
          Rating against his position, wheelo.apr_ovr); skills from
          Wheelo's stats against his position (model.rate_season)
  < 2012  AFL Tables: the AFL position read from his known line and the
          season's numbers (model.knn_position), skills from the stats the
          season kept, overall from the skills by the weights measured on
          2012+ (fit.py, ruling 19)

rated(year) -> {afltables_id: {"ovr", "gm", "pos", "skills", "wheelo"}}
(2012+ AFL Tables players are matched to Wheelo by name and club.)

The ratings of every season are cached in tools/wheelo/cache/ (git-ignored):
delete it after changing the model.
Stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "legacy_1990s"))

import wheelo as W  # noqa: E402
import model as M  # noqa: E402
import fit as F  # noqa: E402
import build_start as B  # noqa: E402

CACHE = os.path.join(HERE, "cache")
SUM_KEYS = ["gm", "ki", "mk", "hb", "di", "gl", "bh", "ho", "tk", "rb", "if50", "cl", "cg", "ff", "fa", "br",
            "cp", "up", "cm", "mi", "one_pct", "bo", "ga"]

_mem: dict = {}


def speed():
    if "speed" not in _mem:
        _mem["speed"] = M.speed_scores(M.speed_records())
    return _mem["speed"]


def fits():
    if "fits" not in _mem:
        path = os.path.join(CACHE, "fits.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                _mem["fits"] = json.load(fh)
        else:
            f = {"full": M.fit_weights(F.wheelo_samples(speed()), M.SKILLS)}
            for tier in F.TIERS:
                f[tier] = M.fit_weights(F.tables_samples(tier), M.SKILLS)
            os.makedirs(CACHE, exist_ok=True)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                json.dump(f, fh, indent=1, sort_keys=True)
            _mem["fits"] = f
    return _mem["fits"]


def tables_by_year():
    if "by_year" not in _mem:
        _mem["by_year"] = B.load_seasons()
    return _mem["by_year"]


def merged(year):
    """AFL Tables rows of a season, a player traded mid-season summed."""
    out = {}
    for r in tables_by_year().get(year, []):
        pid = r["afltables_id"]
        if pid in out:
            m = out[pid]
            for k in SUM_KEYS:
                a, b = B.num(m.get(k)), B.num(r.get(k))
                m[k] = "" if a is None and b is None else str((a or 0) + (b or 0))
            m["pct_played"] = r["pct_played"] or m["pct_played"]
            m["club"] = r["club"]
        else:
            out[pid] = dict(r)
    return out


def _position_train(tier):
    key = ("train", tier)
    if key not in _mem:
        keep = F.TIERS[tier]
        train = []
        for y in range(W.FIRST, W.LAST):
            rows = tables_by_year().get(y, [])
            mt, sc = W.Matcher(y), M.season_scale(rows, keep)
            for r in rows:
                if float(r["gm"] or 0) < 5:
                    continue
                w = mt.find(r["first"], r["last"], B.code(r["club"]))
                if w and w["pos"]:
                    train.append((M.pos_vector(r, B.POS_BY_ID.get(r["afltables_id"]), keep, sc), w["pos"]))
        _mem[key] = train
    return _mem[key]


def _rate_wheelo_year(year):
    rows = W.seasons()[year]
    apr = W.apr_ovr(year)
    ps = [{"pos": r["pos"], "m": M.wheelo_inputs(r), "name": r["Player"], "row": r}
          for r in rows if r["pos"] and r["PlayerId"] in apr]
    M.rate_season(ps, speed())
    by_wid = {p["row"]["PlayerId"]: p for p in ps}
    out = {}
    mt = W.Matcher(year)
    for pid, r in merged(year).items():
        w = mt.find(r["first"], r["last"], B.code(r["club"]))
        if not w or w["PlayerId"] not in by_wid:
            continue
        p = by_wid[w["PlayerId"]]
        out[pid] = {"ovr": round(apr[w["PlayerId"]][0], 2), "gm": int(float(r["gm"] or 0)), "pos": p["pos"],
                    "skills": p["skills"], "wheelo": w["PlayerId"]}
    # Wheelo players this season's AFL Tables rows did not match (a season
    # AFL Tables does not have yet: 2026) are kept under their Wheelo id.
    seen = {v["wheelo"] for v in out.values()}
    for wid, p in by_wid.items():
        if wid not in seen:
            out["wheelo:" + wid] = {"ovr": round(apr[wid][0], 2), "gm": int(apr[wid][1]), "pos": p["pos"],
                                    "skills": p["skills"], "wheelo": wid, "name": p["name"], "club": p["row"]["club"]}
    return out


def _rate_tables_year(year):
    tier = F.tier_of(year)
    keep = F.TIERS[tier]
    rows = merged(year)
    sc = M.season_scale(list(rows.values()), keep)
    train = _position_train(tier)
    fit = fits()[tier]
    ps = []
    for pid, r in rows.items():
        if float(r["gm"] or 0) <= 0:
            continue
        pos = M.knn_position(train, M.pos_vector(r, B.POS_BY_ID.get(pid), keep, sc))
        masked = {k: (r.get(k, "") if k in keep else "") for k in F.ALL_TABLES}
        ps.append({"pos": pos, "m": M.tables_inputs(masked), "id": pid})
    M.rate_season(ps, {})
    out = {}
    for p in ps:
        f = fit.get(p["pos"])
        o = M.overall_from(f, p["skill_raw"]) if f else W.APR_MIDDLE
        out[p["id"]] = {"ovr": round(max(W.OVR_MIN, min(W.OVR_MAX, o)), 2), "gm": int(p["m"]["games"]),
                        "pos": p["pos"], "skills": p["skills"]}
    return out


def rated(year):
    """{afltables_id: {...}} for one season (cached on disk)."""
    if ("rated", year) in _mem:
        return _mem[("rated", year)]
    path = os.path.join(CACHE, "season_%d.json" % year)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            got = json.load(fh)
    else:
        got = _rate_wheelo_year(year) if year >= W.FIRST else _rate_tables_year(year)
        os.makedirs(CACHE, exist_ok=True)
        with open(path, "w", newline="\n", encoding="utf-8") as fh:
            json.dump(got, fh, sort_keys=True)
    _mem[("rated", year)] = got
    return got


if __name__ == "__main__":
    ys = [int(a) for a in sys.argv[1:]] or list(range(1987, W.LAST + 1))
    for y in ys:
        print(y, len(rated(y)), flush=True)
