# The 2010 start against today (Legacy mode, row 142)

Built by `tools/legacy_2010s/build_start.py --report`, on the rating model of the 1990 start (each season rated against its own players, each position scaled on its own season; director 2026-11-10 'A: per era', 2026-11-13 'Scale each position per season').

## Stat averages, per player per game

Every player with a game that season. The 2026 base is the 2020-25 seasons (2026 is not in the AFL Tables files); the game's own 2026 lists are rated on 2026.

| Seasons | di | ki | hb | mk | tk | gl | cl | cp | if50 | rb | rated 80+ per season | median OVR (8+ games) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2009 (the data season) | 17.0 | 8.9 | 8.0 | 4.4 | 2.8 | 0.6 | 1.5 | 5.6 | 2.2 | 1.5 | 45.0 | 61 |
| 2010-19 | 16.7 | 9.4 | 7.3 | 4.1 | 3.0 | 0.6 | 1.7 | 6.4 | 2.3 | 1.6 | 48.8 | 61 |
| 2020-25 (base) | 15.3 | 9.1 | 6.2 | 3.9 | 2.5 | 0.5 | 1.6 | 5.8 | 2.2 | 1.7 | 50.5 | 61 |
| 2009 vs base | +11% | -2% | +29% | +14% | +11% | +19% | -1% | -2% | +1% | -10% | | |

## The 2010 lists as the game loads them, against today's

Both rated by `tools/sim_harness.py` (the game rates again at load, the same model): the 2010 lists on 2009, today's on 2026. Players with a game in the data season.

| Lists | players | rated 80+ | 80+ per club | 70+ | median | 90th pct | best | club medians |
|---|---|---|---|---|---|---|---|---|
| 2010 (on 2009) | 516 | 43 | 2.7 | 114 | 58 | 79 | 96 | 55-63 |
| 2026 (on 2026) | 669 | 51 | 2.8 | 138 | 58 | 78 | 92 | 53-60 |

| Club | players | median OVR | best | 80+ |
|---|---|---|---|---|
| ADE | 32 | 59 | 85 | 2 |
| BRL | 32 | 56 | 89 | 3 |
| CAR | 33 | 58 | 91 | 3 |
| COL | 35 | 57 | 90 | 4 |
| ESS | 31 | 58 | 83 | 2 |
| FRE | 32 | 55 | 88 | 3 |
| GEE | 32 | 61 | 96 | 3 |
| HAW | 35 | 57 | 87 | 3 |
| MEL | 35 | 56 | 78 | 0 |
| NTH | 31 | 55 | 81 | 1 |
| PAD | 34 | 60 | 80 | 2 |
| RIC | 31 | 56 | 82 | 1 |
| STK | 30 | 63 | 90 | 6 |
| SYD | 30 | 57 | 84 | 5 |
| WBD | 31 | 63 | 87 | 4 |
| WCE | 32 | 56 | 83 | 1 |

Top 15 in 2010: Gary Ablett (GEE) 96, Chris Judd (CAR) 91, Nick Maxwell (COL) 90, Lenny Hayes (STK) 90, Nick Riewoldt (STK) 90, Jonathan Brown (BRL) 89, Simon Black (BRL) 89, Nick Dal Santo (STK) 89, Aaron Sandilands (FRE) 88, Brad Sewell (HAW) 87, Matthew Boyd (WBD) 87, Brian Lake (WBD) 86, Nathan Bock (ADE) 85, Joel Selwood (GEE) 85, Josh Gibson (HAW) 85
