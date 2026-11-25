#!/usr/bin/env python3
"""
The 18 attributes of the rating rebuild (Director Bible 4.2.30a,
docs/RATING_REBUILD.md §2): each real player's attributes from his Wheelo
season, on one scale for every position.

  data/attributes_2026.csv
      club,first,last,src,apos,speed_src,<the 18 attributes>: one row per
      listed player (data/players_enriched_2026.csv and the list additions),
      from his 2026 season or, if he missed 2026, his last season (src).

The scale (approved 2026-11-25). A rate: the league's 2nd percentile that
season is 1, its 98th is 99. A count a game: zero is 1, the league's 98th
percentile is 99. The league is that season's players with 12+ games. A
short season leans to his position's average over 5 games (one-on-ones over
10 contests, goalkicking over 14 shots). A stat the season does not keep is
left out of the recipe; an attribute with none of its stats is his
position's average.

Speed, Strength and Work Rate are the director's own rules of 2026-11-25:
  Speed      measured (GPS top speed): 32.5 km/h = 70 up to 36.0+ km/h = 98,
             a straight line (speed_src gps). No GPS but a combine 20 m
             sprint time: 2.80 s = 90, 3.10 s = 50, a straight line (20m).
             Neither: Small (Gen Def, Gen Fwd) 62, Mid (Mid, Mid-Fwd) 56,
             Key (KD, KF) 45, Ruck 32, plus 0 to +10 from bounces and
             pressure acts a game, capped at 68 (est).
  Strength   half weight for his height (his weight against the list's line
             for his height), half contested possessions a game.
  Work Rate  30% pressure acts + 25% bounces + 25% (inside 50s + rebound 50s)
             + 20% uncontested possessions, each a game, measured against
             what his position, height and weight usually produce.

    python3 tools/wheelo/attributes.py            # writes the file
    python3 tools/wheelo/attributes.py --check    # prints the sanity sample
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

sys.path.insert(0, os.path.join(ROOT, "tools", "legacy_1990s"))
import build_start as B  # noqa: E402

DATA = os.path.join(ROOT, "data")
# start -> (season rated, players file, list additions' stats, list additions'
# bodies, output), under data/. The players file is its own body file.
STARTS = {
    "2026": (2026, "players_enriched_2026.csv", "list_additions_stats.csv", "list_additions_2026.csv",
             "attributes_2026.csv"),
    "2020": (2019, "legacy/2020/players_2020.csv", "legacy/2020/list_addition_stats_2020.csv",
             "legacy/2020/list_additions_2020.csv", "legacy/2020/attributes_2020.csv"),
    "2010": (2009, "legacy/2010/players_2010.csv", "legacy/2010/list_addition_stats_2010.csv",
             "legacy/2010/list_additions_2010.csv", "legacy/2010/attributes_2010.csv"),
    "2000": (1999, "legacy/2000/players_2000.csv", "legacy/2000/list_addition_stats_2000.csv",
             "legacy/2000/list_additions_2000.csv", "legacy/2000/attributes_2000.csv"),
    "1990": (1989, "legacy/1990/players_1990.csv", "legacy/1990/list_addition_stats_1990.csv",
             "legacy/1990/list_additions_1990.csv", "legacy/1990/attributes_1990.csv"),
}
OUT = os.path.join(DATA, STARTS["2026"][4])   # review_lists.py reads it

# Storage order, by the card's four groups (§2).
ATTRS = ["speed", "endurance", "strength", "work_rate",
         "kicking", "handballing", "marking", "contested_marking", "one_on_one", "contested_ball",
         "goalkicking", "ruck",
         "vision", "reading_play", "pressure", "forward_craft",
         "discipline", "durability"]

# Attribute -> [(metric, weight)]: the approved recipes (§2). Speed, Strength
# and Work Rate are worked out on their own below.
RECIPES = {
    "endurance": [("TimeOnGround", 100)],
    "kicking": [("KickingEfficiency", 50), ("KickMetresGainedPerKick", 50)],
    "handballing": [("HandballEfficiency", 60), ("HandballMetresGained", 40)],
    "marking": [("uncontested_marks", 100)],
    "contested_marking": [("ContestedMarks", 50), ("ContestOffensiveWinPercentage", 50)],
    "one_on_one": [("def_win", 50), ("Spoils", 30), ("OnePercenters", 20)],
    "contested_ball": [("ContestedPossessions", 30), ("GroundBallGets", 20), ("TotalClearances", 35),
                       ("ContestedPossessionRate", 15)],
    "goalkicking": [("shot_quality", 100)],
    "ruck": [("Hitouts", 35), ("HitoutsToAdvantage", 30), ("HitoutsWinPercentage", 20), ("TotalClearances", 15)],
    "vision": [("GoalAssists", 40), ("ScoreInvolvements", 25), ("ScoreLaunches", 15), ("Inside50s", 20)],
    "reading_play": [("Intercepts", 100)],
    "pressure": [("PressureActs", 70), ("Tackles", 30)],
    "forward_craft": [("Goals_Avg", 50), ("MarksInside50", 30), ("MarksOnLead", 20)],
    "discipline": [("FreesAgainst", 70), ("Clangers", 30)],
}
# "rate" (2nd-98th percentile) or "count" (zero to the 98th percentile);
# "inv" is less-is-better. The sample each shrinks over: games unless named.
METRICS = {
    "TimeOnGround": "rate", "KickingEfficiency": "rate", "KickMetresGainedPerKick": "rate",
    "HandballEfficiency": "rate", "HandballMetresGained": "count", "uncontested_marks": "count",
    "ContestedMarks": "count", "ContestOffensiveWinPercentage": "rate", "def_win": "rate",
    "Spoils": "count", "OnePercenters": "count", "ContestedPossessions": "count", "GroundBallGets": "count",
    "TotalClearances": "count", "ContestedPossessionRate": "rate", "shot_quality": "rate",
    "Hitouts": "count", "HitoutsToAdvantage": "count", "HitoutsWinPercentage": "rate",
    "GoalAssists": "count", "ScoreInvolvements": "count", "ScoreLaunches": "count", "Inside50s": "count",
    "Intercepts": "count", "PressureActs": "count", "Tackles": "count", "MarksInside50": "count",
    "MarksOnLead": "count", "Goals_Avg": "count", "FreesAgainst": "count inv", "Clangers": "count inv",
    # Work Rate and the speed bump.
    "Bounces": "count", "io50": "count", "uncontested_poss": "count",
}
SAMPLE = {"ContestOffensiveWinPercentage": ("_off_n", M.SHRINK_CONTESTS),
          "def_win": ("_def_n", M.SHRINK_CONTESTS), "shot_quality": ("_shots", M.SHRINK_SHOTS)}

WORK_RATE = [("PressureActs", 30), ("Bounces", 25), ("io50", 25), ("uncontested_poss", 20)]

SPEED_LO_KMH, SPEED_LO = 32.5, 70.0
SPEED_HI_KMH, SPEED_HI = 36.0, 98.0
SPEED_BASE = {"Gen. Defender": 62, "Gen. Forward": 62, "Midfielder": 56, "Mid-Forward": 56,
              "Key Defender": 45, "Key Forward": 45, "Ruck": 32}
SPEED_BUMP, SPEED_EST_CAP = 10.0, 68
SPRINT_FAST_S, SPRINT_FAST = 2.80, 90.0   # director 2026-11-25, question box
SPRINT_SLOW_S, SPRINT_SLOW = 3.10, 50.0

IMPORT = "[remap]\n\nimporter=\"keep\"\n"


def _f(v):
    try:
        return None if v in (None, "") else float(v)
    except ValueError:
        return None


def inputs(r: dict) -> dict:
    """A Wheelo row's per-game metrics under the recipe names."""
    g = r.get("Matches") or 0.0
    m = {k: r.get(k) for k in METRICS if k in r}
    m["games"] = g
    mk, cm = r.get("Marks"), r.get("ContestedMarks")
    m["uncontested_marks"] = None if mk is None or cm is None else max(0.0, mk - cm)
    # A one-on-one percentage with no contests, or a hit-out win rate with
    # no hit-outs, says nothing: left out.
    off_n = (r.get("ContestOffensiveOneOnOnes") or 0.0) * g
    def_n = (r.get("ContestDefensiveOneOnOnes") or 0.0) * g
    m["_off_n"], m["_def_n"] = off_n, def_n
    if off_n <= 0:
        m["ContestOffensiveWinPercentage"] = None
    dl = r.get("ContestDefensiveLossPercentage")
    m["def_win"] = None if dl is None or def_n <= 0 else 100.0 - dl
    if not r.get("Hitouts"):
        m["HitoutsWinPercentage"] = None
    # Goalkicking: expected-score rating a shot from 2021, goals out of shots before.
    shots = (r.get("ShotsAtGoal") or 0.0) * g
    goals = (r.get("Goals_Avg") or 0.0) * g
    xs = r.get("xScoreRatingPerShot")
    m["shot_quality"] = xs if xs is not None else (goals / shots if shots > 0 else None)
    m["_shots"] = shots
    i50, r50 = r.get("Inside50s"), r.get("Rebound50s")
    m["io50"] = None if i50 is None and r50 is None else (i50 or 0.0) + (r50 or 0.0)
    # Uncontested possessions from contested possessions and their share.
    cp, rate = r.get("ContestedPossessions"), r.get("ContestedPossessionRate")
    m["uncontested_poss"] = None if cp is None or not rate else cp * (100.0 - rate) / rate
    m["TimeOnGround"] = r.get("TimeOnGround")
    return m


