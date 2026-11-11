#!/usr/bin/env python3
"""Build data/legacy/1990s/*.csv from the pages fetch.py cached.

    python tools/legacy_1990s/build.py --cache data/cache/legacy_1990s

Same format and method as tools/legacy_2010s/build.py. Facts only. Nothing is
guessed: a value the sources do not give stays blank, and
tools/check_legacy_1990s.py reports the blanks.

Draft years follow Draftguru: year Y holds the Y National Draft, the
pre-season draft and rookie draft that followed it, the mid-season draft held
in the middle of season Y+1 (1990-1993) and the Y trade period. Wikipedia
names a mid-season draft by the year it was held, so Draftguru's 1990
mid-season draft is Wikipedia's "1991 mid-season draft".

Era club codes. A club is coded by the name it played under that season:
FIT Fitzroy (to 1996), BRB Brisbane Bears (to 1996), BRL Brisbane Lions (from
1997), FOO Footscray (to 1996), WBD Western Bulldogs (from 1997). Draftguru and
Squiggle use today's names for every year, so their names are mapped through
`era()` with the season they refer to. A draft or trade in year Y is for the
season Y+1, so its club takes the Y+1 name.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import DG, cache_path, club_slugs, wiki_draft_url  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "legacy", "1990s")
CHECKED = "2026-11-11"
SEASONS = range(1990, 2000)
DRAFT_YEARS = range(1989, 2000)

SLUG = {
    "adelaide": "ADE", "brisbane": "BRL", "carlton": "CAR", "collingwood": "COL",
    "essendon": "ESS", "fitzroy": "FIT", "fremantle": "FRE", "geelong": "GEE",
    "hawthorn": "HAW", "melbourne": "MEL", "north-melbourne": "NTH", "port-adelaide": "PAD",
    "richmond": "RIC", "st-kilda": "STK", "sydney": "SYD", "west-coast": "WCE",
    "western-bulldogs": "WBD",
}
# Names as the sources write them, to a base code (today's club); era() then
# gives the name the club played under in a given season.
NAME = {
    "adelaide": "ADE", "adelaide crows": "ADE", "brisbane": "BRL", "brisbane lions": "BRL",
    "brisbane bears": "BRB", "carlton": "CAR", "collingwood": "COL", "essendon": "ESS",
    "fitzroy": "FIT", "fremantle": "FRE", "fremantle dockers": "FRE", "geelong": "GEE",
    "geelong cats": "GEE", "hawthorn": "HAW", "melbourne": "MEL", "north melbourne": "NTH",
    "kangaroos": "NTH", "port adelaide": "PAD", "port adelaide power": "PAD", "richmond": "RIC",
    "st kilda": "STK", "st. kilda": "STK", "sydney": "SYD", "sydney swans": "SYD",
    "west coast": "WCE", "west coast eagles": "WCE", "western bulldogs": "WBD", "footscray": "FOO",
}
# AFL Tables team slugs (stats and season pages).
AT_SLUG = {
    "adelaide": "ADE", "brisbaneb": "BRB", "brisbanel": "BRL", "carlton": "CAR",
    "collingwood": "COL", "essendon": "ESS", "fitzroy": "FIT", "fremantle": "FRE",
    "geelong": "GEE", "hawthorn": "HAW", "melbourne": "MEL", "kangaroos": "NTH",
    "padelaide": "PAD", "richmond": "RIC", "stkilda": "STK", "swans": "SYD",
    "westcoast": "WCE", "bullldogs": "WBD", "bulldogs": "WBD",
}
SQUIGGLE = {
    "Adelaide": "ADE", "Brisbane Lions": "BRL", "Brisbane Bears": "BRB", "Carlton": "CAR",
    "Collingwood": "COL", "Essendon": "ESS", "Fitzroy": "FIT", "Fremantle": "FRE",
    "Geelong": "GEE", "Hawthorn": "HAW", "Melbourne": "MEL", "North Melbourne": "NTH",
    "Port Adelaide": "PAD", "Richmond": "RIC", "St Kilda": "STK", "Sydney": "SYD",
    "West Coast": "WCE", "Western Bulldogs": "WBD", "Footscray": "FOO",
}


def era(code: str, season: int | None) -> str:
    """The code for the name club `code` played under in `season`."""
    if not code or season is None:
        return code
    if code in ("BRL", "BRB"):
        return "BRB" if season <= 1996 else "BRL"
    if code in ("WBD", "FOO"):
        return "FOO" if season <= 1996 else "WBD"
    return code


def base(code: str) -> str:
    return {"BRB": "BRL", "FOO": "WBD"}.get(code, code)


def club_code(name: str, season: int | None = None) -> str:
    n = re.sub(r"\s+", " ", html.unescape(name)).strip().lower()
    n = re.sub(r" (football club|fc)$", "", n)
    return era(NAME.get(n, ""), season)


def text(fragment: str) -> str:
    s = re.sub(r"<[^>]+>", " ", fragment)
    s = html.unescape(s).replace("​", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def read(cache: str, url: str) -> str:
    p = cache_path(cache, url)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def split_name(full: str) -> tuple[str, str]:
    parts = full.split(" ", 1)
    return (parts[0], parts[1] if len(parts) > 1 else "")


def write(name: str, fields: list[str], rows: list[dict]) -> None:
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    print(f"{name}: {len(rows)} rows")


# --------------------------------------------------------------- Draftguru lists

LIST_TYPE = {"": "senior", "r": "rookie", "b": "cat_b", "u": "senior", "ru": "rookie"}


def parse_list(body: str) -> list[dict]:
    """One Draftguru club list. Draftguru's first season (1990) has only that
    season's columns; later seasons add prior and career columns."""
    out = []
    for tr in re.findall(r"<tr>\s*<td class=\"number\">.*?</tr>", body, re.S):
        cells = re.findall(r'<td class="([^"]+)"([^>]*)>(.*?)</td>', tr, re.S)
        by = defaultdict(list)
        for cls, attrs, inner in cells:
            key = re.search(r'data-sorttable_customkey="([^"]*)"', attrs)
            by[cls.split()[0]].append((text(inner), key.group(1) if key else ""))
        name_cell = re.search(r'<td class="name".*?<a href="(/players/[^"]+)">(.*?)</a>', tr, re.S)
        lt = by["listtype"][0][0]
        games = [int(k[1] or 0) * -1 if k[1] else 0 for k in by["games"]]
        goals = [int(k[1] or 0) * -1 if k[1] else 0 for k in by["goals"]]
        votes = [int(k[1] or 0) * -1 if k[1] else 0 for k in by["votes"]]
        row = {
            "num": by["number"][0][0],
            "list_code": lt,
            "dg": html.unescape(name_cell.group(1)),
            "name": text(name_cell.group(2)),
            "dob": by["dob"][0][1],
            "height_cm": str(abs(int(by["height"][0][1]))) if by["height"][0][1] not in ("", "0") else "",
            "origin": by["from-club"][0][0] if by["from-club"] else "",
            "first_drafted": by["movement"][0][0] if by["movement"] else "",
        }
        if len(games) >= 3:
            row.update({"games_prior": games[0], "goals_prior": goals[0],
                        "coach_votes_prior": votes[0], "brownlow_votes_prior": votes[1],
                        "games": games[1], "goals": goals[1],
                        "coach_votes": votes[2], "brownlow_votes": votes[3],
                        "games_career": games[2], "goals_career": goals[2]})
        else:  # season-only page: prior and career stay blank
            row.update({"games_prior": "", "goals_prior": "", "games": games[0], "goals": goals[0],
                        "coach_votes": votes[0], "brownlow_votes": votes[1],
                        "games_career": "", "goals_career": ""})
        out.append(row)
    return out


