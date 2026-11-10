# Legacy mode data: the 2010s (row 142)

The first data step for Legacy mode (TODO row 142, parked): real AFL lists, drafts, list
moves, ladders and season totals for 2010-2019, for a career that starts in 2010. Research and
data only; no game code reads these files yet. No player is rated here.

Built 2026-11-10 by `tools/legacy_2010s/fetch.py` (polite cached fetch of free public pages;
the cache is not committed) and `tools/legacy_2010s/build.py` (cache to CSV). Checked by
`python tools/check_legacy_2010s.py`: **0 failures, 7 warnings** (gaps listed below).

## Files (`data/legacy/2010s/`)

Every file has a `year` column, the 2026 data's club codes (`data/clubs.csv`), a `source_url`
and a `checked` date.

| File | Rows | What it holds | Sources |
|---|---:|---|---|
| `lists.csv` | 8,113 | Every club's list per season 2010-2019: senior, rookie and Category B, with an `underage` flag (GC and GWS underage signings). DOB, height, weight, games/goals/coach votes/Brownlow votes that season, career games/goals before the season and to its end, origin, first draft, and how and when the player joined the club. | Draftguru lists and player pages; AFL Tables season pages and player bios (weight) |
| `drafts.csv` | 1,766 | 2009 National to 2019: National, Pre-season, Rookie, mini and mid-season drafts plus the pre- and post-draft signings. Round, overall pick, club, player, origin, flag (father-son, academy, NGA, zone, priority, compensation, underage/uncontracted concession, international, scholarship, supplemental, top-up). | Draftguru years pages; Wikipedia `<year> AFL draft` (round, notes, flags) |
| `moves.csv` | 415 | Trade periods and free agency 2009-2019 (2009-2011 included: the 2009 period feeds a 2010 start): trades, restricted and unrestricted free agents with compensation, delisted free agents, GC/GWS uncontracted concessions. | Draftguru years and player pages; Wikipedia free-agency tables |
| `ladders.csv` | 177 | Final home-and-away ladder per season, with finals finish (premiers, runners_up, prelim, semi, elim). | Squiggle standings and games; AFL Tables season page (points) |
| `season_stats.csv` | 6,527 | Per player, per club, per season 2010-2019: AFL Tables season totals (GM KI MK HB DI DA GL BH HO TK RB IF CL CG FF FA BR CP UP CM MI 1% BO GA %P). | AFL Tables `stats/<year>.html` |
| `wikipedia_draft_counts.json` | - | Picks per draft per year and free agents per year as Wikipedia counts them; the checker compares against it. | Wikipedia |

Column meanings follow the 2026 files: `club`, `first`, `last`, `dob`, `height_cm`, `list`
(as `list_additions_2026.csv`); `from_club`, `to_club`, `kind` (as `club_moves_2026.csv`,
with `free_agent` split into `free_agent_restricted`, `free_agent_unrestricted`,
`delisted_free_agent`); `pos`, `w`, `l`, `d`, `pts`, `pct`, `finals` (as `ladder_2026.csv`).

## List rows per club and season

Draftguru lists everyone on a list at any point of the season, so a mid-season replacement
or a rookie elevated during the year counts once at the club.

| Club | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ADE | 47 | 47 | 48 | 47 | 45 | 45 | 46 | 45 | 44 | 44 |
| BRL | 46 | 46 | 48 | 46 | 46 | 47 | 47 | 48 | 46 | 47 |
| CAR | 46 | 47 | 48 | 44 | 45 | 46 | 46 | 46 | 45 | 46 |
| COL | 46 | 47 | 48 | 47 | 45 | 45 | 46 | 45 | 45 | 48 |
| ESS | 46 | 47 | 46 | 44 | 45 | 45 | 55 | 45 | 45 | 47 |
| FRE | 45 | 46 | 46 | 45 | 45 | 46 | 45 | 44 | 44 | 46 |
| GCS | - | 52 | 51 | 46 | 45 | 46 | 45 | 45 | 45 | 48 |
| GEE | 47 | 47 | 48 | 46 | 46 | 46 | 45 | 45 | 45 | 46 |
| GWS | - | - | 49 | 52 | 47 | 47 | 44 | 44 | 44 | 46 |
| HAW | 48 | 48 | 47 | 46 | 46 | 46 | 46 | 45 | 46 | 47 |
| MEL | 46 | 46 | 46 | 45 | 44 | 44 | 45 | 46 | 44 | 47 |
| NTH | 46 | 46 | 46 | 45 | 45 | 45 | 44 | 44 | 45 | 46 |
| PAD | 47 | 47 | 45 | 44 | 45 | 46 | 44 | 45 | 45 | 47 |
| RIC | 47 | 45 | 45 | 45 | 44 | 45 | 45 | 45 | 45 | 46 |
| STK | 47 | 46 | 46 | 45 | 45 | 45 | 45 | 45 | 45 | 48 |
| SYD | 45 | 45 | 44 | 45 | 45 | 44 | 46 | 46 | 46 | 49 |
| WBD | 46 | 46 | 46 | 44 | 44 | 44 | 44 | 45 | 44 | 45 |
| WCE | 46 | 46 | 46 | 44 | 44 | 46 | 46 | 47 | 45 | 46 |
| **All** | 741 | 794 | 843 | 820 | 811 | 818 | 824 | 815 | 808 | 839 |

