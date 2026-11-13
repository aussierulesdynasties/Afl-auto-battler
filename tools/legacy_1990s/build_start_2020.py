#!/usr/bin/env python3
"""
Build the 2020 start's rated lists, coaches and captains (Legacy mode, TODO
row 142: "then the 2000, 2010 and 2020 starts").

The same pipeline as the 1990 start (build_start.py, imported, not changed):
every season 1987-2025 rated against its own players, each position scaled on
its own season. The 2020 lists are rated on 2019, the season just played.

Inputs (data/legacy/, gathered 2026-11-11 by tools/legacy_2020s):
  2020s/lists.csv            every club's 2020 list (Draftguru: everyone listed
                             during 2020; no mid-season draft was held in 2020,
                             so nothing comes off)
  <decade>s/season_stats.csv AFL Tables season totals 1987-2025: the 2019 data
                             season, 2017-19 for the rated seasons, every
                             season before 2020 for career stints, 2019-25 for
                             the peak (the director's "Informed" potential)
  <decade>s/drafts.csv       draft pedigree
  Wikipedia's 2020 AFL season page (cached by tools/legacy_2020s/fetch.py):
                             the "Club leadership" table, coaches and captains

Outputs:
  data/legacy/2020/players_2020.csv, history_2020.csv, list_additions_2020.csv,
  list_addition_stats_2020.csv, list_types_2020.csv
  data/legacy/2020s/coaches_2020.csv, captains_2020.csv

    python3 tools/legacy_1990s/build_start_2020.py [--cache DIR] [--report]
Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_start as B  # noqa: E402

ROOT, LEG, H = B.ROOT, B.LEG, B.H
YEAR = 2020
DATA_SEASON = 2019
START_DATE = "2020-03-01"
OUT_DIR = os.path.join(LEG, "2020")
STAFF_DIR = os.path.join(LEG, "2020s")
CACHE = os.path.join(ROOT, "data", "cache", "legacy_2020s")
WIKI = "https://en.wikipedia.org/wiki/2020_AFL_season"
CHECKED = "2026-11-13"
CLUB = {"Adelaide": "ADE", "Brisbane Lions": "BRL", "Carlton": "CAR", "Collingwood": "COL",
        "Essendon": "ESS", "Fremantle": "FRE", "Geelong": "GEE", "Gold Coast": "GCS",
        "Greater Western Sydney": "GWS", "Hawthorn": "HAW", "Melbourne": "MEL",
        "North Melbourne": "NTH", "Port Adelaide": "PAD", "Richmond": "RIC", "St Kilda": "STK",
        "Sydney": "SYD", "West Coast": "WCE", "Western Bulldogs": "WBD"}
# The drafts files' kinds, as the game names them (player_history_2026.csv);
# the 2011 mini-draft of 17-year-olds for Gold Coast and GWS counts as national.
DRAFT_KINDS = {"national": "national", "mini": "national", "preseason": "preseason",
               "pre_season": "preseason", "mid_season": "midseason", "rookie": "rookie"}


def norm(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())


def load_list():
    with open(os.path.join(LEG, "2020s", "lists.csv"), newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if int(r["year"]) == YEAR]
    # A player with no number takes a free one from 60 up: the game keys a
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


def fill_ids(lists, by_year):
    """Draftguru leaves some players' AFL Tables link blank (Charlie Curnow,
    Allen Christensen). Match them to AFL Tables' season rows by name: the
    full name, else surname and the first three letters of the first name,
    kept only when one AFL Tables player fits, preferring one who played for
    the club in 2019 or 2020."""
    seen = defaultdict(set)   # (key) -> {afltables_id}
    clubs = defaultdict(set)  # afltables_id -> clubs 2019-20
    for y, rows in by_year.items():
        for r in rows:
            aid = r["afltables_id"]
            seen[("full", norm(r["first"]), norm(r["last"]))].add(aid)
            seen[("short", norm(r["first"])[:3], norm(r["last"]))].add(aid)
            if y in (DATA_SEASON, YEAR):
                clubs[aid].add(B.code(r["club"]))
    taken = {L["afltables_id"] for L in lists if L["afltables_id"]}
    filled = 0
    for L in lists:
        if L["afltables_id"]:
            continue
        for key in (("full", norm(L["first"]), norm(L["last"])), ("short", norm(L["first"])[:3], norm(L["last"]))):
            got = seen.get(key, set()) - taken
            at_club = {a for a in got if L["club"] in clubs[a]}
            pick = at_club if at_club else got
            if len(pick) == 1:
                L["afltables_id"] = pick.pop()
                taken.add(L["afltables_id"])
                filled += 1
                break
    return filled


def load_drafts():
    """Each player's first draft as the game reads it (national, pre-season,
    mid-season or rookie, with a pick), keyed by Draftguru id."""
    rows = []
    for dec in ("1990s", "2000s", "2010s", "2020s"):
        with open(os.path.join(LEG, dec, "drafts.csv"), newline="", encoding="utf-8") as fh:
            rows += list(csv.DictReader(fh))
    out = {}
    for r in sorted(rows, key=lambda r: int(r["year"])):
        if r["draft"] in DRAFT_KINDS and r["pick"] and r["draftguru_id"]:
            out.setdefault(r["draftguru_id"], r)
    return out


def careers_before(by_year):
    """{afltables_id: [{club, year, games, goals}]}, every season before 2020."""
    out = defaultdict(list)
    for y, rows in by_year.items():
        if y < YEAR:
            for r in rows:
                out[r["afltables_id"]].append({"club": r["club"], "year": y, "games": r["gm"], "goals": r["gl"]})
    return out


def age_at(dob):
    if not dob:
        return ""
    y, m, d = (int(x) for x in dob.split("-"))
    sy, sm, sd = (int(x) for x in START_DATE.split("-"))
    return str(sy - y - ((sm, sd) < (m, d)))


def draft_type(d):
    if not d:
        return ""
    return DRAFT_KINDS[d["draft"]]


def build(by_year, rated, lists):
    careers = careers_before(by_year)
    drafts = load_drafts()
    players, history, additions, add_stats, list_types = [], [], [], [], []
    for L in lists:
        club, pid = L["club"], L["afltables_id"]
        row_ds = rated.get(DATA_SEASON, {}).get(pid) if pid else None
        seasons = []
        for y in (DATA_SEASON - 2, DATA_SEASON - 1, DATA_SEASON):
            got = rated.get(y, {}).get(pid) if pid else None
            if got and got[1] >= B.PEAK_GAMES:
                seasons.append("%d:%d:%d" % (y, got[0], got[1]))
        peak = 0
        for y in rated:
            if y >= DATA_SEASON and pid:
                got = rated[y].get(pid)
                if got and got[1] >= B.PEAK_GAMES:
                    peak = max(peak, got[0])
        first_year = min((int(r["year"]) for r in careers.get(pid, [])), default=None)
        debut = "01-04-%d" % first_year if first_year else ""
        d = drafts.get(L["draftguru_id"]) if L["draftguru_id"] else None
        if row_ds and row_ds[1] > 0:
            cells = B.stat_cells(row_ds[2])
            players.append(dict(cells, club=club, num=L["num"], last=L["last"], first=L["first"],
                                src=str(DATA_SEASON), real_pos=L.get("position", ""), dob=L["dob"],
                                age=age_at(L["dob"]), height_cm=L["height_cm"], weight_kg=L["weight_kg"],
                                debut=debut, height_source="draftguru" if L["height_cm"] else ""))
            history.append({"club": club, "num": L["num"],
                            "slug": pid.rsplit("/", 1)[-1].replace(".html", ""),
                            "draft_year": d["year"] if d else "", "draft_type": draft_type(d),
                            "draft_pick": d["pick"] if d else "", "seasons": ";".join(seasons),
                            "career": B.stints(careers.get(pid, [])), "peak": peak or ""})
            if L["list"] in ("rookie", "cat_b"):
                list_types.append({"club": club, "first": L["first"], "last": L["last"], "dob": L["dob"],
                                   "list": L["list"], "source_url": L["source_url"].split(" | ")[0],
                                   "checked": L["checked"]})
        else:
            additions.append({"first": L["first"], "last": L["last"], "dob": L["dob"], "club": club,
                              "position": L.get("position", ""), "height_cm": L["height_cm"], "list": L["list"],
                              "peak": peak or "", "source_url": L["source_url"], "checked": L["checked"]})
            latest = None
            for y in range(DATA_SEASON - 1, DATA_SEASON - 4, -1):
                got = rated.get(y, {}).get(pid) if pid else None
                if got and got[1] > 0:
                    latest = (y, got)
                    break
            if latest:
                cells = B.stat_cells(latest[1][2])
                add_stats.append(dict(cells, club=club, num="0", last=L["last"], first=L["first"],
                                      src=str(latest[0])))
    return players, history, additions, add_stats, list_types


# ------------------------------------------------------- coaches, captains --
def leadership_table(cache):
    """[(club, coach cell html, captain cell html, vice cell html, group cell html)]."""
    path = os.path.join(cache, "en.wikipedia.org_wiki_2020_AFL_season.html")
    with open(path, encoding="utf-8") as fh:
        body = fh.read()
    i = body.find('id="Club_leadership"')
    seg = re.search(r"<table.*?</table>", body[i:], re.S).group(0)
    out = []
    for tr in re.split(r"<tr[^>]*>", seg)[1:]:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)
        if len(cells) < 5:
            continue
        name = B_text(cells[0])
        if name in CLUB:
            out.append((CLUB[name], cells[1], cells[2], cells[3], cells[4]))
    if len(out) != 18:
        raise SystemExit("2020 Club leadership table: want 18 clubs, have %d" % len(out))
    return out


def B_text(fragment):
    import html
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def names_in(cell):
    """Each linked person in a cell. Wikipedia runs co-captains together
    ("Patrick Cripps Sam Docherty"), so names come from the links, not the text."""
    import html
    got = [B_text(a) for a in re.findall(r"<a [^>]*>(.*?)</a>", cell, re.S)]
    return [html.unescape(g) for g in got if g and not g.startswith("[")]


def build_staff(cache, lists):
    coaches, captains = [], []
    for club, coach, caps, vices, group in leadership_table(cache):
        for n in names_in(coach):
            coaches.append({"club": club, "role": "senior", "name": n, "note": "",
                            "source_url": WIKI + "#Club_leadership", "checked": CHECKED})
        for role, cell in (("captain", caps), ("vice_captain", vices), ("group", group)):
            for n in names_in(cell):
                first, _, last = n.partition(" ")
                on = [L for L in lists if L["club"] == club and norm(L["last"]) == norm(last)
                      and norm(L["first"])[:3] == norm(first)[:3]]
                if len(on) != 1:
                    raise SystemExit("captains_2020: %s %s is not once on %s's 2020 list" % (club, n, club))
                captains.append({"club": club, "role": role, "first": on[0]["first"], "last": on[0]["last"],
                                 "draftguru_id": on[0]["draftguru_id"],
                                 "source_url": WIKI + "#Club_leadership", "checked": CHECKED})
    return coaches, captains


# ------------------------------------------------------------- era report --
def rate_file(path):
    hp = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            e = {("one_pct" if k == "onepct" else "pct_played" if k == "pctp" else k): float(r[k] or 0)
                 for k in B.ENRICHED[4:28]}
            hp.append(B.harness_player({**e, "first": r["first"], "last": r["last"]}, r["club"], r["num"]))
    return hp


def shape(hp, fit):
    H.ERA_ANCHORS.clear()
    H.derive_ratings(hp)
    if fit:
        H.fit_era_anchors(hp)
    by_club = defaultdict(list)
    for p in hp:
        by_club[p["club"]].append(p["overall"])
    allv = sorted(p["overall"] for p in hp)
    return by_club, allv


def era_report(by_year, rated):
    stats = ["di", "ki", "hb", "mk", "tk", "gl", "cl", "cp", "if50", "rb"]
    lines = ["# The 2020 start against today (Legacy mode, row 142)", "",
             "Built by `tools/legacy_1990s/build_start_2020.py --report`. Per player per game, every player "
             "with a game. 2020's matches were 80% of the usual length (16-minute quarters), so its "
             "per-game counts sit about a fifth under the seasons either side.", "",
             "| Seasons | " + " | ".join(stats) + " |", "|" + "---|" * (len(stats) + 1)]
    for label, years in (("2010-19", range(2010, 2020)), ("2019 (rated on)", [2019]), ("2020", [2020]),
                         ("2021-25", range(2021, 2026)), ("2026 base", [2026])):
        tot, gm = defaultdict(float), 0.0
        if years == [2026]:
            src = rate_file(os.path.join(ROOT, "data", "players_enriched_2026.csv"))
            for p in src:
                gm += p["gm"]
                for k in stats:
                    tot[k] += p[k]
        else:
            for y in years:
                for pid, (ovr, g, e, _r) in rated[y].items():
                    gm += g
                    for k in stats:
                        tot[k] += e[k]
        lines.append("| %s | %s |" % (label, " | ".join("%.1f" % (tot[k] / gm) for k in stats)))

    c20, a20 = shape(rate_file(os.path.join(OUT_DIR, "players_%d.csv" % YEAR)), True)
    c26, a26 = shape(rate_file(os.path.join(ROOT, "data", "players_enriched_2026.csv")), False)

    def summ(allv):
        n = len(allv)
        return (n, sum(v >= 80 for v in allv), sum(v >= 85 for v in allv), sum(v >= 90 for v in allv),
                allv[n // 2], allv[int(n * 0.9)], allv[-1])

    lines += ["", "## Rating spread: the 2020 lists (rated on 2019) against 2026", "",
              "Players who played the data season, as the game rates them at load "
              "(2020: each position scaled on 2019; 2026: the game's own anchors).", "",
              "| Start | players | 80+ | 85+ | 90+ | median | 90th pct | best |", "|---|---|---|---|---|---|---|---|"]
    for label, allv in (("2020", a20), ("2026", a26)):
        lines.append("| %s | %d | %d | %d | %d | %d | %d | %d |" % ((label,) + summ(allv)))
    lines += ["", "| Club | 2020 median | 2020 80+ | 2026 median | 2026 80+ |", "|---|---|---|---|---|"]
    for c in sorted(set(c20) | set(c26)):
        v20, v26 = sorted(c20.get(c, [])), sorted(c26.get(c, []))
        lines.append("| %s | %s | %s | %s | %s |" % (
            c, v20[len(v20) // 2] if v20 else "-", sum(x >= 80 for x in v20) if v20 else "-",
            v26[len(v26) // 2] if v26 else "-", sum(x >= 80 for x in v26) if v26 else "-"))
    hp20 = rate_file(os.path.join(OUT_DIR, "players_%d.csv" % YEAR))
    shape(hp20, True)
    top = sorted(hp20, key=lambda p: -p["overall"])[:15]
    lines += ["", "Top 15 in 2020: " + ", ".join("%s (%s) %d" % (p["name"], p["club"], p["overall"]) for p in top)]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------- real last seasons --
def last_seasons(by_year, lists):
    """Each 2020 listed player's real last AFL season, for retirement around
    the real year (director 2026-11-13: "make all historical players
    retirement start roughly when it did irl"). The last season is the later
    of his last year on an AFL list (2020-25, by Draftguru id) and his last
    game (by AFL Tables id). Blank when he is on a 2026 list: he follows the
    normal sim."""
    listed = defaultdict(int)
    with open(os.path.join(LEG, "2020s", "lists.csv"), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["draftguru_id"]:
                listed[r["draftguru_id"]] = max(listed[r["draftguru_id"]], int(r["year"]))
    played = defaultdict(int)
    for y, rows in by_year.items():
        for r in rows:
            if r["afltables_id"] and r["gm"] not in ("", "0"):
                played[r["afltables_id"]] = max(played[r["afltables_id"]], y)
    on_2026 = set()
    for f in ("players_enriched_2026.csv", "list_additions_2026.csv"):
        with open(os.path.join(ROOT, "data", f), newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                on_2026.add((norm(r["first"]), norm(r["last"]), r["dob"]))
                on_2026.add(("", norm(r["last"]), r["dob"]))
    out = []
    for L in lists:
        active = ("", norm(L["last"]), L["dob"]) in on_2026 if L["dob"] else             (norm(L["first"]), norm(L["last"]), "") in on_2026
        last = max(listed.get(L["draftguru_id"], 0), played.get(L["afltables_id"], 0), YEAR)
        out.append({"club": L["club"], "num": L["num"], "first": L["first"], "last": L["last"], "dob": L["dob"],
                    "last_season": "" if active else last})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=CACHE, help="tools/legacy_2020s/fetch.py's cache (Wikipedia's 2020 season page)")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    by_year = B.load_seasons()
    model = B.fit_model(by_year)
    rated = B.rate_seasons(by_year, model)
    lists = load_list()
    print("AFL Tables ids matched by name: %d" % fill_ids(lists, by_year))
    players, history, additions, add_stats, list_types = build(by_year, rated, lists)
    os.makedirs(OUT_DIR, exist_ok=True)
    B.write(os.path.join(OUT_DIR, "players_2020.csv"), B.ENRICHED, players)
    B.write(os.path.join(OUT_DIR, "history_2020.csv"),
            ["club", "num", "slug", "draft_year", "draft_type", "draft_pick", "seasons", "career", "peak"], history)
    B.write(os.path.join(OUT_DIR, "list_additions_2020.csv"),
            ["first", "last", "dob", "club", "position", "height_cm", "list", "peak", "source_url", "checked"],
            additions)
    B.write(os.path.join(OUT_DIR, "list_addition_stats_2020.csv"), B.ADD_STATS, add_stats)
    B.write(os.path.join(OUT_DIR, "list_types_2020.csv"),
            ["club", "first", "last", "dob", "list", "source_url", "checked"], list_types)
    gone = last_seasons(by_year, lists)
    B.write(os.path.join(OUT_DIR, "last_seasons_2020.csv"), ["club", "num", "first", "last", "dob", "last_season"],
            gone)
    print("last seasons: %d still listed in 2026, %d retired by then"
          % (sum(1 for g in gone if g["last_season"] == ""), sum(1 for g in gone if g["last_season"] != "")))
    print("players %d, additions %d (%d with an earlier season), rookie/cat B who played %d"
          % (len(players), len(additions), len(add_stats), len(list_types)))
    coaches, captains = build_staff(a.cache, lists)
    B.write(os.path.join(STAFF_DIR, "coaches_2020.csv"), ["club", "role", "name", "note", "source_url", "checked"],
            coaches)
    B.write(os.path.join(STAFF_DIR, "captains_2020.csv"),
            ["club", "role", "first", "last", "draftguru_id", "source_url", "checked"], captains)
    print("coaches %d, leaders %d" % (len(coaches), len(captains)))
    if a.report:
        path = os.path.join(ROOT, "docs", "research", "LEGACY_ERA_REPORT_2020.md")
        with open(path, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(era_report(by_year, rated))
        print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
