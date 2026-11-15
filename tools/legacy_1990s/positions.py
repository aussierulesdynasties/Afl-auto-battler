#!/usr/bin/env python3
"""
Every Legacy start's real players' real positions (director 2026-11-15: "some
are out of position like Garry Lyon in defence, he's famous as a forward / you
need to audit every legacy player to make sure theyre rated properly and in the
right positions").

The past lists carry no listed position, so the game read each player's
position off one season's numbers, and before the 2000s most of those numbers
(rebound 50s, inside 50s, clearances, one percenters) are estimates. This finds
the position each player is known for, in this order:

  1. his Wikipedia article's infobox "position" (Garry Lyon: "Centre
     half-forward"), the article found in his clubs' players categories by
     name and checked by his birth year;
  2. the article's opening paragraph ("played as a full-back");
  3. his whole AFL career's recorded numbers (AFL Tables, 1987-2025): goals a
     game for a forward, hit-outs for a ruck, and the rest by the recorded
     defensive and midfield numbers where they were kept (2000s on; marks
     inside 50 are left out: they called 58 of 198 midfielders forwards);
  4. for the rest (mostly 1990s players with a stub article), the players
     whose positions came from Wikipedia and whose recorded career numbers
     are most like his (kicks, marks, handballs, scoring shots, hit-outs and
     tackles a game, kick share, height): the line at least 9 of his 15
     nearest share. Checked against the Wikipedia positions held out, it
     matches 84% of the time where it names one; the one-season read it
     replaces matched 60% (1990) to 76% (2020).

Output data/legacy/positions.csv, one row per player (first, last, dob, and his
AFL Tables ids, afltables_ids):
  pos, pos2   FWD / MID / DEF / RUC, and a second line ("" when none)
  source      wiki_infobox / wiki_lead / career / nearest
  wiki_title, wiki_text   the article and the words the position came from
The start builds (build_start*.py) fill real_pos from pos, so the game's
listed_primary keeps a listed forward or defender there (Ratings.gd).

    python3 tools/legacy_1990s/positions.py [--cache DIR]   # fetch and write
Stdlib only. Wikipedia's API, one request every 3 s (faster draws 429s), cached.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEG = os.path.join(ROOT, "data", "legacy")
OUT = os.path.join(LEG, "positions.csv")
API = "https://en.wikipedia.org/w/api.php"
UA = "afl-legacy-positions/1.0 (stdlib research script)"
STARTS = (1990, 2000, 2010, 2020)

# Position words -> line. Longest first, so "centre half-forward" wins over
# "centre" and "half-back flanker" over "flank".
WORDS = [
    ("centre half-forward", "FWD"), ("centre half forward", "FWD"), ("half-forward flanker", "FWD"),
    ("half forward flanker", "FWD"), ("half-forward", "FWD"), ("half forward", "FWD"),
    ("full-forward", "FWD"), ("full forward", "FWD"), ("forward pocket", "FWD"), ("key forward", "FWD"),
    ("key position forward", "FWD"), ("key-position forward", "FWD"), ("tall forward", "FWD"),
    ("small forward", "FWD"), ("medium forward", "FWD"), ("general forward", "FWD"),
    ("marking forward", "FWD"), ("goalsneak", "FWD"), ("goal sneak", "FWD"), ("forward", "FWD"),
    ("centre half-back", "DEF"), ("centre half back", "DEF"), ("half-back flanker", "DEF"),
    ("half back flanker", "DEF"), ("half-back", "DEF"), ("half back", "DEF"), ("full-back", "DEF"),
    ("full back", "DEF"), ("fullback", "DEF"), ("back pocket", "DEF"), ("back-pocket", "DEF"),
    ("key defender", "DEF"), ("key position defender", "DEF"), ("key-position defender", "DEF"),
    ("tall defender", "DEF"), ("small defender", "DEF"), ("general defender", "DEF"),
    ("rebounding defender", "DEF"), ("defender", "DEF"), ("defence", "DEF"),
    ("ruck-rover", "MID"), ("ruck rover", "MID"), ("ruckrover", "MID"),
    ("ruckman", "RUC"), ("ruckmen", "RUC"), ("ruck", "RUC"),
    ("midfielder", "MID"), ("midfield", "MID"), ("onballer", "MID"), ("on-baller", "MID"),
    ("rover", "MID"), ("wingman", "MID"), ("wing", "MID"), ("centreman", "MID"),
    ("inside midfielder", "MID"), ("outside midfielder", "MID"), ("tagger", "MID"),
]
_WORD_RE = re.compile(r"(?<![a-z])(" + "|".join(re.escape(w) for w, _ in WORDS) + r")(?:s)?(?![a-z])")
_LINE = dict(WORDS)


def lines_in(text: str) -> list:
    """The lines a phrase names, in the order it names them, without repeats."""
    out = []
    for m in _WORD_RE.finditer(text.lower()):
        line = _LINE[m.group(1)]
        if line not in out:
            out.append(line)
    return out


# ------------------------------------------------------------------- fetch --
class Wiki:
    def __init__(self, cache):
        self.cache = cache
        os.makedirs(cache, exist_ok=True)
        self.last = 0.0

    def get(self, params):
        params = dict(params, format="json", formatversion="2")
        q = urllib.parse.urlencode(sorted(params.items()))
        path = os.path.join(self.cache, hashlib.sha1(q.encode()).hexdigest() + ".json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        wait = 3.0 - (time.time() - self.last)
        if wait > 0:
            time.sleep(wait)
        for attempt in range(8):
            try:
                req = urllib.request.Request(API + "?" + q, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = json.loads(r.read().decode("utf-8"))
                break
            except Exception as e:  # noqa: BLE001 - retry any network fault
                self.last = time.time()
                print("wiki: retry %d (%s)" % (attempt + 1, e), file=sys.stderr)
                time.sleep(30 * (attempt + 1))
        else:
            raise SystemExit("wiki: gave up on " + q[:200])
        self.last = time.time()
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        return data


# Each club's players category on Wikipedia (Footscray's players are the
# Western Bulldogs'; the Bears and the Lions share BRL in the data).
CLUB_CATEGORIES = {
    "ADE": ["Adelaide Football Club players"], "BRL": ["Brisbane Bears players", "Brisbane Lions players"],
    "CAR": ["Carlton Football Club players"], "COL": ["Collingwood Football Club players"],
    "ESS": ["Essendon Football Club players"], "FIT": ["Fitzroy Football Club players"],
    "FRE": ["Fremantle Football Club players"], "GCS": ["Gold Coast Football Club players"],
    "GEE": ["Geelong Football Club players"], "GWS": ["Greater Western Sydney Giants players"],
    "HAW": ["Hawthorn Football Club players"], "MEL": ["Melbourne Football Club players"],
    "NTH": ["North Melbourne Football Club players"], "PAD": ["Port Adelaide Football Club players"],
    "RIC": ["Richmond Football Club players"], "STK": ["St Kilda Football Club players"],
    "SYD": ["Sydney Swans players"], "WCE": ["West Coast Eagles players"],
    "WBD": ["Western Bulldogs players"],
}


def query_all(wiki, params, key):
    """Every result of a list query, following the API's continuation."""
    out, cont = [], {}
    while True:
        data = wiki.get(dict(params, **cont))
        out += data.get("query", {}).get(key, [])
        if "continue" not in data:
            return out
        cont = dict(data["continue"])