class Season:
    """One Wheelo season (2012 on): its league scale (12+ game players) and
    position averages, and each player's metrics a game."""
    RECIPES, MODES, SAMPLE, WORK_RATE = RECIPES, METRICS, SAMPLE, WORK_RATE
    CP, BOUNCES, PRESSURE_ACTS = "ContestedPossessions", "Bounces", "PressureActs"

    def __init__(self, year: int):
        self.year = year
        self.rows = W.seasons().get(year, [])
        self.matcher = W.Matcher(year)        # also sets row["club"]
        self.m = {id(r): inputs(r) for r in self.rows}
        self._scale([(self.m[id(r)], r["pos"]) for r in self.rows if (r.get("Matches") or 0) >= M.NORM_GAMES])
        self.club_games = defaultdict(float)
        for r in self.rows:
            self.club_games[r["club"]] = max(self.club_games[r["club"]], r.get("Matches") or 0.0)

    def _scale(self, base):
        """base: [(metrics, position)] of the season's players with 12+ games.
        A rate with its own sample (shots, one-on-ones) takes its percentiles
        after the lean to the position average, the values players are rated
        on: raw, a one-shot player's 0% or 100% would set the ends."""
        self.scale, self.mean = {}, defaultdict(dict)
        by_pos = defaultdict(list)
        for m, pos in base:
            by_pos[pos].append(m)
        for pos, ms in by_pos.items():
            for k in self.MODES:
                vals = [x[k] for x in ms if x.get(k) is not None]
                if vals:
                    self.mean[pos][k] = sum(vals) / len(vals)
        for k in self.MODES:
            if k in self.SAMPLE:
                wk, kk = self.SAMPLE[k]
                vals = sorted((m[k] * (m.get(wk) or 0.0) + kk * self.mean[pos][k]) / ((m.get(wk) or 0.0) + kk)
                              for m, pos in base if m.get(k) is not None)
            else:
                vals = sorted(m[k] for m, _p in base if m.get(k) is not None)
            if vals:
                self.scale[k] = (M._pct(vals, 0.02), M._pct(vals, 0.98))

    def find(self, first, last, club, gm=None, ki=None):
        """His row that season: {id, m, pos, games, club, club_games}, or None."""
        w = self.matcher.find(first, last, club)
        if w is None:
            return None
        return {"id": w["PlayerId"], "m": self.m[id(w)], "pos": w["pos"], "games": w.get("Matches") or 0.0,
                "club": w["club"], "club_games": self.club_games.get(w["club"]) or 0.0}

    def keeps(self, k) -> bool:
        return bool(k) and k in self.scale

    def unit(self, m: dict, pos: str, k: str):
        """Metric k on 0..1 (league scale), after the short-sample lean."""
        v = m.get(k)
        if v is None or k not in self.scale:
            return None
        mean = self.mean.get(pos, {}).get(k)
        if mean is not None:
            wk, kk = self.SAMPLE.get(k, ("games", M.SHRINK_GAMES))
            w = m.get(wk) or 0.0
            v = (v * w + kk * mean) / (w + kk)
        lo, hi = self.scale[k]
        mode = self.MODES[k]
        if mode.startswith("count"):
            x = v / hi if hi > 0 else 0.0
        else:
            x = (v - lo) / (hi - lo) if hi > lo else 0.5
        x = max(0.0, min(1.0, x))
        return 1.0 - x if mode.endswith("inv") else x


