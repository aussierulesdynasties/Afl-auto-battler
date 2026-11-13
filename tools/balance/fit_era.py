#!/usr/bin/env python3
"""Fit each past season's football (data/legacy/era_football.csv; legacy, row 142 L5).

An era row is a set of multipliers on the match engine's rates (EraFootball.KEYS,
Ratings.T keys). They are fitted so a match of that season moves each team stat
against a 2026 match as far as the real season moved against real 2026
(afl_year_rates.json): the shift, not the level, so how close the 2026 engine
already sits to real 2026 is left as it is, and 2026 itself plays unchanged.

How each rate moves each stat is measured, not assumed: one paired harness run a
rate (`tools/balance.sh match 1000 --b "--tune KEY=V"`, V the rate times F; on
GitHub, run_on_github.yml what=balance), each report saved as
<steps>/<KEY>@<F>.txt. The log responses make a matrix E (stat x rate); a season's
row solves E x = ln(real season / real 2026) by least squares with a small ridge
(x = ln multipliers), so no rate runs off to fit noise.

A year-mode run (tools/balance.sh year ... --years "... 2026") can then correct
the fit (--correct <run>): the shift each screened season still misses goes back
through E (a Newton step), and seasons between two screened ones take the
correction of the nearer ones, weighted by distance.

    python tools/balance/fit_era.py --steps <dir> [--correct <year run>] [--write]
"""
import argparse, glob, json, math, os, re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "data", "legacy", "era_football.csv")
# EraFootball.KEYS, in order.
KEYS = ["chains_per_game", "handball_share", "mark_share_of_kicks", "pressure_base",
        "inside50_goal", "inside50_behind", "hitouts_per_stoppage", "clanger_is_free",
        "free_rate"]
# The stats fitted (sim key, afl_year_rates key): every one recorded in every season.
STATS = [("disposals", "disposals"), ("handballs", "handballs"), ("marks", "marks"),
         ("tackles", "tackles"), ("goals", "goals"), ("behinds", "behinds"),
         ("hitouts", "hitouts"), ("frees_for", "frees_for")]
RIDGE = 0.02
# A stat's weight in the fit (1 unless named). Frees once weighed 0.2, when only
# clanger_is_free moved them; free_rate (the contextual frees) now reaches them.
WEIGHT = {}
FIRST, LAST = 1990, 2025


