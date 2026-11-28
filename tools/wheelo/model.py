#!/usr/bin/env python3
"""
The rating model of the director's interview (2026-11-15, C:/kt/interview.md,
recorded in docs/DIRECTOR_BIBLE.md): each skill is its real stats against
players of his AFL position that season, by the recipes below.

A player-season is a dict of per-game numbers under Wheelo's names (a 2012+
season) or under the same names worked out from AFL Tables totals
(tables_inputs: an earlier season, which keeps fewer stats). A stat the
season does not keep is None and leaves its recipe (ruling 18: "stats
missing in that season left out"); a skill with none of its stats is his
position's average.

Stdlib only.
"""
from __future__ import annotations

import csv
import glob
import os
import re
from collections import defaultdict

from wheelo import POSITIONS, norm as norm_name

# Positions whose one-on-ones are in attack, in defence (ruling 5); the others
# (midfield, ruck) take both, weighted by how many of each they had.
ATTACK = {"Key Forward", "Gen. Forward", "Mid-Forward"}
DEFENCE = {"Key Defender", "Gen. Defender"}

# Skill -> [(metric, weight)]. Metrics are below (METRICS).
RECIPES = {
    "kicking": [("KickingEfficiency", 40), ("Kicks", 30), ("KickMetresGainedPerKick", 30)],          # 7
    "handballing": [("HandballEfficiency", 40), ("Handballs", 30), ("HandballMetresGained", 30)],    # 8
    "contested_marking": [("ContestedMarks", 50), ("one_on_one", 50)],                               # 5, 6
    "uncontested_marking": [("uncontested_marks", 100)],                                             # 5
    "contested": [("ContestedPossessions", 30), ("GroundBallGets", 20), ("TotalClearances", 35),
                  ("ContestedPossessionRate", 15)],                                                  # 9
    "pressure": [("PressureActs", 70), ("Tackles", 30)],                                             # 3
    "intercept": [("Intercepts", 100)],                                                              # 6
    "speed": [("speed", 100)],                                                                       # 14
    "carry": [("Bounces", 50), ("speed", 50)],                                                       # 15
    "goalkicking": [("Goals_Avg", 100)],                                                             # 10
    "accuracy": [("accuracy", 100)],                                                                 # 11
    "creating": [("GoalAssists", 40), ("ScoreInvolvements", 25), ("ScoreLaunches", 15), ("Inside50s", 20)],  # 12
    "ruck": [("Hitouts", 35), ("HitoutsToAdvantage", 30), ("HitoutsWinPercentage", 20), ("TotalClearances", 15)],  # 15
    "discipline": [("FreesAgainst", 70), ("Clangers", 30)],                                          # 17
    "durability": [("games", 55), ("time_on_ground", 45)],                                           # 16
    "star": [("coaches_votes", 100), ("BrownlowVotes", 100)],   # 17; Brownlow on AFL Tables (ruling 29)
}
SKILLS = list(RECIPES)

# How each metric is put on 0..1 against his position:
#   cap    - a count: 0 at zero, 1 at the position's 98th percentile
#   cap98  - the same, and the overall sees it stopped there too (Brownlow
#            votes)
#   range  - a rate: 0 at the position's 2nd percentile, 1 at its 98th
#   abs    - a fixed range for every position (durability is "as now")
#   z      - already a standard score against his position (speed)
# "inv" marks less-is-better.
METRICS = {
    "KickingEfficiency": "range", "Kicks": "cap", "KickMetresGainedPerKick": "range",
    "HandballEfficiency": "range", "Handballs": "cap", "HandballMetresGained": "cap",
    "ContestedMarks": "cap", "one_on_one": "range", "uncontested_marks": "cap",
    "ContestedPossessions": "cap", "GroundBallGets": "cap", "TotalClearances": "cap",
    "ContestedPossessionRate": "range", "PressureActs": "cap", "Tackles": "cap", "Intercepts": "cap",
    "speed": "z", "Bounces": "cap", "Goals_Avg": "cap", "accuracy": "range",
    "GoalAssists": "cap", "ScoreInvolvements": "cap", "ScoreLaunches": "cap", "Inside50s": "cap",
    "Hitouts": "cap", "HitoutsToAdvantage": "cap", "HitoutsWinPercentage": "range",
    "FreesAgainst": "cap inv", "Clangers": "cap inv", "games": "abs", "time_on_ground": "abs",
    "coaches_votes": "cap", "BrownlowVotes": "cap98",
}
ABS_RANGE = {"games": (0.0, 26.0), "time_on_ground": (30.0, 95.0)}   # Ratings.build_norm_params