def club_titles(wiki):
    """{club: [article titles]} from each club's players category."""
    out = {}
    for club, cats in CLUB_CATEGORIES.items():
        out[club] = []
        for cat in cats:
            for m in query_all(wiki, {"action": "query", "list": "categorymembers", "cmtitle": "Category:" + cat,
                                      "cmnamespace": "0", "cmlimit": "max"}, "categorymembers"):
                out[club].append(m["title"])
    return out


def base(title):
    return re.sub(r"\s*\(.*\)\s*$", "", title).strip().lower()


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())


def birth_year(text):
    m = re.search(r"\[\[Category:(\d{4}) births", text)
    if m:
        return m.group(1)
    m = re.search(r"birth_date\s*=\s*\{\{[^|}]*\|\s*(?:[dm]f=\w+\|\s*)?(\d{4})", text, flags=re.I)
    return m.group(1) if m else ""


def resolve(wiki, players, clubs_of):
    """{key: (title, wikitext)}: the article in his clubs' players categories
    with his name and his birth year. First by full name, or surname and the
    first three letters of his first name (Bill / Billy Brownless); then, for a
    player with AFL games still unmatched, by surname alone at his clubs."""
    titles = club_titles(wiki)
    print("club category articles: %d" % sum(len(v) for v in titles.values()))
    every = sorted({t for v in titles.values() for t in v})
    by_full, by_short, by_last = defaultdict(set), defaultdict(set), defaultdict(set)
    for t in every:
        parts = base(t).split()
        if len(parts) < 2:
            continue
        last = norm(" ".join(parts[1:]))
        by_full[norm(" ".join(parts))].add(t)
        by_short[(last, norm(parts[0])[:3])].add(t)
        by_last[last].add(t)
    found = {}
    for rnd in (1, 2):
        want = {}
        for key in players:
            if key in found:
                continue
            first, last, _ = key
            if rnd == 1:
                cands = by_full.get(norm(first + last), set()) | by_short.get((norm(last), norm(first)[:3]), set())
            else:
                if not players[key]:
                    continue
                own = {t for c in clubs_of.get(key, ()) for t in titles.get(c, [])}
                cands = by_last.get(norm(last), set()) & own
            if cands and len(cands) <= 40:
                want[key] = cands
        text = contents(wiki, {t for c in want.values() for t in c})
        for key, cands in want.items():
            hit = [t for t in sorted(cands) if birth_year(text.get(t, "")) == key[2][:4]]
            if len(hit) == 1:
                found[key] = (hit[0], text[hit[0]])
        print("round %d: %d articles" % (rnd, len(found)))
    return found


