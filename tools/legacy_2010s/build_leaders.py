#!/usr/bin/env python3
"""
The 2010 start's senior coaches and captains, and each coach rated from his
real record before 2010 (Legacy mode, TODO row 142; the 1990 start's
coaches_1990.csv, captains_1990.csv and coach ratings, for 2010).

Reads Wikipedia's "2010 AFL season" page, "Club leadership" and "Coach
changes" (cached under data/cache/legacy_2010s/, fetched once when missing).
The leadership table names each club's coach at the season's end; the coach
at the start is the one a mid-season change replaced (Port Adelaide: Mark
Williams, until round 15).

Captains: the "Captain(s)" column. The second column mixes vice-captains and
leadership groups, so a name marked (vc) is vice-captain, (deputy vc) deputy
vice-captain; an unmarked cell of one or two names is the club's vice-
captains; an unmarked cell of three or more is its leadership group.

Coach skills come from tools/legacy_1990s/rate_coaches.py (record and rate,
director 2026-11-13 "Rate from records"), counting senior seasons before 2010.

Writes data/legacy/2010/coaches_2010.csv, coach_ratings_2010.csv and
captains_2010.csv.

    python tools/legacy_2010s/build_leaders.py            # fetch what is missing
    python tools/legacy_2010s/build_leaders.py --offline  # cache only
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "legacy_1990s"))
import rate_coaches as RC  # noqa: E402

YEAR = 2010
OUT = os.path.join(ROOT, "data", "legacy", "2010")
CACHE = os.path.join(ROOT, "data", "cache", "legacy_2010s")
PAGE = "2010_AFL_season"
WIKI = "https://en.wikipedia.org/wiki/"
CHECKED = "2026-11-13"
CLUB = {"Adelaide": "ADE", "Brisbane Lions": "BRL", "Carlton": "CAR", "Collingwood": "COL", "Essendon": "ESS",
        "Fremantle": "FRE", "Geelong": "GEE", "Hawthorn": "HAW", "Melbourne": "MEL", "North Melbourne": "NTH",
        "Port Adelaide": "PAD", "Richmond": "RIC", "St Kilda": "STK", "Sydney": "SYD", "West Coast": "WCE",
        "Western Bulldogs": "WBD"}


def text(fragment):
    import html
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def page(offline):
    path = os.path.join(CACHE, PAGE + ".html")
    if not os.path.exists(path) and not offline:
        os.makedirs(CACHE, exist_ok=True)
        req = urllib.request.Request(WIKI + PAGE, headers={"User-Agent": "legacy-data-builder"})
        with urllib.request.urlopen(req, timeout=30) as r:
            open(path, "wb").write(r.read())
        time.sleep(1.0)
    body = open(path, encoding="utf-8").read()
    return re.sub(r"<style.*?</style>|<script.*?</script>", "", body, flags=re.S)


def table(body, anchor):
    i = body.find('id="%s"' % anchor)
    seg = re.search(r"<table.*?</table>", body[i:], re.S) if i >= 0 else None
    rows = []
    for tr in re.split(r"<tr[^>]*>", seg.group(0) if seg else "")[1:]:
        cells = [re.sub(r"\s*\[ ?\d+ ?\]", "", text(c)).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        rows.append(cells)
    return rows[1:]


def names(cell):
    """'A , B (vc), C and D' -> [(name, mark)]."""
    cell = re.sub(r",?\s*Jr\.?", "", cell)
    out = []
    for part in re.split(r"\s*,\s*|\s+and\s+", cell):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"(.*?)\s*\(([^)]*)\)$", part)
        out.append((m.group(1).strip(), m.group(2).strip()) if m else (part, ""))
    return out


# A leader the lists (Draftguru) carry under a later name.
LIST_NAME = {"Harry O'Brien": ("Heritier", "Lumumba", "Harry O'Brien in 2010; the lists use his later name")}


def split_name(full):
    full = re.sub(r",?\s*Jr\.?$", "", full).strip()
    first, _, last = full.partition(" ")
    return first, last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    body = page(a.offline)
    src = WIKI + PAGE
    # The coach a mid-season change replaced held the job when the season began.
    replaced = {}
    for cells in table(body, "Coach_changes"):
        if len(cells) >= 4 and cells[1] in CLUB and re.search(r"\d{4}", cells[2]) and "July" in cells[2]:
            replaced[CLUB[cells[1]]] = (cells[0], cells[3], cells[4] if len(cells) > 4 else "")
    coaches, captains = [], []
    for cells in table(body, "Club_leadership"):
        if len(cells) < 3 or cells[0] not in CLUB:
            continue
        club = CLUB[cells[0]]
        coach, note = cells[1], ""
        if club in replaced and replaced[club][1] == coach:
            coach, note = replaced[club][0], "Coached from the start of 2010; %s took over mid-season (%s)" % (
                replaced[club][1], replaced[club][2])
        coaches.append({"club": club, "role": "senior", "name": coach, "note": note,
                        "source_url": src + "#Club_leadership", "checked": CHECKED})
        for name, _ in names(cells[2]):
            f, l = split_name(name)
            captains.append({"club": club, "role": "captain", "first": f, "last": l, "note": "",
                             "source_url": src + "#Club_leadership", "checked": CHECKED})
        second = names(cells[3]) if len(cells) > 3 else []
        marked = any(m for _, m in second)
        for name, mark in second:
            if mark == "vc":
                role = "vice_captain"
            elif mark == "deputy vc":
                role = "deputy_vice_captain"
            elif not marked and len(second) <= 2:
                role = "vice_captain"
            else:
                role = "group"
            f, l = split_name(name)
            note = ""
            if name in LIST_NAME:
                f, l, note = LIST_NAME[name]
            captains.append({"club": club, "role": role, "first": f, "last": l, "note": note,
                             "source_url": src + "#Club_leadership", "checked": CHECKED})
    os.makedirs(OUT, exist_ok=True)
    write("coaches_2010.csv", ["club", "role", "name", "note", "source_url", "checked"], coaches)
    write("captains_2010.csv", ["club", "role", "first", "last", "note", "source_url", "checked"], captains)

    # Each coach rated from his senior record before 2010.
    RC.BEFORE = YEAR
    # AFL Tables' page for Port Adelaide's Mark Williams (the first is another man).
    RC.PAGE_NAME.update({"Mark Williams": "Mark_Williams2"})
    rated = []
    for c in coaches:
        rec = RC.record(RC.page_for(c["name"], a.offline))
        sk = RC.rate(c["role"], rec)
        stem = RC.PAGE_NAME.get(c["name"], c["name"].replace(" ", "_"))
        rated.append({"name": c["name"], "role": c["role"], **rec, **sk,
                      "source_url": RC.URL % stem if rec["seasons"] else ""})
    write("coach_ratings_%d.csv" % YEAR, list(rated[0].keys()), rated)
    print("coaches %d, captains %d" % (len(coaches), len(captains)))
    for r in rated:
        print("  %-20s %2d seasons %3d games %d flags  teach %d tactics %d manage %d" % (
            r["name"], r["seasons"], r["games"], r["flags"], r["teach"], r["tactics"], r["manage"]))


def write(name, cols, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
