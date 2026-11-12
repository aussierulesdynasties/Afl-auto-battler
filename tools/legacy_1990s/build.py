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
from fetch import DG, GROUND_ARTICLES, PRE_SEASONS, cache_path, club_slugs, wiki_draft_url  # noqa: E402

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
    write_to(OUT, name, fields, rows)


def write_to(folder: str, name: str, fields: list[str], rows: list[dict]) -> None:
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, name), "w", newline="", encoding="utf-8") as fh:
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
    for y in list(PRE_SEASONS) + list(SEASONS):
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
    """1989 too: its ladder set the order of the drafts that fed the 1990 lists."""
    rows = []
    for y in [FIRST_SEASON - 1] + list(SEASONS):
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


# ------------------------------------------------------------ the 1990 start
#
# What a career that starts in 1990 needs beyond the season files: each 1990
# player's games before 1990, the lists as they stood at the start of 1990, the
# 1990 coaches and captains, the era's rules and its grounds by name.

LEGACY = os.path.dirname(OUT)
WIKI = "https://en.wikipedia.org/wiki/"
FIRST_SEASON = 1990


def parse_bio_seasons(body: str) -> list[dict]:
    """Season-by-season rows (home-and-away and finals together) from the first
    table of an AFL Tables player page: year, team, jumper, games, goals."""
    m = re.search(r'<table class="sortable".*?</table>', body, re.S)
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", m.group(0) if m else "", re.S):
        year = re.search(r'href="\.\./\.\./(\d{4})\.html', tr)
        team = re.search(r'teams/([a-z]+)_idx\.html">([^<]+)</a>', tr)
        if not year or not team:
            continue
        cells = [text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        # Year, Team, #, GM, W-D-L, KI, MK, HB, DI, GL, ...
        y = int(year.group(1))
        out.append({"year": y, "club": at_code(team.group(1), y), "team": team.group(2), "num": cells[2],
                    "games": cells[3] or "0", "goals": cells[9] or "0"})
    return out


def first_season_ids(cache: str, lists: list[dict]) -> dict[int, str]:
    """AFL Tables id for every 1990 list row: from the 1990 stats match the
    lists build made, else the same club, surname and first name (or jumper) in
    the 1987-89 stats, for a player who did not play in 1990."""
    pre = [r for y in PRE_SEASONS
           for r in parse_afltables_season(read(cache, f"https://afltables.com/afl/stats/{y}.html"), y)]
    ids = {}
    for i, r in enumerate(lists):
        if int(r["year"]) != FIRST_SEASON:
            continue
        if r.get("afltables_id"):
            ids[i] = r["afltables_id"]
            continue
        cand = {a["afltables_id"] for a in pre if base(a["club"]) == base(r["club"])
                and norm(a["last"]) == norm(r["last"]) and norm(a["first"]) == norm(r["first"])}
        if len(cand) == 1:
            ids[i] = cand.pop()
    return ids


def build_pre_careers(cache: str, lists: list[dict], ids: dict[int, str]) -> list[dict]:
    rows = []
    for i, aid in sorted(ids.items(), key=lambda kv: kv[1]):
        r = lists[i]
        url = "https://afltables.com/afl/stats/" + aid
        for s in parse_bio_seasons(read(cache, url)):
            if s["year"] >= FIRST_SEASON:
                continue
            rows.append({"afltables_id": aid, "first": r["first"], "last": r["last"], "year": s["year"],
                         "club": s["club"], "team": s["team"], "num": s["num"], "games": s["games"],
                         "goals": s["goals"], "source_url": url, "checked": CHECKED})
    # One row per player-season-team, once even if two 1990 list rows share a bio.
    seen, out = set(), []
    for r in rows:
        k = (r["afltables_id"], r["year"], r["team"])
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def build_opening_lists(cache: str, lists: list[dict], drafts: list[dict], ids: dict[int, str],
                        careers: list[dict]) -> list[dict]:
    """The 1990 lists as they stood before the season: Draftguru's 1990 lists
    hold everyone listed during the season, so the 1990 mid-season draftees
    (Draftguru's draft year 1989, "Mid-Season") come off.

    games_before is the player's VFL games before 1990, from his AFL Tables
    page. A player with no AFL Tables match who joined in 1986 or later and is
    in none of the 1987-89 stats under his name played no VFL game before 1990
    (0, said in before_from); anyone else without a match stays blank."""
    pre_names = {(norm(a["first"]), norm(a["last"])) for y in PRE_SEASONS
                 for a in parse_afltables_season(read(cache, f"https://afltables.com/afl/stats/{y}.html"), y)}
    mid = {d["draftguru_id"] for d in drafts
           if int(d["year"]) == FIRST_SEASON - 1 and d["draft"] == "mid_season" and d["draftguru_id"]}
    before = defaultdict(lambda: [0, 0])
    for c in careers:
        before[c["afltables_id"]][0] += int(c["games"] or 0)
        before[c["afltables_id"]][1] += int(c["goals"] or 0)
    out = []
    for i, r in enumerate(lists):
        if int(r["year"]) != FIRST_SEASON or r["draftguru_id"] in mid:
            continue
        aid = ids.get(i, "")
        g = before.get(aid)
        if aid:
            how = "afltables"
            g = g or [0, 0]
        elif (r.get("joined_year") and int(r["joined_year"]) >= 1986
              and (norm(r["first"]), norm(r["last"])) not in pre_names):
            how, g = "none_1987_89_joined_1986_on", [0, 0]
        else:
            how, g = "", None
        out.append({
            "club": r["club"], "num": r["num"], "first": r["first"], "last": r["last"], "list": r["list"],
            "dob": r["dob"], "height_cm": r["height_cm"], "weight_kg": r.get("weight_kg", ""),
            "games_before": g[0] if g else "", "goals_before": g[1] if g else "", "before_from": how,
            "games_1990": r["games"], "goals_1990": r["goals"],
            "joined_how": r.get("joined_how", ""), "joined_year": r.get("joined_year", ""),
            "joined_from": r.get("joined_from", ""), "origin": r["origin"],
            "draftguru_id": r["draftguru_id"], "afltables_id": aid,
            "source_url": r["source_url"] + (" | https://afltables.com/afl/stats/" + aid if aid else ""),
            "checked": CHECKED,
        })
    return out, len(mid)


def fill_heights(cache: str, lists: list[dict]) -> None:
    """A height Draftguru leaves blank, from the player's AFL Tables page."""
    bio_cache: dict[str, dict] = {}
    for r in lists:
        if r["height_cm"]:
            r["height_from"] = "draftguru"
            continue
        aid = r.get("afltables_id")
        if not aid:
            continue
        if aid not in bio_cache:
            bio_cache[aid] = parse_bio(read(cache, "https://afltables.com/afl/stats/" + aid))
        if bio_cache[aid]["height"]:
            r["height_cm"] = bio_cache[aid]["height"]
            r["height_from"] = "afltables"


def wiki_text(cache: str, page: str) -> str:
    body = read(cache, WIKI + page)
    body = re.sub(r"<style.*?</style>|<script.*?</script>", "", body, flags=re.S)
    return body


def table_rows(fragment: str) -> list[list[str]]:
    # Split at each row's start: AFL Tables leaves some header rows unclosed.
    return [[text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
            for tr in re.split(r"<tr[^>]*>", fragment)[1:]]


def leadership_1990(cache: str) -> list[tuple[str, str, str]]:
    """(club code, coaches cell, leadership cell) from the "Club leadership"
    table of Wikipedia's 1990 AFL season page."""
    body = wiki_text(cache, "1990_AFL_season")
    i = body.find('id="Club_leadership"')
    seg = re.search(r"<table.*?</table>", body[i:], re.S) if i >= 0 else None
    out = []
    for cells in table_rows(seg.group(0) if seg else ""):
        code = club_code(cells[0], FIRST_SEASON) if cells else ""
        if code and len(cells) >= 6:
            out.append((code, cells[1], cells[5]))
    return out


def roles(cell: str) -> list[tuple[str, str]]:
    """'Tony Shaw (captain) Peter Daicos (v/captain) A, B (deputy v/captains)'
    -> [(name, role)], one per person."""
    out = []
    for names, role in re.findall(r"\s*([^()]+?)\s*\(([^)]+)\)", cell):
        for n in re.split(r",\s*| and ", names):
            if n.strip():
                out.append((n.strip(), role.strip()))
    return out


ROLE = {"senior": "senior", "reserves": "reserves", "under 19s": "under_19s",
        "reserves & under 19s": "reserves_and_under_19s", "captain": "captain",
        "v/captain": "vice_captain", "deputy v/c": "deputy_vice_captain",
        "deputy v/captains": "deputy_vice_captain"}
COACH_PAGE = {"BRB": "brisbaneb", "CAR": "carlton", "COL": "collingwood", "ESS": "essendon",
              "FIT": "fitzroy", "FOO": "bullldogs", "GEE": "geelong", "HAW": "hawthorn",
              "MEL": "melbourne", "NTH": "kangaroos", "RIC": "richmond", "STK": "stkilda",
              "SYD": "swans", "WCE": "westcoast"}


def afltables_coaches(cache: str, code: str) -> list[tuple[str, int, int]]:
    """[(coach 'First Last', first season, last season)] from AFL Tables' club coaches page."""
    body = read(cache, f"https://afltables.com/afl/stats/coaches/{COACH_PAGE[code]}.html")
    out = []
    for cells in table_rows(body):
        if len(cells) > 2 and ", " in cells[0]:
            m = re.match(r"(\d{4})(?:-(\d{4}))?$", cells[1])
            if m:
                last, _, first = cells[0].partition(", ")
                out.append((f"{first} {last}", int(m.group(1)), int(m.group(2) or m.group(1))))
    return out


def build_coaches(cache: str) -> list[dict]:
    rows = []
    src = WIKI + "1990_AFL_season#Club_leadership"
    for code, coaches, _ in leadership_1990(cache):
        at = [(n, a, b) for n, a, b in afltables_coaches(cache, code) if a <= FIRST_SEASON <= b]
        for name, role in roles(coaches):
            r = ROLE.get(role.lower(), role.lower())
            note = ""
            if r == "senior":
                # AFL Tables gives each coach's first and last season at the
                # club, so a span is checked by surname (Col/Colin, Mick/Michael).
                surname = norm(name.split(" ", 1)[-1])
                hit = [n for n, _, _ in at if norm(n.split(" ", 1)[-1]) == surname]
                others = [f"{n} {a}-{b}" for n, a, b in at if norm(n.split(" ", 1)[-1]) != surname]
                note = ("NOT on AFL Tables' coaches for 1990" if not hit
                        else "AFL Tables: coached the club across 1990")
                if others:
                    note += "; AFL Tables spans that also cover 1990: " + ", ".join(others)
            rows.append({"club": code, "role": r, "name": name, "note": note,
                         "source_url": src + (f" | https://afltables.com/afl/stats/coaches/{COACH_PAGE[code]}.html"
                                              if r == "senior" else ""),
                         "checked": CHECKED})
    return rows


def build_captains(cache: str, opening: list[dict]) -> list[dict]:
    rows = []
    for code, _, leaders in leadership_1990(cache):
        for name, role in roles(leaders):
            first, last = split_name(name)
            on = [o for o in opening if o["club"] == code and norm(o["last"]) == norm(last)
                  and norm(o["first"])[:3] == norm(first)[:3]]
            rows.append({"club": code, "role": ROLE.get(role.lower(), role.lower()), "first": first, "last": last,
                         "draftguru_id": on[0]["draftguru_id"] if len(on) == 1 else "",
                         "source_url": WIKI + "1990_AFL_season#Club_leadership", "checked": CHECKED})
    return rows


AR06 = "https://footyindustry.com/docs/AFL%202006%20Annual%20report.pdf"
AR10 = "https://footyindustry.com/docs/AFL%202010%20Annual%20Report.pdf"
AR11 = "https://footyindustry.com/docs/AFL%202011%20Annual%20Report.pdf"
AR19 = "https://footyindustry.com/docs/AFL%202019%20Annual%20Report.pdf"
AR21 = "https://footyindustry.com/docs/AFL%202021%20Annual%20Report.pdf"
# Trove's newspaper article pages carry the article's own (OCR) text.
TROVE = "https://trove.nla.gov.au/newspaper/article/{}"
# Macdonald & Borland, "Professional Sports Competitions in Australia", in Fort &
# Fizel (eds), International Sports Economics Comparisons (2004), p. 304, Table 2
# "Australian Football League Player Payments, 1992-2003": Google Books' snippet
# of its season header and its TPP per Club row, one column a season from 1992.
GBOOK_TPP = ("https://books.google.com.au/books?id=QFDeEAAAQBAJ&newbks=0&hl=en"
             "&q=%221992-2003+1992+1993+1994%22+%22TPP+per+Club%22")
# Era rules. Every value is a statement on the page quoted beside it, checked by
# hand on CHECKED; a year no statement covers stays out (the game decides what
# a missing year means). from_year..to_year is the span the statement covers.
ERA_RULES = [
    # rule, value, from, to, source page, the words that say it
    ("salary_cap", 1250000, 1987, 1989, "AFL_salary_cap",
     "The cap was set at some number A$ 1.25 million ... for 1987-1989 as per VFL agreement"),
    ("salary_floor", 1125000, 1987, 1989, "AFL_salary_cap",
     "with the salary floor set at 90% of the cap or $1.125 million"),
    ("salary_cap", 1600000, 1991, 1991, "Australian_Football_League",
     "Evolution of competition table: 1991 Victoria South Australia West Australia New South Wales Queensland $1,600,000"),
    # Salary caps 1990 and 1997-2012, per club in dollars of the time. Before 1999
    # the base cap; from 1999 Total Player Payments (TPP). The annual reports'
    # ten-year tables give TPP per club in $m: the AFL 2006 report's row for
    # 1997-2006 and the AFL 2010 report's for 2001-2010 (pdftotext puts that row
    # beside the next row's label). A quote starts at its own year's figure.
    ("salary_cap", 1500000, 1990, 1990, "https://www.afl.com.au/news/96194/an-ever-changing-game",
     "Back in 1990 players were paid ... The then $1.5 million salary cap"),
    # 1993, 1995 and 1996 from the Canberra Times: the AFL's own reports of
    # those years (scanned) give no per-club cap but 1996's. 1992 and 1994 from
    # Macdonald & Borland's table (its row also gives 1993 $1.747m and 1995 $2.300m,
    # agreeing with the Canberra Times, and 1996 $2.500m against its $2.55m).
    ("salary_cap", 1600000, 1992, 1992, GBOOK_TPP,
     "1992-2003 1992 1993 1994 1995 Season ... TPP per Club $ 1.600 m $ 1.747 m $ 1.847 m"),
    ("salary_cap", 1750000, 1993, 1993, TROVE.format(118214696),
     "after making it to last year's grand final ... the Blues had voluntarily disclosed they had exceeded the salary cap limit of $1.75 million"),
    ("salary_cap", 1847000, 1994, 1994, GBOOK_TPP,
     "1992-2003 1992 1993 1994 1995 Season ... TPP per Club $ 1.600 m $ 1.747 m $ 1.847 m"),
    ("salary_cap", 2330000, 1995, 1995, TROVE.format(130564397),
     "The commission also agreed to an increase in the salary cap next year from $2.33 million to $2.55 million"),
    ("salary_cap", 2550000, 1996, 1996, TROVE.format(130564397),
     "The commission also agreed to an increase in the salary cap next year from $2.33 million to $2.55 million"),
    ("salary_cap", 2900000, 1997, 1997, AR06,
     "TPP per club from 1997 ($m): 2.900 3.275 4.250 4.750 5.188"),
    ("salary_cap", 3275000, 1998, 1998, AR06,
     "TPP per club from 1998 ($m): 3.275 4.250 4.750 5.188 5.563"),
    ("salary_cap", 4250000, 1999, 1999, AR06,
     "TPP per club from 1999 ($m): 4.250 4.750 5.188 5.563 5.938"),
    ("salary_cap", 4750000, 2000, 2000, AR06,
     "TPP per club from 2000 ($m): 4.750 5.188 5.563 5.938 6.116"),
    ("salary_cap", 5188000, 2001, 2001, AR10,
     "TPP per club from 2001 ($m): 5.188 5.563 5.938 6.116 6.301"),
    ("salary_cap", 5563000, 2002, 2002, AR10,
     "TPP per club from 2002 ($m): 5.563 5.938 6.116 6.301 6.473"),
    ("salary_cap", 5938000, 2003, 2003, AR10,
     "TPP per club from 2003 ($m): 5.938 6.116 6.301 6.473 6.944"),
    ("salary_cap", 6116000, 2004, 2004, AR10,
     "TPP per club from 2004 ($m): 6.116 6.301 6.473 6.944 7.431"),
    ("salary_cap", 6301000, 2005, 2005, AR10,
     "TPP per club from 2005 ($m): 6.301 6.473 6.944 7.431 7.694"),
    ("salary_cap", 6473000, 2006, 2006, AR10,
     "TPP per club from 2006 ($m): 6.473 6.944 7.431 7.694 7.950"),
    ("salary_cap", 6944000, 2007, 2007, AR10,
     "TPP per club from 2007 ($m): 6.944 7.431 7.694 7.950"),
    ("salary_cap", 7431000, 2008, 2008, AR10,
     "TPP per club from 2008 ($m): 7.431 7.694 7.950"),
    ("salary_cap", 7694000, 2009, 2009, AR10,
     "TPP per club from 2009 ($m): 7.694 7.950"),
    ("salary_cap", 7950000, 2010, 2010, AR10,
     "TPP per club from 2010 ($m): 7.950"),
    ("salary_cap", 8210000, 2011, 2011, AR11, "2011 - $8.21 million a club (final year of current agreement)"),
    ("salary_cap", 8787000, 2012, 2012, AR11, "2012 - $8.787 million a club (seven per cent increase)"),
    ("salary_cap", 9130000, 2013, 2013, "Australian_Football_League",
     "this was $9,130,000 for the 2013 season with a salary floor of $8,673,500"),
    ("salary_floor", 8673500, 2013, 2013, "Australian_Football_League",
     "this was $9,130,000 for the 2013 season with a salary floor of $8,673,500"),
    # 2014 and 2017-2021: TPP per club ($m) rows of the AFL 2019 report
    # (2010-2019) and the AFL 2021 report (to 2021; 2020 is the COVID cut).
    ("salary_cap", 9632000, 2014, 2014, AR19,
     "TPP per club from 2014 ($m): 9.632 10.071 10.369 12.445 12.594 12.758"),
    ("salary_cap", 12445000, 2017, 2017, AR19, "TPP per club from 2017 ($m): 12.445 12.594 12.758"),
    ("salary_cap", 12594000, 2018, 2018, AR19, "TPP per club from 2018 ($m): 12.594 12.758"),
    ("salary_cap", 12758000, 2019, 2019, AR19, "TPP per club from 2019 ($m): 12.758"),
    ("salary_cap", 9056000, 2020, 2020, AR21, "TPP per club from 2020 ($m): 9.056 12.071"),
    ("salary_cap", 12071000, 2021, 2021, AR21, "TPP per club from 2021 ($m): 12.071"),
    ("salary_cap", 10070000, 2015, 2015, "Australian_Football_League",
     "increasing from $9.92m to $10.07m in 2015 and $10.22m to $10.37m in 2016"),
    ("salary_cap", 10370000, 2016, 2016, "Australian_Football_League",
     "increasing from $9.92m to $10.07m in 2015 and $10.22m to $10.37m in 2016"),
    ("salary_cap", 13540000, 2022, 2022, "AFL_salary_cap",
     "was A$13,540,000 for the 2022 season, with a salary floor of $12,863,000"),
    ("salary_floor", 12863000, 2022, 2022, "AFL_salary_cap",
     "was A$13,540,000 for the 2022 season, with a salary floor of $12,863,000"),
    ("salary_cap", 15022778, 2023, 2023, "AFL_salary_cap",
     "the aggregate Total Player Payment (TPP) figure was set in 2023 at $15,022,778"),
    ("salary_floor_pct", 90, 1987, 2000, "AFL_salary_cap",
     "salary floor set at 90% of the cap ... increased to 92.5% of the cap in 2001"),
    ("salary_floor_pct", 92.5, 2001, 2012, "AFL_salary_cap",
     "the salary floor was increased to 92.5% of the cap in 2001, and to 95% of the cap for 2013 onwards"),
    ("salary_floor_pct", 95, 2013, 2026, "AFL_salary_cap", "and to 95% of the cap for 2013 onwards"),
    ("senior_list_max", 52, 1993, 1993, "Rookie_list",
     "the reduction in size of AFL lists from 52 to 42 players in 1994"),
    ("senior_list_max", 42, 1994, 1994, "Rookie_list",
     "the reduction in size of AFL lists from 52 to 42 players in 1994"),
    ("rookie_list", 1, 1997, 2026, "Rookie_list", "The rookie list was established in 1997"),
    ("interchange", 2, 1978, 1993, "Interchange_(Australian_rules_football)",
     "1978 - the replacement of two substitutes with two interchanges; 1994 - the introduction of a third interchange"),
    ("interchange", 3, 1994, 1997, "Interchange_(Australian_rules_football)",
     "1994 - the introduction of a third interchange; 1998 - the introduction of a fourth interchange"),
    ("interchange", 4, 1998, 2010, "Interchange_(Australian_rules_football)",
     "1998 - the introduction of a fourth interchange; 2011 - ... three interchanges and a substitute"),
    ("interchange", 3, 2011, 2015, "Interchange_(Australian_rules_football)",
     "Between 2011 and 2015, there were three interchange players and one substitute"),
    ("substitutes", 1, 2011, 2015, "Interchange_(Australian_rules_football)",
     "Between 2011 and 2015, there were three interchange players and one substitute"),
    ("interchange", 4, 2016, 2025, "Interchange_(Australian_rules_football)",
     "2016 - the return to four interchanges without a substitute ... 2026 - ... a fifth interchange player"),
    ("substitutes", 0, 2016, 2020, "Interchange_(Australian_rules_football)",
     "There were no substitutes between 2016 and 2020"),
    ("substitutes", 1, 2021, 2025, "Interchange_(Australian_rules_football)",
     "2021 - ... a medical substitute as a fifth bench player ... 2026 - removal of the substitute"),
    ("interchange", 5, 2026, 2026, "Interchange_(Australian_rules_football)",
     "each team is permitted five interchange players, and a maximum of seventy-five total player interchanges"),
    ("substitutes", 0, 2026, 2026, "Interchange_(Australian_rules_football)",
     "2026 - removal of the substitute and introduction of a fifth interchange player"),
    ("interchange_cap", 120, 2014, 2015, "Interchange_(Australian_rules_football)",
     "2014 - the addition of an interchange cap, limiting teams to 120 interchanges per game"),
    ("interchange_cap", 90, 2016, 2020, "Interchange_(Australian_rules_football)",
     "2016 - ... reduction of the interchange cap to 90 per game"),
    ("interchange_cap", 75, 2021, 2026, "Interchange_(Australian_rules_football)",
     "2021 - the reduction of the interchange cap to 75 a game"),
]


def page_has(cache: str, page: str, words: str) -> bool:
    """Every part of the quote ('...' or ';' between parts) is on the cached
    page, comparing letters and digits only (so a dash or spacing never matters).
    A page is a Wikipedia title or a full URL (a PDF is cached as its text)."""
    def squash(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())
    raw = wiki_text(cache, page) if not page.startswith("https://") else read(cache, page)
    # A page that carries its text as JSON (Google Books' snippets) escapes its tags as <...
    raw = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), raw)
    page_text = squash(text(raw))
    parts = [re.sub(r"^(Evolution of competition table: |TPP per club from \d{4} \(\$m\): |\d{4} - )", "", f)
             for f in re.split(r"\s*\.\.\.\s*|;\s*", words) if f.strip()]
    return all(squash(p)[:60] in page_text for p in parts)


