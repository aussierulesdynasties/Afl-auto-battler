"""Rate each 1990 coach from his real senior record before 1990 (director 2026-11-13, "Rate from records").

Reads data/legacy/1990s/coaches_1990.csv for the names and one AFL Tables coach page per name
(cached under data/cache/legacy_1990s/coaches/, fetched once when missing), and writes
data/legacy/1990s/coach_ratings_1990.csv: the record up to 1989 and the three skills the game uses
(teach, tactics, manage; 55-92, never shown as numbers).

    python tools/legacy_1990s/rate_coaches.py            # fetch missing pages, write the CSV
    python tools/legacy_1990s/rate_coaches.py --offline  # cache only

The scale is the 2026 seed's: its senior coaches average teach 72, tactics 78, manage 79.
- A record is the club's win rate, pulled toward 50% by half a season of even games each way, so a
  short record moves a coach less than a long one.
- Tactics: the win rate, plus 2.5 a premiership and 1 a grand final lost.
- Manage: the win rate (less), the seasons in the job (up to 10), and 1.5 a premiership.
- Teach: a win-loss record says little about teaching, so it moves least.
- A senior coach with under one season of games (22) rates as unproven: 3 under the 2026 mean on
  tactics and manage. A reserves or under-19s coach keeps the assistants' 62 unless his senior
  record is a season or more.
"""

import argparse
import csv
import html
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COACHES = ROOT / "data/legacy/1990s/coaches_1990.csv"
OUT = ROOT / "data/legacy/1990s/coach_ratings_1990.csv"
CACHE = ROOT / "data/cache/legacy_1990s/coaches"
URL = "https://afltables.com/afl/stats/coaches/%s.html"
BEFORE = 1990
# AFL Tables names some coaches differently from the 1990 club records.
PAGE_NAME = {"Michael Malthouse": "Mick_Malthouse", "Colin Kinnear": "Col_Kinnear"}
SC_MEAN = {"teach": 72, "tactics": 78, "manage": 79}
SECOND = {"teach": 62, "tactics": 62, "manage": 62}
UNPROVEN = {"teach": 72, "tactics": 75, "manage": 76}


def page_for(name: str, offline: bool) -> str:
    stem = PAGE_NAME.get(name, name.replace(" ", "_"))
    path = CACHE / f"{stem}.html"
    if not path.exists() and not offline:
        CACHE.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(URL % stem, headers={"User-Agent": "legacy-data-builder"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                path.write_bytes(r.read())
        except Exception:
            path.write_text("")  # no page: no senior record
        time.sleep(1.0)
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def record(page: str) -> dict:
    rec = {"seasons": 0, "games": 0, "wins": 0, "draws": 0, "flags": 0, "grand_finals": 0, "finals_wins": 0}
    for tr in re.findall(r"<tr>(.*?)</tr>", page, re.S):
        c = [html.unescape(re.sub("<[^>]+>", "", x)).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(c) < 19 or not c[0].isdigit() or int(c[0]) >= BEFORE:
            continue
        n = lambda s: int(s) if s.isdigit() else 0
        rec["seasons"] += 1
        rec["games"] += n(c[15])
        rec["wins"] += n(c[12])
        rec["draws"] += n(c[13])
        rec["finals_wins"] += n(c[7])
        rec["flags"] += c[17] == "X"
        rec["grand_finals"] += c[18] == "X"
    return rec


def rate(role: str, rec: dict) -> dict:
    if rec["games"] < 22:
        return dict(UNPROVEN if role == "senior" else SECOND)
    p = (rec["wins"] + rec["draws"] / 2 + 11) / (rec["games"] + 22) - 0.5
    lost_gf = rec["grand_finals"] - rec["flags"]
    years = min(rec["seasons"], 10)
    clamp = lambda v, lo, hi: max(lo, min(hi, round(v)))
    return {
        "teach": clamp(SC_MEAN["teach"] + 10 * p + 0.3 * years - 1.5, 59, 86),
        "tactics": clamp(SC_MEAN["tactics"] + 30 * p + 2.5 * rec["flags"] + lost_gf, 66, 90),
        "manage": clamp(SC_MEAN["manage"] + 20 * p + 0.4 * years - 2 + 1.5 * rec["flags"], 64, 92),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    rows = list(csv.DictReader(COACHES.open(encoding="utf-8")))
    out = []
    for r in rows:
        name = r["name"].strip()
        if not name:
            continue
        rec = record(page_for(name, args.offline))
        sk = rate(r["role"], rec)
        stem = PAGE_NAME.get(name, name.replace(" ", "_"))
        out.append({"name": name, "role": r["role"], **rec, **sk,
                    "source_url": URL % stem if rec["seasons"] else ""})
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out)} coaches")


if __name__ == "__main__":
    main()