# ------------------------------------------------------------ Draftguru players

EVENT_RE = re.compile(r'<tr class="(year-row|between-years-row)[^"]*">(.*?)</tr>', re.S)


def parse_player(body: str) -> list[tuple]:
    """Ordered ('year', year, club, list) and ('event', text) entries; clubs by era."""
    seq = []
    for kind, inner in EVENT_RE.findall(body):
        if kind == "year-row":
            year = re.search(r'class="year">(\d{4})<', inner)
            club = re.search(r'class="afl-club"[^>]*>(.*?)</td>', inner, re.S)
            lst = re.search(r'class="afl-list"[^>]*>(.*?)</td>', inner, re.S)
            if year:
                y = int(year.group(1))
                seq.append(("year", y, club_code(text(club.group(1)), y) if club else "",
                            text(lst.group(1)) if lst else ""))
        else:
            for ev in re.findall(r"<a [^>]*>(.*?)</a>|<td colspan=\"10\">(.*?)</td>", inner, re.S):
                t = text(ev[0] or ev[1])
                if t:
                    seq.append(("event", t))
    return seq


CLUBS_RE = (r"(Adelaide|Brisbane(?: Lions| Bears)?|Carlton|Collingwood|Essendon|Fremantle|Geelong|"
            r"Hawthorn|Melbourne|North Melbourne|Kangaroos|"
            r"Port Adelaide|Richmond|St Kilda|Sydney|West Coast|Western Bulldogs|Footscray|Fitzroy)")


