# Legacy mode data: the 2020s (row 142)

Data for the 2020 Legacy start (TODO row 142; start dates 1990, 2000, 2010, 2020, current
season, 2028 and 2030, director 2026-11-11): real AFL lists, drafts, list moves, ladders,
season totals and season facts for 2020-2025. The game's own data starts in 2026 and is not
touched. Research and data only; no game code reads these files yet. No player is rated here.

Built 2026-11-11 by `tools/legacy_2020s/fetch.py` (polite cached fetch of free public pages;
the cache lives in the gitignored `data/cache/legacy_2020s/`) and `tools/legacy_2020s/build.py`
(cache to CSV), copied from the 2010s tools so one loader can read both decades. Checked by
`python tools/check_legacy_2020s.py`: **0 failures, 9 warnings** (gaps listed below).

## Files (`data/legacy/2020s/`)

Same files and columns as `data/legacy/2010s/` (see
[LEGACY_2010S_MANIFEST.md](LEGACY_2010S_MANIFEST.md)), plus `seasons.csv`.

| File | Rows | What it holds |
|---|---:|---|
| `lists.csv` | 4,859 | Every club's list per season 2020-2025 (1,371 players): senior, rookie and Category B, DOB, height, weight, games/goals/votes that season, career games/goals, origin, first draft, how and when the player joined. |
| `drafts.csv` | 903 | Drafts 2019-2025 (the 2019 draft feeds a 2020 start): National 443, rookie 170, mid-season rookie 107, pre-season 11, pre- and post-draft signings 172. Round, pick, club, player, origin, flag. |
| `moves.csv` | 238 | Trade periods and free agency 2019-2025: 174 trades, 28 unrestricted and 13 restricted free agents (with compensation), 23 delisted free agents. |
| `ladders.csv` | 108 | Final home-and-away ladder per season with finals finish. Premiers: 2020 RIC, 2021 MEL, 2022 GEE, 2023 COL, 2024 BRL, 2025 BRL. |
| `season_stats.csv` | 4,001 | AFL Tables season totals per player per club (2020 654, 2021 674, 2022 684, 2023 663, 2024 658, 2025 668). |
| `seasons.csv` | 6 | New: per season, clubs, rounds, Opening Round, games per club, home-and-away and finals games, Grand Final date and venue, and the season's format notes. |
| `wikipedia_draft_counts.json` | - | Picks per draft and free agents per year as Wikipedia counts them. |

**Year convention for drafts.** As in the 2010s, a draft row's `year` is the off-season it
belongs to (the 2019 National Draft feeds the 2020 lists). Draftguru files a mid-season rookie
draft under the off-season before it, so `2020,mid_season` is the draft held in June 2021;
its Wikipedia source is the 2021 draft page, and `source_url` says so. The 2025 rows (2025
National Draft, 2026 mid-season draft) are the last off-season before the game's own 2026
data.

## Season format (`seasons.csv`, from Squiggle's fixture and Wikipedia's season pages)

| Year | Clubs | Rounds | Games per club | Grand Final | Notes |
|---|---:|---:|---:|---|---|
| 2020 | 18 | 18 | 17 | Gabba | Fixture cut from 22 to 17 (one bye); matches 80% of usual length, 16-minute quarters plus time-on; suspended after round 1, resumed 11 June; quarantine hubs |
| 2021 | 18 | 23 | 22 | Perth Stadium | Forty games relocated outside their fixtured states |
| 2022 | 18 | 23 | 22 | MCG | COVID-19 top-up lists (twenty per club); last season directly affected |
| 2023 | 18 | 24 | 23 | MCG | 23 matches for the first Gather Round |
| 2024 | 18 | 25 | 23 | MCG | Opening Round; Gather Round in South Australia |
| 2025 | 18 | 25 | 23 | MCG | Opening Round and Gather Round |

Each note is ours, kept only when its evidence phrase is on the named Wikipedia page
(`SEASON_NOTES` in `build.py`; the build stops if a phrase is missing).

## List rows per club and season

Draftguru lists everyone on a list at any point of the season (mid-season draftees and
elevations count once at the club).

| Club | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| ADE | 44 | 46 | 45 | 46 | 44 | 44 |
| BRL | 47 | 45 | 45 | 45 | 47 | 44 |
| CAR | 46 | 45 | 46 | 45 | 45 | 46 |
| COL | 47 | 44 | 45 | 44 | 45 | 45 |
| ESS | 47 | 46 | 46 | 45 | 43 | 47 |
| FRE | 47 | 43 | 43 | 44 | 45 | 44 |
| GCS | 51 | 50 | 49 | 48 | 46 | 46 |
| GEE | 46 | 44 | 44 | 44 | 44 | 44 |
| GWS | 45 | 45 | 45 | 44 | 44 | 44 |
| HAW | 47 | 46 | 44 | 45 | 45 | 44 |
| MEL | 45 | 45 | 43 | 44 | 45 | 45 |
| NTH | 45 | 44 | 44 | 46 | 46 | 46 |
| PAD | 45 | 43 | 43 | 44 | 43 | 47 |
| RIC | 44 | 44 | 44 | 45 | 46 | 44 |
| STK | 45 | 44 | 44 | 44 | 45 | 44 |
| SYD | 46 | 44 | 45 | 46 | 45 | 44 |
| WBD | 45 | 43 | 44 | 44 | 44 | 44 |
| WCE | 45 | 44 | 45 | 45 | 45 | 46 |
| **All** | 827 | 805 | 804 | 808 | 807 | 808 |

