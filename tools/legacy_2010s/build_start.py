#!/usr/bin/env python3
"""
Build the 2010 start's rated lists (Legacy mode, TODO row 142: "then the 2000,
2010 and 2020 starts").

The same pipeline as the 1990 start (tools/legacy_1990s/build_start.py, whose
rating code this imports unchanged): every season 1987-2025 is rated against
its own season's players, each position scaled on its own season, and the
2010 lists are rated on 2009, the season just played.

Inputs (all in data/legacy/, already gathered; nothing is fetched):
  2010s/lists.csv            every club's 2010 list (Draftguru). No 2010
                             player joined during the season (no mid-season
                             draft that year), so the 2010 rows are the
                             opening lists.
  <decade>s/season_stats.csv AFL Tables season totals, 1987-2025: the ratings,
                             each player's career before 2010 (club stints),
                             and his peak
  lists.csv first_drafted    draft pedigree ("#17 Rookie 2009")

Outputs (data/legacy/2010/):
  players_2010.csv, history_2010.csv, list_additions_2010.csv,
  list_addition_stats_2010.csv   (the 1990 start's schemas)

    python3 tools/legacy_2010s/build_start.py            # write the files
    python3 tools/legacy_2010s/build_start.py --report   # also the 2010 era report
Stdlib only.
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
OUT_DIR = os.path.join(LEG, "2010")
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "legacy_1990s"))
import build_start as B  # noqa: E402  (the 1990 builder: one rating model for every start)
import sim_harness as H  # noqa: E402

START = 2010
DATA_SEASON = 2009
START_DATE = "2010-03-01"
# Seasons kept in a player's history (the game reads the last three).
HISTORY_YEARS = (2007, 2008, 2009)
DRAFT_TYPE = {"National": "national", "Pre-Season": "preseason", "Rookie": "rookie"}


def norm(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())


def age_at(dob):
    if not dob:
        return ""
    y, m, d = (int(x) for x in dob.split("-"))
    sy, sm, sd = (int(x) for x in START_DATE.split("-"))
    return str(sy - y - ((sm, sd) < (m, d)))


def first_drafted(cell):
    """('national', '58', '2004') from '#58 National 2004'; blanks otherwise
    (a foundation, father-son or zone signing has no pick in the game's sense)."""
    m = re.match(r"#(\d+)\s+(\S+)\s+(\d{4})", cell or "")
    if not m or m.group(2) not in DRAFT_TYPE:
        return "", "", ""
    return DRAFT_TYPE[m.group(2)], m.group(1), m.group(3)


def load_lists():
    with open(os.path.join(LEG, "2010s", "lists.csv"), newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if int(r["year"]) == START]
    # A player with no 2010 number takes a free one from 60 up: the game keys a
    # player on club + number.
    used = defaultdict(set)
    for r in rows:
        if r["num"]:
            used[r["club"]].add(int(r["num"]))
    for r in rows:
        if not r["num"]:
            n = 60
            while n in used[r["club"]]:
                n += 1
            used[r["club"]].add(n)
            r["num"] = str(n)
    return rows


def match_ids(lists, by_year):
    """AFL Tables id for every 2010 list row: the lists build's own match for
    anyone who played in 2010, else the same first name and surname in the
    2005-09 stats, narrowed to his 2010 club or the club he came from when the
    name is not unique. Unmatched means no game before 2010."""
    names = defaultdict(set)
    club_of = defaultdict(set)
    for y in range(2005, START):
        for r in by_year[y]:
            k = (norm(r["first"]), norm(r["last"]))
            names[k].add(r["afltables_id"])
            club_of[r["afltables_id"]].add(B.code(r["club"]))
    for r in lists:
        if r["afltables_id"]:
            continue
        cand = names.get((norm(r["first"]), norm(r["last"])), set())
        if len(cand) > 1:
            cand = {c for c in cand if r["club"] in club_of[c] or r["joined_from"] in club_of[c]}
        if len(cand) == 1:
            r["afltables_id"] = next(iter(cand))


def careers(by_year):
    """{afltables_id: [{year, club, games, goals}]} for every season before 2010."""
    out = defaultdict(list)
    for y in by_year:
        if y >= START:
            continue
        for r in by_year[y]:
            out[r["afltables_id"]].append({"year": y, "club": r["club"], "games": r["gm"], "goals": r["gl"]})
    return out


def build(by_year, rated):
    lists = load_lists()
    match_ids(lists, by_year)
    before = careers(by_year)
    players, history, additions, add_stats = [], [], [], []
    for L in lists:
        club, pid = L["club"], L["afltables_id"]
        data = rated.get(DATA_SEASON, {}).get(pid) if pid else None
        seasons = []
        for y in HISTORY_YEARS:
            got = rated.get(y, {}).get(pid) if pid else None
            if got and got[1] >= B.PEAK_GAMES:
                seasons.append("%d:%d:%d" % (y, got[0], got[1]))
        # Informed potential (director 2026-11-11): his best real season from
        # the data season on sets his ceiling.
        peak = 0
        for y in rated:
            if y >= DATA_SEASON and pid:
                got = rated[y].get(pid)
                if got and got[1] >= B.PEAK_GAMES:
                    peak = max(peak, got[0])
        first_year = min((r["year"] for r in before.get(pid, [])), default=None)
        debut = "01-04-%d" % first_year if first_year else ""
        dtype, dpick, dyear = first_drafted(L["first_drafted"])
        if data and data[1] > 0:
            cells = B.stat_cells(data[2])
            players.append(dict(cells, club=club, num=L["num"], last=L["last"], first=L["first"],
                                src=str(DATA_SEASON), real_pos="", dob=L["dob"], age=age_at(L["dob"]),
                                height_cm=L["height_cm"], weight_kg=L["weight_kg"], debut=debut,
                                height_source="draftguru" if L["height_cm"] else ""))
            history.append({"club": club, "num": L["num"],
                            "slug": pid.rsplit("/", 1)[-1].replace(".html", ""),
                            "draft_year": dyear, "draft_type": dtype, "draft_pick": dpick,
                            "seasons": ";".join(seasons), "career": B.stints(before.get(pid, [])),
                            "peak": peak or ""})
        else:
            additions.append({"first": L["first"], "last": L["last"], "dob": L["dob"], "club": club,
                              "position": "", "height_cm": L["height_cm"], "list": L["list"],
                              "peak": peak or "", "source_url": L["source_url"], "checked": L["checked"]})
            latest = None
            for y in (2008, 2007):
                got = rated.get(y, {}).get(pid) if pid else None
                if got and got[1] > 0:
                    latest = (y, got)
                    break
            if latest:
                cells = B.stat_cells(latest[1][2])
                add_stats.append(dict(cells, club=club, num="0", last=L["last"], first=L["first"],
                                      src=str(latest[0])))
    return players, history, additions, add_stats


# ------------------------------------------------------------- era report --
def harness_from_enriched(rows):
    hp = []
    for r in rows:
        e = {("one_pct" if k == "onepct" else "pct_played" if k == "pctp" else k): float(r[k] or 0)
             for k in B.ENRICHED[4:28]}
        hp.append(B.harness_player({**e, "first": r["first"], "last": r["last"]}, r["club"], r["num"]))
    H.ERA_ANCHORS.clear()
    H.derive_ratings(hp)
    H.fit_era_anchors(hp)
    return hp


def spread(hp):
    by_club = defaultdict(list)
    for p in hp:
        by_club[p["club"]].append(p["overall"])
    allv = sorted(p["overall"] for p in hp)
    meds = {c: sorted(v)[len(v) // 2] for c, v in by_club.items()}
    return by_club, allv, meds


def era_report(by_year, rated, players):
    stats = ["di", "ki", "hb", "mk", "tk", "gl", "cl", "cp", "if50", "rb"]
    lines = ["# The 2010 start against today (Legacy mode, row 142)", "",
             "Built by `tools/legacy_2010s/build_start.py --report`, on the rating model of the 1990 start "
             "(each season rated against its own players, each position scaled on its own season; director "
             "2026-11-10 'A: per era', 2026-11-13 'Scale each position per season').", "",
             "## Stat averages, per player per game", "",
             "Every player with a game that season. The 2026 base is the 2020-25 seasons (2026 is not in the "
             "AFL Tables files); the game's own 2026 lists are rated on 2026.", "",
             "| Seasons | " + " | ".join(stats) + " | rated 80+ per season | median OVR (8+ games) |",
             "|" + "---|" * (len(stats) + 3)]
    rows = {}
    for label, years in (("2009 (the data season)", range(2009, 2010)), ("2010-19", range(2010, 2020)),
                         ("2020-25 (base)", range(2020, 2026))):
        tot, gm, n80, ovrs = defaultdict(float), 0.0, 0, []
        for y in years:
            for _pid, (ovr, g, e, _role) in rated[y].items():
                gm += g
                for k in stats:
                    tot[k] += e[k]
                if g >= B.PEAK_GAMES:
                    ovrs.append(ovr)
                    n80 += ovr >= 80
        ovrs.sort()
        rows[label] = {k: tot[k] / gm for k in stats}
        lines.append("| %s | %s | %.1f | %d |" % (label, " | ".join("%.1f" % rows[label][k] for k in stats),
                                                  n80 / len(list(years)), ovrs[len(ovrs) // 2]))
    base, d09 = rows["2020-25 (base)"], rows["2009 (the data season)"]
    lines.append("| 2009 vs base | %s | | |" % " | ".join("%+.0f%%" % (100 * (d09[k] / base[k] - 1)) for k in stats))

    hp10 = harness_from_enriched(players)
    with open(os.path.join(ROOT, "data", "players_enriched_2026.csv"), newline="", encoding="utf-8") as fh:
        today = list(csv.DictReader(fh))
    hp26 = harness_from_enriched(today)
    c10, a10, m10 = spread(hp10)
    c26, a26, m26 = spread(hp26)

    def pct(v, q):
        return v[min(len(v) - 1, int(q * len(v)))]

    lines += ["", "## The 2010 lists as the game loads them, against today's", "",
              "Both rated by `tools/sim_harness.py` (the game rates again at load, the same model): the 2010 "
              "lists on 2009, today's on 2026. Players with a game in the data season.", "",
              "| Lists | players | rated 80+ | 80+ per club | 70+ | median | 90th pct | best | club medians |",
              "|---|---|---|---|---|---|---|---|---|"]
    for label, v, c, m in (("2010 (on 2009)", a10, c10, m10), ("2026 (on 2026)", a26, c26, m26)):
        meds = sorted(m.values())
        lines.append("| %s | %d | %d | %.1f | %d | %d | %d | %d | %d-%d |" % (
            label, len(v), sum(x >= 80 for x in v), sum(x >= 80 for x in v) / len(c),
            sum(x >= 70 for x in v), pct(v, 0.5), pct(v, 0.9), v[-1], meds[0], meds[-1]))
    lines += ["", "| Club | players | median OVR | best | 80+ |", "|---|---|---|---|---|"]
    for c in sorted(c10):
        v = sorted(c10[c])
        lines.append("| %s | %d | %d | %d | %d |" % (c, len(v), v[len(v) // 2], v[-1], sum(x >= 80 for x in v)))
    top = sorted(hp10, key=lambda p: -p["overall"])[:15]
    lines += ["", "Top 15 in 2010: " + ", ".join("%s (%s) %d" % (p["name"], p["club"], p["overall"]) for p in top)]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    by_year = B.load_seasons()
    model = B.fit_model(by_year)
    rated = B.rate_seasons(by_year, model)
    players, history, additions, add_stats = build(by_year, rated)
    os.makedirs(OUT_DIR, exist_ok=True)
    B.write(os.path.join(OUT_DIR, "players_2010.csv"), B.ENRICHED, players)
    B.write(os.path.join(OUT_DIR, "history_2010.csv"),
            ["club", "num", "slug", "draft_year", "draft_type", "draft_pick", "seasons", "career", "peak"], history)
    B.write(os.path.join(OUT_DIR, "list_additions_2010.csv"),
            ["first", "last", "dob", "club", "position", "height_cm", "list", "peak", "source_url", "checked"],
            additions)
    B.write(os.path.join(OUT_DIR, "list_addition_stats_2010.csv"), B.ADD_STATS, add_stats)
    print("players %d, additions %d (%d with an earlier season)" % (len(players), len(additions), len(add_stats)))
    if a.report:
        path = os.path.join(ROOT, "docs", "research", "LEGACY_ERA_REPORT_2010.md")
        with open(path, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(era_report(by_year, rated, players))
        print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