def same_club(name: str, club: str) -> bool:
    return base(club_code(name)) == base(club)


def classify(event: str, club: str, from_season: int | None = None) -> dict | None:
    """Read one Draftguru movement line. Returns the join it records for club, if any."""
    event = re.sub(r"^\([^)]*\)\s*", "", event)
    m = re.match(rf"Drafted by {CLUBS_RE} with (.+?) pick #(\d+)", event)
    if m and same_club(m.group(1), club):
        kind = m.group(2).lower().replace("-", "_").replace(" draft", "").replace(" ", "_")
        return {"joined_how": f"{kind}_draft", "joined_pick": m.group(3), "joined_detail": event}
    m = re.match(rf"Traded from {CLUBS_RE} to {CLUBS_RE}", event)
    if m and same_club(m.group(2), club):
        return {"joined_how": "trade", "joined_from": club_code(m.group(1), from_season), "joined_detail": event}
    m = re.match(rf"(Restricted |Unrestricted |Delisted )?Free Agent from {CLUBS_RE} to {CLUBS_RE}", event)
    if m and same_club(m.group(3), club):
        sub = (m.group(1) or "").strip().lower()
        return {"joined_how": "free_agent" + (f"_{sub}" if sub else ""),
                "joined_from": club_code(m.group(2), from_season), "joined_detail": event}
    m = re.search(rf"(?:by|to) {CLUBS_RE}\b", event)
    if m and same_club(m.group(1), club) and not event.startswith(("Delisted", "Retired")):
        return {"joined_how": "signed", "joined_detail": event}
    return None


def join_for(seq: list[tuple], club: str, season: int) -> dict:
    """How the player came to `club` for the stint that includes `season`.

    As in the 2010s build. A stint runs through a club's change of name
    (Brisbane Bears to Lions, Footscray to Western Bulldogs): the same base club.
    """
    years = [(i, it[1], it[2]) for i, it in enumerate(seq) if it[0] == "year"]
    pos = [k for k, (_, y, _) in enumerate(years) if y == season]
    if not pos:
        return {}
    k = pos[0]
    if years[k][2] != club:
        return {}
    while k > 0 and base(years[k - 1][2]) == base(club) and years[k - 1][1] == years[k][1] - 1:
        k -= 1
    start_idx, start_year = years[k][0], years[k][1]
    prev_idx = years[k - 1][0] if k > 0 else -1
    events = [it[1] for it in seq[prev_idx + 1:start_idx] if it[0] == "event"]
    best = None
    for ev in events:
        j = classify(ev, club, start_year - 1)
        if j and j["joined_how"] != "signed":
            best = j
    if not best:
        for ev in events:
            j = classify(ev, club, start_year - 1)
            if j:
                best = j
        if not best:
            loose = [ev for ev in events if not ev.startswith(("Delisted", "Retired")) or ev == "Delisted Free Agent"]
            if loose:
                ev = loose[-1]
                how = ("free_agent_delisted" if ev == "Delisted Free Agent"
                       else "supplemental_selection" if "Supplemental" in ev
                       else "supplementary" if "Supplementary" in ev
                       else "zone" if "Zone" in ev else "underage_concession" if "Underage" in ev
                       else "uncontracted_concession" if "Uncontracted" in ev
                       else "father_son" if "Father-Son" in ev else "international" if "International" in ev
                       else "category_b" if ("Unregistered" in ev or "Recruit" in ev)
                       else "top_up" if "Top-Up" in ev else "foundation" if "Foundation" in ev
                       else "compensation" if "Compensation" in ev
                       else "prelisting" if "Prelisting" in ev else "concession" if "Concession" in ev
                       else "signed")
                best = {"joined_how": how, "joined_detail": ev}
    if best:
        best = dict(best)
        best["joined_year"] = start_year - 1
        if best["joined_how"] in ("trade",) or best["joined_how"].startswith("free_agent"):
            prior = [c for (_, y, c) in years[:k] if c]
            if prior and not best.get("joined_from"):
                best["joined_from"] = prior[-1]
        return best
    # No joining line (Draftguru records none for most moves before the 1986
    # National Draft). The year rows still show when the stint began and, for a
    # player who came from another club, which one; how he came stays blank.
    out = {"joined_year": start_year - 1}
    prior = [c for (_, y, c) in years[:k] if c]
    if prior:
        out["joined_from"] = prior[-1]
    return out