Senior / rookie / Category B per season: 2010 627/105/9, 2011 677/102/15, 2012 719/105/19,
2013 723/77/20, 2014 718/73/20, 2015 718/78/22, 2016 718/83/23, 2017 707/81/27,
2018 703/83/22, 2019 703/102/34. Essendon 2016 (55) carries the top-up players signed for
the suspended players.

How players joined (all list rows): national draft 4,502; rookie draft 1,766; trade 1,032;
pre-season draft 180; zone 114; underage concession 91; delisted free agent 80; uncontracted
concession 70; restricted free agent 69; unrestricted free agent 49; Category B 48; mini-draft
26; other concessions, international, supplemental, top-up, mid-season, father-son, prelisting
and foundation signings 91; none recorded 5. `elevated_from_rookie` marks a senior row whose
previous season was on the same club's rookie list.

## What the checker verifies

- Every season has exactly the clubs of that season (16, GC from 2011, GWS from 2012); no
  player appears twice on one club's list in a season.
- Draft picks: every Draftguru pick matches Wikipedia's player at the same number (first four
  letters of the surname), outside ten hand-checked differences recorded in the checker with
  their reason; Wikipedia's pick count per draft equals the matched picks plus the
  Wikipedia-only picks.
- Every move has both clubs and they differ.
- Ladders: the right number of clubs, 22 games each (21 for Adelaide and Geelong in 2015),
  points equal 4W+2D, one premier, one runner-up, eight finalists.
- Warns on list sizes over the published limits (38-40 senior, 6 rookies, 9 for the northern
  clubs, 3 Category B), rows with no way of joining, blank fields, and source disagreements.

## Gaps (reported, not filled)

- **Position**: blank on every row. No free source gives a per-season position for these years.
- **Weight**: blank on 1,590 rows (players with no AFL game, so no AFL Tables bio). Where
  present it is the bio's latest weight, not the weight that season.
- **Veteran list**: not marked. Draftguru does not distinguish it; those players are `senior`.
- **No join recorded (5 rows)**: Kurt Aylett (GWS 2012-13), Will Snelling (ESS 2019),
  Cameron Sutcliffe (PAD 2019), Ryan Gardner (WBD 2019). Their Draftguru pages carry no
  movement line for that club.
- **List limits**: 30 club-seasons over the published limits, all by one to three players and
  all explained by season-long lists (mid-season draftees, elevations, ESS 2016 top-ups,
  GC/GWS start-up concessions).
- **Wikipedia-only picks (240)**: rookie elevations listed as national-draft picks to 2013,
  and re-listed players in later rookie drafts. Draftguru records both as list movements; they
  are kept with `only_in=wikipedia`.
- **2016 free agency**: Draftguru has 7, Wikipedia 9.
- **2015 ladder**: Adelaide v Geelong (round 14) was cancelled. Both sources count wins only
  (Adelaide 52, Geelong 46); the AFL's ladder gave each club 2 points. The rows say so in
  `note`; `pts` is left as the sources give it.
- **Setanta Ó hAilpín** (CAR 2010-11, GWS 2012-13): no AFL Tables match (name spelling).

## Stats a rating pass could use (not done here)

- `season_stats.csv`: the AFL Tables season totals per player per season, the same columns
  `tools/build_history.py` already rates for the 2021-25 seasons. The game's own rating model
  could rate every 2010-2019 season the same way.
- `lists.csv`: games, goals, coach votes and Brownlow votes per season; career games and goals
  before each season; height, DOB (age), draft pick and draft year (pedigree for potential).
- Not here and needed for a 2010 opening rating: the seasons before 2010 (AFL Tables
  2005-2009 totals, same free source).

