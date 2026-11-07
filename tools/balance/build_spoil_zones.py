#!/usr/bin/env python3
"""Real spoils a team a game, in total, by listed position and by zone, from Wheelo
Ratings' Champion Data download (docs/research/wheelo/afl_player_stats_2026.json, every
2026 player, finals included). Writes tools/balance/afl_spoil_zones.json for
balance_report.py (T2.29, TODO row 11).

    python tools/balance/build_spoil_zones.py [year]

Measured: spoils a team a game (sum of each club's players' spoils over the club's games,
the most games any of its players played) and spoils a player-game by listed position.
Champion Data does not publish where a spoil happens, so the zone split is an ESTIMATE:
each player's spoils are spread over his own zones in the share of his possessions there
(Defensive50Possessions, the two midfield thirds, Forward50Possessions). A key back who
gets 60% of his ball in defensive 50 is assumed to spoil there 60% of the time. Zones are
the spoiling side's: d50 its own defensive 50 (the other side's entries), mid between
the arcs, f50 its own forward 50.
"""
import json
import os
import statistics as st
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROLE = {"Key Defender": "DEF", "Gen. Defender": "DEF", "Midfielder": "MID", "Mid-Forward": "FWD",
        "Gen. Forward": "FWD", "Key Forward": "FWD", "Ruck": "RUCK"}
ZONES = {"d50": ["Defensive50Possessions"],
         "mid": ["DefensiveMidfieldPossessions", "AttackingMidfieldPossessions"],
         "f50": ["Forward50Possessions"]}


def load(year):
    path = os.path.join(ROOT, "docs", "research", "wheelo", f"afl_player_stats_{year}.json")
    with open(path, encoding="utf-8") as f:
        d = json.load(f)["Data"]
    return [{k: d[k][i] for k in d} for i in range(len(d["PlayerId"]))]


def band(vals):
    return {"mean": round(st.mean(vals), 2), "lo": round(min(vals), 2), "hi": round(max(vals), 2),
            "sd": round(st.stdev(vals), 2)}


def build(year):
    rows = [r for r in load(year) if (r["Matches"] or 0) > 0]
    clubs = {}
    for r in rows:
        c = clubs.setdefault(r["Team"], {"games": 0, "total": 0.0, "d50": 0.0, "mid": 0.0, "f50": 0.0})
        g = r["Matches"]
        c["games"] = max(c["games"], g)
        sp = (r["Spoils"] or 0) * g
        c["total"] += sp
        z = {k: sum((r[f] or 0) for f in fs) for k, fs in ZONES.items()}
        zs = sum(z.values())
        for k in ZONES:
            c[k] += sp * (z[k] / zs if zs > 0 else (1.0 if k == "mid" else 0.0))
    per = {k: [c[k] / c["games"] for c in clubs.values()] for k in ("total", "d50", "mid", "f50")}
    team_games = sum(c["games"] for c in clubs.values())
    roles = {}
    for role in ("DEF", "MID", "FWD", "RUCK"):
        g = [r for r in rows if ROLE.get(r["Position"]) == role]
        sp = sum((r["Spoils"] or 0) * r["Matches"] for r in g)
        pg = sum(r["Matches"] for r in g)
        roles[role] = {"per_player_game": round(sp / pg, 2), "share": round(sp / sum(c["total"] for c in clubs.values()), 3)}
    return {
        "source": f"Champion Data {year} via Wheelo Ratings (docs/research/wheelo/afl_player_stats_{year}.json), "
                  f"{len(clubs)} clubs, {team_games} team-games, finals included. Total and by position are "
                  "measured; the zone split is an estimate (each player's spoils spread over his zones in the "
                  "share of his possessions there; Champion Data does not publish spoil locations). "
                  "Built by tools/balance/build_spoil_zones.py.",
        "team_games": team_games,
        "per_team_match": {k: band(v) for k, v in per.items()},
        "by_role": roles,
    }


if __name__ == "__main__":
    year = sys.argv[1] if len(sys.argv) > 1 else "2026"
    out = build(year)
    with open(os.path.join(ROOT, "tools", "balance", "afl_spoil_zones.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    print(json.dumps(out, indent=1))
