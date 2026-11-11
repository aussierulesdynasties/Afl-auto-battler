# Legacy mode data: the 2000s (row 142)

Real AFL lists, drafts, trades, ladders and season totals for 2000-2009, for a career that
starts in 2000 (one of the director's seven start dates, 2026-11-11). Research and data only; no
game code reads these files yet. No player is rated here.

Built 2026-11-11 by `tools/legacy_2000s/fetch.py` (polite cached fetch of free public pages;
the cache, `data/cache/legacy_2000s/`, is gitignored) and `tools/legacy_2000s/build.py`
(cache to CSV), both copied from `tools/legacy_2010s/` with the decade changed, so one loader
reads both decades: same files, same columns, same club codes. Checked by
`python tools/check_legacy_2000s.py`: **0 failures, 8 warnings** (gaps listed below).

## Files (`data/legacy/2000s/`)

| File | Rows | What it holds | Sources |
|---|---:|---|---|
| `lists.csv` | 7,031 | Every club's senior and rookie list per season 2000-2009, with DOB, height, weight, games/goals/votes that season and career, origin, first draft, and how and when the player joined. | Draftguru lists and player pages; AFL Tables season pages and bios |
| `drafts.csv` | 1,434 | The 1999 National Draft (before the 2000 season) to the 2008 drafts: National, Pre-season and Rookie drafts plus pre- and post-draft signings, with father-son, priority, international, scholarship and other flags. The 2009 draft is in `data/legacy/2010s`. | Draftguru years pages; Wikipedia `<year> AFL draft` |
| `moves.csv` | 204 | Trades in the 1999-2008 trade periods. No free agency: it began in the 2012 trade period. | Draftguru years and player pages |
| `ladders.csv` | 160 | Final home-and-away ladder per season with finals finish. | Squiggle standings and games; AFL Tables season page |
| `season_stats.csv` | 5,638 | AFL Tables season totals per player, per club, per season (same columns as the 2010s). | AFL Tables `stats/<year>.html` |
| `wikipedia_draft_counts.json` | - | Picks per draft per year as Wikipedia counts them. | Wikipedia |

**Era club codes.** Every 2000-2009 club already plays under its 2000s name: the Brisbane
Lions (BRL) and Western Bulldogs (WBD) from 1997, North Melbourne (NTH) also for its
Kangaroos years (1999-2007). Only `joined_from` reaches back before 1997, and it takes the
name of that season, as in `data/legacy/1990s`: FIT Fitzroy, BRB Brisbane Bears, FOO
Footscray (30 rows, for example Alastair Lynch, traded from Fitzroy to Brisbane in 1993).

## List rows per club and season

| Club | 2000 | 2001 | 2002 | 2003 | 2004 | 2005 | 2006 | 2007 | 2008 | 2009 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ADE | 47 | 44 | 44 | 43 | 43 | 44 | 44 | 44 | 44 | 45 |
| BRL | 44 | 44 | 40 | 41 | 43 | 44 | 47 | 46 | 47 | 46 |
| CAR | 46 | 44 | 44 | 43 | 43 | 44 | 44 | 43 | 44 | 46 |
| COL | 46 | 44 | 43 | 44 | 44 | 44 | 44 | 44 | 44 | 47 |
| ESS | 44 | 43 | 41 | 44 | 44 | 44 | 44 | 44 | 44 | 46 |
| FRE | 46 | 44 | 43 | 41 | 44 | 44 | 44 | 44 | 44 | 46 |
| GEE | 46 | 44 | 44 | 44 | 44 | 44 | 44 | 44 | 44 | 47 |
| HAW | 44 | 42 | 44 | 44 | 44 | 44 | 44 | 45 | 44 | 47 |
| MEL | 46 | 44 | 42 | 44 | 44 | 41 | 44 | 44 | 44 | 46 |
| NTH | 45 | 45 | 43 | 44 | 39 | 43 | 44 | 44 | 45 | 46 |
| PAD | 46 | 44 | 44 | 40 | 43 | 43 | 44 | 44 | 44 | 45 |
| RIC | 45 | 43 | 42 | 39 | 42 | 40 | 42 | 44 | 44 | 45 |
| STK | 46 | 42 | 40 | 39 | 39 | 40 | 41 | 44 | 45 | 48 |
| SYD | 47 | 45 | 46 | 43 | 44 | 47 | 48 | 46 | 47 | 46 |
| WBD | 46 | 43 | 43 | 39 | 41 | 42 | 41 | 44 | 44 | 45 |
| WCE | 46 | 44 | 44 | 44 | 44 | 44 | 44 | 44 | 45 | 47 |
| **All** | 730 | 699 | 687 | 676 | 685 | 692 | 703 | 708 | 713 | 738 |

Senior / rookie per season: 2000 656/74, 2001 623/76, 2002 611/76, 2003 603/73, 2004 616/69,
2005 625/67, 2006 629/74, 2007 632/76, 2008 632/81, 2009 634/101 (plus 3 that Draftguru marks
Category B in 2009: Brian Donnelly, Michael Quinn, Blake McGrath). 1,745 players in all.
Players with an AFL Tables season row: 543-577 per season.

How players joined (all list rows): national draft 3,844; rookie draft 1,369; trade 959;
pre-season draft 359; foundation 119 (Adelaide, Fremantle, Port Adelaide); zone 61;
father-son 57; Fremantle-era underage and uncontracted concessions 47; other signings 21;
mid-season draft 8; none recorded 187.

## Drafts covered

| Draft year | National (Draftguru / Wikipedia) | Pre-season | Rookie |
|---|---|---|---|
| 1999 | 87 / 87 | 15 / 15 | 55 / 63 |
| 2000 | 72 / 74 | 11 / 11 | 54 / 60 |
| 2001 | 68 / 74 | 5 / 5 | 54 / 59 |
| 2002 | 67 / 69 | 4 / 5 | 50 / 58 |
| 2003 | 68 / 71 | 11 / 11 | 46 / 57 |
| 2004 | 69 / 71 | 7 / 7 | 47 / 51 |
| 2005 | 66 / 66 | 10 / 10 | 49 / 56 |
| 2006 | 79 / 80 | 8 / 9 | 50 / 62 |
| 2007 | 67 / 69 | 8 / 8 | 54 / 62 |
| 2008 | 79 / 79 | 6 / 6 | 62 / 74 |

Every Draftguru pick matches Wikipedia's player at the same number, outside two spellings
recorded in the checker (Brent Piltz, Andrew Ericksen). Wikipedia's extra 101 picks are kept
with `only_in=wikipedia` (re-listed and re-drafted players, rookie elevations).

## What the checker verifies

- Exactly the 16 clubs every season in lists, season totals and ladders; no duplicate list row.
- Draft picks against Wikipedia, as in the 2010s check.
- Every move has both clubs and they differ; no free-agent move before 2012.
- Ladders: 16 clubs, 22 games each, points equal 4W+2D, one premier, one runner-up, eight
  finalists. Premiers: 2000 ESS, 2001-03 BRL, 2004 PAD, 2005 SYD, 2006 WCE, 2007 GEE,
  2008 HAW, 2009 GEE.

## Gaps (reported, not filled)

- **Position**: blank on every row (no free source per season).
- **Weight**: blank on 1,397 rows (no AFL Tables bio match, mostly players with no game).
- **No join recorded (187 rows, 55 players)**: veterans recruited before Draftguru's records
  begin (zone and pre-draft recruits such as Michael Voss, Stephen Silvagni, Robert Harvey).
  Their pages carry no movement line.
- **List limits**: 26 club-seasons over the 2010s limits, by one or two (Draftguru counts
  everyone listed during the season).
- **Setanta Ó hAilpín** (CAR 2005-09): no AFL Tables match (name spelling).

## Sources

All free, public, no key, fetched 2026-11-11.

- Draftguru: `https://www.draftguru.com.au/lists/<year>/<club>` (2000-2009),
  `/years/<year>` (1986-2009), `/players/<slug>/<n>`. Its player "Grade" is not copied.
- AFL Tables: `https://afltables.com/afl/stats/<year>.html`, `/afl/seas/<year>.html`,
  `/afl/stats/players/<letter>/<player>.html`.
- Squiggle API: `https://api.squiggle.com.au/?q=standings;year=<year>`, `?q=games;year=<year>`.
- Wikipedia: `https://en.wikipedia.org/wiki/<year>_AFL_draft` (1999-2008).

Rebuild: `python tools/legacy_2000s/fetch.py --cache data/cache/legacy_2000s core`, then
`players`, then `bios`; `python tools/legacy_2000s/build.py --cache data/cache/legacy_2000s`;
`python tools/check_legacy_2000s.py`.
