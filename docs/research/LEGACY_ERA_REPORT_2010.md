# The 2010 start against today (Legacy mode, row 142)

Built by `tools/legacy_2010s/build_start.py --report`, on the rating model of the 1990 start (each season rated against its own players, each position scaled on its own season; director 2026-11-10 'A: per era', 2026-11-13 'Scale each position per season').

## Stat averages, per player per game

Every player with a game that season. The 2026 base is the 2020-25 seasons (2026 is not in the AFL Tables files); the game's own 2026 lists are rated on 2026.

| Seasons | di | ki | hb | mk | tk | gl | cl | cp | if50 | rb | rated 80+ per season | median OVR (8+ games) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2009 (the data season) | 17.0 | 8.9 | 8.0 | 4.4 | 2.8 | 0.6 | 1.5 | 5.6 | 2.2 | 1.5 | 29.0 | 60 |
| 2010-19 | 16.7 | 9.4 | 7.3 | 4.1 | 3.0 | 0.6 | 1.7 | 6.4 | 2.3 | 1.6 | 35.1 | 60 |
| 2020-25 (base) | 15.3 | 9.1 | 6.2 | 3.9 | 2.5 | 0.5 | 1.6 | 5.8 | 2.2 | 1.7 | 39.3 | 61 |
| 2009 vs base | +11% | -2% | +29% | +14% | +11% | +19% | -1% | -2% | +1% | -10% | | |

## The 2010 lists as the game loads them, against today's

Both rated by `tools/sim_harness.py` (the game rates again at load, the same model): the 2010 lists on 2009, today's on 2026. Players with a game in the data season.

| Lists | players | rated 80+ | 80+ per club | 70+ | median | 90th pct | best | club medians |
|---|---|---|---|---|---|---|---|---|
| 2010 (on 2009) | 516 | 79 | 4.9 | 191 | 65 | 83 | 99 | 62-71 |
| 2026 (on 2026) | 669 | 85 | 4.7 | 179 | 62 | 81 | 99 | 59-66 |

| Club | players | median OVR | best | 80+ |
|---|---|---|---|---|
| ADE | 32 | 69 | 92 | 5 |
| BRL | 32 | 63 | 92 | 8 |
| CAR | 33 | 62 | 93 | 5 |
| COL | 35 | 69 | 93 | 7 |
| ESS | 31 | 65 | 81 | 2 |
| FRE | 32 | 65 | 99 | 6 |
| GEE | 32 | 67 | 95 | 8 |
| HAW | 35 | 62 | 85 | 2 |
| MEL | 35 | 64 | 83 | 2 |
| NTH | 31 | 66 | 86 | 2 |
| PAD | 34 | 66 | 91 | 4 |
| RIC | 31 | 65 | 90 | 5 |
| STK | 30 | 69 | 97 | 7 |
| SYD | 30 | 65 | 91 | 4 |
| WBD | 31 | 71 | 97 | 10 |
| WCE | 32 | 64 | 95 | 2 |

Top 15 in 2010: Aaron Sandilands (FRE) 99, Paul Duffield (FRE) 98, Nick Dal Santo (STK) 97, Shaun Higgins (WBD) 97, Jason Akermanis (WBD) 97, Lindsay Gilbee (WBD) 96, Gary Ablett (GEE) 95, Dean Cox (WCE) 95, Marc Murphy (CAR) 93, Dane Swan (COL) 93, Jason Porplyzia (ADE) 92, Jonathan Brown (BRL) 92, Nick Riewoldt (STK) 92, Brad Johnson (WBD) 92, Corey Enright (GEE) 91
