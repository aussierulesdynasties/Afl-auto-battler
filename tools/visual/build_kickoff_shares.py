#!/usr/bin/env python3
"""Build data/kickoff_by_venue.json: how often each AFL ground hosted a day, twilight or
night match in 2026, for the match scenes' time of day (scripts/ui/match/VignetteKickoff.gd).
Looks only: the simulation never reads it.

Source: data/raw/fixtures_2026.json (Squiggle, every 2026 match with its local start time).
A start before 16:00 local is a day match, 16:00 to 17:59 twilight, 18:00 or later night.
Squiggle's venue names are mapped to the keys of data/grounds.json; a ground that is not
in grounds.json keeps its Squiggle name. A ground with fewer than MIN_GAMES matches is
listed with its count but the game uses the league-wide share for it.

    python tools/visual/build_kickoff_shares.py            # rewrite the file
    python tools/visual/build_kickoff_shares.py --check    # exit 1 if the file is stale
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "raw" / "fixtures_2026.json"
OUT = ROOT / "data" / "kickoff_by_venue.json"
SLOTS = ["day", "twilight", "night"]
MIN_GAMES = 6
NAMES = {
    "M.C.G.": "MCG",
    "Docklands": "Marvel Stadium",
    "Perth Stadium": "Optus Stadium",
    "S.C.G.": "SCG",
    "Gabba": "The Gabba",
    "Kardinia Park": "GMHBA Stadium",
    "Carrara": "People First Stadium",
    "Sydney Showground": "Engie Stadium",
}


def slot_of(localtime: str) -> str:
    hour = int(localtime[11:13])
    if hour < 16:
        return "day"
    return "twilight" if hour < 18 else "night"


def shares(counts: Counter) -> dict:
    n = sum(counts.values())
    out = {s: round(counts[s] / n, 3) for s in SLOTS}
    out["games"] = n
    return out


def build() -> dict:
    games = json.loads(SRC.read_text(encoding="utf-8"))["games"]
    by_venue = defaultdict(Counter)
    league = Counter()
    for g in games:
        s = slot_of(g["localtime"])
        by_venue[NAMES.get(g["venue"], g["venue"])][s] += 1
        league[s] += 1
    venues = {v: shares(c) for v, c in sorted(by_venue.items())}
    return {
        "_about": "Share of 2026 AFL matches at each ground that started by day (before 16:00 local), "
                  "at twilight (16:00 to 17:59) or at night (18:00 on), from data/raw/fixtures_2026.json "
                  "(Squiggle). Built by tools/visual/build_kickoff_shares.py; do not edit by hand. Looks "
                  "only: the match scenes pick their sky from it and the simulation never reads it.",
        "min_games": MIN_GAMES,
        "default": shares(league),
        "venues": venues,
    }


def main() -> int:
    text = json.dumps(build(), indent=1) + "\n"
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("data/kickoff_by_venue.json is stale: run tools/visual/build_kickoff_shares.py")
            return 1
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
