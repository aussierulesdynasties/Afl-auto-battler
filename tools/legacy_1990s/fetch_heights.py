"""Heights the club lists leave blank, from each player's Draftguru page.

Director 2026-11-15, "Search other sources": a height the lists don't give is
looked up elsewhere; when no source gives it, it stays blank and counts for
nothing (never a position average).

Writes data/legacy/heights.csv: draftguru_id,height_cm,source_url,checked.
A blank height_cm means the page was read and gives none. Ids already in the
file are skipped, so a rerun only fetches new ones.

    python tools/legacy_1990s/fetch_heights.py
"""
import csv
import datetime
import glob
import os
import re
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEG = os.path.join(ROOT, "data", "legacy")
OUT = os.path.join(LEG, "heights.csv")
COLS = ["draftguru_id", "height_cm", "source_url", "checked"]
UA = "legacy-data-check/1.0 (research script)"


def wanted():
    """Draftguru ids with no height on any club list row."""
    known, need = set(), set()
    for f in glob.glob(os.path.join(LEG, "*s", "lists*.csv")):
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["draftguru_id"]:
                    (known if r["height_cm"].strip() else need).add(r["draftguru_id"])
    for f in glob.glob(os.path.join(LEG, "*s", "drafts.csv")):
        with open(f, newline="", encoding="utf-8") as fh:
            need.update(r["draftguru_id"] for r in csv.DictReader(fh) if r["draftguru_id"])
    return sorted(need - known)


def height_of(page):
    m = re.search(r"Height:\s*(?:<[^>]*>\s*)*(\d{3})\s*cm", page)
    return m.group(1) if m else ""


def main():
    rows = {}
    if os.path.exists(OUT):
        with open(OUT, newline="", encoding="utf-8") as fh:
            rows = {r["draftguru_id"]: r for r in csv.DictReader(fh)}
    today = datetime.date.today().isoformat()
    todo = [d for d in wanted() if d not in rows]
    for i, dg in enumerate(todo):
        url = "https://www.draftguru.com.au" + dg
        for attempt in range(4):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
                break
            except Exception:
                time.sleep(5 * (attempt + 1))
        else:
            continue
        rows[dg] = {"draftguru_id": dg, "height_cm": height_of(page), "source_url": url, "checked": today}
        if i % 25 == 0:
            write(rows)
        time.sleep(0.8)
    write(rows)
    print(len(rows), "ids;", sum(1 for r in rows.values() if r["height_cm"]), "with a height")


def write(rows):
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows[k] for k in sorted(rows))


if __name__ == "__main__":
    main()
