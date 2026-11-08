#!/usr/bin/env python3
"""Real AFL weather effects, 2016-25 (TODO row 61): tools/balance/afl_weather_rates.json.

Every AFL match of 2016-2019 and 2021-2025 (2020 had 16-minute quarters) with the
weather at its ground while it was played, classified in the game's own order
(Weather.condition: rain first, then wind on a dry day, then heat on a still one),
and each stat's change against a perfect day.

Sources (free, no key, no sign-up):
- AFL Tables season pages (afltables.com/afl/seas/<year>.html): date, local and
  AEST start time, ground, each side's score at every quarter's end.
- AFL Tables team game-by-game pages (afltables.com/afl/stats/teams/<club>/<year>_gbg.html):
  each side's match totals (the Totals row under every stat), keyed by the match page.
- Open-Meteo historical weather API (archive-api.open-meteo.com, CC BY 4.0): hourly
  precipitation, 10 m wind speed and 2 m temperature at each ground, in UTC.

Method:
- The match window is the AEST start time (the bracketed time on AFL Tables, or the
  local time where none is given) to three hours later. Rain is the window's total,
  wind and temperature its mean over the hourly readings inside it.
- Marvel Stadium (Docklands) has a roof: left out, as the game always plays it as a
  perfect day.
- Wet: WET_MM (0.3 mm) of rain or more in the window: about 1 outdoor match in 7,
  near ABC's "about 1 game in 6" for Sydney and Victoria (ABC also used Open-Meteo).
  A trace of rain is not a wet game: at the 80th percentile (0.12 mm, 1 match in 5)
  every wet change comes out a fifth smaller than ABC's, the dry games diluting it.
  Windy: dry, mean wind WIND_KMH (20 km/h, OUW's threshold) or more. Hot: dry and
  still, mean temperature HOT_C (25 C, ABC) or more. Perfect: everything else.
- Each match total is divided by its season-month's outdoor mean, so a season's
  trend or a month's typical weather does not leak into a condition. A condition's
  change is mean(ratio | condition) / mean(ratio | perfect) - 1, with its standard
  error by the delta method. Hot is compared with day matches only (start before
  5 pm local), as heat is a day-game condition.
- Validation: the wet against all dry matches of ABC's own seasons, 2022-25, must
  reproduce ABC's table (marks -13%, tackles +12%, clangers +9%, one-percenters +15%,
  kicks 0%, handballs -1%, contested possessions +7%, contested marks -10%, marks
  inside 50 -14%) within two standard errors; if it does not, the method is wrong
  and the wind and heat columns are not to be trusted.
- Accuracy is goals per scoring shot, its change in percentage points.
- Quarter measures: the breeze split (how much more the odd-quarter against
  even-quarter margin varies in windy matches than on a perfect day: with a breeze
  worth B points of margin a quarter to the side kicking with it, the variance
  grows by 16 B^2) and the fourth quarter's share of the scoring.

    python3 tools/balance/build_weather_rates.py              # fetch (cached) and write
    python3 tools/balance/build_weather_rates.py --offline    # cache only

Pages are cached in data/cache/weather/ (git-ignored); a live fetch waits a second
between requests.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import os
import random
import re
import statistics as st
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(ROOT, "data", "cache", "weather")
OUT = os.path.join(HERE, "afl_weather_rates.json")
SEASONS = [2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025]
UA = "Mozilla/5.0 (compatible; AflAutoBattler/1.0; +https://github.com/gabebartolo-spec/Afl-auto-battler)"
WET_MM = 0.3          # mm of rain in the match window: a wet game (see Method)
WIND_KMH = 20.0       # [OUW]: no measurable effect under 20 km/h
HOT_C = 25.0          # [ABC]: heat over 25 C
DAY_BEFORE = 17.0     # local start hour: a day (or twilight) match
WINDOW_H = 3.0
# afl_weather_rates key -> AFL Tables game-by-game table name.
GBG = {"disposals": "Disposals", "kicks": "Kicks", "handballs": "Handballs", "marks": "Marks",
       "contested_marks": "Contested Marks", "marks_inside_50": "Marks Inside 50",
       "tackles": "Tackles", "inside_50s": "Inside 50s", "clearances": "Clearances",
       "clangers": "Clangers", "frees_for": "Frees", "contested_possessions": "Contested Possessions",
       "uncontested_possessions": "Uncontested Possessions", "one_percenters": "One Percenters",
       "bounces": "Bounces", "hitouts": "Hit Outs", "rebound_50s": "Rebounds",
       "goal_assists": "Goal Assists"}
# Ground -> (latitude, longitude); AFL Tables' names.
GROUNDS = {
    "M.C.G.": (-37.8200, 144.9834), "Docklands": (-37.8165, 144.9475),
    "S.C.G.": (-33.8917, 151.2247), "Sydney Showground": (-33.8434, 151.0670),
    "Stadium Australia": (-33.8474, 151.0634), "Blacktown": (-33.7629, 150.8592),
    "Gabba": (-27.4858, 153.0381), "Carrara": (-28.0063, 153.3666),
    "Adelaide Oval": (-34.9156, 138.5961), "Football Park": (-34.8800, 138.4960),
    "Perth Stadium": (-31.9512, 115.8890), "Subiaco": (-31.9445, 115.8303),
    "Kardinia Park": (-38.1580, 144.3546), "York Park": (-41.4258, 147.1394),
    "Bellerive Oval": (-42.8770, 147.3730), "Manuka Oval": (-35.3181, 149.1347),
    "Eureka Stadium": (-37.5398, 143.8476), "Marrara Oval": (-12.3990, 130.8870),
    "Traeger Park": (-23.7092, 133.8766), "Cazaly's Stadium": (-16.9358, 145.7494),
    "Jiangwan Stadium": (31.3080, 121.5150), "Riverway Stadium": (-19.3172, 146.7310),
    "Norwood Oval": (-34.9205, 138.6332), "Summit Sports Park": (-35.0627, 138.8517),
    "Barossa Park": (-34.6040, 138.8890), "Hands Oval": (-33.3370, 115.6400),
    "Wellington": (-41.2729, 174.7859),
}
ROOFED = {"Docklands"}


def fetch(url: str, name: str, offline: bool) -> str:
    path = os.path.join(CACHE, name)
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    if offline:
        raise SystemExit("not cached: " + name)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read().decode("latin-1" if "afltables" in url else "utf-8", errors="replace")
            break
        except OSError:
            # A dropped connection or a busy server: wait longer each time.
            if attempt == 3:
                raise
            time.sleep(5.0 * (attempt + 1) ** 2)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # The page cache sits inside the Godot project (data/cache, git-ignored):
    # a .gdignore keeps the editor from importing about 100 MB of pages.
    gdignore = os.path.join(ROOT, "data", "cache", ".gdignore")
    if not os.path.exists(gdignore):
        open(gdignore, "a").close()
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    time.sleep(1.0)
    return body


def clock(t: str) -> float:
    m = re.match(r"(\d{1,2}):(\d{2}) ([AP])M", t)
    h = int(m.group(1)) % 12 + (12 if m.group(3) == "P" else 0)
    return h + int(m.group(2)) / 60.0


def quarters(tt: str) -> list:
    """Cumulative 'g.b' at each quarter's end -> points scored in each quarter."""
    cum = [int(g) * 6 + int(b) for g, b in re.findall(r"(\d+)\.(\d+)", html.unescape(tt))]
    return [c - (cum[i - 1] if i else 0) for i, c in enumerate(cum)]


