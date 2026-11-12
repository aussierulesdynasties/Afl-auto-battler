#!/usr/bin/env python3
"""Fetch the public pages behind data/legacy/2020s/ into a local cache.

Facts only, free public sources, no keys. Polite: one request at a time with a
pause, and every page is cached so a re-run fetches nothing twice.

    python tools/legacy_2020s/fetch.py --cache <dir> core      # years, lists, stats, ladders
    python tools/legacy_2020s/fetch.py --cache <dir> players   # one Draftguru page per listed player
    python tools/legacy_2020s/fetch.py --cache <dir> bios      # AFL Tables player pages (weight)

The cache is not committed; build.py reads it.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import sys
import time
import urllib.request

UA = "Mozilla/5.0 (compatible; AflAutoBattler-data/1.0; +https://github.com/aussierulesdynasties/Afl-auto-battler)"
DG = "https://www.draftguru.com.au"
SEASONS = range(2020, 2026)
# Draft years build.py reads: the 2019 off-season feeds a 2020 start; 2025 is the
# last off-season before the game's own 2026 data, which this never touches.
DRAFT_YEARS = range(2019, 2026)


def cache_path(cache: str, url: str) -> str:
    name = re.sub(r"^https?://", "", url)
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return os.path.join(cache, name + ".html")


def get(cache: str, url: str, pause: float = 0.6) -> str:
    path = cache_path(cache, url)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
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


def club_slugs(cache: str, year: int) -> list[str]:
    body = get(cache, f"{DG}/lists/{year}")
    return sorted(set(re.findall(rf'href="/lists/{year}/([a-z-]+)"', body)))


def core(cache: str) -> None:
    for y in DRAFT_YEARS:
        get(cache, f"{DG}/years/{y}")
    for y in SEASONS:
        for slug in club_slugs(cache, y):
            get(cache, f"{DG}/lists/{y}/{slug}")
        get(cache, f"https://afltables.com/afl/stats/{y}.html")
        get(cache, f"https://afltables.com/afl/seas/{y}.html")
        get(cache, f"https://api.squiggle.com.au/?q=standings;year={y}")
        get(cache, f"https://api.squiggle.com.au/?q=games;year={y}")
    # One page past the last draft year: Wikipedia files a mid-season rookie draft
    # under the year it is held, Draftguru under the off-season before it.
    for y in range(DRAFT_YEARS.start, DRAFT_YEARS.stop + 1):
        get(cache, f"https://en.wikipedia.org/wiki/{y}_AFL_draft")
    for y in SEASONS:
        # Season facts (round count, quarter length, relocated fixtures).
        get(cache, f"https://en.wikipedia.org/wiki/{y}_AFL_season")
    print("core done")


def players(cache: str) -> None:
    hrefs: set[str] = set()
    for y in SEASONS:
        for slug in club_slugs(cache, y):
            body = get(cache, f"{DG}/lists/{y}/{slug}")
            hrefs.update(html.unescape(h) for h in re.findall(r'href="(/players/[^"]+)"', body))
    # Players who moved in the 2019-2025 trade periods and drafts, so a move's
    # from-club can be read even when the player's next list is 2026.
    for y in DRAFT_YEARS:
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("step", choices=["core", "players", "bios"])
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    {"core": core, "players": players, "bios": bios}[a.step](a.cache)


if __name__ == "__main__":
    main()