# --------------------------------------------- seasons before Wheelo --
# The past starts (director 2026-11-25, "Nearest stats"): AFL Tables counts.
# Each 2026 stat that AFL Tables kept keeps its recipe weight; Kicking,
# Handballing and Marking, whose stats it never kept, take the nearest count
# (kicks, handballs, marks: uncontested marks once contested marks are kept).
# Reading the play (intercepts) was never kept: his position's average.
TABLES_RECIPES = {
    "endurance": [("pct_played", 100)],
    "kicking": [("ki", 100)],
    "handballing": [("hb", 100)],
    "marking": [("unc_mk", 100)],
    "contested_marking": [("cm", 50)],
    "one_on_one": [("one_pct", 20)],
    "contested_ball": [("cp", 30), ("cl", 35), ("cp_rate", 15)],
    "goalkicking": [("gl_rate", 100)],
    "ruck": [("ho", 35), ("cl", 15)],
    "vision": [("ga", 40), ("if50", 20)],
    "reading_play": [],
    "pressure": [("tk", 30)],
    "forward_craft": [("gl", 50), ("mi", 30)],
    "discipline": [("fa", 70), ("cg", 30)],
}
TABLES_METRICS = {
    "pct_played": "rate", "ki": "count", "hb": "count", "unc_mk": "count", "cm": "count", "one_pct": "count",
    "cp": "count", "cl": "count", "cp_rate": "rate", "gl_rate": "rate", "ho": "count", "ga": "count",
    "if50": "count", "tk": "count", "gl": "count", "mi": "count", "fa": "count inv", "cg": "count inv",
    "bo": "count", "io50": "count", "up": "count",
}
TABLES_SAMPLE = {"gl_rate": ("_shots", M.SHRINK_SHOTS)}
TABLES_WORK_RATE = [("bo", 25), ("io50", 25), ("up", 20)]   # pressure acts were never kept
# What AFL Tables kept, from each season on (tools/wheelo/fit.py TIERS).
TABLES_ALL = ["gm", "ki", "mk", "hb", "di", "gl", "bh", "ho", "tk", "rb", "if50", "cl", "cg", "ff", "fa", "br",
              "cp", "up", "cm", "mi", "one_pct", "bo", "ga", "pct_played"]
