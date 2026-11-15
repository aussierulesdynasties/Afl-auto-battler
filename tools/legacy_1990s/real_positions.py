"""Real positions for the players of the pre-2003 data seasons.

Director 2026-11-15, "Source real positions": AFL Tables keeps no position, and
the stats it lacks before 2003 (rebound 50s, contested possessions...) cannot
tell a centre half-forward from a defender (Garry Lyon). So a player's
position comes from his Wikipedia article: the infobox "position" field first;
with no infobox position, the whole article read by hand.

Director 2026-11-15, "dont skim the articles": Matthew Campbell's opening
paragraph names no position, but his career section says "a quick wingman".
Every sentence of every such article that names a position was read, and the
player's main one written to positions_read.csv with the article's own words.
A player whose article names two roles equally, only an early-career or
state-league one, or a single game's, is not in that file: his recorded
stats place him.

1. Wikidata: AFL Tables id (P3547) -> English Wikipedia article.
2. Wikipedia: each article's infobox position (section 0 wikitext).
3. positions_read.csv: the hand-read articles (article,position,quote).
4. positions_afc.csv: australianfootball.com biographies read by hand for the
   players none of the above places (afltables_id,position,quote,source_url).
   A position naming several roles ("DEF|MID") lets his recorded stats choose
   among them (director 2026-11-15).

Writes data/legacy/positions.csv: afltables_id,position,record,from,source_url.
A player with no record is left out; the builders then read his recorded stats.
Fetches are cached in --cache, so a rerun only asks for what is new.

    python tools/legacy_1990s/real_positions.py --cache <dir>
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_start as B  # noqa: E402

OUT = os.path.join(B.LEG, "positions.csv")
UA = "legacy-data-check/1.0 (research script)"
BEFORE = 2003   # B.FULL_STATS_FROM: from 2003 the recorded stats read a position
SPARQL = ("SELECT ?id ?art WHERE { ?p wdt:P3547 ?id . ?art schema:about ?p ; "
          "schema:isPartOf <https://en.wikipedia.org/> . }")


def get(url, params):
    q = urllib.parse.urlencode(params)
    for attempt in range(8):
        try:
            req = urllib.request.Request(url + "?" + q, headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except urllib.error.HTTPError as e:
            time.sleep(int(e.headers.get("Retry-After") or 0) or 5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    sys.exit("gave up on " + url)


def cached(cache, name, fill):
    path = os.path.join(cache, name)
    out = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    fill(out, lambda: json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False))
    return out


def articles(cache):
    def fill(out, save):
        if out:
            return
        d = get("https://query.wikidata.org/sparql", {"query": SPARQL, "format": "json"})
        for b in d["results"]["bindings"]:
            out[b["id"]["value"]] = b["art"]["value"]
        save()
    return cached(cache, "articles.json", fill)


def batch_pages(titles, params, out, save, pick):
    todo = [t for t in titles if t not in out]
    for i in range(0, len(todo), 20):
        b = todo[i:i + 20]
        d = get("https://en.wikipedia.org/w/api.php", dict(params, format="json", formatversion="2",
                                                            redirects="1", titles="|".join(t.replace("_", " ") for t in b)))
        back = {}
        for k in ("normalized", "redirects"):
            for n in d["query"].get(k, []):
                back[n["to"]] = back.get(n["from"], n["from"])
        for p in d["query"]["pages"]:
            out[back.get(p["title"], p["title"]).replace(" ", "_")] = pick(p)
        for t in b:
            out.setdefault(t, "")
        save()
        time.sleep(1.5)


def infobox(p):
    txt = p.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("content", "")
    m = re.search(r"^\s*\|\s*position\s*=\s*(.*)$", txt, re.M | re.I)
    return m.group(1).strip() if m else ""


def first_info(v):
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", v or "")
    s = re.sub(r"\{\{[^}]*\}\}", "", s).strip()
    if not s or s.startswith("|"):
        return ""
    return re.split(r"[,/;<\n(]|&lt;| and | or ", s)[0].strip()


INFO = [("ruck-rover", "MID"), ("ruck rover", "MID"), ("ruck", "RUCK"), ("follower", "RUCK"), ("forward", "FWD"),
        ("back", "DEF"), ("defen", "DEF"), ("rover", "MID"), ("wing", "MID"), ("centre", "MID"), ("midfield", "MID"),
        ("tagger", "MID"), ("on-ball", "MID"), ("onball", "MID")]

READ = os.path.join(HERE, "positions_read.csv")
AFC = os.path.join(HERE, "positions_afc.csv")


def info_role(s):
    s = s.lower()
    return next((r for k, r in INFO if k in s), "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True, help="folder for the Wikidata and Wikipedia fetches")
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    art = articles(a.cache)
    ids = sorted({r["afltables_id"].split("players/")[-1].replace(".html", "")
                  for y, rows in B.load_seasons().items() if y < BEFORE for r in rows if r.get("afltables_id")})
    title = {i: urllib.parse.unquote(art[i].rsplit("/", 1)[1]) for i in ids if i in art}
    info = cached(a.cache, "infobox.json", lambda out, save: batch_pages(
        sorted(set(title.values())), {"action": "query", "prop": "revisions", "rvprop": "content",
                                      "rvslots": "main", "rvsection": "0"}, out, save, infobox))
    read = {r["article"]: r for r in csv.DictReader(open(READ, encoding="utf-8"))}
    unknown = sorted(set(read) - set(title.values()))
    if unknown:
        sys.exit("positions_read.csv names articles no player links to: %s" % unknown)
    rows, n = [], {"infobox": 0, "article (read by hand)": 0, "none": 0, "no article": len(ids) - len(title)}
    for pid in ids:
        t = title.get(pid)
        if not t:
            continue
        raw = first_info(info.get(t, ""))
        role, how = info_role(raw) if raw else "", "infobox"
        if not role and t in read:
            role, raw, how = read[t]["position"], read[t]["quote"], "article (read by hand)"
        n[how if role else "none"] += 1
        if role:
            rows.append({"afltables_id": "players/%s.html" % pid, "position": role, "record": raw,
                         "from": how, "source_url": art[pid]})
    placed = {r["afltables_id"] for r in rows}
    n["australianfootball.com (read by hand)"] = 0
    for r in csv.DictReader(open(AFC, encoding="utf-8")):
        if r["afltables_id"] in placed:
            sys.exit("positions_afc.csv places a player already placed: %s" % r["afltables_id"])
        n["australianfootball.com (read by hand)"] += 1
        rows.append({"afltables_id": r["afltables_id"], "position": r["position"], "record": r["quote"],
                     "from": "australianfootball.com (read by hand)", "source_url": r["source_url"]})
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["afltables_id", "position", "record", "from", "source_url"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(len(ids), "players before %d:" % BEFORE, n)


if __name__ == "__main__":
    main()