def season_matches(year: int, offline: bool) -> tuple[list, set]:
    s = fetch(f"https://afltables.com/afl/seas/{year}.html", f"seas_{year}.html", offline)
    out, slugs = [], set(re.findall(r"teams/(\w+)_idx\.html", s))
    for tab in re.findall(r'<table\s+style="font: 12px Verdana;"\s+width=100% border=1>(.*?)</table>', s, re.S):
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tab, re.S)
        if len(rows) != 2:
            continue
        cells = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S) for r in rows]
        if any(len(c) < 4 for c in cells):
            continue
        link = re.search(r"stats/games/(\d{4})/(\d+)\.html", cells[1][3])
        when = re.search(r"\w{3} (\d{2}-\w{3}-\d{4}) (\d{1,2}:\d{2} [AP]M)(?: \((\d{1,2}:\d{2} [AP]M)\))?", cells[0][3])
        venue = re.search(r'Venue:</b>\s*<a href="[^"]*">([^<]+)</a>', cells[0][3])
        if not (link and when and venue):
            continue
        d = datetime.strptime(when.group(1), "%d-%b-%Y").date()
        local = clock(when.group(2))
        aest = clock(when.group(3)) if when.group(3) else local
        teams = [re.sub(r"<[^>]+>", "", c[0]).strip() for c in cells]
        out.append({"key": link.group(2), "season": year, "date": d.isoformat(), "local": local,
                    "aest": aest, "venue": html.unescape(venue.group(1)).strip(), "teams": teams,
                    "q": [quarters(c[1]) for c in cells],
                    "gb": [[int(x) for x in re.findall(r"(\d+)\.(\d+)", html.unescape(c[1]))[-1]] for c in cells]})
    return out, slugs