Senior / rookie / Category B: 2020 698/97/32, 2021 656/121/28, 2022 659/119/26,
2023 662/117/29, 2024 669/115/23, 2025 663/118/27.

How players joined (all list rows): national draft 2,616; trade 787; rookie draft 520;
mid-season draft 242; supplemental selection 173; zone 120; Category B 84; delisted free
agent 75; unrestricted free agent 64; restricted free agent 56; international 52; pre-season
draft 24; other signings and concessions 41; none recorded 5.

## What the checker verifies

- Every season has exactly 18 clubs, the same 18, in the lists, the ladder, the season totals
  and the fixture; no player appears twice on one club's list in a season.
- Draft picks: every Draftguru pick matches Wikipedia's player (first four letters of the
  surname); Wikipedia's pick count per draft equals the matched picks plus the Wikipedia-only
  picks. Mid-season drafts are matched against the next year's Wikipedia page.
- Every move has both clubs and they differ; free agents per year agree with Wikipedia (all
  seven years match).
- Ladders: 18 clubs, games per club 17 (2020), 22 (2021-22), 23 (2023-25), points 4W+2D, one
  premier, one runner-up, eight finalists. The fixture's games per club, game count and nine
  finals agree; the 2020 note records the 16-minute quarters.

## Gaps (reported, not filled)

- **Position**: blank on every row (no free per-season source).
- **Weight**: blank on 866 rows (no AFL game, so no AFL Tables bio); otherwise the bio's latest.
- **Height**: blank for Zak Evans (GCS 2025).
- **No join recorded (5 rows)**: Lachie Bramble (HAW 2021-23), Wil Parker (COL 2024-25,
  Category B): their Draftguru pages carry no joining line.
- **List limits**: 41 club-seasons over the 2010s checker's limits, nearly all rookie lists
  of 7-10: Draftguru's season-long lists include mid-season draftees taken into inactive
  places. The limits are warnings only and were not re-researched for this decade.
- **Pick numbering**: Wikipedia numbers some rookie and mid-season drafts counting passed
  picks; Draftguru does not. 14 picks are matched by club and surname and say "Wikipedia
  numbers this pick N" in `wiki_note`.
- **Wikipedia-only picks (88)**: delisted players re-listed through the rookie and pre-season
  drafts, and two redrafted players in 2025 (Ryan Byrnes, Jake Stringer). Kept with
  `only_in=wikipedia`.
- **2022 West Coast**: player-games differ (Draftguru 499, AFL Tables 506): six players with
  seven games between them (Mountford, Florenca, Black, Giro, Dewar, Ainsworth) are on AFL
  Tables but on no Draftguru list; West Coast fielded COVID-19 top-up players that year.
- **Hewago Paul Oea** (GCS 2022-23): no AFL Tables match (name spelling).
- **Moves from outside the AFL (5)**: delisted free agents who were on no list that season
  (Sam Skinner, Fergus Greene, Oscar McDonald, Sam Naismith, Toby Pink): `from_club` blank.

## Sources

All free, public, no key, fetched 2026-11-11 (URLs also in `docs/DATA_SOURCES.md`):
Draftguru `lists/<year>/<club>` (2020-2025), `years/<year>` (2019-2025), `players/<slug>/<n>`;
AFL Tables `stats/<year>.html`, `seas/<year>.html`, player bios; Squiggle API standings and
games; Wikipedia `<year>_AFL_draft` (2019-2026) and `<year>_AFL_season` (2020-2025).

Rebuild: `python tools/legacy_2020s/fetch.py --cache data/cache/legacy_2020s core`, then
`players`, then `bios`; `python tools/legacy_2020s/build.py --cache data/cache/legacy_2020s`;
`python tools/check_legacy_2020s.py`.

## Changes from the 2010s tools

- Mid-season rookie drafts are their own `mid_season` kind on the Wikipedia side (the 2010s
  parser read the heading as the rookie draft), matched one year on.
- Wikipedia tables: a "pick due to" column no longer reads as the pick, a passed pick's
  spanned cell is expanded, and a round row without a notes cell keeps its round.
- "Delisted then Drafted by ..." lines (mid-season re-drafts) count as the joining draft.
- The AFL Tables ladder is found by its `lad` anchor (the heading "<year> Ladder" is split by
  a link; checked on the 2015 page, the 2010s build reads no AFL Tables ladder and so used
  Squiggle's points throughout).
