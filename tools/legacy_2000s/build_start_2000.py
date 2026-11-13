#!/usr/bin/env python3
"""
Build the 2000 start's rated lists, coaches and captains (Legacy mode, TODO
row 142: "then the 2000, 2010 and 2020 starts").

The same pipeline as the 1990 start: this imports tools/legacy_1990s/
build_start.py (the per-era rating, the estimate of stats not yet recorded)
and changes only what is the year's own.

Inputs (data/legacy/, gathered 2026-11-11):
  2000s/lists.csv               every club's 2000 list (year 2000 rows)
  <decade>s/season_stats.csv    AFL Tables season totals, 1987-2025
  1990s/careers_before_1990.csv seasons before 1987 (season_stats starts there)
  1990s/drafts.csv, 2000s/drafts.csv  draft pedigree

Outputs:
  data/legacy/2000/players_2000.csv           the lists rated on 1999
  data/legacy/2000/history_2000.csv           rated 1997-99, career stints, draft, peak
  data/legacy/2000/list_additions_2000.csv    listed, no 1999 game
  data/legacy/2000/list_addition_stats_2000.csv  their latest season (1997-98)
  data/legacy/2000/list_types_2000.csv        rookie-listed players who played 1999 (none: no file)
  data/legacy/2000s/coaches_2000.csv          each club's 2000 senior coach (AFL Tables)
  data/legacy/2000s/captains_2000.csv         each club's 2000 captain(s) (Wikipedia)

    python3 tools/legacy_2000s/build_start_2000.py --cache data/cache/legacy_2000s
    python3 tools/legacy_2000s/build_start_2000.py --cache data/cache/legacy_2000s --report
The cache holds AFL Tables' club coach pages and Wikipedia's club captains
lists (tools/legacy_1990s/fetch.py get()). Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEG = os.path.join(ROOT, "data", "legacy")
sys.path.insert(0, os.path.join(ROOT, "tools", "legacy_1990s"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_start as BS  # noqa: E402
import build as B90  # noqa: E402
import sim_harness as H  # noqa: E402

YEAR = 2000
DATA_SEASON = 1999
START_DATE = "2000-03-01"
OUT_DIR = os.path.join(LEG, "2000")
STAFF_DIR = os.path.join(LEG, "2000s")
CHECKED = "2026-11-13"
code = BS.code

# AFL Tables' club coach pages (afltables.com/afl/stats/coaches/<page>.html).
COACH_PAGE = {"ADE": "adelaide", "BRL": "brisbanel", "CAR": "carlton", "COL": "collingwood",
              "ESS": "essendon", "FRE": "fremantle", "GEE": "geelong", "HAW": "hawthorn",
              "MEL": "melbourne", "NTH": "kangaroos", "PAD": "padelaide", "RIC": "richmond",
              "STK": "stkilda", "SYD": "swans", "WCE": "westcoast", "WBD": "bullldogs"}
WIKI = "https://en.wikipedia.org/wiki/"
CAPTAIN_PAGE = {"ADE": "List_of_Adelaide_Football_Club_captains",
                "BRL": "List_of_Brisbane_Lions_captains",
                "CAR": "List_of_Carlton_Football_Club_captains",
                "COL": "List_of_Collingwood_Football_Club_captains",
                "ESS": "List_of_Essendon_Football_Club_captains",
                "FRE": "List_of_Fremantle_Football_Club_captains",
                "GEE": "List_of_Geelong_Football_Club_captains",
                "HAW": "List_of_Hawthorn_Football_Club_captains",
                "MEL": "List_of_Melbourne_Football_Club_captains",
                "NTH": "List_of_North_Melbourne_Football_Club_captains",
                "PAD": "List_of_Port_Adelaide_Football_Club_captains",
                "RIC": "List_of_Richmond_Football_Club_captains",
                "STK": "List_of_St_Kilda_Football_Club_captains",
                "SYD": "List_of_Sydney_Swans_captains",
                "WCE": "List_of_West_Coast_Eagles_captains",
                "WBD": "List_of_Western_Bulldogs_captains"}
# Each club's 2000 captain(s), read off the page above (its captains table:
# the span that covers 2000). Brisbane and Fremantle had co-captains. Wikipedia
# names no 2000 vice-captains on these pages; none are invented.
CAPTAINS = {"ADE": ["Mark Bickley"], "BRL": ["Alastair Lynch", "Michael Voss"],
            "CAR": ["Craig Bradley"], "COL": ["Nathan Buckley"], "ESS": ["James Hird"],
            "FRE": ["Shaun McManus", "Adrian Fletcher"], "GEE": ["Ben Graham"],
            "HAW": ["Shane Crawford"], "MEL": ["David Neitz"], "NTH": ["Wayne Carey"],
            "PAD": ["Gavin Wanganeen"], "RIC": ["Matthew Knights"], "STK": ["Nathan Burke"],
            "SYD": ["Paul Kelly"], "WCE": ["Guy McKenna"], "WBD": ["Scott Wynd"]}
DRAFT_WORD = {"national": "national", "pre-season": "pre_season", "mid-season": "mid_season",
              "rookie": "rookie"}


def age_at(dob):
    if not dob:
        return ""
    y, m, d = (int(x) for x in dob.split("-"))
    sy, sm, sd = (int(x) for x in START_DATE.split("-"))
    return str(sy - y - ((sm, sd) < (m, d)))


def read_csv(*parts):
    with open(os.path.join(LEG, *parts), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def careers_before(by_year):
    """{afltables_id: [{year, club, games, goals}]}: pre-1987 from the 1990
    careers file, 1987-99 from the season totals."""
    out = defaultdict(list)
    for r in read_csv("1990s", "careers_before_1990.csv"):
        if int(r["year"]) < 1987:
            out[r["afltables_id"]].append(r)
    for y in range(1987, YEAR):
        for r in by_year[y]:
            out[r["afltables_id"]].append({"year": r["year"], "club": r["club"],
                                           "games": r["gm"], "goals": r["gl"]})
    return out


def draft_of(L, drafts):
    """(year, type, pick) from the draft files, else the list's first_drafted
    ("#12 Pre-Season 1999"); zone, foundation and concession joins stay blank."""
    d = drafts.get(L["draftguru_id"]) if L["draftguru_id"] else None
    if d:
        return d["year"], "national" if d["draft"] == "national" else d["draft"], d["pick"]
    m = re.match(r"#(\d+) (National|Pre-Season|Mid-Season|Rookie) (\d{4})", L.get("first_drafted", ""))
    if m:
        return m.group(3), DRAFT_WORD[m.group(2).lower()], m.group(1)
    return "", "", ""


LAST_LISTED = 2025  # the latest season the lists cover: still listed then = blank


def last_seasons():
    """Each player's last real season on an AFL list (director 2026-11-13: historical players
    retire "roughly when it did irl"), keyed by AFL Tables id, Draftguru id and name + dob."""
    out = {}
    for dec in ("1990s", "2000s", "2010s", "2020s"):
        for r in read_csv(dec, "lists.csv"):
            y = int(r["year"])
            for k in (r["afltables_id"], r["draftguru_id"], "%s|%s|%s" % (r["first"], r["last"], r["dob"])):
                if k and not k.endswith("||"):
                    out[k] = max(out.get(k, 0), y)
    return out


def last_of(L, last):
    y = max((last.get(k, 0) for k in (L["afltables_id"], L["draftguru_id"],
                                       "%s|%s|%s" % (L["first"], L["last"], L["dob"])) if k), default=0)
    return "" if y >= LAST_LISTED or y < YEAR else str(y)


def build(rated, by_year):
    lists = [r for r in read_csv("2000s", "lists.csv") if int(r["year"]) == YEAR]
    last = last_seasons()
    careers = careers_before(by_year)
    drafts = {}
    for dec in ("1990s", "2000s"):
        for r in read_csv(dec, "drafts.csv"):
            if r["draft"] in ("national", "pre_season", "mid_season") and r["pick"] and r["draftguru_id"]:
                drafts.setdefault(r["draftguru_id"], r)

    # The game keys a player on club + number: a missing or repeated number
    # takes a free one from 60 up.
    used = defaultdict(set)
    for L in lists:
        c = code(L["club"])
        if L["num"] and int(L["num"]) not in used[c]:
            used[c].add(int(L["num"]))
        else:
            L["num"] = ""
    for L in lists:
        if not L["num"]:
            c, n = code(L["club"]), 60
            while n in used[c]:
                n += 1
            used[c].add(n)
            L["num"] = str(n)

    players, history, additions, add_stats, list_types = [], [], [], [], []
    for L in lists:
        club, pid = code(L["club"]), L["afltables_id"]
        row = rated.get(DATA_SEASON, {}).get(pid) if pid else None
        seasons = []
        for y in (DATA_SEASON - 2, DATA_SEASON - 1, DATA_SEASON):
            got = rated.get(y, {}).get(pid) if pid else None
            if got and got[1] >= BS.PEAK_GAMES:
                seasons.append("%d:%d:%d" % (y, got[0], got[1]))
        peak = 0
        for y in rated:
            if y >= DATA_SEASON and pid:
                got = rated[y].get(pid)
                if got and got[1] >= BS.PEAK_GAMES:
                    peak = max(peak, got[0])
        car = careers.get(pid, [])
        first_year = min((int(r["year"]) for r in car), default=None)
        dy, dt, dp = draft_of(L, drafts)
        if row and row[1] > 0:
            players.append(dict(BS.stat_cells(row[2]), club=club, num=L["num"], last=L["last"],
                                first=L["first"], src=str(DATA_SEASON), real_pos="", dob=L["dob"],
                                age=age_at(L["dob"]), height_cm=L["height_cm"], weight_kg=L["weight_kg"],
                                debut="01-04-%d" % first_year if first_year else "",
                                height_source="draftguru" if L["height_cm"] else ""))
            history.append({"club": club, "num": L["num"],
                            "slug": pid.rsplit("/", 1)[-1].replace(".html", ""),
                            "draft_year": dy, "draft_type": dt, "draft_pick": dp,
                            "seasons": ";".join(seasons), "career": BS.stints(car), "peak": peak or "",
                            "last_season": last_of(L, last)})
            if L["list"] == "rookie":
                list_types.append({"club": club, "first": L["first"], "last": L["last"], "dob": L["dob"],
                                   "list": "rookie", "source_url": L["source_url"], "checked": L["checked"]})
        else:
            additions.append({"first": L["first"], "last": L["last"], "dob": L["dob"], "club": club,
                              "position": "", "height_cm": L["height_cm"], "list": L["list"],
                              "peak": peak or "", "last_season": last_of(L, last),
                              "source_url": L["source_url"], "checked": L["checked"]})
            for y in (DATA_SEASON - 1, DATA_SEASON - 2):
                got = rated.get(y, {}).get(pid) if pid else None
                if got and got[1] > 0:
                    add_stats.append(dict(BS.stat_cells(got[2]), club=club, num="0", last=L["last"],
                                          first=L["first"], src=str(y)))
                    break
    return lists, players, history, additions, add_stats, list_types


# ----------------------------------------------------------- coaches, captains --
def coaches(cache):
    B90.COACH_PAGE.update(COACH_PAGE)
    rows = []
    for c in sorted(COACH_PAGE):
        at = [(n, a, b) for n, a, b in B90.afltables_coaches(cache, c) if a <= YEAR <= b]
        if not at:
            raise SystemExit("no %d coach on AFL Tables for %s (is the cache fetched?)" % (YEAR, c))
        # The coach who started the season: the earliest span that covers it.
        name, a, b = min(at, key=lambda t: t[1])
        note = "AFL Tables: senior coach %d-%d" % (a, b)
        if len(at) > 1:
            note += "; also coached in %d: %s" % (YEAR, ", ".join("%s %d-%d" % t for t in at if t[0] != name))
        rows.append({"club": c, "role": "senior", "name": name, "note": note,
                     "source_url": "https://afltables.com/afl/stats/coaches/%s.html" % COACH_PAGE[c],
                     "checked": CHECKED})
    return rows


def captains(cache, lists):
    rows = []
    for c in sorted(CAPTAINS):
        page = B90.read(cache, WIKI + CAPTAIN_PAGE[c])
        for full in CAPTAINS[c]:
            first, last = full.split(" ", 1)
            if last not in page:
                raise SystemExit("%s is not on %s (is the cache fetched?)" % (full, CAPTAIN_PAGE[c]))
            on = [L for L in lists if code(L["club"]) == c and B90.norm(L["last"]) == B90.norm(last)
                  and B90.norm(L["first"])[:3] == B90.norm(first)[:3]]
            if len(on) != 1:
                raise SystemExit("%s is not on %s's %d list once" % (full, c, YEAR))
            # The list's spelling, which the game matches on.
            rows.append({"club": c, "role": "captain", "first": on[0]["first"], "last": on[0]["last"],
                         "draftguru_id": on[0]["draftguru_id"], "source_url": WIKI + CAPTAIN_PAGE[c],
                         "checked": CHECKED})
    return rows


# ------------------------------------------------------------- era report --
def era_report(players, by_year, rated):
    """The 2000 lists as the game loads them, beside the 2026 base."""
    def rate_rows(rows, era):
        hp = []
        for i, r in enumerate(rows):
            e = {}
            for k in BS.ENRICHED[4:28]:
                e["one_pct" if k == "onepct" else "pct_played" if k == "pctp" else k] = float(r[k] or 0)
            hp.append(BS.harness_player({**e, "first": r["first"], "last": r["last"]}, r["club"], r.get("num", i)))
        H.ERA_ANCHORS.clear()
        H.derive_ratings(hp)
        if era:
            H.fit_era_anchors(hp)
        return hp

    with open(os.path.join(ROOT, "data", "players_enriched_2026.csv"), newline="", encoding="utf-8") as fh:
        base = list(csv.DictReader(fh))
    out = {}
    for label, rows, era in (("2000 (rated on 1999)", players, True), ("2026 base", base, False)):
        hp = rate_rows(rows, era)
        by_club = defaultdict(list)
        for p in hp:
            by_club[p["club"]].append(p["overall"])
        allv = sorted(p["overall"] for p in hp)
        out[label] = (hp, by_club, allv)
    lines = ["# The 2000 start against the 2026 base (Legacy mode, row 142)", "",
             "Built by `tools/legacy_2000s/build_start_2000.py --report`. Ratings by `tools/sim_harness.py`, "
             "the Python mirror of Ratings.gd: 2000's lists on their 1999 season, each position scaled on its "
             "own season (director 2026-11-13, 'Scale each position per season'); the 2026 base as it ships. "
             "Decade stat averages are in `LEGACY_ERA_REPORT.md`.", "",
             "| Set | players | rated 80+ | 75+ | 70+ | median | 90th pct | best |", "|---|---|---|---|---|---|---|---|"]
    for label, (hp, by_club, v) in out.items():
        lines.append("| %s | %d | %d | %d | %d | %d | %d | %d |" % (
            label, len(v), sum(x >= 80 for x in v), sum(x >= 75 for x in v), sum(x >= 70 for x in v),
            v[len(v) // 2], v[int(len(v) * 0.9)], v[-1]))
    lines += ["", "## Each club's list median", "", "| Club | 2000 players | 2000 median | 2000 best | 2000 80+ "
              "| 2026 median | 2026 80+ |", "|---|---|---|---|---|---|---|"]
    a, b = out["2000 (rated on 1999)"][1], out["2026 base"][1]
    for c in sorted(a):
        v, w = sorted(a[c]), sorted(b.get(c, [0]))
        lines.append("| %s | %d | %d | %d | %d | %d | %d |" % (c, len(v), v[len(v) // 2], v[-1],
                                                              sum(x >= 80 for x in v), w[len(w) // 2],
                                                              sum(x >= 80 for x in w)))
    # The decades' per-game averages, the 1990 report's table (2020-25 is the 2026 base's era).
    decades = BS.era_report(by_year, rated, players).split("\n## ")[0].split("\n")
    lines += ["", "## Each decade's stats per player per game", ""] + [x for x in decades if x.startswith("|")]
    top = sorted(out["2000 (rated on 1999)"][0], key=lambda p: -p["overall"])[:15]
    lines += ["", "Top 15 in 2000: " + ", ".join("%s (%s) %d" % (p["name"], p["club"], p["overall"]) for p in top)]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    by_year = BS.load_seasons()
    model = BS.fit_model(by_year)
    rated = BS.rate_seasons(by_year, model)
    lists, players, history, additions, add_stats, list_types = build(rated, by_year)
    os.makedirs(OUT_DIR, exist_ok=True)
    BS.write(os.path.join(OUT_DIR, "players_2000.csv"), BS.ENRICHED, players)
    BS.write(os.path.join(OUT_DIR, "history_2000.csv"),
             ["club", "num", "slug", "draft_year", "draft_type", "draft_pick", "seasons", "career", "peak", "last_season"], history)
    BS.write(os.path.join(OUT_DIR, "list_additions_2000.csv"),
             ["first", "last", "dob", "club", "position", "height_cm", "list", "peak", "last_season", "source_url", "checked"],
             additions)
    BS.write(os.path.join(OUT_DIR, "list_addition_stats_2000.csv"), BS.ADD_STATS, add_stats)
    lt = os.path.join(OUT_DIR, "list_types_2000.csv")
    if list_types:
        BS.write(lt, ["club", "first", "last", "dob", "list", "source_url", "checked"], list_types)
    elif os.path.exists(lt):
        os.remove(lt)
    BS.write(os.path.join(STAFF_DIR, "coaches_2000.csv"), ["club", "role", "name", "note", "source_url", "checked"],
             coaches(a.cache))
    BS.write(os.path.join(STAFF_DIR, "captains_2000.csv"),
             ["club", "role", "first", "last", "draftguru_id", "source_url", "checked"], captains(a.cache, lists))
    print("players %d, additions %d (%d with an earlier season), rookies who played %d"
          % (len(players), len(additions), len(add_stats), len(list_types)))
    if a.report:
        path = os.path.join(ROOT, "docs", "research", "LEGACY_ERA_REPORT_2000.md")
        with open(path, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(era_report(players, by_year, rated))
        print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
