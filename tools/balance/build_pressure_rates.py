#!/usr/bin/env python3
"""Real pressure a team a game, from Wheelo Ratings' Champion Data download
(docs/research/wheelo/afl_player_stats_<year>.json, every player, finals included).
Writes tools/balance/afl_pressure_rates.json for balance_report.py (pressure_section).

    python tools/balance/build_pressure_rates.py

Each club-season: the sum of its players' per-game figure times their games, over the
club's games (the most games any of its players played, as build_spoil_zones.py does).
The shares (pressure acts in the defensive half, tackles per pressure act, tackles
inside 50 per tackle) are ratios of those sums, so they do not depend on the game count.
Champion Data: a pressure act is a tackle, a chase, a corral or closing a carrier down;
the defensive half is the presser's own half.
"""
import json
import os
import statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
YEARS = (2025, 2026)


def load(year):
    path = os.path.join(ROOT, "docs", "research", "wheelo", f"afl_player_stats_{year}.json")
    with open(path, encoding="utf-8") as f:
        d = json.load(f)["Data"]
    return [{k: d[k][i] for k in d} for i in range(len(d["PlayerId"]))]


def band(vals, nd=3):
    return {"mean": round(st.mean(vals), nd), "min": round(min(vals), nd), "max": round(max(vals), nd),
            "sd": round(st.stdev(vals), nd)}


def club_seasons(year):
    clubs = {}
    for p in load(year):
        g = float(p.get("Matches") or 0)
        c = clubs.setdefault(p["Team"], {"games": 0.0, "pa": 0.0, "pa_dh": 0.0, "tk": 0.0, "tk_i50": 0.0})
        c["games"] = max(c["games"], g)
        c["pa"] += float(p.get("PressureActs") or 0) * g
        c["pa_dh"] += float(p.get("PressureActsDefensiveHalf") or 0) * g
        c["tk"] += float(p.get("Tackles") or 0) * g
        c["tk_i50"] += float(p.get("TacklesInside50") or 0) * g
    out = []
    for name, c in sorted(clubs.items()):
        n = c["games"]
        out.append({"club": name, "year": year, "games": n,
                    "pressure_acts": c["pa"] / n, "pressure_acts_dhalf": c["pa_dh"] / n,
                    "tackles": c["tk"] / n, "tackles_i50": c["tk_i50"] / n,
                    "dhalf_share": c["pa_dh"] / c["pa"], "tackles_per_act": c["tk"] / c["pa"],
                    "i50_share": c["tk_i50"] / c["tk"]})
    return out


def main():
    rows = [r for y in YEARS for r in club_seasons(y)]
    keys = ["pressure_acts", "pressure_acts_dhalf", "tackles", "tackles_i50",
            "dhalf_share", "tackles_per_act", "i50_share"]
    out = {
        "source": ("Champion Data via Wheelo Ratings (docs/research/wheelo/afl_player_stats_2025.json and "
                   "_2026.json), finals included; each club-season's players' totals over the club's games; "
                   "36 club-seasons (18 clubs x 2025-26) give the mean, range and spread. "
                   "Built by tools/balance/build_pressure_rates.py."),
        "per_team_match": {k: band([r[k] for r in rows]) for k in keys},
        "club_seasons": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()} for r in rows],
    }
    path = os.path.join(ROOT, "tools", "balance", "afl_pressure_rates.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    for k in keys:
        b = out["per_team_match"][k]
        print(f"{k:22s} mean {b['mean']:8.3f}  range {b['min']:.3f}-{b['max']:.3f}  sd {b['sd']:.3f}")


if __name__ == "__main__":
    main()