def team_totals(year: int, slug: str, offline: bool) -> dict:
    """Match page key -> {stat: this side's total}."""
    s = fetch(f"https://afltables.com/afl/stats/teams/{slug}/{year}_gbg.html", f"gbg_{year}_{slug}.html", offline)
    want = {v: k for k, v in GBG.items()}
    out: dict = {}
    for name, body in re.findall(r'<th colspan="\d+">([^<]+)</th>(.*?)</table>', s, re.S):
        key = want.get(name.strip())
        if key is None:
            continue
        tot = re.search(r"<th align=left>Totals</th>(.*?)</tr>", body, re.S)
        opp = re.search(r"<th align=left>Opponent</th>(.*?)</tr>", body, re.S)
        if not tot or not opp:
            continue
        vals = re.findall(r"<th>([^<]*)</th>", tot.group(1))
        games = re.findall(r"<th>(.*?)</th>", opp.group(1))
        for v, g in zip(vals, games):
            m = re.search(r"games/\d{4}/(\d+)\.html", g)
            if m and v.strip().isdigit():
                out.setdefault(m.group(1), {})[key] = int(v)
    return out


def weather(venue: str, year: int, first: str, last: str, offline: bool) -> dict:
    """UTC 'YYYY-MM-DDTHH:00' -> (rain mm in the hour before, wind km/h, temp C)."""
    lat, lon = GROUNDS[venue]
    url = ("https://archive-api.open-meteo.com/v1/archive?latitude=%.4f&longitude=%.4f"
           "&start_date=%s&end_date=%s&hourly=precipitation,wind_speed_10m,temperature_2m&timezone=GMT"
           % (lat, lon, first, last))
    name = "om_%s_%d.json" % (re.sub(r"[^A-Za-z]+", "_", venue).strip("_").lower(), year)
    j = json.loads(fetch(url, name, offline))
    h = j["hourly"]
    return {t: (h["precipitation"][i], h["wind_speed_10m"][i], h["temperature_2m"][i])
            for i, t in enumerate(h["time"])}


