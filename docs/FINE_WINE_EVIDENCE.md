# Fine Wine: the evidence

The director, 2026-11-13: "add a player trait 'Fine Wine', when a player has unnatural longevity like Zorko,
Gawn, Pendlebury etc / every draftee should have a very slim chance of possessing the trait too".

Source: every AFL list 1990-2025 (`data/legacy/*/lists.csv`, date of birth on each row) and the 2026 list
(`data/players_enriched_2026.csv`). Age is the age a player turns in the season (season minus birth year).

## How long real careers run

Final listed season of every career that ended 1990-2024:

| Turned in his last season | Every listed player (6,199) | 100+ games (1,197) |
| --- | --- | --- |
| 32 or older | 6.97% | 33.0% |
| 33 or older | 4.08% | 19.9% |
| 34 or older | 2.19% | 10.7% |
| 35 or older | 0.92% | 4.3% |
| 36 or older | 0.42% | 1.9% |
| 37 or older | 0.16% | 0.75% |
| 38 or older | 0.08% | 0.33% |

The oldest: Dustin Fletcher 40 (2015), Craig Bradley and Shaun Burgoyne 39, Brent Harvey and Michael Tuck 38.
Still listed in 2026: Pendlebury (turns 38), Zorko (37), Dangerfield, Walker, Rampe, Howe, Stanley (36),
Gawn, Sidebottom, Cox, Blicavs, Melksham, Gunston (35).

## Who has it

**Real players: the director's list.** The director, 2026-11-13: "research players who played a lot of games or
significant numbers games past the age of 32 and bring me a list of players for my approval to gain the trait".
He approved **60 or more games in seasons he turned 32 or older**: 72 players who played in 1990 or later
(`data/fine_wine.csv`, rebuilt by `python tools/build_fine_wine.py`; `--table` prints the list). Games by season
from AFL Tables (`data/legacy/*/season_stats.csv`, and `careers_before_1990.csv` for the earlier seasons of the men
listed in 1990). A season counts when he turned 32 or more in it; 2026 players are counted to the end of 2025.
Ten are on the 2026 lists. A Legacy start reads the same file, so a veteran of any year carries it.

Other cut-offs he was shown: 100+ games (15 players), 80+ (36), 70+ (51), 50+ (101).

**Draftees:** he chose odds that match the rate real draftees reached the same mark. Of the 2,789 players who
joined a list aged 21 or younger from 1991 on (born 1990 or earlier, so each could have reached it by 2025),
54 are on the list: **1 in 52** (1.94%), rolled once per generated prospect (and per generated expansion-list
player), every club alike. A generated class is 46-56 prospects, so about one Fine Wine draftee a season.
(The question showed 1 in 34: that counted only draftees who played a game. A generated draftee rolls whether
he plays or not, so the rate over every draftee is the match.)