TABLES_TIERS = {
    "2003": set(TABLES_ALL),
    "1999": set(TABLES_ALL) - {"ga", "pct_played"},
    "1998": set(TABLES_ALL) - {"bo", "cm", "cp", "ga", "mi", "one_pct", "pct_played", "up"},
    "1987": {"gm", "ki", "mk", "hb", "di", "gl", "bh", "ho", "tk", "ff", "fa", "br"},
}
SUM_KEYS = [k for k in TABLES_ALL if k != "pct_played"]
_tables: dict = {}


def tables_tier(year: int) -> str:
    return "2003" if year >= 2003 else "1999" if year >= 1999 else "1998" if year >= 1998 else "1987"


def tables_by_year():
    if "by_year" not in _tables:
        _tables["by_year"] = B.load_seasons()
    return _tables["by_year"]


def tables_merged(year: int) -> dict:
    """{afltables_id: row} of a season, a player traded mid-season summed."""
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


def tables_inputs(r: dict, keep: set) -> dict:
    """An AFL Tables season row's counts a game, under TABLES_METRICS names.
    AFL Tables leaves a zero blank, so a blank in a kept column is 0."""
    g = B.num(r.get("gm")) or 0.0

    def tot(k):
        return None if k not in keep else (B.num(r.get(k)) or 0.0)

    def pg(k):
        v = tot(k)
        return None if v is None or g <= 0 else v / g
    m = {"games": g}
    for k in ("ki", "hb", "cm", "one_pct", "cp", "cl", "ho", "ga", "if50", "tk", "gl", "mi", "fa", "cg", "bo", "up"):
        m[k] = pg(k)
    mk = pg("mk")
    m["unc_mk"] = None if mk is None else max(0.0, mk - m["cm"]) if m["cm"] is not None else mk
    cp, up = tot("cp"), tot("up")
    m["cp_rate"] = 100.0 * cp / (cp + up) if cp is not None and up is not None and cp + up > 0 else None
    gl, bh = tot("gl"), tot("bh")
    shots = (gl or 0.0) + (bh or 0.0)
    m["gl_rate"] = gl / shots if gl is not None and bh is not None and shots > 0 else None
    m["_shots"] = shots
    rb = pg("rb")
    m["io50"] = None if m["if50"] is None and rb is None else (m["if50"] or 0.0) + (rb or 0.0)
    m["pct_played"] = B.num(r.get("pct_played")) if "pct_played" in keep else None
    return m


def position_train(tier: str) -> list:
    """2012-2025 AFL Tables rows with their Wheelo position, on a tier's stats."""
    key = ("train", tier)
    if key not in _tables:
        keep, train = TABLES_TIERS[tier], []
        for y in range(W.FIRST, W.LAST):
            rows = tables_by_year().get(y, [])
            mt, sc = W.Matcher(y), M.season_scale(rows, keep)
            for r in rows:
                if float(r["gm"] or 0) < 5:
                    continue
                w = mt.find(r["first"], r["last"], B.code(r["club"]))
                if w and w["pos"]:
                    train.append((M.pos_vector(r, B.POS_BY_ID.get(r["afltables_id"]), keep, sc), w["pos"]))
        _tables[key] = train
    return _tables[key]