## Sources

All free, public, no key, fetched 2026-11-10. URLs are also in `docs/DATA_SOURCES.md`.

- Draftguru: `https://www.draftguru.com.au/lists/<year>/<club>`, `/years/<year>`,
  `/players/<slug>/<n>`. Draftguru's own player "Grade" was not copied.
- AFL Tables: `https://afltables.com/afl/stats/<year>.html`, `/afl/seas/<year>.html`,
  `/afl/stats/players/<letter>/<player>.html`.
- Squiggle API: `https://api.squiggle.com.au/?q=standings;year=<year>`, `?q=games;year=<year>`.
- Wikipedia: `https://en.wikipedia.org/wiki/<year>_AFL_draft` (2009-2019); list limits from
  `https://en.wikipedia.org/wiki/Rookie_list` and `https://en.wikipedia.org/wiki/AFL_draft`.

Rebuild: `python tools/legacy_2010s/fetch.py --cache <dir> core`, then `players`, then
`bios`; `python tools/legacy_2010s/build.py --cache <dir>`; `python tools/check_legacy_2010s.py`.

## Build scope (for a 2010 start)

**What changes, by area.** The game is built around one data season: `GameDB.DATA_SEASON`
(2026) and `START_YEAR` (2027) are constants, and `GameState.begin_real_lists()` reads the
2026 files.

1. **Data files.** A loader-ready set for the opening season, in the 2026 shapes:
   `players_enriched_2009.csv` (2010 lists with 2009 stats and bios), `draftees_2009.csv`
   (the 2009 National Draft class), `club_moves_2009.csv` (the 2009 trade period),
   `ladder_2009.csv` (the 2009 ladder, needed for draft order and expectations),
   `departures_2009.csv`, `player_history_2009.csv`. This needs the 2009 season and earlier
   (AFL Tables 2005-2009, Wikipedia 2005-2009 drafts): not collected here.
2. **Ratings.** Rate the opening list from those seasons with the game's existing model
   (`tools/build_history.py`), so a 2010 player is rated the way a 2026 player is.
3. **`GameDB`.** Make the data season a choice of the career, not a constant: load the 2026
   set or the 2009 set, and point every `*_2026.csv` path through it. Clubs active per year
   already exist (`active_clubs`): GC joins in 2011 and GWS in 2012, with their concessions.
4. **`GameState.begin_real_lists()`** (or a `begin_legacy_2010()` beside it): the same steps
   with the 2009 files: lists, retirements and delistings, the 2009 trade period, then the
   2009 National Draft in reverse 2009 ladder order, then the 2010 season.
5. **Expansion.** GC's 2011 and GWS's 2012 entries: their underage, uncontracted and zone
   concessions and extra picks (`drafts.csv` and `moves.csv` flags) as rules every club can
   see.
6. **`data/histories`.** Pre-made league histories are made from the current sim for 2028 and
   2030 (`tools/histories/`). A 2010 start needs either its own pre-made histories or none
   (the real 2010-2019 seasons are the history: `ladders.csv`, `season_stats.csv`).
7. **Title screen.** A start choice for the legacy era.

**First shippable slice.** A 2010 real-lists career: every club's real 2010 list, rated from
2009 and earlier, the real 2009 draft class drafted in the real order, then the 2010 season
simulated. 16 clubs; GC and GWS arrive as the real expansion did. The seasons after that are
the player's own.

**What done looks like.** Starting a 2010 career shows each club's real 2010 list; the 2009
draft runs with the real class in real order; the 2010 season plays; a checker passes (every
club's list size within the limits, every player rated, ages from DOB as of 2010); the balance
harness shows the 2010 league plays like real AFL of that era.

**Open questions for the director** (options, not decisions):

1. **The real seasons after 2010.** (a) The sim decides everything from the 2010 lists on;
   (b) real drafts arrive each year as the draft classes (the real 2010-2019 draftees enter
   the league); (c) real drafts and real trades both happen as they did.
2. **Era rules.** (a) 2010 rules (no free agency until the 2012 period, no academies, the
   expansion concessions as they were), introduced in the years they began; (b) today's rules
   from 2010.
3. **Ratings for 2010.** (a) Rated relative to the 2010 league, as 2026 is rated against
   2026; (b) on one scale across eras (a 2010 star rated against today's players).
4. **What the player sees of history.** (a) The real 2010-2019 results are shown as "what
   happened" beside the player's own; (b) only the player's own timeline.
