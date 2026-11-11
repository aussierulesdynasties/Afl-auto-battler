#!/usr/bin/env python3
"""Check data/legacy/1990s/ (TODO row 142, Legacy mode from 1990).

    python tools/check_legacy_1990s.py            # report, exit 1 on a hard failure
    python tools/check_legacy_1990s.py --quiet    # counts only

Hard failures (exit 1): a season whose clubs are not that year's league (14
clubs in 1990; Adelaide from 1991, Fremantle 1995, Port Adelaide 1997; Fitzroy,
the Brisbane Bears and Footscray to 1996, the Brisbane Lions and Western
Bulldogs from 1997), in any of lists, ladders and season stats; a duplicate
list row; a ladder that does not add up or has the wrong number of finalists
(final five 1990, six 1991-1993, eight from 1994); a Draftguru pick with no
Wikipedia pick at the same number (outside the known differences below); a
trade without both clubs.

Warnings (reported, never filled in): list sizes, list rows with no recorded
way of joining, blank weights and positions, and the other gaps the sources
leave.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "data", "legacy", "1990s")
SEASONS = range(1990, 2000)
DRAFT_YEARS = range(1989, 2000)
CORE = {"CAR", "COL", "ESS", "GEE", "HAW", "MEL", "NTH", "RIC", "STK", "SYD", "WCE"}


def clubs_for(y: int) -> set[str]:
    c = set(CORE)
    c |= {"FIT", "BRB", "FOO"} if y <= 1996 else {"BRL", "WBD"}
    if y >= 1991:
        c.add("ADE")
    if y >= 1995:
        c.add("FRE")
    if y >= 1997:
        c.add("PAD")
    return c


# Club counts per season, written out so the era facts are asserted directly.
CLUB_COUNT = {1990: 14, 1991: 15, 1992: 15, 1993: 15, 1994: 15, 1995: 16, 1996: 16,
              1997: 16, 1998: 16, 1999: 16}
# Home-and-away games per club: 1993 was a 20-round season.
GAMES = {y: (20 if y == 1993 else 22) for y in SEASONS}
FINALISTS = {y: (5 if y == 1990 else 6 if y <= 1993 else 8) for y in SEASONS}

# Draftguru's lists count everyone listed during the season (mid-season
# draftees and replacements included) before the rookie list began in 1997, so
# the 1990s senior lists run well above a single cap. Warn only past these.
SENIOR_MAX = 60
ROOKIE_MAX = 6

# Pick-number differences between Draftguru and Wikipedia, each checked by hand
# against both pages on 2026-11-11 (see the PR). Spelling differences are not
# listed: the surname test below allows them only when the pick agrees.
KNOWN_PICK_DIFFS: dict[tuple, str] = {
    (1989, "national", 106): "Ashley McIntosh (West Coast father-son): Wikipedia has him at 112, Ernie Hug at 106",
    (1989, "national", 112): "Ernie Hug (Collingwood father-son): Wikipedia has him at 106, McIntosh at 112",
    (1989, "national", 117): "Tony Begovich: Wikipedia lists West Coast's three post-draft picks apart (1-3)",
    (1989, "national", 118): "Brad Gwilliam: Wikipedia lists West Coast's three post-draft picks apart (1-3)",
    (1989, "national", 119): "Dean Kemp: Wikipedia lists West Coast's three post-draft picks apart (1-3)",
    (1990, "national", 43): "Glyn Tomlinson (Draftguru) is spelt Glen Thomlinson on Wikipedia",
    (1992, "national", 114): "Paul Whelan: Wikipedia has picks 114 and 115 the other way round",
    (1992, "national", 115): "Richard Marr: Wikipedia has picks 114 and 115 the other way round",
    (1994, "national", 72): "Dean Grainger: Wikipedia's pick list has him at 72, its table has Daniel Wilcox",
    (1997, "rookie", 24): "Draftguru numbers the 1998 rookie draft without Wikipedia's passes at 24 and 32",
    (1997, "rookie", 26): "Draftguru numbers the 1998 rookie draft without Wikipedia's passes at 24 and 32",
    (1997, "rookie", 27): "Draftguru numbers the 1998 rookie draft without Wikipedia's passes at 24 and 32",
    (1997, "rookie", 28): "Draftguru numbers the 1998 rookie draft without Wikipedia's passes at 24 and 32",
    (1997, "rookie", 29): "Draftguru numbers the 1998 rookie draft without Wikipedia's passes at 24 and 32",
    (1997, "rookie", 30): "Draftguru numbers the 1998 rookie draft without Wikipedia's passes at 24 and 32",
    (1997, "rookie", 32): "Draftguru numbers the 1998 rookie draft without Wikipedia's passes at 24 and 32",
    (1997, "rookie", 33): "Draftguru numbers the 1998 rookie draft without Wikipedia's passes at 24 and 32",
}


def load(name: str) -> list[dict]:
    with open(os.path.join(DIR, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalpha())


def same_player(d: dict) -> bool:
    """Draftguru's pick and Wikipedia's pick at the same number are one player:
    the surname matches, or is a close spelling (Repacholi/Rapacholi,
    MacKay/McKay) of the same first name."""
    last, wp = norm(d["last"]), d["wiki_player"]
    if not wp:
        return False
    if last[:4] in norm(wp):
        return True
    w_first, _, w_last = wp.partition(" ")
    return (norm(d["first"])[:3] == norm(w_first)[:3]
            and difflib.SequenceMatcher(None, last, norm(w_last)).ratio() >= 0.75)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    fails: list[str] = []
    warns: list[str] = []

    lists = load("lists.csv")
    drafts = load("drafts.csv")
    moves = load("moves.csv")
    ladders = load("ladders.csv")
    stats = load("season_stats.csv")
    with open(os.path.join(DIR, "wikipedia_draft_counts.json"), encoding="utf-8") as fh:
        wiki = json.load(fh)

    # --------------------------------------------------------- era club sets
    for y in SEASONS:
        want = clubs_for(y)
        if len(want) != CLUB_COUNT[y]:
            fails.append(f"{y}: era table gives {len(want)} clubs, want {CLUB_COUNT[y]}")
        for name, rows in (("lists", lists), ("ladders", ladders), ("season_stats", stats)):
            have = {r["club"] for r in rows if int(r["year"]) == y}
            if have != want:
                fails.append(f"{y} {name}: clubs {sorted(have ^ want)} missing or extra")

    # ---------------------------------------------------------------- lists
    by = defaultdict(Counter)
    seen = Counter()
    for r in lists:
        y = int(r["year"])
        by[(y, r["club"])][r["list"]] += 1
        seen[(y, r["club"], r["draftguru_id"])] += 1
    for k, n in seen.items():
        if n > 1:
            fails.append(f"duplicate list row {k}")
    over = []
    for (y, c), cnt in sorted(by.items()):
        if cnt["senior"] > SENIOR_MAX:
            over.append(f"{y} {c} senior {cnt['senior']} > {SENIOR_MAX}")
        if cnt["rookie"] > ROOKIE_MAX:
            over.append(f"{y} {c} rookie {cnt['rookie']} > {ROOKIE_MAX}")
        if y < 1997 and cnt["rookie"]:
            fails.append(f"{y} {c} has {cnt['rookie']} rookies before the rookie list began (1997)")
    if over:
        warns.append(f"{len(over)} club-season list counts above the expected limits: " + "; ".join(over))

    no_join = [r for r in lists if not r["joined_how"]]
    if no_join:
        came = sum(1 for r in no_join if r["joined_from"])
        before = sum(1 for r in no_join if r["joined_year"] and int(r["joined_year"]) < 1986)
        sample = "; ".join(f"{r['year']} {r['club']} {r['first']} {r['last']} ({r['first_drafted']})"
                           for r in no_join[:15])
        warns.append(f"{len(no_join)} list rows have no recorded way of joining their club (Draftguru has no"
                     f" joining line; {before} of them joined before the 1986 National Draft, and {came} came"
                     f" from another club, which joined_from names): {sample}")
    for col in ("dob", "height_cm", "weight_kg", "position"):
        blank = sum(1 for r in lists if not r[col])
        if blank:
            warns.append(f"lists.csv {col} blank on {blank} of {len(lists)} rows")
    blank90 = sum(1 for r in lists if r["year"] == "1990" and r["games_prior"] == "")
    if blank90:
        warns.append(f"lists.csv games_prior/goals_prior/career blank on {blank90} 1990 rows"
                     f" (Draftguru's first season has no prior columns)")
    played = [r for r in lists if int(r["games"]) > 0]
    unmatched = [r for r in played if not r["afltables_id"]]
    if unmatched:
        warns.append(f"{len(unmatched)} of {len(played)} list rows with a game have no AFL Tables match: " +
                     "; ".join(f"{r['year']} {r['club']} {r['first']} {r['last']}" for r in unmatched[:10]))
    at_games = Counter()
    for s in stats:
        at_games[(s["year"], s["club"])] += int(s["gm"] or 0)
    dg_games = Counter()
    for r in lists:
        dg_games[(r["year"], r["club"])] += int(r["games"])
    gdiff = [f"{k[0]} {k[1]} Draftguru {dg_games[k]} AFL Tables {at_games[k]}"
             for k in sorted(at_games) if at_games[k] != dg_games[k]]
    if gdiff:
        warns.append(f"{len(gdiff)} club-seasons where player-games differ between sources: " + "; ".join(gdiff[:10]))
    for y in SEASONS:
        for c in clubs_for(y):
            # Every club fields 18 players (plus interchange) in each game.
            n = at_games[(str(y), c)]
            if n < 18 * GAMES[y]:
                fails.append(f"{y} {c}: AFL Tables player-games {n} < 18 x {GAMES[y]}")

    # --------------------------------------------------------------- drafts
    dg_picks = {}
    wk_picks = {}
    for d in drafts:
        if d["draft"] not in ("national", "preseason", "rookie", "mini", "mid_season") or not d["pick"]:
            continue
        key = (int(d["year"]), d["draft"], int(d["pick"]))
        (wk_picks if d["only_in"] == "wikipedia" else dg_picks)[key] = d
    count_rows = []
    for y in DRAFT_YEARS:
        if not any(k[0] == y and k[1] == "national" for k in dg_picks):
            fails.append(f"{y}: no National Draft picks")
        for kind in ("national", "preseason", "mid_season", "rookie"):
            dg_n = sum(1 for k in dg_picks if k[0] == y and k[1] == kind)
            w_n = wiki.get(str(y), {}).get(kind, 0)
            extra = sum(1 for k in wk_picks if k[0] == y and k[1] == kind)
            if dg_n or w_n:
                count_rows.append((y, kind, dg_n, w_n, extra))
            if kind == "rookie" and y < 1996 and (dg_n or w_n):
                fails.append(f"{y}: rookie draft picks before the first rookie draft (1996, for 1997)")
            if not w_n:
                continue  # Wikipedia has no table for this draft: nothing to compare
            for k in [k for k in dg_picks if k[0] == y and k[1] == kind and k not in KNOWN_PICK_DIFFS]:
                d = dg_picks[k]
                if not same_player(d):
                    fails.append(f"Draftguru pick {k} {d['first']} {d['last']} is "
                                 f"'{d['wiki_player'] or 'absent'}' on Wikipedia")
            matched = sum(1 for k in dg_picks if k[0] == y and k[1] == kind and dg_picks[k]["wiki_player"])
            # Wikipedia picks whose player Draftguru holds at another number.
            elsewhere = wiki.get(str(y), {}).get(f"{kind}_listed_elsewhere", 0)
            if w_n != matched + extra + elsewhere:
                fails.append(f"{y} {kind}: Wikipedia lists {w_n} picks; {matched} match Draftguru by number,"
                             f" {elsewhere} are at another number and {extra} are Wikipedia-only")
    if wk_picks:
        warns.append(f"{len(wk_picks)} picks appear only on Wikipedia; kept with only_in=wikipedia")
    flags = Counter(d["flag"] for d in drafts if d["flag"])
    for need in ("zone", "father_son"):
        if not flags[need]:
            fails.append(f"no {need} selections recorded in the 1989-1999 drafts")

    # ---------------------------------------------------------------- moves
    listed = {(r["year"], r["draftguru_id"]) for r in lists}
    outside = []
    for m in moves:
        if not m["from_club"] and m["to_club"] and (m["year"], m["draftguru_id"]) not in listed:
            outside.append(f"{m['year']} {m['first']} {m['last']} -> {m['to_club']} ({m['kind']})")
        elif not m["from_club"] or not m["to_club"]:
            fails.append(f"move {m['year']} {m['first']} {m['last']} -> {m['to_club']} lacks a club")
        elif m["from_club"] == m["to_club"]:
            fails.append(f"move {m['year']} {m['first']} {m['last']} from and to {m['to_club']}")
    if outside:
        warns.append(f"{len(outside)} moves come from outside the AFL (the player was on no AFL list that"
                     f" season), so from_club is blank: " + "; ".join(outside))

    # -------------------------------------------------------------- ladders
    for y in SEASONS:
        rows = [r for r in ladders if int(r["year"]) == y]
        n = CLUB_COUNT[y]
        if len(rows) != n or sorted(int(r["pos"]) for r in rows) != list(range(1, n + 1)):
            fails.append(f"{y} ladder has {len(rows)} rows, want {n}")
        for r in rows:
            w, l, d = int(r["w"]), int(r["l"]), int(r["d"])
            if w + l + d != GAMES[y]:
                fails.append(f"{y} {r['club']} played {w + l + d}, want {GAMES[y]}")
            if int(r["pts"]) != 4 * w + 2 * d:
                fails.append(f"{y} {r['club']} points {r['pts']} != 4W+2D")
            if r["note"]:
                warns.append(f"{y} {r['club']} ladder: {r['note']}")
        fin = Counter(r["finals"] for r in rows)
        if fin["premiers"] != 1 or fin["runners_up"] != 1:
            fails.append(f"{y} ladder premiers/runners-up count {dict(fin)}")
        nfin = sum(v for k, v in fin.items() if k)
        if nfin != FINALISTS[y]:
            fails.append(f"{y} ladder has {nfin} finalists, want {FINALISTS[y]}")
        top = {r["club"] for r in rows if int(r["pos"]) <= FINALISTS[y]}
        if top != {r["club"] for r in rows if r["finals"]}:
            fails.append(f"{y} finalists are not the top {FINALISTS[y]} on the ladder")

    # --------------------------------------------------------------- report
    print("Clubs per season:", " ".join(f"{y}:{len(clubs_for(y))}" for y in SEASONS))
    print("List rows per season (senior / rookie / Cat B; distinct players):")
    for y in SEASONS:
        tot = Counter()
        for (yy, _), cnt in by.items():
            if yy == y:
                tot.update(cnt)
        players = len({r["draftguru_id"] for r in lists if int(r["year"]) == y})
        print(f"  {y}: {sum(tot.values())} ({tot['senior']} / {tot['rookie']} / {tot['cat_b']}; {players})")
    print("Draft picks (year, draft, Draftguru, Wikipedia, Wikipedia-only):")
    for row in count_rows:
        print("  " + " ".join(str(x) for x in row))
    print("Draft flags:", dict(sorted(flags.items())))
    print("Trades per year:", " ".join(f"{y}:{sum(1 for m in moves if int(m['year']) == y and m['kind'] == 'traded')}"
                                       for y in DRAFT_YEARS))
    if not a.quiet:
        for w in warns:
            print("WARN", w)
    for f in fails:
        print("FAIL", f)
    print(f"{len(fails)} failures, {len(warns)} warnings")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