def tables_positions(year: int, rows: dict, keep: set) -> dict:
    """{afltables_id: AFL position}: read from his known line and the
    season's numbers, the season's mix held to 2012+'s (seasons_rated.py)."""
    tier = tables_tier(year)
    sc = M.season_scale(list(rows.values()), keep)
    train = position_train(tier)
    ids, votes = [], []
    for pid, r in rows.items():
        if float(r["gm"] or 0) <= 0:
            continue
        ids.append(pid)
        votes.append(M.knn_votes(train, M.pos_vector(r, B.POS_BY_ID.get(pid), keep, sc)))
    share = defaultdict(int)
    for _v, p in train:
        share[p] += 1
    target = {p: share[p] / len(train) for p in W.POSITIONS}
    return dict(zip(ids, M.calibrated_positions(votes, target)))


def nearest_position(year: int, r: dict) -> str:
    """A Wheelo row with no position (a handful of games): the position his
    AFL Tables numbers that season are nearest to, the way seasons before
    2012 get theirs."""
    keep = TABLES_TIERS[tables_tier(year)]
    key = ("scale", year)
    if key not in _tables:
        _tables[key] = M.season_scale(list(tables_merged(year).values()), keep)
    r = dict(r, one_pct=r.get("one_pct", r.get("onepct")))   # the list files spell it onepct
    return M.knn_position(position_train(tables_tier(year)), M.pos_vector(r, None, keep, _tables[key]))


class TablesSeason(Season):
    """One season before Wheelo, from AFL Tables (the past starts)."""
    RECIPES, MODES, SAMPLE, WORK_RATE = TABLES_RECIPES, TABLES_METRICS, TABLES_SAMPLE, TABLES_WORK_RATE
    CP, BOUNCES, PRESSURE_ACTS = "cp", "bo", ""

    def __init__(self, year: int):
        self.year = year
        self.keep = TABLES_TIERS[tables_tier(year)]
        self.rows = tables_merged(year)
        self.pos = tables_positions(year, self.rows, self.keep)
        self.m = {pid: tables_inputs(r, self.keep) for pid, r in self.rows.items()}
        self._scale([(self.m[pid], self.pos[pid]) for pid, r in self.rows.items()
                     if pid in self.pos and (B.num(r["gm"]) or 0) >= M.NORM_GAMES])
        self.club_games = defaultdict(float)
        for r in tables_by_year().get(year, []):
            c = B.code(r["club"])
            self.club_games[c] = max(self.club_games[c], B.num(r["gm"]) or 0.0)
        self.by_name_club, self.by_name, self.by_last_club = {}, defaultdict(list), defaultdict(list)
        self.by_line = defaultdict(list)
        for pid, r in self.rows.items():
            f, l, c = W.norm(r["first"]), W.norm(r["last"]), B.code(r["club"])
            self.by_name_club[(f + l, c)] = pid
            self.by_name[f + l].append(pid)
            self.by_last_club[(l, c)].append((f, pid))
            self.by_line[(l, str(int(float(r["gm"] or 0))), str(int(float(r["ki"] or 0))))].append(pid)
        # A player traded mid-season: his first club's rows too.
        for r in tables_by_year().get(year, []):
            self.by_name_club.setdefault((W.norm(r["first"]) + W.norm(r["last"]), B.code(r["club"])),
                                         r["afltables_id"])

    def _pid(self, first, last, club, gm=None, ki=None):
        """tools/wheelo/build.py SeasonIndex.find."""
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

    def find(self, first, last, club, gm=None, ki=None):
        pid = self._pid(first, last, club, gm, ki)
        if pid is None or pid not in self.pos:
            return None
        r = self.rows[pid]
        c = B.code(r["club"])
        return {"id": pid, "m": self.m[pid], "pos": self.pos[pid], "games": B.num(r["gm"]) or 0.0, "club": c,
                "club_games": self.club_games.get(c) or 0.0}


_seasons: dict = {}


def season(year: int) -> Season:
    if year not in _seasons:
        _seasons[year] = Season(year) if year >= W.FIRST else TablesSeason(year)
    return _seasons[year]


def blend(s: Season, m: dict, pos: str, recipe) -> float | None:
    got = [(s.unit(m, pos, k), w) for k, w in recipe]
    got = [(x, w) for x, w in got if x is not None]
    tw = sum(w for _x, w in got)
    return sum(x * w for x, w in got) / tw if got else None


def least_squares(X, y):
    """Normal equations, Gauss-Jordan (a handful of columns)."""
    n = len(X[0])
    A = [[sum(r[i] * r[j] for r in X) for j in range(n)] for i in range(n)]
    b = [sum(r[i] * t for r, t in zip(X, y)) for i in range(n)]
    for i in range(n):
        piv = A[i][i] or 1e-12
        A[i] = [a / piv for a in A[i]]
        b[i] /= piv
        for k in range(n):
            if k != i and A[k][i]:
                f = A[k][i]
                A[k] = [a - f * c for a, c in zip(A[k], A[i])]
                b[k] -= f * b[i]
    return b


