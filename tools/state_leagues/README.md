# State leagues data (VFL, SANFL, WAFL 2026)

Builds `data/state_leagues/` (TODO row 128, step 1). Data only: nothing in the game reads it yet.

```
python tools/state_leagues/build.py           # rewrite data/state_leagues/*.csv (+ keep .import files)
python tools/state_leagues/build.py --check   # exit 1 if the files on disk are out of date
```

## Two stages

| Stage | Where | Input | Output |
| --- | --- | --- | --- |
| A, scrape | `scrape/` | downloaded pages (not in the repo): Zero Hanger and vfl.aflmstats.com (VFL), sanflstats.com API and club guides (SANFL), footyinfo.com and wafl.com.au (WAFL) | `staging/*.csv`, one set per league in that league's own columns |
| B, build | `build.py` | `staging/`, `sources/2026_{VFL,SANFL,WAFL}_season.wiki` (Wikipedia wikitext of the season pages), `data/players_enriched_2026.csv`, `data/list_additions_2026.csv`, `data/clubs.csv` | `data/state_leagues/` in one schema |

Stage B is the reproducible step: it needs nothing outside the repo. Stage A is the record of how
`staging/` was made; rerun it only to refresh the scrape.

## What stage B does

- **One schema.** Clubs: code, kind (standalone / reserves / aligned), AFL club, future AFL club
  (TASD becomes Tasmania's reserves side in 2028, director 2026-11-12), ground, colours, 2026 senior
  coach. Players: identity, flagged dob and height, 2026 League stats (a column the league does not
  record stays blank), reserves and colts games.
- **AFL links.** A state row is an AFL man when name and date of birth match one man on the AFL
  lists; with no date, the full name inside his side's own AFL club, or inside the AFL club the source
  names. A same-named man at another club stays unlinked. Linked men go to `afl_links_2026.csv`,
  keyed by the GameDB id, never to a players file. A man who played for two state clubs has a row
  for each.
- **Imputation, flagged.** `dob_src`: source / age (WAFL ages, read 2026-11-12) / league_median.
  `height_src`: source / role_median_<DEF|MID|FWD|RUC|all> (role from position, else hit-outs or goals
  per game).
- **Lists.** Every club's senior list is capped at 50 (most League games, then Reserves games); WAFL
  men who played only Colts are `junior`; the rest are `extra`.
- **Fixes.** The SANFL API's "Wauer Seb" is Seb Wauer (sources in the row). The WAFL's three
  colts listed twice (own club and West Coast) are one row at their own club.
- **Season files.** `leagues.csv` (rounds, games, byes, finals, Grand Final venue, points per team
  game, spread and goal accuracy from every home-and-away score), `ladders_2026.csv` and
  `finals_2026.csv` (the real 2026 results, for the finals bracket test).

`tests/test_state_leagues_data.gd` checks the result.