def read_report(path):
    """stat -> (A, B) from a paired balance report's main table."""
    out = {}
    for line in open(path, encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 8 and cells[0] in dict(STATS):
            try:
                out[cells[0]] = (float(cells[3]), float(cells[5]))
            except ValueError:
                pass
    return out


def elasticities(steps):
    E = np.zeros((len(STATS), len(KEYS)))
    seen = set()
    for f in glob.glob(os.path.join(steps, "*@*.txt")):
        m = re.match(r"(\w+)@([\d.]+)\.txt$", os.path.basename(f))
        if not m or m.group(1) not in KEYS:
            continue
        k, fac = KEYS.index(m.group(1)), float(m.group(2))
        rows = read_report(f)
        for i, (s, _) in enumerate(STATS):
            a, b = rows[s]
            E[i, k] = math.log(b / a) / math.log(fac)
        seen.add(m.group(1))
    missing = [k for k in KEYS if k not in seen]
    if missing:
        raise SystemExit(f"no step report for {', '.join(missing)} in {steps}")
    return E


def targets(years):
    r26 = years["2026"]["per_team_match"]
    out = {}
    for y in range(FIRST, LAST + 1):
        r = years[str(y)]["per_team_match"]
        out[y] = np.array([math.log(r[rk]["mean"] / r26[rk]["mean"]) for _, rk in STATS])
    return out


# Today's value of each rate (Ratings.T after Ratings.FLOW), so a multiplier never
# makes a chance above MAX_P.
BASE = {"chains_per_game": 275, "handball_share": 0.44, "mark_share_of_kicks": 0.28,
        "pressure_base": 0.16, "inside50_goal": 0.255, "inside50_behind": 0.175,
        "hitouts_per_stoppage": 0.78, "clanger_is_free": 0.43,
        "free_rate": None}
MAX_P = 0.95
LO, HI = math.log(0.3), math.log(2.0)


def bounds():
    out = []
    for k in KEYS:
        hi = HI if BASE[k] is None or k == "chains_per_game" else min(HI, math.log(MAX_P / BASE[k]))
        out.append((LO, hi))
    return out


def solve(E, t):
    w = np.array([WEIGHT.get(s, 1.0) for s, _ in STATS])
    return _solve(E * w[:, None], t * w)


def _solve(E, t):
    """Ridge least squares with each rate held inside bounds(): a rate that runs
    past its bound is fixed there and the rest solved again."""
    b = bounds()
    fixed = {}
    while True:
        free = [j for j in range(len(KEYS)) if j not in fixed]
        r = t - sum((E[:, j] * v for j, v in fixed.items()), np.zeros(len(t)))
        Ef = E[:, free]
        xf = np.linalg.solve(Ef.T @ Ef + RIDGE * np.eye(len(free)), Ef.T @ r)
        out = [j for j, v in zip(free, xf) if not b[j][0] <= v <= b[j][1]]
        if not out:
            x = np.zeros(len(KEYS))
            for j, v in fixed.items():
                x[j] = v
            for j, v in zip(free, xf):
                x[j] = v
            return x
        for j in out:
            v = xf[free.index(j)]
            fixed[j] = min(max(v, b[j][0]), b[j][1])


def read_year_run(run):
    """year -> sim log shift against the run's 2026, per fitted stat."""
    from balance_report import load, per_match
    sims = {int(d): load(os.path.join(run, d), "a") for d in os.listdir(run) if d.isdigit()}
    if 2026 not in sims:
        raise SystemExit("--correct needs a year run that includes 2026")
    mean = {y: np.array([sum(per_match(s, k).values()) / len(s) for k, _ in STATS]) for y, s in sims.items()}
    return {y: np.log(mean[y] / mean[2026]) for y in sims if y != 2026}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", required=True)
    ap.add_argument("--correct", default="")
    ap.add_argument("--write", action="store_true")
    o = ap.parse_args()
    E = elasticities(o.steps)
    years = json.load(open(os.path.join(HERE, "afl_year_rates.json"), encoding="utf-8"))["years"]
    t = targets(years)
    print("Elasticity (d ln stat / d ln rate):")
    print("%-10s " % "" + " ".join("%8s" % k[:8] for k in KEYS))
    for i, (s, _) in enumerate(STATS):
        print("%-10s " % s + " ".join("%8.2f" % v for v in E[i]))
    # The current rows (a correction starts from them).
    cur = {}
    if os.path.exists(OUT):
        import csv
        for r in csv.DictReader(open(OUT, encoding="utf-8")):
            cur[int(r["year"])] = np.log(np.array([float(r.get(k) or 1.0) for k in KEYS]))
    x = {y: solve(E, t[y]) for y in t}
    if o.correct:
        got = read_year_run(o.correct)
        fix = {y: solve(E, t[y] - got[y]) for y in got if y in t}
        ys = sorted(fix)
        for y in t:
            base = cur.get(y, x[y])
            lo = max([s for s in ys if s <= y], default=None)
            hi = min([s for s in ys if s >= y], default=None)
            if lo is None or hi is None or lo == hi:
                d = fix[lo if lo is not None else hi]
            else:
                w = (y - lo) / (hi - lo)
                d = (1 - w) * fix[lo] + w * fix[hi]
            x[y] = base + d
        print("\nCorrected from " + o.correct + " (seasons " + ", ".join(map(str, ys)) + ")")
    print("\nyear " + " ".join("%8s" % k[:8] for k in KEYS) + "   fit residual (per cent, worst stat)")
    rows = []
    for y in sorted(x):
        m = np.exp(x[y])
        res = E @ x[y] - t[y]
        worst = int(np.argmax(np.abs(res)))
        print(f"{y} " + " ".join("%8.3f" % v for v in m) + f"   {100 * res[worst]:+.1f} {STATS[worst][0]}")
        rows.append([str(y)] + ["%.3f" % v for v in m])
    if o.write:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write("year," + ",".join(KEYS) + "\n")
            for r in rows:
                f.write(",".join(r) + "\n")
        print("\nwrote " + OUT)


if __name__ == "__main__":
    main()
