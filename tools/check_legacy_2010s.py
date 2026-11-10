#!/usr/bin/env python3
"""Check data/legacy/2010s/ (TODO row 142, Legacy mode data).

    python tools/check_legacy_2010s.py            # report, exit 1 on a hard failure
    python tools/check_legacy_2010s.py --quiet    # counts only

Hard failures (exit 1): a club missing from a season, a duplicate list row, a
ladder that does not add up, a Draftguru pick with no Wikipedia pick at the
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
DIR = os.path.join(ROOT, "data", "legacy", "2010s")
SEASONS = range(2010, 2020)
CLUBS_2010 = {"ADE", "BRL", "CAR", "COL", "ESS", "FRE", "GEE", "HAW", "MEL", "NTH", "PAD", "RIC",
              "STK", "SYD", "WCE", "WBD"}

# Published limits (Wikipedia, "Rookie list" and "AFL draft"): a 38-player primary
# list (40 with the veterans' allowance of the period), four to six rookies with
# more allowed for the Queensland and NSW clubs, and up to three Category B
# rookies from 2010. Draftguru's lists hold everyone listed at any point in the
# season, so a mid-season replacement can push a club over by one or two.
SENIOR_MAX = 40
ROOKIE_MAX = 6
ROOKIE_MAX_NORTH = 9  # BRL, GCS, GWS, SYD: zone and academy rookies
CAT_B_MAX = 3
NORTH = {"BRL", "GCS", "GWS", "SYD"}
# Expansion concessions: Gold Coast's and GWS's first seasons carried extra
# senior-list places (the underage and uncontracted signings).
EXPANSION = {("GCS", 2011), ("GCS", 2012), ("GWS", 2012), ("GWS", 2013), ("GWS", 2014)}

# Pick-number differences between Draftguru and Wikipedia, each checked by hand
# against both pages on 2026-11-10. Spelling differences are not listed: the
# surname test below allows them only when the pick and club agree.
KNOWN_PICK_DIFFS = {
    (2011, "national", 21): "Tom Mitchell (Sydney father-son): Wikipedia numbers the bid pick differently",
    (2011, "national", 62): "Dylan Buckley: Wikipedia lists him at another pick number",
    (2011, "national", 86): "Jed Bews (Geelong father-son): Wikipedia lists him at another pick number",
    (2010, "national", 55): "Angus Dewar (Draftguru) is Angus Litherland on Wikipedia: same Hawthorn pick, later name",
    (2011, "rookie", 6): "Jai Sheahan (Draftguru) is spelt Jai Sheehan on Wikipedia",
    (2012, "rookie", 56): "Jordon Bourke: Wikipedia's rookie order differs by one",
    (2012, "rookie", 57): "Brandon Jack: Wikipedia's rookie order differs by one",
    (2012, "rookie", 58): "Sam Naismith: Wikipedia's rookie order differs by one",
    (2017, "national", 3): "Paddy Dow: Wikipedia's table merges picks 3 and 53 in one row",
    (2017, "national", 53): "Ryley Stoddart: Wikipedia's table merges picks 3 and 53 in one row",
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
        want = set(CLUBS_2010) | ({"GCS"} if y >= 2011 else set()) | ({"GWS"} if y >= 2012 else set())
        have = {c for (yy, c) in by if yy == y}
        if have != want:
            fails.append(f"{y}: clubs {sorted(have ^ want)} missing or extra")
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
    for y in range(2009, 2020):
        for kind in ("national", "preseason", "rookie", "mini"):
            dg_n = sum(1 for k in dg_picks if k[0] == y and k[1] == kind)
            w_n = wiki.get(str(y), {}).get(kind, 0)
            extra = sum(1 for k in wk_picks if k[0] == y and k[1] == kind)
            if dg_n or w_n:
                count_rows.append((y, kind, dg_n, w_n, extra))
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
    elev = sum(1 for k in wk_picks)
    warns.append(f"{elev} picks appear only on Wikipedia (rookie elevations through the national draft to 2013,"
                 f" re-listed players in later rookie drafts); kept with only_in=wikipedia")

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
    fa_rows = []
    for y in range(2012, 2020):
        dg_fa = sum(1 for m in moves if int(m["year"]) == y and "free_agent" in m["kind"])
        w_fa = wiki.get(str(y), {}).get("free_agency", 0)
        fa_rows.append((y, dg_fa, w_fa))
        if dg_fa != w_fa:
            warns.append(f"{y} free agency: Draftguru {dg_fa}, Wikipedia {w_fa}")

    # -------------------------------------------------------------- ladders
    for y in SEASONS:
        rows = [r for r in ladders if int(r["year"]) == y]
        n = 16 if y == 2010 else 17 if y == 2011 else 18
        if len(rows) != n or sorted(int(r["pos"]) for r in rows) != list(range(1, n + 1)):
            fails.append(f"{y} ladder has {len(rows)} rows, want {n}")
        for r in rows:
            w, l, d = int(r["w"]), int(r["l"]), int(r["d"])
            if w + l + d != 22:
                # 2015: Adelaide v Geelong (round 13) was cancelled; both clubs played 21.
                if not (y == 2015 and r["club"] in ("ADE", "GEE") and w + l + d == 21):
                    fails.append(f"{y} {r['club']} played {w + l + d}")
            # 2015's cancelled Adelaide v Geelong match: the sources count wins only (noted per row).
            if int(r["pts"]) != 4 * w + 2 * d:
                fails.append(f"{y} {r['club']} points {r['pts']} != 4W+2D")
        fin = Counter(r["finals"] for r in rows)
        if fin["premiers"] != 1 or fin["runners_up"] != 1:
            fails.append(f"{y} ladder premiers/runners-up count {dict(fin)}")
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
    print("Free agents (year, Draftguru, Wikipedia):", " ".join(f"{y}:{a}/{b}" for y, a, b in fa_rows))
    if not a.quiet:
        for w in warns:
            print("WARN", w)
    for f in fails:
        print("FAIL", f)
    print(f"{len(fails)} failures, {len(warns)} warnings")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
