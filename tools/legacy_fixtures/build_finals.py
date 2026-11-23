#!/usr/bin/env python3
"""Build data/legacy/finals.csv, the real finals series 1990-2025, from the AFL
Tables season pages fetch.py cached (Legacy mode, bug bash 2026-11-23).

    python tools/legacy_fixtures/build_finals.py --cache <dir>

One row per final, replays included: year, week, kind, label, home, away, ground,
date.

- week: the finals week as the game counts it (1 qualifying and elimination
  finals, 2 semi finals, 3 preliminary finals, 4 the Grand Final). A replay of a
  drawn final keeps its final's week.
- kind: QF, EF, SF, PF or GF.
- label: the final's name as AFL Tables prints it.
- home, away: the game's club codes (build.py's TEAM); AFL Tables lists the home
  club first.
- ground: the game's ground key (build.py's VENUE), so a screen shows the name
  of the year through GameDB.
- date: ISO date the final was played (local).
- own: the club whose own ground it was, when the final went to one club's ground
  rather than a shared Victorian finals ground (Geelong at Kardinia Park in 2013,
  Adelaide at Football Park against Geelong in 1997); else empty. Only that club
  can be sent there. A ground is one club's when no other Victorian club played
  home games there that year (data/legacy/fixtures.csv, three or more).
- in_vic: 1 when the ground is in Victoria. An interstate club hosting a final in
  Victoria (West Coast at Waverley in 1990 and 1991, Brisbane at the MCG in the
  2004 preliminary final) is how the game sends one of its interstate hosts there.

The game draws its own finals from its own ladder, so its clubs are not the real
ones; Season.finals_venue reads this table for where a Victorian club's final was
really played that week (the MCG, Waverley Park, Docklands, and in 2020 and 2021
the grounds of the other states). Nothing is guessed: an unknown club, venue or
final name stops the build.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import DATE_RE, MONTHS, ROW_RE, TABLE_RE, TEAM, TEAM_RE, VENUE, VENUE_RE  # noqa: E402
from fetch import cache_path, season_url  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "legacy", "finals.csv")
SEASONS = range(1990, 2026)

import re  # noqa: E402

HEAD_RE = re.compile(r"<td align=center><b>([A-Za-z ]+?)</td></tr></table>")
# Every ground a final was played at 1990-2025, and whether it is in Victoria.
STATE_VIC = {
    "MCG": True, "Waverley Park": True, "Marvel Stadium": True, "GMHBA Stadium": True,
    "Accor Stadium": False, "Adelaide Oval": False, "Engie Stadium": False, "Football Park": False,
    "Optus Stadium": False, "People First Stadium": False, "SCG": False, "Subiaco Oval": False,
    "The Gabba": False, "WACA": False, "York Park": False,
}
VIC_CLUBS = {"CAR", "COL", "ESS", "FIT", "GEE", "HAW", "MEL", "NTH", "RIC", "STK", "WBD"}
FIXTURES = os.path.join(ROOT, "data", "legacy", "fixtures.csv")

KINDS = {
    "Qualifying Final": ("QF", 1), "Elimination Final": ("EF", 1),
    "Semi Final": ("SF", 2), "Preliminary Final": ("PF", 3), "Grand Final": ("GF", 4),
}


def finals_rows(body: str, year: int) -> list[dict]:
    start = body.find('<a name="fin">')
    if start < 0:
        raise SystemExit(f"{year}: no finals section")
    body = body[start:]
    end = body.find('<a name="lad">')
    if end > 0:
        body = body[:end]
    heads = list(HEAD_RE.finditer(body))
    out: list[dict] = []
    for k, h in enumerate(heads):
        label = h.group(1).strip()
        if label == "Finals":
            continue
        base = label.replace(" Replay", "")
        if base not in KINDS:
            raise SystemExit(f"{year}: unknown final '{label}'")
        chunk = body[h.end():heads[k + 1].start() if k + 1 < len(heads) else len(body)]
        tables = [t for t in TABLE_RE.findall(chunk) if "Venue:" in t]
        if len(tables) != 1:
            raise SystemExit(f"{year} {label}: {len(tables)} match tables")
        rows = ROW_RE.findall(tables[0])
        teams = [TEAM_RE.search(r) for r in rows[:2]]
        if len(rows) != 2 or not all(teams):
            raise SystemExit(f"{year} {label}: a match without its two clubs")
        slugs = [t.group(1) for t in teams]
        for s in slugs:
            if s not in TEAM:
                raise SystemExit(f"{year} {label}: unknown AFL Tables club '{s}'")
        date = DATE_RE.search(rows[0])
        venue = VENUE_RE.search(rows[0])
        if not date or not venue:
            raise SystemExit(f"{year} {label}: no date or venue")
        if venue.group(1) not in VENUE:
            raise SystemExit(f"{year} {label}: unknown AFL Tables venue '{venue.group(1)}'")
        kind, week = KINDS[base]
        out.append({
            "year": year, "week": week, "kind": kind, "label": label,
            "home": TEAM[slugs[0]], "away": TEAM[slugs[1]], "ground": VENUE[venue.group(1)],
            "date": "%s-%02d-%s" % (date.group(3), MONTHS[date.group(2)], date.group(1)),
        })
    return out


def tenants() -> dict:
    """(year, ground) -> the clubs with three or more home games there that year."""
    count: dict = {}
    with open(FIXTURES, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            key = (int(r["year"]), r["ground"])
            count.setdefault(key, {})
            count[key][r["home"]] = count[key].get(r["home"], 0) + 1
    return {k: {c for c, n in v.items() if n >= 3} for k, v in count.items()}


def own_club(row: dict, ten: dict) -> str:
    t = ten.get((row["year"], row["ground"]), set())
    others = {c for c in t if c in VIC_CLUBS and c != row["home"]}
    if others:
        return ""  # a shared Victorian ground
    if row["home"] in t:
        return row["home"]
    if row["away"] in t:
        return row["away"]
    return ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    rows: list[dict] = []
    ten = tenants()
    for y in SEASONS:
        path = cache_path(a.cache, season_url(y))
        if not os.path.exists(path):
            raise SystemExit(f"missing {path}: run fetch.py first")
        with open(path, encoding="utf-8", errors="replace") as fh:
            got = finals_rows(fh.read(), y)
        if sum(1 for r in got if r["kind"] == "GF") < 1:
            raise SystemExit(f"{y}: no Grand Final read")
        got.sort(key=lambda r: (r["week"], r["date"]))
        for r in got:
            if r["ground"] not in STATE_VIC:
                raise SystemExit(f"{y}: no state for finals ground '{r['ground']}'")
            r["own"] = "" if r["kind"] == "GF" else own_club(r, ten)
            r["in_vic"] = 1 if STATE_VIC[r["ground"]] else 0
        rows.extend(got)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "week", "kind", "label", "home", "away", "ground", "date", "own", "in_vic"],
                lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} finals, {len(SEASONS)} seasons -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
