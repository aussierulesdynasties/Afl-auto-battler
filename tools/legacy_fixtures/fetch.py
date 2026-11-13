#!/usr/bin/env python3
"""Fetch the AFL Tables season pages behind data/legacy/fixtures.csv into a local cache.

Facts only, one free public source, no keys. Polite: one request at a time with a
pause, and every page is cached so a re-run fetches nothing twice.

    python tools/legacy_fixtures/fetch.py --cache <dir>

The cache is not committed (keep it outside the repo); build.py reads it. The
pages are the same ones tools/legacy_<decade>s/fetch.py caches, under the same
file names, so a decade cache can be copied in instead of fetching again.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
import urllib.request

UA = "Mozilla/5.0 (compatible; AflAutoBattler-data/1.0; +https://github.com/aussierulesdynasties/Afl-auto-battler)"
# Every real season Legacy mode can play: 1990 to the game's own 2026.
SEASONS = range(1990, 2027)


def season_url(year: int) -> str:
    return f"https://afltables.com/afl/seas/{year}.html"


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True, help="cache folder, outside the repo")
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    for y in SEASONS:
        if not get(a.cache, season_url(y)):
            raise SystemExit(f"no page for {y}")
    print(f"fetched {len(SEASONS)} season pages into {a.cache}")


if __name__ == "__main__":
    main()
