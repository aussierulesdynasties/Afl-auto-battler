"""Turn the director's player types into attribute weights (director
2026-11-15: each type is rated on the stats the game keeps).

  godot --headless --path . --script tools/audit/run_audit.gd -- type_stats_impl > season.txt
  python tools/audit/type_stats_report.py season.txt [season2.txt ...]

For each line it fits every engine stat a game (StatBook.KEYS) on the
attributes, over the players of that line with 5+ games. A type's score is
its stats, each standardised on the line and weighted as the director
listed them; through the fits that is a blend of attributes, printed as
weights that add to 1. Reads; changes nothing.
"""
import sys
from collections import defaultdict

import numpy as np

ATTRS = ["disposal", "contested", "marking", "pressure", "intercept", "carry", "goalkicking",
         "accuracy", "creating", "ruck", "discipline", "durability"]

# The director's types, 2026-11-15, in the engine's stat keys. 1 = listed;
# 1.5 = "more"/"highly"; 0.75 = "slightly less"; 0.5 = "to a lesser degree".
# accuracy = goals over shots. Each listed idea with two engine stats splits
# its weight between them.
TYPES = {
    "RUCK": {
        "Mobile ruck": {"hitouts": 0.5, "hitouts_adv": 0.5, "clearances": 1, "distance_run": 1,
                        "contested_possessions": 1, "disposals": 1, "marks": 1},
        "Tap ruck": {"hitouts": 0.75, "hitouts_adv": 0.75, "marks": 1.5, "goals": 1.5,
                     "contested_possessions": 1, "clearances": 0.75},
    },
    "MID": {
        "Inside midfielder": {"contested_possessions": 1, "disposals": 1, "clearances": 1,
                              "ground_ball_gets": 1, "pressure_acts": 1, "tackles": 1, "handballs": 1},
        "Wing": {"distance_run": 1, "metres_gained": 0.5, "running_bounces": 0.5, "inside50": 1, "kicks": 1,
                 "effective_disposals": 1, "goal_assists": 0.5, "score_involvements": 0.5,
                 "pressure_acts": 0.5, "marks": 0.5, "tackles": 0.5},
        "Defensive midfielder": {"tackles": 1, "pressure_acts": 1, "marks": 1, "one_percenters": 1,
                                 "clearances": 1},
    },
    "DEF": {
        "Key defender": {"contested_marks": 1, "intercepts": 0.5, "intercept_marks": 0.5, "rebounds": 1,
                         "marks": 1, "clangers": -1},
        "Interceptor": {"intercepts": 0.75, "intercept_marks": 0.75, "metres_gained": 1, "kicks": 1,
                        "effective_disposals": 1},
        "Small defender": {"running_bounces": 1, "kicks": 1, "metres_gained": 1, "effective_disposals": 1,
                           "ground_ball_gets": 1},
    },
    "FWD": {
        "Key forward": {"marks": 1, "contested_marks": 1, "accuracy": 1, "shots": 1, "one_percenters": 0.5,
                        "spoils": 0.5, "distance_run": 1},
        "Small forward": {"goals": 1, "pressure_acts": 1, "effective_disposals": 0.5, "goal_assists": 0.5,
                          "score_involvements": 1, "running_bounces": 1},
        "Pressure forward": {"pressure_acts": 1, "goals": 1, "one_percenters": 0.5, "smothers": 0.5,
                             "running_bounces": 1, "tackles": 1},
        "High half forward": {"distance_run": 1, "metres_gained": 1, "inside50": 1, "running_bounces": 1,
                              "goals": 1, "score_involvements": 1},
    },
}


def load(paths):
    rows = []
    for path in paths:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.startswith("ROW "):
                    continue
                f = line[4:].rstrip("\n").split("|")
                a = dict(kv.split("=") for kv in f[6].split(";"))
                s = dict(kv.split("=") for kv in f[7].split(";"))
                rows.append({"id": f[0], "name": f[2], "role": f[3], "gm": int(f[5]),
                             "attr": {k: float(a.get(k, 0)) for k in ATTRS},
                             "s": {k: float(v) for k, v in s.items()}})
    return rows


def stat(r, key):
    s, g = r["s"], max(1, r["gm"])
    if key == "accuracy":
        return s["goals"] / s["shots"] if s.get("shots", 0) >= 5 else None
    return s.get(key, 0.0) / g


def fit(rows, key):
    pts = [(r, stat(r, key)) for r in rows]
    pts = [(r, y) for r, y in pts if y is not None]
    X = np.array([[1.0] + [r["attr"][k] for k in ATTRS] for r, _ in pts])
    y = np.array([v for _, v in pts])
    lam = np.eye(X.shape[1]) * 5.0
    lam[0, 0] = 0
    beta = np.linalg.solve(X.T @ X + lam, X.T @ y)
    pred = X @ beta
    r2 = 1 - ((y - pred) ** 2).sum() / max(1e-9, ((y - y.mean()) ** 2).sum())
    return beta, float(np.std(pred)) or 1.0, r2


def main(paths):
    rows = [r for r in load(paths) if r["gm"] >= 5]
    print("players with 5+ games:", len(rows))
    for line, types in TYPES.items():
        lr = [r for r in rows if r["role"] == line]
        keys = sorted({k for w in types.values() for k in w})
        fits = {k: fit(lr, k) for k in keys}
        print("\n== %s (%d players)  fit R2: %s" % (line, len(lr), ", ".join("%s %.2f" % (k, fits[k][2]) for k in keys)))
        for name, w in types.items():
            c = np.zeros(len(ATTRS))
            for k, wk in w.items():
                beta, sd, _ = fits[k]
                c += wk * beta[1:] / sd
            c = np.clip(c, 0, None)
            c = c / c.sum()
            top = sorted(zip(ATTRS, c), key=lambda t: -t[1])
            print("  %-20s %s" % (name, ", ".join("%s %.2f" % (k, v) for k, v in top if v >= 0.01)))


if __name__ == "__main__":
    main(sys.argv[1:])
