#!/usr/bin/env python3
"""Check data/legacy/second_tier/ (TODO row 142, Legacy mode phase L7).

    python tools/check_legacy_second_tier.py            # report, exit 1 on a hard failure
    python tools/check_legacy_second_tier.py --quiet    # counts only
    python tools/check_legacy_second_tier.py --year 1997  # print one season's shape

The real second tier for every season 1990-2026: what the AFL clubs' players
played in below the seniors. leagues.csv holds the years each league was held;
sides.csv each side's span in one league (scripts/core/SecondTier.gd reads both).

Hard failures (exit 1): a row with no source or evidence; an unknown kind or
league; a span that ends before it starts; a side in two rows the same season;
a reserves side without exactly one AFL club, an aligned side without one or
two, a standalone side with any; a none row with a code; an AFL club
named in a season it did not play; an AFL club with no answer for a season it
played (its own side, an aligned club, a host league or a recorded none); a
held league with fewer than two sides; and 2026 not matching today's VFL, SANFL
and WAFL in data/state_leagues/ (the same codes, kinds and AFL clubs), so a
campaign that reaches 2026 plays today's shape.

Warnings: an AFL club with two sides the same season, a side whose span runs
through a season its league was not held.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "data", "legacy", "second_tier")
TODAY = os.path.join(ROOT, "data", "state_leagues")
FIRST, LAST = 1990, 2026
KINDS = {"reserves", "aligned", "standalone", "host", "none"}
CORE = {"BRL", "CAR", "COL", "ESS", "GEE", "HAW", "MEL", "NTH", "RIC", "STK", "SYD", "WCE", "WBD"}


def afl_clubs(y: int) -> set[str]:
    c = set(CORE)
    if y <= 1996:
        c.add("FIT")
    for code, first in (("ADE", 1991), ("FRE", 1995), ("PAD", 1997), ("GCS", 2011), ("GWS", 2012)):
        if y >= first:
            c.add(code)
    return c


def _read(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _span(r: dict) -> tuple[int, int]:
    return int(r["from"]), int(r["to"]) if r["to"].strip() else 0


def covers(r: dict, y: int) -> bool:
    a, b = _span(r)
    return a <= y and (b == 0 or y <= b)


def held(leagues: list[dict], y: int) -> dict:
    return {r["league"]: r["name"] for r in leagues if covers(r, y)}


def shape(leagues: list[dict], sides: list[dict], y: int) -> dict:
    h = held(leagues, y)
    out = {lg: [] for lg in h}
    for s in sides:
        if s["code"] and covers(s, y) and s["league"] in h:
            out[s["league"]].append(s)
    return {lg: rows for lg, rows in out.items() if rows}  # as SecondTier.shape: a league with no listed side is not laid out


def check(quiet: bool) -> int:
    leagues = _read(os.path.join(DIR, "leagues.csv"))
    sides = _read(os.path.join(DIR, "sides.csv"))
    fails: list[str] = []
    warns: list[str] = []
    ids = {r["league"] for r in leagues}

    for i, r in enumerate(leagues + sides):
        where = f"{r['league']} {r.get('code') or r.get('name')} {r['from']}-{r['to']}"
        if not r.get("source_url", "").strip() or not r.get("evidence", "").strip():
            fails.append(f"{where}: no source or evidence")
        a, b = _span(r)
        if b and b < a:
            fails.append(f"{where}: ends before it starts")
        if a < FIRST - 100 or a > LAST:
            fails.append(f"{where}: starts outside {FIRST}-{LAST}")

    for s in sides:
        where = f"{s['league']} {s['code'] or s['kind']} {s['from']}-{s['to']} ({s['afl_club']})"
        kind = s["kind"]
        afl = [c for c in s["afl_club"].split("|") if c]
        if kind not in KINDS:
            fails.append(f"{where}: unknown kind {kind}")
        if s["league"] not in ids:
            fails.append(f"{where}: unknown league")
        if kind in ("host", "none"):
            if kind == "none" and s["code"]:
                fails.append(f"{where}: a none row has no code")
            if len(afl) != 1:
                fails.append(f"{where}: a {kind} row names one AFL club")
        if kind in ("reserves", "aligned", "standalone") and not s["code"]:
            fails.append(f"{where}: no code")
        if kind == "reserves" and len(afl) != 1:
            fails.append(f"{where}: a reserves side belongs to one AFL club")
        if kind == "aligned" and len(afl) not in (1, 2):
            fails.append(f"{where}: an aligned side has one or two AFL clubs")
        if kind == "standalone" and afl:
            fails.append(f"{where}: a standalone side has no AFL club")
        a, b = _span(s)
        for y in range(max(a, FIRST), (b or LAST) + 1):
            for c in afl:
                if c not in afl_clubs(y):
                    fails.append(f"{where}: {c} did not play in {y}")
                    break
            if kind in ("reserves", "aligned", "standalone", "host") and s["league"] not in held(leagues, y):
                warns.append(f"{where}: {s['league']} not held in {y}")

    for y in range(FIRST, LAST + 1):
        seen: dict[str, int] = defaultdict(int)
        for s in sides:
            if s["code"] and covers(s, y):
                seen[s["code"]] += 1
        for code, n in seen.items():
            if n > 1:
                fails.append(f"{y}: {code} is in {n} rows")
        h = held(leagues, y)
        sh = shape(leagues, sides, y)
        complete = {r["league"] for r in leagues if covers(r, y) and r.get("complete", "yes") == "yes"}
        for lg, rows in sh.items():
            if lg in complete and len(rows) < 2:
                fails.append(f"{y}: {lg} is held with {len(rows)} side(s)")
        for club in sorted(afl_clubs(y)):
            own = [s for s in sides if covers(s, y) and club in s["afl_club"].split("|")
                   and (s["kind"] in ("reserves", "aligned") or (s["kind"] == "host" and s["code"]))
                   and s["league"] in h]
            other = [s for s in sides if covers(s, y) and club in s["afl_club"].split("|")
                     and ((s["kind"] == "host" and s["league"] in h) or s["kind"] == "none")]
            if not own and not other:
                fails.append(f"{y}: {club} has no second tier")
            if len(own) > 1:
                warns.append(f"{y}: {club} has {len(own)} sides ({', '.join(s['code'] for s in own)})")

    # 2026 is today's VFL, SANFL and WAFL.
    want = set()
    for lg in ("VFL", "SANFL", "WAFL"):
        for r in _read(os.path.join(TODAY, f"{lg.lower()}_clubs_2026.csv")):
            want.add((lg, r["code"], r["kind"], r["afl_club"]))
    got = set()
    for lg, rows in shape(leagues, sides, LAST).items():
        for s in rows:
            got.add((lg, s["code"], s["kind"], s["afl_club"]))
    for t in sorted(want - got):
        fails.append(f"2026: today's {t} is missing")
    for t in sorted(got - want):
        fails.append(f"2026: {t} is not in today's leagues")

    counts = {y: {lg: len(rows) for lg, rows in shape(leagues, sides, y).items()} for y in (1990, 2000, 2026)}
    print(f"second tier: {len(leagues)} league rows, {len(sides)} side rows; "
          f"1990 {counts[1990]}, 2000 {counts[2000]}, 2026 {counts[2026]}")
    if not quiet:
        for w in sorted(set(warns)):
            print("warn:", w)
    for f in fails:
        print("FAIL:", f)
    print(f"{len(fails)} failures, {len(set(warns))} warnings")
    return 1 if fails else 0


def show(year: int) -> None:
    leagues = _read(os.path.join(DIR, "leagues.csv"))
    sides = _read(os.path.join(DIR, "sides.csv"))
    for lg, rows in shape(leagues, sides, year).items():
        print(f"{lg} ({held(leagues, year)[lg]}): {len(rows)}")
        for s in rows:
            print(f"  {s['code']:6} {s['kind']:10} {s['afl_club']:8} {s['name']}")
    for s in sides:
        if not s["code"] and covers(s, year):
            print(f"  {s['afl_club']}: {s['kind']} {s['league']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--year", type=int)
    a = ap.parse_args()
    if a.year:
        show(a.year)
        return 0
    return check(a.quiet)


if __name__ == "__main__":
    sys.exit(main())
