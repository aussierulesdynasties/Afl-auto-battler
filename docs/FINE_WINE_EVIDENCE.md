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

**Real players:** on an AFL list in the season he turned 35 or older. Gawn turns 35 in 2026, the youngest
of the three named, so 35 is the line that takes in all three. 73 real players 1990-2026
(`data/fine_wine.csv`, rebuilt by `python tools/build_fine_wine.py`), 13 of them on the 2026 lists.
A Legacy start reads the same file, so a veteran of any year carries it when his real career ran to 35.

**Draftees:** 36 of the 2,789 players who joined a list aged 21 or younger from 1991 on (born 1990 or
earlier, so each could have reached 35 by 2025) were still listed in the season they turned 35: **1.29%**.
Set at **1.25%, 1 draftee in 80**, rolled once per generated prospect (and per generated expansion-list
player), every club alike. A generated class is 46-56 prospects, so about one Fine Wine draftee every
season and a half.

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
