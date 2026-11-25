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

DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "attributes_2026.csv")
LISTS = [("players_enriched_2026.csv", "players_enriched_2026.csv"),
         ("list_additions_stats.csv", "list_additions_2026.csv")]   # (stats rows, body file)

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
    """One season's league scale (12+ game players) and position averages."""

    def __init__(self, year: int):
        self.year = year
        self.rows = W.seasons().get(year, [])
        self.matcher = W.Matcher(year)        # also sets row["club"]
        self.m = {id(r): inputs(r) for r in self.rows}
        base = [r for r in self.rows if (r.get("Matches") or 0) >= M.NORM_GAMES]
        self.scale, self.mean = {}, defaultdict(dict)
        for k in METRICS:
            vals = sorted(self.m[id(r)][k] for r in base if self.m[id(r)].get(k) is not None)
            if vals:
                self.scale[k] = (M._pct(vals, 0.02), M._pct(vals, 0.98))
        by_pos = defaultdict(list)
        for r in base:
            by_pos[r["pos"]].append(self.m[id(r)])
        for pos, ms in by_pos.items():
            for k in METRICS:
                vals = [x[k] for x in ms if x.get(k) is not None]
                if vals:
                    self.mean[pos][k] = sum(vals) / len(vals)
        self.club_games = defaultdict(float)
        for r in self.rows:
            self.club_games[r["club"]] = max(self.club_games[r["club"]], r.get("Matches") or 0.0)

    def unit(self, m: dict, pos: str, k: str):
        """Metric k on 0..1 (league scale), after the short-sample lean."""
        v = m.get(k)
        if v is None or k not in self.scale:
            return None
        mean = self.mean.get(pos, {}).get(k)
        if mean is not None:
            wk, kk = SAMPLE.get(k, ("games", M.SHRINK_GAMES))
            w = m.get(wk) or 0.0
            v = (v * w + kk * mean) / (w + kk)
        lo, hi = self.scale[k]
        mode = METRICS[k]
        if mode.startswith("count"):
            x = v / hi if hi > 0 else 0.0
        else:
            x = (v - lo) / (hi - lo) if hi > lo else 0.5
        x = max(0.0, min(1.0, x))
        return 1.0 - x if mode.endswith("inv") else x


def blend(season: Season, m: dict, pos: str, recipe) -> float | None:
    got = [(season.unit(m, pos, k), w) for k, w in recipe]
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


def best_records(list_names: dict, kind: str, best) -> dict:
    """{(norm name, club code) or norm name: his best record of `kind`} from
    C:/kt/speed (best = max for km/h, min for a sprint time). A name two
    listed players share is matched on club as well; a record of that name
    with no club matches neither."""
    out = {}
    for name, rows in M.speed_records().items():
        for k, v, club, _season in rows:
            if k != kind:
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


def listed_players():
    """Every listed player with his season's Wheelo row: [(list row, body, year, wheelo row)]."""
    seasons, out, missed, seen = {}, [], [], set()
    for stats_f, body_f in LISTS:
        body = {(r["club"], r["first"], r["last"]): r for r in read(os.path.join(DATA, body_f))}
        for r in read(os.path.join(DATA, stats_f)):
            key = (r["club"], r["first"], r["last"])
            if key in seen:
                continue
            seen.add(key)
            year = int(r.get("src") or 2026)
            if year not in seasons:
                seasons[year] = Season(year)
            w = seasons[year].matcher.find(r["first"], r["last"], r["club"])
            if w is None:
                missed.append("%s %s %s %d" % (r["club"], r["first"], r["last"], year))
                continue
            out.append((r, body.get(key, {}), year, w))
    return out, seasons, missed