| Player | Games at 32+ | Total games | Age at last game | Club |
| --- | --- | --- | --- | --- |
| Craig Bradley | 174 | 375 | 39 | CAR |
| Shaun Burgoyne | 163 | 407 | 39 | HAW/PAD |
| Michael Tuck | 161 | 426 | 38 | HAW |
| Brent Harvey | 153 | 432 | 38 | NTH |
| Dustin Fletcher | 143 | 400 | 40 | ESS |
| Robert Harvey | 128 | 383 | 37 | STK |
| David Mundy | 125 | 376 | 37 | FRE |
| Scott Pendlebury | 124 | 425 | 37 | COL |
| Travis Boak | 123 | 387 | 37 | PAD |
| Dayne Zorko | 119 | 304 | 36 | BRL |
| Todd Goldstein | 111 | 345 | 37 | NTH/ESS |
| John Blakey | 110 | 359 | 36 | NTH/FIT |
| Tom Hawkins | 103 | 359 | 36 | GEE |
| Alastair Lynch | 102 | 306 | 36 | BRL/FIT/BRB |
| Kade Simpson | 100 | 342 | 36 | CAR |
| Paul Salmon | 97 | 324 | 37 | ESS/HAW |
| Rod Carter | 93 | 293 | 36 | SYD/FIT |
| Justin Madden | 92 | 332 | 35 | CAR/ESS |
| Corey Enright | 88 | 332 | 35 | GEE |
| Drew Petrie | 88 | 332 | 35 | NTH/WCE |
| Heath Shaw | 88 | 325 | 35 | COL/GWS |
| Paul Roos | 87 | 356 | 35 | FIT/SYD |
| Roger Merrett | 86 | 313 | 36 | BRB/ESS |
| Tony Liberatore | 86 | 283 | 36 | FOO/WBD |
| Doug Hawkins | 85 | 350 | 35 | FOO/FIT |
| Jack Riewoldt | 85 | 347 | 35 | RIC |
| Shannon Hurn | 85 | 333 | 36 | WCE |
| David Cloke | 84 | 333 | 36 | RIC/COL |
| Sam Mitchell | 84 | 329 | 35 | HAW/WCE |
| Gary Ablett | 83 | 357 | 36 | GEE/GCS |
| Zach Tuohy | 83 | 288 | 35 | GEE/CAR |
| Dane Rampe | 82 | 272 | 35 | SYD |
| Taylor Walker | 81 | 301 | 35 | ADE |
| Gary Ablett | 81 | 248 | 35 | GEE/HAW |
| Isaac Smith | 80 | 280 | 35 | HAW/GEE |
| Dale Morris | 80 | 253 | 37 | WBD |
| Callan Ward | 79 | 327 | 35 | GWS/WBD |
| Simon Madden | 78 | 378 | 35 | ESS |
| Aaron Sandilands | 78 | 271 | 37 | FRE |
| Nick Riewoldt | 77 | 336 | 35 | STK |
| Jeremy Howe | 76 | 271 | 35 | COL/MEL |
| Patrick Dangerfield | 75 | 360 | 35 | GEE/ADE |
| Luke Hodge | 75 | 346 | 35 | HAW/BRL |
| Matthew Pavlich | 74 | 353 | 35 | FRE |
| Eddie Betts | 73 | 350 | 35 | CAR/ADE |
| Nigel Smart | 73 | 278 | 35 | ADE |
| Andrew Thompson | 73 | 221 | 35 | STK |
| Adam Goodes | 72 | 372 | 35 | SYD |
| Josh Kennedy | 72 | 293 | 35 | WCE/CAR |
| Matthew Boyd | 72 | 292 | 35 | WBD |
| Brett Kirk | 70 | 241 | 34 | SYD |
| Luke Breust | 69 | 308 | 35 | HAW |
| Terry Daniher | 68 | 313 | 35 | ESS/SYD |
| Mark Blicavs | 68 | 295 | 34 | GEE |
| Chris Grant | 67 | 341 | 35 | WBD/FOO |
| Mark Bickley | 67 | 272 | 34 | ADE |
| Stefan Martin | 67 | 203 | 36 | BRL/MEL/WBD |
| James McDonald | 66 | 264 | 36 | MEL/GWS |
| Max Gawn | 66 | 247 | 34 | MEL |
| Rhys Stanley | 66 | 229 | 35 | GEE/STK |
| Brad Johnson | 65 | 364 | 34 | WBD/FOO |
| Steele Sidebottom | 65 | 354 | 34 | COL |
| Nicky Winmar | 65 | 251 | 34 | STK/WBD |
| Lance Franklin | 64 | 354 | 36 | HAW/SYD |
| Stephen Silvagni | 64 | 312 | 34 | CAR |
| Robert Murphy | 63 | 312 | 35 | WBD |
| Derek Kickett | 63 | 152 | 34 | ESS/SYD/NTH |
| Scott Burns | 62 | 264 | 34 | COL |
| Joel Selwood | 60 | 355 | 34 | GEE |
| Steve Johnson | 60 | 293 | 34 | GEE/GWS |
| Simon Goodwin | 60 | 275 | 34 | ADE |
| Jarrad Waite | 60 | 244 | 35 | CAR/NTH |

## What it does

Normal ageing (`Potential.AGE_STEP`, a yearly band rolled each off-season): growing to 27, then -1..+1 to 30,
-3..0 to 33, -6..-1.5 from 34. Retirement (`Prospects.should_retire`): certain at 37, 70% a year at 35-36,
30% a year at 33+ under OVR 42.

The game's own season ratings of the named players (`data/player_history_2026.csv`, 8+ games):

| Player | Ages | Ratings |
| --- | --- | --- |
| Scott Pendlebury | 33-37 | 73, 70, 70, 68, 66 (-1.75 a year) |
| Dayne Zorko | 32-36 | 77, 62, 58, 86, 87 |
| Max Gawn | 30-34 | 83, 83, 78, 82, 88 |
| Patrick Dangerfield | 31-35 | 82, 81, 81, 75, 71 |
| Dane Rampe | 31-35 | 71, 70, 66, 61, 59 |

Over 33-37 the named group loses about 1.5 a year (median), where the normal band at 34+ loses 3.75.

Fine Wine:
- **Decline three years later:** his band is read three years younger once he is past 27 (at 34 he ages as a
  31-year-old). His growing years are untouched.
- **30% gentler:** any yearly loss is 0.7 of a normal one. At 34-36 the middle step is -1.05 a year; at 37+
  it is -2.6. That brackets Pendlebury's -1.75.
- **Retires three years later:** every retirement age moves by three, so certain at 40 (Fletcher's age),
  70% a year at 38-39. The OVR floor (32) still retires him.

Seeded careers (tests/test_potential.gd, 300 paired careers of the same player from 28, the trait the only
difference): see the PR for OVR at 34 and the average retirement age, with and without.

## Retirement in Legacy

The ruling that historical players retire about when they did in real life is built separately. A real
player's real year already includes his longevity, so that rule wins for real players; Fine Wine moves only
the generic age rules (and slows his decline, which keeps him good enough to last to his real year).
