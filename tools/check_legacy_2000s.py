#!/usr/bin/env python3
"""Check data/legacy/2000s/ (TODO row 142, Legacy mode data).

    python tools/check_legacy_2000s.py            # report, exit 1 on a hard failure
    python tools/check_legacy_2000s.py --quiet    # counts only

Copied from tools/check_legacy_2010s.py with the 2000s league: the same 16
clubs every season (Fitzroy gone after 1996, Gold Coast from 2011, GWS from
2012), no free agency (it began in the 2012 trade period) and no Category B
rookies (from 2010).

Hard failures (exit 1): a season without exactly the 16 clubs (lists, season
totals and ladder), a duplicate list row, a ladder that does not add up, a
free-agent move before free agency, a Draftguru pick with no Wikipedia pick at the
same number (outside the known differences below), a move without both clubs.

Warnings (reported, never filled in): list sizes outside the published limits,
list rows with no recorded way of joining, blank weights, positions and the
other gaps the sources leave.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "data", "legacy", "2000s")
SEASONS = range(2000, 2010)
DRAFT_YEARS = range(1999, 2009)  # the 2009 draft is in data/legacy/2010s
CLUBS_2000 = {"ADE", "BRL", "CAR", "COL", "ESS", "FRE", "GEE", "HAW", "MEL", "NTH", "PAD", "RIC",
              "STK", "SYD", "WCE", "WBD"}

# The same limits as the 2010s check (a primary list of about 38, 40 with the
# veterans' allowance; six rookies, more for the Queensland and NSW clubs'
# zone and scholarship rookies). Category B rookies began in 2010, so the 2000s
# have none. Draftguru's lists hold everyone listed at any point in the season,
# so a mid-season replacement can push a club over by one or two. Warnings only.
SENIOR_MAX = 40
ROOKIE_MAX = 6
ROOKIE_MAX_NORTH = 9  # BRL, SYD: zone and scholarship rookies
CAT_B_MAX = 0
NORTH = {"BRL", "SYD"}
EXPANSION: set = set()

# Pick-number differences between Draftguru and Wikipedia, each checked by hand
# against both pages on 2026-11-11. Spelling differences are not listed: the
# surname test below allows them only when the pick and club agree.
KNOWN_PICK_DIFFS: dict = {
    (2000, "rookie", 60): "Brent Piltz (Sydney, as AFL Tables spells him) is spelt Brent Plitz on Wikipedia",
    (2003, "national", 47): "Andrew Ericksen (Sydney) is spelt Andrew Eriksen on Wikipedia",
}


def load(name: str) -> list[dict]:
    with open(os.path.join(DIR, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalpha())


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
    for y in SEASONS:
        have = {c for (yy, c) in by if yy == y}
        if len(have) != 16 or have != CLUBS_2000:
            fails.append(f"{y}: {len(have)} clubs, want 16; {sorted(have ^ CLUBS_2000)} missing or extra")
        st_clubs = {s["club"] for s in stats if int(s["year"]) == y}
        if st_clubs != CLUBS_2000:
            fails.append(f"{y}: AFL Tables season totals cover {len(st_clubs)} clubs, want 16")
    over = []
    for (y, c), cnt in sorted(by.items()):
        rook_max = ROOKIE_MAX_NORTH if c in NORTH else ROOKIE_MAX
        if cnt["senior"] > SENIOR_MAX and (c, y) not in EXPANSION:
            over.append(f"{y} {c} senior {cnt['senior']} > {SENIOR_MAX}")
        if cnt["rookie"] > rook_max:
            over.append(f"{y} {c} rookie {cnt['rookie']} > {rook_max}")
        if cnt["cat_b"] > CAT_B_MAX:
            over.append(f"{y} {c} cat_b {cnt['cat_b']} > {CAT_B_MAX}")
    if over:
        warns.append(f"{len(over)} club-season list counts above the published limits "
                     f"(Draftguru counts everyone listed during the season): " + "; ".join(over))

    no_join = [r for r in lists if not r["joined_how"]]
    if no_join:
        sample = "; ".join(f"{r['year']} {r['club']} {r['first']} {r['last']} ({r['first_drafted']})"
                           for r in no_join[:15])
        warns.append(f"{len(no_join)} list rows have no recorded way of joining their club: {sample}")
    for col in ("dob", "height_cm", "weight_kg", "position"):
        blank = sum(1 for r in lists if not r[col])
        if blank:
            warns.append(f"lists.csv {col} blank on {blank} of {len(lists)} rows")
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

    # --------------------------------------------------------------- drafts
    dg_picks = {}
    wk_picks = {}
    for d in drafts:
        if d["draft"] not in ("national", "preseason", "rookie", "mini") or not d["pick"]:
            continue
        key = (int(d["year"]), d["draft"], int(d["pick"]))
        (wk_picks if d["only_in"] == "wikipedia" else dg_picks)[key] = d
    count_rows = []
    no_wiki = []
    for y in DRAFT_YEARS:
        for kind in ("national", "preseason", "rookie", "mini"):
            dg_n = sum(1 for k in dg_picks if k[0] == y and k[1] == kind)
            w_n = wiki.get(str(y), {}).get(kind, 0)
            extra = sum(1 for k in wk_picks if k[0] == y and k[1] == kind)
            if dg_n or w_n:
                count_rows.append((y, kind, dg_n, w_n, extra))
            if dg_n and not w_n:
                # Wikipedia's page for this year has no table for this draft.
                no_wiki.append(f"{y} {kind} ({dg_n} picks)")
                continue
            # Wikipedia's count = Draftguru's picks it also lists + the picks only it lists.
            for k in [k for k in dg_picks if k[0] == y and k[1] == kind and k not in KNOWN_PICK_DIFFS]:
                d = dg_picks[k]
                if norm(d["last"])[:4] not in norm(d["wiki_player"]):
                    fails.append(f"Draftguru pick {k} {d['first']} {d['last']} is "
                                 f"'{d['wiki_player'] or 'absent'}' on Wikipedia")
            matched = sum(1 for k in dg_picks if k[0] == y and k[1] == kind and dg_picks[k]["wiki_player"])
            if w_n != matched + extra:
                fails.append(f"{y} {kind}: Wikipedia lists {w_n} picks; {matched} match Draftguru by number"
                             f" and {extra} are Wikipedia-only")
    if no_wiki:
        warns.append("Wikipedia has no table for these drafts, so Draftguru's picks stand unchecked: "
                      + "; ".join(no_wiki))
    elev = sum(1 for k in wk_picks)
    if elev:
        warns.append(f"{elev} picks appear only on Wikipedia; kept with only_in=wikipedia")

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
    # Free agency began in the 2012 trade period: none in this decade.
    fa = [m for m in moves if "free_agent" in m["kind"]]
    if fa:
        fails.append(f"{len(fa)} free-agent moves before free agency existed: " +
                     "; ".join(f"{m['year']} {m['first']} {m['last']}" for m in fa[:10]))
    kinds = Counter(m["kind"] for m in moves)

    # -------------------------------------------------------------- ladders
    for y in SEASONS:
        rows = [r for r in ladders if int(r["year"]) == y]
        n = 16
        if len(rows) != n or sorted(int(r["pos"]) for r in rows) != list(range(1, n + 1)):
            fails.append(f"{y} ladder has {len(rows)} rows, want {n}")
        for r in rows:
            w, l, d = int(r["w"]), int(r["l"]), int(r["d"])
            if w + l + d != 22:
                fails.append(f"{y} {r['club']} played {w + l + d}")
            if int(r["pts"]) != 4 * w + 2 * d:
                fails.append(f"{y} {r['club']} points {r['pts']} != 4W+2D")
        fin = Counter(r["finals"] for r in rows)
        if fin["premiers"] != 1 or fin["runners_up"] != 1:
            fails.append(f"{y} ladder premiers/runners-up count {dict(fin)}")
        if {r["club"] for r in rows} != CLUBS_2000:
            fails.append(f"{y} ladder clubs differ from the 16")
        if sum(v for k, v in fin.items() if k) != 8:
            fails.append(f"{y} ladder has {sum(v for k, v in fin.items() if k)} finalists")

    # --------------------------------------------------------------- report
    print("List rows per season (senior / rookie / Cat B):")
    for y in SEASONS:
        tot = Counter()
        for (yy, _), cnt in by.items():
            if yy == y:
                tot.update(cnt)
        print(f"  {y}: {sum(tot.values())} ({tot['senior']} / {tot['rookie']} / {tot['cat_b']})")
    print("Draft picks (year, draft, Draftguru, Wikipedia, Wikipedia-only):")
    for row in count_rows:
        print("  " + " ".join(str(x) for x in row))
    print("Moves by kind (1999-2008 trade periods):", dict(sorted(kinds.items())))
    if not a.quiet:
        for w in warns:
            print("WARN", w)
    for f in fails:
        print("FAIL", f)
    print(f"{len(fails)} failures, {len(warns)} warnings")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
