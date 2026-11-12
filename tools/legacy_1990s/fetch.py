#!/usr/bin/env python3
"""Fetch the public pages behind data/legacy/1990s/ into a local cache.

Facts only, free public sources, no keys. Polite: one request at a time with a
pause (a few workers at most for the per-player pages), and every page is
cached so a re-run fetches nothing twice. Same method as tools/legacy_2010s.

    python tools/legacy_1990s/fetch.py --cache data/cache/legacy_1990s core      # lists, stats, ladders, drafts
    python tools/legacy_1990s/fetch.py --cache data/cache/legacy_1990s players   # one Draftguru page per listed player
    python tools/legacy_1990s/fetch.py --cache data/cache/legacy_1990s bios      # AFL Tables player pages (weight)
    python tools/legacy_1990s/fetch.py --cache data/cache/legacy_1990s pre       # 1987-89, the 1990 start, era rules, grounds
    python tools/legacy_1990s/fetch.py --cache data/cache/legacy_1990s rules     # era rules' pages only

A PDF source is cached as its text (pdftotext -layout, from poppler).

The cache is not committed (data/cache/ is gitignored); build.py reads it.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

UA = "Mozilla/5.0 (compatible; AflAutoBattler-data/1.0; +https://github.com/aussierulesdynasties/Afl-auto-battler)"
DG = "https://www.draftguru.com.au"
SEASONS = range(1990, 2000)
# Draftguru's year pages start with the first National Draft (1986). The 1989
# drafts fed the 1990 lists; 1999's fed 2000.
DRAFT_YEARS = range(1986, 2000)
WIKI_DRAFT_YEARS = range(1989, 2000)


def club_slugs(year: int) -> list[str]:
    """Draftguru list slugs for the clubs that played the AFL season `year`.

    Era facts, not the site's index (its 1990 index is empty): 14 clubs in 1990
    with Fitzroy and the Brisbane Bears ("brisbane") and Footscray
    ("western-bulldogs"); Adelaide from 1991, Fremantle from 1995, Port Adelaide
    from 1997; Fitzroy's last season 1996 (merged into the Brisbane Lions).
    """
    s = ["brisbane", "carlton", "collingwood", "essendon", "geelong", "hawthorn", "melbourne",
         "north-melbourne", "richmond", "st-kilda", "sydney", "west-coast", "western-bulldogs"]
    if year <= 1996:
        s.append("fitzroy")
    if year >= 1991:
        s.append("adelaide")
    if year >= 1995:
        s.append("fremantle")
    if year >= 1997:
        s.append("port-adelaide")
    return sorted(s)


def wiki_draft_url(year: int) -> str:
    """Wikipedia names the 1989 draft for the VFL (renamed the AFL in 1990)."""
    league = "VFL" if year <= 1989 else "AFL"
    return f"https://en.wikipedia.org/wiki/{year}_{league}_draft"


def cache_path(cache: str, url: str) -> str:
    name = re.sub(r"^https?://", "", url)
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return os.path.join(cache, name + ".html")


def get(cache: str, url: str, pause: float = 0.6) -> str:
    path = cache_path(cache, url)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    body = ""
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as resp:
                body = resp.read().decode("utf-8", "replace")
            break
        except Exception as exc:  # network hiccup: back off and retry
            if attempt == 3:
                print(f"FAIL {url}: {exc}", file=sys.stderr)
                return ""
            time.sleep(3 * (attempt + 1))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    time.sleep(pause)
    return body


def get_pdf(cache: str, url: str) -> str:
    """A PDF's text, as pdftotext -layout reads it, cached like a page."""
    path = cache_path(cache, url)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    tool = shutil.which("pdftotext")
    if not tool:
        raise SystemExit("pdftotext (poppler) is needed to read " + url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    with tempfile.TemporaryDirectory() as tmp:
        pdf, txt = os.path.join(tmp, "src.pdf"), os.path.join(tmp, "src.txt")
        with open(pdf, "wb") as fh:
            fh.write(data)
        subprocess.run([tool, "-layout", "-enc", "UTF-8", pdf, txt], check=True)
        with open(txt, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return body


def core(cache: str) -> None:
    for y in DRAFT_YEARS:
        get(cache, f"{DG}/years/{y}")
    for y in SEASONS:
        for slug in club_slugs(y):
            get(cache, f"{DG}/lists/{y}/{slug}")
        get(cache, f"https://afltables.com/afl/stats/{y}.html")
        get(cache, f"https://afltables.com/afl/seas/{y}.html")
        get(cache, f"https://api.squiggle.com.au/?q=standings;year={y}")
    for y in WIKI_DRAFT_YEARS:
        get(cache, wiki_draft_url(y))
    print("core done")


def players(cache: str) -> None:
    hrefs: set[str] = set()
    for y in SEASONS:
        for slug in club_slugs(y):
            body = get(cache, f"{DG}/lists/{y}/{slug}")
            hrefs.update(html.unescape(h) for h in re.findall(r'href="(/players/[^"]+)"', body))
    # Players who moved in the 1989-1999 trade periods and drafts, so a move's
    # from-club can be read even when the player's next list is 2000.
    for y in WIKI_DRAFT_YEARS:
        body = get(cache, f"{DG}/years/{y}")
        hrefs.update(html.unescape(h) for h in re.findall(r'href="(/players/[^"]+)"', body))
    todo = sorted(hrefs)
    print(f"{len(todo)} player pages")
    # Three polite workers: a small site, so no more than that.
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as pool:
        for i, _ in enumerate(pool.map(lambda h: get(cache, DG + h, pause=0.4), todo)):
            if i % 250 == 0:
                print(i, flush=True)
    print("players done")


def bios(cache: str) -> None:
    hrefs: set[str] = set()
    for y in SEASONS:
        body = get(cache, f"https://afltables.com/afl/stats/{y}.html")
        hrefs.update(re.findall(r'href="(players/[^"]+\.html)"', body))
    todo = sorted(hrefs)
    print(f"{len(todo)} AFL Tables bios")
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as pool:
        for i, _ in enumerate(pool.map(lambda h: get(cache, "https://afltables.com/afl/stats/" + h, pause=0.4), todo)):
            if i % 250 == 0:
                print(i, flush=True)
    print("bios done")


# ------------------------------------------------------------- the 1990 start
# The seasons before the first one a career can start in: their stats, the 1989
# ladder (the 1990 draft order) and the bios behind each player's games before 1990.
PRE_SEASONS = range(1987, 1990)
WIKI = "https://en.wikipedia.org/wiki/"
# AFL Tables team slugs for its coaches pages, by the 1990 clubs.
COACH_PAGES = ["brisbaneb", "carlton", "collingwood", "essendon", "fitzroy", "bullldogs", "geelong",
               "hawthorn", "melbourne", "kangaroos", "richmond", "stkilda", "swans", "westcoast"]
# Era rules: each value in era_rules.csv quotes one of these pages.
RULE_PAGES = ["AFL_salary_cap", "Australian_Football_League", "Interchange_(Australian_rules_football)",
              "Rookie_list"]
# Era-rule sources off Wikipedia, by full URL: the AFL's annual reports (the
# footyindustry.com archive) and AFL articles, and Canberra Times articles on Trove, for the salary caps.
AR = "https://footyindustry.com/docs/AFL%20{}%20Annual%20{}.pdf"
RULE_SOURCES = [AR.format(2006, "report"), AR.format(2010, "Report"), AR.format(2011, "Report"),
                AR.format(2019, "Report"), AR.format(2021, "Report"),
                "https://www.afl.com.au/news/96194/an-ever-changing-game",
                # Canberra Times articles on Trove: the 1993 cap; the 1995 and 1996 caps.
                "https://trove.nla.gov.au/newspaper/article/118214696",
                "https://trove.nla.gov.au/newspaper/article/130564397",
                # Macdonald & Borland's table of AFL player payments 1992-2003 (Fort & Fizel,
                # International Sports Economics Comparisons, 2004, p. 304), as Google Books'
                # search-inside snippet: the 1992 and 1994 caps. Google answers scripted
                # requests from some addresses with 429; the cached copy was saved from a browser.
                "https://books.google.com.au/books?id=QFDeEAAAQBAJ&newbks=0&hl=en"
                "&q=%221992-2003+1992+1993+1994%22+%22TPP+per+Club%22"]
# AFL Tables venue page -> the ground's Wikipedia article (its infobox's former names).
GROUND_ARTICLES = {
    "mcg": "Melbourne_Cricket_Ground", "waverley_park": "Waverley_Park", "princes_park": "Princes_Park_(stadium)",
    "carrara": "Carrara_Stadium", "scg": "Sydney_Cricket_Ground", "western_oval": "Whitten_Oval",
    "kardinia_park": "Kardinia_Park_(stadium)", "moorabbin_oval": "Moorabbin_Oval", "windy_hill": "Windy_Hill,_Essendon",
    "subiaco": "Subiaco_Oval", "victoria_park": "Victoria_Park,_Melbourne", "waca": "WACA_Ground",
    "football_park": "Football_Park", "gabba": "The_Gabba", "north_hobart": "North_Hobart_Oval",
    "bruce_stadium": "Canberra_Stadium", "manuka_oval": "Manuka_Oval", "docklands": "Docklands_Stadium",
    "stadium_australia": "Stadium_Australia", "junction_oval": "Junction_Oval",
    "arden_st": "Arden_Street_Oval", "glenferrie_oval": "Glenferrie_Oval",
}


def pre(cache: str) -> None:
    for y in PRE_SEASONS:
        get(cache, f"https://afltables.com/afl/stats/{y}.html")
        get(cache, f"https://afltables.com/afl/seas/{y}.html")
    get(cache, "https://api.squiggle.com.au/?q=standings;year=1989")
    get(cache, WIKI + "1990_AFL_season")
    for slug in COACH_PAGES:
        get(cache, f"https://afltables.com/afl/stats/coaches/{slug}.html")
    rules(cache)
    for page in sorted(set(GROUND_ARTICLES.values())):
        get(cache, WIKI + page)
    # Bios of the players in the 1987-89 stats not already cached (most are:
    # anyone who also played in the 1990s). build.py reads only the ones whose
    # player is on a 1990 list.
    hrefs: set[str] = set()
    for y in PRE_SEASONS:
        hrefs.update(re.findall(r'href="(players/[^"]+\.html)"', get(cache, f"https://afltables.com/afl/stats/{y}.html")))
    todo = sorted(h for h in hrefs if not os.path.exists(cache_path(cache, "https://afltables.com/afl/stats/" + h)))
    print(f"{len(todo)} more AFL Tables bios")
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda h: get(cache, "https://afltables.com/afl/stats/" + h, pause=0.4), todo))
    print("pre done")


def rules(cache: str) -> None:
    for page in RULE_PAGES:
        get(cache, WIKI + page)
    for url in RULE_SOURCES:
        (get_pdf if url.endswith(".pdf") else get)(cache, url)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("step", choices=["core", "players", "bios", "pre", "rules"])
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    {"core": core, "players": players, "bios": bios, "pre": pre, "rules": rules}[a.step](a.cache)


if __name__ == "__main__":
    main()