# ------------------------------------------------------------- speed --
def club_code(club: str) -> str:
    """The speed records spell a club as its code (WBD), its name (Western
    Bulldogs), its full name (West Coast Eagles, GWS Giants) or not at all."""
    c = (club or "").strip()
    codes = {r["code"]: r["name"] for r in read(os.path.join(DATA, "clubs.csv"))}
    if c.upper() in codes:
        return c.upper()
    for code, nm in codes.items():
        if c.lower().startswith(nm.lower()) or (c.split() and c.split()[0].upper() == code):
            return code
    return c


def best_records(list_names: dict, kind: str, best, last_season: int) -> dict:
    """{(norm name, club code) or norm name: his best record of `kind`} from
    C:/kt/speed (best = max for km/h, min for a sprint time), taken no later
    than the season the start rates (a 2020 start knows nothing from 2021).
    A name two listed players share is matched on club as well; a record of
    that name with no club matches neither."""
    out = {}
    for name, rows in M.speed_records().items():
        for k, v, club, rec_season in rows:
            if k != kind or int(rec_season or 0) > last_season:
                continue
            key = (name, club_code(club)) if list_names.get(name, 0) > 1 else name
            out[key] = best(out[key], v) if key in out else v
    return out


def speed_from_kmh(kmh: float) -> int:
    x = SPEED_LO + (SPEED_HI - SPEED_LO) * (kmh - SPEED_LO_KMH) / (SPEED_HI_KMH - SPEED_LO_KMH)
    return int(round(max(1.0, min(SPEED_HI, x))))


def speed_from_sprint(sec: float) -> int:
    x = SPRINT_FAST + (SPRINT_SLOW - SPRINT_FAST) * (sec - SPRINT_FAST_S) / (SPRINT_SLOW_S - SPRINT_FAST_S)
    return int(round(max(1.0, min(SPEED_HI, x))))


# -------------------------------------------------------------- build --
def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def listed_players(start: str):
    """Every listed player of a start with his season's row:
    [(list row, body row, season, found)], and the ones not found."""
    data_season, players_f, adds_f, adds_body_f, _out = STARTS[start]
    out, missed, seen = [], [], set()
    for stats_f, body_f in ((players_f, players_f), (adds_f, adds_body_f)):
        body = {(r["club"], r["first"], r["last"]): r for r in read(os.path.join(DATA, body_f))}
        for r in read(os.path.join(DATA, stats_f)):
            key = (r["club"], r["first"], r["last"])
            if key in seen:
                continue
            seen.add(key)
            year = int(r.get("src") or data_season)
            got = season(year).find(r["first"], r["last"], r["club"], r.get("gm"), r.get("ki"))
            if got is None:
                missed.append("%s %s %s %d" % (r["club"], r["first"], r["last"], year))
                continue
            out.append((r, body.get(key, {}), year, got))
    # Two listed players on one season row (two Bailey Williams at different
    # clubs): the one at the row's club keeps it.
    by_row = defaultdict(list)
    for item in out:
        by_row[(item[2], item[3]["id"])].append(item)
    drop = set()
    for same in by_row.values():
        if len(same) > 1:
            for item in same:
                if item[0]["club"] != item[3]["club"]:
                    drop.add(id(item))
                    missed.append("%s %s %s %d (his name's row is %s's)" % (
                        item[0]["club"], item[0]["first"], item[0]["last"], item[2], item[3]["club"]))
    return [item for item in out if id(item) not in drop], missed


UNKEPT = "unkept"   # a stat the season never kept: left out, not averaged in