# ----------------------------------------------------------------- AFL Tables

AT_COLS = ["gm", "ki", "mk", "hb", "di", "da", "gl", "bh", "ho", "tk", "rb", "if50", "cl", "cg",
           "ff", "fa", "br", "cp", "up", "cm", "mi", "one_pct", "bo", "ga", "pct_played"]


def at_code(slug: str, season: int) -> str:
    return era(AT_SLUG.get(slug, ""), season)


def parse_afltables_season(body: str, season: int) -> list[dict]:
    """AFL Tables season stats. Columns the 1990s did not record (CP, UP, CM,
    MI, 1%, BO, GA, %P and some others in early years) are blank, not zero."""
    out = []
    for table in re.findall(r'<table[^>]*class="sortable".*?</table>', body, re.S):
        team = re.search(r'href="\.\./teams/([a-z]+)_idx\.html"', table)
        if not team:
            continue
        code = at_code(team.group(1), season)
        for tr in re.findall(r"<tr>(.*?)</tr>", table, re.S):
            link = re.search(r'href="(players/[^"]+\.html)">([^<]+)</a>', tr)
            if not link:
                continue
            cells = [text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            last, _, first = link.group(2).partition(", ")
            row = {"club": code, "num": cells[0], "first": first.strip(), "last": last.strip(),
                   "afltables_id": link.group(1)}
            for col, val in zip(AT_COLS, cells[2:]):
                row[col] = val
            out.append(row)
    return out


def parse_bio(body: str) -> dict:
    t = text(body)
    h = re.search(r"Height:\s*(\d+)\s*cm", t)
    w = re.search(r"Weight:\s*(\d+)\s*kg", t)
    return {"height": h.group(1) if h else "", "weight": w.group(1) if w else ""}


def norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", html.unescape(s).lower())


# ----------------------------------------------------------------- builders


def build_lists(cache: str) -> list[dict]:
    rows = []
    at_by_season = {y: parse_afltables_season(read(cache, f"https://afltables.com/afl/stats/{y}.html"), y)
                    for y in SEASONS}
    player_cache: dict[str, list] = {}
    bio_cache: dict[str, dict] = {}
    for y in SEASONS:
        at = at_by_season[y]
        for slug in club_slugs(y):
            club = era(SLUG[slug], y)
            url = f"{DG}/lists/{y}/{slug}"
            for p in parse_list(read(cache, url)):
                first, last = split_name(p["name"])
                lt = p["list_code"]
                row = {
                    "year": y, "club": club, "num": p["num"], "first": first, "last": last,
                    "list": LIST_TYPE.get(lt, lt), "underage": "yes" if "u" in lt else "",
                    "dob": p["dob"], "height_cm": p["height_cm"],
                    "games": p["games"], "goals": p["goals"],
                    "coach_votes": p["coach_votes"], "brownlow_votes": p["brownlow_votes"],
                    "games_prior": p["games_prior"], "goals_prior": p["goals_prior"],
                    "games_career": p["games_career"], "goals_career": p["goals_career"],
                    "origin": p["origin"], "first_drafted": p["first_drafted"],
                    "draftguru_id": p["dg"],
                }
                if p["dg"] not in player_cache:
                    player_cache[p["dg"]] = parse_player(read(cache, DG + p["dg"]))
                seq = player_cache[p["dg"]]
                row.update(join_for(seq, club, y))
                prev = [s for s in seq if s[0] == "year" and s[1] == y - 1]
                if prev and base(prev[0][2]) == base(club) and prev[0][3].startswith("rookie") \
                        and row["list"] == "senior":
                    row["elevated_from_rookie"] = y
                cand = [a for a in at if a["club"] == club and norm(a["last"]) == norm(last)]
                hit = [a for a in cand if norm(a["first"]) == norm(first)] or \
                      [a for a in cand if a["num"] == p["num"]]
                if len(hit) == 1:
                    aid = hit[0]["afltables_id"]
                    row["afltables_id"] = aid
                    if aid not in bio_cache:
                        bio_cache[aid] = parse_bio(read(cache, "https://afltables.com/afl/stats/" + aid))
                    row["weight_kg"] = bio_cache[aid]["weight"]
                row["source_url"] = f"{url} | https://afltables.com/afl/stats/{y}.html"
                row["checked"] = CHECKED
                rows.append(row)
    return rows


def build_season_stats(cache: str) -> list[dict]:
    rows = []
    for y in SEASONS:
        for r in parse_afltables_season(read(cache, f"https://afltables.com/afl/stats/{y}.html"), y):
            r["year"] = y
            r["source_url"] = f"https://afltables.com/afl/stats/{y}.html"
            r["checked"] = CHECKED
            rows.append(r)
    return rows


def parse_years_page(body: str, club_season: int) -> list[dict]:
    out = []
    for tr in re.findall(r'<tr class="outcome[^"]*">(.*?)</tr>', body, re.S):
        cells = re.findall(r'<td class="([^"]+)"[^>]*>(.*?)</td>', tr, re.S)
        cats = [text(v) for k, v in cells if k == "category"]
        get = {k.split()[-1] if k.startswith("stats") else k: v for k, v in cells}
        player = re.search(r'<a href="(/players/[^"]+)">(.*?)</a>', get.get("player", ""), re.S)
        out.append({
            "draft": text(get.get("draft", "")),
            "pick": text(get.get("number", "")),
            "club": club_code(text(get.get("club", "")), club_season),
            "signing": cats[1] if len(cats) > 1 else "",
            "dg": html.unescape(player.group(1)) if player else "",
            "name": text(player.group(2)) if player else text(get.get("player", "")),
            "origin": text(get.get("from-club", "")),
        })
    return out


DRAFT_KIND = {"National": "national", "Pre-Season": "preseason", "Rookie": "rookie",
              "Mini-Draft": "mini", "Pre-Draft": "pre_draft_signing", "Post-Draft": "post_draft_signing",
              "Mid-Season": "mid_season", "Training Squad Selection": "training_squad"}


def flag_of(signing: str) -> str:
    s = signing.lower()
    if s.startswith("father-son"):
        return "father_son"
    if s.startswith("academy (ng)"):
        return "next_generation_academy"
    if s.startswith("academy"):
        return "academy"
    if s.startswith("zone"):
        return "zone"
    for key, val in (("underage", "underage_concession"), ("uncontracted", "uncontracted_concession"),
                     ("concession", "concession"), ("intl schol", "international_scholarship"),
                     ("international", "international"), ("scholarship", "scholarship"),
                     ("unregistered", "unregistered"), ("special cat b", "category_b"),
                     ("top-up", "top_up"), ("ssp", "supplemental_selection"),
                     ("foundation", "foundation"), ("supplementary", "supplementary"),
                     ("compensation", "compensation"),
                     ("fa (", "free_agent"), ("dfa", "delisted_free_agent")):
        if s.startswith(key):
            return val
    return ""


def wiki_sections(cache: str, page_year: int) -> list[tuple[str, str, dict]]:
    """[(kind, heading id, {pick: record})] for every draft table on one Wikipedia page."""
    body = read(cache, wiki_draft_url(page_year))
    # Parsoid HTML carries JSON in attributes and CSS blocks; drop them first.
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    body = re.sub(r"\sdata-mw='[^']*'|\sdata-mw=\"[^\"]*\"|\stitle=\"[^\"]*\"", "", body)
    out = []
    current, hid, last_kind = None, "", None
    for part in re.split(r'(<h[234][^>]*id="[^"]+")', body):
        h = re.match(r'<h[234][^>]*id="([^"]+)"', part)
        if h:
            hid = h.group(1).lower()
            current = ("national" if "national_draft" in hid
                       else "preseason" if ("pre-season_draft" in hid or "preseason_draft" in hid)
                       else "rookie" if "rookie_draft" in hid else "mini" if "mini-draft" in hid
                       else "mid_season" if "mid-season_draft" in hid
                       # 1992: the national draft's table sits under a "Selections"
                       # subheading after a "Draft tampering" section.
                       else last_kind if hid == "selections" else None)
            last_kind = current or last_kind
            continue
        if not current:
            continue
        picks = {}
        for table in re.findall(r'<table class="[^"]*wikitable.*?</table>', part, re.S):
            trs = re.findall(r"<tr.*?</tr>", table, re.S)
            if not trs:
                continue
            cols = []
            for attrs, c in re.findall(r"<th([^>]*)>(.*?)</th>", trs[0], re.S):
                c = text(c).lower()
                span = re.search(r'colspan="?(\d+)', attrs)
                name = ("round" if ("round" in c or c in ("rd.", "rd")) else "pick" if c in ("pick", "#", "no.") or "pick" in c
                        else "player" if "player" in c or c == "name"
                        else "club" if ("drafted to" in c or c == "club" or "recruited to" in c
                                        or "recruited by" in c or c == "new club")
                        else "notes" if "note" in c else c)
                cols.append(name)
                cols.extend(f"{name}_{i}" for i in range(1, int(span.group(1)) if span else 1))
            if "pick" not in cols or "player" not in cols or "points" in cols:
                continue
            last_round = ""
            for tr in trs[1:]:
                if "<td" not in tr:
                    continue
                cells = [text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
                row_cols = cols
                if "round" in cols and len(cells) == len(cols) - 1:
                    row_cols = [c for c in cols if c != "round"]  # round cell spans rows
                rec = dict(zip(row_cols, cells))
                if "round" in rec and rec["round"]:
                    last_round = rec["round"]
                # 1999 marks a father-son pick in the pick cell: "18 (F/S)".
                m = re.match(r"(\d+)\s*(\(\s*F/S\s*\))?$", rec.get("pick", ""))
                if not m:
                    continue
                pick = m.group(1)
                note = rec.get("notes", "") + (" father-son (F/S)" if m.group(2) else "")
                player = rec.get("player", "")
                picks[int(pick)] = {"round": rec.get("round", last_round), "note": note.strip(),
                                    "player": player, "passed": player.lower().startswith("pass"),
                                    "club_name": rec.get("club", "")}
        if picks:
            out.append((current, hid, picks))
    return out


def wiki_drafts(cache: str, year: int) -> dict:
    """{(kind, pick): {...}} from Wikipedia for Draftguru's draft year `year`.

    The year's page holds the National Draft and the pre-season (and from 1996
    rookie) draft that followed it. The mid-season draft for this year is the
    one held in the middle of year+1, named for year+1: it sits on the year+1
    page (and, for 1990, also on the 1989 page); the first copy found is used.
    """
    out = {}
    for kind, hid, picks in wiki_sections(cache, year):
        if kind == "mid_season":
            continue
        for pick, w in picks.items():
            out[(kind, pick)] = dict(w, club=club_code(w["club_name"], year + 1))
    for page_year in (year, year + 1):
        mids = [p for kind, hid, p in wiki_sections(cache, page_year)
                if kind == "mid_season" and hid.startswith(str(year + 1))]
        if mids:
            for pick, w in mids[0].items():
                out[("mid_season", pick)] = dict(w, club=club_code(w["club_name"], year + 1))
            break
    counts = defaultdict(int)
    for (kind, _), v in out.items():
        if not v["passed"] and v["player"]:
            counts[kind] += 1
    return {"picks": out, "counts": dict(counts)}


def wiki_flag(note: str) -> str:
    n = note.lower()
    for key, val in (("father", "father_son"), ("zone", "zone"), ("priority", "priority"),
                     ("compensation", "compensation"), ("concession", "concession")):
        if key in n:
            return val
    return ""


def build_drafts(cache: str) -> tuple[list[dict], dict]:
    rows = []
    wiki_counts = {}
    for y in DRAFT_YEARS:
        url = f"{DG}/years/{y}"
        wurl = wiki_draft_url(y)
        wk = wiki_drafts(cache, y)
        wiki_counts[y] = wk["counts"]
        for r in parse_years_page(read(cache, url), y + 1):
            if r["draft"] in ("Trade", "Free Agency"):
                continue
            kind = DRAFT_KIND.get(r["draft"], r["draft"].lower())
            first, last = split_name(r["name"])
            pick = int(r["pick"]) if r["pick"].isdigit() else None
            w = wk["picks"].get((kind, pick), {}) if pick else {}
            flag = flag_of(r["signing"]) or wiki_flag(w.get("note", ""))
            # Draftguru prints a 1997-1998 father-son pick's category as the
            # father's name alone (no "Father-Son(...)" wrapper).
            if not flag and r["signing"] and re.fullmatch(r"[A-Z][\w'.-]+(?: [A-Z][\w'.-]+)+", r["signing"]):
                flag = "father_son"
            rows.append({
                "year": y, "draft": kind, "round": re.sub(r"\D", "", w.get("round", "")), "pick": r["pick"],
                "club": r["club"], "first": first, "last": last, "origin": r["origin"],
                "flag": flag, "flag_detail": r["signing"], "wiki_note": w.get("note", ""),
                "wiki_player": "" if w.get("passed") else w.get("player", ""),
                "draftguru_id": r["dg"],
                "source_url": f"{url} | {wurl}",
                "checked": CHECKED,
            })
        seen = {(r["draft"], int(r["pick"])) for r in rows if r["year"] == y and r["pick"].isdigit()}
        for (kind, pick), w in sorted(wk["picks"].items(), key=lambda kv: (kv[0][0], kv[0][1])):
            if w["passed"] or not w["player"] or (kind, pick) in seen:
                continue
            first, last = split_name(re.sub(r"\s+[\^*+x†‡#]+$", "", w["player"]).strip())
            # Same player at another number (Draftguru numbers some drafts
            # without passes): Draftguru's row already holds him.
            if any(r["year"] == y and r["draft"] == kind and norm(r["last"]) == norm(last)
                   and norm(r["first"])[:3] == norm(first)[:3] for r in rows):
                key = f"{kind}_listed_elsewhere"
                wiki_counts[y][key] = wiki_counts[y].get(key, 0) + 1
                continue
            rows.append({
                "year": y, "draft": kind, "round": re.sub(r"\D", "", w.get("round", "")), "pick": pick,
                "club": w["club"], "first": first, "last": last, "origin": "",
                "flag": wiki_flag(w["note"]), "flag_detail": "",
                "wiki_note": w["note"], "draftguru_id": "", "only_in": "wikipedia",
                "source_url": wurl, "checked": CHECKED,
            })
    return rows, wiki_counts


def build_moves(cache: str, lists: list[dict]) -> list[dict]:
    """Trades (no free agency until 2012) and uncontracted concession signings.

    A move in year Y is in the off-season after season Y: from_club takes its
    season-Y name, to_club its season-Y+1 name.
    """
    dobs = {r["draftguru_id"]: r["dob"] for r in lists if r["dob"]}
    rows = []
    for y in DRAFT_YEARS:
        url = f"{DG}/years/{y}"
        for r in parse_years_page(read(cache, url), y + 1):
            if r["draft"] not in ("Trade", "Free Agency") and flag_of(r["signing"]) != "uncontracted_concession":
                continue
            seq = parse_player(read(cache, DG + r["dg"])) if r["dg"] else []
            j = {}
            year_now = None
            for item in seq:
                if item[0] == "year":
                    year_now = item[1]
                    continue
                if year_now == y:
                    c = classify(item[1], r["club"], y)
                    if c:
                        j = c
            if not j.get("joined_from"):
                at_y = [it[2] for it in seq if it[0] == "year" and it[1] == y and it[2]]
                if at_y and base(at_y[-1]) != base(r["club"]):
                    j = dict(j, joined_from=at_y[-1])
            first, last = split_name(r["name"])
            kind = "traded" if r["draft"] == "Trade" else "uncontracted_concession"
            rows.append({
                "year": y, "first": first, "last": last, "dob": dobs.get(r["dg"], ""), "compensation": "",
                "from_club": j.get("joined_from", ""), "to_club": r["club"], "kind": kind,
                "detail": j.get("joined_detail", ""), "draftguru_id": r["dg"],
                "source_url": f"{url} | {wiki_draft_url(y)}",
                "checked": CHECKED,
            })
    return rows


def afltables_ladder(cache: str, y: int) -> list[dict]:
    """Final home-and-away ladder (the table under the season page's "lad" anchor)."""
    body = read(cache, f"https://afltables.com/afl/seas/{y}.html")
    i = body.find('<a name="lad">')
    table = re.search(r"<table.*?</table>", body[i:], re.S) if i >= 0 else None
    out = []
    for tr in re.findall(r"<tr.*?</tr>", table.group(0) if table else "", re.S):
        cells = [text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        slug = re.search(r'teams/([a-z]+)_idx', tr)
        if len(cells) < 14 or not cells[0].isdigit() or not slug:
            continue
        out.append({"pos": int(cells[0]), "club": at_code(slug.group(1), y), "p": cells[2],
                    "w": cells[3], "d": cells[4] or "0", "l": cells[5], "pct": cells[12], "pts": cells[13]})
    return out


def afltables_finals(cache: str, y: int) -> dict:
    """{club: finals result} from the Finals section of AFL Tables' season page.

    A club's result is where its season ended: premiers, runners_up, or the
    final it last lost (elim for a week-one exit, semi, prelim). A drawn final
    (1990 qualifying final) is no loss; the replay decides.
    """
    body = read(cache, f"https://afltables.com/afl/seas/{y}.html")
    i = body.find(">Finals<")
    out: dict[str, str] = {}
    if i < 0:
        return out
    seg = body[i:]
    blocks = re.split(r"(Qualifying Final|Elimination Final|Semi Final|Preliminary Final|Grand Final)", seg)
    for k in range(1, len(blocks) - 1, 2):
        rnd, chunk = blocks[k], blocks[k + 1]
        rows = re.findall(r'teams/([a-z]+)_idx.*?<td width=5% align=center>\s*(\d+)</td>', chunk, re.S)[:2]
        if len(rows) < 2:
            continue
        codes = [at_code(t, y) for t, _ in rows]
        s0, s1 = int(rows[0][1]), int(rows[1][1])
        winner = codes[0] if s0 > s1 else codes[1] if s1 > s0 else ""
        for c in codes:
            out.setdefault(c, "finals")
            if rnd == "Grand Final" and winner:
                out[c] = "premiers" if c == winner else "runners_up"
            elif winner and c != winner:
                out[c] = {"Qualifying Final": "elim", "Elimination Final": "elim",
                          "Semi Final": "semi", "Preliminary Final": "prelim"}[rnd]
    return out


def build_ladders(cache: str) -> list[dict]:
    rows = []
    for y in SEASONS:
        st = json.loads(read(cache, f"https://api.squiggle.com.au/?q=standings;year={y}") or "{}")
        sq = {}
        for s in st.get("standings", []):
            code = SQUIGGLE.get(s["name"], "")
            if s["name"] == "Brisbane Lions" and y <= 1996:
                code = "BRB"  # Squiggle names the Bears by today's club
            sq[era(code, y)] = s
        fin = afltables_finals(cache, y)
        for a in afltables_ladder(cache, y):
            team = a["club"]
            note = ""
            s = sq.get(team)
            if s and (int(a["w"]), int(a["d"]), int(a["l"])) != (s["wins"], s["draws"], s["losses"]):
                note = f"Squiggle W-D-L {s['wins']}-{s['draws']}-{s['losses']}"
            if s and int(a["pts"]) != int(s["pts"]):
                note = (note + "; " if note else "") + f"Squiggle points {s['pts']} (AFL Tables used)"
            if not s:
                note = "not on Squiggle's ladder"
            rows.append({
                "year": y, "pos": a["pos"], "club": team, "w": a["w"], "l": a["l"], "d": a["d"],
                "pts": a["pts"], "pct": a["pct"], "finals": fin.get(team, ""), "note": note,
                "source_url": f"https://afltables.com/afl/seas/{y}.html | https://api.squiggle.com.au/?q=standings;year={y}",
                "checked": CHECKED,
            })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    lists = build_lists(a.cache)
    write("lists.csv", ["year", "club", "num", "first", "last", "list", "underage", "dob", "height_cm",
                        "weight_kg", "position", "games", "goals", "coach_votes", "brownlow_votes",
                        "games_prior", "goals_prior", "games_career", "goals_career", "origin",
                        "first_drafted", "joined_how", "joined_year", "joined_from", "joined_pick",
                        "elevated_from_rookie", "joined_detail", "draftguru_id", "afltables_id",
                        "source_url", "checked"], lists)
    drafts, wiki_counts = build_drafts(a.cache)
    write("drafts.csv", ["year", "draft", "round", "pick", "club", "first", "last", "origin", "flag",
                         "flag_detail", "wiki_note", "wiki_player", "only_in", "draftguru_id", "source_url", "checked"], drafts)
    with open(os.path.join(OUT, "wikipedia_draft_counts.json"), "w", encoding="utf-8") as fh:
        json.dump({str(k): v for k, v in wiki_counts.items()}, fh, indent=1, sort_keys=True)
    write("moves.csv", ["year", "first", "last", "dob", "from_club", "to_club", "kind", "compensation", "detail",
                        "draftguru_id", "source_url", "checked"], build_moves(a.cache, lists))
    write("ladders.csv", ["year", "pos", "club", "w", "l", "d", "pts", "pct", "finals", "note", "source_url",
                          "checked"], build_ladders(a.cache))
    write("season_stats.csv", ["year", "club", "num", "first", "last"] + AT_COLS +
          ["afltables_id", "source_url", "checked"], build_season_stats(a.cache))


if __name__ == "__main__":
    main()