def build():
    players, seasons, missed = listed_players()
    names = defaultdict(int)
    for r, _b, _y, _w in players:
        names[W.norm(r["first"] + r["last"])] += 1
    gps = best_records(names, "gps_top_kmh", max)
    sprint = best_records(names, "sprint20_s", min)
    rows = []
    for r, body, year, w in players:
        s = seasons[year]
        m = s.m[id(w)]
        pos = w["pos"]
        h, kg = _f(body.get("height_cm")), _f(body.get("weight_kg"))
        a01 = {k: blend(s, m, pos, rec) for k, rec in RECIPES.items()}
        a01["_cp"] = s.unit(m, pos, "ContestedPossessions")
        a01["_wr"] = blend(s, m, pos, WORK_RATE)
        a01["_bo"], a01["_pa"] = s.unit(m, pos, "Bounces"), s.unit(m, pos, "PressureActs")
        cg = s.club_games.get(w["club"]) or 0.0
        a01["durability"] = min(1.0, (w.get("Matches") or 0.0) / cg) if cg else None
        nm = W.norm(r["first"] + r["last"])
        rows.append({"r": r, "year": year, "pos": pos, "h": h, "kg": kg, "a01": a01, "games": w.get("Matches") or 0.0,
                     "kmh": gps.get((nm, r["club"])) or gps.get(nm),
                     "sprint": sprint.get((nm, r["club"])) or sprint.get(nm)})
    # An attribute none of his stats feed: his position's average.
    for k in list(RECIPES) + ["durability", "_cp", "_wr", "_bo", "_pa"]:
        by_pos = defaultdict(list)
        for p in rows:
            if p["a01"][k] is not None and p["games"] >= M.NORM_GAMES:
                by_pos[p["pos"]].append(p["a01"][k])
        for p in rows:
            if p["a01"][k] is None:
                v = by_pos.get(p["pos"])
                p["a01"][k] = sum(v) / len(v) if v else 0.5
                p.setdefault("filled", []).append(k)
    # Strength: weight for his height against the list's line.
    body = [p for p in rows if p["h"] and p["kg"]]
    mh = sum(p["h"] for p in body) / len(body)
    mw = sum(p["kg"] for p in body) / len(body)
    slope = sum((p["h"] - mh) * (p["kg"] - mw) for p in body) / sum((p["h"] - mh) ** 2 for p in body)
    for p in body:
        p["w4h_kg"] = p["kg"] - (mw + slope * (p["h"] - mh))
    res = sorted(p["w4h_kg"] for p in body)
    rlo, rhi = M._pct(res, 0.02), M._pct(res, 0.98)
    for p in rows:
        parts = [p["a01"]["_cp"]]
        if "w4h_kg" in p:
            parts.append(max(0.0, min(1.0, (p["w4h_kg"] - rlo) / (rhi - rlo))))
        p["a01"]["strength"] = sum(parts) / len(parts)
    # Work Rate: against what his position, height and weight usually
    # produce (least squares over players with 12+ games); a player missing
    # his weight, or height too, against position and what he has.
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
    # Attributes 1..99; Speed by the director's rule.
    out = []
    for p in rows:
        a = {k: M.scale_attr(p["a01"][k]) for k in ATTRS if k != "speed"}
        if p["kmh"]:
            a["speed"], src = speed_from_kmh(p["kmh"]), "gps"
        elif p["sprint"]:
            a["speed"], src = speed_from_sprint(p["sprint"]), "20m"
        else:
            bump = SPEED_BUMP * (p["a01"]["_bo"] + p["a01"]["_pa"]) / 2.0
            a["speed"], src = min(SPEED_EST_CAP, int(round(SPEED_BASE.get(p["pos"], 56) + bump))), "est"
        r = p["r"]
        row = {"club": r["club"], "first": r["first"], "last": r["last"], "src": p["year"], "apos": p["pos"],
               "speed_src": src}
        row.update({k: a[k] for k in ATTRS})
        row["_p"] = p
        out.append(row)
    info = {"w4h_line": (mw, slope, mh, rlo, rhi), "missed": missed,
            "league98": {k: seasons[2026].scale[k][1] for k in ("uncontested_poss", "Bounces", "PressureActs", "io50",
                                                               "ContestedPossessions")}}
    return out, info


def write(rows):
    cols = ["club", "first", "last", "src", "apos", "speed_src"] + ATTRS
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    imp = OUT + ".import"
    if not os.path.exists(imp):
        with open(imp, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(IMPORT)


SAMPLE_NAMES = ["Nick Daicos", "Errol Gulden", "Nick Blakey", "Kysaiah Pickett", "Charlie Curnow", "Max Gawn"]


def check(rows, info):
    mw, slope, mh, rlo, rhi = info["w4h_line"]
    print("weight line: %.1f kg + %.2f kg a cm over %.0f cm; 2nd pct %+.1f kg, 98th %+.1f kg" % (mw, slope, mh, rlo, rhi))
    print("2026 league 98th a game:", "  ".join("%s %.2f" % kv for kv in info["league98"].items()))
    print("not found in their season:", len(info["missed"]), "; ".join(info["missed"][:20]))
    for nm in SAMPLE_NAMES:
        for r in rows:
            if r["first"] + " " + r["last"] == nm:
                p = r["_p"]
                how = {"gps": "%.1f km/h" % (p["kmh"] or 0), "20m": "%.2f s for 20 m" % (p["sprint"] or 0),
                       "est": "estimate"}[r["speed_src"]]
                print("  %-16s %s %-13s speed %2d (%s)  work rate %2d" % (
                    nm, r["club"], r["apos"], r["speed"], how, r["work_rate"]))
    n = defaultdict(int)
    for r in rows:
        n[r["speed_src"]] += 1
    print("speed from:", dict(n))


def main():
    rows, info = build()
    if "--check" not in sys.argv:
        write(rows)
        print("wrote %s: %d players" % (os.path.relpath(OUT, ROOT), len(rows)))
    check(rows, info)


if __name__ == "__main__":
    main()
