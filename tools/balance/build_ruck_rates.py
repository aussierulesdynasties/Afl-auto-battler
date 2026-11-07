#!/usr/bin/env python3
"""Real ruck rates for the balance report, written to tools/balance/afl_ruck_rates.json (T2.31).

Source: Champion Data per-player season averages for 2025 and 2026 as Wheelo serves them
(docs/research/wheelo/afl_player_stats_<year>.json: Matches, Hitouts, HitoutsToAdvantage,
RuckContests, HitoutsWinPercentage are per-game averages over the games the player played).

Per club and season:
  - team hit-outs and hit-outs to advantage a game: every player's average x his games,
    summed, divided by the club's games (the most games any of its players played);
  - the number-one ruck: the listed Ruck with the most hit-outs in the season, and his own
    per-game hit-outs, hit-outs to advantage, ruck contests, hit-out win rate (hit-outs per
    ruck contest, Champion Data's HitoutsWinPercentage) and his share of the club's hit-outs.
The league figure is the mean of the 18 club values; min, max and sd across clubs.

No per-match hit-out split is in the repo, so this file has no match-by-match duel spread:
the club-level spread (how far apart the 18 clubs' season figures sit) is the sourced
feast-or-famine check.

    python3 tools/balance/build_ruck_rates.py
"""
import json, os, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KEYS = ["team_hitouts", "team_hta", "team_hta_pct", "ruck1_hitouts", "ruck1_hta", "ruck1_hta_pct",
        "ruck1_contests", "ruck1_win_pct", "ruck1_share"]


def season(year):
    path = os.path.join(ROOT, "docs", "research", "wheelo", f"afl_player_stats_{year}.json")
    d = json.load(open(path, encoding="utf-8"))["Data"]
    rows = [{k: d[k][i] for k in d} for i in range(len(d["Player"]))]
    clubs = {}
    for r in rows:
        if not r.get("Team") or not r.get("Matches"):
            continue
        c = clubs.setdefault(r["Team"], {"games": 0, "ho": 0.0, "hta": 0.0, "rucks": []})
        g = float(r["Matches"])
        c["games"] = max(c["games"], g)
        c["ho"] += float(r.get("Hitouts") or 0) * g
        c["hta"] += float(r.get("HitoutsToAdvantage") or 0) * g
        if r.get("Position") == "Ruck":
            c["rucks"].append(r)
    out = {}
    for team, c in clubs.items():
        if not c["rucks"]:
            continue
        r1 = max(c["rucks"], key=lambda r: float(r.get("Hitouts") or 0) * float(r["Matches"]))
        ho = float(r1["Hitouts"] or 0)
        out[team] = {
            "team_hitouts": c["ho"] / c["games"],
            "team_hta": c["hta"] / c["games"],
            "team_hta_pct": 100 * c["hta"] / c["ho"],
            "ruck1": r1["Player"],
            "ruck1_hitouts": ho,
            "ruck1_hta": float(r1["HitoutsToAdvantage"] or 0),
            "ruck1_hta_pct": 100 * float(r1["HitoutsToAdvantage"] or 0) / ho if ho else 0.0,
            "ruck1_contests": float(r1["RuckContests"] or 0),
            "ruck1_win_pct": float(r1["HitoutsWinPercentage"] or 0),
            "ruck1_share": 100 * ho * float(r1["Matches"]) / c["ho"],
        }
    assert len(out) == 18, f"{year}: {len(out)} clubs"
    league = {}
    for k in KEYS:
        v = [out[t][k] for t in out]
        league[k] = {"mean": round(statistics.mean(v), 2), "min": round(min(v), 2),
                     "max": round(max(v), 2), "sd": round(statistics.pstdev(v), 2)}
    return {"league": league, "clubs": {t: {k: (round(x, 2) if isinstance(x, float) else x)
                                            for k, x in out[t].items()} for t in sorted(out)}}


def main() -> None:
    doc = {
        "source": "Champion Data per-player season averages, 2025 and 2026 (finals included), as served by "
                  "Wheelo: docs/research/wheelo/afl_player_stats_<year>.json. Team figures sum every player's "
                  "average x games over the club's games; ruck1 is the club's listed Ruck with the most season "
                  "hit-outs, his figures per game he played. Win % is hit-outs per ruck contest (Champion Data "
                  "HitoutsWinPercentage). League = mean, lowest, highest and sd of the 18 clubs. No per-match "
                  "split is in the repo. Regenerate with tools/balance/build_ruck_rates.py.",
        "keys": {"team_hitouts": "team hit-outs a game", "team_hta": "team hit-outs to advantage a game",
                 "team_hta_pct": "share of the team's hit-outs that went to advantage, %",
                 "ruck1_hitouts": "number-one ruck's hit-outs a game", "ruck1_hta": "his hit-outs to advantage a game",
                 "ruck1_hta_pct": "his share of hit-outs to advantage, %", "ruck1_contests": "his ruck contests a game",
                 "ruck1_win_pct": "his hit-outs per ruck contest, %", "ruck1_share": "his share of the club's season hit-outs, %"},
    }
    for y in (2025, 2026):
        doc[str(y)] = season(y)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "afl_ruck_rates.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    for y in ("2025", "2026"):
        print(y, json.dumps(doc[y]["league"]))


if __name__ == "__main__":
    main()
