"""Fit Weather.gd's WET_K, WIND_CUT and HOT_CUT (row 61) so the game plays each
condition as often as real AFL does, measured the same way as its effects.

The effects (afl_weather_rates.json) were measured on real matches classified by
the weather in the match window: wet at 0.3 mm or more, then windy (dry, mean wind
20 km/h or more), then hot (dry and still, 25 C or more); its share_of_outdoor is how
often each happened at the outdoor grounds, 2016-25 without 2020. This script finds
the cut-offs that give the game's own outdoor matches the same shares, from where
and when the game plays them (weather_fixture.gd) and the venue climate the game
reads (data/weather_by_venue.json), with Weather.gd's formulas copied here.

    godot --headless --path . --script tools/balance/weather_fixture.gd -- \\
        --seasons 20 --out runs/weather_fixture.jsonl
    python tools/balance/weather_cutoffs.py runs/weather_fixture.jsonl
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MONTHS = ["Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
STATE_VENUE = {"VIC": "MCG", "SA": "Adelaide Oval", "WA": "Optus Stadium", "NSW": "SCG",
               "QLD": "The Gabba", "TAS": "Bellerive Oval", "ACT": "Manuka Oval", "NT": "The Gabba"}
SOFT = 3.0       # Weather.SOFT
WIND_CAP = 0.35  # Weather.WIND_CAP


def soft(x):
    return 1.0 / (1.0 + math.exp(-x / SOFT))


def climate(data, ground, month, state):
    """The venue-month row Weather.chances reads, or None for the roofed ground."""
    if ground in data["roofed"]:
        return None
    venues = data["venues"]
    key = ground if ground in venues else STATE_VENUE.get(state, "MCG")
    if key not in venues:
        key = "MCG"
    return venues[key]["months"][MONTHS[month]]


def shares(rows, wet_k, wind_cut, hot_cut):
    """Expected outdoor shares {wet, windy, hot} under Weather.condition's order."""
    tot = {"wet": 0.0, "windy": 0.0, "hot": 0.0}
    for r in rows:
        w = min(1.0, max(0.0, r["rain"] * wet_k))
        v = min(WIND_CAP, soft(r["wind_3pm_kmh"] - wind_cut))
        h = soft(r["mean_max_c"] - hot_cut)
        tot["wet"] += w
        tot["windy"] += (1 - w) * v
        tot["hot"] += (1 - w) * (1 - v) * h
    return {k: v / len(rows) for k, v in tot.items()}


def solve(f, target, lo, hi, rising):
    """Bisection on a monotonic f: rising (f grows with x) or falling."""
    for _ in range(80):
        mid = (lo + hi) / 2
        if (f(mid) < target) == rising:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "runs", "weather_fixture.jsonl")
    data = json.load(open(os.path.join(ROOT, "data", "weather_by_venue.json"), encoding="utf-8"))
    ref = json.load(open(os.path.join(HERE, "afl_weather_rates.json"), encoding="utf-8"))
    want = ref["share_of_outdoor"]
    rows, months, roofed = [], [], 0
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        m = json.loads(line)
        c = climate(data, m["ground"], int(m["month"]), m.get("state", ""))
        if c is None:
            roofed += 1
            continue
        rows.append(c)
        months.append(int(m["month"]))
    wet_k = solve(lambda k: shares(rows, k, 99.0, 99.0)["wet"], want["wet"], 0.0, 3.0, True)
    wind_cut = solve(lambda c: shares(rows, wet_k, c, 99.0)["windy"], want["windy"], 0.0, 60.0, False)
    hot_cut = solve(lambda c: shares(rows, wet_k, wind_cut, c)["hot"], want["hot"], 0.0, 60.0, False)
    got = shares(rows, round(wet_k, 2), round(wind_cut, 1), round(hot_cut, 1))
    print(f"{len(rows)} outdoor matches, {roofed} under the roof")
    print(f"WET_K {wet_k:.2f}  WIND_CUT {wind_cut:.1f}  HOT_CUT {hot_cut:.1f}")
    print("condition | real share of outdoor | game, rounded cut-offs")
    for k in ("wet", "windy", "hot"):
        print(f"{k} | {100 * want[k]:.1f}% | {100 * got[k]:.1f}%")
    n_all = len(rows) + roofed
    print("league-wide, the roofed ground included: "
          + ", ".join(f"{k} {100 * got[k] * len(rows) / n_all:.1f}%" for k in ("wet", "windy", "hot")))
    by_m = {}
    for r, mo in zip(rows, months):
        by_m.setdefault(mo, []).append(r)
    hot_all = got["hot"] * len(rows)
    early = sum(shares(by_m[mo], round(wet_k, 2), round(wind_cut, 1), round(hot_cut, 1))["hot"] * len(by_m[mo])
                for mo in (0, 1) if mo in by_m)
    print(f"hot matches in March and April: {100 * early / hot_all:.0f}%")


if __name__ == "__main__":
    main()