def build(start: str, ref: dict | None = None):
    """The start's rows, and info. ref: 2026's position averages (0..1), for an
    attribute none of the start's seasons recorded."""
    data_season = STARTS[start][0]
    players, missed = listed_players(start)
    names = defaultdict(int)
    for r, _b, _y, _g in players:
        names[W.norm(r["first"] + r["last"])] += 1
    gps = best_records(names, "gps_top_kmh", max, data_season)
    sprint = best_records(names, "sprint20_s", min, data_season)
    rows = []
    for r, body, year, got in players:
        s = season(year)
        m, pos = got["m"], got["pos"] or nearest_position(year, r)
        h, kg = _f(body.get("height_cm")), _f(body.get("weight_kg"))
        a01 = {k: blend(s, m, pos, rec) for k, rec in s.RECIPES.items()}
        for key, metric in (("_cp", s.CP), ("_bo", s.BOUNCES), ("_pa", s.PRESSURE_ACTS)):
            a01[key] = s.unit(m, pos, metric) if s.keeps(metric) else UNKEPT
        a01["_wr"] = blend(s, m, pos, s.WORK_RATE)
        cg = got["club_games"]
        a01["durability"] = min(1.0, got["games"] / cg) if cg else None
        nm = W.norm(r["first"] + r["last"])
        rows.append({"r": r, "year": year, "pos": pos, "h": h, "kg": kg, "a01": a01, "games": got["games"],
                     "kmh": gps.get((nm, r["club"])) or gps.get(nm),
                     "sprint": sprint.get((nm, r["club"])) or sprint.get(nm)})
    wr_measured = any(p["a01"]["_wr"] is not None for p in rows)

    def fill(k):
        """A missing value: his position's average over the start's players
        with 12+ games; if no season of the start recorded it, 2026's."""
        by_pos = defaultdict(list)
        for p in rows:
            v = p["a01"][k]
            if v is not None and v is not UNKEPT and p["games"] >= M.NORM_GAMES:
                by_pos[p["pos"]].append(v)
        for p in rows:
            if p["a01"][k] is None:
                v = by_pos.get(p["pos"])
                if v:
                    p["a01"][k] = sum(v) / len(v)
                elif ref is not None and k in ref.get(p["pos"], {}):
                    p["a01"][k] = ref[p["pos"]][k]
                    p.setdefault("never", []).append(k)
                else:
                    p["a01"][k] = 0.5
                p.setdefault("filled", []).append(k)
    for k in list(RECIPES) + ["durability", "_cp", "_wr", "_bo", "_pa"]:
        fill(k)
    # Strength: weight for his height against the list's line, and contested
    # possessions where the season kept them.
    body = [p for p in rows if p["h"] and p["kg"]]
    mh = sum(p["h"] for p in body) / len(body)
    mw = sum(p["kg"] for p in body) / len(body)
    slope = sum((p["h"] - mh) * (p["kg"] - mw) for p in body) / sum((p["h"] - mh) ** 2 for p in body)
    for p in body:
        p["w4h_kg"] = p["kg"] - (mw + slope * (p["h"] - mh))
    res = sorted(p["w4h_kg"] for p in body)
    rlo, rhi = M._pct(res, 0.02), M._pct(res, 0.98)
    for p in rows:
        parts = [] if p["a01"]["_cp"] is UNKEPT else [p["a01"]["_cp"]]
        if "w4h_kg" in p:
            parts.append(max(0.0, min(1.0, (p["w4h_kg"] - rlo) / (rhi - rlo))))
        p["a01"]["strength"] = sum(parts) / len(parts) if parts else None
    fill("strength")
    # Work Rate: against what his position, height and weight usually
    # produce (least squares over players with 12+ games); a player missing
    # his weight, or height too, against position and what he has. A start
    # whose seasons kept none of its stats: his position's 2026 average.
    if wr_measured:
        poss = sorted({p["pos"] for p in rows})

        def feats(p, cols):
            f = [1.0 if p["pos"] == q else 0.0 for q in poss]
            if "h" in cols:
                f.append(p["h"] - 188.0)
            if "kg" in cols:
                f.append(p["kg"] - 84.0)
            return f
        base = [p for p in rows if p["games"] >= M.NORM_GAMES]
        fits = {}
        for cols in (("h", "kg"), ("h",), ()):
            b = [p for p in base if all(p[c] for c in cols)]
            fits[cols] = least_squares([feats(p, cols) for p in b], [p["a01"]["_wr"] for p in b])
        for p in rows:
            cols = ("h", "kg") if p["h"] and p["kg"] else ("h",) if p["h"] else ()
            p["wr_res"] = p["a01"]["_wr"] - sum(c * f for c, f in zip(fits[cols], feats(p, cols)))
        rs = sorted(p["wr_res"] for p in base)
        wlo, whi = M._pct(rs, 0.02), M._pct(rs, 0.98)
        for p in rows:
            p["a01"]["work_rate"] = max(0.0, min(1.0, (p["wr_res"] - wlo) / (whi - wlo)))
    else:
        for p in rows:
            p["a01"]["work_rate"] = None
        fill("work_rate")
    # Attributes 1..99; Speed by the director's rule. The estimate's bump
    # uses bounces and pressure acts where the season kept them, else none.
    out = []
    for p in rows:
        a = {k: M.scale_attr(p["a01"][k]) for k in ATTRS if k != "speed"}
        if p["kmh"]:
            a["speed"], src = speed_from_kmh(p["kmh"]), "gps"
        elif p["sprint"]:
            a["speed"], src = speed_from_sprint(p["sprint"]), "20m"
        else:
            kept = [p["a01"][k] for k in ("_bo", "_pa") if p["a01"][k] is not UNKEPT]
            bump = SPEED_BUMP * sum(kept) / len(kept) if kept else 0.0
            a["speed"], src = min(SPEED_EST_CAP, int(round(SPEED_BASE.get(p["pos"], 56) + bump))), "est"
        r = p["r"]
        row = {"club": r["club"], "first": r["first"], "last": r["last"], "src": p["year"], "apos": p["pos"],
               "speed_src": src}
        row.update({k: a[k] for k in ATTRS})
        row["_p"] = p
        out.append(row)
    # This start's position averages (0..1) over players with 12+ games.
    means = defaultdict(dict)
    for k in [x for x in ATTRS if x != "speed"] + ["_wr"]:
        by_pos = defaultdict(list)
        for p in rows:
            if p["games"] >= M.NORM_GAMES and p["a01"].get(k) not in (None, UNKEPT):
                by_pos[p["pos"]].append(p["a01"][k])
        for pos, v in by_pos.items():
            means[pos][k] = sum(v) / len(v)
    s = season(data_season)
    info = {"w4h_line": (mw, slope, mh, rlo, rhi), "missed": missed, "means": dict(means)}
    info["league98"] = {k: s.scale[k][1] for k in ("uncontested_poss", "Bounces", "PressureActs", "io50",
                                                     "ContestedPossessions", "up", "bo", "cp", "tk", "ki")
                        if k in s.scale}
    info["never"] = sorted({k for p in rows for k in p.get("never", [])})
    return out, info


