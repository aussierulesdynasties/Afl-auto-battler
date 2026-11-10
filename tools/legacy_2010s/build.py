#!/usr/bin/env python3
"""Build data/legacy/2010s/*.csv from the pages fetch.py cached.

    python tools/legacy_2010s/build.py --cache <dir>

Facts only. Nothing is guessed: a value the sources do not give stays blank,
and tools/check_legacy_2010s.py reports the blanks.
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
from fetch import DG, cache_path  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "legacy", "2010s")
CHECKED = "2026-11-10"
SEASONS = range(2010, 2020)
DRAFT_YEARS = range(2009, 2020)

SLUG = {
    "adelaide": "ADE", "brisbane": "BRL", "carlton": "CAR", "collingwood": "COL",
    "essendon": "ESS", "fremantle": "FRE", "geelong": "GEE", "gold-coast": "GCS",
    "greater-western-sydney": "GWS", "hawthorn": "HAW", "melbourne": "MEL",
    "north-melbourne": "NTH", "port-adelaide": "PAD", "richmond": "RIC",
    "st-kilda": "STK", "sydney": "SYD", "west-coast": "WCE", "western-bulldogs": "WBD",
}
NAME = {
    "adelaide": "ADE", "brisbane": "BRL", "brisbane lions": "BRL", "carlton": "CAR",
    "collingwood": "COL", "essendon": "ESS", "fremantle": "FRE", "geelong": "GEE",
    "gold coast": "GCS", "greater western sydney": "GWS", "gws": "GWS", "hawthorn": "HAW",
    "melbourne": "MEL", "north melbourne": "NTH", "kangaroos": "NTH", "port adelaide": "PAD",
    "richmond": "RIC", "st kilda": "STK", "sydney": "SYD", "west coast": "WCE",
    "western bulldogs": "WBD", "footscray": "WBD", "brisbane bears": "BRL", "fitzroy": "BRL",
}
# AFL Tables team slugs on the season stats page.
AT_SLUG = {
    "adelaide": "ADE", "brisbanel": "BRL", "carlton": "CAR", "collingwood": "COL",
    "essendon": "ESS", "fremantle": "FRE", "geelong": "GEE", "goldcoast": "GCS",
    "gws": "GWS", "hawthorn": "HAW", "melbourne": "MEL", "kangaroos": "NTH",
    "padelaide": "PAD", "richmond": "RIC", "stkilda": "STK", "swans": "SYD",
    "westcoast": "WCE", "bullldogs": "WBD", "bulldogs": "WBD",
}
SQUIGGLE = {
    "Adelaide": "ADE", "Brisbane Lions": "BRL", "Carlton": "CAR", "Collingwood": "COL",
    "Essendon": "ESS", "Fremantle": "FRE", "Geelong": "GEE", "Gold Coast": "GCS",
    "Greater Western Sydney": "GWS", "Hawthorn": "HAW", "Melbourne": "MEL",
    "North Melbourne": "NTH", "Port Adelaide": "PAD", "Richmond": "RIC", "St Kilda": "STK",
    "Sydney": "SYD", "West Coast": "WCE", "Western Bulldogs": "WBD",
}


def club_code(name: str) -> str:
    n = re.sub(r"\s+", " ", html.unescape(name)).strip().lower()
    n = re.sub(r" (football club|fc)$", "", n)
    return NAME.get(n, "")


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
        out.append({
            "num": by["number"][0][0],
            "list_code": lt,
            "dg": html.unescape(name_cell.group(1)),
            "name": text(name_cell.group(2)),
            "dob": by["dob"][0][1],
            "height_cm": str(abs(int(by["height"][0][1]))) if by["height"][0][1] not in ("", "0") else "",
            "games_prior": games[0], "goals_prior": goals[0],
            "coach_votes_prior": votes[0], "brownlow_votes_prior": votes[1],
            "games": games[1], "goals": goals[1],
            "coach_votes": votes[2], "brownlow_votes": votes[3],
            "games_career": games[2], "goals_career": goals[2],
            "origin": by["from-club"][0][0] if by["from-club"] else "",
            "first_drafted": by["movement"][0][0] if by["movement"] else "",
        })
    return out


# ------------------------------------------------------------ Draftguru players

EVENT_RE = re.compile(r'<tr class="(year-row|between-years-row)[^"]*">(.*?)</tr>', re.S)


def parse_player(body: str) -> list[tuple]:
    """Ordered ('year', year, club, list) and ('event', text) entries."""
    seq = []
    for kind, inner in EVENT_RE.findall(body):
        if kind == "year-row":
            year = re.search(r'class="year">(\d{4})<', inner)
            club = re.search(r'class="afl-club"[^>]*>(.*?)</td>', inner, re.S)
            lst = re.search(r'class="afl-list"[^>]*>(.*?)</td>', inner, re.S)
            if year:
                seq.append(("year", int(year.group(1)), club_code(text(club.group(1))) if club else "",
                            text(lst.group(1)) if lst else ""))
        else:
            for ev in re.findall(r"<a [^>]*>(.*?)</a>|<td colspan=\"10\">(.*?)</td>", inner, re.S):
                t = text(ev[0] or ev[1])
                if t:
                    seq.append(("event", t))
    return seq


CLUBS_RE = (r"(Adelaide|Brisbane(?: Lions| Bears)?|Carlton|Collingwood|Essendon|Fremantle|Geelong|"
            r"Gold Coast|Greater Western Sydney|GWS|Hawthorn|Melbourne|North Melbourne|Kangaroos|"
            r"Port Adelaide|Richmond|St Kilda|Sydney|West Coast|Western Bulldogs|Footscray|Fitzroy)")


def classify(event: str, club: str) -> dict | None:
    """Read one Draftguru movement line. Returns the join it records for club, if any."""
    event = re.sub(r"^\([^)]*\)\s*", "", event)  # "(Prelisted by Gold Coast) Traded from ..."
    m = re.match(rf"Drafted by {CLUBS_RE} with (.+?) pick #(\d+)", event)
    if m and club_code(m.group(1)) == club:
        kind = m.group(2).lower().replace("-", "_").replace(" draft", "").replace(" ", "_")
        return {"joined_how": f"{kind}_draft", "joined_pick": m.group(3), "joined_detail": event}
    m = re.match(rf"Traded from {CLUBS_RE} to {CLUBS_RE}", event)
    if m and club_code(m.group(2)) == club:
        return {"joined_how": "trade", "joined_from": club_code(m.group(1)), "joined_detail": event}
    m = re.match(rf"(Restricted |Unrestricted |Delisted )?Free Agent from {CLUBS_RE} to {CLUBS_RE}", event)
    if m and club_code(m.group(3)) == club:
        sub = (m.group(1) or "").strip().lower()
        return {"joined_how": "free_agent" + (f"_{sub}" if sub else ""),
                "joined_from": club_code(m.group(2)), "joined_detail": event}
    # Any other line naming the club as the destination: signings, zone, concessions.
    m = re.search(rf"(?:by|to) {CLUBS_RE}\b", event)
    if m and club_code(m.group(1)) == club and not event.startswith(("Delisted", "Retired")):
        return {"joined_how": "signed", "joined_detail": event}
    return None


def join_for(seq: list[tuple], club: str, season: int) -> dict:
    """How the player came to `club` for the stint that includes `season`.

    The stint starts at the earliest year row of an unbroken run of years at the
    club ending in `season`. The joining event is among the movement lines just
    before that row: a draft, trade or free-agency line naming the club wins;
    otherwise a club-less signing line (zone, scholarship, supplemental, etc.).
    """
    years = [(i, it[1], it[2]) for i, it in enumerate(seq) if it[0] == "year"]
    pos = [k for k, (_, y, _) in enumerate(years) if y == season]
    if not pos:
        return {}
    k = pos[0]
    if years[k][2] != club:
        return {}
    while k > 0 and years[k - 1][2] == club and years[k - 1][1] == years[k][1] - 1:
        k -= 1
    start_idx, start_year = years[k][0], years[k][1]
    prev_idx = years[k - 1][0] if k > 0 else -1
    events = [it[1] for it in seq[prev_idx + 1:start_idx] if it[0] == "event"]
    best = None
    for ev in events:
        j = classify(ev, club)
        if j and j["joined_how"] != "signed":
            best = j
    if not best:
        for ev in events:
            j = classify(ev, club)
            if j:
                best = j
        if not best:
            loose = [ev for ev in events if not ev.startswith(("Delisted", "Retired")) or ev == "Delisted Free Agent"]
            if loose:
                ev = loose[-1]
                how = ("free_agent_delisted" if ev == "Delisted Free Agent"
                       else "supplemental_selection" if "Supplemental" in ev
                       else "zone" if "Zone" in ev else "underage_concession" if "Underage" in ev
                       else "uncontracted_concession" if "Uncontracted Signing" == ev
                       else "father_son" if "Father-Son" in ev else "international" if "International" in ev
                       else "category_b" if ("Unregistered" in ev or "Recruit" in ev)
                       else "top_up" if "Top-Up" in ev else "foundation" if "Foundation" in ev
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
    return best or {}


# ----------------------------------------------------------------- AFL Tables

AT_COLS = ["gm", "ki", "mk", "hb", "di", "da", "gl", "bh", "ho", "tk", "rb", "if50", "cl", "cg",
           "ff", "fa", "br", "cp", "up", "cm", "mi", "one_pct", "bo", "ga", "pct_played"]


def parse_afltables_season(body: str) -> list[dict]:
    out = []
    for table in re.findall(r'<table[^>]*class="sortable".*?</table>', body, re.S):
        team = re.search(r'href="\.\./teams/([a-z]+)_idx\.html"', table)
        if not team:
            continue
        code = AT_SLUG.get(team.group(1), "")
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
    at_by_season = {}
    for y in SEASONS:
        at_by_season[y] = parse_afltables_season(read(cache, f"https://afltables.com/afl/stats/{y}.html"))
    player_cache: dict[str, list] = {}
    bio_cache: dict[str, dict] = {}
    for y in SEASONS:
        idx = read(cache, f"{DG}/lists/{y}")
        slugs = sorted(set(re.findall(rf'href="/lists/{y}/([a-z-]+)"', idx)))
        at = at_by_season[y]
        for slug in slugs:
            club = SLUG[slug]
            if (club == "GCS" and y < 2011) or (club == "GWS" and y < 2012):
                # First AFL seasons: Gold Coast 2011, GWS 2012. Their earlier squads
                # played the VFL / NEAFL and are not AFL lists.
                continue
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
                if prev and prev[0][2] == club and prev[0][3].startswith("rookie") and row["list"] == "senior":
                    row["elevated_from_rookie"] = y
                # AFL Tables: same club, then full name, then number and surname.
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
        for r in parse_afltables_season(read(cache, f"https://afltables.com/afl/stats/{y}.html")):
            r["year"] = y
            r["source_url"] = f"https://afltables.com/afl/stats/{y}.html"
            r["checked"] = CHECKED
            rows.append(r)
    return rows


def parse_years_page(body: str) -> list[dict]:
    out = []
    for tr in re.findall(r'<tr class="outcome[^"]*">(.*?)</tr>', body, re.S):
        cells = re.findall(r'<td class="([^"]+)"[^>]*>(.*?)</td>', tr, re.S)
        cats = [text(v) for k, v in cells if k == "category"]
        get = {k.split()[-1] if k.startswith("stats") else k: v for k, v in cells}
        player = re.search(r'<a href="(/players/[^"]+)">(.*?)</a>', get.get("player", ""), re.S)
        out.append({
            "draft": text(get.get("draft", "")),
            "pick": text(get.get("number", "")),
            "club": club_code(text(get.get("club", ""))),
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
                     ("fa (", "free_agent"), ("dfa", "delisted_free_agent")):
        if s.startswith(key):
            return val
    return ""


def wiki_drafts(cache: str, year: int) -> dict:
    """{(kind, pick): {'round':..,'note':..}} from the Wikipedia draft page."""
    body = read(cache, f"https://en.wikipedia.org/wiki/{year}_AFL_draft")
    # Parsoid HTML carries JSON in attributes and CSS blocks; drop them first.
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    body = re.sub(r"\sdata-mw='[^']*'|\sdata-mw=\"[^\"]*\"|\stitle=\"[^\"]*\"", "", body)
    out = {}
    parts = re.split(r'(<h[234][^>]*id="[^"]+")', body)
    current = None
    for part in parts:
        h = re.match(r'<h[234][^>]*id="([^"]+)"', part)
        if h:
            hid = h.group(1).lower()
            current = ("national" if "national_draft" in hid
                       else "preseason" if ("pre-season_draft" in hid or "preseason_draft" in hid)
                       else "rookie" if "rookie_draft" in hid else "mini" if "mini-draft" in hid else None)
            continue
        if not current:
            continue
        for table in re.findall(r'<table class="[^"]*wikitable.*?</table>', part, re.S):
            trs = re.findall(r"<tr.*?</tr>", table, re.S)
            if not trs:
                continue
            cols = []
            for attrs, c in re.findall(r"<th([^>]*)>(.*?)</th>", trs[0], re.S):
                c = text(c).lower()
                span = re.search(r'colspan="?(\d+)', attrs)
                name = ("round" if ("round" in c or c in ("rd.", "rd")) else "pick" if c in ("pick", "#", "no.") or "pick" in c
                        else "player" if "player" in c or c == "name" else "club" if "drafted to" in c or c == "club"
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
                pick = rec.get("pick", "")
                if not pick.isdigit():
                    continue
                player = rec.get("player", "")
                out[(current, int(pick))] = {"round": rec.get("round", last_round), "note": rec.get("notes", ""),
                                             "player": player, "passed": player.lower().startswith("pass"),
                                             "club": club_code(rec.get("club", ""))}
    counts = defaultdict(int)
    for (kind, _), v in out.items():
        if not v["passed"] and v["player"]:
            counts[kind] += 1
    return {"picks": out, "counts": dict(counts)}


def wiki_free_agents(cache: str, year: int) -> list[dict]:
    body = read(cache, f"https://en.wikipedia.org/wiki/{year}_AFL_draft")
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    body = re.sub(r"\sdata-mw='[^']*'|\sdata-mw=\"[^\"]*\"|\stitle=\"[^\"]*\"", "", body)
    out = []
    for table in re.findall(r'<table class="[^"]*wikitable.*?</table>', body, re.S):
        trs = re.findall(r"<tr.*?</tr>", table, re.S)
        cols = [re.sub(r"\s*\[.*?\]", "", text(c).lower()).strip()
                for c in re.findall(r"<th[^>]*>(.*?)</th>", trs[0], re.S)] if trs else []
        if "free agent type" not in cols:
            continue
        for tr in trs[1:]:
            cells = [text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
            rec = dict(zip(cols, cells))
            if rec.get("player"):
                out.append({"player": rec["player"], "type": rec.get("free agent type", ""),
                            "from": club_code(rec.get("former club", "")), "to": club_code(rec.get("new club", "")),
                            "compensation": rec.get("compensation", "")})
    return out


def wiki_flag(note: str) -> str:
    n = note.lower()
    for key, val in (("father", "father_son"), ("next generation", "next_generation_academy"),
                     ("academy", "academy"), ("priority", "priority"), ("compensation", "compensation"),
                     ("zone", "zone")):
        if key in n:
            return val
    return ""


def build_drafts(cache: str) -> tuple[list[dict], dict]:
    rows = []
    wiki_counts = {}
    for y in DRAFT_YEARS:
        url = f"{DG}/years/{y}"
        wk = wiki_drafts(cache, y)
        wiki_counts[y] = wk["counts"]
        for r in parse_years_page(read(cache, url)):
            if r["draft"] in ("Trade", "Free Agency"):
                continue
            kind = DRAFT_KIND.get(r["draft"], r["draft"].lower())
            first, last = split_name(r["name"])
            pick = int(r["pick"]) if r["pick"].isdigit() else None
            w = wk["picks"].get((kind, pick), {}) if pick else {}
            flag = flag_of(r["signing"]) or wiki_flag(w.get("note", "") + " " + w.get("round", ""))
            rows.append({
                "year": y, "draft": kind, "round": re.sub(r"\D", "", w.get("round", "")), "pick": r["pick"],
                "club": r["club"], "first": first, "last": last, "origin": r["origin"],
                "flag": flag, "flag_detail": r["signing"], "wiki_note": w.get("note", ""),
                "wiki_player": "" if w.get("passed") else w.get("player", ""),
                "draftguru_id": r["dg"],
                "source_url": f"{url} | https://en.wikipedia.org/wiki/{y}_AFL_draft",
                "checked": CHECKED,
            })
        seen = {(r["draft"], int(r["pick"])) for r in rows if r["year"] == y and r["pick"].isdigit()}
        for (kind, pick), w in sorted(wk["picks"].items(), key=lambda kv: (kv[0][0], kv[0][1])):
            if w["passed"] or not w["player"] or (kind, pick) in seen:
                continue
            first, last = split_name(re.sub(r"\s+[\^*+x†‡]+$", "", w["player"]).strip())
            rows.append({
                "year": y, "draft": kind, "round": re.sub(r"\D", "", w.get("round", "")), "pick": pick,
                "club": w["club"], "first": first, "last": last, "origin": "",
                "flag": wiki_flag(w["note"] + " " + w.get("round", "")), "flag_detail": "",
                "wiki_note": w["note"], "draftguru_id": "", "only_in": "wikipedia",
                "source_url": f"https://en.wikipedia.org/wiki/{y}_AFL_draft", "checked": CHECKED,
            })
        wiki_counts[y]["free_agency"] = len(wiki_free_agents(cache, y))
    return rows, wiki_counts


def build_moves(cache: str, lists: list[dict]) -> list[dict]:
    dobs = {r["draftguru_id"]: r["dob"] for r in lists if r["dob"]}
    rows = []
    for y in DRAFT_YEARS:
        url = f"{DG}/years/{y}"
        wiki_fas = wiki_free_agents(cache, y)
        for r in parse_years_page(read(cache, url)):
            if r["draft"] not in ("Trade", "Free Agency") and flag_of(r["signing"]) != "uncontracted_concession":
                continue
            seq = parse_player(read(cache, DG + r["dg"])) if r["dg"] else []
            j = {}
            # The event in the off-season after season y.
            year_now = None
            for item in seq:
                if item[0] == "year":
                    year_now = item[1]
                    continue
                if year_now == y:
                    c = classify(item[1], r["club"])
                    if c:
                        j = c
            if not j.get("joined_from"):
                # The club the player was listed at in season y is the one he left.
                at_y = [it[2] for it in seq if it[0] == "year" and it[1] == y and it[2]]
                if at_y and at_y[-1] != r["club"]:
                    j = dict(j, joined_from=at_y[-1])
            first, last = split_name(r["name"])
            dob = dobs.get(r["dg"], "")
            kind = {"Trade": "traded"}.get(r["draft"], "")
            if r["draft"] == "Free Agency":
                kind = {"FA (Restricted)": "free_agent_restricted", "FA (Unrestricted)": "free_agent_unrestricted",
                        "DFA": "delisted_free_agent"}.get(r["signing"], "free_agent")
            elif not kind:
                kind = "uncontracted_concession"
            comp = ""
            if kind.startswith("free_agent") or kind == "delisted_free_agent":
                for fa in wiki_fas:
                    if norm(fa["player"]).endswith(norm(last)) and fa["to"] == r["club"]:
                        comp = fa["compensation"]
            rows.append({
                "year": y, "first": first, "last": last, "dob": dob, "compensation": comp,
                "from_club": j.get("joined_from", ""), "to_club": r["club"], "kind": kind,
                "detail": j.get("joined_detail", ""), "draftguru_id": r["dg"],
                "source_url": f"{url} | https://en.wikipedia.org/wiki/{y}_AFL_draft",
                "checked": CHECKED,
            })
    return rows


AT_TEAM = {"Brisbane Lions": "BRL", "Greater Western Sydney": "GWS", "Gold Coast": "GCS",
           "North Melbourne": "NTH", "Port Adelaide": "PAD", "St Kilda": "STK", "West Coast": "WCE",
           "Western Bulldogs": "WBD"}


def afltables_ladder(cache: str, y: int) -> dict:
    """{club: {w, d, l, pts, pct}} from the final ladder on AFL Tables' season page."""
    body = read(cache, f"https://afltables.com/afl/seas/{y}.html")
    i = body.rfind(f"{y} Ladder")
    table = re.search(r"<table.*?</table>", body[i:], re.S) if i >= 0 else None
    out = {}
    for tr in re.findall(r"<tr.*?</tr>", table.group(0) if table else "", re.S):
        cells = [text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        if len(cells) < 14 or not cells[0].isdigit():
            continue
        name = cells[1]
        code = AT_TEAM.get(name) or club_code(name)
        out[code] = {"w": cells[3], "d": cells[4] or "0", "l": cells[5], "pct": cells[12], "pts": cells[13]}
    return out


def build_ladders(cache: str) -> list[dict]:
    rows = []
    for y in SEASONS:
        st = json.loads(read(cache, f"https://api.squiggle.com.au/?q=standings;year={y}") or "{}")
        games = json.loads(read(cache, f"https://api.squiggle.com.au/?q=games;year={y}") or "{}")
        finals = {}
        fg = sorted([g for g in games.get("games", []) if g.get("is_final")], key=lambda g: g["date"])
        for g in fg:
            for side in ("hteam", "ateam"):
                team = SQUIGGLE[g[side]]
                won = g["winner"] == g[side]
                rn = g["roundname"].lower()
                if g.get("is_grand_final") or "grand" in rn:
                    finals[team] = "premiers" if won else ("runners_up" if g["winner"] else "grand_final_drawn")
                elif not won:
                    finals[team] = ("prelim" if "prelim" in rn else "semi" if "semi" in rn else "week1_loss")
                else:
                    finals.setdefault(team, "finals")
        at = afltables_ladder(cache, y)
        for s in sorted(st.get("standings", []), key=lambda s: s["rank"]):
            team = SQUIGGLE[s["name"]]
            fin = finals.get(team, "")
            a = at.get(team, {})
            note = ""
            if a and (int(a["w"]), int(a["d"]), int(a["l"])) != (s["wins"], s["draws"], s["losses"]):
                note = f"Squiggle W-D-L {s['wins']}-{s['draws']}-{s['losses']}"
            if a and int(a["pts"]) != int(s["pts"]):
                note = (note + "; " if note else "") + f"Squiggle points {s['pts']} (AFL Tables used)"
            if y == 2015 and team in ("ADE", "GEE"):
                note = (note + "; " if note else "") + ("round 14 Adelaide v Geelong cancelled; both sources"
                                                        " count wins only, the AFL ladder gave each club 2 points")
            rows.append({
                "year": y, "pos": s["rank"], "club": team, "w": s["wins"], "l": s["losses"],
                "d": s["draws"], "pts": a.get("pts", s["pts"]), "pct": f"{float(s['percentage']):.1f}",
                "finals": fin, "note": note,
                "source_url": f"https://api.squiggle.com.au/?q=standings;year={y} | https://afltables.com/afl/seas/{y}.html",
                "checked": CHECKED,
            })
    # A loss in week one ends the season only for 5th-8th (elimination finals).
    for r in rows:
        if r["finals"] == "week1_loss":
            r["finals"] = "elim"
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