def contents(wiki, titles):
    out = {}
    titles = sorted(set(titles))
    for i in range(0, len(titles), 50):
        for p in query_all(wiki, {"action": "query", "titles": "|".join(titles[i:i + 50]), "prop": "revisions",
                                  "rvprop": "content", "rvslots": "main"}, "pages"):
            revs = p.get("revisions") or []
            if revs:
                out[p["title"]] = revs[0]["slots"]["main"]["content"]
    return out


# ------------------------------------------------------------------- parse --
def strip_markup(s):
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"'{2,}", "", s)
    return s


def infobox_position(text):
    m = re.search(r"^\s*\|\s*position\s*=\s*(.*)$", text, flags=re.M | re.I)
    if not m:
        return ""
    v = strip_markup(m.group(1))
    v = re.sub(r"\{\{[^}]*\}\}", " ", v)
    return v.strip(" |")


def lead(text):
    """The first prose paragraph after the infobox and hatnotes."""
    depth, i, n = 0, 0, len(text)
    body = []
    while i < n:
        if text.startswith("{{", i):
            depth += 1
            i += 2
            continue
        if text.startswith("}}", i) and depth:
            depth -= 1
            i += 2
            continue
        if depth == 0:
            body.append(text[i])
        i += 1
    body = "".join(body)
    body = body.split("\n==", 1)[0]
    paras = [p.strip() for p in body.split("\n") if p.strip() and not p.strip().startswith(("[[File", "[[Image", "|", "{|", "!"))]
    return strip_markup(" ".join(paras[:2]))


_LEAD_RE = re.compile(r"\b(?:played|plays|playing|known|used|recruited|utilised|utilized|regarded|"
                      r"established (?:himself)?|was|is|became|starred|excelled|lined up|operated)"
                      r"(?: (?:mainly|primarily|mostly|predominantly|usually|chiefly|generally|"
                      r"principally|often|largely|initially|originally))?"
                      r"(?: (?:as|at|in))(?: (?:a|an|the))? ([a-z\- ,/]{3,60})")