def build_era_rules(cache: str) -> list[dict]:
    """Each rule's words must still be on its cached page (checked here, so a
    stale quote fails the build rather than the data)."""
    rows = []
    for rule, value, a, b, page, words in ERA_RULES:
        if not page_has(cache, page, words):
            raise SystemExit(f"era rule {rule} {a}-{b}: '{words}' not found on {page}")
        rows.append({"rule": rule, "value": value, "from_year": a, "to_year": b, "quote": words,
                     "source_url": page if page.startswith("https://") else WIKI + page, "checked": CHECKED})
    return rows


# A ground's name in each season: the name it carried through that season's
# home-and-away rounds (a change made during a season counts from the next).
# Blank from_year: the ground's name before the first rename; blank to_year:
# still the name. Each row quotes the page that says it, and the build checks
# the words are still there. The ground key is AFL Tables' venue page.
GROUND_NAMES = [
    ("docklands", "Colonial Stadium", 2000, 2002, "Docklands_Stadium", "Colonial Stadium (2000–2002)"),
    ("docklands", "Telstra Dome", 2003, 2008, "Docklands_Stadium",
     "the stadium's name was changed to Telstra Dome in October 2002"),
    ("docklands", "Etihad Stadium", 2009, 2018, "Docklands_Stadium",
     "In March 2009, the naming rights transferred to Etihad Airways"),
    ("docklands", "Marvel Stadium", 2019, None, "Docklands_Stadium",
     "In September 2018, the stadium was renamed Marvel Stadium"),
    ("kardinia_park", "Kardinia Park", None, 1998, "Kardinia_Park_(stadium)",
     "Naming rights sponsors [ edit ] 1999–2001: Shell"),
    ("kardinia_park", "Shell Stadium", 1999, 2001, "Kardinia_Park_(stadium)", "1999–2001: Shell 2002: Baytec"),
    ("kardinia_park", "Baytec Stadium", 2002, 2002, "Kardinia_Park_(stadium)", "2002: Baytec 2002–11: Skilled"),
    ("kardinia_park", "Skilled Stadium", 2003, 2011, "Kardinia_Park_(stadium)", "2002–11: Skilled 2012–17: Simonds"),
    ("kardinia_park", "Simonds Stadium", 2012, 2017, "Kardinia_Park_(stadium)",
     "2012–17: Simonds 2018–present: GMHBA"),
    ("kardinia_park", "GMHBA Stadium", 2018, None, "Kardinia_Park_(stadium)",
     "Since January 2018, the stadium has been commercially named GMHBA Stadium"),
    ("football_park", "Football Park", None, 2001, "Football_Park",
     "known under naming rights as AAMI Stadium from 2002"),
    ("football_park", "AAMI Stadium", 2002, 2013, "Football_Park",
     "From 1991 until 2013, the stadium (known under naming rights as AAMI Stadium from 2002)"),
    ("subiaco", "Subiaco Oval", None, 2010, "Subiaco_Oval",
     "Under naming rights the stadium was known as Patersons Stadium (2011–2014)"),
    ("subiaco", "Patersons Stadium", 2011, 2014, "Subiaco_Oval",
     "the stadium was known as Patersons Stadium (2011–2014) and Domain Stadium (2015–2017)"),
    ("subiaco", "Domain Stadium", 2015, 2017, "Subiaco_Oval",
     "the stadium was known as Patersons Stadium (2011–2014) and Domain Stadium (2015–2017)"),
    ("princes_park", "Princes Park", None, 1993, "Princes_Park_(stadium)",
     "The ground became known as Optus Oval in November 1993"),
    ("princes_park", "Optus Oval", 1994, 2006, "Princes_Park_(stadium)", "Optus Oval (1994–2006)"),
    ("princes_park", "MC Labour Park", 2007, 2008, "Princes_Park_(stadium)", "MC Labour Park (2007–2008)"),
    ("princes_park", "Visy Park", 2009, 2014, "Princes_Park_(stadium)", "Visy Park (2009–2015)"),
    ("princes_park", "Ikon Park", 2015, None, "Princes_Park_(stadium)",
     "Since 2015, the ground has been commercially been known as Ikon Park"),
    ("western_oval", "Western Oval", None, 1994, "Whitten_Oval",
     "Formerly known as the Western Oval , the venue was renamed in 1995"),
    ("western_oval", "Whitten Oval", 1995, None, "Whitten_Oval", "In 1995, the oval was renamed the Whitten Oval"),
    ("waverley_park", "VFL Park", 1970, 1989, "Waverley_Park", "VFL Park (1970–1989)"),
    ("waverley_park", "AFL Park", 1990, 1999, "Waverley_Park", "AFL Park (1990–1999)"),
    ("stadium_australia", "Stadium Australia", 1999, 2001, "Stadium_Australia",
     "The stadium lacked a naming rights sponsor in its formative years, bearing the name Stadium Australia"),
    ("stadium_australia", "Telstra Stadium", 2002, 2007, "Stadium_Australia", "Telstra Stadium (2002–2007)"),
    ("stadium_australia", "ANZ Stadium", 2008, 2020, "Stadium_Australia", "ANZ Stadium (2008–2020)"),
    ("stadium_australia", "Stadium Australia", 2021, 2021, "Stadium_Australia",
     "In December 2020, ANZ's naming rights to the stadium expired and it reverted to being Stadium Australia"),
    ("stadium_australia", "Accor Stadium", 2022, None, "Stadium_Australia",
     "In November 2021, French multinational hospitality company Accor acquired the rights"),
    ("carrara", "Carrara Stadium", 1987, 2010, "Carrara_Stadium",
     "bearing the names Carrara Stadium and Gold Coast Stadium between its opening in 1987 and 2011"),
    ("carrara", "Metricon Stadium", 2011, 2022, "Carrara_Stadium", "to be known henceforth as Metricon Stadium"),
    ("carrara", "Heritage Bank Stadium", 2023, 2023, "Carrara_Stadium",
     "In 2023 the stadium was renamed Heritage Bank Stadium"),
    ("carrara", "People First Stadium", 2024, None, "Carrara_Stadium",
     "the stadium was renamed People First Stadium in March 2024"),
    ("bruce_stadium", "Bruce Stadium", None, None, "Canberra_Stadium", "Former names Bruce Stadium"),
]
# Grounds the era's VFL/AFL knew by one name: the name, and the article that holds it.
PLAIN_NAME = {"mcg": "M.C.G.", "scg": "S.C.G.", "waca": "W.A.C.A.", "gabba": "The Gabba",
              "windy_hill": "Windy Hill", "moorabbin_oval": "Moorabbin Oval", "victoria_park": "Victoria Park",
              "north_hobart": "North Hobart Oval", "manuka_oval": "Manuka Oval", "junction_oval": "Junction Oval",
              "arden_st": "Arden Street Oval", "glenferrie_oval": "Glenferrie Oval"}


