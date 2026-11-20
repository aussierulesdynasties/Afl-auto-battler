#!/usr/bin/env python3
"""
Every AFL season 1987-2026 rated the director's way (interview 2026-11-15):

  2012+   AFL position and overall from Wheelo (the official AFL Player
          Rating against his position, wheelo.apr_ovr); skills from
          Wheelo's stats against his position (model.rate_season)
  < 2012  AFL Tables: the AFL position read from his known line and the
          season's numbers (model.knn_votes, the season's mix held to 2012+'s by
          model.calibrated_positions), skills from the stats the
          season kept, overall from the skills by the director's weights
          (weights_pre2012.json), placed by rank on 2012-25's AFL Player
          Rating: a season's mix is ranked among 2012-25's players of his
          position, rated on the same stats, and takes the rating at that rank
          (rank_maps)

rated(year) -> {afltables_id: {"ovr", "gm", "pos", "skills", "wheelo"}}
(2012+ AFL Tables players are matched to Wheelo by name and club.)

The ratings of every season are cached in tools/wheelo/cache/ (git-ignored):
delete it after changing the model.
Stdlib only.
"""
from __future__ import annotations

import bisect
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


POS_KEY = dict(zip(W.POSITIONS, ["key_defender", "gen_defender", "midfielder", "mid_forward",
                                  "gen_forward", "key_forward", "ruck"]))


def weights():
    if "weights" not in _mem:
        with open(os.path.join(HERE, "weights_pre2012.json"), encoding="utf-8") as fh:
            _mem["weights"] = json.load(fh)
    return _mem["weights"]


def recorded(skill_raws):
    """The skills a set of players' stats feed: those that differ between them."""
    return [k for k in M.SKILLS if len({round(s[k], 6) for s in skill_raws}) > 1]


def mix_weights(tier, pos, rec):
    """The director's weights for a position over the skills the tier records.
    Where contested marks were not kept (before 1999) a mark is a mark: total
    marks carry the contested-marking weight too (director 2026-11-16: Carey,
    a centre half-forward, "marks up the ground")."""
    wj = weights()
    w = dict(wj["positions"][POS_KEY[pos]])
    w.update(wj.get("era", {}).get(tier, {}).get(POS_KEY[pos], {}))
    if "contested_marking" not in rec:
        w["uncontested_marking"] = w.get("uncontested_marking", 0) + w.pop("contested_marking", 0)
    return {k: w[k] for k in rec if w.get(k)}


def mix(w, s):
    tot = sum(w.values())
    return sum(v * s[k] for k, v in w.items()) / tot if tot else 0.0


def rank_maps():
    """Per record tier and position: 2012-25's players (12+ games) rated on the
    stats that tier kept, their mixes and AFL Player Ratings each sorted."""
    if "rank" not in _mem:
        path = os.path.join(CACHE, "rank_maps.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                _mem["rank"] = json.load(fh)
        else:
            out = {}
            for tier in F.TIERS:
                smp = [(p, s, a) for p, s, a, g in F.tables_samples(tier) if g >= 12]
                rec = recorded([s for _p, s, _a in smp])
                out[tier] = {"recorded": rec, "positions": {}}
                for pos in W.POSITIONS:
                    w = mix_weights(tier, pos, rec)
                    rows = [(mix(w, s), a) for p, s, a in smp if p == pos]
                    out[tier]["positions"][pos] = [sorted(b for b, _a in rows), sorted(a for _b, a in rows)]
            os.makedirs(CACHE, exist_ok=True)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                json.dump(out, fh)
            _mem["rank"] = out
    return _mem["rank"]


def by_rank(mixes, ratings, b):
    """The rating at a mix's rank among 2012-25's (between two, in proportion)."""
    i = bisect.bisect_left(mixes, b)
    if i <= 0:
        return ratings[0]
    if i >= len(mixes):
        return ratings[-1]
    lo, hi = mixes[i - 1], mixes[i]
    f = (b - lo) / (hi - lo) if hi > lo else 0.0
    return ratings[i - 1] + f * (ratings[i] - ratings[i - 1])


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
    rm = rank_maps()[tier]
    ps, votes = [], []
    for pid, r in rows.items():
        if float(r["gm"] or 0) <= 0:
            continue
        votes.append(M.knn_votes(train, M.pos_vector(r, B.POS_BY_ID.get(pid), keep, sc)))
        masked = {k: (r.get(k, "") if k in keep else "") for k in F.ALL_TABLES}
        ps.append({"pos": "", "m": M.tables_inputs(masked), "id": pid})
    share = defaultdict(int)
    for _, p in train:
        share[p] += 1
    target = {p: share[p] / len(train) for p in W.POSITIONS}
    for p, pos in zip(ps, M.calibrated_positions(votes, target)):
        p["pos"] = pos
    M.rate_season(ps, {})
    out = {}
    for p in ps:
        mixes, ratings = rm["positions"][p["pos"]]
        w = mix_weights(tier, p["pos"], rm["recorded"])
        o = by_rank(mixes, ratings, mix(w, p["skill_raw"])) if mixes else W.APR_MIDDLE
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