def lead_position(text):
    t = lead(text).lower()
    for m in _LEAD_RE.finditer(t):
        found = lines_in(m.group(1))
        if found:
            return m.group(0), found
    return "", []


# ------------------------------------------------------------------ career --
def career_numbers():
    """{(first, last, dob-year): {stat: total}} over every AFL season on record,
    and which seasons kept rb / one_pct / cl (the 2000s on)."""
    rows = []
    for dec in ("1990s", "2000s", "2010s", "2020s"):
        with open(os.path.join(LEG, dec, "season_stats.csv"), newline="", encoding="utf-8") as fh:
            rows += list(csv.DictReader(fh))
    by_id = defaultdict(lambda: defaultdict(float))
    names = defaultdict(set)
    for r in rows:
        tot = by_id[r["afltables_id"]]
        g = float(r["gm"] or 0)
        tot["gm"] += g
        for k in ("gl", "ho", "mk", "ki", "hb", "di", "tk"):
            tot[k] += float(r[k] or 0)
        if r["rb"] != "" and r["one_pct"] != "" and r["cl"] != "":
            tot["kept_gm"] += g
            for k in ("rb", "one_pct", "cl", "if50", "mi"):
                tot[k] += float(r[k] or 0)
        names[(r["first"].strip().lower(), r["last"].strip().lower())].add(r["afltables_id"])
    return by_id, names


def career_line(t):
    """The line his career numbers say, or "" when they say too little."""
    g = t["gm"]
    if g < 10:
        return ""
    if t["ho"] / g >= 8.0:
        return "RUC"
    if t["gl"] / g >= 1.1:
        return "FWD"
    kg = t["kept_gm"]
    if kg >= 20:
        defn = (t["rb"] + t["one_pct"]) / kg
        mid = (t["cl"] + t["if50"] * 0.5) / kg
        if defn >= 4.0 and defn > mid * 1.3:
            return "DEF"
        if mid >= 3.0:
            return "MID"
    return ""


# ----------------------------------------------------------------- nearest --
NEAREST_K = 15
NEAREST_VOTES = 9           # of NEAREST_K: 0.6, 84% right on held-out players
_NEAR_W = (1.0, 1.0, 1.0, 1.5, 1.5, 1.0, 1.0, 1.2, 0.3)