NORM_GAMES = 12        # players with this many games set a position's scale
SHRINK_GAMES = 5.0     # Ratings.T.shrink_games: a short season leans to his position's average
SHRINK_SHOTS = 14.0    # Ratings.T.shrink_accuracy
SHRINK_CONTESTS = 10.0  # one-on-ones: a handful of contests leans to the average


def scale_attr(x: float) -> int:
    """Ratings.scale_attr: 0..1 -> 1..99."""
    return int(round(1.0 + 98.0 * max(0.0, min(1.0, x))))


def _pct(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    i = q * (len(sorted_vals) - 1)
    lo = int(i)
    hi = min(len(sorted_vals) - 1, lo + 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (i - lo)


# ------------------------------------------------------------ inputs --
def _g(r, k):
    v = r.get(k)
    return None if v is None else float(v)


def wheelo_inputs(r: dict) -> dict:
    """Per-game metrics of a Wheelo row (the row's own per-game averages)."""
    g = _g(r, "Matches") or 0.0
    m = {k: _g(r, k) for k in METRICS if k in r}
    m["games"] = g
    m["time_on_ground"] = _g(r, "TimeOnGround")
    m["Goals_Avg"] = _g(r, "Goals_Avg")
    mk, cm = _g(r, "Marks"), _g(r, "ContestedMarks")
    m["uncontested_marks"] = None if mk is None or cm is None else max(0.0, mk - cm)
    cv = _g(r, "CoachesVotes_Total")
    m["coaches_votes"] = None if cv is None or g <= 0 else cv / g
    # Ruling 11: 2021+ credits hard shots (expected-score rating a shot);
    # before 2021, goals out of shots.
    xs = _g(r, "xScoreRatingPerShot")
    shots = (_g(r, "ShotsAtGoal") or 0.0) * g
    goals = (_g(r, "Goals_Avg") or 0.0) * g
    m["accuracy"] = xs if xs is not None else (goals / shots if shots > 0 else None)
    m["_shots"] = shots
    # Ruling 5: one-on-ones - attack win %, defence loss % (less is better).
    off_n = (_g(r, "ContestOffensiveOneOnOnes") or 0.0) * g
    def_n = (_g(r, "ContestDefensiveOneOnOnes") or 0.0) * g
    off_w = _g(r, "ContestOffensiveWinPercentage")
    def_l = _g(r, "ContestDefensiveLossPercentage")
    m["_off"] = (off_w, off_n)
    m["_def"] = (None if def_l is None else 100.0 - def_l, def_n)
    m["one_on_one"] = None   # set per position in rate_season
    m["speed"] = None
    return m


def tables_inputs(r: dict) -> dict:
    """The same metrics from an AFL Tables season row (totals). AFL Tables
    keeps no efficiencies, metres, pressure acts, ground ball gets,
    intercepts, one-on-ones, score involvements or launches, hit-outs to
    advantage or hit-out win rate: those are left out. Star reads
    Brownlow votes in place of coaches votes (ruling 29)."""
    def n(k):
        v = r.get(k)
        return None if v in (None, "") else float(v)
    g = n("gm") or 0.0
    def pg(k):
        v = n(k)
        return None if v is None or g <= 0 else v / g
    m = {k: None for k in METRICS}
    m.update({"Kicks": pg("ki"), "Handballs": pg("hb"), "ContestedMarks": pg("cm"), "ContestedPossessions": pg("cp"),
              "TotalClearances": pg("cl"), "Tackles": pg("tk"), "Bounces": pg("bo"), "Goals_Avg": pg("gl"),
              "GoalAssists": pg("ga"), "Inside50s": pg("if50"), "Hitouts": pg("ho"), "FreesAgainst": pg("fa"),
              "BrownlowVotes": pg("br"),
              "Clangers": pg("cg"), "games": g, "time_on_ground": n("pct_played") if n("pct_played") is not None else n("pctp")})
    mk, cm = n("mk"), n("cm")
    # Ruling 18: missing stats are left out of the recipe. Before 1999 there
    # are no contested marks, so marks less contested marks is every mark.
    m["uncontested_marks"] = None if mk is None or g <= 0 else max(0.0, mk - (cm or 0.0)) / g
    cp, di = n("cp"), n("di")
    m["ContestedPossessionRate"] = None if cp is None or not di else 100.0 * cp / di
    gl, bh = n("gl") or 0.0, n("bh") or 0.0
    m["accuracy"] = gl / (gl + bh) if gl + bh > 0 else None   # scoring shots: AFL Tables keeps no misses
    m["_shots"] = gl + bh
    m["_off"] = (None, 0.0)
    m["_def"] = (None, 0.0)
    return m


# ------------------------------------------------------------- speed --
FAST = re.compile(r"\b(pace|speed|quick|fast|explosive|burst|jets|sprint|rapid|speedster|gas|zip|turn of speed|"
                  r"line-?breaking|acceleration|fleet)", re.I)
SLOW = re.compile(r"\b(lacks? (genuine |real |top |of )?(pace|speed)|not (overly |the )?(quick|fast|quickest|fastest)|"
                  r"slow|one-?paced|lack of (pace|speed)|limited (pace|speed)|(pace|speed) (is|was) (a|his) (concern|question|weakness))",
                  re.I)


def speed_records():
    """{(norm name): [(kind, value, club, season)]} from the speed searches
    (C:/kt/speed). gps_top_kmh is a season-best GPS speed, sprint20_s a 20 m
    sprint time; a descriptor is a scout's or reporter's words."""
    paths = (["C:/kt/speed/speed_real.csv"] + sorted(glob.glob("C:/kt/speed/pass2/b*_found.csv"))
             + ["C:/kt/speed/pass3/found.csv"])
    out = defaultdict(list)
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                kind = r["kind"]
                if kind == "descriptor":
                    t = r["value"]
                    v = -1.0 if SLOW.search(t) else (1.0 if FAST.search(t) else 0.0)
                elif kind in ("gps_top_kmh", "sprint20_s"):
                    try:
                        v = float(r["value"])
                    except ValueError:
                        continue
                else:
                    continue
                out[norm_name(r["name"])].append((kind, v, r["club"], r["season"]))
    return out


def speed_scores(recs) -> dict:
    """{norm name: standard score}, one scale for every kind of record.
    Each measured kind becomes a standard score against everyone measured
    the same way (a 20 m time turned round: faster is higher). The GPS
    lists are mostly the AFL's fastest-player lists, so its scores are
    moved by what the sprint times say about the same players. A
    descriptor counts as one standard deviation fast or slow."""
    by_kind = defaultdict(dict)
    for name, rows in recs.items():
        for kind, v, _c, _s in rows:
            if kind in ("gps_top_kmh", "sprint20_s"):
                by_kind[kind].setdefault(name, []).append(v)
    z = {}
    for kind, d in by_kind.items():
        best = {n: (max(v) if kind == "gps_top_kmh" else min(v)) for n, v in d.items()}
        vals = list(best.values())
        m = sum(vals) / len(vals)
        sd = (sum((x - m) ** 2 for x in vals) / len(vals)) ** 0.5 or 1.0
        sign = 1.0 if kind == "gps_top_kmh" else -1.0
        z[kind] = {n: sign * (v - m) / sd for n, v in best.items()}
    both = [n for n in z.get("gps_top_kmh", {}) if n in z.get("sprint20_s", {})]
    shift = 0.0
    if both:
        shift = sum(z["sprint20_s"][n] - z["gps_top_kmh"][n] for n in both) / len(both)
    out = {}
    for name, rows in recs.items():
        vals = []
        if name in z.get("gps_top_kmh", {}):
            vals.append(z["gps_top_kmh"][name] + shift)
        if name in z.get("sprint20_s", {}):
            vals.append(z["sprint20_s"][name])
        if not vals:
            d = [v for k, v, _c, _s in rows if k == "descriptor" and v != 0.0]
            if d:
                vals.append(sum(d) / len(d))
        if vals:
            out[name] = sum(vals) / len(vals)
    return out


# -------------------------------------------------------- one season --
def rate_season(players: list, speed: dict | None = None) -> None:
    """players: [{"pos": AFL position, "m": metrics, "name": full name}].
    Sets p["skills"] {skill: 1..99} and p["skill01"] {skill: 0..1}, each
    against players of his position in this list (one season)."""
    speed = speed or {}
    by_pos = defaultdict(list)
    for p in players:
        by_pos[p["pos"]].append(p)
    for pos, group in by_pos.items():
        for p in group:
            m = p["m"]
            # One-on-ones by position (ruling 5).
            off, deff = m.get("_off", (None, 0.0)), m.get("_def", (None, 0.0))
            if pos in ATTACK:
                parts = [off]
            elif pos in DEFENCE:
                parts = [deff]
            else:
                parts = [off, deff]
            parts = [(v, n) for v, n in parts if v is not None and n > 0]
            if parts:
                tot = sum(n for _v, n in parts)
                m["one_on_one"] = sum(v * n for v, n in parts) / tot
                m["_contests"] = tot
            else:
                m["one_on_one"] = None
                m["_contests"] = 0.0
            m["speed"] = speed.get(norm_name(p.get("name", "")))
    # Speed is a standard score against his position: the measured players
    # of the position set its average and spread; no record = the average.
    for pos, group in by_pos.items():
        vals = [p["m"]["speed"] for p in group if p["m"]["speed"] is not None]
        mean = sum(vals) / len(vals) if vals else 0.0
        sd = ((sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5 if len(vals) > 1 else 1.0) or 1.0
        for p in group:
            v = p["m"]["speed"]
            p["m"]["speed_z"] = 0.0 if v is None else (v - mean) / sd
    # The overall reads each count against the whole league that season, not
    # his position: 64 goals in 19 games beats 48 in 23 whoever kicked them
    # (director, 2026-11-16, Carey and Heaver 1993). The skill shown stays
    # against his position.
    lbase = [p for p in players if (p["m"].get("games") or 0) >= NORM_GAMES] or players
    league = {}
    for k in METRICS:
        vals = sorted(p["m"][k] for p in lbase if p["m"].get(k) is not None)
        if vals:
            league[k] = (_pct(vals, 0.02), _pct(vals, 0.98))
    for pos, group in by_pos.items():
        base = [p for p in group if (p["m"].get("games") or 0) >= NORM_GAMES] or group
        scale, mean = {}, {}
        for k, mode in METRICS.items():
            vals = sorted(p["m"][k] for p in base if p["m"].get(k) is not None)
            if not vals:
                continue
            mean[k] = sum(vals) / len(vals)
            scale[k] = (_pct(vals, 0.02), _pct(vals, 0.98))
        for p in group:
            m = p["m"]
            g = m.get("games") or 0.0
            q, qr = {}, {}
            for k, mode in METRICS.items():
                v = m.get(k)
                if mode == "z":
                    q[k] = qr[k] = max(0.0, min(1.0, 0.5 + m.get("speed_z", 0.0) / 4.1))
                    continue
                if v is None or k not in scale:
                    continue
                if mode == "abs":
                    lo, hi = ABS_RANGE[k]
                    q[k] = qr[k] = max(0.0, min(1.0, (v - lo) / (hi - lo)))
                    continue
                # A short sample leans to the position's average.
                if k == "accuracy":
                    w, kk = m.get("_shots", 0.0), SHRINK_SHOTS
                elif k == "one_on_one":
                    w, kk = m.get("_contests", 0.0), SHRINK_CONTESTS
                else:
                    w, kk = g, SHRINK_GAMES
                v = (v * w + kk * mean[k]) / (w + kk)
                lo, hi = scale[k]
                if mode.startswith("cap"):
                    x = v / hi if hi > 0 else 0.0
                else:
                    x = (v - lo) / (hi - lo) if hi > lo else 0.5
                # The overall sees a count in full, against the league's 98th
                # percentile (a rate against the league's 2nd-98th); the skill
                # shown stops at his position's 98th percentile (99).
                llo, lhi = league.get(k, (lo, hi))
                if mode.startswith("cap"):
                    xr = v / lhi if lhi > 0 else 0.0
                else:
                    xr = (v - llo) / (lhi - llo) if lhi > llo else 0.5
                if mode == "cap98" or not mode.startswith("cap"):
                    xr = max(0.0, min(1.0, xr))
                x = max(0.0, min(1.0, x))
                q[k] = 1.0 - x if mode.endswith("inv") else x
                qr[k] = q[k] if mode.endswith("inv") else xr
            p["q"] = q
            s01, sraw = {}, {}
            for skill, recipe in RECIPES.items():
                got = [(q[k], qr[k], w) for k, w in recipe if k in q]
                tw = sum(w for _v, _r, w in got)
                s01[skill] = sum(v * w for v, _r, w in got) / tw if got else None
                sraw[skill] = sum(r * w for _v, r, w in got) / tw if got else None
            p["skill01"] = s01
            p["skill_raw"] = sraw
        # A skill none of his stats feed: his position's average that season
        # (or 0.5 when the season keeps it for nobody).
        for skill in SKILLS:
            have = [p["skill01"][skill] for p in base if p["skill01"][skill] is not None]
            avg = sum(have) / len(have) if have else None
            for p in group:
                if p["skill01"][skill] is None:
                    p["skill01"][skill] = avg if avg is not None else 0.5
                    p["skill_raw"][skill] = p["skill01"][skill]
                    p.setdefault("filled", []).append(skill)
        for p in group:
            p["skills"] = {k: scale_attr(v) for k, v in p["skill01"].items()}


# -------------------------------------------------------- the overall --
def nnls(X, y, iters=4000):
    """Non-negative least squares (projected coordinate descent): weights
    that are each zero or more - a skill never lowers his overall."""
    n, k = len(X), len(X[0])
    w = [0.0] * k
    cols = [[X[i][j] for i in range(n)] for j in range(k)]
    sq = [sum(c * c for c in col) or 1.0 for col in cols]
    r = list(y)
    for _ in range(iters):
        delta = 0.0
        for j in range(k):
            g = sum(cols[j][i] * r[i] for i in range(n))
            nw = max(0.0, w[j] + g / sq[j])
            d = nw - w[j]
            if d:
                for i in range(n):
                    r[i] -= d * cols[j][i]
                w[j] = nw
                delta = max(delta, abs(d))
        if delta < 1e-7:
            break
    return w


def fit_weights(samples, skills, groups=None):
    """samples: [(pos, skill01 dict, target overall, games)]. Per position,
    the share each skill has in the overall (non-negative, summing to 1),
    from players of 12+ games, plus the line mapping the weighted skills
    onto the overall: overall = mid + slope * (blend - blend_mean), with the
    slope set so the blends spread as widely as the overalls do."""
    out = {}
    for pos in (groups or POSITIONS):
        rows = [(s, t) for p, s, t, g in samples if p == pos and g >= NORM_GAMES]
        if len(rows) < 20:
            continue
        ym = sum(t for _s, t in rows) / len(rows)
        xm = {k: sum(s[k] for s, _t in rows) / len(rows) for k in skills}
        X = [[s[k] - xm[k] for k in skills] for s, _t in rows]
        y = [t - ym for _s, t in rows]
        w = nnls(X, y)
        tot = sum(w) or 1.0
        share = {k: w[i] / tot for i, k in enumerate(skills)}
        blend = [sum(share[k] * s[k] for k in skills) for s, _t in rows]
        bm = sum(blend) / len(blend)
        bsd = (sum((b - bm) ** 2 for b in blend) / len(blend)) ** 0.5 or 1.0
        ysd = (sum(v * v for v in y) / len(y)) ** 0.5
        pred = [ym + (b - bm) * ysd / bsd for b in blend]
        ss_res = sum((p - t) ** 2 for p, (_s, t) in zip(pred, rows))
        ss_tot = sum(v * v for v in y) or 1.0
        # Correlation of the blend with the overall (how much it explains).
        cov = sum((b - bm) * yy for b, yy in zip(blend, y)) / len(y)
        out[pos] = {"share": share, "mid": ym, "blend_mean": bm, "slope": ysd / bsd,
                    "r": cov / (bsd * ysd) if ysd else 0.0, "n": len(rows), "rmse": (ss_res / len(rows)) ** 0.5}
    return out


def overall_from(fit_pos: dict, s01: dict) -> float:
    b = sum(fit_pos["share"][k] * s01[k] for k in fit_pos["share"])
    return fit_pos["mid"] + fit_pos["slope"] * (b - fit_pos["blend_mean"])


# ------------------------------------------- positions before 2012 --
# A season before 2012 has no AFL position. It is read from the player's
# line (data/legacy/known_lines.csv: the line he is known for) and that
# season's numbers, by the nearest players of 2012-2025 with the same
# numbers kept: the AFL position most of his 25 nearest neighbours had.
POS_FEATURES = ["ki", "mk", "hb", "gl", "bh", "ho", "tk", "ff", "fa", "rb", "if50", "cl", "cg", "cp", "cm", "mi",
                "one_pct", "bo", "ga"]
LINE_WEIGHT = 2.5   # his known line counts as much as a couple of stats


def pos_vector(r: dict, line: tuple, keep: set, season_scale: dict) -> list:
    g = float(r.get("gm") or 0) or 1.0
    v = []
    for k in POS_FEATURES:
        if k not in keep:
            continue
        x = r.get(k)
        x = 0.0 if x in (None, "") else float(x) / g
        m, sd = season_scale[k]
        v.append((x - m) / sd)
    pos, pos2 = line or ("", "")
    for ln in ("FWD", "MID", "DEF", "RUC"):
        v.append(LINE_WEIGHT * (1.0 if pos == ln else 0.5 if pos2 == ln else 0.0))
    return v


def season_scale(rows: list, keep: set) -> dict:
    out = {}
    for k in POS_FEATURES:
        if k not in keep:
            continue
        xs = []
        for r in rows:
            g = float(r.get("gm") or 0)
            if g >= 5 and r.get(k) not in (None, ""):
                xs.append(float(r[k]) / g)
        m = sum(xs) / len(xs) if xs else 0.0
        sd = ((sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5 if xs else 1.0) or 1.0
        out[k] = (m, sd)
    return out


def knn_votes(train: list, v: list, k: int = 25) -> dict:
    """train: [(vector, position)]. Each position's share of the k nearest votes."""
    d = sorted(((sum((a - b) ** 2 for a, b in zip(tv, v)), p) for tv, p in train))[:k]
    votes = defaultdict(float)
    for dist, p in d:
        votes[p] += 1.0 / (1.0 + dist)
    total = sum(votes.values())
    return {p: x / total for p, x in votes.items()}


def knn_position(train: list, v: list, k: int = 25) -> str:
    votes = knn_votes(train, v, k)
    return max(votes, key=votes.get)


def calibrated_positions(votes: list, target: dict, rounds: int = 200) -> list:
    """One position per player, with the season's mix held to `target`
    (each position's share of 2012+ players).

    Nearest-neighbour votes alone almost never pick a position that sits
    between two bigger ones: a Mid-Forward's neighbours split between
    Midfielder, Gen. Forward and Mid-Forward, so 2012+ seasons lose most of
    their Mid-Forwards (6% of players) when re-guessed. Scaling each
    position's votes until the season's count matches its share keeps the
    mix real; each player still goes to the position his votes favour most
    after scaling."""
    scale = {p: 1.0 for p in target}
    n = len(votes)
    def pick(v):
        return max(v, key=lambda p: v[p] * scale.get(p, 1.0))
    for _ in range(rounds):
        got = defaultdict(int)
        for v in votes:
            got[pick(v)] += 1
        for p in scale:
            scale[p] *= ((target[p] * n + 0.5) / (got[p] + 0.5)) ** 0.3
    return [pick(v) for v in votes]
