#!/usr/bin/env python3
"""Build data/legacy/fixtures.csv, the real home-and-away fixtures 1990-2026, from
the AFL Tables season pages fetch.py cached (Legacy mode, TODO row 142, phase L6).

    python tools/legacy_fixtures/build.py --cache <dir>

One row per home-and-away match: year, round, home, away, ground, date.

- round: the AFL Tables round number. AFL Tables numbers an Opening Round (2024 on)
  as Round 1, so every season's rounds run 1..N with no gap, as the game's do.
- home, away: the game's club codes, one code a club across eras (the Brisbane
  Bears are BRL, Footscray WBD; GameDB.CLUB_CODE_ALIASES). AFL Tables lists the
  home club first.
- ground: the game's key for the ground (today's name, or the last name it had
  while the AFL played there; data/legacy/ground_names.csv and the L9 notes), so a
  screen shows its name of the year through GameDB, never this column directly.
- date: ISO date the match was played (local), from the page.

Byes are not rows. Finals are not here (the game draws its own finals). Nothing is
guessed: an unknown club or venue stops the build. tools/check_legacy_fixtures.py
checks the result.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import SEASONS, cache_path, season_url  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "legacy", "fixtures.csv")

# AFL Tables team slugs -> the game's codes (one code a club across eras).
TEAM = {
    "adelaide": "ADE", "brisbaneb": "BRL", "brisbanel": "BRL", "carlton": "CAR",
    "collingwood": "COL", "essendon": "ESS", "fitzroy": "FIT", "fremantle": "FRE",
    "geelong": "GEE", "goldcoast": "GCS", "gws": "GWS", "hawthorn": "HAW",
    "melbourne": "MEL", "kangaroos": "NTH", "padelaide": "PAD", "richmond": "RIC",
    "stkilda": "STK", "swans": "SYD", "westcoast": "WCE", "bullldogs": "WBD",
    "bulldogs": "WBD", "footscray": "WBD",
}

# AFL Tables venue names -> the game's ground keys.
VENUE = {
    "M.C.G.": "MCG",
    "S.C.G.": "SCG",
    "W.A.C.A.": "WACA",
    "Gabba": "The Gabba",
    "Docklands": "Marvel Stadium",
    "Kardinia Park": "GMHBA Stadium",
    "Carrara": "People First Stadium",
    "Princes Park": "Ikon Park",
    "Western Oval": "Whitten Oval",
    "Waverley Park": "Waverley Park",
    "Football Park": "Football Park",
    "Subiaco": "Subiaco Oval",
    "Victoria Park": "Victoria Park",
    "Windy Hill": "Windy Hill",
    "Moorabbin Oval": "Moorabbin Oval",
    "Stadium Australia": "Accor Stadium",
    "Bruce Stadium": "Bruce Stadium",
    "North Hobart": "North Hobart Oval",
    "Manuka Oval": "Manuka Oval",
    "Adelaide Oval": "Adelaide Oval",
    "Perth Stadium": "Optus Stadium",
    "Sydney Showground": "Engie Stadium",
    "Bellerive Oval": "Bellerive Oval",
    "Norwood Oval": "Norwood Oval",
    "Summit Sports Park": "Barossa Park",
    "Barossa Park": "Barossa Park",
    "York Park": "York Park",
    "Marrara Oval": "Marrara Oval",
    "Traeger Park": "Traeger Park",
    "Hands Oval": "Hands Oval",
    "Cazaly's Stadium": "Cazaly's Stadium",
    "Eureka Stadium": "Mars Stadium",
    "Jiangwan Stadium": "Jiangwan Stadium",
    "Riverway Stadium": "Riverway Stadium",
    "Wellington": "Sky Stadium",
    "Blacktown": "Blacktown International Sportspark",
}

# Matches fixtured but never played, which AFL Tables does not list: the game plays
# the season as it was drawn. Round 14, 2015: Adelaide v Geelong at Adelaide Oval,
# Sunday 5 July, cancelled after the death of Adelaide coach Phil Walsh
# (https://en.wikipedia.org/wiki/2015_AFL_season).
UNPLAYED = [
    {"year": 2015, "round": 14, "home": "ADE", "away": "GEE", "ground": "Adelaide Oval", "date": "2015-07-05"},
]

MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}

ROUND_RE = re.compile(r'<a name="(\d+)"></a>')
TABLE_RE = re.compile(r"<table[^>]*border=1>(.*?)</table>", re.S)
ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
TEAM_RE = re.compile(r'teams/([a-z]+)_idx\.html')
DATE_RE = re.compile(r"\w{3} (\d{2})-(\w{3})-(\d{4})")
VENUE_RE = re.compile(r'<b>Venue:</b>\s*<a href="[^"]*">([^<]+)</a>')


def season_rows(body: str, year: int) -> list[dict]:
    end = body.find('<a name="lad">')
    body = body[:end if end > 0 else len(body)]
    marks = list(ROUND_RE.finditer(body))
    out: list[dict] = []
    for k, m in enumerate(marks):
        rnd = int(m.group(1))
        chunk = body[m.end():marks[k + 1].start() if k + 1 < len(marks) else len(body)]
        for table in TABLE_RE.findall(chunk):
            rows = ROW_RE.findall(table)
            if "Venue:" not in table:
                continue  # a bye, or the round's ladder beside the matches
            if len(rows) != 2:
                raise SystemExit(f"{year} round {rnd}: a match table of {len(rows)} rows")
            teams = [TEAM_RE.search(r) for r in rows]
            if not all(teams):
                raise SystemExit(f"{year} round {rnd}: a match row without a club")
            slugs = [t.group(1) for t in teams]
            for s in slugs:
                if s not in TEAM:
                    raise SystemExit(f"{year} round {rnd}: unknown AFL Tables club '{s}'")
            date = DATE_RE.search(rows[0])
            venue = VENUE_RE.search(rows[0])
            if not date or not venue:
                raise SystemExit(f"{year} round {rnd}: a match without its date or venue")
            if venue.group(1) not in VENUE:
                raise SystemExit(f"{year} round {rnd}: unknown AFL Tables venue '{venue.group(1)}'")
            out.append({
                "year": year, "round": rnd,
                "home": TEAM[slugs[0]], "away": TEAM[slugs[1]],
                "ground": VENUE[venue.group(1)],
                "date": "%s-%02d-%s" % (date.group(3), MONTHS[date.group(2)], date.group(1)),
            })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    rows: list[dict] = []
    for y in SEASONS:
        path = cache_path(a.cache, season_url(y))
        if not os.path.exists(path):
            raise SystemExit(f"missing {path}: run fetch.py first")
        with open(path, encoding="utf-8") as fh:
            got = season_rows(fh.read(), y)
        if not got:
            raise SystemExit(f"{y}: no matches read")
        got.extend(u for u in UNPLAYED if u["year"] == y)
        got.sort(key=lambda r: (r["round"], r["date"]))
        rows.extend(got)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "round", "home", "away", "ground", "date"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} matches, {len(SEASONS)} seasons -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