def heights():
    out = {}
    for dec in ("1990s", "2000s", "2010s", "2020s"):
        with open(os.path.join(LEG, dec, "lists.csv"), newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("height_cm"):
                    out[(r["first"], r["last"], r["dob"])] = float(r["height_cm"])
    return out


def career_shape(t, height):
    """His career a game, as the nearest-player vote compares it (None when
    under 10 games or no height)."""
    g = t["gm"]
    if g < 10 or not height:
        return None
    disp = t["ki"] + t["hb"]
    return [t["ki"] / g, t["mk"] / g, t["hb"] / g, (t["gl"] + t["bh"]) / g, t["ho"] / g, t["tk"] / g,
            t["ki"] / max(disp, 1.0), height, math.log(g)]


def nearest_lines(known, unknown):
    """{key: line} for each unknown shape whose NEAREST_K nearest known shapes
    give one line at least NEAREST_VOTES times. known: [(key, shape, line)]."""
    n = len(known[0][1])
    mu = [sum(k[1][i] for k in known) / len(known) for i in range(n)]
    sd = [math.sqrt(sum((k[1][i] - mu[i]) ** 2 for k in known) / len(known)) or 1.0 for i in range(n)]
    z = lambda f: [(f[i] - mu[i]) / sd[i] * _NEAR_W[i] for i in range(n)]
    pool = [(key, z(f), line) for key, f, line in known]
    out = {}
    for key, f in unknown:
        zf = z(f)
        near = sorted(pool, key=lambda k: (sum((a - b) ** 2 for a, b in zip(k[1], zf)), k[0]))[:NEAREST_K]
        line, votes = Counter(k[2] for k in near).most_common(1)[0]
        if votes >= NEAREST_VOTES:
            out[key] = (line, votes)
    return out


# -------------------------------------------------------------------- main --
def load_players():
    """{(first, last, dob): {afltables ids}} and {(first, last, dob): {clubs}}
    for every player on any start's list or list additions."""
    ids, clubs = defaultdict(set), defaultdict(set)
    for y in STARTS:
        for f in ("%d/players_%d.csv" % (y, y), "%d/list_additions_%d.csv" % (y, y)):
            with open(os.path.join(LEG, f), newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    k = (r["first"], r["last"], r["dob"])
                    ids[k]
                    clubs[k].add(r["club"])
    for dec in ("1990s", "2000s", "2010s", "2020s"):
        with open(os.path.join(LEG, dec, "lists.csv"), newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                k = (r["first"], r["last"], r["dob"])
                if k in ids and r.get("afltables_id"):
                    ids[k].add(r["afltables_id"])
    return ids, clubs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=os.path.join("C:/kt", "wiki_positions_cache"))
    args = ap.parse_args()
    wiki = Wiki(args.cache)
    players, clubs_of = load_players()
    print("players: %d" % len(players))
    found = resolve(wiki, players, clubs_of)
    by_id, _ = career_numbers()
    out = []
    counts = defaultdict(int)
    tall = heights()
    for key in sorted(players):
        first, last, dob = key
        title, body = found.get(key, ("", ""))
        pos, pos2, source, words = "", "", "", ""
        box = infobox_position(body) if body else ""
        if box and lines_in(box):
            ls = lines_in(box)
            pos, pos2, source, words = ls[0], (ls[1] if len(ls) > 1 else ""), "wiki_infobox", box
        elif body:
            w, ls = lead_position(body)
            if ls:
                pos, pos2, source, words = ls[0], (ls[1] if len(ls) > 1 else ""), "wiki_lead", w
        if not pos:
            tot = defaultdict(float)
            for pid in players[key]:
                for k, v in by_id.get(pid, {}).items():
                    tot[k] += v
            line = career_line(tot)
            if line:
                pos, source = line, "career"
                words = "%.0f games, %.2f goals and %.1f hit-outs a game" % (
                    tot["gm"], tot["gl"] / max(1, tot["gm"]), tot["ho"] / max(1, tot["gm"]))
        out.append({"first": first, "last": last, "dob": dob, "afltables_ids": ";".join(sorted(players[key])),
                    "pos": pos, "pos2": pos2,
                    "source": source, "wiki_title": title, "wiki_text": " ".join(words.split())[:120]})
    shapes = {}
    for r in out:
        tot = defaultdict(float)
        for pid in players[(r["first"], r["last"], r["dob"])]:
            for k, v in by_id.get(pid, {}).items():
                tot[k] += v
        shapes[(r["first"], r["last"], r["dob"])] = career_shape(tot, tall.get((r["first"], r["last"], r["dob"])))
    known = [(k, shapes[k], r["pos"]) for r in out for k in [(r["first"], r["last"], r["dob"])]
             if r["source"].startswith("wiki") and shapes[k]]
    unknown = [(k, shapes[k]) for r in out for k in [(r["first"], r["last"], r["dob"])] if not r["pos"] and shapes[k]]
    near = nearest_lines(known, unknown)
    for r in out:
        hit = near.get((r["first"], r["last"], r["dob"]))
        if hit:
            r["pos"], r["source"], r["wiki_text"] = hit[0], "nearest", "%d of the %d most similar careers" % (hit[1], NEAREST_K)
        counts[r["source"] or "none"] += 1
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print("wrote %s: %s" % (os.path.relpath(OUT, ROOT), dict(counts)))


if __name__ == "__main__":
    main()