def write(start: str, rows):
    path = os.path.join(DATA, STARTS[start][4])
    cols = ["club", "first", "last", "src", "apos", "speed_src"] + ATTRS
    with open(path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    imp = path + ".import"
    if not os.path.exists(imp):
        with open(imp, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(IMPORT)
    return path


SAMPLE_NAMES = {
    "2026": ["Nick Daicos", "Errol Gulden", "Nick Blakey", "Kysaiah Pickett", "Charlie Curnow", "Max Gawn"],
    "2020": ["Nat Fyfe", "Patrick Dangerfield", "Dustin Martin", "Lachie Neale", "Tom Hawkins", "Max Gawn"],
    "2010": ["Gary Ablett", "Chris Judd", "Nick Riewoldt", "Lance Franklin", "Dean Cox", "Adam Goodes"],
    "2000": ["Wayne Carey", "Shane Woewodin", "James Hird", "Michael Voss", "Tony Lockett", "Nathan Buckley"],
    "1990": ["Gary Ablett", "Jason Dunstall", "Tony Lockett", "Paul Couch", "Greg Williams", "Simon Madden"],
}


def check(start, rows, info):
    mw, slope, mh, rlo, rhi = info["w4h_line"]
    print("== start %s (season %d): %d players" % (start, STARTS[start][0], len(rows)))
    print("weight line: %.1f kg + %.2f kg a cm over %.0f cm; 2nd pct %+.1f kg, 98th %+.1f kg" % (mw, slope, mh, rlo, rhi))
    print("league 98th a game:", "  ".join("%s %.2f" % kv for kv in info["league98"].items()))
    print("never recorded (2026 position average):", ", ".join(info["never"]) or "none")
    print("not found in their season:", len(info["missed"]), "; ".join(info["missed"][:20]))
    for nm in SAMPLE_NAMES.get(start, []):
        for r in rows:
            if r["first"] + " " + r["last"] == nm:
                p = r["_p"]
                how = {"gps": "%.1f km/h" % (p["kmh"] or 0), "20m": "%.2f s for 20 m" % (p["sprint"] or 0),
                       "est": "estimate"}[r["speed_src"]]
                print("  %-20s %s %-13s %s" % (nm, r["club"], r["apos"], " ".join(
                    "%s %d" % (k[:4], r[k]) for k in ATTRS)) + "  (speed: %s)" % how)
    n = defaultdict(int)
    for r in rows:
        n[r["speed_src"]] += 1
    print("speed from:", dict(n))


def main():
    want = [a for a in sys.argv[1:] if a in STARTS] or list(STARTS)
    ref = None
    for start in ["2026"] + [s for s in STARTS if s != "2026"]:
        if start != "2026" and start not in want:
            continue
        rows, info = build(start, ref)
        if start == "2026":
            ref = info["means"]
            if "2026" not in want:
                continue
        if "--check" not in sys.argv:
            path = write(start, rows)
            print("wrote %s: %d players" % (os.path.relpath(path, ROOT), len(rows)))
        check(start, rows, info)


if __name__ == "__main__":
    main()