def build_ground_names(cache: str) -> list[dict]:
    rows = []
    for ground, name, a, b, page, words in GROUND_NAMES:
        if not page_has(cache, page, words):
            raise SystemExit(f"ground name {ground} {name}: '{words}' not found on {page}")
        rows.append({"ground": ground, "name": name, "from_year": a or "", "to_year": b or "", "quote": words,
                     "source_url": WIKI + page, "checked": CHECKED})
    for ground, name in PLAIN_NAME.items():
        rows.append({"ground": ground, "name": name, "from_year": "", "to_year": "",
                     "quote": "no naming-rights name in the VFL/AFL seasons it hosted",
                     "source_url": WIKI + GROUND_ARTICLES[ground], "checked": CHECKED})
    return rows


def build_venues(cache: str) -> list[dict]:
    """Games at each ground by season, from the AFL Tables season pages."""
    rows = []
    for y in list(PRE_SEASONS) + list(SEASONS):
        body = read(cache, f"https://afltables.com/afl/seas/{y}.html")
        n = defaultdict(int)
        names = {}
        for slug, name in re.findall(r'href="\.\./venues/([^"]+)\.html">([^<]+)</a>', body):
            n[slug] += 1
            names[slug] = name
        for slug in sorted(n):
            rows.append({"year": y, "ground": slug, "afltables_name": names[slug], "games": n[slug],
                         "source_url": f"https://afltables.com/afl/seas/{y}.html", "checked": CHECKED})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    lists = build_lists(a.cache)
    fill_heights(a.cache, lists)
    ids = first_season_ids(a.cache, lists)
    careers = build_pre_careers(a.cache, lists, ids)
    write("careers_before_1990.csv", ["afltables_id", "first", "last", "year", "club", "team", "num", "games",
                                      "goals", "source_url", "checked"], careers)
    drafts, wiki_counts = build_drafts(a.cache)
    opening, n_mid = build_opening_lists(a.cache, lists, drafts, ids, careers)
    print(f"opening 1990 lists: {n_mid} mid-season draftees taken off")
    write("lists_1990_opening.csv", ["club", "num", "first", "last", "list", "dob", "height_cm", "weight_kg",
                                     "games_before", "goals_before", "before_from", "games_1990", "goals_1990", "joined_how",
                                     "joined_year", "joined_from", "origin", "draftguru_id", "afltables_id",
                                     "source_url", "checked"], opening)
    write("coaches_1990.csv", ["club", "role", "name", "note", "source_url", "checked"], build_coaches(a.cache))
    write("captains_1990.csv", ["club", "role", "first", "last", "draftguru_id", "source_url", "checked"],
          build_captains(a.cache, opening))
    write("venues.csv", ["year", "ground", "afltables_name", "games", "source_url", "checked"], build_venues(a.cache))
    write_to(LEGACY, "era_rules.csv", ["rule", "value", "from_year", "to_year", "quote", "source_url", "checked"],
             build_era_rules(a.cache))
    write_to(LEGACY, "ground_names.csv", ["ground", "name", "from_year", "to_year", "quote", "source_url", "checked"],
             build_ground_names(a.cache))
    write("lists.csv", ["year", "club", "num", "first", "last", "list", "underage", "dob", "height_cm",
                        "weight_kg", "position", "games", "goals", "coach_votes", "brownlow_votes",
                        "games_prior", "goals_prior", "games_career", "goals_career", "origin",
                        "first_drafted", "joined_how", "joined_year", "joined_from", "joined_pick",
                        "elevated_from_rookie", "joined_detail", "draftguru_id", "afltables_id",
                        "height_from", "source_url", "checked"], lists)
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