def window(wx: dict, d: str, aest: float) -> tuple:
    """Rain total, mean wind and mean temperature over the match window."""
    start = datetime.fromisoformat(d) + timedelta(hours=aest - 10.0)  # AEST -> UTC
    end = start + timedelta(hours=WINDOW_H)
    rain, wind, temp = 0.0, [], []
    t = start.replace(minute=0)
    while t <= end + timedelta(hours=1):
        row = wx.get(t.strftime("%Y-%m-%dT%H:00"))
        if row and None not in row:
            # The hour stamped t holds the rain of (t - 1 h, t]: count its overlap.
            lo, hi = max(start, t - timedelta(hours=1)), min(end, t)
            if hi > lo:
                rain += row[0] * (hi - lo).total_seconds() / 3600.0
            if start <= t <= end:
                wind.append(row[1])
                temp.append(row[2])
        t += timedelta(hours=1)
    if not wind:
        return None
    return rain, sum(wind) / len(wind), sum(temp) / len(temp)


def quantile(xs: list, q: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def ratio_change(c: list, p: list) -> tuple:
    """mean(c) / mean(p) - 1 and its delta-method standard error."""
    mc, mp = st.mean(c), st.mean(p)
    sc, sp = st.stdev(c) / math.sqrt(len(c)), st.stdev(p) / math.sqrt(len(p))
    r = mc / mp
    return r - 1.0, r * math.sqrt((sc / mc) ** 2 + (sp / mp) ** 2)


def diff_change(c: list, p: list) -> tuple:
    return st.mean(c) - st.mean(p), math.sqrt(st.variance(c) / len(c) + st.variance(p) / len(p))


def breeze(S_w: list, S_p: list, rng: random.Random, n_boot: int = 2000) -> dict:
    """Breeze worth B points of margin a quarter: Var(S_windy) - Var(S_calm) = 16 B^2."""
    def b_of(w, p):
        return math.sqrt(max(0.0, st.variance(w) - st.variance(p))) / 4.0
    boots = sorted(b_of(rng.choices(S_w, k=len(S_w)), rng.choices(S_p, k=len(S_p))) for _ in range(n_boot))
    dv = st.variance(S_w) - st.variance(S_p)
    return {"points_a_quarter": round(b_of(S_w, S_p), 2), "se": round(st.stdev(boots), 2),
            "ci95": [round(boots[int(0.025 * n_boot)], 2), round(boots[int(0.975 * n_boot)], 2)],
            "var_windy": round(st.variance(S_w), 1), "var_perfect": round(st.variance(S_p), 1),
            "var_gap": round(dv, 1)}


def odd_even(m: dict) -> float:
    q = [m["q"][0][i] - m["q"][1][i] for i in range(4)]
    return (q[0] + q[2]) - (q[1] + q[3])


def collect(offline: bool) -> list:
    """Every match with its two sides' totals, its quarter scores and its weather."""
    matches = []
    for year in SEASONS:
        ms, slugs = season_matches(year, offline)
        tot: dict = {}
        for slug in sorted(slugs):
            for k, v in team_totals(year, slug, offline).items():
                tot.setdefault(k, []).append(v)
        unknown = sorted({m["venue"] for m in ms} - set(GROUNDS))
        if unknown:
            raise SystemExit(f"{year}: no coordinates for {unknown}")
        wx: dict = {}
        for venue in sorted({m["venue"] for m in ms} - ROOFED):
            ds = sorted(m["date"] for m in ms if m["venue"] == venue)
            last = (date.fromisoformat(ds[-1]) + timedelta(days=1)).isoformat()
            wx[venue] = weather(venue, year, ds[0], last, offline)
        for m in ms:
            sides = tot.get(m["key"], [])
            if len(sides) != 2 or len(m["q"][0]) < 4 or len(m["q"][1]) < 4:
                continue
            m["stats"] = {k: sides[0].get(k, 0) + sides[1].get(k, 0) for k in GBG}
            m["roofed"] = m["venue"] in ROOFED
            if not m["roofed"]:
                w = window(wx[m["venue"]], m["date"], m["aest"])
                if w is None:
                    continue
                m["rain"], m["wind"], m["temp"] = w
            matches.append(m)
        print(f"{year}: {len(ms)} matches on the season page, {sum(1 for m in matches if m['season'] == year)} with stats", file=sys.stderr)
    # Goals, behinds and points from the season page's quarter scores (rushed behinds included).
    for m in matches:
        pts = [g * 6 + b for g, b in m["gb"]]
        m["stats"]["score"] = sum(pts)
        m["stats"]["goals"] = m["gb"][0][0] + m["gb"][1][0]
        m["stats"]["behinds"] = m["gb"][0][1] + m["gb"][1][1]
        m["stats"]["q4_share"] = (m["q"][0][3] + m["q"][1][3]) / max(1, sum(pts))
        m["stats"]["accuracy"] = m["stats"]["goals"] / max(1, m["stats"]["goals"] + m["stats"]["behinds"])
    return matches


def analyse(matches: list, wet_mm: float | None = None, seasons: list | None = None) -> dict:
    """The conditions' changes against a perfect day. wet_mm None: WET_MM; a negative
    wet_mm is a share, the wet cut being that quantile of outdoor matches' rain."""
    matches = [m for m in matches if seasons is None or m["season"] in seasons]
    out_m = [m for m in matches if not m["roofed"]]
    if wet_mm is None:
        wet_mm = WET_MM
    elif wet_mm < 0:
        wet_mm = quantile([m["rain"] for m in out_m], 1.0 + wet_mm)
    for m in out_m:
        if m["rain"] >= wet_mm and m["rain"] > 0:
            m["cond"] = "wet"
        elif m["wind"] >= WIND_KMH:
            m["cond"] = "windy"
        elif m["temp"] >= HOT_C:
            m["cond"] = "hot"
        else:
            m["cond"] = "perfect"
        m["day"] = m["local"] < DAY_BEFORE
    # Normalise each stat by its season-month outdoor mean.
    keys = list(GBG) + ["goals", "behinds", "score"]
    groups: dict = {}
    for m in out_m:
        groups.setdefault((m["season"], m["date"][:7]), []).append(m)
    for g in groups.values():
        for k in keys:
            mean = st.mean(x["stats"][k] for x in g)
            for x in g:
                x.setdefault("norm", {})[k] = x["stats"][k] / mean if mean else 1.0
    by = {c: [m for m in out_m if m["cond"] == c] for c in ("perfect", "wet", "windy", "hot")}
    perfect_day = [m for m in by["perfect"] if m["day"]]
    dry = [m for m in out_m if m["cond"] != "wet"]
    rng = random.Random(61)

    def column(cond_ms, base_ms):
        col = {}
        for k in keys:
            ch, se = ratio_change([m["norm"][k] for m in cond_ms], [m["norm"][k] for m in base_ms])
            col[k] = {"change": round(ch, 4), "se": round(se, 4)}
        d, se = diff_change([m["stats"]["q4_share"] for m in cond_ms], [m["stats"]["q4_share"] for m in base_ms])
        col["q4_share"] = {"change_points": round(100 * d, 2), "se": round(100 * se, 2),
                           "base": round(100 * st.mean(m["stats"]["q4_share"] for m in base_ms), 2)}
        d, se = diff_change([m["stats"]["accuracy"] for m in cond_ms], [m["stats"]["accuracy"] for m in base_ms])
        col["accuracy"] = {"change_points": round(100 * d, 2), "se": round(100 * se, 2),
                           "base": round(100 * st.mean(m["stats"]["accuracy"] for m in base_ms), 2)}
        return col

    cols = {"wet": column(by["wet"], by["perfect"]), "windy": column(by["windy"], by["perfect"]),
            "hot": column([m for m in by["hot"] if m["day"]], perfect_day)}
    cols["windy"]["breeze"] = breeze([odd_even(m) for m in by["windy"]], [odd_even(m) for m in by["perfect"]], rng)
    for c in ("wet", "hot"):
        cols[c]["breeze"] = breeze([odd_even(m) for m in by[c]], [odd_even(m) for m in by["perfect"]], rng)
    wet_v_dry = column(by["wet"], dry)
    abc = {"marks": -0.13, "tackles": 0.12, "clangers": 0.09, "one_percenters": 0.15, "kicks": 0.0,
           "handballs": -0.01, "contested_possessions": 0.07, "contested_marks": -0.10,
           "marks_inside_50": -0.14}
    gate = {}
    for k, real in abc.items():
        ours = wet_v_dry[k]
        gate[k] = {"abc": real, "ours": ours["change"], "se": ours["se"],
                   "within_2se": abs(ours["change"] - real) <= 2 * ours["se"]}
    doc = {
        "source": ("AFL Tables season pages and team game-by-game pages (afltables.com), 2016-2019 and "
                   "2021-2025, with Open-Meteo historical hourly weather at each ground "
                   "(archive-api.open-meteo.com, CC BY 4.0). Built by tools/balance/build_weather_rates.py."),
        "method": __doc__.split("Method:")[1].split("    python3")[0].strip(),
        "thresholds": {"wet_mm_in_window": round(wet_mm, 2), 
                       "windy_kmh_mean": WIND_KMH, "hot_c_mean": HOT_C, "window_hours": WINDOW_H,
                       "day_match_before_local": DAY_BEFORE},
        "n": {"matches": len(matches), "roofed_left_out": len(matches) - len(out_m), "outdoor": len(out_m),
              **{c: len(v) for c, v in by.items()}, "perfect_day": len(perfect_day),
              "hot_day": sum(1 for m in by["hot"] if m["day"])},
        "share_of_outdoor": {c: round(len(v) / len(out_m), 3) for c, v in by.items()},
        "change_vs_perfect": cols,
        "wet_vs_dry": wet_v_dry,
        "validation_abc_wet": gate,
        "validation_abc_wet_all": gate,
    }
    return doc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--explore", action="store_true", help="print the ABC gate at several wet thresholds")
    o = ap.parse_args()
    matches = collect(o.offline)
    if o.explore:
        for seasons in (None, [2022, 2023, 2024, 2025]):
            for mm in (-0.2, 0.3, 0.5, 1.0, 2.0, 4.0):
                d = analyse(matches, mm, seasons)
                g = d["validation_abc_wet"]
                print(f"{'2022-25' if seasons else '2016-25'} wet>={d['thresholds']['wet_mm_in_window']:.2f} mm "
                      f"n={d['n']['wet']} ({100*d['share_of_outdoor']['wet']:.0f}%): "
                      + ", ".join(f"{k[:8]} {100*v['ours']:+.1f}({100*v['se']:.1f}){'' if v['within_2se'] else '!'}"
                                  for k, v in g.items()))
        return
    doc = analyse(matches)
    abc_seasons = analyse(matches, seasons=[2022, 2023, 2024, 2025])
    doc["validation_abc_wet"] = {"seasons": "2022-25", "wet_n": abc_seasons["n"]["wet"],
                                 "dry_n": abc_seasons["n"]["outdoor"] - abc_seasons["n"]["wet"],
                                 "stats": abc_seasons["validation_abc_wet"]}
    doc["validation_abc_wet_2016_25"] = doc.pop("validation_abc_wet_all")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    gate = doc["validation_abc_wet"]["stats"]
    print(json.dumps({"n": doc["n"], "share": doc["share_of_outdoor"], "thresholds": doc["thresholds"]}, indent=1))
    print("ABC wet v dry gate, 2022-25 (wet %d, dry %d):" % (doc["validation_abc_wet"]["wet_n"], doc["validation_abc_wet"]["dry_n"]))
    for k, g in gate.items():
        print(f"  {k:24s} ABC {100*g['abc']:+5.0f}%  ours {100*g['ours']:+6.1f}% (se {100*g['se']:.1f})  {'ok' if g['within_2se'] else 'MISS'}")


if __name__ == "__main__":
    main()
