#!/usr/bin/env python3
"""
Build the 1990 start's rated lists (Legacy mode, TODO row 142, phase L1).

Inputs (all in data/legacy/, gathered by tools/legacy_<decade>s):
  1990s/lists_1990_opening.csv   every club's real list at the start of 1990
  <decade>s/season_stats.csv     AFL Tables season totals, 1987-2025
  1990s/careers_before_1990.csv  each player's seasons before 1990
  1990s/drafts.csv               draft pedigree (1989 on)
  honours/club_bf.csv            club best-and-fairests, 1987-2025 (Wikipedia)
  honours/all_australian.csv     All-Australian teams: 1987-88 carnivals, 1991 on
  honours/team_of_the_year.csv   the VFL/AFL Team of the Year 1989-90, which the
                                 AFL counts as All-Australian

Outputs (data/legacy/1990/):
  players_1990.csv          players_enriched schema: the opening lists rated on
                            their 1989 season (the data season)
  history_1990.csv          player_history schema: rated 1987-89 seasons,
                            career stints before 1990, draft pedigree, and
                            peak = his best real season from 1989 on (the
                            director's "Informed" potential, 2026-11-11), and
                            honours = his honours score (below)
  list_additions_1990.csv,  listed players with no 1989 game: their latest
  list_addition_stats_1990.csv  season, or none for a new player

Stats the game rates on but that AFL Tables did not record (before 1998: rb,
if50, cl, cg, cp, up, cm, mi, one_pct, bo, ga, pct_played; 1998: cp to
pct_played; 1999-2002: ga, pct_played) stay blank: never estimated (director
2026-11-15, "I never okayed invented stats"; an unrecorded stat counts for
nothing, Ratings.unrecorded). A season's stat counts as unrecorded when most
of its rows are blank; a blank in a recorded season is zero.

A player's position is his real one where a record gives it
(data/legacy/positions.csv, from his Wikipedia article: director 2026-11-15,
"Source real positions"); with none, the recorded stats read it.

Honours (director 2026-11-13, "Add honours"): the stats miss what made some
players great (Roos, Fitzroy's captain, rated 71), so each honour in the three
seasons before the start scores a point - a club best-and-fairest, an All-
Australian or Team of the Year pick, a Brownlow top 3 (4th-10th score half) -
weighted by how recent (the last season in full, then 0.75, 0.5). The game
lifts an honoured player's rating to a floor on that score (Ratings.HONOURS_*).

Every season is rated against its own season's players (tools/sim_harness.py
derive_ratings, the Python mirror of Ratings.gd), each position scaled on
its own season (fit_era_anchors), so ratings are per era (director
2026-11-10, "A: per era"; 2026-11-13, "Scale each position per season").

    python3 tools/legacy_1990s/build_start.py            # write the files
    python3 tools/legacy_1990s/build_start.py --report   # also the era report
Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEG = os.path.join(ROOT, "data", "legacy")
OUT_DIR = os.path.join(LEG, "1990")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import sim_harness as H  # noqa: E402

DATA_SEASON = 1989
START_DATE = "1990-03-01"
# The historical data's codes for clubs that are one club across eras
# (GameDB.CLUB_CODE_ALIASES).
CODE = {"BRB": "BRL", "FOO": "WBD"}
TARGETS = ["rb", "if50", "cl", "cg", "cp", "up", "cm", "mi", "one_pct", "bo", "ga"]
PEAK_GAMES = 8
HONOURS_W = {DATA_SEASON: 1.0, DATA_SEASON - 1: 0.75, DATA_SEASON - 2: 0.5}
HONOURS_FILES = ["club_bf.csv", "all_australian.csv", "team_of_the_year.csv"]
ENRICHED = ["club", "num", "last", "first", "gm", "ki", "mk", "hb", "di", "gl", "bh", "ho", "tk", "rb",
            "if50", "cl", "cg", "ff", "fa", "br", "cp", "up", "cm", "mi", "onepct", "bo", "ga", "pctp",
            "src", "real_pos", "dob", "age", "height_cm", "weight_kg", "debut", "height_source"]
ADD_STATS = ENRICHED[:29]


def code(c):
    return CODE.get(c, c)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- seasons --
def load_seasons():
    rows = []
    for dec in ("1990s", "2000s", "2010s", "2020s"):
        with open(os.path.join(LEG, dec, "season_stats.csv"), newline="", encoding="utf-8") as fh:
            rows += list(csv.DictReader(fh))
    by_year = defaultdict(list)
    for r in rows:
        by_year[int(r["year"])].append(r)
    return by_year


def unrecorded(year_rows):
    """Stats most of a season's rows leave blank: not kept that season.
    Hitouts are blank for anyone without one, so they are always kept."""
    out = set()
    for k in TARGETS + ["pct_played"]:
        if sum(1 for r in year_rows if r[k] == "") > len(year_rows) * 0.5:
            out.add(k)
    return out


GAME_KEY = {"one_pct": "onepct", "pct_played": "pctp"}
HEIGHTS = os.path.join(LEG, "heights.csv")
_heights = None
# Heights read off australianfootball.com player pages, each matched to the
# man by his date of birth (director 2026-11-15, "find sources").
HEIGHTS_AFC = os.path.join(LEG, "heights_afc.csv")
_heights_afc = None


def sourced_height(first, last, dob):
    """His height from data/legacy/heights_afc.csv by name and date of birth,
    '' with none."""
    global _heights_afc
    if _heights_afc is None:
        _heights_afc = {}
        if os.path.exists(HEIGHTS_AFC):
            with open(HEIGHTS_AFC, newline="", encoding="utf-8") as fh:
                _heights_afc = {(r["name"].lower(), r["dob"]): r["height_cm"] for r in csv.DictReader(fh)}
    if not dob:
        return ""
    return _heights_afc.get((("%s %s" % (first, last)).strip().lower(), dob), "")


def with_heights(rows):
    """Fill a list row's blank height from its Draftguru page
    (data/legacy/heights.csv, tools/legacy_1990s/fetch_heights.py: director
    2026-11-15, "Search other sources"). One no source gives stays blank."""
    global _heights
    if _heights is None:
        _heights = {}
        if os.path.exists(HEIGHTS):
            with open(HEIGHTS, newline="", encoding="utf-8") as fh:
                _heights = {r["draftguru_id"]: r["height_cm"] for r in csv.DictReader(fh) if r["height_cm"]}
    for r in rows:
        if not str(r.get("height_cm", "")).strip() and r.get("draftguru_id", "") in _heights:
            r["height_cm"] = _heights[r["draftguru_id"]]
            r["_height_from"] = "draftguru page"
        if not str(r.get("height_cm", "")).strip():
            h = sourced_height(r.get("first", ""), r.get("last", ""), r.get("dob", ""))
            if h:
                r["height_cm"] = h
                r["_height_from"] = "australianfootball.com"
    return rows


def page_height(dg, first="", last="", dob=""):
    return with_heights([{"draftguru_id": dg, "height_cm": "", "first": first, "last": last,
                          "dob": dob}])[0]["height_cm"]

POSITIONS = os.path.join(LEG, "positions.csv")
_positions = None


# From 2003 AFL Tables records every stat the game rates on, and the stats
# read the position; before, a real record does (director 2026-11-15).
FULL_STATS_FROM = 2003


def real_position(pid, season, role=""):
    """His real position (RUCK, MID, DEF or FWD) from data/legacy/positions.csv
    for a season before FULL_STATS_FROM, '' with no record. A record naming
    several roles ("DEF|MID") is passed whole when role is '' (the harness
    picks by his role scores); given role (his stats' reading), it is that
    role when the record names it, else the record's first role."""
    global _positions
    if season >= FULL_STATS_FROM:
        return ""
    if _positions is None:
        _positions = {}
        if os.path.exists(POSITIONS):
            with open(POSITIONS, newline="", encoding="utf-8") as fh:
                _positions = {r["afltables_id"]: r["position"] for r in csv.DictReader(fh)}
    pos = _positions.get(pid, "") if pid else ""
    if role and "|" in pos:
        named = pos.split("|")
        return role if role in named else named[0]
    return pos


def stats_role(rated, pid, upto):
    """His role in his latest rated season up to upto with a game, '' with none."""
    for y in sorted((y for y in rated if y <= upto), reverse=True):
        got = rated[y].get(pid) if pid else None
        if got and got[1] > 0:
            return got[3]
    return ""


def pos_cell(pid, season, role=""):
    """real_pos as the game's CSVs carry it (RUC for a ruck)."""
    pos = real_position(pid, season, role)
    return {"RUCK": "RUC"}.get(pos, pos)


def recorded(r, missing):
    """The row's numbers: an unrecorded stat None (written blank), any other
    blank 0."""
    out = dict(r)
    for k in ["gm", "ki", "mk", "hb", "di", "gl", "bh", "ho", "tk", "ff", "fa", "br"] + TARGETS + ["pct_played"]:
        out[k] = None if k in missing else (num(r[k]) or 0.0)
    out["_unrecorded"] = sorted(missing)
    return out


def harness_player(r, club, num_):
    p = {"club": club, "num": num_, "name": "%s %s" % (r["first"], r["last"]),
         "surname": r["last"], "real_pos": real_position(r.get("afltables_id", ""), int(r.get("year") or 9999)),
         "id": "%s_%s" % (club, num_)}
    p["blank"] = []
    for k in H.STAT_KEYS:
        src = {"onepct": "one_pct", "pctp": "pct_played"}.get(k, k)
        v = r.get(src, r.get(k))
        p[k] = float(v or 0.0)
        if v is None or v == "":
            p["blank"].append(k)
    return p


def unrecorded_in(hp):
    """Ratings.find_unrecorded: stats blank on most of these players."""
    return {k for k in H.STAT_KEYS if sum(k in p["blank"] for p in hp) * 2 > len(hp)}


def rate_seasons(by_year):
    """{year: {afltables_id: (overall, games, recorded row, role)}}."""
    rated = {}
    for y in sorted(by_year):
        missing = unrecorded(by_year[y])
        # A player traded mid-season has a row per club: one season, summed.
        merged = {}
        for r in by_year[y]:
            pid = r["afltables_id"]
            if pid in merged:
                m = merged[pid]
                for k in ["gm", "ki", "mk", "hb", "di", "gl", "bh", "ho", "tk", "ff", "fa", "br"] + TARGETS:
                    a, b = num(m[k]), num(r[k])
                    m[k] = "" if a is None and b is None else str((a or 0) + (b or 0))
                if "pct_played" not in missing:
                    m["pct_played"] = r["pct_played"] or m["pct_played"]
                m["club"] = r["club"]
            else:
                merged[pid] = dict(r)
        est = {pid: recorded(r, missing) for pid, r in merged.items()}
        H.set_unrecorded({GAME_KEY.get(k, k) for k in missing})
        players = [harness_player(e, code(e["club"]), i) for i, e in enumerate(est.values())]
        H.ERA_ANCHORS.clear()
        H.derive_ratings(players)
        H.fit_era_anchors(players)
        rated[y] = {pid: (p["overall"], int(e["gm"]), e, p["role"])
                    for (pid, e), p in zip(est.items(), players)}
    return rated


# ---------------------------------------------------------------- honours --
def honours(by_year, rated):
    """{afltables_id: score} over HONOURS_W's seasons. A named honour finds its
    player by the season's own rows: name and club, else a name unique that
    season, else a surname unique at that club (Steve / Stephen Malaxos). An
    honour with no match is printed."""
    def plain(last):
        return "".join(ch for ch in last.lower().replace(" sr.", "").replace(" jr.", "") if ch.isalpha())
    score = defaultdict(float)
    for y, w in HONOURS_W.items():
        by_name = defaultdict(set)
        by_name_club = {}
        by_last_club = defaultdict(set)
        for r in by_year.get(y, []):
            k = (r["first"].strip().lower(), plain(r["last"]))
            by_name[k].add(r["afltables_id"])
            by_name_club[k + (code(r["club"]),)] = r["afltables_id"]
            by_last_club[(k[1], code(r["club"]))].add(r["afltables_id"])
        for fn in HONOURS_FILES:
            with open(os.path.join(LEG, "honours", fn), newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    if int(r["year"]) != y or r["club"] == "OTHER":
                        continue
                    k = (r["first"].strip().lower(), plain(r["last"]))
                    pid = by_name_club.get(k + (code(r["club"]),))
                    if pid is None and len(by_name[k]) == 1:
                        pid = next(iter(by_name[k]))
                    if pid is None and len(by_last_club[(k[1], code(r["club"]))]) == 1:
                        pid = next(iter(by_last_club[(k[1], code(r["club"]))]))
                    if pid is None:
                        print("honours: no %d player for %s %s (%s, %s)" % (y, r["first"], r["last"], r["club"], fn))
                        continue
                    score[pid] += w
        # Brownlow placings on the season's votes (a mid-season move is one season).
        votes = sorted(((float(e[2]["br"] or 0), pid) for pid, e in rated.get(y, {}).items()), reverse=True)
        for v, pid in votes:
            if v <= 0:
                break
            place = 1 + sum(1 for o, _ in votes if o > v)
            if place <= 3:
                score[pid] += w
            elif place <= 10:
                score[pid] += 0.5 * w
    return score


# ------------------------------------------------------------------ lists --
def stints(career_rows):
    """club:first:last:games:goals, oldest first, a stint per unbroken run."""
    out = []
    for r in sorted(career_rows, key=lambda r: int(r["year"])):
        c, y = code(r["club"]), int(r["year"])
        g, gl = int(num(r["games"]) or 0), int(num(r["goals"]) or 0)
        if out and out[-1][0] == c and out[-1][2] == y - 1:
            out[-1][2] = y
            out[-1][3] += g
            out[-1][4] += gl
        else:
            out.append([c, y, y, g, gl])
    return ";".join("%s:%d:%d:%d:%d" % tuple(s) for s in out)


def fmt(v):
    return str(int(round(v)))


def stat_cells(e):
    vals = {}
    for k in ["gm", "ki", "mk", "hb", "di", "gl", "bh", "ho", "tk", "rb", "if50", "cl", "cg", "ff", "fa",
              "br", "cp", "up", "cm", "mi", "bo", "ga"]:
        vals[k] = "" if e[k] is None else fmt(e[k])
    vals["onepct"] = "" if e["one_pct"] is None else fmt(e["one_pct"])
    vals["pctp"] = "" if e["pct_played"] is None else "%.1f" % float(e["pct_played"])
    return vals


def age_at(dob):
    if not dob:
        return ""
    y, m, d = (int(x) for x in dob.split("-"))
    sy, sm, sd = (int(x) for x in START_DATE.split("-"))
    return str(sy - y - ((sm, sd) < (m, d)))


def build(by_year, rated):
    hon = honours(by_year, rated)
    with open(os.path.join(LEG, "1990s", "lists_1990_opening.csv"), newline="", encoding="utf-8") as fh:
        lists = with_heights(list(csv.DictReader(fh)))
    with open(os.path.join(LEG, "1990s", "careers_before_1990.csv"), newline="", encoding="utf-8") as fh:
        careers = defaultdict(list)
        for r in csv.DictReader(fh):
            careers[r["afltables_id"]].append(r)
    with open(os.path.join(LEG, "1990s", "drafts.csv"), newline="", encoding="utf-8") as fh:
        drafts = {}
        for r in csv.DictReader(fh):
            if r["draft"] in ("national", "pre_season", "mid_season") and r["pick"] and r["draftguru_id"]:
                drafts.setdefault(r["draftguru_id"], r)

    # A player with no 1990 number (most never played that year) takes a free
    # one from 60 up: the game keys a player on club + number.
    used = defaultdict(set)
    for L in lists:
        if L["num"]:
            used[code(L["club"])].add(int(L["num"]))
    for L in lists:
        if not L["num"]:
            c, n = code(L["club"]), 60
            while n in used[c]:
                n += 1
            used[c].add(n)
            L["num"] = str(n)

    players, history, additions, add_stats = [], [], [], []
    for L in lists:
        club, pid = code(L["club"]), L["afltables_id"]
        row89 = rated.get(DATA_SEASON, {}).get(pid) if pid else None
        seasons = []
        for y in (1987, 1988, 1989):
            got = rated.get(y, {}).get(pid) if pid else None
            if got and got[1] >= PEAK_GAMES:
                seasons.append("%d:%d:%d" % (y, got[0], got[1]))
        peak = 0
        for y in rated:
            if y >= DATA_SEASON and pid:
                got = rated[y].get(pid)
                if got and got[1] >= PEAK_GAMES:
                    peak = max(peak, got[0])
        first_year = min((int(r["year"]) for r in careers.get(pid, [])), default=None)
        debut = "01-04-%d" % first_year if first_year else ""
        d = drafts.get(L["draftguru_id"]) if L["draftguru_id"] else None
        if row89 and row89[1] > 0:
            cells = stat_cells(row89[2])
            players.append(dict(cells, club=club, num=L["num"], last=L["last"], first=L["first"],
                                src=str(DATA_SEASON), real_pos=pos_cell(pid, DATA_SEASON, row89[3]), dob=L["dob"], age=age_at(L["dob"]),
                                height_cm=L["height_cm"], weight_kg=L["weight_kg"], debut=debut,
                                height_source="draftguru" if L["height_cm"] else ""))
            history.append({"club": club, "num": L["num"], "slug": pid.rsplit("/", 1)[-1].replace(".html", ""),
                            "draft_year": d["year"] if d else "", "draft_type": "national" if d and d["draft"] == "national" else (d["draft"] if d else ""),
                            "draft_pick": d["pick"] if d else "", "seasons": ";".join(seasons),
                            "career": stints(careers.get(pid, [])), "peak": peak or "",
                            "honours": "%.3g" % hon[pid] if hon.get(pid) else ""})
        else:
            additions.append({"first": L["first"], "last": L["last"], "dob": L["dob"], "club": club,
                              "position": real_position(pid, DATA_SEASON, stats_role(rated, pid, DATA_SEASON)), "height_cm": L["height_cm"], "list": L["list"],
                              "peak": peak or "", "source_url": L["source_url"], "checked": L["checked"],
                              "_height_from": L.get("_height_from", "club list")})
            latest = None
            for y in (1988, 1987):
                got = rated.get(y, {}).get(pid) if pid else None
                if got and got[1] > 0:
                    latest = (y, got)
                    break
            if latest:
                cells = stat_cells(latest[1][2])
                add_stats.append(dict(cells, club=club, num="0", last=L["last"], first=L["first"],
                                      src=str(latest[0])))
    for A in additions:
        # A height no source gives stays blank (director 2026-11-15, "Search
        # other sources"; it replaces 2026-11-13's position average).
        A["height_from"] = A.pop("_height_from", "club list") if A["height_cm"] else ""
        A.pop("_height_from", None)
    return players, history, additions, add_stats


def write(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


# ------------------------------------------------------------- era report --
def era_report(by_year, rated, players):
    """Markdown: each decade's per-game averages and rating spread vs 2025."""
    stats = ["di", "ki", "hb", "mk", "tk", "gl", "cl", "cp", "if50", "rb"]
    lines = ["# Era averages against today (Legacy mode, row 142)", "",
             "Built by `tools/legacy_1990s/build_start.py --report`. Per player per game, every player "
             "with a game; - marks a stat not recorded for most of that era (never estimated). "
             "Ratings are each season against its own players, each position scaled on its own season (director 2026-11-13, 'Scale each position per season').", "",
             "| Seasons | " + " | ".join(stats) + " | rated 80+ per season | median OVR |",
             "|" + "---|" * (len(stats) + 3)]
    for label, years in (("1987-89", range(1987, 1990)), ("1990-99", range(1990, 2000)),
                         ("2000-09", range(2000, 2010)), ("2010-19", range(2010, 2020)),
                         ("2020-25", range(2020, 2026))):
        tot, gm, n80, ovrs, est = defaultdict(float), 0.0, 0, [], set()
        for y in years:
            est |= unrecorded(by_year[y])
            for pid, (ovr, g, e, _role) in rated[y].items():
                gm += g
                for k in stats:
                    tot[k] += e[k] or 0.0
                if g >= PEAK_GAMES:
                    ovrs.append(ovr)
                    n80 += ovr >= 80
        ovrs.sort()
        cells = ["-" if k in est else "%.1f" % (tot[k] / gm) for k in stats]
        lines.append("| %s | %s | %.1f | %d |" % (label, " | ".join(cells), n80 / len(list(years)),
                                                  ovrs[len(ovrs) // 2]))
    lines += ["", "## The 1990 lists as the game loads them", "",
              "Rated on 1989 by `tools/sim_harness.py` (the game rates again at load, the same model).", ""]
    hp = []
    for r in players:
        e = dict((k, r[k]) for k in ENRICHED[4:28])
        p = harness_player({**{("one_pct" if k == "onepct" else "pct_played" if k == "pctp" else k): v
                               for k, v in e.items()}, "first": r["first"], "last": r["last"]},
                           r["club"], r["num"])
        hp.append(p)
    H.ERA_ANCHORS.clear()
    H.set_unrecorded(unrecorded_in(hp))
    H.derive_ratings(hp)
    H.fit_era_anchors(hp)
    by_club = defaultdict(list)
    for p in hp:
        by_club[p["club"]].append(p["overall"])
    lines.append("| Club | players | median OVR | best | 80+ |")
    lines.append("|---|---|---|---|---|")
    for c in sorted(by_club):
        v = sorted(by_club[c])
        lines.append("| %s | %d | %d | %d | %d |" % (c, len(v), v[len(v) // 2], v[-1], sum(x >= 80 for x in v)))
    top = sorted(hp, key=lambda p: -p["overall"])[:15]
    lines += ["", "Top 15 in 1990: " + ", ".join("%s (%s) %d" % (p["name"], p["club"], p["overall"]) for p in top)]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    by_year = load_seasons()
    rated = rate_seasons(by_year)
    players, history, additions, add_stats = build(by_year, rated)
    os.makedirs(OUT_DIR, exist_ok=True)
    write(os.path.join(OUT_DIR, "players_1990.csv"), ENRICHED, players)
    write(os.path.join(OUT_DIR, "history_1990.csv"),
          ["club", "num", "slug", "draft_year", "draft_type", "draft_pick", "seasons", "career", "peak", "honours"], history)
    write(os.path.join(OUT_DIR, "list_additions_1990.csv"),
          ["first", "last", "dob", "club", "position", "height_cm", "height_from", "list", "peak", "source_url",
           "checked"], additions)
    write(os.path.join(OUT_DIR, "list_addition_stats_1990.csv"), ADD_STATS, add_stats)
    print("players %d, additions %d (%d with an earlier season)" % (len(players), len(additions), len(add_stats)))
    # Each real player's last season, read by his retirement (last_seasons.py).
    import last_seasons
    last_seasons.main(1990)
    if a.report:
        path = os.path.join(ROOT, "docs", "research", "LEGACY_ERA_REPORT.md")
        with open(path, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(era_report(by_year, rated, players))
        print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
