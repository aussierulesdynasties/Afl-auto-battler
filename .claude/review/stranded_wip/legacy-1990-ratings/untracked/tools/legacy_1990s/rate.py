#!/usr/bin/env python3
"""Rate a legacy start's real lists (Legacy mode, TODO row 142, design P3).

    python tools/legacy_1990s/rate.py --start 1990
    python tools/legacy_1990s/rate.py --start 1990 --report C:/kt/leg90_report.md

Generic over starts: it reads every decade's season stats in data/legacy/*s/
and the start's opening lists, so another start needs only its own lists file.
Built for 1990; it writes data/legacy/<start>/:

  players.csv              the opening lists' players who played the data
                           season (start - 1), in the 2026 players schema, plus
                           the rest of that season's pool (pool_only = 1: rated
                           so league rates, norms and position anchors are the
                           whole season's, then dropped by GameDB)
  history.csv              their two seasons before the data season, rated on
                           each season's own pool, draft pedigree and careers
  list_additions.csv       listed players with no game in the data season
  list_addition_stats.csv  ... of those, the ones with an earlier senior season

How a season is rated (Ratings.gd, mirrored by tools/sim_harness.py):
  * Stats the season did not record (before 1999: contested possessions,
    contested marks, marks inside 50, one percenters, bounces; before 1998
    also rebounds, inside 50s, clearances, clangers; before 2003 goal
    assists) are imputed by a bridge: a games-weighted least-squares fit on
    later seasons that recorded both (1999-2001, goal assists 2003-05), from
    what every season recorded (kicks, marks, handballs, goals, behinds,
    hit-outs, tackles, frees for and against, per game) and height. League
    patterns only, never a player's own later career. Imputed columns are
    named in `imputed`; GameDB keeps them out of every stat the game shows.
  * Time on ground (recorded from 2003) is one fixed stand-in for everyone:
    the games-weighted mean of the first season that recorded it.
  * Position scale anchors are fitted from the season's own pool (players
    with 12+ games, same percentiles), so each season's best land where
    2026's best do (Ratings.fit_stretch_anchors).
  * Positions (no source lists them) are guessed from height, hit-outs,
    goals, kicking share and possessions, against the season's averages
    (guess_position); checked against the 2026 club listings.

The bridge is chosen against the fallback (era formulas that drop what the
season did not record and reweight) by rating the 1999 pool three ways: on
its real stats, with the bridge (fitted on 2000-02 so 1999 is out of sample)
and with the era formulas; --report prints the correlation and how many move
5+ OVR.

Potential (director 2026-11-11, "Informed", Director Bible): `real_peak` is
his best OVR from the start season on (8+ game seasons, else any), rated the
same way on each season's own pool; 0 when he never played a senior game
from the start season on. Potential.gd turns it into his ceiling, give or
take luck.
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from collections import defaultdict
from datetime import date

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import sim_harness as H  # noqa: E402

LEGACY = os.path.join(ROOT, "data", "legacy")
CLUB_ALIASES = {"BRB": "BRL", "FOO": "WBD"}   # GameDB.CLUB_CODE_ALIASES
COLS = {"one_pct": "onepct", "pct_played": "pctp"}   # season_stats -> STAT_KEYS
COUNTING = [k for k in H.STAT_KEYS if k not in ("gm", "pctp")]
# What every season recorded, per game: the bridge's inputs.
BASE = ["ki", "mk", "hb", "gl", "bh", "ho", "tk", "ff", "fa"]
BRIDGE_YEARS = {"main": (1999, 2001), "ga": (2003, 2005)}
VALIDATE_FIT = {"main": (2000, 2002), "ga": (2003, 2005)}
BRIDGE_MIN_GAMES = 5
MIN_SEASON_GAMES = 8          # tools/build_history.py: a history season
RECORD_YEARS = 2              # seasons before the data season (Ratings.RECORD_W)
PCTP_KEY = "pctp"


def club(code):
    return CLUB_ALIASES.get(code, code)


def fnum(s):
    s = (s or "").strip()
    return float(s) if s else 0.0


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load_seasons():
    """year -> {afltables_id: row}, a player's rows in one season summed (the
    club he played most games for), plus year -> set of recorded columns."""
    by_year = defaultdict(dict)
    recorded = defaultdict(lambda: defaultdict(int))
    for dec in sorted(os.listdir(LEGACY)):
        path = os.path.join(LEGACY, dec, "season_stats.csv")
        if not (dec.endswith("s") and os.path.exists(path)):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                year = int(r["year"])
                row = {COLS.get(k, k): v for k, v in r.items()}
                for k in H.STAT_KEYS:
                    if (row.get(k) or "").strip() != "":
                        recorded[year][k] += 1
                pid = row["afltables_id"] or "%s|%s|%s|%s" % (year, row["club"], row["first"], row["last"])
                p = {"year": year, "club": club(row["club"]), "num": int(fnum(row["num"])),
                     "first": row["first"], "last": row["last"], "aid": row["afltables_id"]}
                for k in H.STAT_KEYS:
                    p[k] = fnum(row.get(k))
                old = by_year[year].get(pid)
                if old is None:
                    by_year[year][pid] = p
                    continue
                main = old if old["gm"] >= p["gm"] else p
                merged = dict(main)
                for k in COUNTING + ["gm"]:
                    merged[k] = old[k] + p[k]
                g = merged["gm"] or 1.0
                merged["pctp"] = (old["pctp"] * old["gm"] + p["pctp"] * p["gm"]) / g
                by_year[year][pid] = merged
    # A column counts as recorded for a season when at least 5% of its rows
    # carry a value (a blank in a recorded column is a zero; a few stray
    # values are not a record).
    rec = {}
    for year, rows in by_year.items():
        rec[year] = {k for k, n in recorded[year].items() if n >= 0.05 * len(rows)} | {"gm"}
    return by_year, rec


def load_heights():
    """afltables_id -> height (cm), latest list that gives one."""
    out = {}
    for dec in sorted(os.listdir(LEGACY)):
        for name in sorted(os.listdir(os.path.join(LEGACY, dec))) if os.path.isdir(os.path.join(LEGACY, dec)) else []:
            if not (name.startswith("lists") and name.endswith(".csv")):
                continue
            with open(os.path.join(LEGACY, dec, name), newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    if r.get("afltables_id") and r.get("height_cm"):
                        out[r["afltables_id"]] = fnum(r["height_cm"])
    return out


# ---------------------------------------------------------------------------
# The bridge
# ---------------------------------------------------------------------------
def _features(p, height):
    g = max(1.0, p["gm"])
    return [1.0] + [p[k] / g for k in BASE] + [height]


class Bridge:
    """Per-target games-weighted least squares, per game, clamped at zero."""

    def __init__(self, seasons, rec, heights, years, h_med):
        self.coef = {}
        self.h_med = h_med
        self.heights = heights
        for group, (y0, y1) in years.items():
            targets = ["ga"] if group == "ga" else [
                k for k in H.STAT_KEYS if k not in BASE and k not in ("gm", "di", "br", "pctp", "ga")]
            for t in targets:
                X, Y, W = [], [], []
                for y in range(y0, y1 + 1):
                    if t not in rec.get(y, ()):
                        continue
                    for p in seasons[y].values():
                        if p["gm"] < BRIDGE_MIN_GAMES:
                            continue
                        X.append(_features(p, self.height(p)))
                        Y.append(p[t] / p["gm"])
                        W.append(p["gm"])
                if not X:
                    raise SystemExit("bridge: no %s rows in %d-%d" % (t, y0, y1))
                X, Y, w = np.array(X), np.array(Y), np.sqrt(np.array(W))
                beta, *_ = np.linalg.lstsq(X * w[:, None], Y * w, rcond=None)
                self.coef[t] = beta

    def height(self, p):
        return self.heights.get(p.get("aid", ""), 0.0) or self.h_med

    def fill(self, p, missing):
        """Impute every missing column on p (totals, 2 decimals)."""
        x = np.array(_features(p, self.height(p)))
        for t in missing:
            pg = max(0.0, float(x @ self.coef[t]))
            p[t] = round(pg * p["gm"], 2)


def pctp_stand_in(seasons, rec):
    year = min(y for y in rec if PCTP_KEY in rec[y])
    rows = [p for p in seasons[year].values() if p["gm"] > 0]
    return round(sum(p["pctp"] * p["gm"] for p in rows) / sum(p["gm"] for p in rows), 1), year


# ---------------------------------------------------------------------------
# Positions
# ---------------------------------------------------------------------------
# Thresholds against the season's per-player-per-game averages (relative, so a
# high-scoring or kick-heavy era reads the same), fitted on the 2026 club
# listings (guess_check): goals 3x average a forward; goals at average and
# possessions under 1.1x average a forward; goals under 0.4x average with a
# kicking share at or over average, or 189 cm+, a defender; 7+ hit-outs a
# ruck (the rating's own ruck gate); the rest midfield (the numbers decide).
POS_FWD_GOALS = 3.0
POS_FWD_GOALS_LOW = 1.0
POS_FWD_DISPOSALS = 1.1
POS_DEF_GOALS = 0.4
POS_DEF_KICK_SHARE = 1.0
POS_DEF_HEIGHT = 189.0
POS_RUCK_HITOUTS = 7.0


def league_shape(pool):
    g = sum(p["gm"] for p in pool) or 1.0
    lg = {k: sum(p[k] for p in pool) / g for k in ("gl", "ki", "di")}
    lg["kshare"] = lg["ki"] / (lg["di"] or 1.0)
    return lg


def guess_position(p, height, lg):
    g = max(1.0, p["gm"])
    if p["ho"] / g >= POS_RUCK_HITOUTS:
        return "RUC"
    gl = p["gl"] / g / (lg["gl"] or 1.0)
    di = p["di"] / g / (lg["di"] or 1.0)
    if gl >= POS_FWD_GOALS or (gl >= POS_FWD_GOALS_LOW and di < POS_FWD_DISPOSALS):
        return "FWD"
    ks = (p["ki"] / max(0.1, p["di"])) / (lg["kshare"] or 1.0)
    if gl < POS_DEF_GOALS and (ks >= POS_DEF_KICK_SHARE or height >= POS_DEF_HEIGHT):
        return "DEF"
    return "MID"


def guess_check():
    """Share of 2026 listed players (5+ games) whose guess matches."""
    rows = []
    with open(H.ENRICHED_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["real_pos"] and fnum(r["gm"]) >= 5:
                p = {k: fnum(r[k]) for k in H.STAT_KEYS}
                rows.append((p, fnum(r["height_cm"]) or 188.0, r["real_pos"]))
    lg = league_shape([p for p, _, _ in rows])
    ok = sum(1 for p, h, pos in rows if guess_position(p, h, lg) == pos)
    return ok, len(rows)


# ---------------------------------------------------------------------------
# Rating a season
# ---------------------------------------------------------------------------
def harness_player(p, pid):
    q = {"club": p["club"], "num": p["num"], "name": "%s %s" % (p["first"], p["last"]),
         "surname": p["last"], "first": p["first"], "last": p["last"],
         "id": pid, "aid": p.get("aid", "")}
    for k in H.STAT_KEYS:
        q[k] = p[k]
    return q


def prepare_pool(rows, recorded, bridge, pctp, heights, h_med, mode="bridge"):
    """rows: {pid: season row}. Returns harness players with imputed stats,
    a position guess and `imputed` (the columns filled in)."""
    lg = league_shape(list(rows.values()))
    pool = []
    for pid, p in rows.items():
        q = harness_player(p, pid)
        h = heights.get(p.get("aid", ""), 0.0)
        q["height_cm"] = h
        missing = [k for k in H.STAT_KEYS if k not in recorded and k not in ("gm", PCTP_KEY)]
        if mode == "bridge":
            bridge.fill(q, missing)
        q["imputed"] = list(missing)
        if PCTP_KEY not in recorded:
            q[PCTP_KEY] = pctp
            q["imputed"].append(PCTP_KEY)
        q["real_pos"] = guess_position(p, h or h_med, lg)
        pool.append(q)
    return pool


def rate_pool(pool):
    """Ratings.derive_all over the pool with anchors fitted from it."""
    H.derive_ratings(pool, fit_anchors=True)
    return H.derive_ratings.anchors


# ---- The era formulas (the fallback the bridge is chosen against) ----------
def rate_era_formula(pool, missing):
    """Rate with formulas that drop the inputs a season did not record and
    reweight the rest; an attribute left with no input uses the nearest
    recorded proxy (contested: tackles and frees for; creating: kicks and
    goals). Python only: it is the arm the bridge is measured against."""
    pool = [dict(p) for p in pool]
    for p in pool:
        for k in missing:
            p[k] = 0.0
    H.derive_ratings(pool)   # rates, norms, attribute shell
    gone = {m for m, s in H.METRIC_SPECS if s in missing} | (
        {"contested_share"} if "cp" in missing else set())

    def blend(q, terms, proxy):
        live = [(w, k) for w, k in terms if k not in gone]
        if not live:
            live = proxy
        tot = sum(w for w, _ in live)
        v = sum(w * (1.0 - q[k] if k.startswith("1-") else q[k]) for w, k in live) / tot
        return int(round(1 + 98 * max(0.0, min(1.0, v))))

    for p in pool:
        q = p["norm"]
        a = dict(p["attr"])
        a["disposal"] = blend(q, [(0.60, "disposals_pg"), (0.25, "contested_pg"), (0.15, "clearances_pg")], [])
        a["contested"] = blend(q, [(0.45, "contested_pg"), (0.30, "clearances_pg"), (0.25, "contested_share")],
                               [(0.5, "tackles_pg"), (0.5, "frees_for_pg")])
        a["marking"] = blend(q, [(0.50, "marks_pg"), (0.28, "contested_marks_pg"), (0.22, "marks_inside50_pg")], [])
        a["pressure"] = blend(q, [(0.62, "tackles_pg"), (0.38, "one_percenters_pg")], [])
        a["intercept"] = blend(q, [(0.45, "rebounds_pg"), (0.28, "marks_pg"), (0.27, "one_percenters_pg")], [])
        a["carry"] = blend(q, [(0.45, "inside50s_pg"), (0.28, "bounces_pg"), (0.27, "disposals_pg")], [])
        a["goalkicking"] = blend(q, [(0.66, "goals_pg"), (0.34, "marks_inside50_pg")], [])
        a["creating"] = blend(q, [(0.45, "goal_assists_pg"), (0.30, "inside50s_pg"), (0.25, "marks_inside50_pg")],
                              [(0.5, "kicks_pg"), (0.5, "goals_pg")])
        a["ruck"] = blend(q, [(0.70, "hitouts_pg"), (0.18, "clearances_pg"), (0.12, "contested_marks_pg")], [])
        p["attr"] = a
        sc = {
            "FWD": [(0.50, "goals_pg"), (0.26, "marks_inside50_pg"), (0.14, "goal_assists_pg"), (0.10, "behinds_pg")],
            "MID": [(0.42, "disposals_pg"), (0.30, "contested_pg"), (0.28, "clearances_pg")],
            "DEF": [(0.42, "rebounds_pg"), (0.30, "one_percenters_pg"), (0.20, "marks_pg"), (0.08, "1-goals_pg")],
        }
        scores = {}
        for role, terms in sc.items():
            live = [(w, k) for w, k in terms if k.replace("1-", "") not in gone]
            tot = sum(w for w, _ in live) or 1.0
            scores[role] = sum(w * (1.0 - q[k[2:]] if k.startswith("1-") else q[k]) for w, k in live) / tot
        scores["RUCK"] = (0.25 + 0.85 * q["hitouts_pg"]) if p["ho"] / max(1.0, p["gm"]) >= 7.0 else -1.0
        role = max(scores, key=scores.get)
        if p.get("real_pos") in ("FWD", "DEF") and role != "RUCK":
            role = p["real_pos"]
        p["role"] = role
    anchors = H.fit_stretch_anchors(pool)
    for p in pool:
        p["overall"] = H.rate_overall(p["attr"], p["role"], p["gm"], anchors)
    return pool


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = math.sqrt(sum((x - ma) ** 2 for x in a))
    vb = math.sqrt(sum((y - mb) ** 2 for y in b))
    return cov / (va * vb) if va and vb else 0.0


def validate(seasons, rec, heights, h_med, pctp):
    """Rate the 1999 pool on its real stats, with the bridge (fitted on
    2000-02) and with the era formulas. Returns the comparison."""
    year = 1999
    rows = seasons[year]
    real_rec = rec[year]
    old_rec = rec[1989] if 1989 in rec else rec[min(rec)]
    bridge = Bridge(seasons, rec, heights, VALIDATE_FIT, h_med)
    full = prepare_pool(rows, real_rec, bridge, pctp, heights, h_med)
    rate_pool(full)
    hidden = sorted(real_rec - old_rec - {"gm"})
    arm = prepare_pool(rows, old_rec, bridge, pctp, heights, h_med)
    # Same goal assists and time on ground as the real arm: 1999 recorded
    # neither, so only the columns 1989 lacks and 1999 has differ.
    by_id = {p["id"]: p for p in full}
    for p in arm:
        p["ga"] = by_id[p["id"]]["ga"]
    rate_pool(arm)
    era_in = prepare_pool(rows, real_rec, bridge, pctp, heights, h_med)
    era = rate_era_formula(era_in, hidden)
    out = {"hidden": hidden, "n": len(full)}
    for name, pool in (("bridge", arm), ("era formula", era)):
        a = [by_id[p["id"]]["overall"] for p in pool]
        b = [p["overall"] for p in pool]
        moved = sum(1 for x, y in zip(a, b) if abs(x - y) >= 5)
        reg = [(x, y) for x, y, p in zip(a, b, pool) if p["gm"] >= 12]
        out[name] = {"r": pearson(a, b), "moved5": moved,
                     "r12": pearson([x for x, _ in reg], [y for _, y in reg]),
                     "moved5_12": sum(1 for x, y in reg if abs(x - y) >= 5), "n12": len(reg),
                     "top": sum(1 for x, y in zip(a, b) if x >= 80 and y >= 80),
                     "top_real": sum(1 for x in a if x >= 80), "top_arm": sum(1 for y in b if y >= 80)}
    return out


# ---------------------------------------------------------------------------
# The start
# ---------------------------------------------------------------------------
def age_on(dob, day):
    try:
        y, m, d = (int(x) for x in dob.split("-"))
    except ValueError:
        return 0.0
    born = date(y, m, d)
    return round((day - born).days / 365.25, 2)


def opening_lists(start):
    dec = "%ds" % (start // 10 * 10)
    path = os.path.join(LEGACY, dec, "lists_%d_opening.csv" % start)
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    detail = {}
    with open(os.path.join(LEGACY, dec, "lists.csv"), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if int(r["year"]) == start:
                detail[r["draftguru_id"] or "%s|%s" % (r["club"], r["num"])] = r
    for r in rows:
        d = detail.get(r["draftguru_id"] or "%s|%s" % (r["club"], r["num"]), {})
        r["joined_pick"] = d.get("joined_pick", "")
        r["position_list"] = d.get("position", "")
    return rows


def careers_before(start):
    dec = "%ds" % (start // 10 * 10)
    out = defaultdict(list)
    with open(os.path.join(LEGACY, dec, "careers_before_%d.csv" % start), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[r["afltables_id"]].append((int(r["year"]), club(r["club"]), int(fnum(r["games"])), int(fnum(r["goals"]))))
    return out


def career_stints(rows):
    stints = []
    for year, code, gm, gl in sorted(rows):
        if gm <= 0:
            continue
        if stints and stints[-1][0] == code:
            s = stints[-1]
            s[2] = year
            s[3] += gm
            s[4] += gl
        else:
            stints.append([code, year, year, gm, gl])
    return ";".join("%s:%d:%d:%d:%d" % tuple(s) for s in stints)


DRAFT_TYPES = {"national_draft": "national", "pre_season_draft": "preseason",
               "mid_season_draft": "midseason"}


def fmt(v):
    return ("%.2f" % v).rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=1990)
    ap.add_argument("--report", default="", help="write the validation numbers (JSON) here")
    args = ap.parse_args()
    start = args.start
    season = start - 1
    day = date(start, 3, 1)

    seasons, rec = load_seasons()
    heights = load_heights()
    h_med = float(np.median([h for h in heights.values() if h > 0]))
    pctp, pctp_year = pctp_stand_in(seasons, rec)
    bridge = Bridge(seasons, rec, heights, BRIDGE_YEARS, h_med)

    # Every season from the record window to the last with data, rated.
    rated = {}
    anchors = {}
    for year in sorted(seasons):
        if year < season - RECORD_YEARS:
            continue
        pool = prepare_pool(seasons[year], rec[year], bridge, pctp, heights, h_med)
        anchors[year] = rate_pool(pool)
        rated[year] = {p["id"]: p for p in pool}

    lists = opening_lists(start)
    for r in lists:
        if r["afltables_id"] and r["height_cm"]:
            heights.setdefault(r["afltables_id"], fnum(r["height_cm"]))
    careers = careers_before(start)
    out_dir = os.path.join(LEGACY, str(start))
    os.makedirs(out_dir, exist_ok=True)

    # ---- real peaks (informed POT) --------------------------------------------
    def real_peak(aid):
        if not aid:
            return 0
        best8 = best = 0
        for year, pool in rated.items():
            if year < start or aid not in pool:
                continue
            p = pool[aid]
            if p["gm"] <= 0:
                continue
            best = max(best, p["overall"])
            if p["gm"] >= MIN_SEASON_GAMES:
                best8 = max(best8, p["overall"])
        return best8 or best

    # ---- players.csv ------------------------------------------------------------
    data = rated[season]
    listed_ids = set()
    head = ["club", "num", "last", "first"] + H.STAT_KEYS + [
        "src", "real_pos", "dob", "age", "height_cm", "weight_kg", "debut", "height_source",
        "data_club", "imputed", "real_peak", "pool_only", "ovr_python"]
    players_rows, additions, addition_stats, history = [], [], [], []
    for r in lists:
        code = club(r["club"])
        aid = r["afltables_id"]
        age = age_on(r["dob"], day)
        p = data.get(aid) if aid else None
        if p is not None and p["gm"] > 0:
            listed_ids.add(aid)
            row = {"club": code, "num": r["num"], "last": r["last"], "first": r["first"]}
            row.update({k: fmt(p[k]) for k in H.STAT_KEYS})
            row.update({"src": season, "real_pos": p["real_pos"], "dob": r["dob"],
                        "age": fmt(age) if age > 0 else "", "height_cm": r["height_cm"],
                        "weight_kg": r["weight_kg"], "debut": "", "height_source": "club list" if r["height_cm"] else "",
                        "data_club": p["club"], "imputed": ";".join(p["imputed"]),
                        "real_peak": real_peak(aid), "pool_only": "", "ovr_python": p["overall"]})
            players_rows.append(row)
            # history: the two seasons before, draft pedigree, career to S-1
            seasons_txt = []
            for year in range(season - RECORD_YEARS, season):
                q = rated.get(year, {}).get(aid)
                if q is not None and q["gm"] >= MIN_SEASON_GAMES:
                    seasons_txt.append("%d:%d:%d" % (year, q["overall"], q["gm"]))
            dt = DRAFT_TYPES.get(r["joined_how"], "")
            history.append({
                "club": code, "num": r["num"], "slug": aid.split("/")[-1].replace(".html", ""),
                "draft_year": r["joined_year"] if dt and r["joined_pick"] else "",
                "draft_type": dt if r["joined_pick"] else "",
                "draft_pick": r["joined_pick"] if dt else "",
                "seasons": ";".join(seasons_txt),
                "career": career_stints([c for c in careers.get(aid, []) if c[0] < season])})
            continue
        # No game in the data season: a list addition.
        last = None
        for year in range(season - 1, season - RECORD_YEARS - 1, -1):
            q = rated.get(year, {}).get(aid) if aid else None
            if q is not None and q["gm"] > 0:
                last = (year, q)
                break
        pos = ""
        add = {"first": r["first"], "last": r["last"], "dob": r["dob"], "club": code, "num": r["num"],
               "position": "", "height_cm": r["height_cm"], "list": "senior",
               "draft_pick": r["joined_pick"] if r["joined_how"] == "national_draft" else "",
               "real_peak": real_peak(aid)}
        if last is not None:
            year, q = last
            pos = {"RUC": "RUCK"}.get(q["real_pos"], q["real_pos"])
            add["position"] = pos if pos in ("FWD", "DEF", "RUCK") else ""
            st = {"club": code, "num": r["num"], "last": r["last"], "first": r["first"]}
            st.update({k: fmt(q[k]) for k in H.STAT_KEYS})
            st.update({"src": year, "imputed": ";".join(q["imputed"])})
            addition_stats.append(st)
        additions.append(add)

    # The rest of the data season's pool: rated with them, then dropped.
    for aid, p in data.items():
        if aid in listed_ids or p["gm"] <= 0:
            continue
        row = {"club": p["club"], "num": p["num"], "last": p["last"], "first": p["first"]}
        row.update({k: fmt(p[k]) for k in H.STAT_KEYS})
        row.update({"src": season, "real_pos": p["real_pos"], "dob": "", "age": "", "height_cm": "",
                    "weight_kg": "", "debut": "", "height_source": "", "data_club": p["club"],
                    "imputed": ";".join(p["imputed"]), "real_peak": "", "pool_only": 1,
                    "ovr_python": p["overall"]})
        players_rows.append(row)

    def write(name, rows, header):
        with open(os.path.join(out_dir, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=header, lineterminator="\n")
            w.writeheader()
            for row in rows:
                w.writerow(row)

    write("players.csv", players_rows, head)
    write("history.csv", history, ["club", "num", "slug", "draft_year", "draft_type", "draft_pick", "seasons", "career"])
    write("list_additions.csv", additions, ["first", "last", "dob", "club", "num", "position", "height_cm",
                                            "list", "draft_pick", "real_peak"])
    write("list_addition_stats.csv", addition_stats, ["club", "num", "last", "first"] + H.STAT_KEYS + ["src", "imputed"])

    # ---- check that the files rate as written --------------------------------
    pool = []
    with open(os.path.join(out_dir, "players.csv"), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            q = {"club": r["club"], "num": int(fnum(r["num"])), "name": "%s %s" % (r["first"], r["last"])}
            for k in H.STAT_KEYS:
                q[k] = float(r[k])
            q["real_pos"] = r["real_pos"]
            q["want"] = int(r["ovr_python"])
            pool.append(q)
    H.derive_ratings(pool, fit_anchors=True)
    bad = [q for q in pool if q["overall"] != q["want"]]
    if bad:
        raise SystemExit("players.csv re-rates differently for %d rows" % len(bad))

    ok, n = guess_check()
    print("%d: %d listed players rated on %d (%d pool-only), %d list additions (%d with an earlier season)"
          % (start, len(listed_ids), season, len(players_rows) - len(listed_ids), len(additions), len(addition_stats)))
    print("time on ground stand-in %.1f%% (%d); position guess matches %d of %d 2026 listings (%.0f%%)"
          % (pctp, pctp_year, ok, n, 100.0 * ok / n))
    print("anchors %d: %s" % (season, {k: tuple(round(x, 2) for x in v) for k, v in anchors[season].items()}))
    if args.report:
        import json
        val = validate(seasons, rec, heights, h_med, pctp)
        val.update({"pctp": pctp, "pctp_year": pctp_year, "guess_ok": ok, "guess_n": n,
                    "anchors": {str(y): {k: list(v) for k, v in a.items()} for y, a in anchors.items() if y <= season},
                    "recorded": {str(y): sorted(rec[y]) for y in sorted(rec) if y <= season}})
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(val, fh, indent=1)
        print("validation 1999:", {k: val[k] for k in ("bridge", "era formula", "hidden")})


if __name__ == "__main__":
    main()
